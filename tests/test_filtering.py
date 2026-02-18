import pytest
from ai_hackernews_ingest.filter import is_ai_story

@pytest.mark.parametrize("title,expected", [
    ("New AI model released", True),
    ("Advances in Machine Learning", True),
    ("LLMs are changing the world", True),
    ("Python 3.14 released", False),
    ("Mail server configuration", False), # "ai" in "mail" should not match if logic is good
    ("The future of artificial intelligence", True),
    ("Neural Networks explained", True),
    ("GPT-5 rumors", True),
    ("Generative AI art", True),
    ("OpenAI announces new features", True),
    ("My cat likes food", False)
])
def test_is_ai_story(title, expected):
    assert is_ai_story(title) == expected
