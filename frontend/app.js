/**
 * AURA — Autonomous Research Agent (AE-02) Frontend Controller
 */

// Demo Initial Data representing realistic pgvector & Supabase agent execution
const mockPassages = [
  {
    id: "p-01",
    source: "https://docs.supabase.com/guides/database/extensions/pgvector",
    score: 0.942,
    content: "Supabase provides native PostgreSQL vector similarity search via pgvector. By default, embeddings created with 1536 dimensions (e.g. OpenAI text-embedding-3-small) can be stored in Vector(1536) columns with HNSW or IVFFlat indexing.",
    embeddingDim: "1536d",
    tokens: ["pgvector", "supabase", "hnsw", "vector(1536)"]
  },
  {
    id: "p-02",
    source: "https://python.langchain.com/docs/integrations/vectorstores/supabase",
    score: 0.887,
    content: "When connecting SQLAlchemy asyncpg to Supabase PgBouncer pooler on port 6543, prepared statements must be disabled using statement_cache_size=0 to prevent transaction-mode protocol errors.",
    embeddingDim: "1536d",
    tokens: ["asyncpg", "pgbouncer", "sqlalchemy", "port-6543"]
  },
  {
    id: "p-03",
    source: "https://arxiv.org/abs/2305.14251",
    score: 0.841,
    content: "Self-Evolving Autonomous Agents continuously update their strategy definitions based on governance-validated evaluation benchmarks, storing versioned code snippets in immutable strategy stores.",
    embeddingDim: "1536d",
    tokens: ["self-evolving", "agent-strategy", "governance"]
  },
  {
    id: "p-04",
    source: "https://fastapi.tiangolo.com/advanced/events/",
    score: 0.812,
    content: "FastAPI lifespan handlers provide a robust context manager to execute async database extension checks (like CREATE EXTENSION IF NOT EXISTS vector) on startup and dispose connections on shutdown.",
    embeddingDim: "1536d",
    tokens: ["fastapi", "lifespan", "startup-init"]
  }
];

const mockClaims = [
  {
    id: "c-01",
    text: "Supabase supports 1536-dimensional embeddings natively in PostgreSQL via pgvector without manual build scripts.",
    confidence: 0.96,
    isInterpretation: false,
    evidenceType: "Direct Entailment",
    linkedPassage: "p-01"
  },
  {
    id: "c-02",
    text: "PgBouncer in transaction mode requires statement_cache_size=0 for SQLAlchemy asyncpg engine connections.",
    confidence: 0.92,
    isInterpretation: false,
    evidenceType: "Protocol Requirement",
    linkedPassage: "p-02"
  },
  {
    id: "c-03",
    text: "Self-evolving strategy code stored in StrategyVersion requires explicit governance approval before execution.",
    confidence: 0.87,
    isInterpretation: true,
    evidenceType: "Synthesized Governance Policy",
    linkedPassage: "p-03"
  }
];

const mockAuditLogs = [
  {
    id: "log-001",
    action: "INIT_TASK",
    target: "ResearchTask#a7c4d21",
    status: "SUCCESS",
    timestamp: "17:34:02",
    details: {
      user_prompt: "Verify Supabase pgvector asyncpg setup and strategy governance",
      status: "RUNNING",
      created_at: new Date().toISOString()
    }
  },
  {
    id: "log-002",
    action: "EMBEDDING_GEN",
    target: "OpenAI text-embedding-3-small",
    status: "SUCCESS",
    timestamp: "17:34:04",
    details: {
      model: "text-embedding-3-small",
      dimensions: 1536,
      tokens_processed: 42
    }
  },
  {
    id: "log-003",
    action: "PGVECTOR_COSINE_SEARCH",
    target: "document_passages",
    status: "SUCCESS",
    timestamp: "17:34:05",
    details: {
      similarity_threshold: 0.80,
      matched_rows: 4,
      index_used: "hnsw_vector_cosine_idx"
    }
  },
  {
    id: "log-004",
    action: "CLAIM_TRIANGULATION",
    target: "claim_nodes",
    status: "SUCCESS",
    timestamp: "17:34:06",
    details: {
      extracted_claims: 3,
      entailment_verified: true,
      min_confidence: 0.87
    }
  }
];

// App Initialization
document.addEventListener("DOMContentLoaded", () => {
  renderPassages(mockPassages);
  renderClaims(mockClaims);
  renderAuditLogs(mockAuditLogs);
  checkBackendHealth();
  setupEventListeners();
});

