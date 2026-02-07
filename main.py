import google.generativeai as genai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings, logger
from app.routes import router

# Validate configuration
if not settings.validate():
    raise RuntimeError("Configuration validation failed!")

# Configure Gemini API
genai.configure(api_key=settings.gemini_api_key)
logger.info(f"Gemini API configured with model: {settings.gemini_model}")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="OCR API using Google Gemini AI",
)

# CORS
if settings.cors_enabled:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )

# Register routes
app.include_router(router)

# Log configuration on startup
settings.log_summary()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=settings.workers,
        log_level=settings.log_level.lower(),
    )
