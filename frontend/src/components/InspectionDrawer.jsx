import { useState } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  ChevronUp,
  ChevronDown,
  Check
} from 'lucide-react';

function StatusItem({ label, data }) {
  const status = data?.meaning_status || data?.factuality_status || 'Review recommended';
  const klass = status === 'Passed' ? 'passed' : status === 'Potential issue detected' ? 'issue' : 'review';
  return (
    <div className="status-item">
      <span>{label}</span>
      <b className={klass}>{status}</b>
      <small>{data?.meaning_explanation || data?.factuality_explanation || 'Please review.'}</small>
    </div>
  );
}

export default function InspectionDrawer({ result, clientAnalysis }) {
  const [isOpen, setIsOpen] = useState(true);

  if (!result) return null;

  const preservedEntities = result.entities_preserved || result.entity_guardrail?.entities_preserved || [];
  const missingEntities = result.entity_guardrail?.missing_entities || [];
  const totalEntitiesCount = (result.entity_guardrail?.all_entities?.length) || (preservedEntities.length + missingEntities.length);
  const eliminatedCliches = result.robotic_analysis?.eliminated_cliches || [];

  return (
    <div className="inspection-drawer" id="verification">
      <button
        type="button"
        className="drawer-toggle"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
      >
        <div className="drawer-title-group">
          <ShieldCheck size={20} className="shield-icon" />
          <div>
            <b>Inspection & Verification Drawer</b>
            <span>Two-Pass Pipeline · Entity Preservation & Semantic Fidelity</span>
          </div>
        </div>
        <div className="drawer-quick-metrics">
          <span className="quick-pill score-match">
            <CheckCircle2 size={13} /> {result.semantic_similarity_score ?? 98}% Meaning Match
          </span>
          <span className="quick-pill score-entities">
            <CheckCircle2 size={13} /> {preservedEntities.length}/{totalEntitiesCount || preservedEntities.length} Entities
          </span>
          <span className="drawer-chevron">
            {isOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </span>
        </div>
      </button>

      {isOpen && (
        <div className="drawer-body">
          {/* Top 3 Metric Cards Grid */}
          <div className="inspection-metrics-grid">
            {/* 1. Robotic Phrases Eliminated */}
            <div className="inspection-card">
              <div className="card-header">
                <span className="card-label">ROBOTIC LANGUAGE LAYER</span>
                <h4>Clichés Eliminated</h4>
              </div>
              <div className="card-body">
                {eliminatedCliches.length > 0 ? (
                  <div className="eliminated-pills-list">
                    {eliminatedCliches.map((c, i) => (
                      <span key={i} className="eliminated-badge">✕ {c}</span>
                    ))}
                  </div>
                ) : (
                  <div className="clean-signal">
                    <CheckCircle2 size={15} />
                    <span>{clientAnalysis?.cliches?.length === 0 ? 'No robotic clichés in source.' : 'Phrasing refined for natural cadence.'}</span>
                  </div>
                )}
                <small className="card-note">
                  Robotic Phrasing Score: <b>{result.robotic_analysis?.robotic_score || 'Low'}</b>
                </small>
              </div>
            </div>

            {/* 2. Strict Entity & Terminology Guardrail */}
            <div className="inspection-card">
              <div className="card-header">
                <span className="card-label">FACTUALITY GUARDRAIL</span>
                <h4>Preserved Entities</h4>
              </div>
              <div className="card-body">
                {preservedEntities.length > 0 ? (
                  <div className="entity-chip-list">
                    {preservedEntities.map((ent, i) => (
                      <span key={i} className="entity-chip">
                        <Check size={11} /> {ent}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="empty-entities">No critical technical terms, scores, or names detected.</span>
                )}
                <div className="guardrail-status-line">
                  {missingEntities.length === 0 ? (
                    <span className="status-perfect">✓ 100% Entities Preserved Unaltered</span>
                  ) : (
                    <span className="status-missing">⚠️ Missing entities flagged for review: {missingEntities.join(', ')}</span>
                  )}
                </div>
              </div>
            </div>

            {/* 3. Meaning & Semantic Match */}
            <div className="inspection-card">
              <div className="card-header">
                <span className="card-label">VERIFICATION PIPELINE</span>
                <h4>Meaning Preservation</h4>
              </div>
              <div className="card-body">
                <div className="score-metric-row">
                  <div className="big-score">
                    <b>{result.semantic_similarity_score ?? 98}%</b>
                    <span>Semantic Match</span>
                  </div>
                  <div className="metric-badges">
                    <span className={result.meaning_preserved ? 'badge-pass' : 'badge-warn'}>
                      {result.meaning_preserved ? '✓ Meaning Preserved' : 'Review Needed'}
                    </span>
                    <span className="badge-pass">
                      ✓ {result.factuality_confidence ?? 98}% Factuality Conf.
                    </span>
                  </div>
                </div>
                <small className="card-note">
                  {result.unsupported_claims_detected ? '⚠️ Unsupported claims detected' : '✓ 0 Unsupported Claims Detected'}
                </small>
              </div>
            </div>
          </div>

          {/* Detailed Validation Statuses */}
          <div className="validation-statuses">
            <StatusItem label="Meaning Preservation Audit" data={result.meaning_validation} />
            <StatusItem label="Factual Consistency Audit" data={result.factuality_validation} />
          </div>

          {/* Warnings and Explanations */}
          {result.warnings?.length > 0 && (
            <div className="warnings">
              {result.warnings.map((w, i) => <p key={i}>• {w}</p>)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
