import { initializeApp } from "https://www.gstatic.com/firebasejs/10.1.0/firebase-app.js";
import {
  getDatabase,
  ref,
  onChildChanged,
  onChildAdded,
  query,
  startAt,
  push,
  child,
  orderByKey,
  orderByChild,
  equalTo,
  get,
} from "https://www.gstatic.com/firebasejs/10.1.0/firebase-database.js";

const firebaseConfig = {
  apiKey: "AIzaSyAKBm5kuT0f-hwVg3ecC6SjZTE4MMxfRi4",
  authDomain: "maxweb-5ea84.firebaseapp.com",
  databaseURL:
    "https://maxweb-5ea84-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "maxweb-5ea84",
  storageBucket: "maxweb-5ea84.appspot.com",
  messagingSenderId: "765328893873",
  appId: "1:765328893873:web:9546126eb532e9165fff90",
};
const app = initializeApp(firebaseConfig);

const db = getDatabase();
const returnRef = ref(db, "Return");

let now = push(child(ref(db), "Return")).key;
const returnedQuery = query(
  returnRef,
  orderByChild("status"),
  equalTo("returned to supplier")
);

let returnCount = 0;
get(returnedQuery)
  .then((data) => {
    if (data.exists()) {
      returnCount = Object.keys(data.val()).length;
      $("#returnedItems").text(returnCount);
    }
  })
  .catch((error) => {
    console.error(error);
  });

const returnQuery = query(returnRef, orderByKey(), startAt(now));
onChildAdded(returnQuery, (data) => {
  if (data.val().status != "received") {
    returnCount += 1;
    $("#returnedItems").text(returnCount);
  }
});

onChildChanged(returnRef, (data) => {
  if (data.val().status == "received") {
    returnCount -= 1;
    $("#returnedItems").text(returnCount);
  }
});

function checkExpiry(currentDate, expiryDate, notifyDate, key) {
  let expiry = new Date(expiryDate);
  let notify = Number(notifyDate);
  let newExpiry = new Date(expiry.setDate(expiry.getDate() - notify));

  if (currentDate >= newExpiry) {
    if (expiredKeys.includes(key) == false) {
      return true;
    } else {
      return false;
    }
  }
}

const itemsRef = ref(db, "Items");
let critKeys = [];
let overKeys = [];
let expiredKeys = [];
let critQuan = 0;
let overQuan = 0;
let expiredQuan = 0;
get(itemsRef)
  .then((data) => {
    if (data.exists()) {
      for (let key in data.val()) {
        let quantity = data.val()[key]["itemQuantity"];
        let criticalQuantity = data.val()[key]["itemCriticalQuantity"];
        let overQuantity = data.val()[key]["itemMaxQuantity"];

        if (quantity <= criticalQuantity) {
          critKeys.push(key);
          critQuan++;
        }
        if (quantity > overQuantity) {
          overKeys.push(key);
          overQuan++;
        }
        if (typeof data.val()[key]["expiryDate"] != "undefined") {
          const currentDate = new Date();
          let expiryDate = data.val()[key]["expiryDate"];
          for (let x = 0; x < expiryDate.length; x++) {
            let expiry = expiryDate[x]["date"];
            let notify = expiryDate[x]["notify"];
            if (checkExpiry(currentDate, expiry, notify, key)) {
              expiredKeys.push(key);
              expiredQuan++;
              break;
            }
          }
        }
      }
      $("#criticalStock").text(critQuan);
      $("#overStocked").text(overQuan);
      $("#aboutToExpire").text(expiredQuan);
    }
  })
  .catch((error) => {
    console.error(error);
  });

onChildChanged(itemsRef, (data) => {
  if (critKeys.includes(data.key)) {
    if (data.val().itemQuantity >= data.val().itemCriticalQuantity) {
      critKeys.splice(critKeys.indexOf(data.key), 1);
      critQuan -= 1;
    }
  } else {
    if (data.val().itemQuantity <= data.val().itemCriticalQuantity) {
      critKeys.push(data.key);
      critQuan += 1;
    }
  }

  if (overKeys.includes(data.key)) {
    if (data.val().itemQuantity <= data.val().itemMaxQuantity) {
      overKeys.splice(overKeys.indexOf(data.key), 1);
      overQuan -= 1;
    }
  } else {
    if (data.val().itemQuantity > data.val().itemMaxQuantity) {
      overKeys.push(data.key);
      overQuan += 1;
    }
  }

  if (expiredKeys.includes(data.key)) {
    let expiredCounter = 0;
    if (typeof data.val()["expiryDate"] != "undefined") {
      const currentDate = new Date();
      let expiryDate = data.val()["expiryDate"];

      for (let x = 0; x < expiryDate.length; x++) {
        let expiry = expiryDate[x]["date"];
        let notify = expiryDate[x]["notify"];
        if (checkExpiry(currentDate, expiry, notify, data.key)) {
          expiredCounter++;
        }
      }
      if (expiredCounter <= 0) {
        expiredKeys.splice(expiredKeys.indexOf(data.key), 1);
        expiredQuan -= 1;
      }
    } else {
      expiredKeys.splice(expiredKeys.indexOf(data.key), 1);
      expiredQuan -= 1;
    }
  } else {
    if (typeof data.val()["expiryDate"] != "undefined") {
      const currentDate = new Date();
      let expiryDate = data.val()["expiryDate"];

      for (let x = 0; x < expiryDate.length; x++) {
        let expiry = expiryDate[x]["date"];
        let notify = expiryDate[x]["notify"];

        if (checkExpiry(currentDate, expiry, notify, data.key)) {
          expiredKeys.push(data.key);
          expiredQuan++;
          break;
        }
      }
    }
  }

  $("#criticalStock").text(critQuan);
  $("#overStocked").text(overQuan);
  $("#aboutToExpire").text(expiredQuan);
});

