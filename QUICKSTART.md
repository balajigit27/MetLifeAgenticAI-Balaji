# QUICKSTART Guide - Agentic Research Orchestrator

## 🚀 Get Started in 5 Minutes

### 1. Clone & Setup (1 min)

```bash
cd agentic-research-orchestrator
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies (2 min)

```bash
pip install -r requirements.txt
```

### 3. Configure LLM (1 min)

**Option A: Use OpenAI (Cloud)**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key:
# OPENAI_API_KEY=sk-your-key-here
# LLM_MODE=cloud
```

**Option B: Use Ollama (Local/Private)**
```bash
# 1. Install Ollama: https://ollama.ai
# 2. Run a model: ollama run mistral
# 3. In .env:
# LLM_MODE=local
# OLLAMA_BASE_URL=http://localhost:11434
```

### 4. Run Your First Research (1 min)

```bash
# Quick research (local Ollama)
python main.py --topic "AI agents in 2025" --depth quick --llm local

# Standard research (OpenAI)
python main.py --topic "Climate tech startups" --depth standard --llm cloud

# Show configuration
python main.py --info

# Show recent research history
python main.py --history
```

---

## 📚 Common Examples

### Example 1: Quick Market Research
```bash
python main.py \
  --topic "Emerging AI applications in healthcare" \
  --depth quick \
  --llm local \
  --output reports/healthcare_ai.json
```

### Example 2: Deep Competitive Analysis
```bash
python main.py \
  --topic "AI agent frameworks comparison" \
  --domains "AI,software-engineering,frameworks" \
  --depth deep \
  --llm cloud \
  --context "Focus on production-ready systems"
```

### Example 3: Resume Interrupted Research
```bash
# See recent research
python main.py --history

# Resume a specific research
python main.py --resume task-20250511-143022
```

---

## 🧠 How It Works

```
Your Topic
   ↓
[Planner] ← Breaks into research questions
   ↓
[Researcher] ← Fetches information from web
   ↓
[Analyzer] ← Evaluates findings & patterns
   ↓
[Synthesizer] ← Creates final report
   ↓
Research Report (JSON + Text)
```

Each agent is powered by your chosen LLM (OpenAI or Ollama).

---

## 📊 Output

Research results are saved to `reports/` directory:

```
reports/
├── climate_tech_20250511-143022.json       # Structured data
└── climate_tech_20250511-143022.txt        # Formatted report
```

JSON contains:
- Executive summary
- Main findings (prioritized)
- Detailed analysis
- Citations and sources
- Limitations & recommendations

---

## ⚙️ Configuration Options

| Option | Values | Default |
|--------|--------|---------|
| `--depth` | quick, standard, deep | standard |
| `--llm` | cloud, local | Uses LLM_MODE from .env |
| `--format` | json, text, both | both |
| `--output` | file path | Auto-generated |
| `--domains` | comma-separated | None |

### Environment Variables (in .env)

```bash
# LLM Selection
LLM_MODE=cloud                    # or "local"

# Cloud (OpenAI)
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4-turbo

# Local (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# Features
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
ENABLE_CHECKPOINTS=true           # Save/resume capability
```

---

## 🔍 Understanding Output

### Quick Research Example
```
Research Depth: quick
Expected Time: 2-5 min
Questions: 1-2
Sources: 3-5
Output: Brief findings with top 2-3 sources
```

### Standard Research Example
```
Research Depth: standard
Expected Time: 5-15 min
Questions: 3-5
Sources: 5-10
Output: Comprehensive report with analysis
```

### Deep Research Example
```
Research Depth: deep
Expected Time: 15-30 min
Questions: 5+
Sources: 10+
Output: Detailed analysis with multiple perspectives
```

---

## 🛠️ For Developers

### Run Tests

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/test_e2e.py -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

### View Code Structure

