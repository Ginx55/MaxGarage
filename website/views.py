from datetime import datetime, date, timedelta
import json
import random
import time
import threading
import os
import imghdr
from itertools import islice
import pytz

from django import forms
from django.conf import settings
from django.contrib import auth
from django.core.mail import EmailMessage
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, Http404
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

import pyrebase

config = {
    'apiKey': "AIzaSyAKBm5kuT0f-hwVg3ecC6SjZTE4MMxfRi4",
    'authDomain': "maxweb-5ea84.firebaseapp.com",
    'databaseURL': "https://maxweb-5ea84-default-rtdb.asia-southeast1.firebasedatabase.app",
    'projectId': "maxweb-5ea84",
    'storageBucket': "maxweb-5ea84.appspot.com",
    'messagingSenderId': "765328893873",
    'appId': "1:765328893873:web:9546126eb532e9165fff90"
}
firebase = pyrebase.initialize_app(config)
authentication = firebase.auth()
db = firebase.database()
storage = firebase.storage()

# Create your views here.
def send_email(subject_message, email_message):
    recipient_list = []
    user_data_list = db.child("Users").order_by_child("status").equal_to(True).get().val()

    for user_data in user_data_list.values():
        recipient_list.append(user_data['email'])

    subject = subject_message
    message = email_message
    from_email = 'mxgmotorparts@gmail.com'

    email = EmailMessage(subject, message, from_email, recipient_list)
    email.send()

# LogIn
def log_in(email, password):
    try:
        user_data = db.child("Users").order_by_child("email").equal_to(email).get().val()
        user_data_key = list(user_data.keys())[0]
        if user_data and "tempPassword" in user_data[user_data_key]:
            if password == user_data[user_data_key]["tempPassword"]:
                return "SetUp"
            else:
                return None
        user = authentication.sign_in_with_email_and_password(email, password)
        return user
    except pyrebase.pyrebase.HTTPError as e:
        return None
    except:
        return None

def AccountSetUp(request):
    if not request.session.get('email'):
        return redirect('LogIn')
    return render(request, "personalTemplates/AccountSetUp.html")

def insertAccount(request):
    password = request.POST.get('password')
    confirmpass = request.POST.get('confirmpass')

    if password == confirmpass:
        email = request.session['email']

        user = authentication.create_user_with_email_and_password(email, password)

        user_data = db.child("Users").order_by_child("email").equal_to(email).get().val()
        user_data_key = list(user_data.keys())[0]
        
        db.child("Users").child(user_data_key).child("tempPassword").remove()

        current_date = str(date.today())
        newData = {
            "lastLogin" : current_date,
            "userID" : user['localId']
        }
        db.child("Users").child(user_data_key).update(newData)
        
        user = log_in(email, password)        
        if user:
            local_id = user['localId']

            user_data = db.child("Users").order_by_child("userID").equal_to(local_id).get().val()

            if user_data:
                user_data_key = list(user_data.keys())[0]

                if user_data[user_data_key]["status"]:
                    db.child("Users").child(user_data_key).set(user_data[user_data_key], user['idToken'])

                    update_last_login(user_data_key)

                    role = user_data[user_data_key]['role']
                    request.session['sessionID'] = user['idToken']
                    request.session['username'] = user_data[user_data_key]['username']
                    request.session['role'] = role
                    request.session['uid'] = local_id

                    if role == "Cashier":
                        return JsonResponse({'authenticated': True, 'redirect_url': '/PurchaseTransaction/'})
                    else:
                        return JsonResponse({'authenticated': True, 'redirect_url': '/Dashboard/'})
                    
                else:
                    return JsonResponse({'authenticated': False, 'error_message': 'Account Disabled!'})
            else:
                return JsonResponse({'authenticated': False, 'error_message': 'Account not found!'}, status=400)
        else:
            return JsonResponse({'authenticated': False, 'error_message': 'Invalid credentials!'}, status=400)

    else:
        return JsonResponse({'authenticated': False, 'error_message': 'Password and Confirm Password doesnt match!'}, status=400)

def update_last_login(user_key):
    current_date = str(date.today())
    last_login = {"lastLogin": current_date}
    db.child("Users").child(user_key).update(last_login)

def login(request):
    auth.logout(request)
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = log_in(email, password)
        if user == "SetUp":
            request.session['email'] = email
            return JsonResponse({'authenticated': True, 'redirect_url': '/AccountSetUp/'})
        
        if user:
            local_id = user['localId']

            user_data = db.child("Users").order_by_child("userID").equal_to(local_id).get().val()

            if user_data:
                user_data_key = list(user_data.keys())[0]

                if user_data[user_data_key]["status"]:
                    db.child("Users").child(user_data_key).set(user_data[user_data_key], user['idToken'])

                    update_last_login(user_data_key)

                    role = user_data[user_data_key]['role']
                    request.session['sessionID'] = user['idToken']
                    request.session['username'] = user_data[user_data_key]['username']
                    request.session['role'] = role
                    request.session['uid'] = local_id

                    if role == "Cashier":
                        return JsonResponse({'authenticated': True, 'redirect_url': '/PurchaseTransaction/'})
                    else:
                        return JsonResponse({'authenticated': True, 'redirect_url': '/Dashboard/'})
                    
                else:
                    return JsonResponse({'authenticated': False, 'error_message': 'Account Disabled!'})
            else:
                return JsonResponse({'authenticated': False, 'error_message': 'Account not found!'}, status=400)
        else:
            return JsonResponse({'authenticated': False, 'error_message': 'Invalid credentials!'}, status=400)

    return render(request, "personalTemplates/LogIn.html")

def ForgotPass(request):
    return render(request , "personalTemplates/ForgotPassword.html")

def send_forgot_pass(request):
    emailText = request.POST.get('email')
    try:
        user_data = db.child("Users").order_by_child("email").equal_to(emailText).get().val()
        if user_data:
            user_key = list(user_data.keys())[0]
            if user_data[user_key]['status']:
                authentication.send_password_reset_email(emailText)
                return JsonResponse({'authenticated': True, 'success_message': 'Check your email!'})
            else:
                return JsonResponse({'authenticated': False, 'error_message': 'Account Disabled!'}, status=400)
        else:
            return JsonResponse({'authenticated': False, 'error_message': 'Account not found!'}, status=400)
    except Exception as e:
        return JsonResponse({'authenticated': False, 'error_message': f'Error: {str(e)}'}, status=500)

