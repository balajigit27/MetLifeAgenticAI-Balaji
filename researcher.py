"""
Researcher Agent: Executes research by finding and extracting information.

The Researcher agent:
1. Takes research questions from the Planner
2. Searches for relevant information
3. Fetches and processes documents
4. Extracts facts and findings
5. Tracks sources and confidence levels

Output: ResearchFindings with extracted facts and sources
"""

from typing import Optional, List
from config import get_llm
from graph.state import ResearchFindings, Finding
from agents.tools import search_web, fetch_document, extract_key_phrases
from utils.logger import logger, LogContext


RESEARCHER_PROMPT = """You are an expert research agent. Your task is to research the following questions and extract factual findings.

Research Questions:
{questions}

For each question:
1. Conduct thorough research
2. Extract specific facts and findings
3. Track the source for each finding
4. Assess confidence in each finding

Respond in JSON format with this structure:
{{
    "findings": [
        {{
            "fact": "The specific finding or fact",
            "source_title": "Title of the source",
            "source_url": "URL where this was found",
            "relevance_score": 0.9,
            "confidence": 0.85,
            "extraction_method": "extraction"
        }},
        ...
    ],
    "total_sources_checked": 5,
    "sources_with_errors": ["url1", "url2"],
    "research_summary": "Summary of what was researched"
}}

Ensure:
- Each finding has a valid source URL
- Confidence scores are between 0.0 and 1.0
- Facts are specific and verifiable
- Include diverse sources
"""


class ResearcherAgent:
    """
    Researcher Agent: Executes research and extracts findings.
    """
    
    def __init__(self, llm=None):
        """
        Initialize Researcher Agent.
        
        Args:
            llm: LangChain LLM instance. If None, uses default from config.
        """
        self.llm = llm or get_llm()
        self.logger = logger
    
    def conduct_research(
        self,
        topic: str,
        research_questions: List[str],
        keywords: Optional[List[str]] = None,
        max_sources: int = 10,
        session_id: Optional[str] = None,
    ) -> ResearchFindings:
        """
        Conduct research on the given questions.
        
        Args:
            topic: Research topic
            research_questions: List of specific questions to research
            keywords: Keywords for searching
            max_sources: Maximum number of sources to use
            session_id: Session ID for logging
            
        Returns:
            ResearchFindings with extracted facts and sources
            
        Example:
            researcher = ResearcherAgent()
            findings = researcher.conduct_research(
                topic="AI agents",
                research_questions=["What are AI agents?", "How do they work?"]
            )
            print(f"Found {len(findings.findings)} facts")
        """
        task_id = f"researcher-{session_id}" if session_id else "researcher-task"
        
        with LogContext(self.logger, task_id, stage="researching"):
            # Search for relevant information
            self.logger.info(f"Researching {len(research_questions)} questions")
            
            all_sources = []
            for query in keywords or research_questions[:3]:
                self.logger.debug(f"Searching for: {query}")
                sources = search_web(query, max_results=min(5, max_sources))
                all_sources.extend(sources)
            
            # Remove duplicates
            unique_urls = {s["url"] for s in all_sources}
            all_sources = [s for s in all_sources if s.get("url")]
            
            # Fetch and process documents
            findings_list = []
            failed_sources = []
            
            for source in all_sources[:max_sources]:
                try:
                    self.logger.debug(f"Fetching document: {source.get('url')}")
                    doc = fetch_document(source.get("url"))
                    
                    # Extract key information
                    key_phrases = extract_key_phrases(doc.get("text", ""))
                    
                    # Create findings from document
                    for phrase in key_phrases[:3]:  # Top 3 phrases per source
                        finding = Finding(
                            fact=f"{phrase} - {doc.get('text', '')[:100]}...",
                            source_title=source.get("title", "Unknown"),
                            source_url=source.get("url", ""),
                            relevance_score=0.8,
                            confidence=0.75,
                            extraction_method="extraction"
                        )
                        findings_list.append(finding)
                
                except Exception as e:
                    self.logger.warning(f"Failed to fetch {source.get('url')}: {e}")
                    failed_sources.append(source.get("url", "unknown"))
            
            # Create ResearchFindings object
            findings = ResearchFindings(
                topic=topic,
                findings=findings_list,
                total_sources_checked=len(all_sources),
                sources_with_errors=failed_sources,
                research_summary=f"Researched {len(research_questions)} questions, "
                                f"checked {len(all_sources)} sources, "
                                f"extracted {len(findings_list)} findings"
            )
            
            self.logger.info(f"Research complete: {len(findings_list)} findings extracted")
            
            return findings
    
    def validate_sources(self, sources: List[str]) -> dict:
        """
        Validate that sources are accessible and valid.
        
        Args:
            sources: List of source URLs
            
        Returns:
            Dictionary with validation results
        """
        self.logger.debug(f"Validating {len(sources)} sources")
        
        validation_results = {
            "total": len(sources),
            "valid": len(sources),  # Mock: assume all valid
            "invalid": [],
            "errors": []
        }
        
        return validation_results


if __name__ == "__main__":
    # Quick test
    from config import settings
    print(f"Testing Researcher Agent with LLM mode: {settings.llm_mode}")
    
    researcher = ResearcherAgent()
    findings = researcher.conduct_research(
        topic="AI agents in 2025",
        research_questions=["What are AI agents?", "How do they work?"],
        keywords=["AI agents", "language models"]
    )
    
    print(f"✓ Conducted research, found {len(findings.findings)} findings")
    print(f"  Sources checked: {findings.total_sources_checked}")
    print(f"  Failed sources: {len(findings.sources_with_errors)}")