function insertDetails(key, value) {
  const td = document.createElement("td");
  const span = document.createElement("span");

  $(span).text(value);
  span.className = "primary";
  span.addEventListener("click", function () {
    viewDetails(key);
  });

  td.appendChild(span);
  return td;
}

function insertDataToTable(value, status) {
  const td = document.createElement("td");
  $(td).text(value);
  if (status) {
    if (value == "Paid") {
      td.className = "success";
    } else {
      td.className = "danger";
    }
  }
  return td;
}

const logRef = ref(db, "TransactionLog");
const logQuery = query(logRef, orderByKey(), startAt(now));
onChildAdded(logQuery, (data) => {
  var rowCount = $("#reportTable tr").length - 1;
  if (rowCount == 5) {
    $("#reportTable").find("tr:last").remove();
  }

  const tr = document.createElement("tr");

  tr.appendChild(insertDataToTable(data.val().transactionID));
  tr.appendChild(insertDataToTable(data.val().currentDate));
  tr.appendChild(insertDataToTable(data.val().currentTime));
  tr.appendChild(insertDataToTable(data.val().status, true));
  tr.appendChild(insertDataToTable(data.val().totalPrice));
  tr.appendChild(insertDetails(data.key, "Details"));

  document.querySelector("#reportTable tbody").prepend(tr);
});

// const actRef = ref(db, "SystemActivities");
// const actQuery = query(actRef, orderByKey(), startAt(now));
// onChildAdded(actQuery, (data) => {
//   var rowCount = $("#updateData div").length;
//   if (rowCount >= 9) {
//     $("#updateData").find("div:last").remove();
//     $("#updateData").find("div:last").remove();
//     $("#updateData").find("div:last").remove();
//   }

//   const divData = document.createElement("div");
//   divData.className = "update";

//   const divImage = document.createElement("div");
//   divImage.className = "profile-photo";

//   const image = document.createElement("img");
//   divImage.appendChild(image);
//   image.setAttribute("src" , data.val().imgsrc);
//   const divMessage = document.createElement("div");
//   divMessage.className = "message";

//   const p = document.createElement("p");
//   const b = document.createElement("b");
//   const text = document.createTextNode(data.val().actionsMade);
//   $(b).text(data.val().currentUser);

//   p.appendChild(b);
//   p.appendChild(text);

//   const small = document.createElement("small");
//   small.className = "text-muted";
//   $(small).text("2 Minutes Ago");

//   divMessage.appendChild(p);
//   divMessage.appendChild(small);

//   divData.appendChild(divImage);
//   divData.appendChild(divMessage);

//   document.querySelector("#updateData").prepend(divData);
// });

const reference = ref(db, "Items/");
function addTableItemClass(itemData) {
  const { itemQuantity, itemCriticalQuantity, itemMaxQuantity } = itemData;
  let className = "";
  if (itemQuantity <= itemCriticalQuantity) {
    className = "danger";
  } else if (itemQuantity > itemMaxQuantity) {
    className = "warning";
  }
  return className;
}

function expiryDataChecker(expiryDateParams) {
  const expiryList = expiryDateParams.map((expiryData) => ({
    notify: Number(expiryData.notify),
    date: new Date(expiryData.date),
  }));

  expiryList.sort((date1, date2) => date1.date - date2.date);

  let firstAboutToExpire = null;
  let className = null;

  if (expiryList.length > 0) {
    const today = new Date();

    for (const expiryData of expiryList) {
      const expiryDate = expiryData.date.toISOString().slice(0, 10);

      if (expiryData.date > today) {
        const aboutToExpire = new Date(expiryData.date);
        aboutToExpire.setDate(aboutToExpire.getDate() - expiryData.notify);

        if (
          aboutToExpire <= today &&
          (!firstAboutToExpire || expiryData.date > firstAboutToExpire)
        ) {
          className = "warning";
          firstAboutToExpire = expiryDate;
        }
      } else {
        className = "danger";
        if (!firstAboutToExpire || expiryData.date > firstAboutToExpire) {
          firstAboutToExpire = expiryDate;
        }
      }
    }

    if (!firstAboutToExpire) {
      firstAboutToExpire = expiryList[0].date.toISOString().slice(0, 10);
    }
  } else {
    firstAboutToExpire = "";
  }

  let dataObject = {
    expiry: firstAboutToExpire,
    class: className,
  };

  return dataObject;
}

onChildChanged(reference, (data) => {
  const itemData = data.val();

  const quantityClass = addTableItemClass(itemData);
  if (quantityClass == "danger" && itemData.criticalNotif) {
    showAlert(
      "error",
      "An item has reached a critical level",
      itemData.criticalNotif
    );
  } else if (quantityClass == "warning" && itemData.overStockNotif) {
    showAlert(
      "warning",
      "An item has reached an overstocked level",
      itemData.overStockNotif
    );
  }
});
