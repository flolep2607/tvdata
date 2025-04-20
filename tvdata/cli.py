import asyncio
from functools import wraps

import click
from rich.console import Console
from rich.table import Table
from rich import box

from .settings import settings
from .core.client import Client, DEFAULT_API_URL

console = Console()


@click.group()
def main():
    pass


def syncify(f):
    """This simple decorator converts an async function into a sync function,
    allowing it to work with Click.
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@main.command(help=f"Display the current installed version of {settings.project_name}.")
def version():
    from . import _version

    console.print(f"[bold green]{settings.project_name}[/bold green] - [yellow]{_version.version}[/yellow]")


@main.command()
@click.option("--api-url", default=DEFAULT_API_URL, show_default=True, help="Base URL of the API")
@click.argument("symbol")
@click.argument("timeframe")
@click.option("--start", type=int, default=None, help="Start timestamp (inclusive, seconds; optional)")
@click.option("--end", type=int, default=None, help="End timestamp (exclusive, seconds; optional)")
@click.option("--chunk-size", default=100, show_default=True, help="Number of candles per request")
@click.option("--csv", default=None, help="Path to export CSV file (optional)")
def candles(api_url, symbol, timeframe, start, end, chunk_size, csv):
    """Fetch candles and optionally export as CSV."""
    import csv as _csv

    client = Client(api_url=api_url)
    # Determine start/end; use raw streaming if any is missing
    if start is None or end is None:
        # Raw stream via SSE when no range is specified
        if csv:

            async def _stream_and_write():
                with open(csv, "w", newline="") as f:
                    writer = _csv.writer(f)
                    writer.writerow(["timestamp", "open", "high", "close", "low", "volume"])
                    async for row in client.stream_raw_candles(symbol, timeframe, chunk_size):
                        writer.writerow(row)

            asyncio.run(_stream_and_write())
            console.print(f"[green]Exported raw streamed candles to {csv}[/green]")
        else:
            print(",".join(["timestamp", "open", "high", "close", "low", "volume"]))

            async def _stream_into_table():
                async for row in client.stream_raw_candles(symbol, timeframe, chunk_size):
                    print(",".join([str(x) for x in row]))

            asyncio.run(_stream_into_table())
        # End raw streaming block
    else:
        df = client.fetch_candles(symbol, timeframe, start, end, chunk_size)
        if csv:
            df.to_csv(csv, index=False)
            console.print(f"[green]Exported candles to {csv}[/green]")
        else:
            if df.empty:
                console.print("[yellow]No candles found.[/yellow]")
            else:
                table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
                for col in df.columns:
                    table.add_column(str(col))
                for row in df.itertuples(index=False):
                    table.add_row(*[str(x) for x in row])
                console.print(table)


@main.command()
@click.option("--api-url", default=DEFAULT_API_URL, show_default=True, help="Base URL of the API")
def timeframes(api_url):
    """List available timeframes from the API."""
    client = Client(api_url=api_url)
    tfs = client.fetch_timeframes()
    if not tfs:
        console.print("[yellow]No timeframes found.[/yellow]")
    else:
        table = Table(box=box.SIMPLE)
        table.add_column("Timeframe", style="cyan")
        for tf in tfs:
            table.add_row(str(tf))
        console.print(table)


@main.command()
@click.option("--api-url", default=DEFAULT_API_URL, show_default=True, help="Base URL of the API")
def tickers(api_url):
    """List available tickers from the API."""
    client = Client(api_url=api_url)
    tks = client.fetch_tickers()
    if not tks:
        console.print("[yellow]No tickers found.[/yellow]")
    else:
        table = Table(box=box.SIMPLE)
        table.add_column("Ticker", style="green")
        for tk in tks:
            table.add_row(str(tk))
        console.print(table)


if __name__ == "__main__":
    main()
