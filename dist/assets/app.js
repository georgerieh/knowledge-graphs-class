const API_BASE = "";
let currentIntent = "article-keyword"; // Default intent

const intentCache = {};

function setIntent(intent, element) {
  const workspace = document.getElementById("workspace");

  if (workspace) {
    intentCache[currentIntent] = workspace.innerHTML;
  }

  currentIntent = intent;

  document
    .querySelectorAll(".chip")
    .forEach((chip) => chip.classList.remove("active"));
  element.classList.add("active");

  const input = document.getElementById("search-input");
  switch (intent) {
    case "article-keyword":
      input.placeholder = "Enter paper keyword (e.g. graph database)...";
      break;
    case "article-text":
      input.placeholder = "Enter text to search for...";
      break;
    case "article-field":
      input.placeholder = "Enter numeric field id to search articles/...";
      break;
    case "paper-info":
      input.placeholder = "Enter Article ID...";
      break;
    case "researcher-info":
      input.placeholder = "Enter researcher name...";
      break;
    case "researcher-alike":
      input.placeholder = "Enter researcher id...";
      break;
    case "researcher-hindex":
      input.placeholder = "Enter researcher ID for H-index...";
      break;
    case "researcher-articles":
      input.placeholder = "Enter researcher ID for H-index...";
      break;
    case "keyword-search":
      input.placeholder = "Enter keyword or field of science...";
      break;
    case "keyword-community":
      input.placeholder =
        "Enter keyword community id to find similar communities...";
      break;
    case "networking":
      input.placeholder =
        "Enter two researcher IDs separated by comma (id1,id2)...";
      break;
    case "custom-query":
      input.placeholder = "Enter graph query expression...";
      break;
  }

  if (intentCache[currentIntent]) {
    workspace.innerHTML = intentCache[currentIntent];
  } else {
    workspace.innerHTML = `<div class="placeholder-state">Enter a query above to explore the academic graph.</div>`;
  }
}

async function handleSearch(event) {
  if (event) event.preventDefault();

  const inputVal = document.getElementById("search-input").value.trim();
  const workspace = document.getElementById("workspace");

  if (!inputVal) return;

  workspace.innerHTML =
    '<div class="placeholder-state">Querying graph database...</div>';

  let endpoint = "";
  // #TODO : dict instead of case break
  switch (currentIntent) {
    case "article-keyword":
      endpoint = `api/article/search_by_keyword?_id=${encodeURIComponent(inputVal)}`;
      break;
    case "article-text":
      endpoint = `api/article/search_by_text?_id=${encodeURIComponent(inputVal)}`;
      break;
    case "article-field":
      endpoint = `api/article/search_by_field?_id=${encodeURIComponent(inputVal)}`;
      break;
    case "paper-info":
      endpoint = `api/paper/get_info?_id=${encodeURIComponent(inputVal)}`;
      break;
    case "researcher-info":
      endpoint = `api/researcher/get_info?who=${encodeURIComponent(inputVal)}`;
      break;
    case "researcher-hindex":
      endpoint = `api/researcher/h_index?_id=${encodeURIComponent(inputVal)}`;
      break;
    case "researcher-articles":
      endpoint = `api/researcher/most_influential?_id=${encodeURIComponent(inputVal)}`;
      break;
    case "keyword-search":
      endpoint = `api/keyword/get?keyword=${encodeURIComponent(inputVal)}`;
      break;
    case "keyword-community":
      endpoint = `api/keyword/search?_id=${encodeURIComponent(inputVal)}`;
      break;
    case "researcher-alike":
      endpoint = `api/community/search?_id=${encodeURIComponent(inputVal)}`;
      break;
    case "networking":
      const ids = inputVal.split(",");
      endpoint = `api/networking?id1=${ids[0] ? ids[0].trim() : ""}&id2=${ids[1] ? ids[1].trim() : ""}`;
      break;
    case "custom-query":
      endpoint = `query?query=${encodeURIComponent(inputVal)}`;
      break;
    default:
      endpoint = `api/article/search_by_keyword?_id=${encodeURIComponent(inputVal)}`;
  }

  try {
    const response = await fetch(`${API_BASE}/${endpoint}`);
    const text = await response.text();
    const viewElement = parseApiResponseToView(text);

    workspace.innerHTML = "";
    workspace.appendChild(viewElement);

    intentCache[currentIntent] = workspace.innerHTML;
  } catch (err) {
    console.error("Search failed:", err);
    workspace.innerHTML =
      '<div class="placeholder-state" style="color: #d93025;">Failed to connect to backend server.</div>';
  }
}

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

function parseApiResponseToView(inputData) {
  let data = inputData;

  if (typeof inputData === "string") {
    try {
      data = JSON.parse(inputData);
    } catch (error) {
      console.error("Invalid JSON string:", error);
      data = { error: "Invalid JSON", raw: inputData };
    }
  }

  const container = document.createElement("div");
  container.className = "api-response-container";

  if (data === null || data === undefined) {
    container.textContent = "No data available";
    return container;
  }

  if (Array.isArray(data)) {
    if (data.length === 0) {
      container.textContent = "Empty list returned from API";
      return container;
    }

    data.forEach((item, index) => {
      const card = document.createElement("div");
      card.className = "api-card";

      const header = document.createElement("div");
      header.className = "api-card-header";
      header.textContent = `Record #${index + 1}`;
      card.appendChild(header);

      card.appendChild(renderItem(item));
      container.appendChild(card);
    });
  } else if (typeof data === "object") {
    const card = document.createElement("div");
    card.className = "api-card single-object-card";

    card.appendChild(renderItem(data));
    container.appendChild(card);
  } else {
    const el = document.createElement("div");
    el.className = "api-primitive-value";
    el.textContent = String(data);
    container.appendChild(el);
  }

  return container;
}

function renderItem(item) {
  const list = document.createElement("dl");
  list.className = "api-kv-list";

  const flattened =
    item !== null && typeof item === "object" && !Array.isArray(item)
      ? flattenObject(item)
      : { value: item };

  for (const [key, value] of Object.entries(flattened)) {
    const dt = document.createElement("dt");
    dt.textContent = key.replace(/^n\./, "").toUpperCase();

    const dd = document.createElement("dd");
    if (value !== null && value !== undefined) {
      const tempDiv = document.createElement("div");
      tempDiv.innerHTML = String(value);
      dd.textContent = tempDiv.textContent || tempDiv.innerText || value;
    } else {
      dd.textContent = "—";
      dd.className = "empty-cell";
    }

    list.appendChild(dt);
    list.appendChild(dd);
  }

  return list;
}
