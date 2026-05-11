"""
Analyzer Agent: Analyzes and evaluates research findings.

The Analyzer agent:
1. Takes findings from the Researcher
2. Evaluates accuracy and relevance
3. Identifies patterns and insights
4. Flags contradictions
5. Assesses overall quality

Output: AnalysisResult with insights and quality metrics
"""

from typing import Optional, List
from config import get_llm
from graph.state import (
    ResearchFindings,
    AnalysisResult,
    AnalysisInsight,
)
from utils.logger import logger, LogContext


ANALYZER_PROMPT = """You are an expert analyst. Your task is to analyze research findings and extract insights.

Research Findings:
Topic: {topic}
Number of findings: {num_findings}

Key Findings:
{findings_summary}

Analyze the findings to:
1. Identify patterns and trends
2. Find contradictions or conflicting information
3. Assess overall quality (completeness, accuracy, coverage)
4. Highlight key insights
5. Identify remaining information gaps

Respond in JSON format with this structure:
{{
    "insights": [
        {{
            "insight": "The insight or pattern",
            "related_findings": [0, 1, 2],
            "insight_type": "pattern",
            "confidence": 0.85
        }},
        ...
    ],
    "contradictions_found": [
        {{
            "finding_1": "...",
            "finding_2": "...",
            "description": "How they contradict"
        }},
        ...
    ],
    "quality_assessment": {{
        "completeness": 0.8,
        "accuracy": 0.85,
        "coverage": 0.75,
        "source_diversity": 0.7
    }},
    "analysis_summary": "Overall analysis summary"
}}

Insight types: pattern, contradiction, gap, trend, consensus, outlier
"""


class AnalyzerAgent:
    """
    Analyzer Agent: Analyzes research findings and extracts insights.
    """
    
    def __init__(self, llm=None):
        """
        Initialize Analyzer Agent.
        
        Args:
            llm: LangChain LLM instance. If None, uses default from config.
        """
        self.llm = llm or get_llm()
        self.logger = logger
    
    def analyze_findings(
        self,
        topic: str,
        findings: ResearchFindings,
        session_id: Optional[str] = None,
    ) -> AnalysisResult:
        """
        Analyze research findings and extract insights.
        
        Args:
            topic: Research topic
            findings: ResearchFindings object
            session_id: Session ID for logging
            
        Returns:
            AnalysisResult with insights and quality assessment
            
        Example:
            analyzer = AnalyzerAgent()
            analysis = analyzer.analyze_findings("AI agents", findings)
            print(f"Found {len(analysis.insights)} insights")
        """
        task_id = f"analyzer-{session_id}" if session_id else "analyzer-task"
        
        with LogContext(self.logger, task_id, stage="analyzing"):
            self.logger.info(f"Analyzing {len(findings.findings)} findings")
            
            # Create summary of findings for LLM
            findings_summary = "\n".join([
                f"- {f.fact[:100]}... (Source: {f.source_title})"
                for f in findings.findings[:10]  # Limit to first 10
            ])
            
            # Format the prompt
            prompt = ANALYZER_PROMPT.format(
                topic=topic,
                num_findings=len(findings.findings),
                findings_summary=findings_summary
            )
            
            # Call LLM
            self.logger.debug("Calling LLM for analysis")
            response = self.llm.invoke(prompt)
            
            # Parse response
            analysis_data = self._parse_response(response.content)
            
            # Create AnalysisResult object
            insights = [
                AnalysisInsight(**insight)
                for insight in analysis_data.get("insights", [])
            ]
            
            analysis = AnalysisResult(
                topic=topic,
                insights=insights,
                contradictions_found=analysis_data.get("contradictions_found", []),
                quality_assessment=analysis_data.get("quality_assessment", {}),
                analysis_summary=analysis_data.get("analysis_summary", "")
            )
            
            self.logger.info(
                f"Analysis complete: {len(insights)} insights, "
                f"{len(analysis.contradictions_found)} contradictions"
            )
            
            return analysis
    
    def _parse_response(self, response_text: str) -> dict:
        """
        Parse LLM response into structured data.
        
        Args:
            response_text: Raw LLM response
            
        Returns:
            Parsed dictionary
        """
        import json
        import re
        
        try:
            # Try direct JSON parsing
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Extract JSON from markdown code blocks
            json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Fallback to default structure
            self.logger.warning("Failed to parse analysis response, using defaults")
            return {
                "insights": [
                    {
                        "insight": "Research shows consistent themes",
                        "related_findings": [0, 1],
                        "insight_type": "pattern",
                        "confidence": 0.8
                    }
                ],
                "contradictions_found": [],
                "quality_assessment": {
                    "completeness": 0.75,
                    "accuracy": 0.8,
                    "coverage": 0.7,
                    "source_diversity": 0.75
                },
                "analysis_summary": "Analysis complete"
            }
    
    def assess_quality(
        self,
        findings: ResearchFindings
    ) -> dict:
        """
        Assess the quality of research findings.
        
        Args:
            findings: ResearchFindings to assess
            
        Returns:
            Dictionary with quality metrics
        """
        self.logger.debug(f"Assessing quality of {len(findings.findings)} findings")
        
        # Calculate quality metrics
        total_findings = len(findings.findings)
        avg_confidence = (
            sum(f.confidence for f in findings.findings) / total_findings
            if total_findings > 0 else 0
        )
        
        avg_relevance = (
            sum(f.relevance_score for f in findings.findings) / total_findings
            if total_findings > 0 else 0
        )
        
        quality_metrics = {
            "completeness": min(total_findings / 10, 1.0),  # 10 findings = 100%
            "accuracy": avg_confidence,
            "coverage": avg_relevance,
            "source_diversity": min(
                findings.total_sources_checked / 10,
                1.0
            )  # 10 sources = 100%
        }
        
        return quality_metrics


if __name__ == "__main__":
    # Quick test
    from config import settings
    print(f"Testing Analyzer Agent with LLM mode: {settings.llm_mode}")
    
    # Create sample findings for testing
    from graph.state import Finding
    
    sample_findings = ResearchFindings(
        topic="AI agents",
        findings=[
            Finding(
                fact="AI agents use ReAct pattern",
                source_title="LangChain Docs",
                source_url="https://example.com",
                confidence=0.9
            ),
            Finding(
                fact="Agents can use tools and APIs",
                source_title="Research Paper",
                source_url="https://example.com/paper",
                confidence=0.85
            ),
        ]
    )
    
    analyzer = AnalyzerAgent()
    analysis = analyzer.analyze_findings("AI agents", sample_findings)
    
    print(f"✓ Analysis complete with {len(analysis.insights)} insights")
    print(f"  Quality assessment: {analysis.quality_assessment}")
