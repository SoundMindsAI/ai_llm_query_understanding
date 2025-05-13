"""
Main application entry point for the LLM Query Understanding Service.

This module exports the FastAPI application for production ASGI servers.
"""
from llm_query_understand.api.app import app

# This allows running with "uvicorn llm_query_understand.main:app"
# The app itself is defined in llm_query_understand.api.app
# but we re-export it here for proper package structure