# Dashboard
def Dashboard(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    user = authentication.get_account_info(request.session.get('sessionID'))

    local_id = user['users'][0]['localId']

    user_data = db.child("Users").order_by_child("userID").equal_to(local_id).get().val()
    user_data_key = list(user_data.keys())[0]
    request.session['username'] = user_data[user_data_key]['username']
    request.session['role'] = user_data[user_data_key]['role']
    request.session['mode'] = user_data[user_data_key]['mode']
    request.session['uid'] = local_id
    request.session['imgsrc'] = user_data[user_data_key]['imgsrc']
    
    if request.session['role'] == 'Cashier':
        raise Http404("You do not have permission to access this page.")
    
    thread = threading.Thread(target=check_quantities, args=(5,))
    thread.start()

    topItemsSold = db.child("Items").order_by_child("totalSold").limit_to_last(5).get().val()

    ph_timezone = pytz.timezone('Asia/Manila')
    current_date = datetime.now(ph_timezone)
    negaInt = int(current_date.strftime("%Y%m%d%H%M%S")) * -1

    try:
        transactionList = db.child("TransactionLog").order_by_child("negaIntDate").start_at(negaInt).limit_to_first(5).get().val()
        activityList = db.child("SystemActivities").order_by_child("negaIntDate").start_at(negaInt).limit_to_first(3).get().val()
    except AttributeError:
        pass

    startDate = current_date - timedelta(days=6)
    date_range = [(startDate + timedelta(x)).strftime("%Y%m%d") for x in range((current_date - startDate).days + 1)]

    labels = [int(date[-4:]) for date in date_range]
    data = []

    for date in date_range:
        daily_transactions = db.child("TransactionLog").order_by_child("intDate").equal_to(int(date)).get().val() or {}
        total = sum(float(entry.get("totalPrice", 0)) for entry in daily_transactions.values())
        data.append(total)

    data = {
        "Title": "Dashboard",
        "User": request.session.get('username'),
        "imageURL" : request.session['imgsrc'],
        "TransactionList": transactionList,
        "ActivityList": activityList,
        "labels": labels,
        "data": data,
        "topItemSold": topItemsSold,
        "role" : request.session['role'],
        "mode" : request.session['mode'],
    }

    return render(request, "personalTemplates/Dashboard.html", data)

# Sales
def PurchaseTransaction(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    user = authentication.get_account_info(request.session.get('sessionID'))

    local_id = user['users'][0]['localId']

    user_data = db.child("Users").order_by_child("userID").equal_to(local_id).get().val()
    user_data_key = list(user_data.keys())[0]
    request.session['username'] = user_data[user_data_key]['username']
    request.session['role'] = user_data[user_data_key]['role']
    request.session['mode'] = user_data[user_data_key]['mode']
    request.session['imgsrc'] = user_data[user_data_key]['imgsrc']

    thread = threading.Thread(target=check_quantities, args=(5,))
    thread.start()

    data = {
        "Title" : "Purchase Transaction",
        "User" : request.session['username'],
        "imageURL" : request.session['imgsrc'],
        "salesClass" : True,
        "role" : request.session['role'],
        "mode" : request.session['mode'],
    }
    return render(request, "personalTemplates/PurchaseTransaction.html", data)

def SearchItem(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    if request.method == 'POST':
        textbox = request.POST.get('textbox')
        if len(textbox) < 3:
            return HttpResponse("Input length must be at least 3 characters.")

        itemData = search_item(textbox)
        
        if itemData:
            return JsonResponse(itemData)
        else:
            return HttpResponse("Cannot find item")

def search_item(textbox):
    itemData = search_item_by_id(textbox)
    if not itemData:
        itemData = search_item_by_name(textbox)
    return itemData

def get_item_details(item_key, item_details):
    return {
        "itemName": item_details[item_key]['itemName'],
        "itemPrice": item_details[item_key]['itemPrice'],
        "itemKey": item_key,
        "itemID": item_details[item_key]['itemID'],
        "itemQuantity": item_details[item_key]['itemQuantity'],
        "fixedID": item_details[item_key]['fixedID'],
    }

def search_item_by_id(textbox):
    try:
        item_details = db.child("Items").order_by_child("itemID").equal_to(textbox).limit_to_first(1).get().val()
        if item_details:
            item_key = list(item_details.keys())[0]
            return get_item_details(item_key, item_details)
    except Exception as e:
        print("Error:", e)
    return None

def search_item_by_name(textbox):
    try:
        item_details = db.child("Items").order_by_child("itemName").start_at(textbox).limit_to_first(1).get().val()
        if item_details:
            first_entry = list(item_details.keys())[0]
            return get_item_details(first_entry, item_details)
    except Exception as e:
        print("Error:", e)
    return None

def generate_transaction_id():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    max_timestamp_digits = 6

    timestamp = timestamp[-max_timestamp_digits:]

    remaining_digits = 10 - len(timestamp)
    random_number = random.randint(10**(remaining_digits-1), (10**remaining_digits) - 1)

    transaction_id = int(f"{timestamp}{random_number:0{remaining_digits}d}")
    return transaction_id

def insert_transaction(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    if request.method == 'POST':
        try:
            item_ids = [item['itemID'] for item in json.loads(request.POST['itemList'])]
            item_details = {}

            bought_data = []

            for item_id in item_ids:
                item_data = db.child("Items").order_by_child("itemID").equal_to(item_id).get().val()
                item_key = list(item_data.keys())[0]
                if item_data:
                    item_details[item_id] = next(iter(item_data.values()))
                    item_details[item_id]["key"] = item_key

            items = json.loads(request.POST['itemList'])
            customer = request.POST.get('customer')
            payment = float(request.POST.get('payment'))
            total = float(0)

            item_updates = {}

            for item_data in items:
                item_ID = item_data['itemID']
                item_detail = item_details.get(item_ID)
                item_key = item_detail["key"]
                item_data["pricePerPiece"] = float(item_detail['itemPrice'])
                if item_detail:
                    item_quantity = int(item_data['itemQuantity'])
                    item_price = float(item_detail['itemPrice'])
                    quantity = int(item_detail['itemQuantity']) - item_quantity
                    if quantity <= 0:
                        quantity = 0

                    total += item_quantity * item_price

                    total_sold = item_quantity + int(item_detail['totalSold'])
                    item_updates[item_key] = {
                        "itemQuantity": quantity,
                        "totalSold": total_sold,
                    }

                    bought_data.append({
                        'itemCode': item_detail['itemCode'], 
                        'quantity': item_quantity, 
                        'price' : item_quantity * item_price
                    })

            for item_key, update_data in item_updates.items():
                db.child("Items").child(item_key).update(update_data)

            ph_timezone = pytz.timezone('Asia/Manila')
            current_date_time_ph = datetime.now(ph_timezone)
            transaction_id = generate_transaction_id()
            current_date = str(date.today())
            current_time = current_date_time_ph.strftime("%I:%M %p")
            int_date = int(current_date_time_ph.strftime("%Y%m%d"))
            nega_int = -1 * int(current_date_time_ph.strftime("%Y%m%d%H%M%S"))
            current_user = request.session.get('username', '')

            change = payment - total

            transaction_data = {
                "customer": customer,
                "currentTime": current_time,
                "currentDate": current_date,
                "negaIntDate": nega_int,
                "transactionID": str(transaction_id),
                "currentUser": current_user,
                "itemsBought": items,
                "totalPrice": total,
                "status": "Paid",
                "remarks": "",
                "intDate": int_date,
                "itemStatus": "",
                "payment": float(payment),
                "change": float(change),
            }

            db.child("TransactionLog").push(transaction_data)

            trans_data = {
                "date": current_date,
                "time": current_time,
                "ref": transaction_id,
                "customer": customer,
                "cashier": current_user,
                "total": float(total),
                "change": float(change),
                "payment": float(payment),
                "itemsBought" : bought_data,
            }

            thread = threading.Thread(target=check_quantities, args=(1,))
            thread.start()

            return JsonResponse(trans_data)

        except Exception as e:
            return JsonResponse({"message": str(e)}, status=500)

def TransactionLog(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    user = authentication.get_account_info(request.session.get('sessionID'))

    local_id = user['users'][0]['localId']

    user_data = db.child("Users").order_by_child("userID").equal_to(local_id).get().val()
    user_data_key = list(user_data.keys())[0]
    request.session['username'] = user_data[user_data_key]['username']
    request.session['role'] = user_data[user_data_key]['role']
    request.session['mode'] = user_data[user_data_key]['mode']
    request.session['uid'] = local_id
    request.session['imgsrc'] = user_data[user_data_key]['imgsrc']

    ph_timezone = pytz.timezone('Asia/Manila')
    current_date = datetime.now(ph_timezone)
    negaInt = int(current_date.strftime("%Y%m%d%H%M%S")) * -1

    transactionList = db.child("TransactionLog").order_by_child("negaIntDate").start_at(negaInt).limit_to_first(10).get().val()
    topItemsSold = db.child("Items").order_by_child("totalSold").limit_to_last(5).get().val()

    startDate = current_date - timedelta(6)
    date_range = [(startDate + timedelta(x)).strftime("%Y%m%d") for x in range((current_date - startDate).days + 1)]

    labels = [int(date[4:8]) for date in date_range]
    data = []

    for date in date_range:
        daily_transactions = db.child("TransactionLog").order_by_child("intDate").equal_to(int(date)).get().val() or {}
        total = sum(float(entry.get("totalPrice", 0)) for entry in daily_transactions.values())
        data.append(total)

    thread = threading.Thread(target=check_quantities, args=(5,))
    thread.start()

    data = {
        "Title": "Transaction Log",
        "User": request.session['username'],
        "imageURL" : request.session['imgsrc'],
        "TransactionList": transactionList,
        "labels": labels,
        "data": data,
        "topItemSold": topItemsSold,
        "salesClass" : True,
        "role" : request.session['role'],
        "mode" : request.session['mode'],
    }

    return render(request, "personalTemplates/TransactionLog.html", data)

def TransactionDetails(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    if request.method == 'POST':
        transactionID = request.POST.get('transID')
        transaction = db.child("TransactionLog").child(transactionID).get().val()
        items_bought = transaction["itemsBought"]
        for index, item_bought in enumerate(items_bought):
            items_bought[index]["imgsrc"] = getImageURL("item_images/", item_bought["fixedID"])
        request.session['transactionKey'] = transactionID
        return JsonResponse(transaction)
    
def send_void_email(delay, transactionID, remarks):
    time.sleep(delay)
    subject, message = voided_transaction_message(transactionID, remarks)
    send_email(subject, message)

def VoidTransaction(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    if request.method == 'POST':
        try:
            transactionKey = request.session['transactionKey']
            remarks = request.POST.get('remarks')
            
            transaction = db.child("TransactionLog").child(transactionKey).get().val()

            transaction["status"] = "Voided"
            transaction["remarks"] = remarks

            items_bought = transaction["itemsBought"]
            for index, item_bought in enumerate(items_bought):
                if item_bought["itemQuantity"] != "REFUNDED":
                    item_key, item_details = get_item_details_return(item_bought["itemID"], item_bought["fixedID"])
                    if item_details:
                        current_total_sold = int(item_details[item_key]['totalSold'])
                        new_total_sold = current_total_sold - int(item_bought['itemQuantity'])
                        db.child("Items").child(item_key).update({"totalSold": new_total_sold})
                    else:
                        pass
            db.child("VoidedTransactions").push(transaction)
            db.child("TransactionLog").child(transactionKey).remove()

            removeValue = {
                "Transaction ID": transaction['transactionID']
            }
            add_system_activities(request, "voided a transaction", removeValue)

            thread = threading.Thread(target=send_void_email, args=(1, transaction['transactionID'], remarks))
            thread.start()
            
            return JsonResponse({"message": "The transaction has been successfully voided!"})

        except Exception as e:
            error_message = f"An error occurred while voiding the transaction: {str(e)}"
            return JsonResponse({"error": error_message}, status=500)

    else:
        return JsonResponse({"error": "Invalid request method. Only POST requests are allowed."}, status=405)

def Date(dateData):
    try:
        stringDate = datetime.strptime(dateData, "%Y-%m-%d")
        intDate = int(stringDate.strftime("%Y%m%d"))
        return intDate
    except ValueError:
        return None

def GetSalesReport(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    user = authentication.get_account_info(request.session.get('sessionID'))

    local_id = user['users'][0]['localId']

    user_data = db.child("Users").order_by_child("userID").equal_to(local_id).get().val()
    user_data_key = list(user_data.keys())[0]
    request.session['username'] = user_data[user_data_key]['username']
    request.session['role'] = user_data[user_data_key]['role']
    request.session['uid'] = local_id
    request.session['imgsrc'] = user_data[user_data_key]['imgsrc']
    
    if request.session['role'] == 'Cashier':
        raise Http404("You do not have permission to access this page.")
    
    if request.method == 'POST':
        startDate = request.POST.get('startDate')
        endDate = request.POST.get('endDate')

        startingDate = Date(startDate)
        endingDate = Date(endDate)

        if startingDate is None or endingDate is None:
            return JsonResponse({"error": "Invalid date format"}, status=400)

        if endingDate < startingDate:
            startingDate, endingDate = endingDate, startingDate

        try:
            query = db.child("TransactionLog").order_by_child("intDate").start_at(startingDate).end_at(endingDate).get().val()
            if query:
                return JsonResponse(query)
            else:
                return JsonResponse({"error": "No transactions found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method. Only POST requests are allowed."}, status=405)

def VoidedTransactions(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    user = authentication.get_account_info(request.session.get('sessionID'))

    local_id = user['users'][0]['localId']

    user_data = db.child("Users").order_by_child("userID").equal_to(local_id).get().val()
    user_data_key = list(user_data.keys())[0]
    request.session['username'] = user_data[user_data_key]['username']
    request.session['role'] = user_data[user_data_key]['role']
    request.session['mode'] = user_data[user_data_key]['mode']
    request.session['uid'] = local_id
    request.session['imgsrc'] = user_data[user_data_key]['imgsrc']

    ph_timezone = pytz.timezone('Asia/Manila')
    current_date = datetime.now(ph_timezone)
    nega_int = int(current_date.strftime("%Y%m%d%H%M%S")) * -1
    transactionList = db.child("VoidedTransactions").order_by_child("negaIntDate").start_at(nega_int).limit_to_first(10).get().val()
    data = {
        "Title" : "Voided Transactions",
        "User" : request.session['username'],
        "imageURL" : request.session['imgsrc'],
        "TransactionList" : transactionList,
        "salesClass" : True,
        "role" : request.session['role'],
        "mode" : request.session['mode'],
    }
    return render(request, "personalTemplates/VoidedTransactions.html", data)

def VoidedDetails(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    if request.method == 'POST':
        transactionID = request.POST.get('transID')
        transaction = db.child("VoidedTransactions").child(transactionID).get().val()
        request.session['transactionKey'] = transactionID
        items_bought = transaction["itemsBought"]
        for index, item_bought in enumerate(items_bought):
            items_bought[index]["imgsrc"] = getImageURL("item_images/", item_bought["fixedID"])
        return JsonResponse(transaction)

def get_item_details_return(item_id, fixed_id):
    item_details = db.child("Items").order_by_child("itemID").equal_to(item_id).get().val()

    if not item_details:
        item_details = db.child("Items").order_by_child("fixedID").equal_to(fixed_id).get().val()

    if item_details:
        item_key = list(item_details.keys())[0]
        return item_key, item_details

    return None, None

def ReturnToInventory(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    if request.method == 'POST':
        transkey = request.POST.get('transkey')
        try:
            transaction = db.child("VoidedTransactions").child(transkey).get().val()
            items_bought = transaction["itemsBought"]
            for index, item_bought in enumerate(items_bought):
                if item_bought["itemQuantity"] != "REFUNDED":
                    item_key, item_details = get_item_details_return(item_bought["itemID"], item_bought["fixedID"])
                    if item_details:
                        current_quantity = int(item_details[item_key]['itemQuantity'])
                        new_quantity = current_quantity + int(item_bought['itemQuantity'])
                        db.child("Items").child(item_key).update({"itemQuantity": new_quantity})
                    else:
                        pass

            db.child("VoidedTransactions").child(transkey).update({"itemStatus": "returned to inventory"})

            return HttpResponse("Items have been successfully returned to inventory!")
        except Exception as e:
            return HttpResponse(f"An error occurred: {str(e)}", status=500)
    else:
        return HttpResponse("Invalid request method." , status=400)

def get_file_extension(file_path):
    _, extension = os.path.splitext(file_path)
    return extension.lower()

def is_image(file_path):
    # Check if the file is an image using imghdr
    return imghdr.what(file_path) is not None
    
class AddItemForm(forms.Form):
    itemID = forms.CharField(max_length=12, min_length=8, error_messages={
        'min_length': 'Barcode must be at least 8 characters long.',
        'max_length': 'Barcode cannot exceed 12 characters.',
    })
    itemName = forms.CharField(max_length=30, min_length=3, error_messages={
        'min_length': 'Item name must be at least 3 characters long.',
        'max_length': 'Item name cannot exceed 30 characters.',
    })
    itemPrice = forms.FloatField(validators=[MinValueValidator(0.0)], error_messages={
        'min_value': 'Item price must be a non-negative value.',
    })
    itemQuantity = forms.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(1000)], error_messages={
        'min_value': 'Item quantity must be a non-negative integer.',
        'max_value': 'Item quantity cannot exceed 1000.',
    })
    itemMaxQuantity = forms.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(1000)], error_messages={
        'min_value': 'Maximum quantity must be a non-negative integer.',
        'max_value': 'Maximum quantity cannot exceed 1000.',
    })

    itemCriticalQuantity = forms.IntegerField(validators=[MinValueValidator(0)], error_messages={
        'min_value': 'Critical quantity must be a non-negative integer.',
    })

    expiryDates = forms.JSONField(required=False)

    # Custom validation example:
    def clean(self):
        cleaned_data = super().clean()
        item_max_quantity = cleaned_data.get('itemMaxQuantity')
        item_critical_quantity = cleaned_data.get('itemCriticalQuantity')

        if item_max_quantity is not None and item_critical_quantity is not None:
            if item_critical_quantity >= item_max_quantity:
                raise forms.ValidationError("Critical quantity must be less than the maximum quantity.")
            
    def clean_expiryDates(self):
        expiry_dates = self.cleaned_data.get('expiryDates')

        if not expiry_dates:
            return []

        cleaned_expiry_dates = []

        for entry in expiry_dates:
            date = entry.get('date')
            notify = entry.get('notify')

            if not date:
                raise forms.ValidationError("Expiry date is required.")
           

            if notify is not None:
                try:
                    notify = int(notify)
                except ValueError:
                    raise forms.ValidationError("Notify value must be a valid integer.")

                if notify < 0:
                    raise forms.ValidationError("Notify value must be a non-negative integer.")
            cleaned_expiry_dates.append({'date': date, 'notify': notify})
        return cleaned_expiry_dates
    
def generate_unique_id():
    timestamp = int(time.time() * 1000)
    random_number = random.randint(0, 999)
    unique_id = f"{timestamp}-{random_number}"
    return unique_id

def generate_item_code(word):
    if len(word) == 0:
        return word

    first_letter = word[0]
    rest_of_word = word[1:]
    without_vowels = ''.join(char for char in rest_of_word if char.lower() not in 'aeiou')

    return first_letter + without_vowels

def add_item(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    user = authentication.get_account_info(request.session.get('sessionID'))

    local_id = user['users'][0]['localId']

    user_data = db.child("Users").order_by_child("userID").equal_to(local_id).get().val()
    user_data_key = list(user_data.keys())[0]
    request.session['username'] = user_data[user_data_key]['username']
    request.session['role'] = user_data[user_data_key]['role']
    request.session['uid'] = local_id
    request.session['imgsrc'] = user_data[user_data_key]['imgsrc']
    
    if request.session['role'] == 'Cashier':
        raise Http404("You do not have permission to access this page.")
    
    try:
        if request.method == 'POST':
            form = AddItemForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data

                check_item = db.child("Items").order_by_child("itemID").equal_to(data['itemID']).get().val()

                if check_item:
                    return JsonResponse({"message": "Barcode ID already exists"}, status=400)
                
                fixedID = generate_unique_id()

                image_file = request.FILES.get('image')
                imgsrc = ""
                imgsrccopy = ""
                fixedidCopy = generate_unique_id()

                if image_file is not None:

                    file_extension = get_file_extension(image_file.name)

                    if file_extension == '.gif':
                        storage.child("item_images/" + fixedID).put(image_file)
                        imgsrc = getImageURL("item_images/", fixedID)

                        storage.child("item_images/" + fixedidCopy).put(image_file)
                        imgsrccopy = getImageURL("item_images/",  fixedidCopy)
                        pass
                    elif is_image(image_file):
                        storage.child("item_images/" + fixedID).put(image_file)
                        imgsrc = getImageURL("item_images/", fixedID)

                        storage.child("item_images/" + fixedidCopy).put(image_file)
                        imgsrccopy = getImageURL("item_images/",  fixedidCopy)
                        pass
                    else:
                        error_message = "Invalid file format."
                        return JsonResponse({"message": "Invalid data", "errors": {"file": [error_message]}}, status=400)

                ph_timezone = pytz.timezone('Asia/Manila')
                current_date = datetime.now(ph_timezone)
                nega_int = int(current_date.strftime("%Y%m%d%H%M%S")) * -1

                item_data = {
                    "fixedID" : fixedID,
                    "itemID": data['itemID'],
                    "itemCode" : generate_item_code(data['itemName']),
                    "itemName": data['itemName'],
                    "itemPrice": data['itemPrice'],
                    "itemQuantity": data['itemQuantity'],
                    "itemMaxQuantity": data['itemMaxQuantity'],
                    "itemCriticalQuantity": data['itemCriticalQuantity'],
                    "expiryDate": data['expiryDates'],
                    "location": 'Items',
                    "negaIntDate": nega_int,
                    "totalSold": 0,
                    "criticalNotif" : True,
                    "overStockNotif" : True,
                    "expiryNotif" : True,
                    "imgsrc" : imgsrc,
                    "imgsrccopy" : imgsrccopy,
                    "fixedidCopy" : fixedidCopy,
                }
                db.child("Items").push(item_data)

                activities_data = {
                    "Item ID": data['itemID'],
                    "Item Name": data['itemName'],
                    "Item Price": data['itemPrice'],
                    "Item Quantity": data['itemQuantity'],
                    "Item Max Quantity": data['itemMaxQuantity'],
                    "Item Critical Quantity": data['itemCriticalQuantity'],
                }
                add_system_activities(request, "added an item", activities_data)
                return JsonResponse({"message": "Item inserted successfully!"})
            else:
                return JsonResponse({"message": "Invalid data", "errors": form.errors}, status=400)

        return JsonResponse({"message": "Invalid request method"}, status=400)
    
    except Exception as e:
        return JsonResponse({"message": "An error occurred", "error": str(e)}, status=500)

def EditItem(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    user = authentication.get_account_info(request.session.get('sessionID'))

    local_id = user['users'][0]['localId']

    user_data = db.child("Users").order_by_child("userID").equal_to(local_id).get().val()
    user_data_key = list(user_data.keys())[0]
    request.session['username'] = user_data[user_data_key]['username']
    request.session['role'] = user_data[user_data_key]['role']
    request.session['uid'] = local_id
    request.session['imgsrc'] = user_data[user_data_key]['imgsrc']
    
    if request.session['role'] == 'Cashier':
        raise Http404("You do not have permission to access this page.")
    
    if request.method == 'POST':
        item_key = request.POST.get('itemKey')
        item = db.child("Items").child(item_key).get().val()

        if item:
            item_details = {
                "key" : item_key,
                "itemID": item.get('itemID', ''),
                "itemName": item.get('itemName', ''),
                "itemPrice": item.get('itemPrice', ''),
                "itemQuantity": item.get('itemQuantity', ''),
                "itemMaxQuantity": item.get('itemMaxQuantity', ''),
                "itemCriticalQuantity": item.get('itemCriticalQuantity', ''),
                "expiryDate": item.get('expiryDate', ''),
                "imgsrc" : item.get('imgsrc', ''),
            }

            request.session['itemDetails'] = item_details
            return JsonResponse(item_details)
        else:
            return JsonResponse({"error": "Item not found"}, status=404)

def save_edit_item(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    user = authentication.get_account_info(request.session.get('sessionID'))

    local_id = user['users'][0]['localId']

    user_data = db.child("Users").order_by_child("userID").equal_to(local_id).get().val()
    user_data_key = list(user_data.keys())[0]
    request.session['username'] = user_data[user_data_key]['username']
    request.session['role'] = user_data[user_data_key]['role']
    request.session['uid'] = local_id
    request.session['imgsrc'] = user_data[user_data_key]['imgsrc']
    
    if request.session['role'] == 'Cashier':
        raise Http404("You do not have permission to access this page.")
    
    try:
        if request.method == 'POST':
            item_key = request.POST.get('itemkey')
            form = AddItemForm(request.POST)

            if form.is_valid():
                thread = threading.Thread(target=check_quantities, args=(600,))
                thread.start()

                item_details = db.child("Items").child(item_key).get().val()

                data = form.cleaned_data

                image_file = request.FILES.get('image')

                check_item = db.child("Items").order_by_child("itemID").equal_to(data['itemID']).get().val()

                existing_entries = {}
                # Check if the barcode ID already exists for entries other than the one being updated
                if check_item:
                    existing_entries = {key: value for key, value in check_item.items() if key != item_key}

                if existing_entries:
                    return JsonResponse({"message": "Barcode ID already exists for other items"}, status=400)

                all_item_data = db.child("Items").child(item_key).get().val()
                imgsrc = all_item_data['imgsrc']
                imgsrccopy = all_item_data['imgsrccopy']
                fixedidCopy = all_item_data['fixedidCopy']

                imgcopyID = generate_unique_id()
                if image_file is not None:
                    try:
                        storage.delete("item_images/" + fixedidCopy, request.session['sessionID'])
                    except:
                        pass

                    file_extension = get_file_extension(image_file.name)

                    if file_extension == '.gif' or is_image(image_file):
                        storage.child("item_images/" + all_item_data['fixedID']).put(image_file)
                        imgsrc = getImageURL("item_images/", all_item_data['fixedID'])

                        storage.child("item_images/" + imgcopyID).put(image_file)
                        imgsrccopy = getImageURL("item_images/", imgcopyID)
                    else:
                        error_message = "Invalid file format. Only image files are allowed."
                        return JsonResponse({"message": "Invalid data", "errors": {"file": [error_message]}}, status=400)

                item_id = data['itemID']
                item_name = data['itemName']
                item_price = data['itemPrice']
                item_quantity = data['itemQuantity']
                item_max_quantity = data['itemMaxQuantity']
                item_critical_quantity = data['itemCriticalQuantity']
                expiry_date = data['expiryDates']

                item_data = {
                    "itemID": item_id,
                    "itemCode": generate_item_code(item_name),
                    "itemName": item_name,
                    "itemPrice": item_price,
                    "itemQuantity": item_quantity,
                    "itemMaxQuantity": item_max_quantity,
                    "itemCriticalQuantity": item_critical_quantity,
                    "expiryDate": expiry_date,
                    "criticalNotif": True,
                    "overStockNotif": True,
                    "expiryNotif": True,
                    "imgsrc": imgsrc,
                    "imgsrccopy": imgsrccopy,
                    "fixedidCopy": imgcopyID,
                }
                db.child("Items").child(item_key).update(item_data)

                field_labels = {
                    "itemID": "Barcode",
                    "itemName": "Item Name",
                    "itemPrice": "Price",
                    "itemQuantity": "Quantity",
                    "itemMaxQuantity": "Maximum Quantity",
                    "itemCriticalQuantity": "Critical Quantity"
                }

                # Compare old and new values to identify changes
                changed_fields = {}
                for field, label in field_labels.items():
                    if item_details[field] != data[field]:
                        changed_fields[label] = {
                            "old": item_details[field],
                            "new": data[field]
                        }

                if changed_fields:
                    add_system_activities(request, "updated an item", changed_fields)

                return JsonResponse({"message": f"{item_name} has been updated successfully"}, status=200)

            else:
                return JsonResponse({"message": "Invalid form data", "errors": form.errors}, status=400)
        else:
            return JsonResponse({"message": "Invalid request method"}, status=405)
    
    except Exception as e:
        return JsonResponse({"message": "An unexpected error occurred"}, status=500)

def check_expiry(expiry_dates):
    current_date = datetime.now()
    expired_dates = []
    about_to_expire_dates = []
    earliest_expiry_date = None
    
    if expiry_dates:
        for expiry_date in expiry_dates:
            date = datetime.strptime(expiry_date["date"], "%Y-%m-%d")
            notify_days = int(expiry_date["notify"])
            threshold_date = date - timedelta(days=notify_days)
            
            if current_date >= date:
                expired_dates.append(date)
            elif current_date >= threshold_date:
                about_to_expire_dates.append(date)
            
            if not earliest_expiry_date or date < earliest_expiry_date:
                earliest_expiry_date = date
        
        if expired_dates:
            return "danger", min(expired_dates).strftime("%Y-%m-%d")
        elif about_to_expire_dates:
            return "warning", min(about_to_expire_dates).strftime("%Y-%m-%d")
        else:
            return "notExpired", earliest_expiry_date.strftime("%Y-%m-%d")

def item_list(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    user = authentication.get_account_info(request.session.get('sessionID'))

    local_id = user['users'][0]['localId']

    user_data = db.child("Users").order_by_child("userID").equal_to(local_id).get().val()
    user_data_key = list(user_data.keys())[0]
    request.session['username'] = user_data[user_data_key]['username']
    request.session['role'] = user_data[user_data_key]['role']
    request.session['mode'] = user_data[user_data_key]['mode']
    request.session['uid'] = local_id
    request.session['imgsrc'] = user_data[user_data_key]['imgsrc']

    
    ph_timezone = pytz.timezone('Asia/Manila')
    current_date = datetime.now(ph_timezone)
    nega_int = int(current_date.strftime("%Y%m%d%H%M%S")) * -1
    item_list = db.child("Items").order_by_child("negaIntDate").start_at(nega_int).limit_to_first(10).get().val()

    if item_list:
        for key, item in item_list.items():
            try:
                item_quantity = item.get("itemQuantity", 0)
                critical_quantity = item.get("itemCriticalQuantity", 0)
                max_quantity = item.get("itemMaxQuantity", 0)
                item_class = "danger" if item_quantity <= critical_quantity else ("warning" if item_quantity > max_quantity else "")
                item["itemClass"] = item_class

                expiry = item.get("expiryDate", [])
                date_list = sorted([{"notify": ex.get("notify", ""), "date": ex.get("date", "")} for ex in expiry], key=lambda ex: datetime.strptime(ex["date"], "%Y-%m-%d"))

                expiry_status, first_expiry_date = check_expiry(date_list)
                item["expiryClass"] = expiry_status
                item["expiryDate"] = first_expiry_date

            except Exception as e:
                item["expiryClass"] = ""
                item["expiryDate"] = ""

    thread = threading.Thread(target=check_quantities, args=(5,))
    thread.start()

    data = {
        "Title": "Item List",
        "User": request.session.get('username', ''),
        "imageURL" : request.session['imgsrc'],
        "Items": item_list,
        "itemClass": True,
        "role" : request.session['role'],
        "mode" : request.session['mode'],
    }
    return render(request, "personalTemplates/ItemList.html", data)

def remove_data(location, key, user):
    item = db.child(location).child(key).get().val()
    current_date = str(date.today())
    bin_data = create_bin_data(item, location, current_date)
    deleted_data = create_deleted_data(item, bin_data, user)

    db.child("RecycleBin").push(deleted_data)
    db.child(location).child(key).remove()

def create_bin_data(item, location, current_date):
    return {
        "ID": item['itemID'],
        "itemName": item['itemName'],
        "date": current_date,
        "location": location
    }

def create_deleted_data(item, bin_data, user):
    ph_timezone = pytz.timezone('Asia/Manila')
    current_date = datetime.now(ph_timezone)
    nega_int_date = int(current_date.strftime("%Y%m%d%H%M%S")) * -1
    
    return {
        "negaIntDate": nega_int_date,
        "data": item,
        "binData": bin_data,
        "user" : user,
    }

def remove_item(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    user = authentication.get_account_info(request.session.get('sessionID'))

    local_id = user['users'][0]['localId']

    user_data = db.child("Users").order_by_child("userID").equal_to(local_id).get().val()
    user_data_key = list(user_data.keys())[0]
    request.session['username'] = user_data[user_data_key]['username']
    request.session['role'] = user_data[user_data_key]['role']
    request.session['uid'] = local_id
    request.session['imgsrc'] = user_data[user_data_key]['imgsrc']
    
    if request.session['role'] == 'Cashier':
        raise Http404("You do not have permission to access this page.")
    
    if request.method == 'POST':
        item_key = request.POST.get('itemID')
        item = db.child("Items").child(item_key).get().val()

        if item:
            remove_data("Items", item_key, request.session['username'])

            remove_value = {
                "Barcode": item['itemID'],
                "Item Name": item['itemName'],
            }

            add_system_activities(request, "removed an item", remove_value)

            return JsonResponse({"message": f"{item['itemName']} has been removed successfully"}, status=200)
        else:
            return JsonResponse({"message": "Item not found or already removed"}, status=404)

    return JsonResponse({"message": "Invalid request method"}, status=405)

# Return
def Return(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    user = authentication.get_account_info(request.session.get('sessionID'))

    local_id = user['users'][0]['localId']

    user_data = db.child("Users").order_by_child("userID").equal_to(local_id).get().val()
    user_data_key = list(user_data.keys())[0]
    request.session['username'] = user_data[user_data_key]['username']
    request.session['role'] = user_data[user_data_key]['role']
    request.session['mode'] = user_data[user_data_key]['mode']
    request.session['uid'] = local_id
    request.session['imgsrc'] = user_data[user_data_key]['imgsrc']

    
    ph_timezone = pytz.timezone('Asia/Manila')
    current_date = datetime.now(ph_timezone)
    nega_int = int(current_date.strftime("%Y%m%d%H%M%S")) * -1
    returnList = db.child("Return").order_by_child("negaIntDate").start_at(nega_int).limit_to_first(10).get().val()
    data = {
        "Title" : "Return",
        "User" : request.session['username'],
        "imageURL" : request.session['imgsrc'],
        "ReturnList" : returnList,
        "role" : request.session['role'],
        "mode" : request.session['mode'],
    }
    return render(request, "personalTemplates/Return.html", data)

def SearchTransactions(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    if request.method == 'POST':
        transactionID = request.POST.get('transID')
        transaction = db.child("TransactionLog").order_by_child("transactionID").equal_to(transactionID).get().val()

        if transaction:
            trans = list(transaction.values())[0]
            items_bought = trans["itemsBought"]

            for index, item_bought in enumerate(items_bought):
                items_bought[index]["imgsrc"] = getImageURL("item_images/", item_bought["fixedID"])

            return JsonResponse(trans, status=200)
        else:
            return JsonResponse({"message": "Transaction not found"}, status=404)

    return JsonResponse({"message": "Invalid request method"}, status=405)

class ReturnForm(forms.Form):
    itemList = forms.JSONField()
    transactionID = forms.CharField()

    def clean_itemList(self):
        item_list = self.cleaned_data.get('itemList', []) 
        for entry in item_list:
            itemName = entry.get('itemName')
            itemQuantity = entry.get('itemQuantity')
            itemID = entry.get('itemID')
            fixedID = entry.get('fixedID')
            returnType = entry.get('returnType')

            # Check if itemQuantity is not an integer
            try:
                itemQuantity = int(itemQuantity)
                if itemQuantity <= 0:
                    raise ValidationError('Invalid itemQuantity. It should be a positive integer.')
            except (ValueError, TypeError):
                raise ValidationError('Invalid itemQuantity. It should be a valid integer.')

            # Check if returnType is not 'Replacement' or 'Refund'
            if returnType not in ['Replacement', 'Refund']:
                raise ValidationError('Invalid returnType. It should be either "Replacement" or "Refund".')

            # Validate itemName, itemID, and fixedID
            if not itemName or not isinstance(itemName, str):
                raise ValidationError('Invalid itemName. It should be a non-empty string.')

            if not itemID or not isinstance(itemID, str):
                raise ValidationError('Invalid itemID. It should be a non-empty string.')

            if not fixedID or not isinstance(fixedID, str):
                raise ValidationError('Invalid fixedID. It should be a non-empty string.')

        return item_list

def calculate_total_price(data_update):
    new_total = sum(float(item["itemPrice"]) if item["itemPrice"] != "REFUNDED" else 0 for item in data_update)
    # new_tax = (12 / 100) * new_total
    return new_total

def insert_return(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    try:
        if request.method == 'POST':
            # Parse the returned_items using the ReturnForm
            form = ReturnForm(request.POST)
            if form.is_valid():
                returned_items = form.cleaned_data['itemList']
                transID = form.cleaned_data['transactionID']

                # Fetch transaction details
                transaction = db.child("TransactionLog").order_by_child("transactionID").equal_to(transID).get().val()

                if not transaction:
                    return JsonResponse({"error": "Transaction not found."}, status=400)

                transaction_key = list(transaction.keys())[0]
                items_bought = transaction[transaction_key]["itemsBought"]

                for returned_item in returned_items:
                    item_name = returned_item['itemName']
                    returned_quantity = returned_item['itemQuantity']
                    item_id = returned_item['itemID']
                    fixed_id = returned_item['fixedID']
                    return_type = returned_item['returnType']

                    ph_timezone = pytz.timezone('Asia/Manila')

                    current_datetime = datetime.now(ph_timezone)
                    current_date = str(date.today())
                    current_time = current_datetime.strftime("%I:%M %p")

                    nega_int_date = int(current_datetime.strftime("%Y%m%d%H%M%S")) * -1

                    item_key, item_details = get_item_details_return(item_id, fixed_id)

                    for index, item_bought in enumerate(items_bought):
                        if item_bought["fixedID"] == fixed_id:
                            item_bought["returnedDate"] = current_date
                            if return_type == "Replacement":
                                if item_details:
                                    current_quantity = int(item_details[item_key]['itemQuantity'])
                                    remaining_quantity = max(current_quantity - int(returned_quantity), 0)
                                    db.child("Items").child(item_key).update({"itemQuantity": remaining_quantity})

                            elif return_type == "Refund":
                                bought_quantity = item_bought["itemQuantity"]
                                new_quantity = max(int(bought_quantity) - int(returned_quantity), 0)

                                if new_quantity == 0:
                                    item_bought["itemQuantity"] = "REFUNDED"
                                    item_bought["itemPrice"] = "REFUNDED"
                                else:
                                    item_bought["itemQuantity"] = new_quantity
                                    item_bought["itemPrice"] = int(item_bought["pricePerPiece"]) * new_quantity

                    return_data = {
                        "itemID": item_id,
                        "fixedID": fixed_id,
                        "returnType": return_type,
                        "itemName": item_name,
                        "returnedQuantity": returned_quantity,
                        "currentDate": current_date,
                        "currentTime": current_time,
                        "transactionID": transID,
                        "status": "returned to supplier",
                        "negaIntDate": nega_int_date,
                        "currentUser": request.session['username'],
                        "customer": transaction[transaction_key]["customer"],
                    }

                    db.child("Return").push(return_data)
                    returnValue = {
                        "Transaction ID": transID,
                        "Item Name" : item_name,
                        "Returned Quantity" : returned_quantity,
                        "Return Type" : return_type,
                    }
                    add_system_activities(request, "added a return", returnValue)

                data_update = [item for index, item in enumerate(items_bought)]

                new_total_price = calculate_total_price(data_update)
                update_data = {
                    "itemsBought": data_update,
                    "totalPrice": new_total_price,
                    "change": transaction[transaction_key]["payment"] - new_total_price,
                }

                db.child("TransactionLog").child(transaction_key).update(update_data)

                return JsonResponse({"message": "Items have been successfully added to the return!"})
            else:
                errors = dict(form.errors)
                return JsonResponse({"error": "Invalid input data. Please check the provided values.", "form_errors": errors}, status=400)
        else:
            return JsonResponse({"error": "Invalid request method. Only POST requests are allowed."}, status=400)
        
    except Exception as e:
        error_message = f"An error occurred while processing the return: {str(e)}"
        return JsonResponse({"error": error_message}, status=500)

def ReturnDetails(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    try:
        returnID = request.POST.get('returnKey')
        returnData = db.child("Return").child(returnID).get().val()

        if returnData is not None:
            return JsonResponse(returnData)
        else:
            return JsonResponse({"error": "Return not found with the specified returnID."}, status=404)
    except Exception as e:
        error_message = f"An error occurred while retrieving return details: {str(e)}"
        return JsonResponse({"error": error_message}, status=500)

def ItemReceived(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    try:
        returnID = request.POST.get('returnKey')
        returnData = db.child("Return").child(returnID).get().val()

        itemID = returnData['itemID']
        fixedID = returnData['fixedID']
        quantity = returnData['returnedQuantity']

        item_key, item_details = get_item_details_return(itemID, fixedID)
        if item_details:
            new_quantity = int(item_details[item_key]['itemQuantity']) + int(quantity)
            db.child("Items").child(item_key).update({"itemQuantity": new_quantity})
            db.child("Return").child(returnID).child("status").set("received")

            returnValue = {
                "Transaction ID": returnData["transactionID"],
                "Item Name" : returnData["itemName"],
                "Returned Quantity" : quantity,
                "Status" : "received",
            }
            add_system_activities(request, "updated a return", returnValue)
            
            return JsonResponse({"message": "Item has been successfully marked as received."})
        else:
            return JsonResponse({"error": "Cannot find the item in inventory."}, status=404)
    except Exception as e:
        error_message = f"An error occurred while processing the item status: {str(e)}"
        return JsonResponse({"error": error_message}, status=500)

# SystemActivities
def SystemActivities(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    user = authentication.get_account_info(request.session.get('sessionID'))

    local_id = user['users'][0]['localId']

    user_data = db.child("Users").order_by_child("userID").equal_to(local_id).get().val()
    user_data_key = list(user_data.keys())[0]
    request.session['username'] = user_data[user_data_key]['username']
    request.session['role'] = user_data[user_data_key]['role']
    request.session['mode'] = user_data[user_data_key]['mode']
    request.session['uid'] = local_id
    request.session['imgsrc'] = user_data[user_data_key]['imgsrc']
    
    if request.session['role'] != 'Admin':
        raise Http404("You do not have permission to access this page.")
    
    ph_timezone = pytz.timezone('Asia/Manila')
    current_date = datetime.now(ph_timezone)
    nega_int = int(current_date.strftime("%Y%m%d%H%M%S")) * -1
    activityList = db.child("SystemActivities").order_by_child("negaIntDate").start_at(nega_int).get().val()
    try:
        for key, item in activityList.items():
            action = item["actionsMade"]
            if "voided" in action or "removed" in action:
                item["class"] = "danger"
            elif "restored" in action or "added" in action:
                item["class"] = "success"
            elif "updated" in action:
                item["class"] = "warning"
    except Exception as e:
        pass

    data = {
        "Title" : "Audit Trail",
        "User" : request.session['username'],
        "imageURL" : request.session['imgsrc'],
        "ActivityList" : activityList,
        "role" : request.session['role'],
        "mode" : request.session['mode'],
    }
    return render(request, "personalTemplates/SystemActivities.html", data)

def add_system_activities(request, activity, updatedValues):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    user = authentication.get_account_info(request.session.get('sessionID'))

    local_id = user['users'][0]['localId']

    user_data = db.child("Users").order_by_child("userID").equal_to(local_id).get().val()
    user_data_key = list(user_data.keys())[0]
    request.session['username'] = user_data[user_data_key]['username']
    request.session['role'] = user_data[user_data_key]['role']
    request.session['uid'] = local_id
    request.session['imgsrc'] = user_data[user_data_key]['imgsrc']

    ph_timezone = pytz.timezone('Asia/Manila')

    int_current_date = datetime.now(ph_timezone)
    int_date = int(int_current_date.strftime("%Y%m%d%H%M%S"))

    current_date = str(date.today())
    current_time = int_current_date.strftime("%I:%M %p")

    nega_int = int(int_current_date.strftime("%Y%m%d%H%M%S")) * -1
    activitiesData = {
        "intDateCreated" : int_date,
        "dateCreated" : current_date,
        "timeCreated" : current_time,
        "actionsMade" : activity,
        "updatedValues" : updatedValues,
        "negaIntDate" : nega_int,
        "userID" : local_id,
        "role" : user_data[user_data_key]['role'],
        "currentUser" : user_data[user_data_key]['username'],
        "imgsrc" : user_data[user_data_key]['imgsrc'],
    }
    db.child("SystemActivities").push(activitiesData)

def ViewSystemActivities(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    user = authentication.get_account_info(request.session.get('sessionID'))

    local_id = user['users'][0]['localId']

    user_data = db.child("Users").order_by_child("userID").equal_to(local_id).get().val()
    user_data_key = list(user_data.keys())[0]
    request.session['username'] = user_data[user_data_key]['username']
    request.session['role'] = user_data[user_data_key]['role']
    request.session['uid'] = local_id
    request.session['imgsrc'] = user_data[user_data_key]['imgsrc']
    
    if request.session['role'] != 'Admin':
        raise Http404("You do not have permission to access this page.")
    
    if request.method == 'POST':
        activityID = request.POST.get('activityKey')
        activityData = db.child("SystemActivities").child(activityID).get().val()
        return JsonResponse(activityData)

# RecycleBin
def RecycleBin(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    user = authentication.get_account_info(request.session.get('sessionID'))

    local_id = user['users'][0]['localId']

    user_data = db.child("Users").order_by_child("userID").equal_to(local_id).get().val()
    user_data_key = list(user_data.keys())[0]
    request.session['username'] = user_data[user_data_key]['username']
    request.session['role'] = user_data[user_data_key]['role']
    request.session['mode'] = user_data[user_data_key]['mode']
    request.session['uid'] = local_id
    request.session['imgsrc'] = user_data[user_data_key]['imgsrc']

    
    if request.session['role'] == 'Cashier':
        raise Http404("You do not have permission to access this page.")
    
    ph_timezone = pytz.timezone('Asia/Manila')
    current_date = datetime.now(ph_timezone)
    nega_int = int(current_date.strftime("%Y%m%d%H%M%S")) * -1
    binList = db.child("RecycleBin").order_by_child("negaIntDate").start_at(nega_int).get().val()
    data = {
        "Title" : "Archive",
        "User" : request.session['username'],
        "imageURL" : request.session['imgsrc'],
        "BinList": binList,
        "role" : request.session['role'],
        "mode" : request.session['mode'],
    }
    return render(request, "personalTemplates/RecycleBin.html", data)

# UserList
def UserList(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    user = authentication.get_account_info(request.session.get('sessionID'))

    local_id = user['users'][0]['localId']

    user_data = db.child("Users").order_by_child("userID").equal_to(local_id).get().val()
    user_data_key = list(user_data.keys())[0]
    request.session['username'] = user_data[user_data_key]['username']
    request.session['role'] = user_data[user_data_key]['role']
    request.session['mode'] = user_data[user_data_key]['mode']
    request.session['uid'] = local_id
    request.session['imgsrc'] = user_data[user_data_key]['imgsrc']

    
    if request.session['role'] != 'Admin':
        raise Http404("You do not have permission to access this page.")
    
    ph_timezone = pytz.timezone('Asia/Manila')
    current_date = datetime.now(ph_timezone)
    nega_int = int(current_date.strftime("%Y%m%d%H%M%S")) * -1
    userList = db.child("Users").order_by_child("negaIntDate").start_at(nega_int).get().val()
    data = {
        "Title" : "User List",
        "User" : request.session['username'],
        "imageURL" : request.session['imgsrc'],
        "UserList" : userList,
        "role" : request.session['role'],
        "mode" : request.session['mode'],
    }
    return render(request, "personalTemplates/UserList.html", data)

class AddUserForm(forms.Form):
    username = forms.CharField(
        max_length=15,
        min_length=3,
        error_messages={
            'min_length': 'Username must be at least 3 characters long.',
            'max_length': 'Username cannot be more than 15 characters long.',
        }
    )
    email = forms.EmailField(
        error_messages={
            'invalid': 'Enter a valid email address.',
        }
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=6,
        error_messages={
            'min_length': 'Password must be at least 6 characters long.',
        }
    )
    confirmpass = forms.CharField(
        widget=forms.PasswordInput,
        min_length=6,
        error_messages={
            'min_length': 'Confirm Password must be at least 6 characters long.',
        }
    )
    contact = forms.CharField(
        max_length=11,
        min_length=11,
        error_messages={
            'min_length': 'Contact number must be 11 digits long.',
            'max_length': 'Contact number must be 11 digits long.',
        }
    )
    role = forms.CharField(
        error_messages={
            'required': 'Role is required.',
        }
    )

    def clean_role(self):
        role = self.cleaned_data.get('role')
        allowed_roles = ['Admin', 'Manager', 'Cashier']
        if role not in allowed_roles:
            raise forms.ValidationError('Invalid role. Allowed values are: ' + ', '.join(allowed_roles))
        return role

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirmpass = cleaned_data.get('confirmpass')

        # Check if password and confirm password match
        if password and confirmpass and password != confirmpass:
            self.add_error('confirmpass', 'Password and Confirm Password do not match.')

def AddUser(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    user = authentication.get_account_info(request.session.get('sessionID'))

    local_id = user['users'][0]['localId']

    user_data = db.child("Users").order_by_child("userID").equal_to(local_id).get().val()
    user_data_key = list(user_data.keys())[0]
    request.session['username'] = user_data[user_data_key]['username']
    request.session['role'] = user_data[user_data_key]['role']
    request.session['uid'] = local_id
    request.session['imgsrc'] = user_data[user_data_key]['imgsrc']
    
    if request.session['role'] != 'Admin':
        raise Http404("You do not have permission to access this page.")
    
    try:
        if request.method == "POST":
            form = AddUserForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data

                username = data['username']
                email = data['email']
                password = data['password']
                contact = data['contact']
                role = data['role']

                check_user = db.child("Users").order_by_child("email").equal_to(email).get().val()
                if check_user:
                    errors = {'email': 'Email already exists'}
                    return JsonResponse({"error": "Form validation failed", "errors": errors}, status=400)

                image_file = request.FILES.get('image')
                imgsrc = ""
                uniqueID = generate_unique_id()

                if image_file is not None:
                    file_extension = get_file_extension(image_file.name)
                    
                    if file_extension == '.gif' or is_image(image_file):
                        storage.child("user_profiles/" + uniqueID).put(image_file)
                        imgsrc = getImageURL("user_profiles/", uniqueID)
                    else:
                        error_message = "Invalid file format."
                        return JsonResponse({"message": "Invalid data", "errors": {"file": [error_message]}}, status=400)
                
                current_date = str(date.today())
                ph_timezone = pytz.timezone('Asia/Manila')
                current_date = datetime.now(ph_timezone)
                nega_int = int(current_date.strftime("%Y%m%d%H%M%S")) * -1
                userData = {
                    "dateCreated": current_date,
                    "username": username,
                    "role": role,
                    "email": email,
                    "contact": contact,
                    "mode": "Light Mode",
                    "negaIntDate": nega_int,
                    "status": True,
                    "lastLogin": "",
                    "imgsrc" : imgsrc,
                    "tempPassword" : password,
                    "imageName" : uniqueID,
                }
                db.child("Users").push(userData)
                return JsonResponse({"message": "User added successfully"})
            else:
                # Form is not valid, you can access the custom error messages
                errors = {
                    'username': form.errors.get('username', [])[0] if 'username' in form.errors else None,
                    'email': form.errors.get('email', [])[0] if 'email' in form.errors else None,
                    'password': form.errors.get('password', [])[0] if 'password' in form.errors else None,
                    'confirmpass': form.errors.get('confirmpass', [])[0] if 'confirmpass' in form.errors else None,
                    'contact': form.errors.get('contact', [])[0] if 'contact' in form.errors else None,
                    'role': form.errors.get('role', [])[0] if 'role' in form.errors else None,
                }

                # Filter out None values
                errors = {key: value for key, value in errors.items() if value is not None}
                return JsonResponse({"error": "Form validation failed", "errors": errors}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)

def SearchUser(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    user = authentication.get_account_info(request.session.get('sessionID'))

    local_id = user['users'][0]['localId']

    user_data = db.child("Users").order_by_child("userID").equal_to(local_id).get().val()
    user_data_key = list(user_data.keys())[0]
    request.session['username'] = user_data[user_data_key]['username']
    request.session['role'] = user_data[user_data_key]['role']
    request.session['uid'] = local_id
    request.session['imgsrc'] = user_data[user_data_key]['imgsrc']
    
    if request.session['role'] != 'Admin':
        raise Http404("You do not have permission to access this page.")
    
    if request.method == 'POST':
        userKey = request.POST.get('userKey')
        userData = db.child("Users").child(userKey).get().val()
        userData['currentuser'] = user_data[user_data_key]["email"]
        request.session['userKey'] = userKey
        return JsonResponse(userData)

class EditUserForm(forms.Form):
    username = forms.CharField(
        max_length=15,
        min_length=3,
        error_messages={
            'min_length': 'Username must be at least 3 characters long.',
            'max_length': 'Username cannot be more than 15 characters long.',
        }
    )
    contact = forms.CharField(
        max_length=11,
        min_length=11,
        error_messages={
            'min_length': 'Contact number must be 11 digits long.',
            'max_length': 'Contact number must be 11 digits long.',
        }
    )

    role = forms.CharField(
        error_messages={
            'required': 'Role is required.',
        }
    )
    
    status = forms.TypedChoiceField(
        coerce=lambda x: x == 'True',  # Convert 'True' and 'False' strings to actual booleans
        choices=((True, 'True'), (False, 'False')),
        error_messages={
            'invalid_choice': 'Select a valid status (True or False).',
        }
    )

    def clean_role(self):
        role = self.cleaned_data.get('role')
        allowed_roles = ['Admin', 'Manager', 'Cashier']
        if role not in allowed_roles:
            raise forms.ValidationError('Invalid role. Allowed values are: ' + ', '.join(allowed_roles))
        return role
    
def SaveUser(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    user = authentication.get_account_info(request.session.get('sessionID'))

    local_id = user['users'][0]['localId']

    user_data = db.child("Users").order_by_child("userID").equal_to(local_id).get().val()
    user_data_key = list(user_data.keys())[0]
    request.session['username'] = user_data[user_data_key]['username']
    request.session['role'] = user_data[user_data_key]['role']
    request.session['uid'] = local_id
    request.session['imgsrc'] = user_data[user_data_key]['imgsrc']

    if request.session['role'] != 'Admin':
        raise Http404("You do not have permission to access this page.")
    
    # try:
    if request.method == 'POST':
        form = EditUserForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data

            userKey = request.session['userKey']
            userData = db.child("Users").child(userKey).get().val()

            image_file = request.FILES.get('image')
            imgsrc = userData["imgsrc"]

            uniqueID = userData["imageName"]
            
            if image_file is not None:
                file_extension = get_file_extension(image_file.name)
                if file_extension == '.gif' or is_image(image_file):
                    try:
                        storage.delete("user_profiles/" + uniqueID, request.session['sessionID'])
                    except:
                        pass
                    
                    uniqueID = generate_unique_id()
                    storage.child("user_profiles/" + uniqueID).put(image_file)
                    imgsrc = getImageURL("user_profiles/", uniqueID)
                else:
                    error_message = "Invalid file format."
                    return JsonResponse({"message": "Invalid data", "errors": {"file": [error_message]}}, status=400)

            username = data['username']
            contact = data['contact']
            role = data['role']
            status = data['status']

            updatedData = {
                "username": username,
                "role": role,
                "contact": contact,
                "status": status,
                "imgsrc": imgsrc,
                "imageName" : uniqueID,
            }
            db.child("Users").child(userKey).update(updatedData)

            changed_fields = {}
            field_labels = {
                "username": "Username",
                "contact": "Contact",
                "role": "Role",
                "status": "Status"
            }

            for field, label in field_labels.items():
                if userData[field] != data[field]:
                    changed_fields[label] = {
                        "old": userData[field],
                        "new": data[field]
                    }
                    
            if changed_fields:
                add_system_activities(request, "updated a user", changed_fields)
            return JsonResponse({"message": "User updated successfully"})
        else:
            # Form is not valid, you can access the custom error messages
            errors = {
                'username': form.errors.get('username', [])[0] if 'username' in form.errors else None,
                'contact': form.errors.get('contact', [])[0] if 'contact' in form.errors else None,
                'role': form.errors.get('role', [])[0] if 'role' in form.errors else None,
                'status': form.errors.get('status', [])[0] if 'status' in form.errors else None,
                # Add other fields as needed
            }
            # Filter out None values
            errors = {key: value for key, value in errors.items() if value is not None}
            return JsonResponse({"error": "Form validation failed", "errors": errors}, status=400)
        
    # except Exception as e:
    #     return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)

def restore_data(request):
    try:
        if not request.session.get('sessionID'):
            return redirect('LogIn')

        user = authentication.get_account_info(request.session.get('sessionID'))

        local_id = user['users'][0]['localId']

        user_data = db.child("Users").order_by_child("userID").equal_to(local_id).get().val()
        user_data_key = list(user_data.keys())[0]
        request.session['username'] = user_data[user_data_key]['username']
        request.session['role'] = user_data[user_data_key]['role']
        request.session['uid'] = local_id
        request.session['imgsrc'] = user_data[user_data_key]['imgsrc']

        if request.session['role'] == 'Cashier':
            raise Http404("You do not have permission to access this page.")

        if request.method == 'POST':
            data_key = request.POST.get('dataKey')
            recycle_bin_data = db.child("RecycleBin").child(data_key).get().val()

            if recycle_bin_data:
                original_data = recycle_bin_data['data']
                location = recycle_bin_data['binData']['location']

                item = db.child("Items").order_by_child("itemID").equal_to(original_data["itemID"]).get().val()
                if item:
                    return JsonResponse({"message": "Barcode already exist"})
                else:
                    db.child(location).push(original_data)
                    db.child("RecycleBin").child(data_key).remove()

                    restored_data = {
                        'Item Name': original_data["itemName"],
                        'Barcode': original_data["itemID"],
                    }
                    add_system_activities(request, "restored data", restored_data)
                    return JsonResponse({"message": "Data restored successfully!"})
            else:
                return JsonResponse({"message": "Data not found in the Archive"}, status=404)

        return JsonResponse({"message": "Invalid request method"}, status=400)

    except Exception as e:
        return JsonResponse({"message": "An error occurred", "error": str(e)}, status=500)

def getImageURL(location, imageID):
    url = storage.child(location + imageID).get_url(None)
    return url

def CriticalQuantities(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    user = authentication.get_account_info(request.session.get('sessionID'))

    local_id = user['users'][0]['localId']

    user_data = db.child("Users").order_by_child("userID").equal_to(local_id).get().val()
    user_data_key = list(user_data.keys())[0]
    request.session['username'] = user_data[user_data_key]['username']
    request.session['role'] = user_data[user_data_key]['role']
    request.session['mode'] = user_data[user_data_key]['mode']
    request.session['uid'] = local_id
    request.session['imgsrc'] = user_data[user_data_key]['imgsrc']

    
    ph_timezone = pytz.timezone('Asia/Manila')
    current_date = datetime.now(ph_timezone)
    nega_int = int(current_date.strftime("%Y%m%d%H%M%S")) * -1
    filtered_items = {}
    try:
        filtered_items = {
            key: item for key, item in db.child("Items").order_by_child("negaIntDate").start_at(nega_int).get().val().items()
            if item['itemQuantity'] <= item['itemCriticalQuantity']
        }
    except:
        pass

    filtered_items = dict(islice(filtered_items.items(), 10))

    if filtered_items:
        for item in filtered_items.values():
            try:
                expiry = item.get("expiryDate", [])
                date_list = [{"notify": ex["notify"], "date": ex["date"]} for ex in expiry]
                date_list.sort(key=lambda ex: datetime.strptime(ex["date"], "%Y-%m-%d"))

                expiry_status, first_expiry_date = check_expiry(date_list)

                item["expiryClass"] = expiry_status
                item["expiryDate"] = first_expiry_date

            except Exception as e:
                item["expiryClass"] = ""
                item["expiryDate"] = ""
    
    thread = threading.Thread(target=check_quantities, args=(5,))
    thread.start()

    data = {
        "Title": "Critical Quantities",
        "User": request.session.get('username', ''),
        "imageURL" : request.session['imgsrc'],
        "CriticalList": filtered_items,
        "itemClass": True,
        "role" : request.session['role'],
        "mode" : request.session['mode'],
    }
    return render(request, "personalTemplates/CriticalQuantities.html", data)


def AboutToExpire(request):
    if not request.session.get('sessionID'):
        return redirect('LogIn')
    
    user = authentication.get_account_info(request.session.get('sessionID'))

    local_id = user['users'][0]['localId']

    user_data = db.child("Users").order_by_child("userID").equal_to(local_id).get().val()
    user_data_key = list(user_data.keys())[0]
    request.session['username'] = user_data[user_data_key]['username']
    request.session['role'] = user_data[user_data_key]['role']
    request.session['mode'] = user_data[user_data_key]['mode']
    request.session['uid'] = local_id
    request.session['imgsrc'] = user_data[user_data_key]['imgsrc']
    
    ph_timezone = pytz.timezone('Asia/Manila')
    current_date = datetime.now(ph_timezone)
    nega_int = int(current_date.strftime("%Y%m%d%H%M%S")) * -1
    item_list = db.child("Items").order_by_child("negaIntDate").start_at(nega_int).get().val()
    filtered_items = {}
    
    if item_list:
        for key, item in item_list.items():
            try:
                if item["itemQuantity"] <= item["itemCriticalQuantity"]:
                    item["itemClass"] = "danger"
                elif item["itemQuantity"] > item["itemMaxQuantity"]:
                    item["itemClass"] = "warning"
                else:
                    item["itemClass"] = ""
            
                expiry = item.get("expiryDate", [])
                date_list = [{"notify": ex["notify"], "date": ex["date"]} for ex in expiry]
                date_list.sort(key=lambda ex: datetime.strptime(ex["date"], "%Y-%m-%d"))

                if expiry:
                    expiry_status, first_expiry_date = check_expiry(date_list)
                
                    if expiry_status != "notExpired":
                        item["expiryClass"] = expiry_status
                        item["expiryDate"] = first_expiry_date
                        filtered_items[key] = item

            except Exception as e:
                pass

    filtered_items = dict(islice(filtered_items.items(), 10))

    thread = threading.Thread(target=check_quantities, args=(5,))
    thread.start()

    data = {
        "Title": "About To Expire",
        "User": request.session['username'],
        "imageURL" : request.session['imgsrc'],
        "AboutToExpire": filtered_items,
        "itemClass": True,
        "role" : request.session['role'],
        "mode" : request.session['mode'],
    }
    
    return render(request, "personalTemplates/AboutToExpire.html", data)

def getItemData(request):
    item_list = db.child("Items").get().val()
    return JsonResponse(item_list)

# FOR SENDING EMAILS
def voided_transaction_message(transaction_id, remarks):
    current_date = str(date.today())
    ph_timezone = pytz.timezone('Asia/Manila')

    current_date_time_ph = datetime.now(ph_timezone)
    current_time_ph = current_date_time_ph.strftime("%I:%M %p")

    subject = "Transaction Voided - Important Notification"
    
    message = f"""
Automated System Notification:

This message serves as an alert for a recently voided transaction:

Transaction ID: {transaction_id}
Voided Date: {current_date + " " + current_time_ph}
Remarks: {remarks}

Please review the voided transaction and take any necessary actions.

Thank you for your attention.

Best regards,

MXGM
Date: {current_date}
Time: {current_time_ph}
"""

    return subject, message

def email_expiry_contents(expiry_datelist):
    current_date = str(date.today())
    ph_timezone = pytz.timezone('Asia/Manila')

    current_date_time_ph = datetime.now(ph_timezone)
    current_time_ph = current_date_time_ph.strftime("%I:%M %p")

    subject = "Inventory Alert - Expiry Notification"
    
    message = """
Automated System Notification:

This message serves as an alert for items that are about to expire or have already expired:

"""

    for entry in expiry_datelist:
        item_name = entry['item_name']
        expired_items = entry['expired']
        about_to_expire_items = entry['about_to_expire']

        if expired_items:
            message += f"{item_name} - Expired Items:\n"
            for item in expired_items:
                expiry_date = item['date'].strftime("%Y-%m-%d")
                message += f"""
Expiry Date: {expiry_date}
Status: EXPIRED
-------------------------
"""

        if about_to_expire_items:
            message += f"{item_name} - About to Expire Items:\n"
            for item in about_to_expire_items:
                expiry_date = item['date'].strftime("%Y-%m-%d")
                within_days = item['within_days']
                message += f"""
Expiry Date: {expiry_date}
Status: About to expire {within_days}
-------------------------
"""

    message += f"""
Timely action is advised to manage these items efficiently. Please review and address this matter promptly to ensure product quality and customer satisfaction.

Thank you for your attention.

Best regards,

MXGM
Date: {current_date}
Time: {current_date_time_ph}
"""

    return subject, message

def email_critical_contents(items):
    current_date = str(date.today())
    ph_timezone = pytz.timezone('Asia/Manila')

    current_date_time_ph = datetime.now(ph_timezone)
    current_time_ph = current_date_time_ph.strftime("%I:%M %p")

    subject = "Inventory Alert - Critical Quantity"
    
    message = """
Automated System Notification:

This message serves as an alert that the inventory levels have reached a critical quantity threshold for the following items:
"""

    for item in items:
        item_name = item['item_name']
        current_quantity = item['current_quantity']
        critical_quantity = item['critical_quantity']

        message += f"""
Item: {item_name}
Current Quantity: {current_quantity}
Critical Quantity: {critical_quantity}
-------------------------
"""

    message += f"""
Timely action is advised to prevent any potential disruptions in the supply chain. Please review and address this matter promptly to maintain operational efficiency.

Thank you for your attention.

Best regards,

MXGM
Date: {current_date}
Time: {current_time_ph}
"""

    return subject, message

def email_overstocked_contents(items):
    current_date = str(date.today())
    ph_timezone = pytz.timezone('Asia/Manila')

    current_date_time_ph = datetime.now(ph_timezone)
    current_time_ph = current_date_time_ph.strftime("%I:%M %p")

    subject = "Inventory Alert - Overstocked Quantity"
    
    message = """
Automated System Notification:

This message serves as an alert that the inventory levels have exceeded the acceptable quantity threshold for the following items:

"""

    for item in items:
        item_name = item['item_name']
        current_quantity = item['current_quantity']
        overstocked_quantity = item['overstocked_quantity']

        message += f"""
Item: {item_name}
Current Quantity: {current_quantity}
Critical Quantity: {overstocked_quantity}
-------------------------
"""

    message += f"""
Timely action is advised to manage the excess inventory efficiently. Please review and address this matter promptly to optimize inventory levels.

Thank you for your attention.

Best regards,

MXGM
Date: {current_date}
Time: {current_time_ph}
"""

    return subject, message

def check_all_expiry(expiry_dates):
    current_date = datetime.now()
    
    expired_dates = []
    about_to_expire_dates = []
    earliest_expiry_date = None
    
    for expiry_date in expiry_dates:
        date = datetime.strptime(expiry_date["date"], "%Y-%m-%d")
        notify_days = int(expiry_date["notify"])
        threshold_date = date - timedelta(days=notify_days)
        
        if current_date >= date:
            expired_dates.append({
                'date': date,
                'expiry_status' : "EXPIRED"
            })
        elif current_date >= threshold_date:
            days_until_expiry = (date - current_date).days
            about_to_expire_dates.append({
                'date': date,
                'expiry_status': "About to expire",
                'within_days': f'in {days_until_expiry} days',
            })
        
        if not earliest_expiry_date or date < earliest_expiry_date:
            earliest_expiry_date = date
    
    return expired_dates, about_to_expire_dates

def check_quantities(delay):
    time.sleep(delay)
    item_list = db.child("Items").get().val()

    critical_items = []
    overstocked_items = []
    expiry_datelist = []
    item_updates = {}

    if item_list:
        for key, item_data in item_list.items():
            
            item_name = item_data["itemName"]
            item_quantity = int(item_data["itemQuantity"])
            critical_quantity = int(item_data['itemCriticalQuantity'])
            max_quantity = int(item_data['itemMaxQuantity'])
            critical_notif = item_data["criticalNotif"]
            overstocked_notif = item_data["overStockNotif"]
            expiry_notif = item_data["expiryNotif"]

            if item_quantity <= critical_quantity and critical_notif:
                critical_items.append({
                    'item_name': item_name,
                    'current_quantity': item_quantity,
                    'critical_quantity': critical_quantity
                })
                critical_notif = False
            elif item_quantity > max_quantity and overstocked_notif:
                overstocked_items.append({
                    'item_name': item_name,
                    'current_quantity': item_quantity,
                    'overstocked_quantity': max_quantity
                })
                overstocked_notif = False
            
            expiry = item_data.get("expiryDate", [])
            date_list = [{"notify": ex["notify"], "date": ex["date"]} for ex in expiry]
            date_list.sort(key=lambda ex: datetime.strptime(ex["date"], "%Y-%m-%d"))
            
            expired, about_to_expire = check_all_expiry(date_list)
            if (expired or about_to_expire) and expiry_notif:
                expiry_datelist.append({
                    'item_name': item_name,
                    'about_to_expire': about_to_expire,
                    'expired': expired
                })
                expiry_notif = False

            item_updates[key] = {
                "criticalNotif": critical_notif,
                "overStockNotif": overstocked_notif,
                "expiryNotif": expiry_notif,
            }

        if expiry_datelist:
            subject, message = email_expiry_contents(expiry_datelist)
            send_email(subject, message)

        if critical_items:
            subject, message = email_critical_contents(critical_items)
            send_email(subject, message)

        if overstocked_items:
            subject, message = email_overstocked_contents(overstocked_items)
            send_email(subject, message)

        for item_key, update_data in item_updates.items():
            db.child("Items").child(item_key).update(update_data)

def color_modes(request):
    try:
        if not request.session.get('sessionID'):
            return redirect('LogIn')
        
        user = authentication.get_account_info(request.session.get('sessionID'))
        local_id = user['users'][0]['localId']
        user_data = db.child("Users").order_by_child("userID").equal_to(local_id).get().val()

        user_data_key = list(user_data.keys())[0]

        request.session['username'] = user_data[user_data_key]['username']
        request.session['role'] = user_data[user_data_key]['role']
        request.session['uid'] = local_id
        request.session['imgsrc'] = user_data[user_data_key]['imgsrc']

        if request.method == 'POST':
            mode = request.POST.get('mode')
            db.child("Users").child(user_data_key).update({"mode": mode})
            return JsonResponse({"status": "success"})
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    