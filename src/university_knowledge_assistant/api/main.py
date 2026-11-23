"""FastAPI application entry point."""

from fastapi import FastAPI

from .routes import router
from university_knowledge_assistant import __version__

app = FastAPI(
    title="University Knowledge Assistant",
    version=__version__,
    description="Ask questions grounded in indexed university course PDFs.",
)
app.include_router(router)
