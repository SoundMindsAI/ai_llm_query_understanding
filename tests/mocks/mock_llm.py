"""Mock LLM implementation for testing.

This module provides a mock implementation of the LargeLanguageModel class
that can be used in tests to avoid loading the actual model.
"""
from typing import Dict, Any, Optional
import json


class MockLargeLanguageModel:
    """Mock implementation of LargeLanguageModel for testing.
    
    This class mimics the interface of the actual LargeLanguageModel class
    but doesn't load any real model weights or perform actual inference.
    """
    
    def __init__(self, responses: Optional[Dict[str, str]] = None):
        """Initialize the mock LLM with predefined responses.
        
        Args:
            responses: A dictionary mapping queries to predefined responses.
                      If not provided, default responses will be used.
        """
        # Default responses for common queries
        self._default_responses = {
            "blue wooden table": """
            {
                "item_type": "table",
                "material": "wooden",
                "color": "blue"
            }
            """,
            "green plastic chair": """
            {
                "item_type": "chair",
                "material": "plastic",
                "color": "green"
            }
            """,
            "red leather sofa": """
            {
                "item_type": "sofa",
                "material": "leather",
                "color": "red"
            }
            """,
            "wooden bookshelf with glass doors": """
            {
                "item_type": "bookshelf",
                "material": "wooden",
                "color": null
            }
            """
        }
        
        # Use custom responses if provided, otherwise use defaults
        self.responses = responses if responses is not None else self._default_responses
        
        # Track calls for testing purposes
        self.calls = []
    
    def generate(self, prompt: str, max_new_tokens: int = 100) -> str:
        """Mock implementation of generate method.
        
        Args:
            prompt: The input prompt text
            max_new_tokens: Maximum number of tokens to generate
            
        Returns:
            A predefined response based on the prompt content
        """
        # Record this call for testing purposes
        self.calls.append({
            "prompt": prompt,
            "max_new_tokens": max_new_tokens
        })
        
        # Extract the query from the prompt
        # Assuming format like: "System prompt...\n\nQuery: \"actual query\""
        try:
            query_part = prompt.split('Query: "')[-1].split('"')[0].lower()
        except (IndexError, AttributeError):
            query_part = prompt.lower()
        
        # Find the most appropriate predefined response
        for key, response in self.responses.items():
            if key.lower() in query_part:
                return response
        
        # Fall back to a default response if no match is found
        return """
        {
            "item_type": "furniture",
            "material": null,
            "color": null
        }
        """
    
    def get_calls(self) -> list:
        """Get the list of calls made to this mock.
        
        Returns:
            List of call records with prompt and max_new_tokens
        """
        return self.calls
    
    def reset_calls(self) -> None:
        """Reset the list of recorded calls."""
        self.calls = []
