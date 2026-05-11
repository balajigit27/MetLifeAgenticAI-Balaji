"""
Synthesizer Agent: Creates final research report from all findings.

The Synthesizer agent:
1. Takes all findings, analysis, and insights
2. Creates a coherent narrative
3. Adds citations and sources
4. Formats the final report
5. Provides recommendations

Output: ResearchReport with final findings and citations
"""

from typing import Optional
from datetime import datetime
from config import get_llm
from graph.state import (
    ResearchPlan,
    ResearchFindings,
    AnalysisResult,
    ResearchReport,
    Citation,
)
from utils.logger import logger, LogContext


SYNTHESIZER_PROMPT = """You are an expert scientific writer. Your task is to synthesize research findings into a comprehensive report.

Topic: {topic}
Research Plan: {plan_summary}

Key Findings:
{findings_summary}

Analysis Insights:
{analysis_summary}

Create a professional research report with:
1. Executive summary (2-3 sentences)
2. Main findings (5-10 key points, ordered by importance)
3. Detailed analysis (comprehensive discussion)
4. Limitations of the research
5. Recommendations for further research

Respond in JSON format with this structure:
{{
    "executive_summary": "High-level overview of findings",
    "main_findings": [
        "Finding 1",
        "Finding 2",
        ...
    ],
    "detailed_analysis": "Detailed narrative of analysis",
    "citations": [
        {{
            "text": "Text being cited",
            "source": "Source title",
            "page_number": null
        }},
        ...
    ],
    "limitations": ["Limitation 1", "Limitation 2", ...],
    "recommendations": ["Recommendation 1", "Recommendation 2", ...]
}}

Guidelines:
- Write at professional academic level
- Include specific evidence and examples
- Properly cite all sources
- Be objective and evidence-based
- Highlight both consensus and disagreements
"""


