#!/usr/bin/env python3
"""
AI Business Team — Interactive Dashboard
A team of 7 AI agents that build and run online businesses from scratch.

Usage:
  python main.py                    # Interactive dashboard
  python main.py --headless         # Run one cycle and exit
  python main.py --agent researcher --task "Find 3 SaaS ideas"
"""
import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

sys.path.insert(0, str(Path(__file__).parent))

from core.state_manager import StateManager
from core.message_bus import MessageBus
from core.tools import ToolRegistry
from agents.orchestrator import OrchestratorAgent
from agents.researcher import ResearcherAgent
from agents.planner import PlannerAgent
from agents.builder import BuilderAgent
from agents.marketer import MarketerAgent
from agents.finance import FinanceAgent
from agents.growth import GrowthAgent

console = Console() if RICH_AVAILABLE else None


def build_team(base_dir: str = "."):
    state = StateManager(base_dir)
    bus = MessageBus(str(state.db_path))
    registry = ToolRegistry(state, bus)

    agents = {
        "researcher": ResearcherAgent(registry, state, bus),
        "planner":    PlannerAgent(registry, state, bus),
        "builder":    BuilderAgent(registry, state, bus),
        "marketer":   MarketerAgent(registry, state, bus),
        "finance":    FinanceAgent(registry, state, bus),
        "growth":     GrowthAgent(registry, state, bus),
    }

    orchestrator = OrchestratorAgent(registry, state, bus, agent_registry=agents)
    return orchestrator, agents, state, bus


def print_banner():
    if not RICH_AVAILABLE:
        print("\n=== AI BUSINESS TEAM ===")
        print("7 AI agents building online businesses 24/7\n")
        return

    console.print(Panel(
        "[bold cyan]AI BUSINESS TEAM[/bold cyan]\n"
        "[white]7 specialized agents building online businesses from scratch — 24/7[/white]",
        box=box.DOUBLE, border_style="cyan"
    ))

    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    t.add_column("", width=4)
    t.add_column("Agent", style="bold", width=14)
    t.add_column("Role")
    for row in [
        ("👑", "Orchestrator", "CEO — coordinates the team, drives the portfolio"),
        ("🔬", "Researcher",   "Finds profitable niches, validates ideas"),
        ("📋", "Planner",      "Business plans, MVP specs, financial models"),
        ("🏗️",  "Builder",      "Landing pages, product code, email templates"),
        ("📢", "Marketer",     "Blog posts, email sequences, social content"),
        ("💰", "Finance",      "Revenue tracking, pricing strategy, P&L"),
        ("🚀", "Growth",       "Experiments, referral programs, scaling"),
    ]:
        t.add_row(*row)
    console.print(Panel(t, title="[bold]The Team[/bold]", border_style="dim"))


def print_portfolio(state: StateManager):
    businesses = state.list_businesses()
    if not RICH_AVAILABLE:
        print(f"\n{len(businesses)} businesses in portfolio")
        for b in businesses:
            print(f"  [{b['id']}] {b['name']} — {b.get('status')} | rev: ${b.get('revenue',0):.2f}")
        return

    if not businesses:
        console.print(Panel("[yellow]No businesses yet. Run a cycle![/yellow]", title="Portfolio"))
        return

    t = Table(title="Business Portfolio", box=box.ROUNDED)
    t.add_column("ID", style="dim", width=10)
    t.add_column("Name", style="bold cyan")
    t.add_column("Niche", style="green")
    t.add_column("Model", style="blue")
    t.add_column("Status", style="yellow")
    t.add_column("Revenue", justify="right", style="green")
    t.add_column("Profit", justify="right")

    colors = {"ideation": "dim", "planning": "yellow", "building": "blue",
              "launching": "cyan", "growing": "green", "scaling": "bold green", "paused": "red"}

    for b in businesses:
        rev = b.get("revenue", 0)
        profit = rev - b.get("expenses", 0)
        status = b.get("status", "ideation")
        t.add_row(
            b["id"], b["name"], b.get("niche", ""), b.get("model", ""),
            f"[{colors.get(status, 'white')}]{status}[/{colors.get(status, 'white')}]",
            f"${rev:,.2f}",
            f"[green]${profit:,.2f}[/green]" if profit >= 0 else f"[red]-${abs(profit):,.2f}[/red]"
        )
    console.print(t)


