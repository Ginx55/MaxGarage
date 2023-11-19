"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from website import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication
    path('', views.login, name="LogIn"),
    path('ForgotPass/', views.ForgotPass, name="ForgotPass"),
    path('send_forgot_pass/', views.send_forgot_pass, name="send_forgot_pass"),

    # Dashboard
    path('Dashboard/', views.Dashboard, name="Dashboard"),

    # SalesLink
    path('TransactionLog/', views.TransactionLog, name="TransactionLog"),
    path('TransactionDetails/', views.TransactionDetails, name="TransactionDetails"),
    path('VoidedDetails/', views.VoidedDetails, name="VoidedDetails"),
    path('PurchaseTransaction/', views.PurchaseTransaction, name="PurchaseTransaction"),
    path('SearchItem/', views.SearchItem, name="SearchItem"),
    path('InsertTransaction/', views.insert_transaction, name="InsertTransaction"),
    path('VoidedTransactions/', views.VoidedTransactions, name="VoidedTransactions"),
    path('ReturnToInventory/', views.ReturnToInventory, name="ReturnToInventory"),
    path('VoidTransaction/', views.VoidTransaction, name="VoidTransaction"),
    path('GetSalesReport/', views.GetSalesReport, name="GetSalesReport"),

    # Inventory
    path('ItemList/', views.item_list, name="ItemList"),
    path('EditItem/', views.EditItem, name="EditItem"),
    path('SaveEditItem/', views.save_edit_item, name="SaveEditItem"),
    path('RemoveItem/', views.remove_item, name="RemoveItem"),

    # Return
    path('Return/', views.Return, name="Return"),
    path('SearchTransactions/', views.SearchTransactions, name="SearchTransactions"),
    path('ReturnDetails/', views.ReturnDetails, name="ReturnDetails"),
    path('ItemReceived/', views.ItemReceived, name="ItemReceived"),
    path('InsertReturn/', views.insert_return, name="InsertReturn"),

    # SystemActivities
    path('SystemActivities/', views.SystemActivities, name="SystemActivities"),
    path('ViewSystemActivities/', views.ViewSystemActivities, name="ViewSystemActivities"),

    # Recycle Bin
    path('RecycleBin/', views.RecycleBin, name="RecycleBin"),
    path('RestoreData/', views.restore_data, name="RestoreData"),

    # Userlist
    path('UserList/', views.UserList, name="UserList"),
    path('SearchUser/', views.SearchUser, name="SearchUser"),
    path('UserList/SaveUser/', views.SaveUser, name="SaveUser"),
    path('UserList/AddUser/', views.AddUser, name="AddUser"),

    # Other Paths
    path('AddItem/', views.add_item, name="AddItem"),
    path('CriticalQuantities/', views.CriticalQuantities, name="CriticalQuantities"),
    path('AboutToExpire/', views.AboutToExpire, name="AboutToExpire"),
    path('getItemData/', views.getItemData, name="getItemData"),

    path('color-mode/', views.color_modes, name="color_modes"),
]
