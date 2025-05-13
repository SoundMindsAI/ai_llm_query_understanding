#!/usr/bin/env python3
"""FastAPI application for the LLM Query Understanding Service.

This module implements a REST API that processes natural language queries about furniture
into structured JSON data using a small LLM (Qwen2-0.5B-Instruct).
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
import json
import time
import os
import re
from typing import Dict, Any, Optional, Union, List

# Updated imports to reflect the new package structure
from llm_query_understand.core.llm import LargeLanguageModel
from llm_query_understand.core.cache import QueryCache
from llm_query_understand.utils.logging_config import get_logger

# Get the configured logger
logger = get_logger()

# API version and metadata
API_VERSION = "1.0.0"
API_TITLE = "LLM Query Understanding Service"
API_DESCRIPTION = "Service that transforms natural language queries into structured data using LLM technology"

# Initialize the FastAPI app with OpenAPI documentation
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Import the logging middleware
from llm_query_understand.api.middleware import RequestLoggingMiddleware, ResponseTimeHeaderMiddleware

# Add middleware for request logging and performance tracking
app.add_middleware(RequestLoggingMiddleware, exclude_paths=["/health", "/docs", "/redoc", "/openapi.json"])
app.add_middleware(ResponseTimeHeaderMiddleware)

# Enable CORS for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Allow requests from all origins
    allow_credentials=True,    # Allow cookies in cross-origin requests
    allow_methods=["*"],       # Allow all HTTP methods
    allow_headers=["*"],       # Allow all headers
)

# Initialize the LLM (lazy loading - will be initialized on first request)
llm: Optional[LargeLanguageModel] = None

# Initialize the cache service
cache = QueryCache()


# Pydantic models for request/response validation
class QueryRequest(BaseModel):
    """Request model for query parsing endpoints."""
    query: str = Field(..., description="The natural language query to be parsed")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "blue wooden dining table"
            }
        }
    )

# Response models for structured output and documentation
class ParsedQuery(BaseModel):
    """Structured representation of a furniture query."""
    item_type: Optional[str] = Field(None, description="The main furniture item type")
    material: Optional[str] = Field(None, description="The material of the furniture item")
    color: Optional[str] = Field(None, description="The color of the furniture item")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "item_type": "couch",
                "material": "leather",
                "color": "black"
            }
        }
    )

class QueryResponse(BaseModel):
    """Standard response model for query parsing operations."""
    generation_time: float = Field(..., description="Time taken for LLM to generate the response")
    parsed_query: ParsedQuery = Field(..., description="Structured data extracted from the query")
    query: str = Field(..., description="The original query string")
    cached: bool = Field(..., description="Whether the response was retrieved from cache")
    total_time: float = Field(..., description="Total processing time in seconds")
    cache_lookup_time: Optional[float] = Field(None, description="Time taken to look up query in cache")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "generation_time": 0.235,
                "parsed_query": {
                    "item_type": "dining table",
                    "material": "wooden",
                    "color": "brown"
                },
                "query": "brown wooden dining table",
                "cached": False,
                "total_time": 0.251,
                "cache_lookup_time": 0.002
            }
        }
    )

# System prompt for furniture query understanding
FURNITURE_PROMPT = """
You are a LITERAL furniture query parser. You extract EXACTLY what is mentioned in the query, with no interpretation or added context.

CRITICAL INSTRUCTIONS:
1. ONLY output a valid JSON object with these three fields: "item_type", "material", and "color"
2. PARSE THE EXACT QUERY TEXT PROVIDED - Do not reference or use any patterns from examples
3. EXTRACT LITERAL MENTIONS of furniture type, material, and color - nothing more
4. SET A FIELD TO NULL when that property is not explicitly mentioned
5. NEVER GUESS OR INVENT information not present in the query

Rules for property extraction:
- item_type: Extract the EXACT furniture type mentioned (e.g., "table", "chair", "bookshelf", "sofa")
- material: Extract the EXACT material mentioned (e.g., "metal", "wood", "wooden", "plastic", "leather")
- color: Extract the EXACT color mentioned (e.g., "blue", "green", "red", "black", "brown")

For example, if the query is "blue metal dining table":
- item_type should be "dining table" (EXACTLY as mentioned)
- material should be "metal" (EXACTLY as mentioned)
- color should be "blue" (EXACTLY as mentioned)

YOUR RESPONSE MUST BE JUST THE JSON OBJECT, NOTHING ELSE. NO EXPLANATIONS OR ADDITIONAL TEXT.

