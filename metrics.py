"""
Metrics and observability utilities.

Features:
- Performance metrics collection
- LangSmith integration (optional)
- Structured logging integration
- Error tracking
"""

from datetime import datetime
from typing import Dict, Any, Optional
from utils.logger import logger
from config import settings


class MetricsCollector:
    """Collect and report workflow metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.logger = logger
        self.metrics = {}
    
    def record_stage_execution(
        self,
        stage_name: str,
        duration_seconds: float,
        success: bool,
        error_message: Optional[str] = None,
        **additional_metrics
    ) -> None:
        """
        Record execution metrics for a stage.
        
        Args:
            stage_name: Name of the stage (planner, researcher, etc.)
            duration_seconds: Execution time
            success: Whether execution was successful
            error_message: Error message if failed
            **additional_metrics: Additional metrics to record
        """
        metric_key = f"{stage_name}_{datetime.utcnow().timestamp()}"
        
        self.metrics[metric_key] = {
            "stage": stage_name,
            "duration_seconds": duration_seconds,
            "success": success,
            "error": error_message,
            "timestamp": datetime.utcnow().isoformat(),
            **additional_metrics
        }
        
        self.logger.debug(
            f"Recorded metrics for {stage_name}: {duration_seconds:.2f}s, "
            f"success={success}"
        )
    
    def record_findings(
        self,
        findings_count: int,
        sources_checked: int,
        errors: int,
        **metadata
    ) -> None:
        """
        Record research findings metrics.
        
        Args:
            findings_count: Number of findings extracted
            sources_checked: Number of sources checked
            errors: Number of errors encountered
            **metadata: Additional metadata
        """
        self.logger.info(
            f"Research metrics: {findings_count} findings from {sources_checked} "
            f"sources with {errors} errors"
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get metrics summary.
        
        Returns:
            Dictionary with aggregated metrics
        """
        if not self.metrics:
            return {}
        
        durations = [
            m["duration_seconds"]
            for m in self.metrics.values()
            if m.get("duration_seconds")
        ]
        
        success_count = sum(1 for m in self.metrics.values() if m.get("success"))
        error_count = len(self.metrics) - success_count
        
        return {
            "total_stages": len(self.metrics),
            "successful": success_count,
            "failed": error_count,
            "total_time_seconds": sum(durations),
            "avg_stage_time_seconds": sum(durations) / len(durations) if durations else 0,
            "min_stage_time_seconds": min(durations) if durations else 0,
            "max_stage_time_seconds": max(durations) if durations else 0,
        }


class LangSmithTracer:
    """Optional LangSmith integration for observability."""
    
    def __init__(self):
        """Initialize LangSmith tracer."""
        self.logger = logger
        self.enabled = settings.langsmith_enabled
        
        if self.enabled:
            try:
                import langsmith
                self.client = langsmith.Client(
                    api_key=settings.langsmith_api_key
                )
                self.logger.info("LangSmith tracer enabled")
            except Exception as e:
                self.logger.warning(f"Failed to initialize LangSmith: {e}")
                self.enabled = False
    
    def log_run(
        self,
        name: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        run_type: str = "chain",
        error: Optional[str] = None,
        duration_seconds: Optional[float] = None,
    ) -> None:
        """
        Log a run to LangSmith.
        
        Args:
            name: Name of the run
            inputs: Input data
            outputs: Output data
            run_type: Type of run (chain, agent, llm, tool)
            error: Error message if applicable
            duration_seconds: Duration of execution
        """
        if not self.enabled:
            return
        
        try:
            self.logger.debug(f"Logging to LangSmith: {name}")
            # In production, use:
            # with self.client.trace_as_chain_run(name, inputs=inputs, run_type=run_type):
            #     # ... perform work ...
            #     return outputs
        
        except Exception as e:
            self.logger.warning(f"Failed to log to LangSmith: {e}")


class PerformanceBenchmark:
    """Track performance benchmarks."""
    
    def __init__(self):
        """Initialize benchmark tracker."""
        self.logger = logger
        self.benchmarks = {}
    
    def record_benchmark(
        self,
        benchmark_name: str,
        duration_seconds: float,
        success: bool,
    ) -> None:
        """
        Record a performance benchmark.
        
        Args:
            benchmark_name: Name of the benchmark
            duration_seconds: Execution time
            success: Whether execution was successful
        """
        if benchmark_name not in self.benchmarks:
            self.benchmarks[benchmark_name] = []
        
        self.benchmarks[benchmark_name].append({
            "duration": duration_seconds,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        self.logger.debug(
            f"Recorded benchmark {benchmark_name}: {duration_seconds:.2f}s"
        )
    
    def get_benchmark_stats(self, benchmark_name: str) -> Dict[str, float]:
        """
        Get statistics for a benchmark.
        
        Args:
            benchmark_name: Name of the benchmark
            
        Returns:
            Dictionary with statistics
        """
        if benchmark_name not in self.benchmarks:
            return {}
        
        records = self.benchmarks[benchmark_name]
        durations = [r["duration"] for r in records]
        
        return {
            "count": len(records),
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "success_rate": (
                sum(1 for r in records if r["success"]) / len(records)
                if records else 0
            )
        }


if __name__ == "__main__":
    # Quick test
    metrics = MetricsCollector()
    metrics.record_stage_execution("planner", 2.5, True)
    metrics.record_stage_execution("researcher", 5.2, True)
    metrics.record_stage_execution("analyzer", 1.8, True)
    
    print("✓ Metrics recorded")
    summary = metrics.get_summary()
    print(f"Summary: {summary}")
    
    # Test benchmarks
    benchmark = PerformanceBenchmark()
    benchmark.record_benchmark("quick_research", 45.0, True)
    benchmark.record_benchmark("quick_research", 48.0, True)
    benchmark.record_benchmark("quick_research", 46.5, True)
    
    stats = benchmark.get_benchmark_stats("quick_research")
    print(f"Benchmark stats: {stats}")
