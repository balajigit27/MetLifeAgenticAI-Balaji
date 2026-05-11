# Architecture & Design Documentation

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                   AGENTIC RESEARCH ORCHESTRATOR                     │
│                    Industrial-Grade Production System               │
└─────────────────────────────────────────────────────────────────────┘

                           USER (CLI or API)
                                  ↓
                          ┌────────────────┐
                          │   main.py      │  ← CLI Entry Point
                          │  (argparse)    │
                          └────────┬───────┘
                                   ↓
                    ┌──────────────────────────────┐
                    │  Configuration Management    │
                    │  • LLM Mode Selection        │
                    │  • Environment Variables     │
                    │  • Logging Setup            │
                    └──────────┬───────────────────┘
                               ↓
                    ┌──────────────────────────────┐
                    │  ResearchOrchestrator        │
                    │  (LangGraph State Machine)   │
                    └──────────┬───────────────────┘
                               ↓
        ┌──────────────────────┼──────────────────────┐
        ↓                      ↓                      ↓
   ┌─────────┐          ┌─────────┐          ┌─────────────┐
   │ Planner │          │Researcher│        │  Analyzer   │
   │ Agent   │          │ Agent    │        │   Agent     │
   │         │          │          │        │             │
   │ • Break │          │ • Search │        │ • Evaluate  │
   │   topic │          │ • Fetch  │        │ • Patterns  │
   │ • Find  │          │ • Extract│        │ • Quality   │
   │  Qs     │          │  facts   │        │ • Insights  │
   └─────┬───┘          └────┬─────┘        └──────┬──────┘
         │                   │                      │
         └───────────────────┼──────────────────────┘
                             ↓
                      ┌──────────────┐
                      │ Synthesizer  │
                      │   Agent      │
                      │              │
                      │ • Combine    │
                      │ • Format     │
                      │ • Citations  │
                      └──────┬───────┘
                             ↓
              ┌──────────────────────────────┐
              │  Persistence Layer           │
              │  • Checkpoints (SQLite)      │
              │  • Workflow History          │
              │  • State Recovery            │
              └──────────┬───────────────────┘
                         ↓
           ┌─────────────────────────────┐
           │   Output Formats            │
           │ • JSON (Structured)         │
           │ • Text (Formatted Report)   │
           │ • Database Records          │
           └─────────────────────────────┘
```

---

## Data Flow Architecture

```
                    RESEARCH WORKFLOW STATE MACHINE
                    
WorkflowState (Pydantic Model)
├── session_id: str                          ← Unique identifier
├── topic: ResearchTopic                     ← Input research topic
│   ├── topic: str
│   ├── domains: List[str]
│   ├── depth: str (quick|standard|deep)
│   └── context: str
│
├── plan: ResearchPlan                       ← Planner output
│   ├── research_questions: List[ResearchQuestion]
│   ├── information_gaps: List[str]
│   ├── suggested_keywords: List[str]
│   └── plan_summary: str
│
├── findings: ResearchFindings                ← Researcher output
│   ├── findings: List[Finding]
│   │   ├── fact: str
│   │   ├── source_title: str
│   │   ├── source_url: str
│   │   ├── relevance_score: float (0-1)
│   │   └── confidence: float (0-1)
│   ├── total_sources_checked: int
│   ├── sources_with_errors: List[str]
│   └── research_summary: str
│
├── analysis: AnalysisResult                  ← Analyzer output
│   ├── insights: List[AnalysisInsight]
│   │   ├── insight: str
│   │   ├── insight_type: str
│   │   ├── related_findings: List[int]
│   │   └── confidence: float (0-1)
│   ├── contradictions_found: List[Dict]
│   ├── quality_assessment: Dict[str, float]
│   └── analysis_summary: str
│
├── report: ResearchReport                   ← Synthesizer output
│   ├── executive_summary: str
│   ├── main_findings: List[str]
│   ├── detailed_analysis: str
│   ├── citations: List[Citation]
│   ├── sources: List[Dict]
│   ├── limitations: List[str]
│   ├── recommendations: List[str]
│   └── report_metadata: Dict
│
├── current_stage: str                       ← Workflow progress
│   (planning|researching|analyzing|synthesizing|completed)
│
├── errors: List[Dict]                       ← Error tracking
├── stage_timings: Dict[str, float]          ← Performance metrics
└── created_at, updated_at: datetime         ← Timestamps
```

---

## Agent Architecture

### Each Agent Pattern

```
┌─────────────────────────────────────┐
│         Agent Class                 │
│                                     │
│ 1. __init__(llm)                    │
│    └─ Receives LLM instance         │
│                                     │
│ 2. main_method(inputs)              │
│    ├─ Format prompt with inputs     │
│    ├─ Call LLM.invoke(prompt)       │
│    ├─ Parse JSON response           │
│    ├─ Validate with Pydantic        │
│    ├─ Log results                   │
│    └─ Return structured output      │
│                                     │
│ 3. Helper methods                   │
│    ├─ _parse_response()             │
│    ├─ _format_prompt()              │
│    └─ error_handling()              │
└─────────────────────────────────────┘
```

### Agent Execution Flow

```
Input Data
    ↓
