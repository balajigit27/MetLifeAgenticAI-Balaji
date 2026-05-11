"""
Main CLI entry point for the Agentic Research Orchestrator.

This module provides a command-line interface for running research workflows.

Usage:
    python main.py --topic "AI agents in 2025" --depth standard --llm cloud
    python main.py --topic "Climate tech" --depth quick --llm local
    python main.py --resume task-20250511-143022
    python main.py --info
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from argparse import ArgumentParser, RawDescriptionHelpFormatter

# Project imports
from config import settings, validate_settings, get_llm_info
from graph.orchestrator import ResearchOrchestrator
from graph.state import WorkflowState
from persistence.checkpoint_manager import CheckpointManager
from utils.logger import setup_logger, LogContext
from utils.metrics import MetricsCollector


# Setup logger
logger = setup_logger(__name__)


def create_parser() -> ArgumentParser:
    """Create CLI argument parser."""
    parser = ArgumentParser(
        description="Agentic Research Orchestrator - Multi-agent AI research system",
        formatter_class=RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick research with local Ollama
  python main.py --topic "AI agents" --depth quick --llm local
  
  # Standard research with OpenAI
  python main.py --topic "Climate tech startups" --depth standard --llm cloud
  
  # Deep research
  python main.py --topic "Quantum computing" --depth deep --llm cloud
  
  # Resume interrupted research
  python main.py --resume task-20250511-143022
  
  # Show configuration
  python main.py --info

Research Depths:
  quick    - 1-2 questions, 3-5 sources (~2-5 minutes)
  standard - 3-5 questions, 5-10 sources (~5-15 minutes) [default]
  deep     - 5+ questions, 10+ sources (~15-30 minutes)
        """
    )
    
    # Research options
    parser.add_argument(
        "--topic",
        type=str,
        help="Research topic (e.g., 'AI agents in 2025')"
    )
    
    parser.add_argument(
        "--depth",
        choices=["quick", "standard", "deep"],
        default="standard",
        help="Research depth (default: standard)"
    )
    
    parser.add_argument(
        "--domains",
        type=str,
        help="Comma-separated domains to focus on (e.g., 'AI,ethics,business')"
    )
    
    parser.add_argument(
        "--context",
        type=str,
        help="Additional context for research"
    )
    
    # LLM options
    parser.add_argument(
        "--llm",
        choices=["cloud", "local"],
        help="LLM provider (overrides LLM_MODE from .env)"
    )
    
    # Output options
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: reports/[topic]_[timestamp].json)"
    )
    
    parser.add_argument(
        "--format",
        choices=["json", "text", "both"],
        default="both",
        help="Output format (default: both)"
    )
    
    # Workflow control
    parser.add_argument(
        "--resume",
        type=str,
        help="Resume research from saved checkpoint (session ID)"
    )
    
    parser.add_argument(
        "--session-id",
        type=str,
        help="Custom session ID (default: auto-generated)"
    )
    
    # System options
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show configuration information and exit"
    )
    
    parser.add_argument(
        "--history",
        action="store_true",
        help="Show recent research history"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save results or checkpoints"
    )
    
    return parser


def show_info() -> None:
    """Show configuration information."""
    print("\n" + "=" * 70)
    print("AGENTIC RESEARCH ORCHESTRATOR - CONFIGURATION")
    print("=" * 70)
    
    print(f"\n📋 LLM Configuration:")
    llm_info = get_llm_info()
    for key, value in llm_info.items():
        print(f"   {key:.<30} {value}")
    
    print(f"\n🔧 System Configuration:")
    config_items = [
        ("Log Level", settings.log_level),
        ("Research Directory", settings.reports_dir),
        ("Database Path", settings.db_path),
        ("Checkpoints Enabled", settings.enable_checkpoints),
        ("JSON Logging", settings.json_logging),
        ("LangSmith Enabled", settings.langsmith_enabled),
    ]
    for label, value in config_items:
        print(f"   {label:.<30} {value}")
    
    print(f"\n📊 Research Depths:")
    depths = {
        "quick": "1-2 questions, 3-5 sources (~2-5 min)",
        "standard": "3-5 questions, 5-10 sources (~5-15 min)",
        "deep": "5+ questions, 10+ sources (~15-30 min)"
    }
    for depth, desc in depths.items():
        print(f"   {depth:.<30} {desc}")
    
    print("\n" + "=" * 70 + "\n")


def show_history() -> None:
    """Show recent research history."""
    try:
        manager = CheckpointManager()
        history = manager.get_workflow_history(limit=10)
        
        if not history:
            print("No research history found.")
            return
        
        print("\n" + "=" * 70)
        print("RECENT RESEARCH HISTORY")
        print("=" * 70)
        print(f"{'Session ID':<20} {'Topic':<25} {'Depth':<10} {'Status':<12} {'Time':<8}")
        print("-" * 70)
        
        for record in history:
            topic = record["topic"][:20] + "..." if len(record["topic"]) > 20 else record["topic"]
            time_str = f"{record['total_time_seconds']:.1f}s" if record["total_time_seconds"] else "N/A"
            print(f"{record['session_id']:<20} {topic:<25} {record['depth']:<10} {record['status']:<12} {time_str:<8}")
        
        print("=" * 70 + "\n")
    
    except Exception as e:
        logger.error(f"Failed to show history: {e}")


