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
const reference = ref(db, "Users");

function insertDetails(key, value) {
  const td = document.createElement("td");
  const span = document.createElement("span");
  $(span).text(value);

  span.className = "primary";
  span.addEventListener("click", function () {
    editUser(key);
  });

  td.appendChild(span);
  return td;
}

function insertDataToTable(key, value) {
  const td = document.createElement("td");
  $(td).text(value);
  td.setAttribute("id", key);
  return td;
}

let now = push(child(ref(db), "Users")).key;
const queryData = query(reference, orderByKey(), startAt(now));
onChildAdded(queryData, (data) => {
  var rowCount = $("#userTable tr").length - 1;
  if (rowCount == 10) {
    $("#userTable").find("tr:last").remove();
  }
  const tr = document.createElement("tr");
  
  tr.appendChild(insertDataToTable(data.key + "0", data.val().dateCreated));
  tr.appendChild(insertDataToTable(data.key + "1", data.val().username));
  tr.appendChild(insertDataToTable(data.key + "2", data.val().role));
  tr.appendChild(insertDataToTable(data.key + "3", data.val().email));
  tr.appendChild(insertDataToTable(data.key + "4", data.val().contact));

  tr.appendChild(insertDetails(data.key, "Details"));

  document.querySelector("#userTable tbody").prepend(tr);
});

onChildChanged(reference, (data) => {
  let details = document.getElementById(data.key + "0");
  if (details != null) {
    let key = "#" + data.key;
    $(key + "0").text(data.val().dateCreated);
    $(key + "1").text(data.val().username);
    $(key + "2").text(data.val().role);
    $(key + "3").text(data.val().email);
    $(key + "4").text(data.val().contact);
  }
});
