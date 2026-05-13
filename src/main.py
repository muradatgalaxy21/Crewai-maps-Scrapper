"""
Maps Lead Gen — Interactive CLI for scraping Google Maps business data.

Usage:
    python -m src.main
"""

import sys
import os
import datetime
import re

def _strip_ansi(text: str) -> str:
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

class TeeLogger:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(_strip_ansi(message))
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

class TeeErrorLogger:
    def __init__(self, filename):
        self.terminal = sys.stderr
        self.log = open(filename, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(_strip_ansi(message))
        self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()

os.makedirs("logs", exist_ok=True)
_ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
sys.stdout = TeeLogger(f"logs/scraper_{_ts}.log")
sys.stderr = TeeErrorLogger(f"logs/scraper_{_ts}.err")

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich import print as rprint

from src.tools.location_api import LocationDiscoveryTool
from src.orchestration.pipeline import ScrapingPipeline

app = typer.Typer(
    name="maps-lead-gen",
    help="Scrape Google Maps business leads by area and category.",
    add_completion=False,
)
console = Console()


@app.command()
def scrape():
    """
    Interactive scraping flow:
    1. Enter target area -> discover sub-locations
    2. Select a specific location
    3. Enter business type -> scrape Google Maps
    4. Get CSV output
    """

    # ─── Banner ───
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]MAPS LEAD GENERATOR[/bold cyan]\n"
            "[dim]Playwright Stealth + Nominatim[/dim]",
            border_style="cyan",
            padding=(0, 2),
        )
    )
    console.print()

    # ─── Step 1: Enter Target Area ───
    area = Prompt.ask(
        "[bold yellow]  TARGET AREA[/bold yellow]",
        default="Luxembourg",
    )

    console.print(f"\n[dim]  Discovering locations in [bold]{area}[/bold]...[/dim]\n")

    location_tool = LocationDiscoveryTool()
    locations = location_tool.discover_locations(area)

    if not locations:
        console.print("[bold red]  ERROR: No locations found. Try a different query.[/bold red]")
        raise typer.Exit(code=1)

    # ─── Step 2: Display Locations Table ───
    table = Table(
        title=f"Locations in [bold]{area}[/bold]",
        show_lines=True,
        border_style="cyan",
    )
    table.add_column("#", style="bold cyan", width=4)
    table.add_column("Location", style="white")
    table.add_column("Type", style="dim")

    for idx, loc in enumerate(locations, 1):
        short_name = loc.display_name
        if len(short_name) > 80:
            short_name = short_name[:77] + "..."
        table.add_row(str(idx), short_name, loc.place_type)

    console.print(table)
    console.print()

    # ─── Step 3: User Selects Location ───
    selected_idx = IntPrompt.ask(
        "[bold yellow]  SELECT LOCATION #[/bold yellow]",
        default=1,
    )

    if selected_idx < 1 or selected_idx > len(locations):
        console.print("[bold red]  ERROR: Invalid selection.[/bold red]")
        raise typer.Exit(code=1)

    selected_location = locations[selected_idx - 1]
    location_name = selected_location.display_name.split(",")[0].strip()
    full_location = selected_location.display_name

    console.print(f"\n[green]  SELECTED:[/green] [bold]{full_location}[/bold]\n")

    # ─── Step 4: Enter Business Type ───
    business_type = Prompt.ask(
        "[bold yellow]  BUSINESS TYPE[/bold yellow]",
        default="Hair Salon",
    )

    # ─── Step 5: Run Scraper ───
    output_file = f"csv/leads_{location_name.lower().replace(' ', '_')}_{business_type.lower().replace(' ', '_')}.csv"

    console.print()
    console.print(
        Panel(
            f"[bold]Location:[/bold] {full_location}\n"
            f"[bold]Business:[/bold] {business_type}\n"
            f"[bold]Output:[/bold]   {output_file}",
            title="SCRAPE CONFIG",
            border_style="green",
            padding=(0, 1),
        )
    )
    console.print()

    pipeline = ScrapingPipeline()
    results = pipeline.run(
        location=full_location,
        business_type=business_type,
        output_file=output_file,
        place_type=selected_location.place_type,
    )

    # ─── Step 6: Display Results Summary ───
    console.print()

    if not results:
        console.print(
            Panel(
                "[bold red]No results found.[/bold red]\n"
                "[dim]Possible CAPTCHA, no listings, or Google blocking.\n"
                "Check for screenshot files in the project folder.[/dim]",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)

    # Results table
    results_table = Table(
        title=f"RESULTS: {len(results)} {business_type}(s) in {location_name}",
        show_lines=True,
        border_style="green",
    )
    results_table.add_column("#", style="bold", width=4)
    results_table.add_column("Business Name", style="cyan", max_width=30)
    results_table.add_column("Rev", width=5)
    results_table.add_column("Phone", style="dim", max_width=20)
    results_table.add_column("Email", style="bold green", max_width=22)
    results_table.add_column("Website", max_width=22)
    results_table.add_column("Address", style="dim", max_width=28)
    results_table.add_column("Social", max_width=12)

    for idx, lead in enumerate(results[:20], 1):
        social_display = "N/A"
        if lead.social_links and lead.social_links != "N/A":
            social_display = f"{len(lead.social_links.split(', '))} link(s)"

        web_display = lead.website or "N/A"
        if web_display != "N/A" and len(web_display) > 22:
            try:
                from urllib.parse import urlparse
                web_display = urlparse(web_display).netloc
            except Exception:
                web_display = web_display[:22]

        results_table.add_row(
            str(idx),
            lead.business_name[:26],
            str(lead.total_reviews),
            lead.phone_number or "N/A",
            (lead.email_address or "N/A")[:22],
            web_display,
            (lead.address or "N/A")[:28],
            social_display,
        )

    console.print(results_table)

    if len(results) > 20:
        console.print(f"[dim]  ... and {len(results) - 20} more in {output_file}[/dim]")

    console.print(
        f"\n[bold green]  COMPLETE:[/bold green] {len(results)} leads saved to [bold]{output_file}[/bold]\n"
    )


def main():
    app()


if __name__ == "__main__":
    main()
