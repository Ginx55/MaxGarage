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
  databaseURL: "https://max-web-8f968-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "max-web-8f968",
  storageBucket: "max-web-8f968.appspot.com",
  messagingSenderId: "222284867736",
  appId: "1:222284867736:web:cc6f2bc627da9bc1ae08ed"
};
const app = initializeApp(firebaseConfig);

const db = getDatabase();
const reference = ref(db, "RecycleBin/");

function insertDetails(key, value) {
  const td = document.createElement("td");
  const span = document.createElement("span");

  $(span).text(value);
  span.className = "danger";
  span.addEventListener("click", function () {
    restoreData(key);
  });

  td.appendChild(span);
  return td;
}

function insertDataToTable(value) {
  const td = document.createElement("td");
  $(td).text(value);
  return td;
}

let now = push(child(ref(db), "RecycleBin")).key;
const queryData = query(reference, orderByKey(), startAt(now));
onChildAdded(queryData, (data) => {
  const tr = document.createElement("tr");
  tr.setAttribute("id", data.key + "0");

  tr.appendChild(insertDataToTable(data.val().data.binData.ID));
  tr.appendChild(insertDataToTable(data.val().data.binData.itemName));
  tr.appendChild(insertDataToTable(data.val().data.binData.location));
  tr.appendChild(insertDataToTable(data.val().data.binData.date));

  tr.appendChild(insertDetails(data.key, "Restore"));

  document.querySelector("table tbody").prepend(tr);
});

onChildRemoved(reference, (data) => {
  let element = document.getElementById(data.key + "0");
  if (element != null) {
    element.remove();
  }
});
