import { useState, useEffect, useRef, useCallback } from "react";

const API = "https://podgen-ai.onrender.com/api/v1";
// ─── Design tokens ──────────────────────────────────────────────────────────
const css = `
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #0a0a0f;
    --surface: #12121a;
    --surface2: #1a1a26;
    --border: rgba(255,255,255,0.07);
    --accent: #7c6aff;
    --accent2: #ff6a8a;
    --accent3: #6affcb;
    --text: #f0eeff;
    --muted: #7a788f;
    --glow: 0 0 40px rgba(124,106,255,0.25);
  }

  html, body, #root { height: 100%; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    font-size: 15px;
    line-height: 1.6;
    overflow-x: hidden;
  }

  /* Animated grain overlay */
  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
    pointer-events: none;
    z-index: 9999;
    opacity: 0.35;
  }

  /* Scrollbar */
  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: var(--bg); }
  ::-webkit-scrollbar-thumb { background: var(--accent); border-radius: 2px; }

  h1, h2, h3 { font-family: 'Syne', sans-serif; letter-spacing: -0.02em; }

  .app {
    display: grid;
    grid-template-columns: 280px 1fr;
    grid-template-rows: 64px 1fr;
    min-height: 100vh;
  }

  /* ── Header ── */
  .header {
    grid-column: 1 / -1;
    display: flex;
    align-items: center;
    padding: 0 32px;
    border-bottom: 1px solid var(--border);
    background: rgba(10,10,15,0.9);
    backdrop-filter: blur(20px);
    position: sticky;
    top: 0;
    z-index: 100;
    gap: 16px;
  }

  .logo {
    font-family: 'Syne', sans-serif;
    font-size: 20px;
    font-weight: 800;
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent2) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.03em;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .logo-icon {
    width: 32px;
    height: 32px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    -webkit-text-fill-color: initial;
    flex-shrink: 0;
  }

  .header-right {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .badge {
    font-size: 11px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 20px;
    background: rgba(124,106,255,0.15);
    color: var(--accent);
    border: 1px solid rgba(124,106,255,0.3);
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }

  /* ── Sidebar ── */
  .sidebar {
    border-right: 1px solid var(--border);
    padding: 24px 0;
    overflow-y: auto;
    background: var(--surface);
  }

  .sidebar-section {
    padding: 0 20px;
    margin-bottom: 32px;
  }

  .sidebar-label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 12px;
    padding: 0 4px;
  }

  .nav-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.15s;
    color: var(--muted);
    font-size: 14px;
    font-weight: 500;
    border: 1px solid transparent;
    margin-bottom: 4px;
  }

  .nav-item:hover { background: rgba(255,255,255,0.04); color: var(--text); }

  .nav-item.active {
    background: rgba(124,106,255,0.12);
    color: var(--accent);
    border-color: rgba(124,106,255,0.2);
  }

  .nav-icon { font-size: 16px; width: 20px; text-align: center; }

  .job-card {
    padding: 12px;
    border-radius: 10px;
    border: 1px solid var(--border);
    margin-bottom: 8px;
    cursor: pointer;
    transition: all 0.15s;
    background: rgba(255,255,255,0.02);
  }

  .job-card:hover { border-color: rgba(124,106,255,0.3); background: rgba(124,106,255,0.05); }
  .job-card.active { border-color: rgba(124,106,255,0.5); background: rgba(124,106,255,0.08); }

  .job-title {
    font-size: 12px;
    font-weight: 600;
    font-family: 'Syne', sans-serif;
    color: var(--text);
    margin-bottom: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .job-meta {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    color: var(--muted);
  }

  .status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
  }
  .status-dot.queued { background: #888; }
  .status-dot.processing { background: var(--accent3); animation: pulse 1.5s infinite; }
  .status-dot.completed { background: #4ade80; }
  .status-dot.failed { background: var(--accent2); }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }

  /* ── Main content ── */
  .main {
    overflow-y: auto;
    padding: 32px;
    display: flex;
    flex-direction: column;
    gap: 28px;
  }

  /* ── Panels ── */
  .panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    overflow: hidden;
  }

  .panel-header {
    padding: 20px 24px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .panel-title {
    font-size: 16px;
    font-weight: 700;
    font-family: 'Syne', sans-serif;
    color: var(--text);
  }

  .panel-body { padding: 24px; }

  /* ── Input Tabs ── */
  .tabs {
    display: flex;
    gap: 4px;
    padding: 4px;
    background: rgba(255,255,255,0.04);
    border-radius: 12px;
    width: fit-content;
    margin-bottom: 24px;
  }

  .tab {
    padding: 8px 18px;
    border-radius: 9px;
    border: none;
    cursor: pointer;
    font-size: 13px;
    font-weight: 600;
    font-family: 'DM Sans', sans-serif;
    transition: all 0.15s;
    color: var(--muted);
    background: transparent;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .tab.active {
    background: var(--surface2);
    color: var(--text);
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  }

  .tab:hover:not(.active) { color: var(--text); }

  /* ── Form controls ── */
  .form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 16px;
  }

  .form-group { display: flex; flex-direction: column; gap: 6px; }
  .form-group.full { grid-column: 1 / -1; }

  label {
    font-size: 12px;
    font-weight: 600;
    color: var(--muted);
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }

  input[type=text], input[type=url], textarea, select {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 14px;
    color: var(--text);
    font-size: 14px;
    font-family: 'DM Sans', sans-serif;
    transition: border-color 0.15s, box-shadow 0.15s;
    width: 100%;
    outline: none;
  }

  input:focus, textarea:focus, select:focus {
    border-color: rgba(124,106,255,0.5);
    box-shadow: 0 0 0 3px rgba(124,106,255,0.1);
  }

  textarea { resize: vertical; min-height: 80px; }
  select option { background: var(--surface2); }

  /* ── Upload zone ── */
  .upload-zone {
    border: 2px dashed var(--border);
    border-radius: 12px;
    padding: 36px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    position: relative;
  }

  .upload-zone:hover, .upload-zone.dragging {
    border-color: var(--accent);
    background: rgba(124,106,255,0.05);
  }

  .upload-zone input { position: absolute; inset: 0; opacity: 0; cursor: pointer; }

  .upload-icon { font-size: 32px; margin-bottom: 12px; }
  .upload-text { font-size: 14px; color: var(--muted); }
  .upload-text strong { color: var(--text); }
  .upload-hint { font-size: 12px; color: var(--muted); margin-top: 6px; }
  .upload-filename { font-size: 13px; color: var(--accent3); margin-top: 8px; font-weight: 500; }

  /* ── Buttons ── */
  .btn {
    padding: 12px 24px;
    border-radius: 10px;
    border: none;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
    font-family: 'DM Sans', sans-serif;
    transition: all 0.15s;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    letter-spacing: 0.01em;
  }

  .btn-primary {
    background: linear-gradient(135deg, var(--accent), #9b5de5);
    color: white;
    box-shadow: 0 4px 15px rgba(124,106,255,0.35);
  }

  .btn-primary:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(124,106,255,0.45);
  }

  .btn-primary:active { transform: translateY(0); }

  .btn-secondary {
    background: rgba(255,255,255,0.06);
    color: var(--text);
    border: 1px solid var(--border);
  }

  .btn-secondary:hover { background: rgba(255,255,255,0.1); }

  .btn-danger {
    background: rgba(255,106,138,0.1);
    color: var(--accent2);
    border: 1px solid rgba(255,106,138,0.25);
  }

  .btn-danger:hover { background: rgba(255,106,138,0.2); }

  .btn:disabled { opacity: 0.4; cursor: not-allowed; transform: none !important; }

  .btn-sm { padding: 8px 14px; font-size: 12px; border-radius: 8px; }

  /* ── Progress ── */
  .progress-container { margin: 16px 0; }

  .progress-label {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 8px;
    font-weight: 500;
  }

  .progress-bar {
    height: 6px;
    background: rgba(255,255,255,0.06);
    border-radius: 3px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    border-radius: 3px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
    transition: width 0.5s ease;
    box-shadow: 0 0 10px rgba(124,106,255,0.5);
  }

  .stage-steps {
    display: flex;
    gap: 6px;
    margin-top: 16px;
    flex-wrap: wrap;
  }

  .stage-chip {
    font-size: 11px;
    padding: 4px 10px;
    border-radius: 20px;
    font-weight: 600;
    border: 1px solid transparent;
  }

  .stage-chip.done { background: rgba(74,222,128,0.1); color: #4ade80; border-color: rgba(74,222,128,0.2); }
  .stage-chip.active { background: rgba(124,106,255,0.15); color: var(--accent); border-color: rgba(124,106,255,0.3); animation: pulse 1.5s infinite; }
  .stage-chip.pending { background: rgba(255,255,255,0.03); color: var(--muted); border-color: var(--border); }

  /* ── Audio player ── */
  .player {
    background: var(--surface2);
    border-radius: 14px;
    padding: 20px 24px;
    border: 1px solid var(--border);
  }

  .player-title {
    font-family: 'Syne', sans-serif;
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 4px;
    color: var(--text);
  }

  .player-desc {
    font-size: 13px;
    color: var(--muted);
    margin-bottom: 16px;
  }

  .audio-element {
    width: 100%;
    accent-color: var(--accent);
    height: 36px;
    border-radius: 8px;
    margin-bottom: 12px;
  }

  .player-controls {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }

  .tags-list {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 12px;
  }

  .tag {
    font-size: 11px;
    padding: 3px 10px;
    background: rgba(124,106,255,0.1);
    border: 1px solid rgba(124,106,255,0.2);
    border-radius: 20px;
    color: var(--accent);
    font-weight: 500;
  }

  /* ── Script editor ── */
  .script-editor {
    width: 100%;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    color: var(--text);
    font-family: 'DM Mono', 'Fira Code', monospace;
    font-size: 13px;
    line-height: 1.7;
    min-height: 320px;
    resize: vertical;
    outline: none;
    transition: border-color 0.15s;
  }

  .script-editor:focus { border-color: rgba(124,106,255,0.4); }

  /* ── Quality score ── */
  .score-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    margin-top: 16px;
  }

  .score-item {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px;
  }

  .score-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; }

  .score-value {
    font-size: 24px;
    font-family: 'Syne', sans-serif;
    font-weight: 700;
  }

  .score-bar {
    height: 3px;
    background: rgba(255,255,255,0.06);
    border-radius: 2px;
    margin-top: 8px;
  }

  .score-bar-fill {
    height: 100%;
    border-radius: 2px;
    background: linear-gradient(90deg, var(--accent), var(--accent3));
    transition: width 1s ease;
  }

  /* ── Empty state ── */
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 20px;
    text-align: center;
    color: var(--muted);
  }

  .empty-icon { font-size: 48px; margin-bottom: 16px; opacity: 0.5; }
  .empty-title { font-family: 'Syne', sans-serif; font-size: 18px; font-weight: 700; color: var(--text); margin-bottom: 8px; }
  .empty-desc { font-size: 14px; max-width: 300px; }

  /* ── Settings panel ── */
  .settings-section { margin-bottom: 24px; }
  .settings-section-title {
    font-size: 12px;
    font-weight: 700;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 12px;
  }

  .advanced-toggle {
    background: none;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--muted);
    font-size: 13px;
    font-family: 'DM Sans', sans-serif;
    padding: 8px 0;
    transition: color 0.15s;
  }

  .advanced-toggle:hover { color: var(--text); }

  /* ── Alert / Toast ── */
  .toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px 18px;
    font-size: 14px;
    font-weight: 500;
    z-index: 1000;
    display: flex;
    align-items: center;
    gap: 10px;
    animation: slideUp 0.3s ease;
    max-width: 320px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
  }

  .toast.success { border-color: rgba(74,222,128,0.3); color: #4ade80; }
  .toast.error { border-color: rgba(255,106,138,0.3); color: var(--accent2); }
  .toast.info { border-color: rgba(124,106,255,0.3); color: var(--accent); }

  @keyframes slideUp {
    from { transform: translateY(20px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
  }

  /* ── Waveform animation ── */
  .waveform {
    display: flex;
    align-items: center;
    gap: 3px;
    height: 24px;
  }

  .wave-bar {
    width: 3px;
    background: var(--accent);
    border-radius: 2px;
    animation: wave 1.2s ease-in-out infinite;
  }

  @keyframes wave {
    0%, 100% { height: 4px; }
    50% { height: 20px; }
  }

  .divider { height: 1px; background: var(--border); margin: 20px 0; }

  .text-accent { color: var(--accent); }
  .text-muted { color: var(--muted); }
  .text-sm { font-size: 13px; }
  .mt-8 { margin-top: 8px; }
  .mt-12 { margin-top: 12px; }
  .mt-16 { margin-top: 16px; }

  .flex { display: flex; }
  .items-center { align-items: center; }
  .gap-8 { gap: 8px; }
  .gap-12 { gap: 12px; }
  .justify-between { justify-content: space-between; }
  .flex-wrap { flex-wrap: wrap; }

  @media (max-width: 768px) {
    .app { grid-template-columns: 1fr; grid-template-rows: 64px auto 1fr; }
    .sidebar { display: none; }
    .form-grid { grid-template-columns: 1fr; }
    .score-grid { grid-template-columns: 1fr; }
  }
`;