```bash
# See what's in each module
ls -la agents/           # Agent implementations
ls -la graph/            # LangGraph orchestration
ls -la persistence/      # Checkpoint management
ls -la utils/            # Logging & metrics
```

### Debug Mode

```bash
DEBUG_MODE=true python main.py --topic "Test" --depth quick --debug
```

---

## ⚡ Performance Tips

### For Speed
- Use **quick** depth (fewer questions, faster)
- Use **local Ollama** (no network latency)
- Use smaller models: `mistral` (7B) vs `llama2` (13B)

### For Quality
- Use **deep** depth (more comprehensive)
- Use **cloud OpenAI** (higher quality models)
- Use GPT-4 model (better reasoning)

### For Cost
- Use **local Ollama** (free, no API calls)
- Use **quick** depth (fewer API calls)
- Use `gpt-3.5-turbo` (cheaper but less capable)

---

## 🐛 Troubleshooting

### Error: "OpenAI API key not found"
```bash
# Solution: Set OPENAI_API_KEY in .env
OPENAI_API_KEY=sk-your-key-here
```

### Error: "Connection refused: http://localhost:11434"
```bash
# Solution: Start Ollama
ollama serve

# In another terminal, download a model
ollama pull mistral  # Or: llama2, neural-chat, etc.
```

### Error: "CUDA out of memory"
```bash
# Solution: Use smaller model
OLLAMA_MODEL=mistral        # Instead of: llama2-13b

# Or: Run on CPU
ollama serve --cpu-only
```

### Error: "Rate limit exceeded (429)"
```bash
# Solution: Adjust retries in .env
MAX_RETRIES=5              # Increase retry attempts

# Or: Wait and retry
sleep 60
python main.py --topic "..." --llm cloud
```

---

## 📖 Learning Path

1. **Start here** → `python main.py --info` (see config)
2. **Run quick research** → `python main.py --topic "X" --depth quick --llm local`
3. **Check output** → `cat reports/*.json` (see results)
4. **Read code** → Start with [agents/planner.py](agents/planner.py)
5. **Understand flow** → Read [graph/orchestrator.py](graph/orchestrator.py)
6. **Run tests** → `pytest tests/ -v`
7. **Modify prompts** → Edit agent prompt templates in each agent file
8. **Add custom tools** → Extend [agents/tools.py](agents/tools.py)

---

## 🎯 Next Steps

- **Integrate Real Data**: Replace mock search with SerpAPI or Firecrawl
- **Improve Prompts**: Add few-shot examples to agent prompts
- **Add Custom Tools**: Connect to your own APIs and databases
- **Deploy as API**: Wrap `main.run_research()` in FastAPI
- **Scale Up**: Add parallel researcher agents for multi-query research
- **Fine-tune Models**: Use your research data to improve local LLMs

---

## 📞 Get Help

- **Configuration Issues**: Check `.env` file and compare to `.env.example`
- **LLM Issues**: Verify API keys or Ollama is running
- **Test Failures**: Run `pytest tests/ -v --tb=short`
- **Debug Output**: Enable `DEBUG_MODE=true` and check logs

---

## 💡 Pro Tips

1. **Experiment with depths** - Start quick, then use standard/deep as needed
2. **Use local first** - Develop locally with Ollama, then test with OpenAI
3. **Parallel workflows** - Run multiple research tasks simultaneously
4. **Save money** - Use `gpt-3.5-turbo` for faster prototyping, `gpt-4` for final reports
5. **Monitor quality** - Check JSON output's `quality_assessment` metrics

---

## 📝 License & Attribution

This is an industrial-strength, production-ready agentic AI orchestration system built with:
- **LangGraph** - State machine orchestration
- **LangChain** - LLM framework
- **OpenAI/Ollama** - Language models
- **Pydantic** - Type validation

Built for: AI practitioners, researchers, and developers learning agentic patterns.

---

**Ready to get started?** Run: `python main.py --info` 🚀
