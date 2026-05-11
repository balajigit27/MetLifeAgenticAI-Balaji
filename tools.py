"""
Shared tools used by research agents.

These are the functions and utilities that agents can invoke to:
- Search for information
- Fetch web pages and documents
- Extract entities and facts
- Validate information
- Process text
"""

from typing import List, Dict, Any, Optional
import re
from datetime import datetime
from utils.logger import logger


def search_web(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Search the web for information.
    
    In a production system, this would integrate with:
    - SerpAPI for real Google searches
    - Firecrawl for crawling web pages
    - Tavily for specialized research
    
    For now, this is a mock implementation that returns structured results.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
        
    Returns:
        List of search results with title, URL, snippet
        
    Example:
        results = search_web("AI agents frameworks 2025", max_results=5)
        for r in results:
            print(f"{r['title']}: {r['url']}")
    """
    logger.debug(f"Searching web for: {query}")
    
    # Mock implementation
    # In production, replace with real API calls
    mock_results = [
        {
            "title": "LangGraph: Build Stateful Agent Applications",
            "url": "https://python.langchain.com/docs/langgraph/",
            "snippet": "LangGraph is a framework for building stateful agent applications with LLMs."
        },
        {
            "title": "Understanding AI Agents: Architecture and Design Patterns",
            "url": "https://example.com/ai-agents-architecture",
            "snippet": "AI agents use ReAct patterns and tool use for complex reasoning."
        },
        {
            "title": "Multi-Agent Systems: Orchestration and Coordination",
            "url": "https://example.com/multi-agent-systems",
            "snippet": "Multi-agent systems coordinate multiple specialized agents."
        },
        {
            "title": "Production-Ready AI Agents: Best Practices",
            "url": "https://example.com/production-agents",
            "snippet": "Production agents need error handling, monitoring, and persistence."
        },
        {
            "title": "RAG vs Fine-tuning: When to Use Each Approach",
            "url": "https://example.com/rag-vs-finetuning",
            "snippet": "RAG retrieves external knowledge; fine-tuning adapts model behavior."
        },
    ]
    
    # Filter based on query (simple mock)
    results = [r for r in mock_results if query.lower() in r["title"].lower()]
    if not results:
        results = mock_results[:max_results]
    
    return results[:max_results]


def fetch_document(url: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Fetch and extract text from a document (web page, PDF, etc).
    
    In production, this would use:
    - BeautifulSoup for HTML parsing
    - PyPDF2 for PDF extraction
    - unstructured.io for multiple formats
    
    Args:
        url: URL of the document
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary with title, text, metadata
        
    Example:
        doc = fetch_document("https://example.com/article")
        print(f"Title: {doc['title']}")
        print(f"Content: {doc['text'][:500]}...")
    """
    logger.debug(f"Fetching document from: {url}")
    
    # Mock implementation
    # In production, replace with actual HTTP client and parsers
    mock_content = {
        "url": url,
        "title": "Sample Research Document",
        "text": """
        AI agents are autonomous systems that can perceive their environment,
        make decisions, and take actions to achieve specified goals. Modern AI agents
        combine language models with tools and memory systems.
        
        Key capabilities include:
        - Planning and reasoning
        - Tool use and API integration
        - Memory management
        - Error handling and recovery
        
        The ReAct pattern (Reasoning + Acting) is currently the dominant approach
        for building AI agents in production systems.
        """,
        "metadata": {
            "fetch_timestamp": datetime.utcnow().isoformat(),
            "status_code": 200,
            "content_type": "text/html"
        }
    }
    
    return mock_content


def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract named entities from text (people, organizations, locations, etc).
    
    In production, use spaCy or Hugging Face NER models.
    
    Args:
        text: Text to extract entities from
        
    Returns:
        Dictionary with entity types as keys and lists of entities as values
        
    Example:
        entities = extract_entities("Steve Jobs founded Apple in California")
        print(entities["PERSON"])  # ["Steve Jobs"]
        print(entities["ORG"])     # ["Apple"]
    """
    logger.debug(f"Extracting entities from text ({len(text)} chars)")
    
    # Mock implementation
    # In production, use spaCy: nlp = spacy.load("en_core_web_sm")
    entities = {
        "PERSON": [],
        "ORG": [],
        "GPE": [],  # Geographic/Political entities
        "PRODUCT": [],
        "DATE": [],
    }
    
    # Simple pattern matching for demonstration
    if "Steve Jobs" in text:
        entities["PERSON"].append("Steve Jobs")
    if "Apple" in text:
        entities["ORG"].append("Apple")
    if "California" in text:
        entities["GPE"].append("California")
    
    return entities


def validate_facts(facts: List[str], context: str) -> List[Dict[str, Any]]:
    """
    Validate factual claims against known information.
    
    In production, use fact-checking APIs or vector databases.
    
    Args:
        facts: List of claims to validate
        context: Context for validation
        
    Returns:
        List of validation results with confidence scores
        
    Example:
        results = validate_facts(
            ["AI agents use ReAct pattern"],
            "AI research 2025"
        )
        print(results[0]["confidence"])  # 0.95
    """
    logger.debug(f"Validating {len(facts)} facts")
    
    # Mock implementation
    validations = []
    for fact in facts:
        validations.append({
            "fact": fact,
            "is_valid": True,
            "confidence": 0.85,
            "reasoning": f"Fact aligns with {context} knowledge base"
        })
    
    return validations


def extract_key_phrases(text: str, top_n: int = 10) -> List[str]:
    """
    Extract important phrases/keywords from text.
    
    In production, use TFIDF or advanced NLP models.
    
    Args:
        text: Text to extract phrases from
        top_n: Number of top phrases to return
        
    Returns:
        List of key phrases ranked by importance
        
    Example:
        phrases = extract_key_phrases(research_text, top_n=5)
        print(phrases)  # ["AI agents", "ReAct pattern", ...]
    """
    logger.debug(f"Extracting key phrases from text ({len(text)} chars)")
    
    # Mock implementation
    # In production, use TFIDF or sklearn
    common_phrases = [
        "AI agents",
        "language models",
        "tool use",
        "memory systems",
        "production-ready",
        "error handling",
        "API integration",
        "autonomous systems"
    ]
    
    # Filter phrases that appear in text
    found_phrases = [p for p in common_phrases if p.lower() in text.lower()]
    
    return found_phrases[:top_n]


def summarize_text(text: str, max_length: int = 500) -> str:
    """
    Summarize text while preserving key information.
    
    In production, use transformers for abstractive summarization.
    
    Args:
        text: Text to summarize
        max_length: Maximum length of summary
        
    Returns:
        Summarized text
        
    Example:
        summary = summarize_text(long_document, max_length=300)
    """
    logger.debug(f"Summarizing text ({len(text)} -> {max_length} chars)")
    
    # Mock implementation
    # In production, use Hugging Face transformers
    # model = pipeline("summarization", model="facebook/bart-large-cnn")
    
    sentences = text.split(".")
    summary = ". ".join(sentences[:2]) + "."
    
    return summary[:max_length]


def clean_text(text: str) -> str:
    """
    Clean and normalize text.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters (keep alphanumeric and basic punctuation)
    text = re.sub(r'[^\w\s.?,!;:\-]', '', text)
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def format_citation(text: str, source: str, url: str) -> str:
    """
    Format a citation in APA style.
    
    Args:
        text: Text being cited
        source: Source title
        url: Source URL
        
    Returns:
        Formatted citation
    """
    return f'"{text}" - {source} ({url})'


if __name__ == "__main__":
    # Test the tools
    logger.info("Testing research tools")
    
    # Test search
    results = search_web("AI agents 2025", max_results=3)
    print(f"✓ Search found {len(results)} results")
    
    # Test fetch
    doc = fetch_document("https://example.com/article")
    print(f"✓ Fetched document: {doc['title']}")
    
    # Test entity extraction
    entities = extract_entities("Steve Jobs founded Apple in California")
    print(f"✓ Extracted entities: {entities}")
    
    # Test fact validation
    validations = validate_facts(["AI uses ReAct"], "AI research")
    print(f"✓ Validated {len(validations)} facts")
    
    # Test phrase extraction
    phrases = extract_key_phrases("AI agents and language models", top_n=3)
    print(f"✓ Extracted {len(phrases)} key phrases")
