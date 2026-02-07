from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from PIL import Image
from gtts import gTTS
import io

from app.config import settings, logger
from app.utils import _validate_upload, _extract_text, _text_response, _text_to_audio_response

router = APIRouter()

DEFAULT_PROMPT = "Extract all text from this image. Preserve the layout and structure as much as possible."


@router.get("/")
async def root():
    """Root / health check endpoint."""
    logger.info("Health check request received")
    return {
        "message": "OCR API is running",
        "name": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/health")
async def health_check():
    """Lightweight health probe."""
    return {"status": "healthy"}


@router.post("/ocr")
async def extract_text(file: UploadFile = File(...)):
    """Extract text from an image using Gemini Vision API.

    Supported formats: JPEG, PNG, GIF, WebP
    """
    logger.info(f"OCR request: {file.filename}")
    try:
        contents = await file.read()
        _validate_upload(file, contents)
        Image.open(io.BytesIO(contents))  # validate image

        text = _extract_text(contents, file.content_type, DEFAULT_PROMPT)
        logger.info(f"Text extraction successful: {file.filename}")
        return _text_response(text, file.filename)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing image: {e}")


@router.post("/ocr-with-prompt")
async def extract_text_with_prompt(
    file: UploadFile = File(...),
    prompt: str = "Extract all text from this image",
):
    """Extract text from an image with a custom prompt."""
    logger.info(f"OCR-with-prompt request: {file.filename}")
    try:
        contents = await file.read()
        _validate_upload(file, contents)
        Image.open(io.BytesIO(contents))

        text = _extract_text(contents, file.content_type, prompt)
        logger.info(f"Text extraction successful (custom prompt): {file.filename}")
        return _text_response(text, file.filename)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image with prompt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing image: {e}")


@router.post("/ocr-audio")
async def extract_text_as_audio(file: UploadFile = File(...), lang: str = "en"):
    """Extract text from an image and return it as an MP3 audio file.

    - **file**: Image file (JPEG, PNG, GIF, WebP)
    - **lang**: Language code for speech (default: en)
    """
    logger.info(f"OCR-Audio request: {file.filename}")
    try:
        contents = await file.read()
        _validate_upload(file, contents)
        Image.open(io.BytesIO(contents))

        text = _extract_text(contents, file.content_type, DEFAULT_PROMPT)
        logger.info(f"Text extraction successful: {file.filename}")

        if not text.strip():
            raise HTTPException(status_code=422, detail="No text found in the image.")

        logger.info(f"Converting text to audio (lang={lang})")
        return _text_to_audio_response(text, file.filename, lang)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in OCR-Audio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing image: {e}")


@router.post("/text-to-audio")
async def text_to_audio(text: str = Form(...), lang: str = Form("en")):
    """Convert raw text to an MP3 audio file.

    - **text**: The text to convert to speech
    - **lang**: Language code (default: en)
    """
    logger.info(f"Text-to-Audio request ({len(text)} chars, lang={lang})")
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty.")

        tts = gTTS(text=text, lang=lang)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)

        logger.info("Text-to-Audio conversion successful")
        from fastapi.responses import Response

        return Response(
            content=buf.read(),
            media_type="audio/mpeg",
            headers={"Content-Disposition": 'attachment; filename="text_audio.mp3"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Text-to-Audio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error converting text to audio: {e}")
