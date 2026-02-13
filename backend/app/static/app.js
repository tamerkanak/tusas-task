const errorEl = document.getElementById("error");
const healthEl = document.getElementById("health");

const fileInput = document.getElementById("fileInput");
const selectedFilesEl = document.getElementById("selectedFiles");
const uploadBtn = document.getElementById("uploadBtn");
const uploadResultEl = document.getElementById("uploadResult");
const acceptedListEl = document.getElementById("acceptedList");
const rejectedListEl = document.getElementById("rejectedList");

const refreshBtn = document.getElementById("refreshBtn");
const docGridEl = document.getElementById("docGrid");

const questionInput = document.getElementById("questionInput");
const askBtn = document.getElementById("askBtn");
const qaResultEl = document.getElementById("qaResult");
const qaMetaEl = document.getElementById("qaMeta");
const qaAnswerEl = document.getElementById("qaAnswer");
const qaCitationsEl = document.getElementById("qaCitations");

const state = {
  selectedFiles: /** @type {File[]} */ ([]),
  documents: /** @type {any[]} */ ([]),
  selectedDocumentIds: new Set(),
};

function setHidden(el, hidden) {
  if (!el) return;
  el.classList.toggle("hidden", hidden);
}

function setError(message) {
  if (!errorEl) return;
  if (!message) {
    errorEl.textContent = "";
    setHidden(errorEl, true);
    return;
  }
  errorEl.textContent = `Hata: ${message}`;
  setHidden(errorEl, false);
}

async function parseError(response) {
  let detail = `HTTP ${response.status}`;
  try {
    const payload = await response.json();
    if (payload && typeof payload.detail === "string") {
      detail = payload.detail;
    }
  } catch {
    // ignore
  }
  throw new Error(detail);
}

function formatDate(iso) {
  const date = new Date(iso);
  if (Number.isNaN(date.valueOf())) return iso;
  return date.toLocaleString("tr-TR");
}

function renderSelectedFiles() {
  selectedFilesEl.textContent = "";
  for (const file of state.selectedFiles) {
    const li = document.createElement("li");
    li.textContent = file.name;
    selectedFilesEl.appendChild(li);
  }
}

function renderUploadResult(payload) {
  acceptedListEl.textContent = "";
  rejectedListEl.textContent = "";

  const accepted = payload?.accepted_files ?? [];
  const rejected = payload?.rejected_files ?? [];

  if (accepted.length === 0) {
    const li = document.createElement("li");
    li.textContent = "-";
    acceptedListEl.appendChild(li);
  } else {
    for (const item of accepted) {
      const li = document.createElement("li");
      li.textContent = `${item.filename} (${item.status})`;
      acceptedListEl.appendChild(li);
    }
  }

  if (rejected.length === 0) {
    const li = document.createElement("li");
    li.textContent = "-";
    rejectedListEl.appendChild(li);
  } else {
    for (const item of rejected) {
      const li = document.createElement("li");
      li.textContent = `${item.filename}: ${item.reason}`;
      rejectedListEl.appendChild(li);
    }
  }

  setHidden(uploadResultEl, false);
}

function renderDocuments() {
  docGridEl.textContent = "";

  if (!state.documents.length) {
    const p = document.createElement("p");
    p.textContent = "Henuz belge yok.";
    docGridEl.appendChild(p);
    return;
  }

  for (const doc of state.documents) {
    const canSelect = doc.status === "indexed";
    const isChecked = state.selectedDocumentIds.has(doc.id);

    const label = document.createElement("label");
    label.className = `doc-card ${canSelect ? "" : "disabled"}`.trim();

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.disabled = !canSelect;
    checkbox.checked = isChecked;
    checkbox.addEventListener("change", () => {
      if (checkbox.checked) state.selectedDocumentIds.add(doc.id);
      else state.selectedDocumentIds.delete(doc.id);
    });

    const body = document.createElement("div");

    const title = document.createElement("strong");
    title.textContent = doc.filename;
    body.appendChild(title);

    const idLine = document.createElement("p");
    idLine.textContent = `ID: ${String(doc.id).slice(0, 12)}...`;
    body.appendChild(idLine);

    const typeLine = document.createElement("p");
    typeLine.textContent = `Tip: ${String(doc.file_type).toUpperCase()}`;
    body.appendChild(typeLine);

    const langLine = document.createElement("p");
    langLine.textContent = `Dil: ${doc.language}`;
    body.appendChild(langLine);

    const statusLine = document.createElement("p");
    statusLine.textContent = `Durum: ${doc.status}`;
    body.appendChild(statusLine);

    const createdLine = document.createElement("p");
    createdLine.textContent = `Olusturma: ${formatDate(doc.created_at)}`;
    body.appendChild(createdLine);

    label.appendChild(checkbox);
    label.appendChild(body);
    docGridEl.appendChild(label);
  }
}

