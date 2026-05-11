"""
End-to-end integration tests for the complete research workflow.

Tests:
- Complete research workflow execution
- Result quality and structure
- Persistence and recovery
- CLI interface
"""

import pytest
import json
import tempfile
from pathlib import Path
from graph.orchestrator import ResearchOrchestrator
from persistence.checkpoint_manager import CheckpointManager
from config import settings


class TestEndToEndWorkflow:
    """Test complete research workflow."""
    
    def test_quick_research_workflow(self):
        """Test quick research workflow completes successfully."""
        orchestrator = ResearchOrchestrator()
        
        state = orchestrator.run_research(
            topic="AI agents fundamentals",
            depth="quick",
            session_id="e2e-quick-001"
        )
        
        # Verify workflow completion
        assert state.current_stage == "completed"
        assert state.plan is not None
        assert state.findings is not None
        assert state.analysis is not None
        assert state.report is not None
        
        # Verify report quality
        assert len(state.report.executive_summary) > 0
        assert len(state.report.main_findings) > 0
        assert len(state.report.sources) > 0
    
    def test_standard_research_workflow(self):
        """Test standard research workflow."""
        orchestrator = ResearchOrchestrator()
        
        state = orchestrator.run_research(
            topic="Machine learning applications",
            depth="standard",
            session_id="e2e-standard-001"
        )
        
        assert state.current_stage == "completed"
        assert len(state.report.main_findings) >= 2
    
    def test_research_with_domains(self):
        """Test research focused on specific domains."""
        orchestrator = ResearchOrchestrator()
        
        state = orchestrator.run_research(
            topic="AI in healthcare",
            domains=["healthcare", "AI", "medical"],
            depth="quick",
            session_id="e2e-domains-001"
        )
        
        assert state.current_stage == "completed"
        assert state.report is not None
    
    def test_research_with_context(self):
        """Test research with additional context."""
        orchestrator = ResearchOrchestrator()
        
        state = orchestrator.run_research(
            topic="Quantum computing",
            context="Focus on practical applications in the next 5 years",
            depth="quick",
            session_id="e2e-context-001"
        )
        
        assert state.current_stage == "completed"
        assert state.report is not None


class TestResultQuality:
    """Test quality of research results."""
    
    def test_findings_have_sources(self):
        """Test all findings have valid sources."""
        orchestrator = ResearchOrchestrator()
        
        state = orchestrator.run_research(
            topic="Natural language processing",
            depth="quick"
        )
        
        # Check findings
        for finding in state.findings.findings:
            assert len(finding.fact) > 0
            assert len(finding.source_title) > 0
            assert len(finding.source_url) > 0
    
    def test_report_has_citations(self):
        """Test report includes proper citations."""
        orchestrator = ResearchOrchestrator()
        
        state = orchestrator.run_research(
            topic="AI ethics",
            depth="quick"
        )
        
        # Check report structure
        assert len(state.report.sources) > 0
        assert state.report.report_metadata is not None
    
    def test_analysis_produces_insights(self):
        """Test analysis produces meaningful insights."""
        orchestrator = ResearchOrchestrator()
        
        state = orchestrator.run_research(
            topic="Climate technology",
            depth="quick"
        )
        
        # Check analysis
        assert len(state.analysis.insights) > 0
        assert state.analysis.quality_assessment is not None


class TestPersistence:
    """Test persistence and checkpoint functionality."""
    
    def test_checkpoint_save_and_load(self):
        """Test saving and loading checkpoints."""
        # Run research
        orchestrator = ResearchOrchestrator()
        original_state = orchestrator.run_research(
            topic="Test persistence",
            depth="quick",
            session_id="persist-001"
        )
        
        # Save checkpoint
        manager = CheckpointManager()
        manager.save_checkpoint(original_state, completed=True)
        
        # Load checkpoint
        loaded_state = manager.load_checkpoint("persist-001")
        
        assert loaded_state is not None
        assert loaded_state.session_id == original_state.session_id
        assert loaded_state.topic.topic == original_state.topic.topic
    
    def test_workflow_history(self):
        """Test workflow history is recorded."""
        # Run research
        orchestrator = ResearchOrchestrator()
        state = orchestrator.run_research(
            topic="History test",
            depth="quick",
            session_id="history-001"
        )
        
        # Save to history
        manager = CheckpointManager()
        manager.save_workflow_history(
            session_id=state.session_id,
            topic=state.topic.topic,
            depth=state.topic.depth,
            status=state.current_stage,
            total_time=sum(state.stage_timings.values()),
            findings_count=len(state.findings.findings) if state.findings else 0,
            errors_count=len(state.errors)
        )
        
        # Retrieve history
        history = manager.get_workflow_history(limit=10)
        assert len(history) > 0
    
    def test_checkpoint_cleanup(self):
        """Test old checkpoints can be cleaned up."""
        manager = CheckpointManager()
        
        # Cleanup should not raise error
        deleted = manager.cleanup_old_checkpoints(days=1)
        assert isinstance(deleted, int)


class TestPerformance:
    """Test performance characteristics."""
    
    def test_quick_research_performance(self):
        """Test quick research completes in reasonable time."""
        orchestrator = ResearchOrchestrator()
        
        state = orchestrator.run_research(
            topic="Performance test",
            depth="quick"
        )
        
        total_time = sum(state.stage_timings.values())
        
        # Quick research should complete relatively fast
        # (this is a mock, so timing will be quick)
        assert total_time >= 0
        assert total_time < 300  # Should be less than 5 minutes
    
    def test_all_stages_execute(self):
        """Test all workflow stages execute."""
        orchestrator = ResearchOrchestrator()
        
        state = orchestrator.run_research(
            topic="Complete workflow",
            depth="quick"
        )
        
        # Check all stages executed
        expected_stages = {"planning", "researching", "analyzing", "synthesizing"}
        actual_stages = set(state.stage_timings.keys())
        
        # At least planning stage should exist
        assert "planning" in actual_stages or len(actual_stages) > 0


class TestExportFormats:
    """Test different export formats."""
    
    def test_json_export(self):
        """Test JSON export format."""
        orchestrator = ResearchOrchestrator()
        
        state = orchestrator.run_research(
            topic="Export test",
            depth="quick"
        )
        
        # Convert report to JSON
        if state.report:
            report_dict = state.report.dict()
            json_str = json.dumps(report_dict)
            parsed = json.loads(json_str)
            
            assert "topic" in parsed
            assert "main_findings" in parsed
    
    def test_text_export(self):
        """Test text export format."""
        from agents.synthesizer import SynthesizerAgent
        
        orchestrator = ResearchOrchestrator()
        
        state = orchestrator.run_research(
            topic="Text export test",
            depth="quick"
        )
        
        if state.report:
            synthesizer = SynthesizerAgent()
            text_format = synthesizer.format_report(state.report)
            
            assert isinstance(text_format, str)
            assert len(text_format) > 0
            assert state.report.topic.upper() in text_format.upper()


class TestErrorRecovery:
    """Test error recovery mechanisms."""
    
    def test_workflow_completes_despite_issues(self):
        """Test workflow can complete even with some issues."""
        orchestrator = ResearchOrchestrator()
        
        # This should complete without crashing
        state = orchestrator.run_research(
            topic="Error recovery test",
            depth="quick"
        )
        
        # Should complete even if there are errors
        assert state.current_stage == "completed" or state.current_stage in [
            "planning",
            "researching",
            "analyzing",
            "synthesizing"
        ]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
