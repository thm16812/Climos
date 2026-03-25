# Mirror Fish — Claude Code Context

This project is a terminal-based **Mercy Operation Plan Effectiveness Analyzer** powered by Claude AI.

## What It Does
1. User defines a **scenario** (conflict zone, disaster, political crisis, etc.)
2. User creates **mercy operation plans** (humanitarian interventions to test)
3. Claude Sonnet **analyzes each plan** and returns effectiveness scores, risks, predicted outcomes, and recommendations
4. Reports are saved locally and displayed in rich terminal UI

## File Map
| File | Role |
|------|------|
| `main.py` | CLI entry point — all `click` command groups live here |
| `models.py` | Pydantic data models: `Scenario`, `MercyPlan`, `EffectivenessReport` |
| `storage.py` | JSON read/write — saves to `~/.climos/` |
| `analyzer.py` | Calls Claude API (`anthropic` SDK), parses JSON responses |
| `prompts.py` | Prompt templates: `build_analysis_prompt`, `build_comparison_prompt` |
| `display.py` | Rich terminal UI — tables, panels, color-coded score display |
| `config.py` | Loads `.env`, exposes `ANTHROPIC_API_KEY`, `MODEL`, `MAX_TOKENS` |

## Key Commands
```bash
python main.py scenario new              # Create a scenario
python main.py plan new <scenario-id>    # Add a mercy plan
python main.py analyze <scenario-id>     # Analyze all plans
python main.py analyze <id> --compare    # Side-by-side comparison
python main.py report <scenario-id>      # View saved reports
```

## Adding Features
- **New approach types**: Add to the choices list in `main.py plan new`
- **New context types**: Add to choices in `main.py scenario new`
- **Change the model**: Edit `MODEL` in `.env`
- **Modify analysis depth**: Edit prompts in `prompts.py`
- **Change report format**: Edit `display.py`

## Data Location
All data stored in `~/.climos/` as JSON. Safe to delete and start fresh.

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env   # add ANTHROPIC_API_KEY
python main.py --help
```
