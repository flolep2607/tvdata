try:
    from . import _version

    __version__ = _version.__version__
except:  # noqa: E722
    __version__ = "0.0.0-dev"

import pandas as pd
import requests
from typing import Iterator, List, Dict, Any

DEFAULT_API_URL: str = "http://candles.macrofinder.flolep.fr"


def fetch_candles(
    symbol: str,
    timeframe: str,
    start: int,
    end: int,
    chunk_size: int = 100,
    api_url: str = DEFAULT_API_URL,
) -> pd.DataFrame:
    """
    Fetch candle data from the API using pagination and return as a Pandas DataFrame.
    :param symbol: Symbol for which to fetch candles.
    :param timeframe: Timeframe of the candles.
    :param start: Start timestamp.
    :param end: End timestamp.
    :param chunk_size: Number of candles to fetch per request (page size).
    :param api_url: Base URL of the API (default: candles.macrofinder.flolep.fr)
    :return: Pandas DataFrame containing the candle data.
    """
    all_candles: List[Dict[str, Any]] = []
    page: int = 1
    while True:
        params: Dict[str, Any] = {
            "ticker": symbol,
            "timeframe": timeframe,
            "from": start,
            "to": end,
            "limit": chunk_size,
            "page": page,
        }
        response = requests.get(f"{api_url}/candles", params=params)
        response.raise_for_status()
        data: Any = response.json()
        candles: Any = data.get("candles") if isinstance(data, dict) else data
        if candles is None:
            candles = data.get("data") if isinstance(data, dict) else data
        if isinstance(candles, dict) and "candles" in candles:
            candles = candles["candles"]
        if not candles:
            break
        all_candles.extend(candles)
        if len(candles) < chunk_size:
            break
        page += 1
    return pd.DataFrame(all_candles)


def stream_candles(
    symbol: str,
    timeframe: str,
    start: int,
    end: int,
    chunk_size: int = 100,
    api_url: str = DEFAULT_API_URL,
) -> Iterator[List[Dict[str, Any]]]:
    """
    Stream candle data from the API using pagination (generator).
    :param symbol: Symbol for which to fetch candles.
    :param timeframe: Timeframe of the candles.
    :param start: Start timestamp.
    :param end: End timestamp.
    :param chunk_size: Number of candles to fetch per request (page size).
    :param api_url: Base URL of the API (default: candles.macrofinder.flolep.fr)
    :yield: List of candle dicts per chunk.
    """
    page: int = 1
    while True:
        params: Dict[str, Any] = {
            "ticker": symbol,
            "timeframe": timeframe,
            "from": start,
            "to": end,
            "limit": chunk_size,
            "page": page,
        }
        response = requests.get(f"{api_url}/candles", params=params)
        response.raise_for_status()
        data: Any = response.json()
        candles: Any = data.get("candles") if isinstance(data, dict) else data
        if candles is None:
            candles = data.get("data") if isinstance(data, dict) else data
        if isinstance(candles, dict) and "candles" in candles:
            candles = candles["candles"]
        if not candles:
            break
        yield candles
        if len(candles) < chunk_size:
            break
        page += 1


def fetch_timeframes(api_url: str = DEFAULT_API_URL) -> List[str]:
    """
    Fetch available timeframes from the API.
    :param api_url: Base URL of the API (default: candles.macrofinder.flolep.fr)
    :return: List of available timeframes.
    """
    response = requests.get(f"{api_url}/timeframes")
    response.raise_for_status()
    return response.json()  # type: ignore[return-value]


def fetch_tickers(api_url: str = DEFAULT_API_URL) -> List[str]:
    """
    Fetch available tickers from the API.
    :param api_url: Base URL of the API (default: candles.macrofinder.flolep.fr)
    :return: List of available tickers.
    """
    response = requests.get(f"{api_url}/tickers")
    response.raise_for_status()
    return response.json()  # type: ignore[return-value]
