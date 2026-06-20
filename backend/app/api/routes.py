from pathlib import Path
import logging
from urllib.parse import quote

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from app.services.pipeline_service import SpeechAssistancePipeline
from app.services.video_service import VideoAudioExtractionService
from app.utils.errors import SpeechAssistError
from app.utils.storage import load_debug_transcript, save_upload, save_video_upload

router = APIRouter()
logger = logging.getLogger(__name__)
pipeline = SpeechAssistancePipeline()
video_extractor = VideoAudioExtractionService()


@router.post(
    "/audio-file",
    response_class=FileResponse,
    summary="Upload audio and receive corrected speech audio",
)
async def process_audio_file(file: UploadFile = File(...)) -> FileResponse:
    logger.info("audio request received | filename=%s content_type=%s", file.filename, file.content_type)
    try:
        audio_id, audio_path, size_bytes = await save_upload(file)
        logger.info("audio upload saved | audio_id=%s size_bytes=%s path=%s", audio_id, size_bytes, audio_path)
        result = pipeline.process(audio_path)
        logger.info(
            "audio request completed | audio_id=%s accepted=%s similarity=%s output=%s",
            audio_id,
            result["accepted"],
            result["similarity_score"],
            result["corrected_audio_path"],
        )
        return _corrected_audio_response(result, "corrected-audio.wav")
    except SpeechAssistError as exc:
        logger.exception("audio request failed | detail=%s", exc.message)
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post(
    "/video-file",
    response_class=FileResponse,
    summary="Upload video, extract audio with ffmpeg, and receive corrected speech audio",
)
async def process_video_file(file: UploadFile = File(...)) -> FileResponse:
    logger.info("video request received | filename=%s content_type=%s", file.filename, file.content_type)
    try:
        video_id, video_path, size_bytes = await save_video_upload(file)
        logger.info("video upload saved | video_id=%s size_bytes=%s path=%s", video_id, size_bytes, video_path)
        extracted_audio_id, extracted_audio = video_extractor.extract_wav(video_path)
        logger.info(
            "video audio extracted | video_id=%s extracted_audio_id=%s path=%s",
            video_id,
            extracted_audio_id,
            extracted_audio,
        )
        result = pipeline.process(extracted_audio)
        logger.info(
            "video request completed | video_id=%s accepted=%s similarity=%s output=%s",
            video_id,
            result["accepted"],
            result["similarity_score"],
            result["corrected_audio_path"],
        )
        return _corrected_audio_response(result, "corrected-video-audio.wav")
    except SpeechAssistError as exc:
        logger.exception("video request failed | detail=%s", exc.message)
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


def _corrected_audio_response(result: dict[str, object], filename: str) -> FileResponse:
    audio_path = Path(str(result["corrected_audio_path"]))
    if not audio_path.is_absolute():
        audio_path = Path(__file__).resolve().parents[2] / audio_path

    headers = {
        "X-Original-Transcript": quote(str(result["original_transcript"])),
        "X-Corrected-Transcript": quote(str(result["corrected_transcript"])),
        "X-Language": str(result["language"]),
        "X-Similarity-Score": str(result["similarity_score"]),
        "X-Correction-Accepted": str(result["accepted"]).lower(),
        "X-Correction-Reason": quote(str(result["reason"])),
        "X-Debug-Transcript-Id": str(result["debug_id"]),
        "X-Pipeline-Stages": quote(str(result["pipeline_stages"])),
        "Access-Control-Expose-Headers": (
            "X-Original-Transcript, X-Corrected-Transcript, X-Language, "
            "X-Similarity-Score, X-Correction-Accepted, X-Correction-Reason, "
            "X-Debug-Transcript-Id, X-Pipeline-Stages"
        ),
    }
    logger.info("returning corrected audio file | filename=%s path=%s", filename, audio_path)
    return FileResponse(
        audio_path,
        media_type="audio/wav",
        filename=filename,
        headers=headers,
    )


@router.get("/debug/transcript/{debug_id}", summary="Get staged transcript and confidence debug data")
def get_debug_transcript(debug_id: str) -> JSONResponse:
    try:
        return JSONResponse(load_debug_transcript(debug_id))
    except SpeechAssistError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
