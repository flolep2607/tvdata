import pandas as pd
from unittest.mock import patch
from tvdata import fetch_candles, fetch_timeframes, fetch_tickers

MOCK_CANDLES = [
    {"timestamp": 1, "open": 10, "high": 12, "low": 9, "close": 11, "volume": 100},
    {"timestamp": 2, "open": 11, "high": 13, "low": 10, "close": 12, "volume": 110},
]

MOCK_TIMEFRAMES = ["1m", "5m", "1h"]
MOCK_TICKERS = ["AAPL", "GOOG"]


@patch("tvdata.requests.get")
def test_fetch_candles(mock_get):
    mock_get.return_value.json.side_effect = [MOCK_CANDLES, []]
    mock_get.return_value.raise_for_status = lambda: None
    df = fetch_candles("AAPL", "1m", 0, 2, chunk_size=2, api_url="http://mock.api")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert set(df.columns) == set(MOCK_CANDLES[0].keys())


@patch("tvdata.requests.get")
def test_fetch_timeframes(mock_get):
    mock_get.return_value.json.return_value = MOCK_TIMEFRAMES
    mock_get.return_value.raise_for_status = lambda: None
    tfs = fetch_timeframes("http://mock.api")
    assert tfs == MOCK_TIMEFRAMES


@patch("tvdata.requests.get")
def test_fetch_tickers(mock_get):
    mock_get.return_value.json.return_value = MOCK_TICKERS
    mock_get.return_value.raise_for_status = lambda: None
    tks = fetch_tickers("http://mock.api")
    assert tks == MOCK_TICKERS
