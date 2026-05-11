# Agentic Research Orchestrator

A production-ready, multi-agent AI research system using LangGraph. Orchestrates 4 specialized agents (Planner → Researcher → Analyzer → Synthesizer) to conduct comprehensive research on any topic.

## Features

✅ **Multi-Agent Orchestration**: Planner, Researcher, Analyzer, Synthesizer pipeline
✅ **Dual LLM Support**: OpenAI (cloud) or Ollama (local/private)
✅ **Durable Execution**: Checkpoint system for pause/resume capability
✅ **Production-Ready**: Error handling, retries, structured logging, observability
✅ **Easy CLI**: Simple command-line interface with configurable parameters
✅ **Type-Safe**: Pydantic models for state management and validation

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings
```

### 2. Configure LLM

**Option A: Cloud (OpenAI)**
```bash
# In .env
LLM_MODE=cloud
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-turbo
```

**Option B: Local (Ollama)**
```bash
# Install Ollama from https://ollama.ai
ollama run mistral  # or any other model

# In .env
LLM_MODE=local
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
```

### 3. Run Research

```bash
# Quick research
python main.py --topic "AI agents in 2025" --depth quick --llm local

# Standard research (with all features)
python main.py --topic "Climate tech startups" --depth standard --llm cloud

# Deep research (comprehensive)
python main.py --topic "Quantum computing applications" --depth deep --llm cloud

# Resume from checkpoint
python main.py --resume task-20250511-143022
```

## Architecture

```
Input (Research Topic)
    ↓
┌─────────────────────────────────────────┐
│         Planner Agent                   │
│  • Breaks topic into research questions │
│  • Identifies information gaps          │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│        Researcher Agent                 │
│  • Fetches web sources                  │
│  • Extracts relevant information        │
│  • Validates document accessibility     │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│         Analyzer Agent                  │
│  • Evaluates factual accuracy           │
│  • Identifies patterns & insights       │
│  • Flags contradictions                 │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│       Synthesizer Agent                 │
│  • Combines findings into narrative     │
│  • Adds citations and sources           │
│  • Generates final report               │
└─────────────────────────────────────────┘
    ↓
Output (Research Report JSON + Formatted Text)
```

## Project Structure

```
agentic-research-orchestrator/
├── main.py                    # CLI entry point
├── config.py                  # LLM & environment configuration
├── agents/
│   ├── planner.py            # Planner agent
│   ├── researcher.py         # Researcher agent
│   ├── analyzer.py           # Analyzer agent
│   ├── synthesizer.py        # Synthesizer agent
│   └── tools.py              # Shared tools (search, fetch, validate)
├── graph/
│   ├── state.py              # Pydantic state models
│   └── orchestrator.py       # LangGraph workflow definition
├── persistence/
│   └── checkpoint_manager.py # Checkpoint save/load logic
├── utils/
│   ├── logger.py             # Structured logging
│   └── metrics.py            # Performance metrics
├── tests/                     # Unit & E2E tests
├── reports/                   # Output research reports
├── requirements.txt           # Python dependencies
├── .env.example              # Configuration template
└── README.md                 # This file
```

## Configuration

See `.env.example` for all available options:

- **LLM_MODE**: `cloud` (OpenAI) or `local` (Ollama)
- **Research Depth**: `quick` (5 min), `standard` (15 min), `deep` (30+ min)
- **Logging**: LOG_LEVEL, JSON_LOGGING, DEBUG_MODE
- **Observability**: LangSmith integration (optional)
- **Persistence**: ENABLE_CHECKPOINTS for pause/resume

## Usage Examples

### Python API

```python
from main import run_research
from config import settings

# Run research programmatically
result = run_research(
    topic="AI agents in 2025",
    depth="standard",
    llm_mode="cloud"
)

print(result["report"])
print(f"Sources: {result['sources']}")
```

### CLI

```bash
# Check current configuration
python main.py --info

# Run with custom parameters
python main.py \
  --topic "Quantum computing" \
  --depth deep \
  --llm cloud \
  --output custom_report.json

# Resume interrupted research
python main.py --resume task-20250511-143022
```

## Development

### Run Tests

```bash
# All tests
pytest tests/

# With coverage
pytest tests/ --cov=. --cov-report=html

# Specific test file
pytest tests/test_e2e.py -v
```

### Debug Mode

```bash
# Enable debug logging
DEBUG_MODE=true python main.py --topic "Test" --depth quick
```

### LangSmith Integration

```bash
# Enable observability
LANGSMITH_ENABLED=true \
LANGSMITH_API_KEY=your-key \
python main.py --topic "AI agents" --depth standard
```

View traces at: https://smith.langchain.com/

## Performance

| Mode | Depth | Cloud (GPT-4) | Local (Mistral) |
|------|-------|---------------|-----------------|
| Quick | 1-2 questions | ~2 min | ~1.5 min |
| Standard | 3-5 questions | ~5 min | ~4 min |
| Deep | 5+ questions | ~15 min | ~12 min |

*Timings are estimates and depend on LLM speed and network latency.*

## Troubleshooting

### OpenAI API Key Error
```
ValueError: OpenAI API key not found
```
**Solution**: Set `OPENAI_API_KEY` in `.env` or environment variable

### Ollama Connection Failed
```
Connection error: http://localhost:11434
```
**Solution**: Start Ollama: `ollama serve`

### Out of Memory
```
CUDA out of memory error
```
**Solution**: Reduce model size or use smaller model (e.g., `mistral` instead of `llama2-13b`)

### Token Limit Exceeded
```
This model's maximum context length is 4096 tokens
```
**Solution**: Reduce research depth or increase `OPENAI_MAX_TOKENS`

## API Reference

### Main Entry Points

```python
# From main.py
run_research(topic: str, depth: str, llm_mode: str) -> dict
resume_research(session_id: str) -> dict

# From config.py
get_llm(mode: str | None = None) -> ChatOpenAI | ChatOllama
get_llm_info() -> dict
```

### Agents

```python
# From agents/
PlannerAgent(llm) -> ResearchPlan
ResearcherAgent(llm) -> ResearchFindings
AnalyzerAgent(llm) -> AnalysisResult
SynthesizerAgent(llm) -> ResearchReport
```

## Next Steps

- [ ] Integrate real web search (SerpAPI, Tavily)
- [ ] Add document parsing (PDF, Word, PowerPoint)
- [ ] Implement parallel researcher agents for multi-query research
- [ ] Add user feedback loop for iterative refinement
- [ ] Fine-tune prompts with few-shot examples
- [ ] Deploy as FastAPI service
- [ ] Add vector database for long-term memory

## Contributing

Contributions welcome! Please follow PEP 8 and add tests for new features.

## License

MIT

## Support

- **Issues**: GitHub Issues
- **Documentation**: See README.md and code comments
- **Questions**: Check troubleshooting section above

---

**Made with ❤️ for AI orchestration enthusiasts**