Format Prompt Template
    ↓
Call LLM (Cloud or Local)
    ↓
Receive Text Response
    ↓
Extract JSON (with regex fallback)
    ↓
Parse into Pydantic Model
    ↓
Validate Schema
    ↓
Log Success/Error
    ↓
Return Structured Output
```

---

## LLM Integration Layer

### Dual-Mode LLM Support

```
                    get_llm(mode: str)
                           ↓
                    ┌──────────────┐
                    │ Check Mode   │
                    └──┬───────┬───┘
                       ↓       ↓
                    CLOUD    LOCAL
                       ↓       ↓
                  OpenAI    Ollama
                   API      Server
                    ↓       ↓
                ChatOpenAI ChatOllama
                    ↓       ↓
                   LLM Instance
                    (LangChain)
```

### Configuration Strategy

```
.env Configuration
    ↓
settings = Settings()  (Pydantic)
    ↓
    ├─ LLM_MODE (cloud|local)
    ├─ OPENAI_API_KEY
    ├─ OLLAMA_BASE_URL
    └─ Model parameters
    ↓
get_llm() factory
    ├─ If cloud → ChatOpenAI(api_key, model, ...)
    └─ If local → ChatOllama(base_url, model, ...)
    ↓
Unified LLM Interface
    (both have .invoke(prompt) method)
```

---

## State Machine (LangGraph)

```
                    StateGraph(WorkflowState)
                           ↓
    ┌──────────────────────┼──────────────────────┐
    ↓                      ↓                      ↓
entry_point          node definitions        edges
    ↓                      ↓                      ↓
"planner"        add_node("planner",      add_edge()
                 _node_planner)
                 add_node("researcher",    ├─ planner → researcher
                 _node_researcher)        ├─ researcher → analyzer
                 add_node("analyzer",     ├─ analyzer → synthesizer
                 _node_analyzer)          └─ synthesizer → END
                 add_node("synthesizer",
                 _node_synthesizer)
    ↓
   graph = workflow.compile()
    ↓
   final_state = graph.invoke(initial_state)
```

---

## Error Handling & Retry Strategy

```
┌──────────────────────────────────────────┐
│   @retry_with_exponential_backoff()      │
│   def node_function(state):              │
└──────────────────────────────────────────┘
                    ↓
    ┌───────────────┴───────────────┐
    ↓ (Attempt 1)                   ↓ (If fails)
  Try Execute                    Wait 1s
    │                               ↓
    ├─ Success → Return          Try Again (2s wait)
    │                               ↓
    ├─ Fails → Catch Exception   Try Again (4s wait)
    │                               ↓
    └─ Continue...               Exponential backoff
                                 (max 30s between retries)
                                    ↓
                            Max 3 attempts
                                    ↓
                            If all fail → Log Error
                                    ↓
                            Propagate Exception
```

---

## Persistence Architecture

```
┌─────────────────────────────────────┐
│     Checkpoint Manager              │
│     (SQLite Database)               │
└─────────────────────────────────────┘
           ↓
    ┌──────────────────┐
    │  checkpoints     │  (In-progress workflows)
    │  ─────────────   │
    │  session_id (PK) │
    │  topic           │
    │  current_stage   │
    │  state_json      │
    │  created_at      │
    │  updated_at      │
    │  completed       │
    └──────────────────┘
           ↓
    ┌──────────────────┐
    │ workflow_history │  (Completed workflows)
    │ ─────────────── │
    │ session_id (PK)  │
    │ topic            │
    │ depth            │
    │ status           │
    │ total_time_sec   │
    │ findings_count   │
    │ errors_count     │
    │ completed_at     │
    └──────────────────┘

Flow:
    Run Research
         ↓
    Save Checkpoint (after each stage)
         ↓
    If Interrupted:
      Load Checkpoint → Resume from last stage
         ↓
    If Completed:
      Mark as completed → Move to history
         ↓
    Query History:
      get_workflow_history(limit=10, days=30)
