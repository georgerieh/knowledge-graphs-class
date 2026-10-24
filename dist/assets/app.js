// Source - https://stackoverflow.com/q/71506410
// Posted by EricVallieres
// Retrieved 2026-10-24, License - CC BY-SA 4.0
const url = new URL("http://localhost:8000");
function flattenObject(obj, prefix = "") {
  let flattened = {};

  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      const newKey = prefix ? `${prefix}.${key}` : key;
      const value = obj[key];

      if (
        value !== null &&
        typeof value === "object" &&
        !Array.isArray(value)
      ) {
        Object.assign(flattened, flattenObject(value, newKey));
      } else {
        flattened[newKey] = value;
      }
    }
  }
  return flattened;
}
function jsonToTableParser(inputData) {
  let jsonData = inputData;

  if (typeof inputData === "string") {
    try {
      jsonData = JSON.parse(inputData);
    } catch (error) {
      console.error("Invalid JSON string:", error);
      jsonData = [];
    }
  }

  if (!Array.isArray(jsonData) || jsonData.length === 0) {
    const table = document.createElement("table");
    const row = table.insertRow();
    const cell = row.insertCell();
    cell.textContent = "No data available or invalid JSON";
    return table;
  }
  const flattenedData = jsonData.map((item) => {
    return item && typeof item === "object"
      ? flattenObject(item)
      : { value: item };
  });

  const keysSet = new Set();
  flattenedData.forEach((item) => {
    if (item && typeof item === "object") {
      Object.keys(item).forEach((key) => keysSet.add(key));
    }
  });
  const headers = Array.from(keysSet);

  const table = document.createElement("table");
  table.className = "json-data-table";

  const thead = table.createTHead();
  const tbody = table.createTBody();

  const headerRow = thead.insertRow();
  headers.forEach((headerKey) => {
    const th = document.createElement("th");
    th.textContent = headerKey.replace(/^n\./, "").toUpperCase();
    headerRow.appendChild(th);
  });

  flattenedData.forEach((item) => {
    const row = tbody.insertRow();
    headers.forEach((headerKey) => {
      const td = row.insertCell();
      const value = item[headerKey];

      if (value !== null && value !== undefined) {
        const tempDiv = document.createElement("div");
        tempDiv.innerHTML = String(value);
        td.textContent = tempDiv.textContent || tempDiv.innerText || value;
      } else {
        td.textContent = "—";
        td.className = "empty-cell";
      }
    });
  });

  return table;
}

async function dosearch(event) {
  if (event) event.preventDefault();
  const activeForm = document.querySelector(
    '.tabcontent[style*="display: block"] form',
  );
  const select = activeForm.querySelector('select[name="sengines"]');
  const input = activeForm.querySelector('input[type="text"]');
  const queryUrl = url + select.value + encodeURIComponent(input.value);
  if (select.value == "api/networking?val=") {
    queryUrl =
      url +
      "api/networking?" +
      "id1=" +
      input.value.split(",")[0] +
      "id2=" +
      input.value.split(",")[1];
  }
  try {
    const response = await fetch(queryUrl);
    const text = await response.text();
    const display = document.getElementById("response");
    display.style.display = "block";
    display.replaceChildren(jsonToTableParser(text));
  } catch (err) {
    console.error("Search failed:", err);
  }
  return false;
}
function openTab(cityName, elmnt) {
  var i, tabcontent, tablinks;
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }

  tablinks = document.getElementsByClassName("tablink");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].style.backgroundColor = "";
  }

  document.getElementById(cityName).style.display = "block";

  elmnt.style.backgroundColor = "#0b57d0";
}

document.getElementById("defaultOpen").click();
