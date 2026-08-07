import React, { useState } from "react";

interface GovernanceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  proposedCode?: string;
  astStatus?: "Approved" | "Blocked" | "Pending";
  astReason?: string;
  targetFilePath?: string;
  onApproveStrategy?: (code: string) => Promise<void>;
  onRejectStrategy?: () => void;
}

const DEFAULT_SAMPLE_PATCH = `def rank_passages(passages, query, rrf_k=60):
    """Self-evolved RRF reciprocal rank fusion algorithm."""
    ranked = []
    for p in passages:
        sim_score = p.get("similarity_score", 0.5)
        freshness = p.get("freshness_score", 0.8)
        
        # Calculate hybrid reciprocal score
        combined_score = (sim_score * 0.6) + (freshness * 0.4)
        ranked.append({**p, "rrf_score": round(combined_score, 4)})

    ranked.sort(key=lambda x: x["rrf_score"], reverse=True)
    return ranked
`;

export const GovernanceDrawer: React.FC<GovernanceDrawerProps> = ({
  isOpen,
  onClose,
  proposedCode = DEFAULT_SAMPLE_PATCH,
  astStatus = "Approved",
  astReason = "AST parser clean: No forbidden imports (os, sys, subprocess) or dangerous built-in calls.",
  targetFilePath = "backend/app/rag/strategies/hybrid_strategy.py",
  onApproveStrategy,
  onRejectStrategy,
}) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [editableCode, setEditableCode] = useState(proposedCode);

  if (!isOpen) return null;

  const handleApprove = async () => {
    if (!onApproveStrategy) return;
    setIsSubmitting(true);
    try {
      await onApproveStrategy(editableCode);
      onClose();
    } catch (e) {
      alert(`Approval error: ${e}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-950/70 backdrop-blur-sm transition-opacity flex justify-end">
      <div className="w-full max-w-xl bg-slate-950 border-l border-slate-800 shadow-2xl h-full flex flex-col font-sans text-slate-100">
        {/* Drawer Header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-white">Governance & AST Patch Inspector</h3>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Human-in-the-Loop strategy gatekeeper review
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white text-[15px] font-bold p-1 cursor-pointer"
          >
            Close
          </button>
        </div>

        {/* Drawer Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Target File Info */}
          <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono">
            <span className="text-slate-500 block mb-1">TARGET EVOLUTION FILE:</span>
            <span className="text-slate-200 font-semibold">{targetFilePath}</span>
          </div>

          {/* AST Status Badge */}
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">
                AST Safety Gatekeeper Status
              </span>
              <span
                className={`text-xs font-mono font-bold px-3 py-1 rounded-full border ${
                  astStatus === "Approved"
                    ? "bg-white text-black border-white"
                    : "bg-zinc-900 text-zinc-300 border-zinc-700 animate-pulse"
                }`}
              >
                {astStatus === "Approved" ? "AST APPROVED" : "BLOCKED BY GATEKEEPER"}
              </span>
            </div>
            <p className="text-xs font-mono text-slate-300 bg-slate-950 p-2.5 rounded border border-slate-800/80">
              {astReason}
            </p>
          </div>

          {/* Code Inspector */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-mono text-slate-400 uppercase tracking-wider">
                Proposed Strategy Code (Max 60 lines diff)
              </label>
              <span className="text-xs font-mono text-slate-500">
                {editableCode.split("\n").length} / 60 lines
              </span>
            </div>
            <textarea
              value={editableCode}
              onChange={(e) => setEditableCode(e.target.value)}
              rows={12}
              className="w-full font-mono text-xs p-4 rounded-xl bg-slate-900 border border-slate-800 text-slate-100 focus:outline-none focus:border-slate-500 transition-colors resize-none shadow-inner"
            />
          </div>
        </div>

        {/* Drawer Footer Actions */}
        <div className="p-6 border-t border-slate-800 bg-slate-900/60 flex items-center justify-end gap-3">
          <button
            onClick={() => {
              if (onRejectStrategy) onRejectStrategy();
              onClose();
            }}
            className="px-4 py-2 rounded-xl border border-slate-700 text-slate-300 hover:bg-slate-800 text-xs font-semibold transition-colors cursor-pointer"
          >
            Reject / Rollback
          </button>
          <button
            onClick={handleApprove}
            disabled={isSubmitting || astStatus !== "Approved"}
            className={`px-5 py-2.5 rounded-xl text-xs font-semibold transition-all shadow-md cursor-pointer ${
              astStatus === "Approved" && !isSubmitting
                ? "bg-white text-black hover:bg-slate-200"
                : "bg-slate-800 text-slate-500 cursor-not-allowed"
            }`}
          >
            {isSubmitting ? "Persisting Strategy..." : "Approve Strategy & Activate Version"}
          </button>
        </div>

      </div>
    </div>
  );
};