def print_log(state: StateManager, limit: int = 20):
    log = state.get_agent_log(limit=limit)
    if not RICH_AVAILABLE:
        for e in log:
            print(f"  {e['timestamp'][:19]} [{e['agent']}] {e.get('summary','')[:80]}")
        return

    t = Table(title="Agent Activity", box=box.SIMPLE)
    t.add_column("Time", style="dim", width=20)
    t.add_column("Agent", style="bold", width=14)
    t.add_column("Business", width=10)
    t.add_column("Summary", style="dim")
    colors = {"orchestrator": "magenta", "researcher": "cyan", "planner": "blue",
              "builder": "yellow", "marketer": "green", "finance": "red", "growth": "bright_magenta"}
    for e in log:
        ag = e.get("agent", "?")
        c = colors.get(ag, "white")
        t.add_row(
            (e.get("timestamp") or "")[:19].replace("T", " "),
            f"[{c}]{ag}[/{c}]",
            e.get("business_id") or "—",
            (e.get("summary") or "")[:90]
        )
    console.print(t)


def interactive_menu(orchestrator, agents, state, bus):
    print_banner()
    while True:
        if RICH_AVAILABLE:
            console.print("\n[bold]What would you like to do?[/bold]")
            console.print("  [cyan]1[/cyan]  Run full orchestration cycle")
            console.print("  [cyan]2[/cyan]  View portfolio")
            console.print("  [cyan]3[/cyan]  View agent log")
            console.print("  [cyan]4[/cyan]  Run a specific agent")
            console.print("  [cyan]5[/cyan]  Add a business manually")
            console.print("  [cyan]6[/cyan]  List output files")
            console.print("  [cyan]q[/cyan]  Quit")
            choice = Prompt.ask("\nChoice", choices=["1","2","3","4","5","6","q"], default="1")
        else:
            print("\n1=cycle 2=portfolio 3=log 4=agent 5=add-biz 6=outputs q=quit")
            choice = input("Choice [1]: ").strip() or "1"

        if choice == "q":
            print("Goodbye.")
            break

        elif choice == "1":
            print("\nRunning orchestration cycle...\n")
            result = orchestrator.run_cycle()
            if RICH_AVAILABLE:
                console.print(Panel(result, title="CEO Report", border_style="green"))
            else:
                print(f"\n--- CEO REPORT ---\n{result}\n")

        elif choice == "2":
            print_portfolio(state)

        elif choice == "3":
            print_log(state)

        elif choice == "4":
            names = list(agents.keys())
            if RICH_AVAILABLE:
                agent_name = Prompt.ask("Which agent", choices=names)
                task = Prompt.ask("Task")
                bid = Prompt.ask("Business ID (blank=none)", default="")
            else:
                print(f"Agents: {', '.join(names)}")
                agent_name = input("Agent: ").strip()
                task = input("Task: ").strip()
                bid = input("Business ID (blank=none): ").strip()

            result = agents[agent_name].run(task, business_id=bid or None)
            if RICH_AVAILABLE:
                console.print(Panel(result, title=f"{agent_name} Output", border_style="cyan"))
            else:
                print(f"\n{result}\n")

        elif choice == "5":
            if RICH_AVAILABLE:
                name  = Prompt.ask("Name")
                niche = Prompt.ask("Niche")
                model = Prompt.ask("Model", choices=["saas","content","ecommerce","digital_product","affiliate","service"])
                desc  = Prompt.ask("Description")
            else:
                name  = input("Name: ").strip()
                niche = input("Niche: ").strip()
                model = input("Model: ").strip()
                desc  = input("Description: ").strip()
            b = state.create_business(name, niche, model, desc)
            print(f"Created '{name}' with ID: {b['id']}")

        elif choice == "6":
            output_root = state.outputs_dir
            files = list(output_root.rglob("*"))
            files = [f for f in files if f.is_file()]
            if not files:
                print("No outputs yet.")
            else:
                for f in sorted(files):
                    print(f"  {f.relative_to(output_root)}")


def main():
    parser = argparse.ArgumentParser(description="AI Business Team")
    parser.add_argument("--headless", action="store_true", help="Run one cycle and exit")
    parser.add_argument("--agent", help="Run a specific agent")
    parser.add_argument("--task", help="Task for the agent")
    parser.add_argument("--business-id", help="Business ID context")
    parser.add_argument("--dir", default=".", help="Data directory")
    args = parser.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY is not set.")
        print("Copy .env.example to .env and add your key.")
        sys.exit(1)

    orchestrator, agents, state, bus = build_team(args.dir)

    if args.headless:
        print(f"[{datetime.utcnow().isoformat()}] Starting cycle...")
        result = orchestrator.run_cycle()
        print(result)

    elif args.agent:
        if args.agent not in agents:
            print(f"Unknown agent '{args.agent}'. Available: {list(agents.keys())}")
            sys.exit(1)
        task = args.task or "Do a status check and output a summary."
        result = agents[args.agent].run(task, business_id=args.business_id)
        print(result)

    else:
        interactive_menu(orchestrator, agents, state, bus)


if __name__ == "__main__":
    main()
