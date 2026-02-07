from contextlib import asynccontextmanager

import google.generativeai as genai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings, logger
from app.routes import router


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Run startup tasks after the server is ready to accept connections."""
    # Validate configuration
    if not settings.validate():
        logger.error("Configuration validation failed — API calls will fail.")
    else:
        genai.configure(api_key=settings.gemini_api_key)
        logger.info(f"Gemini API configured with model: {settings.gemini_model}")
    settings.log_summary()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="OCR API using Google Gemini AI",
    lifespan=lifespan,
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
