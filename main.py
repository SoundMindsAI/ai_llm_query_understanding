#!/usr/bin/env python3
import uvicorn

def main():
    """
    Entry point for running the LLM Query Understanding Service
    """
    print("Starting LLM Query Understanding Service...")
    
    # Run the FastAPI app using uvicorn
    uvicorn.run(
        "llm_query_understand.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


if __name__ == "__main__":
    main()