// ─── Constants ───────────────────────────────────────────────────────────────
const STAGES = ["queued","extracting","extracted","indexing","indexed","planning","planned","scripting","scripted","metadata","metadata_done","generating_audio","completed"];
const STAGE_LABELS = { queued:"Queued", extracting:"Extracting", extracted:"Extracted", indexing:"Indexing", indexed:"Indexed", planning:"Planning", planned:"Planned", scripting:"Scripting", scripted:"Scripted", metadata:"Metadata", metadata_done:"Metadata", generating_audio:"Audio", completed:"Done" };

function stageIndex(s) { return STAGES.indexOf(s); }

// ─── Components ──────────────────────────────────────────────────────────────

function Waveform() {
  return (
    <div className="waveform">
      {[0.4, 0.7, 1, 0.6, 0.9, 0.5, 0.8, 0.4, 0.7, 0.6].map((delay, i) => (
        <div key={i} className="wave-bar" style={{ animationDelay: `${delay * 0.5}s` }} />
      ))}
    </div>
  );
}

function Toast({ message, type, onClose }) {
  useEffect(() => { const t = setTimeout(onClose, 4000); return () => clearTimeout(t); }, [onClose]);
  const icons = { success: "✓", error: "✕", info: "ℹ" };
  return <div className={`toast ${type}`}><span>{icons[type]}</span>{message}</div>;
}

