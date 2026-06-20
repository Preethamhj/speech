# AI Speech Assistance System

Local MVP for stutter-aware speech assistance in Kannada and English.

## Architecture

The system follows a simple speech-to-speech pipeline:

1. Audio upload is validated and stored.
2. Whisper Large-v3 transcribes the uploaded audio.
3. An intent-preserving editor removes stuttering repetitions and disfluencies.
4. Sentence Transformers compares the original and corrected transcript.
5. Corrections below `0.90` semantic similarity are rejected.
6. Coqui TTS generates corrected speech from the accepted transcript.
7. The frontend displays original text, corrected text, similarity, and audio playback.

## Why These Components

- **FastAPI**: lightweight Python API framework with good file-upload support.
- **Whisper Large-v3 via faster-whisper**: strong multilingual ASR, including Kannada and English.
- **Qwen-compatible LLM via Transformers**: multilingual instruction following for conservative text editing.
- **Deterministic cleanup fallback**: keeps the MVP usable when a local LLM is not installed.
- **Sentence Transformers `all-MiniLM-L6-v2`**: fast local semantic similarity check.
- **Coqui TTS**: local text-to-speech generation.
- **React + Vite**: small interactive frontend for upload and playback.

Coqui `TTS==0.22.0` only supports Python versions below 3.12. The requirements file installs Coqui on compatible Python versions and installs `pyttsx3` as a local system-voice fallback on Python 3.12+.

## Intent Preservation

The correction service is constrained to remove only stuttering artifacts: repeated words, repeated phrases, repeated syllable fragments, stretched initial sounds, and filler tokens. It does not summarize, paraphrase, or add information. After editing, semantic similarity validation rejects risky corrections.

Intentional emphasis is preserved by design. For example, `very very important` is not collapsed because it can express emphasis.

## Kannada Limitations

Kannada speech recognition can be affected by regional accents, code-switching, clipped syllables, and stuttered partial words. Whisper Large-v3 is a strong baseline, but transcripts may still require conservative correction. This MVP favors meaning preservation over aggressive grammar cleanup.

## Local Setup

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Optional model environment variables:

```powershell
$env:WHISPER_MODEL_SIZE="large-v3"
$env:WHISPER_DEVICE="cpu"
$env:WHISPER_COMPUTE_TYPE="int8"
$env:ENABLE_PHASE2_POSTPROCESSING="true"
$env:QWEN_MODEL_NAME="Qwen/Qwen2.5-1.5B-Instruct"
$env:TTS_MODEL_NAME="tts_models/multilingual/multi-dataset/xtts_v2"
```

To temporarily disable the Phase 2 post-ASR cleanup in the same PowerShell session:

```powershell
$env:ENABLE_PHASE2_POSTPROCESSING="false"
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Tests:

```powershell
cd backend
pytest
```

The first run can take time because Whisper, Sentence Transformers, Qwen, and Coqui TTS models may need to download.
