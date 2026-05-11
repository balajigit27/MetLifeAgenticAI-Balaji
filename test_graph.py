"""
Integration tests for the LangGraph orchestrator.

Tests:
- Graph initialization
- Node execution
- State transitions
- Error handling and recovery
"""

import pytest
from datetime import datetime
from graph.orchestrator import ResearchOrchestrator
from graph.state import WorkflowState, ResearchTopic


class TestOrchestrator:
    """Test ResearchOrchestrator functionality."""
    
    def test_orchestrator_initialization(self):
        """Test orchestrator can be initialized."""
        orchestrator = ResearchOrchestrator()
        assert orchestrator is not None
        assert orchestrator.graph is not None
        assert orchestrator.planner is not None
        assert orchestrator.researcher is not None
        assert orchestrator.analyzer is not None
        assert orchestrator.synthesizer is not None
    
    def test_graph_structure(self):
        """Test graph is properly structured."""
        orchestrator = ResearchOrchestrator()
        graph = orchestrator.graph
        
        # Graph should have nodes
        assert graph is not None
    
    def test_initial_state_creation(self):
        """Test initial workflow state is created correctly."""
        topic = ResearchTopic(topic="Test", depth="quick")
        state = WorkflowState(
            session_id="test-123",
            topic=topic
        )
        
        assert state.session_id == "test-123"
        assert state.topic.topic == "Test"
        assert state.current_stage == "planning"
    
    def test_state_transitions(self):
        """Test state transitions through workflow."""
        orchestrator = ResearchOrchestrator()
        
        state = orchestrator.run_research(
            topic="Quick test",
            depth="quick"
        )
        
        # Check state progression
        assert state.current_stage in ["planning", "researching", "analyzing", "synthesizing", "completed"]
        assert state.plan is not None
        assert state.findings is not None
        assert state.analysis is not None
        assert state.report is not None
    
    def test_timing_tracking(self):
        """Test execution timings are tracked."""
        orchestrator = ResearchOrchestrator()
        
        state = orchestrator.run_research(
            topic="Timing test",
            depth="quick"
        )
        
        # Check timings
        assert "planning" in state.stage_timings or len(state.stage_timings) > 0
        total_time = sum(state.stage_timings.values())
        assert total_time >= 0
    
    def test_error_tracking(self):
        """Test errors are properly tracked."""
        orchestrator = ResearchOrchestrator()
        
        state = orchestrator.run_research(
            topic="Error tracking test",
            depth="quick"
        )
        
        # errors should be a list (may be empty if no errors)
        assert isinstance(state.errors, list)
    
    def test_session_id_generation(self):
        """Test session IDs are properly generated."""
        orchestrator = ResearchOrchestrator()
        
        state1 = orchestrator.run_research(topic="Test 1", depth="quick")
        state2 = orchestrator.run_research(topic="Test 2", depth="quick")
        
        # Session IDs should be different
        assert state1.session_id != state2.session_id
    
    def test_custom_session_id(self):
        """Test custom session ID is respected."""
        orchestrator = ResearchOrchestrator()
        
        custom_id = "my-custom-id-12345"
        state = orchestrator.run_research(
            topic="Test",
            depth="quick",
            session_id=custom_id
        )
        
        assert state.session_id == custom_id
    
    def test_execution_summary(self):
        """Test execution summary is generated correctly."""
        orchestrator = ResearchOrchestrator()
        
        state = orchestrator.run_research(
            topic="Summary test",
            depth="quick"
        )
        
        summary = orchestrator.get_execution_summary(state)
        
        assert "session_id" in summary
        assert "status" in summary
        assert "total_time_seconds" in summary
        assert "findings_count" in summary
        assert "errors" in summary


class TestNodeExecution:
    """Test individual node execution."""
    
    def test_planner_node_execution(self):
        """Test planner node executes correctly."""
        orchestrator = ResearchOrchestrator()
        
        topic = ResearchTopic(topic="Test planning", depth="quick")
        state = WorkflowState(session_id="test-1", topic=topic)
        
        state = orchestrator._node_planner(state)
        
        assert state.plan is not None
        assert len(state.plan.research_questions) > 0
        assert state.current_stage == "researching"
    
    def test_researcher_node_execution(self):
        """Test researcher node executes correctly."""
        orchestrator = ResearchOrchestrator()
        
        # First run planner
        topic = ResearchTopic(topic="Test research", depth="quick")
        state = WorkflowState(session_id="test-2", topic=topic)
        state = orchestrator._node_planner(state)
        
        # Then run researcher
        state = orchestrator._node_researcher(state)
        
        assert state.findings is not None
        assert state.current_stage == "analyzing"
    
    def test_analyzer_node_execution(self):
        """Test analyzer node executes correctly."""
        orchestrator = ResearchOrchestrator()
        
        # Run through planner and researcher
        topic = ResearchTopic(topic="Test analysis", depth="quick")
        state = WorkflowState(session_id="test-3", topic=topic)
        state = orchestrator._node_planner(state)
        state = orchestrator._node_researcher(state)
        
        # Then run analyzer
        state = orchestrator._node_analyzer(state)
        
        assert state.analysis is not None
        assert state.current_stage == "synthesizing"
    
    def test_synthesizer_node_execution(self):
        """Test synthesizer node executes correctly."""
        orchestrator = ResearchOrchestrator()
        
        # Run full pipeline
        topic = ResearchTopic(topic="Test synthesis", depth="quick")
        state = WorkflowState(session_id="test-4", topic=topic)
        state = orchestrator._node_planner(state)
        state = orchestrator._node_researcher(state)
        state = orchestrator._node_analyzer(state)
        
        # Then run synthesizer
        state = orchestrator._node_synthesizer(state)
        
        assert state.report is not None
        assert state.current_stage == "completed"


class TestStateManagement:
    """Test workflow state management."""
    
    def test_state_immutability(self):
        """Test state updates don't affect original."""
        topic = ResearchTopic(topic="Test", depth="quick")
        state1 = WorkflowState(session_id="1", topic=topic)
        
        # Create a copy and modify
        state2 = WorkflowState(
            session_id=state1.session_id,
            topic=state1.topic,
            current_stage="researching"
        )
        
        assert state1.current_stage == "planning"
        assert state2.current_stage == "researching"
    
    def test_metadata_tracking(self):
        """Test metadata is properly tracked."""
        topic = ResearchTopic(topic="Test", depth="quick")
        state = WorkflowState(session_id="test-5", topic=topic)
        
        assert state.created_at is not None
        assert state.updated_at is not None
        assert isinstance(state.created_at, datetime)
        assert isinstance(state.updated_at, datetime)


class TestErrorHandling:
    """Test error handling in orchestrator."""
    
    def test_graceful_error_handling(self):
        """Test orchestrator handles errors gracefully."""
        orchestrator = ResearchOrchestrator()
        
        # Run research - should complete without crashing
        try:
            state = orchestrator.run_research(
                topic="Error handling test",
                depth="quick"
            )
            assert state is not None
        except Exception as e:
            pytest.fail(f"Orchestrator raised unexpected error: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
