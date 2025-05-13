from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os
import time
import gc  # For garbage collection to free memory
from llm_query_understand.logging_config import get_logger

# Get the configured logger
logger = get_logger()

# Determine the device to use (CUDA, MPS, or CPU)
DEVICE = torch.device("cuda" if torch.cuda.is_available() else 
                     "mps" if torch.backends.mps.is_available() else 
                     "cpu")

# Default model - use a smaller model for CPU
DEFAULT_MODEL = "Qwen/Qwen2-0.5B-Instruct"

class LargeLanguageModel:
    """
    A wrapper class for interacting with transformer-based language models.
    """

    def __init__(self, device=DEVICE, model=DEFAULT_MODEL):
        """
        Initialize the language model with the specified device and model.
        
        Args:
            device: The device to run the model on (cuda, mps, or cpu)
            model: The model identifier to load from Hugging Face
        """
        self.device = device
        logger.info(f"Initializing LLM with model={model} on device={device}")
        
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
            
            # For CPU inference, use int8 quantization for better performance
            dtype = torch.int8 if device == "cpu" else torch.float16
            
            self.model = AutoModelForCausalLM.from_pretrained(
                model,
                torch_dtype=dtype,
                device_map="auto",
                low_cpu_mem_usage=True    # Enable low CPU memory usage
            )
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
            
            # For inputs that need to be on the same device as the model's first layer,
            # we detect and move only if necessary
            if hasattr(self.model, 'hf_device_map') and 'model.embed_tokens' in self.model.hf_device_map:
                embed_device = self.model.hf_device_map['model.embed_tokens']
                logger.debug(f"Moving input tensors to {embed_device} device")
                inputs = {k: v.to(embed_device) for k, v in inputs.items()}
            
            # Use generate with proper parameters to avoid conflicts
            logger.debug(f"Starting text generation with max_new_tokens={max_new_tokens}")
            generation_start = time.time()
            outputs = self.model.generate(
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                max_new_tokens=max_new_tokens,  # Use max_new_tokens instead of max_length
                pad_token_id=self.tokenizer.pad_token_id,
                do_sample=False  # Deterministic generation
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
