import asyncio
from functools import wraps

import typer

from .settings import settings
from . import fetch_candles, fetch_timeframes, fetch_tickers

app = typer.Typer()


def syncify(f):
    """This simple decorator converts an async function into a sync function,
    allowing it to work with Typer.
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@app.command(help=f"Display the current installed version of {settings.project_name}.")
def version() -> None:
    from . import _version

    typer.echo(f"{settings.project_name} - {_version.version}")


@app.command()
def candles(
    api_url: str = typer.Option("http://candles.macrofinder.flolep.fr", help="Base URL of the API"),
    symbol: str = typer.Argument(..., help="Symbol to fetch candles for"),
    timeframe: str = typer.Argument(..., help="Timeframe to fetch"),
    start: int = typer.Argument(..., help="Start timestamp (inclusive)"),
    end: int = typer.Argument(..., help="End timestamp (exclusive)"),
    chunk_size: int = typer.Option(100, help="Number of candles per request"),
    csv: str = typer.Option(None, help="Path to export CSV file (optional)"),
) -> None:
    """Fetch candles and optionally export as CSV."""
    df = fetch_candles(symbol, timeframe, start, end, chunk_size, api_url)
    if csv:
        df.to_csv(csv, index=False)
        typer.echo(f"Exported candles to {csv}")
    else:
        typer.echo(df)


@app.command()
def timeframes(api_url: str = typer.Option("http://candles.macrofinder.flolep.fr", help="Base URL of the API")) -> None:
    """List available timeframes from the API."""
    tfs = fetch_timeframes(api_url)
    typer.echo(tfs)


@app.command()
def tickers(api_url: str = typer.Option("http://candles.macrofinder.flolep.fr", help="Base URL of the API")) -> None:
    """List available tickers from the API."""
    tks = fetch_tickers(api_url)
    typer.echo(tks)


if __name__ == "__main__":
    app()
