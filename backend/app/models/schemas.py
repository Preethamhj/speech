from pydantic import BaseModel, Field


class UploadAudioResponse(BaseModel):
    audio_id: str
    filename: str
    content_type: str
    size_bytes: int


class AudioIdRequest(BaseModel):
    audio_id: str


class TranscriptRequest(BaseModel):
    transcript: str = Field(min_length=1)
    language: str | None = None


class GenerateAudioRequest(BaseModel):
    text: str = Field(min_length=1)
    language: str = "kn"


class TranscriptionResponse(BaseModel):
    audio_id: str
    transcript: str
    language: str


class CorrectionResponse(BaseModel):
    original_transcript: str
    corrected_transcript: str
    accepted: bool
    similarity_score: float
    reason: str


class AudioGenerationResponse(BaseModel):
    audio_id: str
    audio_url: str


class ProcessResponse(BaseModel):
    audio_id: str
    original_transcript: str
    corrected_transcript: str
    language: str
    similarity_score: float
    accepted: bool
    corrected_audio_id: str
    corrected_audio_url: str
    reason: str


class VideoProcessResponse(ProcessResponse):
    video_id: str
    extracted_audio_id: str
