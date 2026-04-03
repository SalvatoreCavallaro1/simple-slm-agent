const GRAPH_STEPS = [
  {
    node: "input_node",
    idleDetail: "Waiting for the next prompt normalization step.",
  },
  {
    node: "model_node",
    idleDetail: "Waiting for the next Ollama model call.",
  },
  {
    node: "evaluator_node",
    idleDetail: "Waiting to compute metrics for the next response.",
  },
];

const state = {
  messages: [],
  pending: false,
  lastRun: null,
  graphActivity: createInitialGraphActivity(),
};

const elements = {
  composer: document.getElementById("composer"),
  input: document.getElementById("promptInput"),
  messages: document.getElementById("messages"),
  modelSelect: document.getElementById("modelSelect"),
  resetButton: document.getElementById("resetButton"),
  sendButton: document.getElementById("sendButton"),
  status: document.getElementById("status"),
  metricModel: document.getElementById("metricModel"),
  metricLatency: document.getElementById("metricLatency"),
  metricWords: document.getElementById("metricWords"),
  metricChars: document.getElementById("metricChars"),
  metricTimestamp: document.getElementById("metricTimestamp"),
  metricTurns: document.getElementById("metricTurns"),
  graphActivity: document.getElementById("graphActivity"),
};

function setStatus(message, tone = "neutral") {
  elements.status.textContent = message;
  elements.status.dataset.tone = tone;
}

function setPending(isPending) {
  state.pending = isPending;
  elements.input.disabled = isPending;
  elements.modelSelect.disabled = isPending;
  elements.resetButton.disabled = isPending;
  elements.sendButton.disabled = isPending;
  elements.sendButton.textContent = isPending ? "Thinking..." : "Send";
}

function createInitialGraphActivity() {
  return GRAPH_STEPS.map((step) => ({
    node: step.node,
    phase: "idle",
    detail: step.idleDetail,
    timestamp: null,
  }));
}

function humanizePhase(phase) {
  switch (phase) {
    case "running":
      return "Running";
    case "completed":
      return "Done";
    case "failed":
      return "Failed";
    default:
      return "Idle";
  }
}

function formatActivityTimestamp(timestamp) {
  if (!timestamp) {
    return "No events yet";
  }

  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }

  return date.toLocaleTimeString();
}

function renderGraphActivity() {
  elements.graphActivity.replaceChildren();

  for (const item of state.graphActivity) {
    const wrapper = document.createElement("article");
    wrapper.className = "activity-item";

    const topline = document.createElement("div");
    topline.className = "activity-topline";

    const node = document.createElement("p");
    node.className = "activity-node";
    node.textContent = item.node;

    const phase = document.createElement("span");
    phase.className = "activity-phase";
    phase.dataset.phase = item.phase;
    phase.textContent = humanizePhase(item.phase);

    topline.append(node, phase);

    const detail = document.createElement("p");
    detail.className = "activity-detail";
    detail.textContent = item.detail;

    const time = document.createElement("p");
    time.className = "activity-time";
    time.textContent = formatActivityTimestamp(item.timestamp);

    wrapper.append(topline, detail, time);
    elements.graphActivity.appendChild(wrapper);
  }
}

function resetGraphActivity() {
  state.graphActivity = createInitialGraphActivity();
  renderGraphActivity();
}

function applyGraphEvent(event) {
  state.graphActivity = state.graphActivity.map((item) => {
    if (item.node !== event.node) {
      return item;
    }

    return {
      ...item,
      phase: event.phase || item.phase,
      detail: event.detail || item.detail,
      timestamp: event.timestamp || item.timestamp,
    };
  });
  renderGraphActivity();
}

function resizeInput() {
  elements.input.style.height = "auto";
  elements.input.style.height = `${elements.input.scrollHeight}px`;
}

function scrollTranscriptToBottom() {
  elements.messages.scrollTop = elements.messages.scrollHeight;
}

function isLoadingMessage(message) {
  return state.pending && message.role === "assistant" && !message.content;
}

