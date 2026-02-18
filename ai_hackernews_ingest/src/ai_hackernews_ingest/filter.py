
AI_KEYWORDS = {
    "ai", "artificial intelligence", "llm", "large language model", 
    "machine learning", "neural network", "transformer", "gpt", 
    "openai", "anthropic", "deepmind", "generative ai", "diffusion model"
}

def is_ai_story(title: str) -> bool:
    """
    Determines if a story is related to AI based on the title.
    Case-insensitive matching against a set of keywords.
    """
    if not title:
        return False
        
    # Word boundary check is better, but simple substring sufficient for now given the list
    # Improved: Check for word boundaries to avoid false positives (e.g., "mail" matches "ai")
    normalized_title = title.lower()
    
    # A simple regex or word splitting would be more robust for "ai"
    # For now, let's just split by space and check, or use simple substring for longer terms
    
    words = set(normalized_title.split())
    if "ai" in words:
        return True
        
    for keyword in AI_KEYWORDS:
        if keyword == "ai": continue # Handled by word split
        if keyword in normalized_title:
            return True
            
    return False
