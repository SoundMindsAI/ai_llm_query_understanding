"""Unit tests for the LargeLanguageModel class.

This module contains tests for the LLM functionality.
"""
import pytest
from unittest.mock import patch, MagicMock, call
import torch
import time
from transformers import AutoTokenizer, AutoModelForCausalLM

from llm_query_understand.core.llm import LargeLanguageModel


class TestLargeLanguageModel:
    """Test suite for the LargeLanguageModel class."""

    @patch('llm_query_understand.core.llm.AutoTokenizer')
    @patch('llm_query_understand.core.llm.AutoModelForCausalLM')
    def test_init(self, mock_model, mock_tokenizer):
        """Test LLM initialization."""
        # Setup mocks
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        mock_tokenizer_instance.pad_token = None
        mock_tokenizer_instance.eos_token = "[EOS]"
        
        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        
        # Mock torch.backends.mps.is_available
        with patch('torch.backends.mps.is_available', return_value=False):
            with patch('torch.cuda.is_available', return_value=False):
                # Initialize LLM
                llm = LargeLanguageModel()
                
                # Verify tokenizer and model were loaded correctly
                mock_tokenizer.from_pretrained.assert_called_once()
                mock_model.from_pretrained.assert_called_once()
                
                # Verify pad token was set to eos token
                assert mock_tokenizer_instance.pad_token == mock_tokenizer_instance.eos_token
                
                # Check device handling
                assert llm.device == "cpu"

    @patch('llm_query_understand.core.llm.AutoTokenizer')
    @patch('llm_query_understand.core.llm.AutoModelForCausalLM')
    def test_init_mps(self, mock_model, mock_tokenizer):
        """Test LLM initialization on Apple Silicon (MPS)."""
        # Setup mocks
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        
        # Mock MPS availability
        with patch('torch.backends.mps.is_available', return_value=True):
            # Initialize LLM
            llm = LargeLanguageModel()
            
            # Verify model was loaded with CPU device_map
            assert mock_model.from_pretrained.call_args[1]["device_map"] == "cpu"
            assert llm.device == "cpu"

    @patch('llm_query_understand.core.llm.AutoTokenizer')
    @patch('llm_query_understand.core.llm.AutoModelForCausalLM')
    def test_generate(self, mock_model, mock_tokenizer):
        """Test the generate method."""
        # Setup mocks
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        # Mock tokenizer call result with input_ids properly included
        mock_tokens = {
            "input_ids": torch.tensor([[1, 2, 3, 4, 5]]),
            "attention_mask": torch.ones((1, 5))
        }
        mock_tokenizer_instance.return_value = mock_tokens
        
        # Mock model output
        mock_output = torch.tensor([[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]])
        mock_model_instance = MagicMock()
        mock_model_instance.generate.return_value = mock_output
        mock_model.from_pretrained.return_value = mock_model_instance
        
        # Mock decode output
        mock_tokenizer_instance.decode.return_value = "Generated text response"
        
        # Mock device attributes
        with patch('torch.backends.mps.is_available', return_value=False):
            with patch('torch.cuda.is_available', return_value=False):
                # Initialize LLM
                llm = LargeLanguageModel()
                
                # Set device attribute manually
                llm.device = "cpu"
                
                # Test generate method
                result = llm.generate("Test prompt", max_new_tokens=10)
                
                # Verify tokenizer was called correctly
                mock_tokenizer_instance.assert_called_once_with(
                    "Test prompt", 
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    return_attention_mask=True
                )
                
                # Verify model generate was called correctly
                mock_model_instance.generate.assert_called_once()
                
                # Verify tokenizer decode was called (without comparing tensors directly)
                assert mock_tokenizer_instance.decode.call_count == 1
                call_args = mock_tokenizer_instance.decode.call_args
                assert len(call_args[0]) == 1  # First positional arg should be tensor
                assert call_args[1].get('skip_special_tokens') == True  # Check kwargs
                
                # Verify correct result
                assert result == "Generated text response"

    @patch('llm_query_understand.core.llm.AutoTokenizer')
    @patch('llm_query_understand.core.llm.AutoModelForCausalLM')
    def test_generate_error(self, mock_model, mock_tokenizer):
        """Test error handling in generate method."""
        # Setup mocks
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        # Mock tokenizer call result with input_ids properly included
        mock_tokens = {
            "input_ids": torch.tensor([[1, 2, 3, 4, 5]]),
            "attention_mask": torch.ones((1, 5))
        }
        mock_tokenizer_instance.return_value = mock_tokens
        
        # Mock model generate to raise exception
        mock_model_instance = MagicMock()
        mock_model_instance.generate.side_effect = RuntimeError("Test error")
        mock_model.from_pretrained.return_value = mock_model_instance
        
        # Initialize LLM
        with patch('torch.backends.mps.is_available', return_value=False):
            llm = LargeLanguageModel()
            
            # Test generate method with error
            with pytest.raises(RuntimeError):
                llm.generate("Test prompt")
                
                # Verify error was properly logged
                # We'd need to capture logs to verify this properly
