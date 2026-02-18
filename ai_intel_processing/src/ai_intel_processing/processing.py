import logging
import json
from typing import Optional, Dict, Any
from .schema import NewsArticle, OutputSchema
from .utils import setup_logger, log_struct

logger = setup_logger("ai_intel_processing")

class IntelProcessor:
    def __init__(self, api_key: Optional[str] = None):
        from .llm import LLMClient
        self.llm = LLMClient(api_key=api_key)

    def process_article(self, article: NewsArticle) -> OutputSchema:
        """
        Processes a raw news article and returns a structured output.
        """
        import hashlib
        from datetime import datetime
        
        log_struct(logger, logging.INFO, "Processing article", url=article.url)

        # 1. Compute Article Hash (SHA-256)
        article_hash = hashlib.sha256(article.content.encode('utf-8')).hexdigest()

        # 2. Generate analysis (LLM)
        analysis_data = {}
        model_used = "unknown"
        
        # Default fallback values
        event_type = "other"
        
        try:
            from .prompts import ANALYSIS_PROMPT_TEMPLATE, PROMPT_VERSION
            from .schema import InvestmentAnalysis
            
            if self.llm.client:
                model_used = self.llm.model
            
            prompt = ANALYSIS_PROMPT_TEMPLATE.format(
                title=article.title,
                source=article.source,
                date=article.published_at,
                content=article.content[:15000] # Increased truncate limit slightly
            )
            
            # Updated call: removed 'content' arg
            analysis = self.llm.analyze(prompt, InvestmentAnalysis)
            
            if analysis:
                analysis_data = analysis.model_dump()
                event_type = analysis_data.get("event_type", "other")
            else:
                log_struct(logger, logging.WARNING, "LLM returned no analysis", url=article.url)
                
        except Exception as e:
            log_struct(logger, logging.ERROR, "LLM processing failed", error=str(e), url=article.url)
            # We continue with empty analysis data rather than crashing
            from .prompts import PROMPT_VERSION # Ensure we have it for fallback

        # 3. Construct OutputSchema
        output = OutputSchema(
            schema_version="2.0",
            source=article.source,
            title=article.title,
            url=article.url,
            published_at=article.published_at.isoformat() if article.published_at else None,
            company=analysis_data.get("company"),
            funding_amount=analysis_data.get("funding_amount"),
            funding_stage=analysis_data.get("funding_stage"),
            investors=analysis_data.get("investors", []),
            summary=analysis_data.get("summary", "Analysis failed or content unavailable."),
            investment_relevant=analysis_data.get("investment_relevant", False),
            event_type=event_type,
            
            # Traceability
            model_used=model_used,
            prompt_version=PROMPT_VERSION,
            processing_timestamp=datetime.utcnow().isoformat(),
            article_hash=article_hash,
            
            metadata=article.raw_metadata
        )

        return output