function populateMessageBubble(bubble, message) {
  bubble.className = "message-bubble";
  bubble.replaceChildren();

  if (isLoadingMessage(message)) {
    bubble.classList.add("loading");

    const indicator = document.createElement("div");
    indicator.className = "loading-indicator";

    const spinner = document.createElement("span");
    spinner.className = "loading-spinner";
    spinner.setAttribute("aria-hidden", "true");

    const label = document.createElement("span");
    label.className = "loading-label";
    label.textContent = "Thinking...";

    indicator.append(spinner, label);
    bubble.appendChild(indicator);
    return;
  }

  bubble.textContent = message.content;
}

function createMessageElement(message, index) {
  const wrapper = document.createElement("article");
  wrapper.className = `message ${message.role}`;
  wrapper.dataset.messageIndex = String(index);

  const role = document.createElement("p");
  role.className = "message-role";
  role.textContent = message.role === "user" ? "You" : "Assistant";

  const bubble = document.createElement("div");
  populateMessageBubble(bubble, message);

  wrapper.append(role, bubble);
  return wrapper;
}

function renderMessageAt(index) {
  const message = state.messages[index];
  if (!message) {
    renderMessages();
    return;
  }

  const bubble = elements.messages.querySelector(
    `.message[data-message-index="${index}"] .message-bubble`,
  );
  if (!bubble) {
    renderMessages();
    return;
  }

  populateMessageBubble(bubble, message);
  scrollTranscriptToBottom();
}

function renderMessages() {
  elements.messages.replaceChildren();

  if (state.messages.length === 0) {
    const emptyState = document.createElement("div");
    emptyState.className = "empty-state";
    emptyState.textContent =
      "Start a conversation. The UI keeps the chat history in the browser and sends it back on each turn so the model can answer in context.";
    elements.messages.appendChild(emptyState);
    return;
  }

  for (const [index, message] of state.messages.entries()) {
    elements.messages.appendChild(createMessageElement(message, index));
  }

  scrollTranscriptToBottom();
}

function renderRunDetails() {
  const turnCount = state.messages.length;
  elements.metricTurns.textContent = String(turnCount);

  if (!state.lastRun) {
    elements.metricModel.textContent = elements.modelSelect.value || "-";
    elements.metricLatency.textContent = "-";
    elements.metricWords.textContent = "-";
    elements.metricChars.textContent = "-";
    elements.metricTimestamp.textContent = "-";
    return;
  }

  elements.metricModel.textContent = state.lastRun.model;
  elements.metricLatency.textContent = `${state.lastRun.metrics.latency_ms} ms`;
  elements.metricWords.textContent = String(state.lastRun.metrics.word_count);
  elements.metricChars.textContent = String(state.lastRun.metrics.char_count);
  elements.metricTimestamp.textContent = new Date(state.lastRun.timestamp).toLocaleString();
}

function resetConversation() {
  state.messages = [];
  state.lastRun = null;
  resetGraphActivity();
  renderMessages();
  renderRunDetails();
  elements.input.value = "";
  resizeInput();
  setStatus("Conversation cleared.", "neutral");
  elements.input.focus();
}

function appendAssistantPlaceholder() {
  state.messages = [...state.messages, { role: "assistant", content: "" }];
  return state.messages.length - 1;
}

function removeMessageAt(index) {
  state.messages = state.messages.filter((_, messageIndex) => messageIndex !== index);
}

function appendAssistantChunk(index, chunk) {
  state.messages = state.messages.map((message, messageIndex) => {
    if (messageIndex !== index) {
      return message;
    }

    return {
      ...message,
      content: `${message.content}${chunk}`,
    };
  });
}

function setAssistantMessage(index, content) {
  state.messages = state.messages.map((message, messageIndex) => {
    if (messageIndex !== index) {
      return message;
    }

    return {
      ...message,
      content,
    };
  });
}

async function loadConfig() {
  const response = await fetch("/chat/config");
  if (!response.ok) {
    throw new Error("Failed to load chat configuration.");
  }

  return response.json();
}

function populateModelSelect(config) {
  elements.modelSelect.replaceChildren();

  for (const model of config.available_models) {
    const option = document.createElement("option");
    option.value = model;
    option.textContent = model;
    option.selected = model === config.primary_model;
    elements.modelSelect.appendChild(option);
  }
}

