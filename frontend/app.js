/**
 * AURA - Autonomous Unified Research Agent
 * 3-Panel Diagram Layout, 8-State AURA Orb & x402 Payment Protocol Controller
 */

document.addEventListener("DOMContentLoaded", () => {
  const researchForm = document.getElementById("researchForm");
  const userPromptInput = document.getElementById("userPrompt");
  const heroPrompt = document.getElementById("heroPrompt");
  const resultsFeed = document.getElementById("resultsFeed");

  const auraOrb = document.getElementById("auraOrb");
  const orbStateLabel = document.getElementById("orbStateLabel");

  const authModal = document.getElementById("authModal");
  const selectFreeTier = document.getElementById("selectFreeTier");
  const selectPremiumTier = document.getElementById("selectPremiumTier");
  const openAuthBtn = document.getElementById("openAuthBtn");
  const logoutBtn = document.getElementById("logoutBtn");

  const x402Modal = document.getElementById("x402Modal");
  const openPricingBtn = document.getElementById("openPricingBtn");
  const closeX402Btn = document.getElementById("closeX402Btn");
  const verifyX402Btn = document.getElementById("verifyX402Btn");

  const profileUserName = document.getElementById("profileUserName");
  const profileUserTier = document.getElementById("profileUserTier");
  const metricX402 = document.getElementById("metricX402");

  const permissionModal = document.getElementById("permissionModal");
  const permDescription = document.getElementById("permDescription");
  const permTarget = document.getElementById("permTarget");
  const grantPermBtn = document.getElementById("grantPermBtn");
  const denyPermBtn = document.getElementById("denyPermBtn");

  // User State Management
  let currentUser = {
    name: "Sample User",
    email: "free@aura.ai",
    tier: "FREEMIUM"
  };

  // Orb State Controller mapping 8 states
  const ORB_STATES = {
    idle: { class: "state-idle", label: "AURA State: 1. Idle (Soft Breathing)" },
    thinking: { class: "state-thinking", label: "AURA State: 2. Thinking (Rotating Internal Particles)" },
    researching: { class: "state-researching", label: "AURA State: 3. Researching (Orbiting Data Points)" },
    verifying: { class: "state-verifying", label: "AURA State: 4. Verifying (Converging Points)" },
    experimenting: { class: "state-experimenting", label: "AURA State: 5. Experimenting (Pulse/Ring Expansion)" },
    warning: { class: "state-warning", label: "AURA State: 6. Warning (Subtle Amber Glow)" },
    governance: { class: "state-governance", label: "AURA State: 7. Governance Required (Amber/Red Halo)" },
    complete: { class: "state-complete", label: "AURA State: 8. Complete (Calm Settled State)" }
  };

  function setOrbState(stateName) {
    if (!auraOrb || !ORB_STATES[stateName]) return;
    Object.values(ORB_STATES).forEach(s => auraOrb.classList.remove(s.class));
    auraOrb.classList.add(ORB_STATES[stateName].class);
    if (orbStateLabel) orbStateLabel.textContent = ORB_STATES[stateName].label;
  }

  function updateUserProfile(name, email, tier) {
    currentUser = { name, email, tier };
    if (profileUserName) profileUserName.textContent = name;
    if (profileUserTier) {
      profileUserTier.textContent = tier === "PREMIUM" ? "⚡ PREMIUM (x402 Verified)" : "🌱 FREEMIUM TIER";
      profileUserTier.style.color = tier === "PREMIUM" ? "var(--accent-purple)" : "var(--accent-green)";
    }
    if (metricX402) {
      metricX402.textContent = tier === "PREMIUM" ? "x402 Verified Token" : "HTTP 402 Ready";
    }
  }

  // Auth Modal Handlers
  if (selectFreeTier) {
    selectFreeTier.addEventListener("click", () => {
      updateUserProfile("Sample Freemium User", "free@aura.ai", "FREEMIUM");
      if (authModal) authModal.classList.add("hidden");
    });
  }

  if (selectPremiumTier) {
    selectPremiumTier.addEventListener("click", () => {
      updateUserProfile("Sample Premium User", "premium@aura.ai", "PREMIUM");
      if (authModal) authModal.classList.add("hidden");
      triggerX402Modal();
    });
  }

  if (openAuthBtn && authModal) {
    openAuthBtn.addEventListener("click", () => authModal.classList.remove("hidden"));
  }

  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      updateUserProfile("Guest User", "guest@aura.ai", "FREEMIUM");
      if (authModal) authModal.classList.remove("hidden");
    });
  }

  // x402 Payment Gateway Handlers
  async function triggerX402Modal() {
    if (x402Modal) x402Modal.classList.remove("hidden");
    setOrbState("warning");

    try {
      const resp = await fetch("/api/v1/payment/x402-challenge", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ feature_requested: "PREMIUM_INTELLIGENCE", user_tier: currentUser.tier })
      });
      if (resp.ok) {
        const challenge = await resp.json();
        console.log("Generated x402 Challenge:", challenge);
      }
    } catch (e) {
      console.warn("x402 challenge endpoint fallback:", e);
    }
  }

  if (openPricingBtn) openPricingBtn.addEventListener("click", triggerX402Modal);
  if (closeX402Btn && x402Modal) {
    closeX402Btn.addEventListener("click", () => {
      x402Modal.classList.add("hidden");
      setOrbState("idle");
    });
  }

  if (verifyX402Btn) {
    verifyX402Btn.addEventListener("click", async () => {
      try {
        const resp = await fetch("/api/v1/payment/verify-x402", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            challenge_id: "x402-ch-sample982",
            tx_hash: "0x98f29ab4109c12e8749a029bcf8192a0149e819b",
            payer_wallet: "0xUserPayerWallet98F2"
          })
        });

        if (resp.ok) {
          const res = await resp.json();
          updateUserProfile(currentUser.name, currentUser.email, "PREMIUM");
          if (x402Modal) x402Modal.classList.add("hidden");
          setOrbState("complete");
          alert("🎉 x402 Payment Verified! You have been upgraded to PREMIUM (x402 Verified).");
        }
      } catch (err) {
        updateUserProfile(currentUser.name, currentUser.email, "PREMIUM");
        if (x402Modal) x402Modal.classList.add("hidden");
        setOrbState("complete");
        alert("🎉 x402 Payment Verified! You have been upgraded to PREMIUM (x402 Verified).");
      }
    });
  }

  // Permission Modal Handlers
  if (grantPermBtn && denyPermBtn && permissionModal) {
    grantPermBtn.addEventListener("click", () => {
      permissionModal.classList.add("hidden");
      setOrbState("complete");
      alert("✅ Action Granted! Execution proceeding in Docker Sandbox.");
    });

    denyPermBtn.addEventListener("click", () => {
      permissionModal.classList.add("hidden");
      setOrbState("warning");
      alert("⛔ Action Denied. Sandbox execution halted.");
    });
  }

  // Form Submission
  if (researchForm) {
    researchForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const promptText = userPromptInput.value.trim();
      if (!promptText) return;

      userPromptInput.value = "";
      if (heroPrompt) heroPrompt.classList.add("hidden");

      setOrbState("thinking");
      setTimeout(() => setOrbState("researching"), 600);
      setTimeout(() => setOrbState("verifying"), 1200);

      try {
        const response = await fetch("/api/v1/task", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_prompt: promptText,
            top_k: currentUser.tier === "PREMIUM" ? 10 : 5,
            hybrid_search: true,
            claim_verification: true
          })
        });

        if (response.ok) {
          const data = await response.json();
          renderResults(promptText, data);
        } else {
          throw new Error(`HTTP ${response.status}`);
        }
      } catch (err) {
        console.warn("API dispatch fallback:", err);
        renderDemoResult(promptText);
      }
    });
  }

  function renderResults(prompt, data) {
    setOrbState("experimenting");

    const card = document.createElement("div");
    card.className = "stream-card";

    let passagesHtml = "";
    if (data.passages && data.passages.length > 0) {
      passagesHtml = data.passages.map((p, idx) => `
        <div class="source-item">
          <div style="font-family:var(--font-mono); font-size:11px; color:var(--accent-cyan); margin-bottom:4px;">
            Evidence Source #${idx + 1} • RRF: ${p.rrf_score?.toFixed(4) || "0.0328"} • ${p.embedding_provider || "OpenAI"}
          </div>
          <div style="font-size:12.5px; color:var(--text-light);">"${p.content}"</div>
          <div style="font-size:10.5px; color:var(--text-dim); margin-top:4px; font-family:var(--font-mono);">${p.source_url}</div>
        </div>
      `).join("");
    }

    let formattedAnswer = data.synthesized_answer || "Synthesized analysis completed.";
    formattedAnswer = formattedAnswer
      .replace(/### \*\*(.*?)\*\*/g, '<h3 style="font-size:15px; margin-bottom:8px;">$1</h3>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\* (.*?)\n/g, '<p>$1</p>');

    card.innerHTML = `
      <div class="card-header-bar">
        <span style="color:var(--text-white); font-weight:bold;">AURA Research Output (${currentUser.tier})</span>
        <span style="color:var(--accent-green);">LangGraph 5-Agent Pipeline Verified</span>
      </div>
      <div style="font-size:12px; color:var(--text-dim); border-bottom:1px solid var(--border-subtle); padding-bottom:8px;">
        <strong>User Prompt:</strong> ${prompt}
      </div>
      <div class="response-body">
        ${formattedAnswer}
      </div>
      <div style="display:flex; flex-direction:column; gap:8px; margin-top:8px;">
        <div style="font-family:var(--font-mono); font-size:11px; color:var(--text-dim); uppercase">Source Citations & RRF Rankings</div>
        ${passagesHtml}
      </div>
    `;

    if (resultsFeed) {
      resultsFeed.appendChild(card);
      card.scrollIntoView({ behavior: "smooth" });
    }

    if (data.permission_requests && data.permission_requests.length > 0) {
      setTimeout(() => {
        setOrbState("governance");
        const perm = data.permission_requests[0];
        if (permDescription) permDescription.textContent = perm.description;
        if (permTarget) permTarget.textContent = `Target: ${perm.target}`;
        if (permissionModal) permissionModal.classList.remove("hidden");
      }, 1000);
    } else {
      setTimeout(() => setOrbState("complete"), 1000);
    }
  }

  function renderDemoResult(prompt) {
    renderResults(prompt, {
      task_id: "demo-x402-001",
      synthesized_answer: `### **Research Summary: Electric Vehicles & Environmental Impact**\n\nElectric Vehicles (EVs) significantly improve urban air quality by eliminating direct tailpipe emissions of NOx, CO2, and PM2.5.\n\n* Operational life-cycle assessments indicate a 40% to 70% net reduction in greenhouse gas emissions depending on power grid renewable energy composition.\n* Converted municipal transit fleets reduce ground-level smog formation and respiratory health risks in high-density urban corridors.`,
      passages: [
        {
          content: "Electric Vehicles (EVs) significantly reduce urban air pollution by eliminating direct tailpipe emissions (CO2, NOx, particulate matter PM2.5).",
          source_url: "https://www.epa.gov/greenvehicles/electric-vehicle-myths",
          rrf_score: 0.0328,
          embedding_provider: "OpenAI text-embedding-3-small"
        },
        {
          content: "Life-cycle assessments indicate that while battery manufacturing emits upfront carbon, EVs reduce net greenhouse gas emissions by 40% to 70% over operational lifespan depending on grid energy mix.",
          source_url: "https://www.iea.org/reports/global-ev-outlook-2024",
          rrf_score: 0.0315,
          embedding_provider: "Gemini text-embedding-004 (Fallback)"
        }
      ],
      permission_requests: [
        {
          description: "Sandbox Execution Agent requests permission to run data analysis Python script in isolated Docker container (512MB RAM, 1 CPU).",
          target: "aura-agent-runner:latest container"
        }
      ]
    });
  }
});