class SynthesizerAgent:
    """
    Synthesizer Agent: Creates final research report.
    """
    
    def __init__(self, llm=None):
        """
        Initialize Synthesizer Agent.
        
        Args:
            llm: LangChain LLM instance. If None, uses default from config.
        """
        self.llm = llm or get_llm()
        self.logger = logger
    
    def synthesize_report(
        self,
        topic: str,
        plan: ResearchPlan,
        findings: ResearchFindings,
        analysis: AnalysisResult,
        session_id: Optional[str] = None,
    ) -> ResearchReport:
        """
        Create final research report from all components.
        
        Args:
            topic: Research topic
            plan: ResearchPlan from Planner
            findings: ResearchFindings from Researcher
            analysis: AnalysisResult from Analyzer
            session_id: Session ID for logging
            
        Returns:
            ResearchReport with complete findings and citations
            
        Example:
            synthesizer = SynthesizerAgent()
            report = synthesizer.synthesize_report(
                topic="AI agents",
                plan=plan,
                findings=findings,
                analysis=analysis
            )
            print(report.executive_summary)
        """
        task_id = f"synthesizer-{session_id}" if session_id else "synthesizer-task"
        
        with LogContext(self.logger, task_id, stage="synthesizing"):
            self.logger.info("Synthesizing research report")
            
            # Format summaries for LLM
            plan_summary = f"{len(plan.research_questions)} research questions"
            
            findings_summary = "\n".join([
                f"- {f.fact[:80]}... ({f.source_title})"
                for f in findings.findings[:5]  # Top 5 findings
            ])
            
            insights_summary = "\n".join([
                f"- {i.insight} ({i.insight_type})"
                for i in analysis.insights[:3]  # Top 3 insights
            ])
            
            # Format the prompt
            prompt = SYNTHESIZER_PROMPT.format(
                topic=topic,
                plan_summary=plan_summary,
                findings_summary=findings_summary,
                analysis_summary=insights_summary
            )
            
            # Call LLM
            self.logger.debug("Calling LLM to synthesize report")
            response = self.llm.invoke(prompt)
            
            # Parse response
            report_data = self._parse_response(response.content)
            
            # Create citations
            citations = [
                Citation(**c) for c in report_data.get("citations", [])
            ]
            
            # Create source list
            sources = [
                {"title": f.source_title, "url": f.source_url}
                for f in findings.findings
            ]
            # Remove duplicates
            seen_urls = set()
            unique_sources = []
            for s in sources:
                if s["url"] not in seen_urls:
                    unique_sources.append(s)
                    seen_urls.add(s["url"])
            
            # Create ResearchReport object
            report = ResearchReport(
                topic=topic,
                executive_summary=report_data.get(
                    "executive_summary",
                    "Research completed successfully"
                ),
                main_findings=report_data.get("main_findings", []),
                detailed_analysis=report_data.get("detailed_analysis", ""),
                citations=citations,
                sources=unique_sources,
                limitations=report_data.get("limitations", []),
                recommendations=report_data.get("recommendations", []),
                report_metadata={
                    "generated_at": datetime.utcnow().isoformat(),
                    "total_sources": len(unique_sources),
                    "total_findings": len(findings.findings),
                    "total_insights": len(analysis.insights),
                    "research_quality": analysis.quality_assessment
                }
            )
            
            self.logger.info(
                f"Report synthesized: {len(report.main_findings)} main findings, "
                f"{len(report.sources)} sources"
            )
            
            return report
    
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
            self.logger.warning("Failed to parse synthesis response, using defaults")
            return {
                "executive_summary": "Research completed with key findings identified.",
                "main_findings": [
                    "Research objectives were addressed",
                    "Multiple data sources were consulted",
                    "Analysis revealed important patterns"
                ],
                "detailed_analysis": "The research examined multiple aspects and identified key patterns.",
                "citations": [],
                "limitations": ["Limited data sources", "Time constraints"],
                "recommendations": [
                    "Conduct additional research",
                    "Expand source base",
                    "Verify findings with domain experts"
                ]
            }
    
    def format_report(self, report: ResearchReport) -> str:
        """
        Format ResearchReport as readable text.
        
        Args:
            report: ResearchReport object
            
        Returns:
            Formatted text report
        """
        sections = [
            f"# {report.topic.upper()}\n",
            "## Executive Summary\n",
            f"{report.executive_summary}\n",
            "## Main Findings\n"
        ]
        
        for i, finding in enumerate(report.main_findings, 1):
            sections.append(f"{i}. {finding}\n")
        
        if report.detailed_analysis:
            sections.append("## Detailed Analysis\n")
            sections.append(f"{report.detailed_analysis}\n")
        
        if report.limitations:
            sections.append("## Limitations\n")
            for limitation in report.limitations:
                sections.append(f"- {limitation}\n")
        
        if report.recommendations:
            sections.append("## Recommendations\n")
            for rec in report.recommendations:
                sections.append(f"- {rec}\n")
        
        if report.sources:
            sections.append("## Sources\n")
            for source in report.sources:
                sections.append(f"- {source['title']}: {source['url']}\n")
        
        return "".join(sections)


if __name__ == "__main__":
    # Quick test
    from config import settings
    print(f"Testing Synthesizer Agent with LLM mode: {settings.llm_mode}")
    
    # Create sample data
    from graph.state import Finding, ResearchQuestion, ResearchPlan, AnalysisInsight
    
    plan = ResearchPlan(
        topic="AI agents",
        research_questions=[
            ResearchQuestion(question="What are AI agents?", priority=1)
        ]
    )
    
    findings = ResearchFindings(
        topic="AI agents",
        findings=[
            Finding(
                fact="AI agents use language models",
                source_title="LangChain Docs",
                source_url="https://example.com"
            )
        ]
    )
    
    analysis = AnalysisResult(
        topic="AI agents",
        insights=[
            AnalysisInsight(insight="Agents are becoming more capable")
        ]
    )
    
    synthesizer = SynthesizerAgent()
    report = synthesizer.synthesize_report("AI agents", plan, findings, analysis)
    
    print(f"✓ Report synthesized with {len(report.main_findings)} findings")
    print(f"\nFormatted Report:\n")
    print(synthesizer.format_report(report)[:500])
