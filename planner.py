"""
Planner Agent: Breaks down research topic into specific questions.

The Planner agent:
1. Takes a high-level research topic
2. Analyzes it to identify key dimensions
3. Creates 3-5 specific research questions
4. Identifies information gaps
5. Suggests relevant keywords for searching

Output: ResearchPlan with structured questions and gaps
"""

from typing import Optional
from config import get_llm
from graph.state import ResearchPlan, ResearchQuestion
from utils.logger import logger, LogContext


PLANNER_PROMPT = """You are an expert research planning agent. Your task is to analyze a research topic and create a comprehensive research plan.

Given the research topic, you should:
1. Identify key dimensions and aspects of the topic
2. Create 3-5 specific research questions that need to be answered
3. Identify information gaps that need to be filled
4. Suggest relevant keywords for searching

Topic: {topic}
Domains: {domains}
Depth: {depth}
Context: {context}

Respond in JSON format with this structure:
{{
    "research_questions": [
        {{"question": "...", "priority": 1, "reasoning": "..."}},
        ...
    ],
    "information_gaps": ["gap1", "gap2", ...],
    "suggested_keywords": ["keyword1", "keyword2", ...],
    "plan_summary": "Brief summary of the research plan"
}}

Make sure to:
- Prioritize questions by importance (1=high, 3=low)
- Cover different aspects of the topic
- Identify what is NOT known and needs investigation
- Suggest search terms that will find relevant information
"""


class PlannerAgent:
    """
    Planner Agent: Breaks down research topics into structured questions.
    """
    
    def __init__(self, llm=None):
        """
        Initialize Planner Agent.
        
        Args:
            llm: LangChain LLM instance. If None, uses default from config.
        """
        self.llm = llm or get_llm()
        self.logger = logger
    
    def plan_research(
        self,
        topic: str,
        domains: Optional[list] = None,
        depth: str = "standard",
        context: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> ResearchPlan:
        """
        Create a research plan for the given topic.
        
        Args:
            topic: Research topic
            domains: Specific domains to focus on
            depth: Research depth (quick, standard, deep)
            context: Additional context
            session_id: Session ID for logging
            
        Returns:
            ResearchPlan with questions and analysis
            
        Example:
            planner = PlannerAgent()
            plan = planner.plan_research("AI agents in 2025")
            print(f"Questions: {len(plan.research_questions)}")
        """
        task_id = f"planner-{session_id}" if session_id else "planner-task"
        
        with LogContext(self.logger, task_id, stage="planning"):
            # Format the prompt
            domains_str = ", ".join(domains) if domains else "General"
            context_str = context or "No additional context"
            
            prompt = PLANNER_PROMPT.format(
                topic=topic,
                domains=domains_str,
                depth=depth,
                context=context_str,
            )
            
            # Call LLM
            self.logger.debug(f"Calling LLM to plan research for: {topic}")
            response = self.llm.invoke(prompt)
            
            # Parse response
            plan_data = self._parse_response(response.content)
            
            # Create ResearchPlan object
            research_questions = [
                ResearchQuestion(**q) for q in plan_data.get("research_questions", [])
            ]
            
            plan = ResearchPlan(
                topic=topic,
                research_questions=research_questions,
                information_gaps=plan_data.get("information_gaps", []),
                suggested_keywords=plan_data.get("suggested_keywords", []),
                plan_summary=plan_data.get("plan_summary", ""),
            )
            
            self.logger.info(
                f"Created research plan with {len(plan.research_questions)} questions"
            )
            
            return plan
    
    def _parse_response(self, response_text: str) -> dict:
        """
        Parse LLM response into structured data.
        
        Args:
            response_text: Raw LLM response
            
        Returns:
            Parsed dictionary
        """
        import json
        
        # Extract JSON from response
        try:
            # Try direct JSON parsing
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Fallback to default structure
            self.logger.warning("Failed to parse LLM response, using defaults")
            return {
                "research_questions": [
                    {
                        "question": "What are the main aspects of this topic?",
                        "priority": 1,
                        "reasoning": "Fundamental understanding needed"
                    }
                ],
                "information_gaps": ["Current state of the field"],
                "suggested_keywords": ["research", "analysis", "current"],
                "plan_summary": "Basic research plan"
            }


if __name__ == "__main__":
    # Quick test
    from config import settings
    print(f"Testing Planner Agent with LLM mode: {settings.llm_mode}")
    
    planner = PlannerAgent()
    plan = planner.plan_research(
        topic="AI agents in 2025",
        depth="standard"
    )
    
    print(f"✓ Created plan with {len(plan.research_questions)} questions:")
    for q in plan.research_questions:
        print(f"  - {q.question}")
