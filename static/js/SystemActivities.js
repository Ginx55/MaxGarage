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
  databaseURL: "https://max-web-8f968-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "max-web-8f968",
  storageBucket: "max-web-8f968.appspot.com",
  messagingSenderId: "222284867736",
  appId: "1:222284867736:web:cc6f2bc627da9bc1ae08ed"
};
const app = initializeApp(firebaseConfig);

const db = getDatabase();
const reference = ref(db, "SystemActivities/");

function insertDataToTable(value) {
  const td = document.createElement("td");
  $(td).text(value);

  if (value.includes("added") || value.includes("restored")) {
    $(td).addClass("success");
  } else if (value.includes("update")) {
    $(td).addClass("warning");
  }
  else if (value.includes("removed")) {
    $(td).addClass("danger");
  }

  return td;
}

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

let now = push(child(ref(db), "SystemActivities")).key;
const queryData = query(reference, orderByKey(), startAt(now));
onChildAdded(queryData, (data) => {
  var rowCount = $("#activityTable tr").length - 1;
  if (rowCount == 10) {
    $("#activityTable").find("tr:last").remove();
  }
  const tr = document.createElement("tr");

  tr.appendChild(insertDataToTable(data.val().dateCreated));
  tr.appendChild(insertDataToTable(data.val().timeCreated));
  tr.appendChild(insertDataToTable(data.val().role));
  tr.appendChild(insertDataToTable(data.val().currentUser));
  tr.appendChild(insertDataToTable(data.val().actionsMade));

  tr.appendChild(insertDetails(data.key, "Details"));

  document.querySelector("table tbody").prepend(tr);
});
