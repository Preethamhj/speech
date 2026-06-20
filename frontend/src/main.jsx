import React, { useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { CheckCircle2, Loader2, Mic, Upload, Volume2, XCircle } from "lucide-react";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8001";

function App() {
  const [file, setFile] = useState(null);
  const [fileKind, setFileKind] = useState("audio");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [stageLogs, setStageLogs] = useState([]);
  const stageTimers = useRef([]);

  const audioUrl = useMemo(() => {
    if (!result?.audioUrl) return "";
    return result.audioUrl;
  }, [result]);

  async function processAudio() {
    if (!file) {
      setError("Choose an audio file first.");
      return;
    }

    setIsProcessing(true);
    setError("");
    setResult(null);
    startStageLogs(fileKind);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const endpoint = fileKind === "video" ? "video-file" : "audio-file";
      const response = await fetch(`${API_BASE}/${endpoint}`, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Processing failed.");
      }
      const blob = await response.blob();
      clearStageTimers();
      appendStageLog("Corrected audio received from backend.", "done");
      setResult({
        original_transcript: decodeHeader(response.headers.get("X-Original-Transcript")),
        corrected_transcript: decodeHeader(response.headers.get("X-Corrected-Transcript")),
        language: response.headers.get("X-Language") || "unknown",
        similarity_score: Number(response.headers.get("X-Similarity-Score") || 0),
        accepted: response.headers.get("X-Correction-Accepted") === "true",
        reason: decodeHeader(response.headers.get("X-Correction-Reason")),
        pipeline_stages: decodeHeader(response.headers.get("X-Pipeline-Stages")),
        audioUrl: URL.createObjectURL(blob),
      });
    } catch (err) {
      clearStageTimers();
      appendStageLog(`Failed: ${err.message}`, "error");
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  }

  function appendStageLog(message, status = "active") {
    setStageLogs((current) => [
      ...current,
      {
        id: `${Date.now()}-${current.length}`,
        time: new Date().toLocaleTimeString(),
        message,
        status,
      },
    ]);
  }

  function startStageLogs(kind) {
    clearStageTimers();
    setStageLogs([]);
    const stages =
      kind === "video"
        ? [
            "Uploading video file.",
            "Backend is extracting WAV audio with ffmpeg.",
            "Whisper is transcribing extracted speech.",
            "Correction engine is removing disfluencies.",
            "Similarity validation is checking meaning preservation.",
            "TTS is generating corrected audio.",
          ]
        : [
            "Uploading audio file.",
            "Whisper is transcribing speech.",
            "Correction engine is removing disfluencies.",
            "Similarity validation is checking meaning preservation.",
            "TTS is generating corrected audio.",
          ];

    stages.forEach((stage, index) => {
      const timer = window.setTimeout(() => appendStageLog(stage), index * 1400);
      stageTimers.current.push(timer);
    });
  }

  function clearStageTimers() {
    stageTimers.current.forEach((timer) => window.clearTimeout(timer));
    stageTimers.current = [];
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <div className="topbar">
          <div>
            <p className="eyebrow">Kannada and English MVP</p>
            <h1>Speech Assistance</h1>
          </div>
          <div className="status-pill">
            <Mic size={18} />
            Intent preserving
          </div>
        </div>

          <div className="controls">
          <div className="file-kind" aria-label="File type">
            <button
              className={fileKind === "audio" ? "active" : ""}
              type="button"
              onClick={() => {
                setFileKind("audio");
                setFile(null);
              }}
            >
              Audio
            </button>
            <button
              className={fileKind === "video" ? "active" : ""}
              type="button"
              onClick={() => {
                setFileKind("video");
                setFile(null);
              }}
            >
              Video
            </button>
          </div>
          <label className="upload-box">
            <Upload size={22} />
            <span>
              {file
                ? file.name
                : fileKind === "video"
                  ? "Select mp4, mov, mkv, avi, webm, or m4v video"
                  : "Select wav, mp3, m4a, flac, ogg, or webm audio"}
            </span>
            <input
              type="file"
              accept={
                fileKind === "video"
                  ? "video/mp4,video/quicktime,video/x-matroska,video/x-msvideo,video/webm,video/x-m4v"
                  : "audio/wav,audio/mpeg,audio/mp3,audio/mp4,audio/x-m4a,audio/flac,audio/ogg,audio/webm"
              }
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
          </label>
          <button className="process-button" type="button" onClick={processAudio} disabled={isProcessing}>
            {isProcessing ? <Loader2 className="spin" size={20} /> : <Volume2 size={20} />}
            {isProcessing ? "Processing" : "Process"}
          </button>
        </div>

        {error && (
          <div className="message error">
            <XCircle size={18} />
            {error}
          </div>
        )}

        {stageLogs.length > 0 && (
          <div className="stage-panel">
            <h2>Pipeline Logs</h2>
            <ol>
              {stageLogs.map((log) => (
                <li key={log.id} className={log.status}>
                  <span>{log.time}</span>
                  <p>{log.message}</p>
                </li>
              ))}
            </ol>
          </div>
        )}

        {result && (
          <>
            <div className="metrics">
              <div>
                <span>Similarity</span>
                <strong>{Number(result.similarity_score).toFixed(2)}</strong>
              </div>
              <div>
                <span>Language</span>
                <strong>{result.language}</strong>
              </div>
              <div className={result.accepted ? "accepted" : "rejected"}>
                {result.accepted ? <CheckCircle2 size={18} /> : <XCircle size={18} />}
                <strong>{result.accepted ? "Accepted" : "Rejected"}</strong>
              </div>
            </div>

            <div className="transcripts">
              <article>
                <h2>Original Transcript</h2>
                <p>{result.original_transcript}</p>
              </article>
              <article>
                <h2>Corrected Transcript</h2>
                <p>{result.corrected_transcript}</p>
              </article>
            </div>

            <div className="player">
              <h2>Corrected Audio</h2>
              <audio controls src={audioUrl} />
              <p>{result.reason}</p>
              {result.pipeline_stages && <p>Server stages: {result.pipeline_stages}</p>}
            </div>
          </>
        )}
      </section>
    </main>
  );
}

function decodeHeader(value) {
  if (!value) return "";
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

createRoot(document.getElementById("root")).render(<App />);