```

---

## Production Features Architecture

### Logging

```
┌────────────────────────────────┐
│   setup_logger(__name__)       │
└────────────┬───────────────────┘
             ↓
    ┌────────────────────┐
    │  Formatters        │
    │  ──────────────    │
    │  - JSONFormatter   │ ← Production
    │  - ColoredFormatter│ ← Development
    └────────────────────┘
             ↓
    ┌────────────────────┐
    │  Handlers          │
    │  ──────────────    │
    │  - Console         │
    │  - File (optional) │
    └────────────────────┘
             ↓
    Structured Logs
    (Metrics: task_id, duration, success status)
```

### Metrics Collection

```
┌─────────────────────────────┐
│  MetricsCollector           │
│                             │
│ record_stage_execution()    │
│   ├─ Stage name             │
│   ├─ Duration (seconds)     │
│   ├─ Success flag           │
│   ├─ Error message          │
│   └─ Custom metrics         │
│                             │
│ get_summary()               │
│   ├─ Total stages           │
│   ├─ Success/failed count   │
│   ├─ Total time             │
│   ├─ Average stage time     │
│   └─ Min/max times          │
└─────────────────────────────┘
         ↓
  Available for:
  - Console display
  - LangSmith tracking
  - Monitoring dashboards
  - Performance analysis
```

---

## File Organization

```
agentic-research-orchestrator/
│
├── main.py                      ← CLI Entry Point
├── config.py                    ← Configuration & LLM Factory
│
├── agents/
│   ├── __init__.py
│   ├── planner.py              ← Planner Agent
│   ├── researcher.py           ← Researcher Agent
│   ├── analyzer.py             ← Analyzer Agent
│   ├── synthesizer.py          ← Synthesizer Agent
│   └── tools.py                ← Shared Tools
│
├── graph/
│   ├── __init__.py
│   ├── state.py                ← Pydantic Models (20+ classes)
│   └── orchestrator.py         ← LangGraph State Machine
│
├── persistence/
│   ├── __init__.py
│   └── checkpoint_manager.py   ← SQLite Persistence
│
├── utils/
│   ├── __init__.py
│   ├── logger.py               ← Structured Logging
│   └── metrics.py              ← Observability
│
├── tests/
│   ├── __init__.py
│   ├── test_agents.py          ← Unit Tests
│   ├── test_graph.py           ← Integration Tests
│   └── test_e2e.py             ← End-to-End Tests
│
├── reports/                    ← Output Directory
│   └── *.json, *.txt files
│
├── requirements.txt            ← Dependencies
├── .env.example                ← Configuration Template
├── .env                        ← User Configuration (gitignored)
│
└── Documentation/
    ├── README.md               ← Full Documentation
    ├── QUICKSTART.md           ← Getting Started
    └── IMPLEMENTATION_COMPLETE.md ← This Project Summary
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Orchestration** | LangGraph | State machine coordination |
| **LLM Framework** | LangChain | Unified LLM interface |
| **LLMs** | OpenAI, Ollama | Language models |
| **Data Validation** | Pydantic | Type-safe models |
| **Persistence** | SQLite | State checkpoints |
| **Logging** | Python logging | Structured logs |
| **CLI** | argparse | Command-line interface |
| **Testing** | pytest | Test framework |
| **Config** | python-dotenv | Environment management |

---

## Design Patterns Used

1. **Factory Pattern** - `get_llm()` for LLM initialization
2. **State Machine** - LangGraph for workflow coordination
3. **Decorator Pattern** - `@retry_with_exponential_backoff()`
4. **Context Manager** - `LogContext` for scoped logging
5. **Strategy Pattern** - Different agents for different tasks
6. **Composition** - Agents composed of tools and prompts
7. **Dependency Injection** - LLM injected into agents

---

## Performance Characteristics

```
Execution Time Breakdown (Standard Research):

Planning:    ████░░░░░░░░░  1-2 min (LLM call)
Researching: ███████░░░░░░░  3-5 min (web search + fetch)
Analyzing:   ██░░░░░░░░░░░░  0.5-1 min (pattern analysis)
Synthesizing:██░░░░░░░░░░░░  0.5-1 min (report generation)
─────────────────────────────────────────────
Total:       5-15 minutes

Memory Usage: ~200MB (depends on findings size)
Database:    <1MB for 100 workflows
```

---

## Security Considerations

1. **API Keys** - Stored in .env (never in version control)
2. **Local Processing** - Ollama option for privacy
3. **Data Isolation** - Each workflow has unique session_id
4. **No Telemetry** - Unless LangSmith explicitly enabled
5. **Input Validation** - Pydantic models validate all inputs

---

This architecture ensures:
✅ Scalability - Easy to add more agents
✅ Maintainability - Clear separation of concerns
✅ Testability - Each component independently testable
✅ Debuggability - Detailed logging and metrics
✅ Extensibility - Plugin architecture for custom tools
✅ Reliability - Error handling and persistence
✅ Performance - Efficient state management
