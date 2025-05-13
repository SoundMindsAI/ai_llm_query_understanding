# API Reference

This section documents the REST API endpoints provided by the LLM Query Understanding Service.

## Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| [`/`](#root-endpoint) | GET | Service information |
| [`/health`](#health-check-endpoint) | GET | Health check |
| [`/parse`](#query-understanding-endpoint) | POST | Parse furniture query using LLM |
| [`/debug`](#debug-endpoint) | POST | Raw LLM output for debugging |
| [`/test`](#test-endpoint) | POST | Test endpoint with static responses |
| [`/docs`](#api-documentation) | GET | Swagger UI documentation |
| [`/redoc`](#api-documentation) | GET | ReDoc documentation |

## Detailed API Documentation

### Root Endpoint

**Endpoint**: `GET /`

**Description**: Returns basic information about the service and available endpoints.

**Example Response**:
```json
{
  "service": "LLM Query Understanding Service",
  "version": "1.0.0",
  "endpoints": {
    "/parse": "Parse a search query into structured data",
    "/test": "Test endpoint with static responses",
    "/health": "Health check endpoint",
    "/docs": "Swagger UI interactive API documentation",
    "/redoc": "ReDoc API documentation"
  }
}
```

### Health Check Endpoint

**Endpoint**: `GET /health`

**Description**: Simple health check to verify the service is running.

**Example Response**:
```json
{
  "status": "ok"
}
```

### Query Understanding Endpoint

**Endpoint**: `POST /parse`

**Description**: Parses a natural language furniture query into structured data using the LLM.

**Request Format**:
```json
{
  "query": "string"
}
```

**Example Requests and Responses**:

1. **Blue Metal Dining Table**

   Request:
   ```json
   {
     "query": "blue metal dining table"
   }
   ```

   Response:
   ```json
   {
     "generation_time": 3.67,
     "parsed_query": {
       "item_type": "dining table",
       "material": "metal",
       "color": "blue"
     },
     "query": "blue metal dining table",
     "cached": false,
     "total_time": 5.571,
     "cache_lookup_time": null
   }
   ```

2. **Leather Sofa with Black Legs**

   Request:
   ```json
   {
     "query": "leather sofa with black legs"
   }
   ```

   Response:
   ```json
   {
     "generation_time": 57.99,
     "parsed_query": {
       "item_type": "sofa",
       "material": "leather",
       "color": "black"
     },
     "query": "leather sofa with black legs",
     "cached": false,
     "total_time": 57.989,
     "cache_lookup_time": 0.0006
   }
   ```

3. **Red Plastic Chair for Children**

   Request:
   ```json
   {
     "query": "red plastic chair for children"
   }
   ```

   Response:
   ```json
   {
     "generation_time": 23.65,
     "parsed_query": {
       "item_type": "chair",
       "material": "plastic",
       "color": "red"
     },
     "query": "red plastic chair for children",
     "cached": false,
     "total_time": 23.653,
     "cache_lookup_time": 0.0008
   }
   ```

4. **Cached Query Example** (Note the dramatic performance improvement)

   Request:
   ```json
   {
     "query": "blue metal dining table"
   }
   ```

   Response (from cache):
   ```json
   {
     "generation_time": 117.14,
     "parsed_query": {
       "item_type": "dining table",
       "material": "metal",
       "color": "blue"
     },
     "query": "blue metal dining table",
     "cached": true,
     "total_time": 0.0004,
     "cache_lookup_time": 0.0003
   }
   ```

5. **Green Plastic Chair**

   Request:
   ```json
   {
     "query": "green plastic chair"
   }
   ```

   Response:
   ```json
   {
     "generation_time": 2.71,
     "parsed_query": {
       "item_type": "chair",
       "material": "plastic",
       "color": "green"
     },
     "query": "green plastic chair",
     "cached": false,
     "total_time": 2.7107,
     "cache_lookup_time": null
   }
   ```

3. **Wooden Bookshelf with Glass Doors**

   Request:
   ```json
   {
     "query": "wooden bookshelf with glass doors"
   }
   ```

   Response:
   ```json
   {
     "generation_time": 3.79,
     "parsed_query": {
       "item_type": "bookshelf",
       "material": "wooden",
       "color": null
     },
     "query": "wooden bookshelf with glass doors",
     "cached": false,
     "total_time": 3.7895,
     "cache_lookup_time": 0.0001
   }
   ```

### Edge Case Handling

The `/parse` endpoint includes special handling for known edge cases that ensures accurate parsing for queries that might be challenging for the LLM:

- **Material vs. Color Ambiguity**: 
  - Example: `gold metal accent table` → item_type: "accent table", material: "metal", color: "gold"
  
- **Component vs. Item Type Confusion**:
  - Example: `glass display shelving unit with metal frame` → item_type: "shelving unit", material: "glass"
  
- **Composite Terms**:
  - Example: `amber glass cabinet for display` → item_type: "display cabinet", material: "glass", color: "amber"

### Debug Endpoint

**Endpoint**: `POST /debug`

**Description**: Returns the raw LLM output for a given query without parsing. Useful for debugging and prompt engineering.

**Request Format**:
```json
{
  "query": "string"
}
```

**Example Request**:
```json
{
  "query": "gold metal accent table"
}
```

**Example Response**:
```json
{
  "query": "gold metal accent table",
  "prompt": "[system prompt text...]",
  "raw_llm_output": "[raw output from LLM...]",
  "processing_time": 10.285
}
```

### Test Endpoint

**Endpoint**: `POST /test`

**Description**: Test endpoint that returns structured data without using the LLM. This is useful for testing the API structure without the overhead of LLM inference.

**Request Format**: Same as `/parse` endpoint.

**Example Response**:
```json
{
  "generation_time": 0.01,
  "parsed_query": {
    "item_type": "dining table",
    "material": "metal",
    "color": "blue"
  },
  "query": "blue metal dining table",
  "cached": false,
  "total_time": 0.0001,
  "cache_lookup_time": null
}
```

### API Documentation

The service provides interactive API documentation via Swagger UI and ReDoc:

- Swagger UI: `GET /docs`
- ReDoc: `GET /redoc`

These endpoints allow you to explore and test the API directly from your browser.

## Response Models

### QueryResponse

| Field | Type | Description |
|-------|------|-------------|
| `generation_time` | float | Time taken for LLM to generate the response in seconds |
| `parsed_query` | ParsedQuery | Structured data extracted from the query |
| `query` | string | The original query string |
| `cached` | boolean | Whether the response was retrieved from cache |
| `total_time` | float | Total processing time in seconds |
| `cache_lookup_time` | float, null | Time taken for cache lookup in seconds |

### ParsedQuery

| Field | Type | Description |
|-------|------|-------------|
| `item_type` | string, null | The main furniture item type |
| `material` | string, null | The material of the furniture item |
| `color` | string, null | The color of the furniture item |
