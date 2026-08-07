import React from "react";

export interface AgentStep {
  id: string;
  agentName: string;
  role: string;
  status: "COMPLETED" | "PENDING" | "BLOCKED" | "FAILED" | "IN_PROGRESS";
  thoughtText: string;
  durationMs?: number;
  timestamp?: string;
}

interface AgentFeedProps {
  steps: AgentStep[];
  activeAgentIndex?: number;
}

const AGENT_ROSTER = [
  { name: "Planner Agent", icon: "1", defaultRole: "Task Planning & DAG Decomposition" },
  { name: "Sandbox Executor", icon: "2", defaultRole: "Docker Resource-Constrained Sandbox" },
  { name: "RAG Retrieval Agent", icon: "3", defaultRole: "BM25 + PgVector Cosine Hybrid Search" },
  { name: "Evolution Critic", icon: "4", defaultRole: "Held-out Strategy Evaluation Engine" },
  { name: "Governance Gatekeeper", icon: "5", defaultRole: "AST Safety & Code Boundary Guard" },
];

export const AgentFeed: React.FC<AgentFeedProps> = ({ steps }) => {
  const getBadgeStyle = (status: AgentStep["status"]) => {
    switch (status) {
      case "COMPLETED":
        return "bg-white text-black font-bold border-white";
      case "PENDING":
      case "IN_PROGRESS":
        return "bg-zinc-900 text-zinc-300 border-zinc-700 font-medium animate-pulse";
      case "BLOCKED":
      case "FAILED":
        return "bg-zinc-950 text-zinc-400 border-zinc-700 font-medium";
      default:
        return "bg-zinc-900 text-zinc-400 border-zinc-800";
    }
  };


  return (
    <div className="w-full max-w-4xl mx-auto my-6 p-6 rounded-2xl bg-slate-950/80 border border-slate-800 shadow-2xl backdrop-blur-md text-slate-100 font-sans">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-emerald-500 animate-ping" />
          <h3 className="text-lg font-bold tracking-tight text-white">
            LangGraph 5-Agent Live Stream
          </h3>
        </div>
        <span className="text-xs font-mono px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-slate-400">
          Real-Time Tracing
        </span>
      </div>

      <div className="relative pl-6 space-y-6 before:absolute before:left-3.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-800">
        {AGENT_ROSTER.map((agentMeta, index) => {
          const matchedStep = steps.find(
            (s) => s.agentName.toLowerCase() === agentMeta.name.toLowerCase()
          ) || {
            id: `agent-step-${index}`,
            agentName: agentMeta.name,
            role: agentMeta.defaultRole,
            status: "PENDING" as const,
            thoughtText: "Awaiting preceding DAG agent completion...",
          };

          return (
            <div key={agentMeta.name} className="relative flex items-start gap-4 group">
              {/* Timeline Dot Icon */}
              <div className="absolute -left-[30px] top-1.5 w-7 h-7 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center text-sm shadow-md group-hover:scale-110 transition-transform">
                {agentMeta.icon}
              </div>

              {/* Card Container */}
              <div className="flex-1 p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all shadow-sm">
                <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                  <div>
                    <h4 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                      {agentMeta.name}
                      <span className="text-xs font-mono font-normal text-slate-400">
                        • {matchedStep.role}
                      </span>
                    </h4>
                  </div>
                  <span
                    className={`text-xs px-2.5 py-0.5 rounded-full border ${getBadgeStyle(
                      matchedStep.status
                    )}`}
                  >
                    {matchedStep.status}
                  </span>
                </div>

                <p className="text-xs text-slate-300 font-mono leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800/60">
                  {matchedStep.thoughtText}
                </p>

                {matchedStep.durationMs && (
                  <div className="mt-2 text-[10px] font-mono text-slate-500 text-right">
                    Execution time: {matchedStep.durationMs}ms
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
