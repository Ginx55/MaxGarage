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
const reference = ref(db, "Return/");

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

function insertDataToTable(key, value) {
  const td = document.createElement("td");
  if (value == "received") {
    td.className = "success";
  }
  if (value == "return outwards") {
    td.className = "danger";
  }
  $(td).text(value);
  td.setAttribute("id", key);
  return td;
}

let now = push(child(ref(db), "Return")).key;
const queryData = query(reference, orderByKey(), startAt(now));
onChildAdded(queryData, (data) => {
  var rowCount = $("#returnTable tr").length - 1;
  if (rowCount == 10) {
    $("#returnTable").find("tr:last").remove();
  }

  const tr = document.createElement("tr");

  tr.appendChild(insertDataToTable(data.key + "0", data.val().transactionID));
  tr.appendChild(insertDataToTable(data.key + "1", data.val().itemName));
  tr.appendChild(insertDataToTable(data.key + "6", data.val().currentUser));
  tr.appendChild(insertDataToTable(data.key + "2", data.val().currentDate));
  tr.appendChild(insertDataToTable(data.key + "3", data.val().currentTime));
  tr.appendChild(
    insertDataToTable(data.key + "4", data.val().returnedQuantity)
  );
  tr.appendChild(insertDataToTable(data.key + "5", data.val().status));

  tr.appendChild(insertDetails(data.key, "Details"));

  document.querySelector("#returnTable tbody").prepend(tr);
});

onChildChanged(reference, (data) => {
  let details = document.getElementById(data.key + "0");
  if (details != null) {
    if (data.val().status == "received") {
      $("#" + data.key + "5").removeClass("danger");
      $("#" + data.key + "5").addClass("success");
      $("#" + data.key + "5").text(data.val().status);
    }else{
      $("#" + data.key + "5").removeClass("success");
      $("#" + data.key + "5").addClass("danger");
      $("#" + data.key + "5").text(data.val().status);
    }
  }
});
