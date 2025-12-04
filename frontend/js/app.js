const INGEST_URL = "http://localhost:8000/ingest/";
const CHAT_URL = "http://localhost:8000/chat/";

document.getElementById("ingestBtn").addEventListener("click", async () => {
  const text = document.getElementById("kbText").value;
  const source = document.getElementById("sourceName").value || "user-paste";
  if (!text.trim()) {
    alert("Collez quelque chose d'abord.");
    return;
  }
  document.getElementById("ingestResult").innerText = "Indexation en cours...";
  try {
    const resp = await fetch(INGEST_URL, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ text, source_name: source })
    });
    const j = await resp.json();
    document.getElementById("ingestResult").innerText = `Indexé: ${j.indexed} documents (source: ${j.source})`;
  } catch (e) {
    document.getElementById("ingestResult").innerText = "Erreur d'indexation: " + e;
  }
});

document.getElementById("askBtn").addEventListener("click", async () => {
  const q = document.getElementById("questionInput").value;
  if (!q.trim()) return;
  addChatMessage("user", q);
  document.getElementById("questionInput").value = "";
  addChatMessage("system", "Rafiq-AI réfléchit...");
  try {
    const resp = await fetch(CHAT_URL, {
      method:"POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ question: q })
    });
    const j = await resp.json();
    // remove last "thinking" message
    removeLastSystemThinking();
    addChatMessage("assistant", j.answer || (j.answer===undefined ? JSON.stringify(j) : "Aucune réponse"));
    // show sources
    document.getElementById("sourcesPre").innerText = JSON.stringify(j.sources, null, 2);
  } catch (e) {
    removeLastSystemThinking();
    addChatMessage("assistant", "Erreur: " + e);
  }
});

function addChatMessage(who, text){
  const box = document.getElementById("chatBox");
  const el = document.createElement("div");
  el.className = "message " + who;
  el.style.marginBottom = "8px";
  el.innerHTML = `<strong>${who === "user" ? "Vous" : who==="assistant" ? "Rafiq-AI" : ""}:</strong> ${escapeHtml(text)}`;
  box.appendChild(el);
  box.scrollTop = box.scrollHeight;
}

function removeLastSystemThinking(){
  const box = document.getElementById("chatBox");
  const items = box.querySelectorAll("div.message.system");
  if (items.length) items[items.length-1].remove();
}

function escapeHtml(unsafe) {
  return unsafe
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}
