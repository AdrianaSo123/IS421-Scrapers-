import os
import logging
import json
from typing import Optional, Dict, Any, Type
from pydantic import BaseModel
from openai import OpenAI, OpenAIError, RateLimitError, APIError
import time

from .utils import setup_logger, log_struct
from .prompts import SYSTEM_PROMPT
from dotenv import load_dotenv

load_dotenv()

logger = setup_logger("ai_intel_processing.llm")

class LLMClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("LLM_MODEL", "gpt-4o-2024-08-06")
        if not self.api_key:
            log_struct(logger, logging.WARNING, "No OpenAI API key found. LLM features will be disabled or mock-only.")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)

    def analyze(self, prompt: str, schema_model: Type[BaseModel]) -> Optional[BaseModel]:
        """
        Analyzes content using OpenAI and enforces a Pydantic schema for the output.
        Uses structured outputs (response_format).
        """
        if not self.client:
            log_struct(logger, logging.ERROR, "Cannot perform analysis: No API Client")
            return None

        retries = 3
        for attempt in range(retries):
            try:
                log_struct(logger, logging.INFO, "Sending request to OpenAI", model=self.model, attempt=attempt+1)
                
                completion = self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    response_format=schema_model,
                    temperature=0,
                    seed=42,
                    timeout=30
                )
                
                result = completion.choices[0].message.parsed
                log_struct(logger, logging.INFO, "Received structured response from OpenAI")
                return result

            except RateLimitError as e:
                log_struct(logger, logging.WARNING, "Rate limit hit", error=type(e).__name__, attempt=attempt+1)
                if attempt == retries - 1:
                    raise e
                time.sleep(2 ** attempt)
            except Exception as e:
                log_struct(logger, logging.ERROR, "LLM analysis error", error=type(e).__name__, message=str(e), attempt=attempt+1)
                if attempt == retries - 1:
                    raise RuntimeError(f"LLM processing failed explicitly: {str(e)}") from e
                time.sleep(2 ** attempt)
        
        raise RuntimeError(f"LLM processing failed after {retries} attempts.")
