"""
State models for the research orchestration workflow.

These Pydantic models define the structure of data that flows through
the LangGraph state machine. They ensure type safety and make the
workflow self-documenting.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ResearchTopic(BaseModel):
    """Input: Research topic provided by user."""
    
    topic: str = Field(..., description="Main research topic/question")
    domains: Optional[List[str]] = Field(
        default=None,
        description="Specific domains to focus on (e.g., ['AI', 'ethics'])"
    )
    depth: str = Field(
        default="standard",
        description="Research depth: quick (shallow), standard, deep (comprehensive)"
    )
    max_sources: int = Field(
        default=10,
        description="Maximum number of sources to use"
    )
    context: Optional[str] = Field(
        default=None,
        description="Additional context or background information"
    )


class ResearchQuestion(BaseModel):
    """A specific research question derived from the main topic."""
    
    question: str = Field(..., description="Specific research question")
    priority: int = Field(
        default=1,
        description="Priority level (1=high, 3=low)"
    )
    reasoning: str = Field(
        default="",
        description="Why this question is important for the research"
    )


class ResearchPlan(BaseModel):
    """Output of Planner Agent: Breakdown of research into specific questions."""
    
    topic: str = Field(..., description="Original research topic")
    research_questions: List[ResearchQuestion] = Field(
        ...,
        description="List of specific research questions to investigate"
    )
    information_gaps: List[str] = Field(
        default_factory=list,
        description="Identified gaps in current knowledge"
    )
    suggested_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords to use in web searches"
    )
    plan_summary: str = Field(
        default="",
        description="Summary of the research plan"
    )


class Finding(BaseModel):
    """A single research finding with source information."""
    
    fact: str = Field(..., description="The research finding")
    source_title: str = Field(..., description="Title of the source")
    source_url: str = Field(..., description="URL of the source")
    relevance_score: float = Field(
        default=0.5,
        description="How relevant this finding is (0-1)"
    )
    confidence: float = Field(
        default=0.5,
        description="Confidence in the accuracy of this finding (0-1)"
    )
    extraction_method: str = Field(
        default="extraction",
        description="How the finding was extracted (extraction, summary, synthesis)"
    )


class ResearchFindings(BaseModel):
    """Output of Researcher Agent: Collected findings from research."""
    
    topic: str = Field(..., description="Original research topic")
    findings: List[Finding] = Field(
        default_factory=list,
        description="List of extracted findings"
    )
    total_sources_checked: int = Field(
        default=0,
        description="Total number of sources examined"
    )
    sources_with_errors: List[str] = Field(
        default_factory=list,
        description="Sources that failed to load or process"
    )
    research_summary: str = Field(
        default="",
        description="Summary of findings collected"
    )


class AnalysisInsight(BaseModel):
    """An insight derived from analyzing research findings."""
    
    insight: str = Field(..., description="The insight or pattern identified")
    related_findings: List[int] = Field(
        default_factory=list,
        description="Indices of related findings"
    )
    insight_type: str = Field(
        default="pattern",
        description="Type of insight: pattern, contradiction, gap, trend, etc."
    )
    confidence: float = Field(
        default=0.5,
        description="Confidence in this insight (0-1)"
    )


class AnalysisResult(BaseModel):
    """Output of Analyzer Agent: Analysis of research findings."""
    
    topic: str = Field(..., description="Original research topic")
    insights: List[AnalysisInsight] = Field(
        default_factory=list,
        description="List of insights derived from findings"
    )
    contradictions_found: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Contradictions or conflicting information"
    )
    quality_assessment: Dict[str, float] = Field(
        default_factory=dict,
        description="Quality metrics (completeness, accuracy, coverage, etc.)"
    )
    analysis_summary: str = Field(
        default="",
        description="Summary of the analysis"
    )


class Citation(BaseModel):
    """A citation in the final report."""
    
    text: str = Field(..., description="Text being cited")
    source: str = Field(..., description="Source title/URL")
    page_number: Optional[int] = Field(
        default=None,
        description="Page number if applicable"
    )


class ResearchReport(BaseModel):
    """Output of Synthesizer Agent: Final research report."""
    
    topic: str = Field(..., description="Original research topic")
    executive_summary: str = Field(
        ...,
        description="High-level summary of findings"
    )
    main_findings: List[str] = Field(
        default_factory=list,
        description="Key findings in order of importance"
    )
    detailed_analysis: str = Field(
        default="",
        description="Detailed narrative analysis"
    )
    citations: List[Citation] = Field(
        default_factory=list,
        description="All citations used in the report"
    )
    sources: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of all sources (title, URL)"
    )
    limitations: List[str] = Field(
        default_factory=list,
        description="Limitations of the research"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommendations for further research"
    )
    report_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata (generated timestamp, research duration, etc.)"
    )


class WorkflowState(BaseModel):
    """Complete state of the research orchestration workflow."""
    
    # Identifiers
    session_id: str = Field(..., description="Unique session ID for this research")
    topic: ResearchTopic = Field(..., description="Original research topic")
    
    # Intermediate results
    plan: Optional[ResearchPlan] = Field(
        default=None,
        description="Research plan from Planner agent"
    )
    findings: Optional[ResearchFindings] = Field(
        default=None,
        description="Research findings from Researcher agent"
    )
    analysis: Optional[AnalysisResult] = Field(
        default=None,
        description="Analysis from Analyzer agent"
    )
    report: Optional[ResearchReport] = Field(
        default=None,
        description="Final report from Synthesizer agent"
    )
    
    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this workflow was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this workflow was last updated"
    )
    current_stage: str = Field(
        default="planning",
        description="Current stage: planning, researching, analyzing, synthesizing, completed"
    )
    
    # Error tracking
    errors: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of errors encountered (stage, message)"
    )
    
    # Performance metrics
    stage_timings: Dict[str, float] = Field(
        default_factory=dict,
        description="Execution time for each stage in seconds"
    )
    
    class Config:
        """Pydantic config."""
        extra = "allow"  # Allow extra fields for flexibility
        arbitrary_types_allowed = True


if __name__ == "__main__":
    # Example usage and validation
    topic = ResearchTopic(
        topic="AI agents in 2025",
        depth="standard",
        domains=["AI", "software engineering"]
    )
    print("✓ ResearchTopic created:", topic.topic)
    
    plan = ResearchPlan(
        topic=topic.topic,
        research_questions=[
            ResearchQuestion(
                question="What are the current capabilities of AI agents?",
                priority=1
            )
        ]
    )
    print("✓ ResearchPlan created with", len(plan.research_questions), "questions")
