from fastapi import UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from PIL import Image
from gtts import gTTS
import google.generativeai as genai
import io
import os

from app.config import settings, logger


def _validate_upload(file: UploadFile, contents: bytes) -> None:
    """Validate file type and size; raises HTTPException on failure."""
    if not settings.is_file_type_allowed(file.content_type):
        allowed = ", ".join(settings.allowed_file_types)
        logger.warning(f"Invalid file type: {file.content_type}")
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {allowed}")

    if len(contents) > settings.max_file_size:
        logger.warning(f"File too large: {len(contents)} bytes (max: {settings.max_file_size})")
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_file_size_mb:.2f}MB",
        )


def _extract_text(contents: bytes, mime_type: str, prompt: str) -> str:
    """Call Gemini Vision API and return extracted text."""
    image_data = {"mime_type": mime_type, "data": contents}
    model = genai.GenerativeModel(settings.gemini_model)
    response = model.generate_content([prompt, image_data])
    return response.text


def _text_response(text: str, filename: str) -> Response:
    """Return extracted text as a downloadable .txt file."""
    base = os.path.splitext(filename)[0]
    return Response(
        content=text,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{base}_extracted.txt"'},
    )


def _text_to_audio_response(text: str, filename: str, lang: str) -> Response:
    """Convert text to MP3 and return as downloadable response."""
    tts = gTTS(text=text, lang=lang)
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    base = os.path.splitext(filename)[0]
    return Response(
        content=buf.read(),
        media_type="audio/mpeg",
        headers={"Content-Disposition": f'attachment; filename="{base}_audio.mp3"'},
    )
