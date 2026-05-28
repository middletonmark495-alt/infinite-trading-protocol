# AI Business Team

A team of **7 specialized AI agents** that collaboratively build and run online businesses from scratch — autonomously, 24/7.

Each agent is powered by Claude (Anthropic) and has its own expertise, tools, and responsibilities. The Orchestrator (CEO) coordinates everyone and drives the portfolio forward cycle by cycle.

---

## The Team

| Agent | Role | What They Build |
|-------|------|-----------------|
| **Orchestrator** | CEO | Portfolio strategy, agent dispatch, cycle management |
| **Researcher** | Market Analyst | Opportunity research, idea validation, competitor analysis |
| **Planner** | Business Strategist | Business plans, MVP specs, financial models, customer personas |
| **Builder** | Full-Stack Dev | Landing pages (HTML), product code, email templates, legal docs |
| **Marketer** | Content Creator | Blog posts, email sequences, social content, ad copy, SEO strategy |
| **Finance** | CFO | Revenue/expense tracking, pricing strategy, P&L reports, unit economics |
| **Growth** | Growth Hacker | A/B experiments, referral programs, scaling playbooks, partnerships |

---

## Quick Start

```bash
# 1. Install dependencies
cd ai_business_team
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 3. Run the interactive dashboard
python main.py

# 4. Or run headless (one cycle, for cron)
python main.py --headless

# 5. Or run continuously 24/7
python run_team.py
```

---

## How It Works

The team runs in **cycles**. Each cycle:

1. **Orchestrator** checks the portfolio (all businesses + their stages)
2. Decides what each business needs next based on its lifecycle stage
3. Dispatches specialist agents to do real work
4. Agents generate and save concrete outputs (HTML, code, content, reports)
5. Orchestrator updates business statuses and queues next actions
6. Sleeps until next cycle (default: 1 hour)

### Business Lifecycle

```
IDEATION → PLANNING → BUILDING → LAUNCHING → GROWING → SCALING
```

| Stage | Agents Working | What Gets Built |
|-------|---------------|------------------|
| Ideation | Researcher | Opportunity report, idea validation |
| Planning | Planner | Business plan, MVP spec, financial model, ICP |
| Building | Builder | Landing page, product code, email templates, legal docs |
| Launching | Marketer | SEO strategy, blog posts, email sequence, social posts |
| Growing | Finance + Growth | P&L report, growth experiments, referral program |
| Scaling | Growth + All | Scaling playbook, partnerships, optimization |

---

## Output Files

Everything the team builds is saved to disk:

```
outputs/
  {business_id}/
    website/
      index.html          ← Complete landing page
    product/
      main.py             ← Core product code
    emails/
      welcome.html        ← Email template
      welcome_sequence.json
    content/
      {slug}.md           ← Blog posts
    social/
      twitter_posts.json
    marketing/
      seo_strategy.md
    legal/
      terms_of_service.md
      privacy_policy.md
    research/
      {report}.md
    finance/
      pnl_report.json
      unit_economics.json
    growth/
      experiment_{id}.json
      referral_program.md
      scaling_playbook.md

businesses/
  {business_id}.json      ← Full business state

team.db                   ← SQLite: businesses, agent log, metrics, tasks
team.log                  ← Continuous runner log
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | **required** | Your Anthropic API key |
| `ORCHESTRATOR_MODEL` | `claude-opus-4-7` | Model for the CEO agent |
| `SPECIALIST_MODEL` | `claude-sonnet-4-6` | Model for all specialist agents |
| `CYCLE_INTERVAL_HOURS` | `1` | Hours between autonomous cycles |
| `MAX_BUSINESSES` | `10` | Max portfolio size |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG/INFO/WARNING) |

---

## CLI Usage

```bash
# Interactive dashboard (recommended for first run)
python main.py

# Run one full CEO cycle and print the report
python main.py --headless

# Run a specific agent directly
python main.py --agent researcher --task "Find 3 profitable micro-SaaS ideas for developers"
python main.py --agent builder --task "Create a landing page" --business-id abc12345
python main.py --agent marketer --task "Write a 5-email welcome sequence" --business-id abc12345
python main.py --agent planner --task "Create a full business plan" --business-id abc12345

# Run continuously (24/7 mode)
python run_team.py
```

---

## Scheduling (Cron / 24/7)

**Using cron** (run every hour):
```bash
0 * * * * cd /path/to/ai_business_team && python main.py --headless >> logs/cron.log 2>&1
```

**Using PM2** (Node process manager):
```bash
npm install -g pm2
pm2 start run_team.py --interpreter python3 --name ai-business-team
pm2 save
pm2 startup
```

**Using systemd**:
```ini
[Unit]
Description=AI Business Team

[Service]
WorkingDirectory=/path/to/ai_business_team
ExecStart=/usr/bin/python3 run_team.py
Restart=always
EnvironmentFile=/path/to/ai_business_team/.env

[Install]
WantedBy=multi-user.target
```

---

## Architecture

```
OrchestratorAgent (CEO)
    │
    ├─ dispatch_agent(researcher) → ResearcherAgent
    ├─ dispatch_agent(planner)    → PlannerAgent
    ├─ dispatch_agent(builder)    → BuilderAgent
    ├─ dispatch_agent(marketer)   → MarketerAgent
    ├─ dispatch_agent(finance)    → FinanceAgent
    └─ dispatch_agent(growth)     → GrowthAgent

All agents share:
  ├─ StateManager  — SQLite + JSON file persistence
  ├─ MessageBus    — Inter-agent communication queue
  └─ ToolRegistry  — Tool implementations (save files, update state)
```

Each agent runs a **tool-use loop** via the Anthropic SDK:
1. Agent receives task + business context
2. Calls tools to read/write state and save outputs
3. Generates complete content in its text response
4. Loop continues until `stop_reason == end_turn`

---

## Cost Estimate

| Cycle Activity | ~Tokens | ~Cost |
|----------------|---------|-------|
| Orchestrator cycle | 5K | $0.075 |
| Researcher report | 3K | $0.009 |
| Planner (full plan) | 8K | $0.024 |
| Builder (landing page) | 10K | $0.030 |
| Marketer (blog post) | 6K | $0.018 |
| Full cycle (all agents) | ~40K | ~$0.15 |

*At hourly cycles: ~$3.60/day. Adjust `CYCLE_INTERVAL_HOURS` to control cost.*

---

## License

MIT — part of the Infinite Trading Protocol repository.
