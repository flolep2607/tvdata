# TvData

[![PyPI](https://github.com/flolep2607/tvdata/actions/workflows/pypi.yaml/badge.svg)](https://github.com/flolep2607/tvdata/actions/workflows/pypi.yaml)

[🇫🇷 Version française](#-version-française)

A Python library and CLI for fetching and exporting financial candle data, timeframes, and tickers from your custom API.

## Features
- Fetch candle data in chunks and return as a Pandas DataFrame
- Export candle data as CSV via CLI
- List available timeframes and tickers
- **Type hints everywhere** for static analysis (compatible with mypy)
- **Examples available** in the `examples/` folder

## Installation

```bash
pip install TvData
```

## Usage

### Library

```python
from tvdata import Client

client = Client()

# Get available timeframes
timeframes = client.fetch_timeframes()
print(timeframes)

# Get available tickers
tickers = client.fetch_tickers()
print(tickers)

df = client.fetch_candles(
    symbol='BINANCE:BTCUSDT',
    timeframe='1',
    start=1700000000,
    end=1700003600,
    chunk_size=100,
)
print(df)
```

See more in `examples/example_tvdata.py`.

### CLI

```bash
tvdata candles SYMBOL TIMEFRAME START END --csv output.csv
# Example:
tvdata candles "BINANCE:BTCUSDT" "1" 1700000000 1700003600 --csv aapl_1m.csv

tvdata timeframes

tvdata tickers
```

## License

MIT

---

# 🇫🇷 Version française

Une bibliothèque Python et une CLI pour récupérer et exporter des données de chandeliers, timeframes et tickers depuis votre API personnalisée.

## Fonctionnalités
- Récupération des chandeliers en DataFrame Pandas (par lots)
- Export CSV via la CLI
- Liste des timeframes et tickers disponibles
- **Typage partout** pour l'analyse statique (compatible mypy)
- **Exemples** dans le dossier `examples/`

## Installation

```bash
pip install TvData
```

## Utilisation

### Librairie

```python
from tvdata import Client

client = Client()

# Récupérer les timeframes disponibles
timeframes = client.fetch_timeframes()
print(timeframes)

# Récupérer les tickers disponibles
tickers = client.fetch_tickers()
print(tickers)

df = client.fetch_candles(
    symbol='BINANCE:BTCUSDT',
    timeframe='1',
    start=1700000000,
    end=1700003600,
    chunk_size=100,
)
print(df)
```

Voir plus dans `examples/example_tvdata.py`.

### CLI

```bash
tvdata candles SYMBOL TIMEFRAME START END --csv output.csv
# Exemple :
tvdata candles AAPL 1m 1700000000 1700003600 --csv aapl_1m.csv

tvdata timeframes

tvdata tickers
```

## Licence

MIT
