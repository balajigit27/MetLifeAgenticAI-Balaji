"""
Checkpoint Manager: Handles persistence and resumable workflows.

Features:
- Save workflow state to SQLite database
- Resume interrupted research from last checkpoint
- Query research history
- Clean up old checkpoints
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from graph.state import WorkflowState
from config import settings
from utils.logger import logger


class CheckpointManager:
    """Manages workflow state persistence and resumption."""
    
    def __init__(self, db_path: str = None):
        """
        Initialize checkpoint manager.
        
        Args:
            db_path: Path to SQLite database. Defaults to settings.db_path
        """
        self.db_path = db_path or settings.db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        self.logger = logger
    
    def _init_database(self) -> None:
        """Initialize database schema."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create checkpoints table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    session_id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    current_stage TEXT NOT NULL,
                    state_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed BOOLEAN DEFAULT 0
                )
            """)
            
            # Create history table for tracking all workflows
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_history (
                    session_id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    depth TEXT,
                    status TEXT,
                    total_time_seconds REAL,
                    findings_count INTEGER,
                    errors_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            self.logger.debug("Database initialized")
        
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise
    
    def save_checkpoint(
        self,
        state: WorkflowState,
        completed: bool = False
    ) -> None:
        """
        Save workflow state checkpoint.
        
        Args:
            state: WorkflowState to save
            completed: Whether the workflow is complete
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Serialize state to JSON
            state_json = self._serialize_state(state)
            
            # Save checkpoint
            cursor.execute("""
                INSERT OR REPLACE INTO checkpoints
                (session_id, topic, current_stage, state_json, updated_at, completed)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                state.session_id,
                state.topic.topic,
                state.current_stage,
                state_json,
                datetime.utcnow().isoformat(),
                completed
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.debug(
                f"Checkpoint saved: {state.session_id} at stage {state.current_stage}"
            )
        
        except sqlite3.Error as e:
            self.logger.error(f"Failed to save checkpoint: {e}")
            raise
    
    def load_checkpoint(self, session_id: str) -> Optional[WorkflowState]:
        """
        Load a saved workflow checkpoint.
        
        Args:
            session_id: Session ID to load
            
        Returns:
            WorkflowState if found, None otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT state_json FROM checkpoints WHERE session_id = ?
            """, (session_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                state_json = result[0]
                state = self._deserialize_state(state_json)
                self.logger.info(f"Checkpoint loaded: {session_id}")
                return state
            else:
                self.logger.warning(f"Checkpoint not found: {session_id}")
                return None
        
        except sqlite3.Error as e:
            self.logger.error(f"Failed to load checkpoint: {e}")
            raise
    
    def save_workflow_history(
        self,
        session_id: str,
        topic: str,
        depth: str,
        status: str,
        total_time: float,
        findings_count: int,
        errors_count: int
    ) -> None:
        """
        Save workflow execution to history.
        
        Args:
            session_id: Session ID
            topic: Research topic
            depth: Research depth
            status: Final status (completed, failed, etc.)
            total_time: Total execution time in seconds
            findings_count: Number of findings extracted
            errors_count: Number of errors encountered
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO workflow_history
                (session_id, topic, depth, status, total_time_seconds,
                 findings_count, errors_count, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                topic,
                depth,
                status,
                total_time,
                findings_count,
                errors_count,
                datetime.utcnow().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.debug(f"Workflow history saved: {session_id}")
        
        except sqlite3.Error as e:
            self.logger.error(f"Failed to save workflow history: {e}")
            raise
    
    def get_workflow_history(
        self,
        limit: int = 10,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get recent workflow history.
        
        Args:
            limit: Maximum number of records to return
            days: Only return workflows from last N days
            
        Returns:
            List of workflow history records
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = (
                datetime.utcnow() - timedelta(days=days)
            ).isoformat()
            
            cursor.execute("""
                SELECT session_id, topic, depth, status, total_time_seconds,
                       findings_count, errors_count, completed_at
                FROM workflow_history
                WHERE completed_at > ?
                ORDER BY completed_at DESC
                LIMIT ?
            """, (cutoff_date, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            history = [
                {
                    "session_id": row[0],
                    "topic": row[1],
                    "depth": row[2],
                    "status": row[3],
                    "total_time_seconds": row[4],
                    "findings_count": row[5],
                    "errors_count": row[6],
                    "completed_at": row[7]
                }
                for row in rows
            ]
            
            return history
        
        except sqlite3.Error as e:
            self.logger.error(f"Failed to retrieve workflow history: {e}")
            raise
    
    def cleanup_old_checkpoints(self, days: int = 7) -> int:
        """
        Delete old completed checkpoints.
        
        Args:
            days: Delete checkpoints older than N days
            
        Returns:
            Number of checkpoints deleted
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = (
                datetime.utcnow() - timedelta(days=days)
            ).isoformat()
            
            cursor.execute("""
                DELETE FROM checkpoints
                WHERE completed = 1 AND updated_at < ?
            """, (cutoff_date,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            self.logger.info(f"Cleaned up {deleted_count} old checkpoints")
            
            return deleted_count
        
        except sqlite3.Error as e:
            self.logger.error(f"Cleanup failed: {e}")
            raise
    
    def _serialize_state(self, state: WorkflowState) -> str:
        """Convert WorkflowState to JSON string."""
        # For now, save only essential state
        # In production, use custom encoder for Pydantic models
        state_dict = {
            "session_id": state.session_id,
            "topic": state.topic.dict(),
            "current_stage": state.current_stage,
            "plan": state.plan.dict() if state.plan else None,
            "findings": state.findings.dict() if state.findings else None,
            "analysis": state.analysis.dict() if state.analysis else None,
            "report": state.report.dict() if state.report else None,
            "created_at": state.created_at.isoformat(),
            "updated_at": state.updated_at.isoformat(),
            "errors": state.errors,
            "stage_timings": state.stage_timings
        }
        
        return json.dumps(state_dict)
    
    def _deserialize_state(self, state_json: str) -> WorkflowState:
        """Convert JSON string back to WorkflowState."""
        import dateutil.parser
        
        state_dict = json.loads(state_json)
        
        # Reconstruct ResearchTopic
        from graph.state import ResearchTopic
        topic = ResearchTopic(**state_dict["topic"])
        
        # Create new WorkflowState with loaded data
        state = WorkflowState(
            session_id=state_dict["session_id"],
            topic=topic,
            current_stage=state_dict["current_stage"],
            created_at=dateutil.parser.parse(state_dict["created_at"]),
            updated_at=dateutil.parser.parse(state_dict["updated_at"]),
            errors=state_dict.get("errors", []),
            stage_timings=state_dict.get("stage_timings", {})
        )
        
        # Restore nested states if they exist
        if state_dict.get("plan"):
            from graph.state import ResearchPlan
            state.plan = ResearchPlan(**state_dict["plan"])
        
        if state_dict.get("findings"):
            from graph.state import ResearchFindings
            state.findings = ResearchFindings(**state_dict["findings"])
        
        if state_dict.get("analysis"):
            from graph.state import AnalysisResult
            state.analysis = AnalysisResult(**state_dict["analysis"])
        
        if state_dict.get("report"):
            from graph.state import ResearchReport
            state.report = ResearchReport(**state_dict["report"])
        
        return state


if __name__ == "__main__":
    # Quick test
    manager = CheckpointManager()
    print("✓ Checkpoint manager initialized")
    
    # Create sample state
    from graph.state import WorkflowState, ResearchTopic
    topic = ResearchTopic(topic="Test topic", depth="quick")
    state = WorkflowState(session_id="test-123", topic=topic)
    
    # Save checkpoint
    manager.save_checkpoint(state, completed=False)
    print("✓ Checkpoint saved")
    
    # Load checkpoint
    loaded_state = manager.load_checkpoint("test-123")
    if loaded_state:
        print(f"✓ Checkpoint loaded: {loaded_state.session_id}")
    
    # Get history
    history = manager.get_workflow_history(limit=5)
    print(f"✓ Retrieved {len(history)} history records")
