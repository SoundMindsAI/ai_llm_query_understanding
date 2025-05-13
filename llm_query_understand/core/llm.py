import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import time
import gc  # For garbage collection to free memory
from llm_query_understand.utils.logging_config import get_logger

# Get the configured logger
logger = get_logger()

# Default to using CPU with int8 quantization as recommended in README
# Let device_map='auto' handle optimal device placement

# Default model - use a smaller model for CPU
DEFAULT_MODEL = "Qwen/Qwen2-0.5B-Instruct"

class LargeLanguageModel:
    """
    A wrapper class for interacting with transformer-based language models.
    """

    def __init__(self, model=DEFAULT_MODEL):
        """
        Initialize the language model with the specified model.
        The device is managed automatically via device_map='auto'.
        
        Args:
            model: The model identifier to load from Hugging Face
        """
        logger.info(f"Initializing LLM with model={model} using device_map='auto'")
        
        try:
            # Initialize tokenizer with proper padding settings
            logger.debug(f"Loading tokenizer for {model}")
            start_time = time.time()
            self.tokenizer = AutoTokenizer.from_pretrained(model)
            logger.debug(f"Tokenizer loaded in {time.time() - start_time:.2f} seconds")
            
            # Set pad_token_id if it doesn't exist (important for proper attention masking)
            if self.tokenizer.pad_token is None:
                logger.debug("Setting pad_token to eos_token as it was not defined")
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Run garbage collection before model loading to free memory
            gc.collect()
            
            # Load the model with standard settings and device mapping
            logger.info(f"Loading model {model}, this may take several minutes...")
            start_time = time.time()
            
            # Check for MPS (Apple Silicon) availability and handle differently
            # to avoid the "Placeholder storage has not been allocated on MPS device!" error
            if torch.backends.mps.is_available():
                logger.info("Apple Silicon (MPS) detected, using CPU device for compatibility")
                # On Apple Silicon, force CPU usage to avoid MPS device errors
                self.model = AutoModelForCausalLM.from_pretrained(
                    model,
                    device_map="cpu",      # Force CPU to avoid MPS issues
                    low_cpu_mem_usage=True # Enable low CPU memory usage
                )
                self.device = "cpu"
            else:
                # For other devices, use standard approach with auto device mapping
                self.model = AutoModelForCausalLM.from_pretrained(
                    model,
                    device_map="auto",     # Let the library handle optimal device placement
                    low_cpu_mem_usage=True # Enable low CPU memory usage
                )
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            load_time = time.time() - start_time
            logger.info(f"Model loaded in {load_time:.2f} seconds")
            
            # Log the device map for debugging
            if hasattr(self.model, 'hf_device_map'):
                logger.debug(f"Model layer distribution: {self.model.hf_device_map}")
            
        except Exception as e:
            logger.error(f"Error initializing LLM: {str(e)}", exc_info=True)
            raise
    
    def generate(self, prompt: str, max_new_tokens: int = 100):
        """
        Generate text from the model based on the provided prompt.
        
        Args:
            prompt: The input text prompt
            max_new_tokens: Maximum number of new tokens to generate
            
        Returns:
            The generated text response
        """
        start_time = time.time()
        logger.debug(f"Generating response for prompt of length {len(prompt)} chars")
        
        try:
            # Properly tokenize with padding and attention mask
            tokenize_start = time.time()
            inputs = self.tokenizer(
                prompt, 
                return_tensors="pt",
                padding=True,
                truncation=True,
                return_attention_mask=True
            )
            logger.debug(f"Tokenization completed in {time.time() - tokenize_start:.4f} seconds")
            
            # Log token count for performance monitoring
            token_count = inputs["input_ids"].shape[1]
            logger.debug(f"Input token count: {token_count}")
            
            # Handle input tensor device placement based on our configuration
            # This fixes issues with MPS devices on Apple Silicon
            if hasattr(self, 'device'):
                # Use the device we explicitly set during initialization
                logger.debug(f"Moving input tensors to {self.device} device")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            elif hasattr(self.model, 'hf_device_map') and 'model.embed_tokens' in self.model.hf_device_map:
                # Fallback to device map if available
                embed_device = self.model.hf_device_map['model.embed_tokens']
                logger.debug(f"Moving input tensors to {embed_device} device")
                inputs = {k: v.to(embed_device) for k, v in inputs.items()}
            else:
                # Last resort - move to CPU
                logger.debug("No device mapping found, using CPU")
                inputs = {k: v.to('cpu') for k, v in inputs.items()}
            
            # Use generate with proper parameters to avoid conflicts
            logger.debug(f"Starting text generation with max_new_tokens={max_new_tokens}")
            generation_start = time.time()
            outputs = self.model.generate(
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                max_new_tokens=max_new_tokens,  # Use max_new_tokens instead of max_length
                pad_token_id=self.tokenizer.pad_token_id,
                do_sample=True,  # Enable sampling for more diverse outputs
                temperature=0.7,  # Moderate temperature for balanced creativity/coherence
                top_p=0.9  # Nucleus sampling to focus on more reasonable options
            )
            
            # Log generation performance metrics
            generation_time = time.time() - generation_start
            logger.debug(f"Generation completed in {generation_time:.2f} seconds")
            
            # Decode only the generated part, skipping the prompt
            prompt_length = inputs["input_ids"].shape[-1]
            generated_tokens = outputs[0][prompt_length:]
            generated_token_count = len(generated_tokens)
            logger.debug(f"Generated {generated_token_count} new tokens")
            
            # Calculate tokens per second for performance monitoring
            if generation_time > 0:
                tokens_per_second = generated_token_count / generation_time
                logger.debug(f"Generation speed: {tokens_per_second:.2f} tokens/second")
            
            # Return the full response (prompt + generated text)
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            total_time = time.time() - start_time
            logger.info(f"Total generation process took {total_time:.2f} seconds")
            
            return response
            
        except Exception as e:
            logger.error(f"Error during text generation: {str(e)}", exc_info=True)
            raise