IF YOU FIND ANY EXACT MATCH FOR A PROPERTY, SET IT IN THE JSON. IF NOT FOUND, USE null.
"""

class ServiceInfo(BaseModel):
    """Service information response model."""
    service: str = Field(..., description="Name of the service")
    version: str = Field(..., description="API version number")
    endpoints: Dict[str, str] = Field(..., description="Available endpoints and their descriptions")


@app.get("/", response_model=ServiceInfo, summary="Service Information")
async def read_root() -> ServiceInfo:
    """Root endpoint returning service information and available endpoints.
    
    Returns:
        ServiceInfo: Object containing service name, version, and available endpoints
    """
    return ServiceInfo(
        service=API_TITLE,
        version=API_VERSION,
        endpoints={
            "/parse": "Parse a search query into structured data",
            "/test": "Test endpoint with static responses",
            "/health": "Health check endpoint",
            "/docs": "Swagger UI interactive API documentation",
            "/redoc": "ReDoc API documentation"
        }
    )

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Current health status of the service")


@app.get("/health", response_model=HealthResponse, summary="Health Check")
async def health_check() -> HealthResponse:
    """Simple health check endpoint to verify the service is running.
    
    Returns:
        HealthResponse: Object containing the current health status
    """
    return HealthResponse(status="ok")


@app.post("/test", response_model=QueryResponse, summary="Test Query Understanding")
async def test_endpoint(request: QueryRequest) -> QueryResponse:
    """Simple test endpoint that returns structured data without using the LLM.
    
    This endpoint provides a lightweight way to test the API structure without needing
    to load or run the language model. It parses the query based on simple keyword matching.
    
    Args:
        request: The query request containing the text to analyze
        
    Returns:
        QueryResponse: Structured data extracted from the query using simple rules
    """
    start_time = time.time()
    query = request.query.strip()
    logger.info(f"Test endpoint processing: '{query}'")
    
    query_lower = query.lower()
    
    # Determine item type based on query keywords
    if "table" in query_lower:
        item_type = "dining table" if "dining" in query_lower else "table"
    elif "chair" in query_lower:
        item_type = "chair"
    elif "sofa" in query_lower or "couch" in query_lower:
        item_type = "sofa"
    elif "bookshelf" in query_lower or "shelf" in query_lower:
        item_type = "bookshelf"
    elif "bed" in query_lower:
        item_type = "bed"
    elif "desk" in query_lower:
        item_type = "desk"
    elif "dresser" in query_lower or "drawer" in query_lower:
        item_type = "dresser"
    else:
        item_type = "furniture"
        
    # Determine material based on query keywords
    if "wood" in query_lower or "wooden" in query_lower:
        material = "wooden"
    elif "metal" in query_lower or "steel" in query_lower or "iron" in query_lower:
        material = "metal"
    elif "plastic" in query_lower:
        material = "plastic"
    elif "leather" in query_lower:
        material = "leather"
    elif "fabric" in query_lower or "cloth" in query_lower:
        material = "fabric"
    elif "glass" in query_lower:
        material = "glass"
    else:
        material = None
        
    # Determine color based on query keywords
    if "blue" in query_lower:
        color = "blue"
    elif "red" in query_lower:
        color = "red"
    elif "green" in query_lower:
        color = "green"
    elif "yellow" in query_lower:
        color = "yellow"
    elif "black" in query_lower:
        color = "black"
    elif "white" in query_lower:
        color = "white"
    elif "brown" in query_lower:
        color = "brown"
    elif "gray" in query_lower or "grey" in query_lower:
        color = "gray"
    else:
        color = None
        
    # Create the parsed query object
    parsed_query = ParsedQuery(
        item_type=item_type,
        material=material,
        color=color
    )
    
    # Calculate timing metrics
    total_time = time.time() - start_time
    
    # Return the response using the proper model
    return QueryResponse(
        generation_time=0.01,
        parsed_query=parsed_query,
        query=query,
        cached=False,
        total_time=round(total_time, 4),
        cache_lookup_time=None
    )

@app.post("/parse", response_model=QueryResponse, summary="Parse Furniture Query", 
       responses={
        200: {"description": "Successfully parsed query"},
        500: {"description": "Server error during processing"}
    })
async def parse_query(request: QueryRequest) -> QueryResponse:
    """Parse a natural language furniture query into structured data using the LLM.
    
    This endpoint processes natural language queries about furniture and extracts
    key information such as the item type, material, and color. It uses a small
    but efficient LLM (Qwen2-0.5B-Instruct) with intelligent caching for
    performance optimization.
    
    Args:
        request: The query request containing the text to analyze
        
    Returns:
        QueryResponse: Structured data extracted from the query by the LLM
        
    Raises:
        HTTPException: If an error occurs during processing
    """
    # Record the starting time for performance tracking
    start_time = time.time()
    
    # Get the query from the request and normalize it
    query = request.query.strip()
    if not query:
        logger.warning("Received empty query")
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    logger.info(f"Processing query: '{query}'")
    
    # Check if the query has been cached
    cache_lookup_start = time.time()
    cached_result = cache.get(query)
    cache_lookup_time = time.time() - cache_lookup_start
    
    # If the result is cached, return it immediately
    if cached_result:
        logger.info(f"Cache hit for query: '{query}'")
        total_time = time.time() - start_time
        
        # Ensure the response follows our Pydantic model structure
        return QueryResponse(
            generation_time=cached_result.get("generation_time", 0.0),
            parsed_query=ParsedQuery(**cached_result.get("parsed_query", {})),
            query=query,
            cached=True,
            total_time=round(total_time, 4),
            cache_lookup_time=round(cache_lookup_time, 4)
        )
    
    # Initialize the LLM if it hasn't been already (lazy initialization)
    global llm
    if llm is None:
        logger.info("Initializing LLM for first request")
        try:
            llm = LargeLanguageModel()
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to initialize language model: {str(e)}"
            )
    
    # Generate the response from the LLM
    try:
        # Measure generation time
        generation_start = time.time()
        
        # Combine the system prompt and user query into a single prompt
        combined_prompt = f"{FURNITURE_PROMPT}\n\nQuery: \"{query}\""
        
        # Generate response with the LLM
        response_text = llm.generate(combined_prompt, 100)  # Use 100 as max_new_tokens
        generation_time = time.time() - generation_start
        logger.info(f"LLM generation completed in {generation_time:.2f} seconds")
        
        # Parse the JSON response from the LLM output
        parsed_data = parse_llm_json_response(response_text)
        parsed_query = ParsedQuery(**parsed_data)
        
        # Calculate the total processing time
        total_time = time.time() - start_time
        
        # Create the result following our response model
        result = QueryResponse(
            generation_time=round(generation_time, 2),
            parsed_query=parsed_query,
            query=query,
            cached=False,
            total_time=round(total_time, 4),
            cache_lookup_time=round(cache_lookup_time, 4) if cache_lookup_time else None
        )
        
        # Cache the result for future queries
        cache.set(query, result.model_dump())
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing query: {str(e)}"
        )

def parse_llm_json_response(text: str) -> Dict[str, Optional[str]]:
    """Parse the JSON response from the LLM output with multiple fallback methods.
    
    This function attempts several approaches to extract valid JSON from LLM output,
    which may contain formatting issues or additional text. It uses a series of 
    increasingly flexible parsing methods to maximize the chances of extracting
    useful information.
    
    Args:
        text: The raw text output from the LLM
        
    Returns:
        Dict[str, Optional[str]]: Parsed furniture data with item_type, material, and color fields
        
    Note:
        If all parsing attempts fail, a minimal valid response with None values is returned
        rather than raising an exception, to ensure the API remains functional.
    """
    if not text or not text.strip():
        logger.error("Received empty text for JSON parsing")
        return {"item_type": None, "material": None, "color": None}
        
    logger.debug(f"Parsing LLM response text of length {len(text)}")
    
    # Try multiple approaches to extract valid JSON, from strict to lenient
    try:
        # First attempt: Try to parse the entire response as JSON
        logger.debug("Attempting to parse entire response as JSON")
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parsing failed: {e}. Trying fallback methods")
        
        try:
            # Second attempt: Look for JSON between { and }
            logger.debug("Attempting to extract JSON using regex")
            json_match = re.search(r'(\{.*?\})', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                logger.debug(f"Found potential JSON: {json_str}")
                return json.loads(json_str)
        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"Regex extraction failed: {e}")
            
        try:
            # Third attempt: Try to fix common JSON formatting issues
            logger.debug("Attempting to fix malformed JSON")
            # Replace single quotes with double quotes
            fixed_text = text.replace("'", '"')
            # Fix unquoted keys
            fixed_text = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)\s*:', r'\1"\2":', fixed_text)
            # Try to extract JSON again
            json_match = re.search(r'(\{.*?\})', fixed_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
        except Exception as e:
            logger.warning(f"JSON fixing attempt failed: {e}")
    
    # If all parsing attempts fail, return a minimal valid response
    logger.error("All JSON parsing methods failed, returning empty object")
    return {"item_type": None, "material": None, "color": None}

# Custom exception models for structured error responses
class ErrorResponse(BaseModel):
    """Standardized error response model."""
    detail: str = Field(..., description="Error description")
    timestamp: str = Field(..., description="Time when the error occurred")
    path: str = Field(..., description="Request path that caused the error")
    type: str = Field(..., description="Type of error")    


# Handle global exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for all unhandled exceptions.
    
    This handler ensures all errors are properly logged and return a consistent
    error format to the client with helpful debug information.
    
    Args:
        request: The FastAPI request that caused the exception
        exc: The exception that was raised
        
    Returns:
        JSONResponse: A standardized error response
    """
    # Get current timestamp in ISO format
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Log the error with full stack trace for debugging
    logger.error(
        f"Unhandled exception on {request.url.path}: {str(exc)}",
        exc_info=True
    )
    
    # Create a standardized error response
    error_response = ErrorResponse(
        detail=str(exc),
        timestamp=now,
        path=str(request.url),
        type=exc.__class__.__name__
    )
    
    # Return the error as a properly formatted JSON response
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(),
    )
