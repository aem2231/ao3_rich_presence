const TARGET_DOMAIN = "archiveofourown.org";
let ws;
let messageQueue = [];
let lastUrl = "";
let lastTabId = null;

function connect() {
  ws = new WebSocket("ws://127.0.0.1:8765");

  ws.onopen = () => {
    console.log("[AO3 RPC] WebSocket connected");
    while (messageQueue.length > 0) {
      ws.send(JSON.stringify(messageQueue.shift()));
    }
  };

  ws.onerror = (err) => {
    console.error("[AO3 RPC] WebSocket error:", err);
  };

  ws.onclose = () => {
    console.warn("[AO3 RPC] WebSocket disconnected, retrying in 5s");
    setTimeout(connect, 5000);
  };
}

function sendPayload(payload) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(payload));
  } else {
    messageQueue.push(payload);
  }
}

function updatePresence(tab) {
  if (tab && tab.url && tab.url.includes(TARGET_DOMAIN)) {
    if (tab.url === lastUrl) return;
    lastUrl = tab.url;
    lastTabId = tab.id;

    const payload = {
      action: "update",
      title: tab.title,
      timestamp: Date.now(),
    };
    sendPayload(payload);
    console.log("[AO3 RPC] Sent update:", payload);
  } else {
    if (lastUrl === "") return;
    lastUrl = "";
    lastTabId = null;
    sendPayload({ action: "clear" });
    console.log("[AO3 RPC] Sent clear");
  }
}

connect();

browser.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete") {
    updatePresence(tab);
  }
});

browser.tabs.onActivated.addListener((activeInfo) => {
  browser.tabs.get(activeInfo.tabId, (tab) => {
    updatePresence(tab);
  });
});

browser.tabs.onRemoved.addListener((tabId, removeInfo) => {
  if (tabId === lastTabId) {
    lastUrl = "";
    lastTabId = null;
    sendPayload({ action: "clear" });
    console.log("[AO3 RPC] Sent clear on tab close");
  }
});

console.log("[AO3 RPC] Plugin loaded!");
