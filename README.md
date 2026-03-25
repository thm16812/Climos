# Mirror Fish — Scenario Planner

A terminal CLI tool for testing **mercy operation plans** against real-world scenarios and gauging their effectiveness using Claude AI.

Inspired by [MiroFish](https://github.com/666ghj/MiroFish) — swarm intelligence prediction engine.

---

## Setup (MacBook)

**Requirements:** Python 3.11+

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API key
cp .env.example .env
# Open .env and set your ANTHROPIC_API_KEY

# 3. Run
python main.py --help
```

---

## Usage

### 1. Create a Scenario
```bash
python main.py scenario new
```
You'll be prompted for:
- Scenario name & description
- Context type (humanitarian, conflict, economic, etc.)
- Key variables (population, conflict level, resources, etc.)
- Constraints (access limitations, supply shortages, etc.)

### 2. Add Mercy Operation Plans
```bash
python main.py plan new <scenario-id>
```
Define plans with approach type, resources, timeline, and objectives.

### 3. Analyze Effectiveness
```bash
# Analyze all plans in a scenario
python main.py analyze <scenario-id>

# Analyze a specific plan
python main.py analyze <scenario-id> --plan <plan-id>

# Compare all plans side-by-side
python main.py analyze <scenario-id> --compare
```

### 4. View Reports
```bash
python main.py report <scenario-id>
python main.py report <scenario-id> --plan <plan-id>
```

### Other Commands
```bash
python main.py scenario list          # List all scenarios
python main.py scenario show <id>     # Show scenario details
python main.py scenario delete <id>   # Delete a scenario
python main.py plan list <scenario-id>
python main.py plan show <scenario-id> <plan-id>
```

---

## Data Storage

All scenarios, plans, and reports are stored locally in `~/.climos/` as JSON files.

```
~/.climos/
├── scenarios/
├── plans/<scenario-id>/
└── reports/<scenario-id>/
```

---

## Model

Uses `claude-sonnet-4-6` by default. Override in `.env`:
```
MODEL=claude-sonnet-4-6
MAX_TOKENS=2000
```