function StatusDot({ status }) {
  return <div className={`status-dot ${status}`} />;
}

function JobCard({ job, active, onClick }) {
  const title = job.title || job.metadata?.topic || job.metadata?.url || job.metadata?.filename || "Untitled";
  return (
    <div className={`job-card ${active ? "active" : ""}`} onClick={onClick}>
      <div className="job-title">{title}</div>
      <div className="job-meta">
        <StatusDot status={job.status} />
        <span>{job.status}</span>
        {job.status === "processing" && <Waveform />}
      </div>
    </div>
  );
}

function ProgressTracker({ job }) {
  const currentIdx = stageIndex(job.stage);
  return (
    <div className="progress-container">
      <div className="progress-label">
        <span>{STAGE_LABELS[job.stage] || job.stage}</span>
        <span>{job.progress}%</span>
      </div>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${job.progress}%` }} />
      </div>
      <div className="stage-steps">
        {STAGES.filter(s => s !== "extracted" && s !== "indexed" && s !== "planned" && s !== "scripted" && s !== "metadata").map(s => {
          const idx = stageIndex(s);
          const state = idx < currentIdx ? "done" : idx === currentIdx ? "active" : "pending";
          return <span key={s} className={`stage-chip ${state}`}>{idx < currentIdx ? "✓ " : ""}{STAGE_LABELS[s]}</span>;
        })}
      </div>
    </div>
  );
}

function AudioPlayer({ job, apiBase }) {
  const audioSrc = job.audio_url ? `${apiBase.replace("/api/v1", "")}${job.audio_url}` : null;
  const score = job.quality_score || {};
  const metrics = ["coherence","engagement","naturalness","information_density"].filter(k => score[k]);
  const colors = { coherence: "#7c6aff", engagement: "#ff6a8a", naturalness: "#6affcb", information_density: "#ffca6a" };

  return (
    <div>
      <div className="player">
        <div className="player-title">{job.title || "Your Podcast"}</div>
        <div className="player-desc">{job.description || ""}</div>
        {audioSrc ? (
          <audio controls className="audio-element" src={audioSrc} />
        ) : (
          <div style={{ padding: "16px 0", color: "var(--muted)", fontSize: "13px" }}>
            🎙️ Audio generation in progress…
          </div>
        )}
        <div className="player-controls">
          {audioSrc && (
            <a href={audioSrc} download={`${(job.title || "podcast").replace(/\s+/g, "_")}.mp3`} className="btn btn-secondary btn-sm">
              ⬇ Download MP3
            </a>
          )}
          {job.script && (
            <a
              href={`data:text/plain;charset=utf-8,${encodeURIComponent(job.script)}`}
              download="podcast_script.txt"
              className="btn btn-secondary btn-sm"
            >
              📄 Export Script
            </a>
          )}
        </div>
        {job.tags?.length > 0 && (
          <div className="tags-list">
            {job.tags.map(t => <span key={t} className="tag">{t}</span>)}
          </div>
        )}
      </div>

      {metrics.length > 0 && (
        <div className="mt-16">
          <div className="text-sm text-muted" style={{ fontWeight: 600, marginBottom: 8 }}>QUALITY ANALYSIS</div>
          <div className="score-grid">
            {metrics.map(k => (
              <div key={k} className="score-item">
                <div className="score-label">{k.replace("_", " ")}</div>
                <div className="score-value" style={{ color: colors[k] }}>{score[k]}<span style={{ fontSize: 14, color: "var(--muted)" }}>/10</span></div>
                <div className="score-bar"><div className="score-bar-fill" style={{ width: `${score[k] * 10}%`, background: colors[k] }} /></div>
              </div>
            ))}
          </div>
          {score.feedback && <div className="mt-12 text-sm text-muted">{score.feedback}</div>}
        </div>
      )}
    </div>
  );
}

function ScriptViewer({ job, onSave, saving }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(job.script || "");

  useEffect(() => { setDraft(job.script || ""); }, [job.script]);

  const handleSave = async () => {
    await onSave(draft);
    setEditing(false);
  };

  if (!job.script) {
    return <div className="empty-state"><div className="empty-icon">📝</div><div className="empty-title">No script yet</div><div className="empty-desc">Script will appear here once generated.</div></div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between" style={{ marginBottom: 12 }}>
        <span className="text-sm text-muted">{job.script.split("\n").length} lines · {Math.round(job.script.length / 5)} words</span>
        <div className="flex gap-8">
          {editing ? (
            <>
              <button className="btn btn-secondary btn-sm" onClick={() => { setEditing(false); setDraft(job.script); }}>Cancel</button>
              <button className="btn btn-primary btn-sm" onClick={handleSave} disabled={saving}>{saving ? "Saving…" : "Save Changes"}</button>
            </>
          ) : (
            <button className="btn btn-secondary btn-sm" onClick={() => setEditing(true)}>✏️ Edit Script</button>
          )}
        </div>
      </div>
      {editing ? (
        <textarea
          className="script-editor"
          value={draft}
          onChange={e => setDraft(e.target.value)}
          style={{ height: 440 }}
        />
      ) : (
        <div style={{ background: "var(--bg)", borderRadius: 12, border: "1px solid var(--border)", padding: 16, maxHeight: 440, overflowY: "auto" }}>
          {job.script.split("\n").map((line, i) => {
            const hostMatch = line.match(/^(HOST|GUEST)\s*:/);
            const speaker = hostMatch ? hostMatch[1] : null;
            const rest = hostMatch ? line.slice(hostMatch[0].length).trim() : line;
            return (
              <div key={i} style={{ marginBottom: 4 }}>
                {speaker ? (
                  <span>
                    <span style={{ color: speaker === "HOST" ? "var(--accent)" : "var(--accent2)", fontWeight: 700, fontFamily: "Syne, sans-serif", fontSize: 12 }}>{speaker}: </span>
                    <span style={{ fontSize: 13, color: "var(--text)" }}>{rest}</span>
                  </span>
                ) : (
                  <span style={{ fontSize: 12, color: "var(--muted)", fontStyle: "italic" }}>{line}</span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ─── GenerateForm ─────────────────────────────────────────────────────────────
function GenerateForm({ onSubmit, loading }) {
  const [tab, setTab] = useState("topic");
  const [topic, setTopic] = useState("");
  const [url, setUrl] = useState("");
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [config, setConfig] = useState({
    style: "educational", audience: "general", tone: "conversational",
    duration_minutes: 10, language: "en",
    host_name: "Alex", guest_name: "Jordan",
    host_personality: "curious and engaging",
    guest_personality: "knowledgeable and enthusiastic"
  });

  const setC = (k, v) => setConfig(prev => ({ ...prev, [k]: v }));

  const handleSubmit = () => {
    if (tab === "topic" && !topic.trim()) return;
    if (tab === "url" && !url.trim()) return;
    if (tab === "document" && !file) return;
    onSubmit({ tab, topic, url, file, config });
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <span style={{ fontSize: 20 }}>🎙️</span>
        <span className="panel-title">Generate New Podcast</span>
      </div>
      <div className="panel-body">
        <div className="tabs">
          {[["topic","💡","Topic"],["url","🌐","URL"],["document","📄","Document"]].map(([id,icon,label]) => (
            <button key={id} className={`tab ${tab === id ? "active" : ""}`} onClick={() => setTab(id)}>
              {icon} {label}
            </button>
          ))}
        </div>

        {tab === "topic" && (
          <div className="form-group full">
            <label>Podcast Topic</label>
            <textarea placeholder="e.g. The future of quantum computing and its impact on cryptography…" value={topic} onChange={e => setTopic(e.target.value)} style={{ minHeight: 100 }} />
          </div>
        )}

        {tab === "url" && (
          <div className="form-group full">
            <label>Website URL</label>
            <input type="url" placeholder="https://example.com/article" value={url} onChange={e => setUrl(e.target.value)} />
          </div>
        )}

        {tab === "document" && (
          <div
            className={`upload-zone ${dragging ? "dragging" : ""}`}
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={e => { e.preventDefault(); setDragging(false); const f = e.dataTransfer.files[0]; if (f) setFile(f); }}
          >
            <input type="file" accept=".pdf,.docx,.txt" onChange={e => setFile(e.target.files[0])} />
            <div className="upload-icon">📎</div>
            <div className="upload-text"><strong>Drop file here</strong> or click to browse</div>
            <div className="upload-hint">PDF, DOCX, TXT · Max 20MB</div>
            {file && <div className="upload-filename">✓ {file.name}</div>}
          </div>
        )}

        <div className="divider" />

        <div className="form-grid">
          <div className="form-group">
            <label>Style</label>
            <select value={config.style} onChange={e => setC("style", e.target.value)}>
              <option value="educational">📚 Educational</option>
              <option value="debate">⚡ Debate</option>
              <option value="storytelling">📖 Storytelling</option>
            </select>
          </div>
          <div className="form-group">
            <label>Audience</label>
            <select value={config.audience} onChange={e => setC("audience", e.target.value)}>
              <option value="general">👥 General</option>
              <option value="technical">🔧 Technical</option>
              <option value="experts">🎓 Experts</option>
              <option value="kids">🌟 Kids</option>
            </select>
          </div>
          <div className="form-group">
            <label>Tone</label>
            <select value={config.tone} onChange={e => setC("tone", e.target.value)}>
              <option value="conversational">💬 Conversational</option>
              <option value="formal">👔 Formal</option>
              <option value="casual">😊 Casual</option>
              <option value="excited">🚀 Excited</option>
            </select>
          </div>
          <div className="form-group">
            <label>Duration (min)</label>
            <select value={config.duration_minutes} onChange={e => setC("duration_minutes", parseInt(e.target.value))}>
              {[5,10,15,20,30].map(v => <option key={v} value={v}>{v} min</option>)}
            </select>
          </div>
        </div>

        <button className="advanced-toggle" onClick={() => setShowAdvanced(!showAdvanced)}>
          {showAdvanced ? "▲" : "▼"} Advanced Settings
        </button>

        {showAdvanced && (
          <div className="form-grid" style={{ marginTop: 12 }}>
            <div className="form-group">
              <label>Host Name</label>
              <input type="text" value={config.host_name} onChange={e => setC("host_name", e.target.value)} placeholder="Alex" />
            </div>
            <div className="form-group">
              <label>Guest Name</label>
              <input type="text" value={config.guest_name} onChange={e => setC("guest_name", e.target.value)} placeholder="Jordan" />
            </div>
            <div className="form-group">
              <label>Host Personality</label>
              <input type="text" value={config.host_personality} onChange={e => setC("host_personality", e.target.value)} />
            </div>
            <div className="form-group">
              <label>Guest Personality</label>
              <input type="text" value={config.guest_personality} onChange={e => setC("guest_personality", e.target.value)} />
            </div>
          </div>
        )}

        <div style={{ marginTop: 20 }}>
          <button className="btn btn-primary" onClick={handleSubmit} disabled={loading} style={{ width: "100%", justifyContent: "center", padding: "14px" }}>
            {loading ? <><Waveform /> Generating…</> : "🚀 Generate Podcast"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── JobDetail ────────────────────────────────────────────────────────────────
function JobDetail({ job, apiBase, onRefresh, onCancel, onScriptSave }) {
  const [activeTab, setActiveTab] = useState("player");
  const [saving, setSaving] = useState(false);

  const handleScriptSave = async (script) => {
    setSaving(true);
    await onScriptSave(job.job_id, script);
    setSaving(false);
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <span style={{ fontSize: 18 }}>🎧</span>
        <div>
          <div className="panel-title">{job.title || "Generating Podcast…"}</div>
          <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 2 }}>
            {job.input_type} · {new Date(job.created_at).toLocaleString()}
          </div>
        </div>
        <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
          {job.status === "processing" && (
            <button className="btn btn-danger btn-sm" onClick={() => onCancel(job.job_id)}>✕ Cancel</button>
          )}
          <button className="btn btn-secondary btn-sm" onClick={onRefresh}>↺ Refresh</button>
        </div>
      </div>

      <div className="panel-body">
        {job.status !== "completed" && job.status !== "failed" && (
          <ProgressTracker job={job} />
        )}

        {job.status === "failed" && (
          <div style={{ padding: "16px", background: "rgba(255,106,138,0.08)", borderRadius: 10, border: "1px solid rgba(255,106,138,0.2)", color: "var(--accent2)", marginBottom: 16, fontSize: 13 }}>
            ⚠ Error: {job.error}
          </div>
        )}

        {(job.script || job.audio_url) && (
          <>
            <div className="tabs" style={{ marginBottom: 20 }}>
              {[["player","🎧","Player"],["script","📝","Script"]].map(([id,icon,label]) => (
                <button key={id} className={`tab ${activeTab === id ? "active" : ""}`} onClick={() => setActiveTab(id)}>
                  {icon} {label}
                </button>
              ))}
            </div>

            {activeTab === "player" && <AudioPlayer job={job} apiBase={apiBase} />}
            {activeTab === "script" && <ScriptViewer job={job} onSave={handleScriptSave} saving={saving} />}
          </>
        )}
      </div>
    </div>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function PodGenAI() {
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState(null);
  const [view, setView] = useState("generate");
  const [generating, setGenerating] = useState(false);
  const [toast, setToast] = useState(null);
  const pollRef = useRef(null);

  const showToast = (message, type = "info") => setToast({ message, type });

  // ── Polling ──
  const fetchJobs = useCallback(async () => {
    try {
      const res = await fetch(`${API}/jobs`);
      if (!res.ok) return;
      const data = await res.json();
      setJobs(data.jobs || []);
    } catch (_) {}
  }, []);

  useEffect(() => {
    fetchJobs();
    pollRef.current = setInterval(fetchJobs, 3000);
    return () => clearInterval(pollRef.current);
  }, [fetchJobs]);

  const selectedJob = jobs.find(j => j.job_id === selectedJobId);

  // ── Generate ──
  const handleGenerate = async ({ tab, topic, url, file, config }) => {
    setGenerating(true);
    try {
      let res, body;
      if (tab === "topic") {
        res = await fetch(`${API}/generate/topic`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ topic, ...config }),
        });
      } else if (tab === "url") {
        res = await fetch(`${API}/generate/url`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url, ...config }),
        });
      } else {
        const form = new FormData();
        form.append("file", file);
        Object.entries(config).forEach(([k, v]) => form.append(k, v));
        res = await fetch(`${API}/generate/document`, { method: "POST", body: form });
      }

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed");

      showToast("Podcast generation started!", "success");
      setSelectedJobId(data.job_id);
      setView("result");
      fetchJobs();
    } catch (e) {
      showToast(e.message, "error");
    } finally {
      setGenerating(false);
    }
  };

  // ── Cancel ──
  const handleCancel = async (jobId) => {
    try {
      await fetch(`${API}/job/${jobId}`, { method: "DELETE" });
      showToast("Job cancelled", "info");
      fetchJobs();
    } catch (_) {}
  };

  // ── Script save ──
  const handleScriptSave = async (jobId, script) => {
    try {
      await fetch(`${API}/job/script`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobId, script }),
      });
      showToast("Script saved!", "success");
      fetchJobs();
    } catch (_) {}
  };

  return (
    <>
      <style>{css}</style>
      <div className="app">
        {/* Header */}
        <header className="header">
          <div className="logo">
            <div className="logo-icon">🎙</div>
            PodGen AI
          </div>
          <div className="header-right">
            <span className="badge">Beta</span>
            <span style={{ fontSize: 13, color: "var(--muted)" }}>Powered by Groq</span>
          </div>
        </header>

        {/* Sidebar */}
        <aside className="sidebar">
          <div className="sidebar-section">
            <div className="sidebar-label">Create</div>
            <div className={`nav-item ${view === "generate" ? "active" : ""}`} onClick={() => setView("generate")}>
              <span className="nav-icon">✨</span> New Podcast
            </div>
          </div>

          <div className="sidebar-section">
            <div className="sidebar-label">History ({jobs.length})</div>
            {jobs.length === 0 && (
              <div style={{ fontSize: 12, color: "var(--muted)", padding: "4px 4px" }}>No podcasts yet</div>
            )}
            {jobs.map(job => (
              <JobCard
                key={job.job_id}
                job={job}
                active={selectedJobId === job.job_id}
                onClick={() => { setSelectedJobId(job.job_id); setView("result"); }}
              />
            ))}
          </div>
        </aside>

        {/* Main */}
        <main className="main">
          {view === "generate" && (
            <>
              <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
                <div>
                  <h1 style={{ fontSize: 28, fontWeight: 800, marginBottom: 4 }}>
                    Create a Podcast <span style={{ color: "var(--accent)" }}>in seconds</span>
                  </h1>
                  <p style={{ fontSize: 14, color: "var(--muted)" }}>AI-powered script + audio from any topic, URL, or document</p>
                </div>
              </div>
              <GenerateForm onSubmit={handleGenerate} loading={generating} />
            </>
          )}

          {view === "result" && selectedJob && (
            <JobDetail
              job={selectedJob}
              apiBase={API}
              onRefresh={fetchJobs}
              onCancel={handleCancel}
              onScriptSave={handleScriptSave}
            />
          )}

          {view === "result" && !selectedJob && (
            <div className="panel">
              <div className="empty-state">
                <div className="empty-icon">🎧</div>
                <div className="empty-title">Select a podcast</div>
                <div className="empty-desc">Choose a job from the sidebar or generate a new one.</div>
              </div>
            </div>
          )}
        </main>
      </div>

      {toast && (
        <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />
      )}
    </>
  );
}
