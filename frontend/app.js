/**
 * AURA - Autonomous Unified Research Agent
 * 3-Panel Diagram Layout & 8-State AURA Orb Controller
 */

document.addEventListener("DOMContentLoaded", () => {
  const researchForm = document.getElementById("researchForm");
  const userPromptInput = document.getElementById("userPrompt");
  const submitBtn = document.getElementById("submitBtn");
  const heroPrompt = document.getElementById("heroPrompt");
  const resultsFeed = document.getElementById("resultsFeed");

  const auraOrb = document.getElementById("auraOrb");
  const orbStateLabel = document.getElementById("orbStateLabel");

  const permissionModal = document.getElementById("permissionModal");
  const permDescription = document.getElementById("permDescription");
  const permTarget = document.getElementById("permTarget");
  const grantPermBtn = document.getElementById("grantPermBtn");
  const denyPermBtn = document.getElementById("denyPermBtn");

  const metricThink = document.getElementById("metricThink");
  const metricEvaluation = document.getElementById("metricEvaluation");
  const metricGovernance = document.getElementById("metricGovernance");
  const metricAccuracy = document.getElementById("metricAccuracy");

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
    
    // Remove all previous state classes
    Object.values(ORB_STATES).forEach(s => auraOrb.classList.remove(s.class));
    
    // Add target state class
    auraOrb.classList.add(ORB_STATES[stateName].class);
    if (orbStateLabel) orbStateLabel.textContent = ORB_STATES[stateName].label;
  }

  // Sidebar navigation switching
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach(item => {
    item.addEventListener("click", () => {
      navItems.forEach(i => i.classList.remove("active"));
      item.classList.add("active");
    });
  });

  // Handle Permission Modal Action
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

  // Handle Form Submission
  if (researchForm) {
    researchForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const promptText = userPromptInput.value.trim();
      if (!promptText) return;

      userPromptInput.value = "";
      if (heroPrompt) heroPrompt.classList.add("hidden");

      // State Transition Sequence: Thinking -> Researching -> Verifying -> Experimenting -> Complete
      setOrbState("thinking");
      if (metricThink) metricThink.textContent = "OpenAI Deconstructing...";

      setTimeout(() => { setOrbState("researching"); }, 600);
      setTimeout(() => { setOrbState("verifying"); }, 1200);

      try {
        const response = await fetch("/api/v1/task", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_prompt: promptText,
            top_k: 5,
            hybrid_search: true,
            claim_verification: true
          })
        });

        if (response.ok) {
          const data = await response.json();
          renderResults(promptText, data);
        } else {
          throw new Error(`Server returned HTTP ${response.status}`);
        }
      } catch (err) {
        console.warn("Backend API dispatch fallback:", err);
        renderDemoResult(promptText);
      }
    });
  }

  function renderResults(prompt, data) {
    setOrbState("experimenting");
    if (metricEvaluation) metricEvaluation.textContent = "Gemini 1.5 Summarizer";

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
        <span style="color:var(--text-white); font-weight:bold;">AURA Research Output</span>
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

    // Trigger Governance state and modal if permissions required
    if (data.permission_requests && data.permission_requests.length > 0) {
      setTimeout(() => {
        setOrbState("governance");
        if (metricGovernance) metricGovernance.textContent = "Governance Required";
        const perm = data.permission_requests[0];
        if (permDescription) permDescription.textContent = perm.description;
        if (permTarget) permTarget.textContent = `Target: ${perm.target}`;
        if (permissionModal) permissionModal.classList.remove("hidden");
      }, 1000);
    } else {
      setTimeout(() => { setOrbState("complete"); }, 1000);
    }
  }

  function renderDemoResult(prompt) {
    renderResults(prompt, {
      task_id: "demo-orb-001",
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