async function sendMessage(event) {
  event.preventDefault();

  if (state.pending) {
    return;
  }

  const prompt = elements.input.value.trim();
  if (!prompt) {
    setStatus("Write a message before sending.", "error");
    return;
  }

  const userMessage = { role: "user", content: prompt };
  const conversationForRequest = [...state.messages, userMessage];
  state.messages = [...conversationForRequest];
  const assistantIndex = appendAssistantPlaceholder();
  state.lastRun = null;
  resetGraphActivity();
  setPending(true);
  renderMessages();
  renderRunDetails();

  elements.input.value = "";
  resizeInput();
  setStatus("Opening stream...", "pending");

  try {
    const response = await fetch("/stream", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: elements.modelSelect.value || null,
        messages: conversationForRequest,
      }),
    });

    if (!response.ok) {
      const payload = await response.json();
      const detail = typeof payload.detail === "string" ? payload.detail : "Request failed.";
      throw new Error(detail);
    }

    if (!response.body) {
      throw new Error("Streaming response body is not available.");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let streamCompleted = false;
    let sawError = false;

    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const rawLine of lines) {
        const line = rawLine.trim();
        if (!line) {
          continue;
        }

        const payload = JSON.parse(line);

        if (payload.type === "status") {
          setStatus(
            `Connected to ${payload.model}. Waiting for streamed tokens...`,
            "pending",
          );
          continue;
        }

        if (payload.type === "graph") {
          applyGraphEvent(payload);
          continue;
        }

        if (payload.type === "token") {
          appendAssistantChunk(assistantIndex, payload.content);
          renderMessageAt(assistantIndex);
          continue;
        }

        if (payload.type === "done") {
          setAssistantMessage(assistantIndex, payload.result.response);
          state.lastRun = payload.result;
          renderMessageAt(assistantIndex);
          renderRunDetails();
          setStatus(`Completed in ${payload.result.metrics.latency_ms} ms.`, "success");
          streamCompleted = true;
          continue;
        }

        if (payload.type === "error") {
          if (!state.messages[assistantIndex]?.content) {
            removeMessageAt(assistantIndex);
          }
          renderMessages();
          renderRunDetails();
          setStatus(payload.detail || "Streaming failed.", "error");
          sawError = true;
        }
      }
    }

    buffer += decoder.decode();
    const trailingLine = buffer.trim();
    if (trailingLine) {
      const payload = JSON.parse(trailingLine);
      if (payload.type === "graph") {
        applyGraphEvent(payload);
      } else if (payload.type === "done") {
        setAssistantMessage(assistantIndex, payload.result.response);
        state.lastRun = payload.result;
        renderMessageAt(assistantIndex);
        renderRunDetails();
        setStatus(`Completed in ${payload.result.metrics.latency_ms} ms.`, "success");
        streamCompleted = true;
      } else if (payload.type === "error") {
        if (!state.messages[assistantIndex]?.content) {
          removeMessageAt(assistantIndex);
        }
        renderMessages();
        renderRunDetails();
        setStatus(payload.detail || "Streaming failed.", "error");
        sawError = true;
      }
    }

    if (!streamCompleted && !sawError) {
      if (!state.messages[assistantIndex]?.content) {
        removeMessageAt(assistantIndex);
      }
      renderMessages();
      renderRunDetails();
      throw new Error("Stream ended before a final response was received.");
    }
  } catch (error) {
    if (!state.messages[assistantIndex]?.content) {
      removeMessageAt(assistantIndex);
    }
    renderMessages();
    renderRunDetails();
    setStatus(error instanceof Error ? error.message : "Request failed.", "error");
  } finally {
    setPending(false);
    scrollTranscriptToBottom();
    elements.input.focus();
  }
}

function handleTextareaKeydown(event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    elements.composer.requestSubmit();
  }
}

async function init() {
  renderMessages();
  renderRunDetails();
  renderGraphActivity();
  resizeInput();
  setPending(true);

  try {
    const config = await loadConfig();
    populateModelSelect(config);
    renderRunDetails();
    setStatus("Ready.", "success");
  } catch (error) {
    setStatus(error instanceof Error ? error.message : "Failed to load configuration.", "error");
  } finally {
    setPending(false);
  }
}

elements.composer.addEventListener("submit", sendMessage);
elements.input.addEventListener("input", resizeInput);
elements.input.addEventListener("keydown", handleTextareaKeydown);
elements.resetButton.addEventListener("click", resetConversation);

void init();
