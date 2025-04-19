# TvData

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
from tvdata import fetch_candles, fetch_timeframes, fetch_tickers

df = fetch_candles(
    symbol="AAPL",
    timeframe="1m",
    start=1700000000,
    end=1700003600,
    chunk_size=100,
    api_url="http://candles.macrofinder.flolep.fr"
)
print(df)

# Get available timeframes
timeframes = fetch_timeframes("http://candles.macrofinder.flolep.fr")
print(timeframes)

# Get available tickers
tickers = fetch_tickers("http://candles.macrofinder.flolep.fr")
print(tickers)
```

See more in `examples/example_tvdata.py`.

### CLI

```bash
tvdata candles SYMBOL TIMEFRAME START END --csv output.csv
# Example:
tvdata candles AAPL 1m 1700000000 1700003600 --csv aapl_1m.csv

tvdata timeframes

tvdata tickers
```

## Development

- Clone the repository
- Install dependencies: `pip install -r requirements-dev.txt`
- Run tests: `pytest`
- Check typing: `mypy tvdata`

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
from tvdata import fetch_candles, fetch_timeframes, fetch_tickers

candles = fetch_candles(
    symbol="AAPL",
    timeframe="1m",
    start=1700000000,
    end=1700003600,
    chunk_size=100,
    api_url="http://candles.macrofinder.flolep.fr"
)
print(candles)

timeframes = fetch_timeframes("http://candles.macrofinder.flolep.fr")
print(timeframes)

tickers = fetch_tickers("http://candles.macrofinder.flolep.fr")
print(tickers)
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

## Développement

- Clonez le dépôt
- Installez les dépendances : `pip install -r requirements-dev.txt`
- Lancez les tests : `pytest`
- Vérifiez le typage : `mypy tvdata`

## Licence

MIT