// Check FastAPI Backend Health
async function checkBackendHealth() {
  const statusPill = document.getElementById("backendStatusPill");
  const statusText = document.getElementById("backendStatusText");
  const statusIndicator = statusPill.querySelector(".status-indicator");

  try {
    const response = await fetch("http://localhost:8000/health", { method: "GET" });
    if (response.ok) {
      const data = await response.json();
      statusText.textContent = `API Connected (${data.database || 'Supabase DB'})`;
      statusIndicator.classList.remove("loading");
      statusPill.style.backgroundColor = "var(--emerald-bg)";
      statusPill.style.color = "var(--emerald-text)";
      statusPill.style.borderColor = "var(--emerald-border)";
    } else {
      throw new Error("HTTP " + response.status);
    }
  } catch (err) {
    statusText.textContent = "Backend Offline (Standby Mode)";
    statusIndicator.classList.add("loading");
    statusPill.style.backgroundColor = "var(--amber-bg)";
    statusPill.style.color = "var(--amber-text)";
    statusPill.style.borderColor = "var(--amber-border)";
  }
}

// Render Passages Column
function renderPassages(passages) {
  const container = document.getElementById("passagesList");
  document.getElementById("passageCountBadge").textContent = `${passages.length} Items`;

  container.innerHTML = passages.map(p => `
    <div class="passage-card">
      <div class="passage-header">
        <a href="${p.source}" target="_blank" class="source-link" title="${p.source}">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
          </svg>
          ${p.source.replace("https://", "").split("/")[0]}
        </a>
        <span class="score-tag">Sim: ${(p.score * 100).toFixed(1)}%</span>
      </div>
      <div class="passage-text">${escapeHtml(p.content)}</div>
      <div class="passage-footer">
        <span class="dim-tag">${p.embeddingDim}</span>
        ${p.tokens.map(t => `<span class="token-tag">#${t}</span>`).join("")}
      </div>
    </div>
  `).join("");
}

// Render Claims Column
function renderClaims(claims) {
  const container = document.getElementById("claimsList");
  document.getElementById("claimCountBadge").textContent = `${claims.length} Claims`;

  container.innerHTML = claims.map(c => `
    <div class="claim-card">
      <div class="claim-header">
        <span class="confidence-pill ${c.confidence >= 0.9 ? 'confidence-high' : 'confidence-med'}">
          ${(c.confidence * 100).toFixed(0)}% Confidence
        </span>
        <span class="claim-type">${c.isInterpretation ? 'Interpretation' : 'Fact Node'}</span>
      </div>
      <div class="claim-body">${escapeHtml(c.text)}</div>
      <div class="evidence-box">
        <div class="evidence-title">Transformation: ${c.evidenceType}</div>
        <div>Linked to passage passage: <strong>${c.linkedPassage}</strong></div>
      </div>
    </div>
  `).join("");
}

// Render Audit Logs Stream
function renderAuditLogs(logs) {
  const container = document.getElementById("auditLogStream");
  
  container.innerHTML = logs.map(l => `
    <div class="audit-item" onclick="openLogModal('${l.id}')">
      <div class="audit-item-header">
        <span class="audit-action">${l.action}</span>
        <span class="audit-time">${l.timestamp}</span>
      </div>
      <div class="audit-target">Target: <strong>${escapeHtml(l.target)}</strong></div>
    </div>
  `).join("");
}

// Event Listeners setup
function setupEventListeners() {
  const form = document.getElementById("researchForm");
  const submitBtn = document.getElementById("submitBtn");
  const btnSpinner = document.getElementById("btnSpinner");
  const closeModalBtn = document.getElementById("closeModalBtn");
  const modal = document.getElementById("detailModal");

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const promptText = document.getElementById("userPrompt").value.trim();
    if (!promptText) return;

    // Simulate task submission UI state
    btnSpinner.classList.remove("hidden");
    submitBtn.disabled = true;

    setTimeout(() => {
      // Add new simulated task log entry
      const newLog = {
        id: `log-${Date.now()}`,
        action: "NEW_RESEARCH_SUBMIT",
        target: "ResearchTask#user_input",
        status: "RUNNING",
        timestamp: new Date().toLocaleTimeString(),
        details: {
          prompt: promptText,
          top_k: document.getElementById("topK").value,
          hybrid_search: document.getElementById("hybridSearchToggle").checked,
          self_evolve: document.getElementById("selfEvolveToggle").checked
        }
      };

      mockAuditLogs.unshift(newLog);
      renderAuditLogs(mockAuditLogs);

      btnSpinner.classList.add("hidden");
      submitBtn.disabled = false;
      document.getElementById("userPrompt").value = "";
    }, 800);
  });

  closeModalBtn.addEventListener("click", () => {
    modal.classList.add("hidden");
  });

  modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.classList.add("hidden");
  });
}

// Modal inspection helper
window.openLogModal = function(logId) {
  const log = mockAuditLogs.find(l => l.id === logId);
  if (!log) return;

  document.getElementById("modalTitle").textContent = `Audit Event: ${log.action}`;
  document.getElementById("modalJsonContent").querySelector("code").textContent = JSON.stringify(log, null, 2);
  document.getElementById("detailModal").classList.remove("hidden");
};

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