def run_research(args) -> WorkflowState:
    """
    Execute research workflow.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Final workflow state
    """
    # Override LLM mode if specified
    if args.llm:
        import os
        os.environ["LLM_MODE"] = args.llm
    
    # Parse domains if provided
    domains = None
    if args.domains:
        domains = [d.strip() for d in args.domains.split(",")]
    
    # Create orchestrator
    logger.info("Initializing Research Orchestrator")
    orchestrator = ResearchOrchestrator()
    
    # Run research
    logger.info(f"Starting research: {args.topic}")
    state = orchestrator.run_research(
        topic=args.topic,
        domains=domains,
        depth=args.depth,
        context=args.context,
        session_id=args.session_id
    )
    
    return state, orchestrator


def save_results(
    state: WorkflowState,
    output_path: Optional[str] = None,
    format: str = "both"
) -> None:
    """
    Save research results to file.
    
    Args:
        state: Workflow state with results
        output_path: Output file path
        format: Output format (json, text, both)
    """
    try:
        # Generate output path if not specified
        if not output_path:
            topic_slug = state.topic.topic.lower().replace(" ", "_")[:20]
            timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
            output_path = f"reports/{topic_slug}_{timestamp}"
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save JSON format
        if format in ["json", "both"]:
            json_path = f"{output_path}.json"
            with open(json_path, "w") as f:
                # Convert state to dict for JSON serialization
                data = {
                    "session_id": state.session_id,
                    "topic": state.topic.topic,
                    "depth": state.topic.depth,
                    "current_stage": state.current_stage,
                    "report": state.report.dict() if state.report else None,
                    "metadata": {
                        "created_at": state.created_at.isoformat(),
                        "updated_at": state.updated_at.isoformat(),
                        "total_time_seconds": sum(state.stage_timings.values()),
                        "stage_timings": state.stage_timings,
                        "errors": len(state.errors)
                    }
                }
                json.dump(data, f, indent=2)
            logger.info(f"JSON report saved: {json_path}")
        
        # Save text format
        if format in ["text", "both"]:
            text_path = f"{output_path}.txt"
            if state.report:
                from agents.synthesizer import SynthesizerAgent
                synthesizer = SynthesizerAgent()
                text_content = synthesizer.format_report(state.report)
            else:
                text_content = "Research incomplete - no report generated."
            
            with open(text_path, "w") as f:
                f.write(text_content)
            logger.info(f"Text report saved: {text_path}")
    
    except Exception as e:
        logger.error(f"Failed to save results: {e}")


def print_results(state: WorkflowState) -> None:
    """Print research results to console."""
    print("\n" + "=" * 70)
    print("RESEARCH RESULTS")
    print("=" * 70)
    
    # Execution summary
    print(f"\n📊 Execution Summary:")
    print(f"   Session ID:........... {state.session_id}")
    print(f"   Topic:................ {state.topic.topic}")
    print(f"   Depth:................ {state.topic.depth}")
    print(f"   Status:............... {state.current_stage}")
    print(f"   Total Time:........... {sum(state.stage_timings.values()):.1f}s")
    
    # Stage timings
    print(f"\n⏱️  Stage Timings:")
    for stage, timing in state.stage_timings.items():
        print(f"   {stage:.<20} {timing:.1f}s")
    
    # Report
    if state.report:
        print(f"\n📋 Report:")
        print(f"   Title:............... {state.report.topic}")
        print(f"   Executive Summary:... {state.report.executive_summary[:100]}...")
        print(f"   Main Findings:....... {len(state.report.main_findings)}")
        print(f"   Sources:............. {len(state.report.sources)}")
        print(f"   Limitations:......... {len(state.report.limitations)}")
        print(f"   Recommendations:.... {len(state.report.recommendations)}")
    
    # Errors
    if state.errors:
        print(f"\n⚠️  Errors ({len(state.errors)}):")
        for error in state.errors:
            print(f"   - {error['stage']}: {error['error'][:50]}...")
    else:
        print(f"\n✅ No errors encountered")
    
    print("\n" + "=" * 70 + "\n")


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # Show info and exit
        if args.info:
            show_info()
            return 0
        
        # Show history and exit
        if args.history:
            show_history()
            return 0
        
        # Validate settings
        validate_settings()
        
        # Resume from checkpoint
        if args.resume:
            logger.info(f"Resuming research from checkpoint: {args.resume}")
            manager = CheckpointManager()
            state = manager.load_checkpoint(args.resume)
            
            if state is None:
                logger.error(f"Checkpoint not found: {args.resume}")
                return 1
            
            print_results(state)
            return 0
        
        # Run new research
        if not args.topic:
            parser.print_help()
            print("\n❌ Error: --topic is required for new research")
            return 1
        
        task_id = f"research-{args.session_id}" if args.session_id else "research"
        
        with LogContext(logger, task_id, topic=args.topic, depth=args.depth):
            # Run research
            state, orchestrator = run_research(args)
            
            # Print results
            print_results(state)
            
            # Save results
            if not args.no_save:
                save_results(state, args.output, args.format)
                
                # Save checkpoint
                if settings.enable_checkpoints:
                    manager = CheckpointManager()
                    manager.save_checkpoint(state, completed=True)
                    manager.save_workflow_history(
                        session_id=state.session_id,
                        topic=state.topic.topic,
                        depth=state.topic.depth,
                        status=state.current_stage,
                        total_time=sum(state.stage_timings.values()),
                        findings_count=len(state.findings.findings) if state.findings else 0,
                        errors_count=len(state.errors)
                    )
                    logger.info(f"Workflow saved to database")
            
            # Return exit code
            return 0 if len(state.errors) == 0 else 1
    
    except KeyboardInterrupt:
        logger.info("Research interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
