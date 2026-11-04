"""
CLI interface for the Travel Planner Agent.
Run: python cli.py
"""

from __future__ import annotations

import json
import sys
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich import box

from src.agent.planner_agent import TravelPlannerAgent

console = Console()

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║         ✈️  TRAVEL PLANNER AGENT  ✈️                         ║
║         Powered by IBM Granite on IBM watsonx.ai             ║
╚══════════════════════════════════════════════════════════════╝
"""

HELP_TEXT = """
[bold cyan]What you can ask:[/bold cyan]

  • [green]Suggest destinations[/green] — "Suggest me a destination for a beach holiday with $2000 budget"
  • [green]Full trip plan[/green]       — "Plan a 7-day trip to Japan from New York for $3000"
  • [green]Weather[/green]              — "What's the weather like in Paris next week?"
  • [green]Itinerary[/green]            — "Create a 5-day itinerary for Barcelona"
  • [green]Transport[/green]            — "How can I get from London to Rome?"
  • [green]Accommodation[/green]        — "Find me hotels in Kyoto for $80/night"
  • [green]Local guide[/green]          — "Give me insider tips for visiting Tokyo"

  Type [bold]reset[/bold] to clear conversation history
  Type [bold]quit[/bold] or [bold]exit[/bold] to exit
"""


def print_result(result: dict) -> None:
    """Pretty-print agent results."""
    intent = result.get("intent_detected", "unknown")
    console.print(f"\n[dim]Intent detected: [bold]{intent}[/bold][/dim]")

    if intent == "get_weather":
        summary = result.get("weather_summary", "")
        console.print(Panel(summary, title="🌤 Weather Report", border_style="blue"))

    elif intent == "suggest_destinations":
        dests = result.get("destinations", [])
        if dests:
            table = Table(title="🌍 Suggested Destinations", box=box.ROUNDED, border_style="green")
            table.add_column("Rank", style="dim", width=5)
            table.add_column("City", style="bold cyan")
            table.add_column("Country", style="cyan")
            table.add_column("Est. Cost (USD)", justify="right", style="green")
            table.add_column("Best Months", style="yellow")
            table.add_column("Why", style="white", max_width=45)
            for d in dests:
                table.add_row(
                    str(d.get("rank", "")),
                    d.get("city", ""),
                    d.get("country", ""),
                    f"${d.get('estimated_cost_usd', 'N/A')}",
                    ", ".join(d.get("best_months", [])[:2]),
                    d.get("why", ""),
                )
            console.print(table)
        else:
            _print_raw(result)

    elif intent == "build_itinerary":
        days = result.get("itinerary", [])
        console.print(Panel(
            f"[bold]Destination:[/bold] {result.get('destination', '')}\n"
            f"[bold]Duration:[/bold] {result.get('duration_days', '')} days\n"
            f"[bold]Budget level:[/bold] {result.get('budget_level', '')}\n"
            f"[bold]Estimated total:[/bold] ${result.get('total_estimated_cost_usd', 'N/A')}",
            title="📅 Itinerary Overview", border_style="magenta",
        ))
        for day in days[:3]:  # Show first 3 days in CLI
            console.print(f"\n[bold yellow]Day {day.get('day')} — {day.get('theme', '')}[/bold yellow]")
            for period in ("morning", "afternoon", "evening"):
                slot = day.get(period, {})
                if slot:
                    console.print(f"  [{period[:2].upper()}] {slot.get('activity', '')} — {slot.get('description', '')}")
        if len(days) > 3:
            console.print(f"  [dim]... and {len(days) - 3} more days. See full JSON for complete itinerary.[/dim]")

    elif intent in ("recommend_transport", "recommend_accommodation"):
        options = result.get("options", [])
        title = "🚀 Transport Options" if intent == "recommend_transport" else "🏨 Accommodation Options"
        for opt in options[:3]:
            console.print(Panel(
                f"[bold]{opt.get('mode', opt.get('name', ''))}[/bold]\n"
                f"Cost: ${opt.get('estimated_cost_usd', opt.get('estimated_price_per_night_usd', 'N/A'))}\n"
                f"Pros: {', '.join(opt.get('pros', []))}\n"
                f"Tip: {opt.get('booking_tips', opt.get('tips', ''))}",
                title=title, border_style="blue",
            ))

    elif intent == "local_guide":
        must_see = result.get("must_see", [])
        must_eat = result.get("must_eat", [])
        gems = result.get("hidden_gems", [])
        console.print(Panel(
            f"[bold]Must See:[/bold] {', '.join(m.get('name','') for m in must_see[:3])}\n"
            f"[bold]Must Eat:[/bold] {', '.join(m.get('dish','') for m in must_eat[:3])}\n"
            f"[bold]Hidden Gems:[/bold] {'; '.join(gems[:2])}\n"
            f"[bold]Best Time:[/bold] {result.get('best_time_to_visit', '')}",
            title="🗺 Local Guide", border_style="green",
        ))

    elif intent == "full_plan":
        console.print(Panel(
            f"[bold green]✅ Complete travel plan generated![/bold green]\n"
            f"Destination: {result.get('destination', '')}\n"
            f"Duration: {result.get('duration_days', '')} days\n"
            f"Sections: Weather, Itinerary, Transport, Accommodation, Local Guide",
            title="🌐 Full Travel Plan", border_style="green",
        ))
        if result.get("weather"):
            console.print(Panel(result["weather"].get("summary", ""), title="🌤 Weather", border_style="blue"))

    else:
        # General answer
        answer = result.get("answer", "")
        if answer:
            console.print(Panel(answer, title="💬 Travel Assistant", border_style="cyan"))
        else:
            _print_raw(result)


def _print_raw(result: dict) -> None:
    """Fallback: print as pretty JSON."""
    clean = {k: v for k, v in result.items() if k not in ("intent_detected", "extracted_params")}
    console.print_json(json.dumps(clean, indent=2, default=str))


def main() -> None:
    console.print(BANNER, style="bold green")
    console.print(HELP_TEXT)

    try:
        agent = TravelPlannerAgent()
    except EnvironmentError as exc:
        console.print(f"[bold red]Configuration Error:[/bold red] {exc}")
        sys.exit(1)

    console.print("[bold green]Agent initialized! IBM Granite is ready.[/bold green]\n")

    while True:
        try:
            user_input = console.input("[bold blue]You:[/bold blue] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold]Goodbye! Safe travels! ✈️[/bold]")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "bye"):
            console.print("[bold]Goodbye! Safe travels! ✈️[/bold]")
            break

        if user_input.lower() == "reset":
            agent.reset()
            console.print("[dim]Conversation history cleared.[/dim]")
            continue

        console.print("[dim]Thinking...[/dim]")
        try:
            result = agent.chat(user_input)
            print_result(result)
        except EnvironmentError as exc:
            console.print(f"[bold red]Error:[/bold red] {exc}")
        except Exception as exc:
            console.print(f"[bold red]Unexpected error:[/bold red] {exc}")


if __name__ == "__main__":
    main()
