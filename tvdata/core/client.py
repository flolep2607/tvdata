from typing import Iterator, List, Dict, Any
import pandas as pd
import requests

DEFAULT_API_URL: str = "https://candles.macrofinder.flolep.fr"


class Client:
    def __init__(self, api_url: str = DEFAULT_API_URL):
        self.api_url = api_url

    def fetch_candles(
        self,
        symbol: str,
        timeframe: str,
        start: int,
        end: int,
        chunk_size: int = 100,
    ) -> pd.DataFrame:
        """
        Fetch candle data from the API using pagination and return as a Pandas DataFrame.
        """
        all_candles: List[Dict[str, Any]] = []
        page: int = 1
        headers: List[str] = []
        first = True
        while True:
            params: Dict[str, Any] = {
                "ticker": symbol,
                "timeframe": timeframe,
                "from": start,
                "to": end,
                "limit": chunk_size,
                "page": page,
            }
            response = requests.get(f"{self.api_url}/candles", params=params)
            response.raise_for_status()
            data: Any = response.json()
            if first:
                if isinstance(data, dict) and "headers" in data:
                    headers = data["headers"]
                first = False
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
        if headers:
            return pd.DataFrame(all_candles, columns=headers)
        return pd.DataFrame(all_candles)

    def stream_candles(
        self,
        symbol: str,
        timeframe: str,
        start: int,
        end: int,
        chunk_size: int = 100,
    ) -> Iterator[List[Dict[str, Any]]]:
        """
        Stream candle data from the API using pagination (generator).
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
            response = requests.get(f"{self.api_url}/candles", params=params)
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

    def fetch_timeframes(self) -> List[str]:
        """
        Fetch available timeframes from the API.
        """
        response = requests.get(f"{self.api_url}/timeframes")
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and "timeframes" in data:
            return data["timeframes"]
        return data  # type: ignore[return-value]

    def fetch_tickers(self) -> List[str]:
        """
        Fetch available tickers from the API.
        """
        response = requests.get(f"{self.api_url}/tickers")
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and "tickers" in data:
            return data["tickers"]
        return data  # type: ignore[return-value]
