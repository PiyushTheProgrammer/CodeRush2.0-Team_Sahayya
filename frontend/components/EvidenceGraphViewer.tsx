import React, { useState } from "react";

export interface EvidenceLink {
  passage_id: string;
  transformation_type: string;
  source_url?: string;
  content_snippet: string;
  timestamp: string;
  freshness_score?: number;
}

export interface ClaimNode {
  claim_id: string;
  claim_text: string;
  confidence_score: number;
  is_interpretation: boolean;
  evidence_links: EvidenceLink[];
}

interface EvidenceGraphViewerProps {
  claims: ClaimNode[];
  task_id?: string;
  onDownloadPackage?: () => void;
}

export const EvidenceGraphViewer: React.FC<EvidenceGraphViewerProps> = ({
  claims,
  task_id,
  onDownloadPackage,
}) => {
  const [expandedClaimId, setExpandedClaimId] = useState<string | null>(null);

  const toggleExpand = (claimId: string) => {
    setExpandedClaimId(expandedClaimId === claimId ? null : claimId);
  };

  return (
    <div className="w-full max-w-4xl mx-auto my-6 p-6 rounded-2xl bg-slate-950/80 border border-slate-800 shadow-2xl backdrop-blur-md text-slate-100 font-sans">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-4 mb-6 flex-wrap gap-3">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            Verified Evidence Graph
          </h3>
          <p className="text-xs text-slate-400">
            Fact triangulation, confidence scoring & entailment provenance
          </p>
        </div>

        {onDownloadPackage && (
          <button
            onClick={onDownloadPackage}
            className="flex items-center gap-2 text-xs font-semibold px-4 py-2 rounded-lg bg-white text-black hover:bg-slate-200 transition-colors shadow-md cursor-pointer"
          >
            Download Export Package (.zip)
          </button>
        )}
      </div>


      {/* Claims List */}
      {claims.length === 0 ? (
        <div className="text-center py-10 text-slate-500 text-sm italic font-mono bg-slate-900/40 rounded-xl border border-slate-800/50">
          No verified claim nodes indexed yet for task.
        </div>
      ) : (
        <div className="space-y-4">
          {claims.map((c, index) => {
            const isExpanded = expandedClaimId === c.claim_id;
            const confidencePercent = Math.round(c.confidence_score * 100);

            return (
              <div
                key={c.claim_id || index}
                className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden hover:border-slate-700 transition-all"
              >
                {/* Claim Card Bar */}
                <div
                  onClick={() => toggleExpand(c.claim_id)}
                  className="p-4 flex items-start justify-between gap-4 cursor-pointer select-none hover:bg-slate-800/30 transition-colors"
                >
                  <div className="space-y-1.5 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                        Claim #{index + 1}
                      </span>
                      {c.is_interpretation ? (
                        <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-purple-950 text-purple-400 border border-purple-800">
                          Analytical Interpretation
                        </span>
                      ) : (
                        <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                          Direct Entailment Fact
                        </span>
                      )}
                    </div>
                    <p className="text-sm font-medium text-slate-200 leading-snug">
                      {c.claim_text}
                    </p>
                  </div>

                  {/* Right Score Badge */}
                  <div className="text-right flex flex-col items-end gap-1">
                    <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-md bg-slate-950 border border-slate-800 text-emerald-400">
                      {confidencePercent}% Entailment
                    </span>
                    <span className="text-[10px] font-mono text-slate-500">
                      {isExpanded ? "▲ Hide Sources" : "▼ Expand Sources"}
                    </span>
                  </div>
                </div>

                {/* Expanded Source Details */}
                {isExpanded && (
                  <div className="p-4 bg-slate-950/80 border-t border-slate-800/80 space-y-3">
                    <h5 className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider">
                      Grounding Citations & Provenance Timestamps
                    </h5>
                    {c.evidence_links.length === 0 ? (
                      <p className="text-xs font-mono text-slate-500 italic">
                        No external links associated.
                      </p>
                    ) : (
                      c.evidence_links.map((link, lIdx) => (
                        <div
                          key={link.passage_id || lIdx}
                          className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs space-y-1.5 font-mono"
                        >
                          <div className="flex items-center justify-between text-[11px] text-cyan-400">
                            <span>Link #{lIdx + 1} • {link.transformation_type}</span>
                            <span className="text-slate-500">
                              Freshness: {link.freshness_score ?? 0.88} • {link.timestamp}
                            </span>
                          </div>
                          <p className="text-slate-300 font-sans text-xs italic">
                            "{link.content_snippet}"
                          </p>
                          {link.source_url && (
                            <a
                              href={link.source_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-xs text-blue-400 hover:text-blue-300 underline font-semibold inline-flex items-center gap-1 mt-1"
                            >
                              Click here for reference ↗
                            </a>
                          )}

                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
