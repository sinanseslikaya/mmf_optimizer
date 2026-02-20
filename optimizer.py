import argparse
import requests
import json
import os
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, FloatPrompt, Confirm
from rich import box

# Local imports
from tax_data import FEDERAL_BRACKETS, STATE_TAX_DATA
from logic import get_marginal_rate, process_fund, filter_funds

CONFIG_PATH = os.path.expanduser("~/.mmf_optimizer_config.json")
console = Console()


@dataclass
class Config:
    federal_tax_rate: Optional[float] = None
    state_tax_rate: Optional[float] = None
    state: Optional[str] = None
    last_updated: str = ""

    def is_valid(self):
        if not self.last_updated:
            return False
        try:
            updated_dt = datetime.fromisoformat(self.last_updated)
            return datetime.now() - updated_dt < timedelta(days=30)
        except (ValueError, TypeError):
            return False

    @classmethod
    def load(cls):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r") as f:
                    data = json.load(f)
                    return cls(**data)
            except (json.JSONDecodeError, TypeError, IOError):
                pass
        return cls()

    def save(self):
        data = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
        data["last_updated"] = datetime.now().isoformat()
        with open(CONFIG_PATH, "w") as f:
            json.dump(data, f)


def get_fund_data(
    url: str = "https://moneymarket.fun/data/fundYields.json",
) -> Optional[List[Dict[str, Any]]]:
    """Retrieves fund data from a specified URL."""
    try:
        with console.status("[bold green]Fetching fund data..."):
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
    except requests.RequestException as e:
        console.print(f"[bold red]Error:[/bold red] Failed to retrieve data: {e}")
        return None


def display_top_funds(funds: List[Dict[str, Any]], investment_amount: float):
    table = Table(
        title="[bold blue]Top 5 Money Market Funds[/bold blue]",
        box=box.ROUNDED,
        header_style="bold magenta",
        show_lines=True,
    )
    table.add_column("Rank", justify="center")
    table.add_column("Ticker", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("After-Tax Yield", justify="right")
    table.add_column("Tax-Equiv Yield", justify="right")
    table.add_column("Annual Dist", justify="right", style="green")

    for i, fund in enumerate(funds[:5], start=1):
        table.add_row(
            str(i),
            fund["ticker"],
            fund["name"],
            f"{fund['after_tax_yield']:.2f}%",
            f"{fund['tax_equivalent_yield']:.2f}%",
            f"${investment_amount * fund['after_tax_yield'] / 100:,.2f}",
        )
    console.print(table)


def get_tax_info(args: argparse.Namespace, config: Config) -> Tuple[float, float, str]:
    state = (
        args.state
        or config.state
        or Prompt.ask(
            "Enter your [bold]State Abbreviation[/bold] (e.g., NY, CA, WA)"
        ).upper()
    )

    if args.federal_tax_rate is not None and args.state_tax_rate is not None:
        return args.federal_tax_rate / 100, args.state_tax_rate / 100, state

    if config.is_valid() and not any([args.federal_tax_rate, args.state_tax_rate]):
        last_upd = datetime.fromisoformat(config.last_updated).strftime("%Y-%m-%d")
        if Confirm.ask(f"Reuse saved settings from {last_upd}?"):
            return config.federal_tax_rate, config.state_tax_rate, state

    if Confirm.ask("Would you like to estimate tax rates based on income?"):
        income = FloatPrompt.ask("Enter your [bold]Annual Taxable Income[/bold] ($)")
        filing_status = Prompt.ask(
            "Filing Status", choices=["single", "married"], default="single"
        )

        fed_rate = get_marginal_rate(income, FEDERAL_BRACKETS[filing_status])
        state_brackets = STATE_TAX_DATA.get(state, [(0, 0.05)])
        state_rate = get_marginal_rate(income, state_brackets)

        console.print(
            f"Estimated Rates: Federal [bold]{fed_rate * 100:.1f}%[/bold], State [bold]{state_rate * 100:.1f}%[/bold]"
        )
        if not Confirm.ask("Use these rates?"):
            fed_rate = FloatPrompt.ask("Enter Federal Tax Rate (%)") / 100
            state_rate = FloatPrompt.ask("Enter State Tax Rate (%)") / 100
    else:
        fed_rate = (
            args.federal_tax_rate or FloatPrompt.ask("Enter Federal Tax Rate (%)")
        ) / 100
        state_rate = (
            args.state_tax_rate or FloatPrompt.ask("Enter State Tax Rate (%)")
        ) / 100

    return fed_rate, state_rate, state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--federal_tax_rate", type=float)
    parser.add_argument("--state_tax_rate", type=float)
    parser.add_argument("--state", type=str)
    parser.add_argument("--investment_amount", type=float)
    parser.add_argument("--bank_apy", type=float)
    parser.add_argument("--issuer", type=str)
    args = parser.parse_args()

    console.clear()
    config = Config.load()
    fed_rate, state_rate, state = get_tax_info(args, config)
    inv_amt = args.investment_amount or FloatPrompt.ask("Enter Investment Amount ($)")

    bank_apy = args.bank_apy
    if bank_apy is None:
        bank_apy_input = Prompt.ask(
            "Enter [bold]Bank APY[/bold] (%) to compare against (optional)", default=""
        )
        if bank_apy_input:
            try:
                bank_apy = float(bank_apy_input)
            except ValueError:
                console.print(
                    "[yellow]Invalid input for APY, skipping comparison.[/yellow]"
                )

    issuer = args.issuer
    if issuer is None:
        issuer_input = Prompt.ask(
            "Enter [bold]Issuer Name[/bold] to filter by (optional)", default=""
        )
        issuer = issuer_input if issuer_input.strip() else None

    # Update and save config
    config.federal_tax_rate = fed_rate
    config.state_tax_rate = state_rate
    config.state = state
    config.save()

    console.print(
        Panel(
            f"Federal Tax: [bold]{fed_rate * 100:.1f}%[/bold] | State Tax: [bold]{state_rate * 100:.1f}%[/bold] ({state})\nInvestment: [bold]${inv_amt:,.2f}[/bold]",
            title="[bold]Optimizer Configuration[/bold]",
            box=box.ROUNDED,
        )
    )

    fund_data = get_fund_data()
    if not fund_data:
        return

    processed = sorted(
        [
            process_fund(f, state, fed_rate, state_rate)
            for f in fund_data
            if filter_funds(f, inv_amt, issuer)
        ],
        key=lambda x: x["tax_equivalent_yield"],
        reverse=True,
    )
    if not processed:
        console.print("[yellow]No funds found.[/yellow]")
        return
    display_top_funds(processed, inv_amt)

    if bank_apy:
        bank_yield = bank_apy * (1 - fed_rate)
        console.print(
            Panel(
                f"Bank After-tax Yield: [bold]{bank_yield:.2f}%[/bold]\nAnnual Dist: [bold]${inv_amt * bank_yield / 100:,.2f}[/bold]",
                title="[bold yellow]Bank Comparison[/bold yellow]",
                box=box.ROUNDED,
            )
        )


if __name__ == "__main__":
    main()
