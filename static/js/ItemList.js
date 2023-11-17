import { initializeApp } from "https://www.gstatic.com/firebasejs/10.1.0/firebase-app.js";
import {
  getDatabase,
  ref,
  onChildChanged,
  onChildAdded,
  onChildRemoved,
  query,
  startAt,
  push,
  child,
  orderByKey,
} from "https://www.gstatic.com/firebasejs/10.1.0/firebase-database.js";

const firebaseConfig = {
  apiKey: "AIzaSyAGnYk6RTT0-1il6BqNKfF60QN2ctEmTlk",
  authDomain: "max-web-8f968.firebaseapp.com",
  databaseURL:
    "https://max-web-8f968-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "max-web-8f968",
  storageBucket: "max-web-8f968.appspot.com",
  messagingSenderId: "222284867736",
  appId: "1:222284867736:web:cc6f2bc627da9bc1ae08ed",
};
const app = initializeApp(firebaseConfig);

const db = getDatabase();
const reference = ref(db, "Items/");

function createTableCell(value, id) {
  const td = document.createElement("td");
  td.textContent = value;
  if (id) {
    td.setAttribute("id", id);
  }
  return td;
}

function createDetailsCell(key) {
  const td = document.createElement("td");
  const span = document.createElement("span");
  span.textContent = "Details";
  span.className = "primary";
  span.addEventListener("click", () => {
    editItem(key);
  });
  td.appendChild(span);
  return td;
}

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

function formatPrice(price) {
  return price % 1 === 0 ? price.toFixed(1) : price;
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

function addItemToTable(data) {
  const rowCount = document.querySelectorAll("#itemTable tr").length - 1;
  if (rowCount === 10) {
    document.querySelector("#itemTable tr:last-child").remove();
  }
  const itemData = data.val();
  const tr = document.createElement("tr");
  tr.setAttribute("id", data.key + "0");

  tr.appendChild(createTableCell(itemData.itemID, data.key + "1"));
  tr.appendChild(createTableCell(itemData.itemName, data.key + "2"));

  const itemQuantity = createTableCell(itemData.itemQuantity, data.key + "3");
  itemQuantity.className = addTableItemClass(itemData);
  tr.appendChild(itemQuantity);

  tr.appendChild(
    createTableCell(formatPrice(parseFloat(itemData.itemPrice)), data.key + "4")
  );

  if (itemData.expiryDate) {
    const dataObject = expiryDataChecker(itemData.expiryDate);
    const expiryElement = createTableCell(dataObject.expiry, data.key + "5");
    expiryElement.className = dataObject.class;

    tr.appendChild(expiryElement);
  } else {
    tr.appendChild(createTableCell("", data.key + "5"));
  }

  tr.appendChild(createDetailsCell(data.key));

  document.querySelector("#itemTable tbody").prepend(tr);
}

const now = push(child(ref(db), "Items")).key;
const queryData = query(reference, orderByKey(), startAt(now));
onChildAdded(queryData, (data) => {
  addItemToTable(data);
});

onChildChanged(reference, (data) => {
  const key = "#" + data.key;
  const itemData = data.val();

  $(key + "1").text(itemData.itemID);
  $(key + "2").text(itemData.itemName);
  const itemQuantity = $(key + "3").removeClass("danger warning");
  itemQuantity.addClass(addTableItemClass(itemData));

  if (itemData.expiryDate) {
    const expiryElement = $(key + "5").removeClass("danger warning");

    const dataObject = expiryDataChecker(itemData.expiryDate);
    expiryElement.addClass(dataObject.class);
    expiryElement.text(dataObject.expiry);
  } else {
    $(key + "5")
      .removeClass("danger warning")
      .text("");
  }

  $(key + "4").text(formatPrice(parseFloat(itemData.itemPrice)));
  $(key + "3").text(itemData.itemQuantity);
});

onChildRemoved(reference, (data) => {
  const element = document.getElementById(data.key + "0");
  if (element !== null) {
    element.remove();
  }
});
