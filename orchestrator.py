"""
LangGraph Orchestrator: Coordinates the multi-agent research workflow.

The orchestrator:
1. Defines the workflow state machine (Planner → Researcher → Analyzer → Synthesizer)
2. Creates nodes for each agent
3. Defines edges and transitions
4. Implements error handling and retries
5. Manages state persistence via checkpoints

This is the core coordination layer for the entire system.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional
from functools import wraps
import time

from langgraph.graph import StateGraph, END
from config import get_llm, settings
from graph.state import (
    WorkflowState,
    ResearchTopic,
    ResearchPlan,
    ResearchFindings,
    AnalysisResult,
    ResearchReport,
)
from agents.planner import PlannerAgent
from agents.researcher import ResearcherAgent
from agents.analyzer import AnalyzerAgent
from agents.synthesizer import SynthesizerAgent
from utils.logger import logger


def retry_with_exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                        delay = min(delay * 2, max_delay)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed: {e}")
            
            raise last_exception
        
        return wrapper
    return decorator


class ResearchOrchestrator:
    """
    Main orchestrator for the multi-agent research workflow.
    
    Coordinates Planner → Researcher → Analyzer → Synthesizer pipeline.
    """
    
    def __init__(self, llm=None):
        """
        Initialize the orchestrator.
        
        Args:
            llm: LangChain LLM instance. If None, uses default from config.
        """
        self.llm = llm or get_llm()
        self.logger = logger
        
        # Initialize agents
        self.planner = PlannerAgent(self.llm)
        self.researcher = ResearcherAgent(self.llm)
        self.analyzer = AnalyzerAgent(self.llm)
        self.synthesizer = SynthesizerAgent(self.llm)
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """
        Build the LangGraph state machine.
        
        Returns:
            Compiled StateGraph
        """
        self.logger.debug("Building LangGraph state machine")
        
        workflow = StateGraph(WorkflowState)
        
        # Add nodes (each agent is a node)
        workflow.add_node("planner", self._node_planner)
        workflow.add_node("researcher", self._node_researcher)
        workflow.add_node("analyzer", self._node_analyzer)
        workflow.add_node("synthesizer", self._node_synthesizer)
        
        # Add edges (transitions between nodes)
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "researcher")
        workflow.add_edge("researcher", "analyzer")
        workflow.add_edge("analyzer", "synthesizer")
        workflow.add_edge("synthesizer", END)
        
        # Compile the graph
        app = workflow.compile()
        self.logger.info("LangGraph state machine built successfully")
        
        return app
    
    @retry_with_exponential_backoff(max_retries=3)
    def _node_planner(self, state: WorkflowState) -> WorkflowState:
        """
        Planner node: Break down research topic into questions.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with research plan
        """
        self.logger.info("Executing Planner node")
        start_time = datetime.utcnow()
        
        try:
            # Execute planner agent
            plan = self.planner.plan_research(
                topic=state.topic.topic,
                domains=state.topic.domains,
                depth=state.topic.depth,
                context=state.topic.context,
                session_id=state.session_id
            )
            
            # Update state
            state.plan = plan
            state.current_stage = "researching"
            state.updated_at = datetime.utcnow()
            
            # Track timing
            duration = (datetime.utcnow() - start_time).total_seconds()
            state.stage_timings["planning"] = duration
            
            self.logger.info(f"Planner completed in {duration:.1f}s")
            
            return state
        
        except Exception as e:
            self.logger.error(f"Planner node failed: {e}")
            state.errors.append({
                "stage": "planning",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            raise
    
    @retry_with_exponential_backoff(max_retries=2)
    def _node_researcher(self, state: WorkflowState) -> WorkflowState:
        """
        Researcher node: Execute research on questions.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with research findings
        """
        self.logger.info("Executing Researcher node")
        start_time = datetime.utcnow()
        
        try:
            # Prepare research questions
            questions = [q.question for q in state.plan.research_questions]
            keywords = state.plan.suggested_keywords
            
            # Execute researcher agent
            findings = self.researcher.conduct_research(
                topic=state.topic.topic,
                research_questions=questions,
                keywords=keywords,
                max_sources=state.topic.max_sources,
                session_id=state.session_id
            )
            
            # Update state
            state.findings = findings
            state.current_stage = "analyzing"
            state.updated_at = datetime.utcnow()
            
            # Track timing
            duration = (datetime.utcnow() - start_time).total_seconds()
            state.stage_timings["researching"] = duration
            
            self.logger.info(f"Researcher completed in {duration:.1f}s")
            
            return state
        
        except Exception as e:
            self.logger.error(f"Researcher node failed: {e}")
            state.errors.append({
                "stage": "researching",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            raise
    
    @retry_with_exponential_backoff(max_retries=2)
    def _node_analyzer(self, state: WorkflowState) -> WorkflowState:
        """
        Analyzer node: Analyze findings and extract insights.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with analysis
        """
        self.logger.info("Executing Analyzer node")
        start_time = datetime.utcnow()
        
        try:
            # Execute analyzer agent
            analysis = self.analyzer.analyze_findings(
                topic=state.topic.topic,
                findings=state.findings,
                session_id=state.session_id
            )
            
            # Update state
            state.analysis = analysis
            state.current_stage = "synthesizing"
            state.updated_at = datetime.utcnow()
            
            # Track timing
            duration = (datetime.utcnow() - start_time).total_seconds()
            state.stage_timings["analyzing"] = duration
            
            self.logger.info(f"Analyzer completed in {duration:.1f}s")
            
            return state
        
        except Exception as e:
            self.logger.error(f"Analyzer node failed: {e}")
            state.errors.append({
                "stage": "analyzing",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            raise
    
    @retry_with_exponential_backoff(max_retries=2)
    def _node_synthesizer(self, state: WorkflowState) -> WorkflowState:
        """
        Synthesizer node: Create final research report.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with final report
        """
        self.logger.info("Executing Synthesizer node")
        start_time = datetime.utcnow()
        
        try:
            # Execute synthesizer agent
            report = self.synthesizer.synthesize_report(
                topic=state.topic.topic,
                plan=state.plan,
                findings=state.findings,
                analysis=state.analysis,
                session_id=state.session_id
            )
            
            # Update state
            state.report = report
            state.current_stage = "completed"
            state.updated_at = datetime.utcnow()
            
            # Track timing
            duration = (datetime.utcnow() - start_time).total_seconds()
            state.stage_timings["synthesizing"] = duration
            
            self.logger.info(f"Synthesizer completed in {duration:.1f}s")
            
            return state
        
        except Exception as e:
            self.logger.error(f"Synthesizer node failed: {e}")
            state.errors.append({
                "stage": "synthesizing",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            raise
    
    def run_research(
        self,
        topic: str,
        domains: Optional[list] = None,
        depth: str = "standard",
        context: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> WorkflowState:
        """
        Run the complete research workflow.
        
        Args:
            topic: Research topic
            domains: Specific domains (optional)
            depth: Research depth (quick, standard, deep)
            context: Additional context
            session_id: Unique session ID. Generated if not provided.
            
        Returns:
            Final WorkflowState with complete research results
            
        Example:
            orchestrator = ResearchOrchestrator()
            state = orchestrator.run_research(
                topic="AI agents in 2025",
                depth="standard"
            )
            print(state.report.executive_summary)
        """
        # Generate session ID if not provided
        session_id = session_id or f"research-{uuid.uuid4().hex[:8]}"
        
        # Create initial state
        topic_obj = ResearchTopic(
            topic=topic,
            domains=domains,
            depth=depth,
            context=context
        )
        
        initial_state = WorkflowState(
            session_id=session_id,
            topic=topic_obj,
            current_stage="planning"
        )
        
        self.logger.info(f"Starting research workflow: {session_id}")
        self.logger.info(f"  Topic: {topic}")
        self.logger.info(f"  Depth: {depth}")
        
        # Execute the graph
        final_state = self.graph.invoke(initial_state)
        
        # Log final status
        total_time = sum(final_state.stage_timings.values())
        self.logger.info(f"Research workflow completed in {total_time:.1f}s")
        
        if final_state.errors:
            self.logger.warning(f"Workflow had {len(final_state.errors)} errors")
        
        return final_state
    
    def get_execution_summary(self, state: WorkflowState) -> dict:
        """
        Get a summary of the workflow execution.
        
        Args:
            state: Final workflow state
            
        Returns:
            Dictionary with execution summary
        """
        return {
            "session_id": state.session_id,
            "status": state.current_stage,
            "topic": state.topic.topic,
            "total_time_seconds": sum(state.stage_timings.values()),
            "stage_timings": state.stage_timings,
            "findings_count": len(state.findings.findings) if state.findings else 0,
            "insights_count": len(state.analysis.insights) if state.analysis else 0,
            "sources_count": len(state.report.sources) if state.report else 0,
            "errors": len(state.errors),
            "error_details": state.errors if state.errors else None,
        }


if __name__ == "__main__":
    # Quick test
    from config import settings
    print(f"Testing Orchestrator with LLM mode: {settings.llm_mode}")
    
    orchestrator = ResearchOrchestrator()
    
    state = orchestrator.run_research(
        topic="AI agents in 2025",
        depth="quick"
    )
    
    print("\n✓ Research workflow completed!")
    print("\nExecution Summary:")
    summary = orchestrator.get_execution_summary(state)
    for key, value in summary.items():
        if key != "error_details":
            print(f"  {key}: {value}")
    
    if state.report:
        print(f"\n✓ Final Report:")
        print(f"  Executive Summary: {state.report.executive_summary[:100]}...")
        print(f"  Main Findings: {len(state.report.main_findings)}")
        print(f"  Sources: {len(state.report.sources)}")