function renderQaResult(payload) {
  qaMetaEl.textContent = "";
  qaCitationsEl.textContent = "";

  const modePill = document.createElement("span");
  modePill.className = `mode ${payload.mode}`;
  modePill.textContent = payload.mode;

  const conf = document.createElement("span");
  conf.textContent = `Confidence: ${payload.confidence}`;

  const used = document.createElement("span");
  used.textContent = `Used Chunks: ${payload.used_chunks}`;

  qaMetaEl.appendChild(modePill);
  qaMetaEl.appendChild(conf);
  qaMetaEl.appendChild(used);

  qaAnswerEl.textContent = payload.answer ?? "";

  const citations = payload.citations ?? [];
  if (!citations.length) {
    const li = document.createElement("li");
    li.textContent = "-";
    qaCitationsEl.appendChild(li);
  } else {
    for (const c of citations) {
      const li = document.createElement("li");
      const strong = document.createElement("strong");
      strong.textContent = c.filename;
      li.appendChild(strong);
      const suffix = c.page ? ` (sayfa ${c.page})` : "";
      li.appendChild(document.createTextNode(`${suffix} - ${c.snippet}`));
      qaCitationsEl.appendChild(li);
    }
  }

  setHidden(qaResultEl, false);
}

async function refreshHealth() {
  if (!healthEl) return;
  try {
    const response = await fetch("/api/health");
    if (!response.ok) return;
    const payload = await response.json();
    const services = payload.services || {};
    healthEl.textContent = `Health: ${payload.status} | db=${services.database} vector=${services.vector_store} gemini=${services.gemini}`;
  } catch {
    // ignore
  }
}

async function refreshDocuments() {
  setError("");
  try {
    refreshBtn.disabled = true;
    const response = await fetch("/api/documents");
    if (!response.ok) return parseError(response);
    state.documents = await response.json();
    renderDocuments();
  } catch (err) {
    setError(err?.message ?? String(err));
  } finally {
    refreshBtn.disabled = false;
  }
}

async function uploadDocuments() {
  if (!state.selectedFiles.length) {
    setError("Lutfen en az bir dosya secin.");
    return;
  }

  setError("");
  setHidden(uploadResultEl, true);

  const formData = new FormData();
  for (const file of state.selectedFiles) {
    formData.append("files", file, file.name);
  }

  try {
    uploadBtn.disabled = true;
    uploadBtn.textContent = "Yukleniyor...";
    const response = await fetch("/api/documents", { method: "POST", body: formData });
    if (!response.ok) return parseError(response);
    const payload = await response.json();
    renderUploadResult(payload);
    state.selectedFiles = [];
    fileInput.value = "";
    renderSelectedFiles();
    await refreshDocuments();
  } catch (err) {
    setError(err?.message ?? String(err));
  } finally {
    uploadBtn.disabled = false;
    uploadBtn.textContent = "Dosyalari Yukle";
  }
}

async function askQuestion() {
  const question = String(questionInput.value ?? "").trim();
  if (!question) {
    setError("Soru alani bos birakilamaz.");
    return;
  }

  const documentIds = Array.from(state.selectedDocumentIds);
  if (!documentIds.length) {
    setError("Soru icin en az bir indexed belge secin.");
    return;
  }

  setError("");
  setHidden(qaResultEl, true);

  try {
    askBtn.disabled = true;
    askBtn.textContent = "Sorgulaniyor...";
    const response = await fetch("/api/questions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, document_ids: documentIds }),
    });
    if (!response.ok) return parseError(response);
    const payload = await response.json();
    renderQaResult(payload);
  } catch (err) {
    setError(err?.message ?? String(err));
  } finally {
    askBtn.disabled = false;
    askBtn.textContent = "Soru Sor";
  }
}

fileInput.addEventListener("change", () => {
  const files = fileInput.files ? Array.from(fileInput.files) : [];
  state.selectedFiles = files;
  renderSelectedFiles();
});

uploadBtn.addEventListener("click", () => void uploadDocuments());
refreshBtn.addEventListener("click", () => void refreshDocuments());
askBtn.addEventListener("click", () => void askQuestion());

void refreshHealth();
void refreshDocuments();

