"""
Unit tests for individual agent implementations.

Tests:
- Planner agent planning functionality
- Researcher agent research execution
- Analyzer agent analysis
- Synthesizer agent report generation
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from config import get_llm
from graph.state import (
    ResearchTopic,
    ResearchPlan,
    ResearchQuestion,
    Finding,
    ResearchFindings,
    AnalysisInsight,
    AnalysisResult,
)
from agents.planner import PlannerAgent
from agents.researcher import ResearcherAgent
from agents.analyzer import AnalyzerAgent
from agents.synthesizer import SynthesizerAgent
from agents.tools import (
    search_web,
    fetch_document,
    extract_entities,
    validate_facts,
    extract_key_phrases,
)


class TestPlannerAgent:
    """Test Planner Agent functionality."""
    
    def test_planner_initialization(self):
        """Test planner agent can be initialized."""
        planner = PlannerAgent()
        assert planner is not None
        assert planner.llm is not None
    
    def test_plan_research_structure(self):
        """Test plan_research returns correct structure."""
        planner = PlannerAgent()
        plan = planner.plan_research(
            topic="AI agents",
            depth="quick"
        )
        
        assert isinstance(plan, ResearchPlan)
        assert plan.topic == "AI agents"
        assert isinstance(plan.research_questions, list)
        assert len(plan.research_questions) > 0
        assert isinstance(plan.research_questions[0], ResearchQuestion)
    
    def test_plan_research_with_domains(self):
        """Test planning with specific domains."""
        planner = PlannerAgent()
        plan = planner.plan_research(
            topic="AI ethics",
            domains=["ethics", "AI", "governance"]
        )
        
        assert plan.topic == "AI ethics"
        assert len(plan.research_questions) > 0
    
    def test_plan_research_includes_keywords(self):
        """Test that plan includes suggested keywords."""
        planner = PlannerAgent()
        plan = planner.plan_research(topic="Quantum computing")
        
        assert len(plan.suggested_keywords) > 0
        assert all(isinstance(k, str) for k in plan.suggested_keywords)


class TestResearcherAgent:
    """Test Researcher Agent functionality."""
    
    def test_researcher_initialization(self):
        """Test researcher agent can be initialized."""
        researcher = ResearcherAgent()
        assert researcher is not None
        assert researcher.llm is not None
    
    def test_conduct_research_structure(self):
        """Test conduct_research returns correct structure."""
        researcher = ResearcherAgent()
        findings = researcher.conduct_research(
            topic="AI agents",
            research_questions=["What are AI agents?"]
        )
        
        assert isinstance(findings, ResearchFindings)
        assert findings.topic == "AI agents"
        assert isinstance(findings.findings, list)
    
    def test_research_with_keywords(self):
        """Test research with specific keywords."""
        researcher = ResearcherAgent()
        findings = researcher.conduct_research(
            topic="Web3",
            research_questions=["What is Web3?"],
            keywords=["blockchain", "decentralized"]
        )
        
        assert findings.topic == "Web3"
        assert findings.total_sources_checked > 0


class TestAnalyzerAgent:
    """Test Analyzer Agent functionality."""
    
    def test_analyzer_initialization(self):
        """Test analyzer agent can be initialized."""
        analyzer = AnalyzerAgent()
        assert analyzer is not None
        assert analyzer.llm is not None
    
    def test_analyze_findings_structure(self):
        """Test analyze_findings returns correct structure."""
        analyzer = AnalyzerAgent()
        
        # Create sample findings
        findings = ResearchFindings(
            topic="AI agents",
            findings=[
                Finding(
                    fact="AI agents use ReAct",
                    source_title="Paper",
                    source_url="https://example.com"
                )
            ]
        )
        
        analysis = analyzer.analyze_findings("AI agents", findings)
        
        assert isinstance(analysis, AnalysisResult)
        assert analysis.topic == "AI agents"
        assert isinstance(analysis.insights, list)
        assert isinstance(analysis.quality_assessment, dict)
    
    def test_quality_assessment_metrics(self):
        """Test quality assessment produces valid metrics."""
        analyzer = AnalyzerAgent()
        findings = ResearchFindings(
            topic="Test",
            findings=[
                Finding(
                    fact="Test fact",
                    source_title="Test Source",
                    source_url="https://example.com",
                    confidence=0.9
                )
            ],
            total_sources_checked=5
        )
        
        metrics = analyzer.assess_quality(findings)
        
        assert 0 <= metrics.get("accuracy", 0) <= 1
        assert 0 <= metrics.get("completeness", 0) <= 1


class TestSynthesizerAgent:
    """Test Synthesizer Agent functionality."""
    
    def test_synthesizer_initialization(self):
        """Test synthesizer agent can be initialized."""
        synthesizer = SynthesizerAgent()
        assert synthesizer is not None
        assert synthesizer.llm is not None
    
    def test_synthesize_report_structure(self):
        """Test synthesize_report returns correct structure."""
        synthesizer = SynthesizerAgent()
        
        # Create sample data
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
                    fact="AI agents combine language models with tools",
                    source_title="LangChain Docs",
                    source_url="https://example.com"
                )
            ]
        )
        
        analysis = AnalysisResult(
            topic="AI agents",
            insights=[
                AnalysisInsight(insight="Agents are powerful", insight_type="pattern")
            ]
        )
        
        report = synthesizer.synthesize_report(
            topic="AI agents",
            plan=plan,
            findings=findings,
            analysis=analysis
        )
        
        assert report.topic == "AI agents"
        assert len(report.executive_summary) > 0
        assert len(report.main_findings) > 0
        assert len(report.sources) > 0
    
    def test_format_report(self):
        """Test report formatting."""
        from graph.state import ResearchReport
        
        synthesizer = SynthesizerAgent()
        report = ResearchReport(
            topic="Test Topic",
            executive_summary="Summary here"
        )
        
        formatted = synthesizer.format_report(report)
        assert "Test Topic" in formatted.upper()
        assert "Summary here" in formatted


class TestTools:
    """Test shared tools."""
    
    def test_search_web(self):
        """Test web search tool."""
        results = search_web("AI agents", max_results=3)
        assert isinstance(results, list)
        assert len(results) <= 3
        if results:
            assert "title" in results[0]
            assert "url" in results[0]
    
    def test_fetch_document(self):
        """Test document fetching."""
        doc = fetch_document("https://example.com")
        assert isinstance(doc, dict)
        assert "title" in doc
        assert "text" in doc
        assert "metadata" in doc
    
    def test_extract_entities(self):
        """Test entity extraction."""
        text = "Steve Jobs founded Apple in California"
        entities = extract_entities(text)
        
        assert isinstance(entities, dict)
        assert "PERSON" in entities
        assert "ORG" in entities
        assert "GPE" in entities
    
    def test_validate_facts(self):
        """Test fact validation."""
        facts = ["AI agents use ReAct pattern"]
        validations = validate_facts(facts, "AI research")
        
        assert isinstance(validations, list)
        assert len(validations) == 1
        assert "confidence" in validations[0]
    
    def test_extract_key_phrases(self):
        """Test key phrase extraction."""
        text = "AI agents and language models are powerful"
        phrases = extract_key_phrases(text, top_n=3)
        
        assert isinstance(phrases, list)
        assert len(phrases) <= 3


class TestDataModels:
    """Test Pydantic data models."""
    
    def test_research_topic_validation(self):
        """Test ResearchTopic model validation."""
        topic = ResearchTopic(
            topic="AI agents",
            depth="standard"
        )
        
        assert topic.topic == "AI agents"
        assert topic.depth == "standard"
    
    def test_research_plan_validation(self):
        """Test ResearchPlan model validation."""
        plan = ResearchPlan(
            topic="Test",
            research_questions=[
                ResearchQuestion(question="Q1", priority=1)
            ]
        )
        
        assert len(plan.research_questions) == 1
    
    def test_finding_validation(self):
        """Test Finding model validation."""
        finding = Finding(
            fact="Test fact",
            source_title="Source",
            source_url="https://example.com"
        )
        
        assert 0 <= finding.confidence <= 1
        assert 0 <= finding.relevance_score <= 1


# Fixtures
@pytest.fixture
def mock_llm():
    """Create mock LLM for testing."""
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(content='{"key": "value"}')
    return mock


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
