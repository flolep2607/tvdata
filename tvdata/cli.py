import asyncio
from functools import wraps

import click

from .settings import settings
from .core.client import Client


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

    click.echo(f"{settings.project_name} - {_version.version}")


@main.command()
@click.option(
    "--api-url", default="http://candles.macrofinder.flolep.fr", show_default=True, help="Base URL of the API"
)
@click.argument("symbol")
@click.argument("timeframe")
@click.argument("start", type=int)
@click.argument("end", type=int)
@click.option("--chunk-size", default=100, show_default=True, help="Number of candles per request")
@click.option("--csv", default=None, help="Path to export CSV file (optional)")
def candles(api_url, symbol, timeframe, start, end, chunk_size, csv):
    """Fetch candles and optionally export as CSV."""
    client = Client(api_url=api_url)
    df = client.fetch_candles(symbol, timeframe, start, end, chunk_size)
    if csv:
        df.to_csv(csv, index=False)
        click.echo(f"Exported candles to {csv}")
    else:
        click.echo(df)


@main.command()
@click.option(
    "--api-url", default="http://candles.macrofinder.flolep.fr", show_default=True, help="Base URL of the API"
)
def timeframes(api_url):
    """List available timeframes from the API."""
    client = Client(api_url=api_url)
    tfs = client.fetch_timeframes()
    click.echo(tfs)


@main.command()
@click.option(
    "--api-url", default="http://candles.macrofinder.flolep.fr", show_default=True, help="Base URL of the API"
)
def tickers(api_url):
    """List available tickers from the API."""
    client = Client(api_url=api_url)
    tks = client.fetch_tickers()
    click.echo(tks)


if __name__ == "__main__":
    main()
