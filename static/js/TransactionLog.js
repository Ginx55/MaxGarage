import { initializeApp } from "https://www.gstatic.com/firebasejs/10.1.0/firebase-app.js";
import {
  getDatabase,
  ref,
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
const reference = ref(db, "TransactionLog/");

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
  let textValue = document.createTextNode(value);
  if (status) {
    td.className = "success";
  }
  td.appendChild(textValue);
  return td;
}

let now = push(child(ref(db), "TransactionLog")).key;
const queryData = query(reference, orderByKey(), startAt(now));
onChildAdded(queryData, (data) => {
  var rowCount = $("#reportTable tr").length - 1;
  if (rowCount == 10) {
    $("#reportTable").find("tr:last").remove();
  }

  const tr = document.createElement("tr");
  tr.setAttribute("id", data.key + "0");

  tr.appendChild(insertDataToTable(data.val().transactionID));
  tr.appendChild(insertDataToTable(data.val().currentDate));
  tr.appendChild(insertDataToTable(data.val().currentTime));
  tr.appendChild(insertDataToTable(data.val().currentUser));
  tr.appendChild(insertDataToTable(data.val().status, true));
  tr.appendChild(insertDataToTable(data.val().totalPrice));
  tr.appendChild(insertDetails(data.key, "Details"));

  document.querySelector("table tbody").prepend(tr);
});

onChildRemoved(reference, (data) => {
  let element = document.getElementById(data.key + "0");
  if (element != null) {
    element.remove();
  }
});
