from typing import Iterator, List, Dict, Any, Optional, Tuple, AsyncIterator
import pandas as pd
import requests
import json
from aiosseclient import aiosseclient  # type: ignore[import]
import threading
import logging
import signal
from tqdm import tqdm

DEFAULT_API_URL: str = "https://candles.macrofinder.flolep.fr"


# Configuration du logging
logger = logging.getLogger("tvdata")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class ThreadSafeCounter:
    # constructor
    def __init__(self, _counter: int = 0):
        self._counter = _counter
        self._lock = threading.Lock()

    def increment(self) -> int:
        with self._lock:
            self._counter += 1
            return self._counter

    def value(self):
        with self._lock:
            return self._counter


class Client:
    def __init__(self, api_url: str = DEFAULT_API_URL, log_level: int = logging.INFO):
        self.api_url = api_url
        logger.setLevel(log_level)

    def fetch_timestamp_range(self, symbol: str, timeframe: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Fetch the min and max timestamp available for a ticker and timeframe.

        Args:
            symbol (str): Ticker symbol.
            timeframe (str): Timeframe string (e.g. '1d', '1h').

        Returns:
            tuple: (min_timestamp, max_timestamp) in seconds, or (None, None) if no data available
        """
        logger.debug(f"Fetching timestamp range for {symbol} {timeframe}")
        try:
            params = {
                "ticker": symbol,
                "timeframe": timeframe,
            }
            response = requests.get(f"{self.api_url}/candles/range", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            min_ts = data.get("range", {}).get("min")
            max_ts = data.get("range", {}).get("max")

            logger.debug(f"Timestamp range for {symbol} {timeframe}: {min_ts} to {max_ts}")
            return (min_ts, max_ts)
        except Exception as e:
            logger.warning(f"Error fetching timestamp range: {e}")
            return (None, None)

    def fetch_candles(
        self,
        symbol: str,
        timeframe: str,
        start_ts: int,
        end_ts: int,
        chunk_size: int = 10_000,
        show_progress: bool = True,
        log_level: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Fetch candle data from the API using parallel pagination (5 threads max) and return as a Pandas DataFrame.
        Uses a simple thread-safe counter for page numbers and stops when a page returns less than chunk_size items.
        The progress bar is based on the maximum timestamp fetched so far.

        Args:
            symbol (str): Ticker symbol.
            timeframe (str): Timeframe string (e.g. '1d', '1h').
            start_ts (int): Start timestamp (inclusive, in seconds).
            end_ts (int): End timestamp (exclusive, in seconds).
            chunk_size (int): Number of candles per request (default 10_000).
            show_progress (bool): Show tqdm progress bar (default True).
            log_level (int): Logging level for this operation (default: use instance level).
        Returns:
            pd.DataFrame: DataFrame containing the candles.
        """
        # Configure logging level for this operation
        if log_level is not None:
            old_level = logger.level
            logger.setLevel(log_level)

        logger.info(f"Fetching {symbol} {timeframe} data from {start_ts} to {end_ts}")

        # Get actual available timestamp range for more accurate progress bar
        available_min, available_max = self.fetch_timestamp_range(symbol, timeframe)

        if available_min is not None and available_max is not None:
            # Adjust requested range to available data
            actual_start = max(start_ts, available_min)
            actual_end = min(end_ts, available_max)

            if actual_start > actual_end:
                logger.warning(f"No data available in requested range: {start_ts} to {end_ts}")
                if log_level is not None:
                    logger.setLevel(old_level)
                return pd.DataFrame()

            if actual_start != start_ts or actual_end != end_ts:
                logger.info(f"Adjusting request to available data range: {actual_start} to {actual_end}")
                start_ts = actual_start
                end_ts = actual_end

        headers: List[str] = []
        all_candles: List[Dict[str, Any]] = []

        # Thread coordination
        page_counter = ThreadSafeCounter()
        results_lock = threading.Lock()
        found_last_page = threading.Event()
        stop_event = threading.Event()  # Événement pour signaler l'arrêt aux workers
        results = {}
        max_fetched_ts = start_ts
        total_range = max(1, end_ts - start_ts)
        pbar = tqdm(total=total_range, disable=not show_progress, desc="Fetching candles (time)")
        pbar_lock = threading.Lock()

        logger.debug(f"Initialized fetch with page_counter={page_counter.value()}, total_range={total_range}")

        # Gestionnaire de signal pour Ctrl+C
        original_sigint_handler = signal.getsignal(signal.SIGINT)

        def sigint_handler(sig, frame):
            logger.info("Ctrl+C détecté! Arrêt des workers en cours...")
            stop_event.set()  # Signal à tous les workers de s'arrêter
            # On ne restore pas encore le gestionnaire original pour éviter les interruptions pendant la fermeture

        # Installer le gestionnaire de signal
        signal.signal(signal.SIGINT, sigint_handler)

        def worker():
            thread_id = threading.get_ident()
            logger.debug(f"[Thread-{thread_id}] Worker thread started")
            nonlocal page_counter, headers, max_fetched_ts
            fail = False
            current_page = None

            while not (found_last_page.is_set() or stop_event.is_set()):  # Vérifier aussi stop_event
                # Get next page to fetch
                if not fail:
                    current_page = page_counter.increment()
                    logger.debug(f"[Thread-{thread_id}] Fetching page {current_page}")
                else:
                    logger.warning(f"[Thread-{thread_id}] Retrying page {current_page} after failure")

                # Sortir si arrêt demandé
                if stop_event.is_set():
                    logger.debug(f"[Thread-{thread_id}] Stop requested, exiting")
                    break

                # Fetch the page
                params = {
                    "ticker": symbol,
                    "timeframe": timeframe,
                    "from": start_ts,
                    "to": end_ts,
                    "limit": chunk_size,
                    "page": current_page,
                }
                try:
                    logger.debug(f"[Thread-{thread_id}] GET {self.api_url}/candles with params={params}")
                    response = requests.get(f"{self.api_url}/candles", params=params, timeout=10)  # Ajout d'un timeout
                    response.raise_for_status()
                    data = response.json()
                    logger.debug(f"[Thread-{thread_id}] Received response for page {current_page}")

                    # Sortir si arrêt demandé même après une requête réussie
                    if stop_event.is_set():
                        logger.debug(f"[Thread-{thread_id}] Stop requested after fetch, exiting")
                        break

                    local_headers = []
                    if current_page == 1:
                        if isinstance(data, dict) and "headers" in data:
                            local_headers = data["headers"]
                            logger.debug(f"[Thread-{thread_id}] Found headers: {local_headers}")

                    candles = data.get("candles") if isinstance(data, dict) else data
                    if candles is None:
                        candles = data.get("data") if isinstance(data, dict) else data
                    if isinstance(candles, dict) and "candles" in candles:
                        candles = candles["candles"]

                    candles = candles or []
                    logger.debug(f"[Thread-{thread_id}] Page {current_page} returned {len(candles)} candles")

                    # Store results
                    with results_lock:
                        results[current_page] = candles
                        if current_page == 1 and local_headers:
                            headers.extend(local_headers)
                            logger.debug(f"[Thread-{thread_id}] Stored headers: {headers}")
                        logger.debug(f"[Thread-{thread_id}] Stored {len(candles)} candles for page {current_page}")

                    # Update progress bar if we have candles
                    if candles:
                        # Log les premiers éléments pour voir la structure des données
                        logger.debug(f"[Thread-{thread_id}] First candle sample: {candles[0]}")

                        # Les données sont sous forme de tableaux où l'indice 0 est le timestamp
                        try:
                            # Vérifie qu'on a bien des tableaux
                            if isinstance(candles[0], (list, tuple)):
                                # Extrait tous les timestamps (premier élément de chaque tableau)
                                all_ts_values = [c[0] for c in candles if len(c) > 0]
                                if all_ts_values:
                                    min_ts = min(all_ts_values)
                                    page_max_ts = max(all_ts_values)
                                    logger.debug(
                                        f"[Thread-{thread_id}] Page {current_page} timestamp range: {min_ts} to {page_max_ts}"
                                    )

                                    with pbar_lock:
                                        current_max = max_fetched_ts
                                        logger.debug(
                                            f"[Thread-{thread_id}] Current max_fetched_ts: {current_max}, new max: {page_max_ts}"
                                        )

                                        if page_max_ts > current_max:
                                            progress = min(page_max_ts, end_ts) - current_max
                                            logger.debug(f"[Thread-{thread_id}] Calculated progress: {progress}")

                                            max_fetched_ts = max(page_max_ts, current_max)
                                            if progress > 0:
                                                logger.info(
                                                    f"[Thread-{thread_id}] Updating progress bar: +{progress}, new max_ts={max_fetched_ts}"
                                                )
                                                pbar.update(progress)
                                            else:
                                                logger.warning(
                                                    f"[Thread-{thread_id}] No progress to update: {progress} <= 0"
                                                )
                                        else:
                                            logger.debug(
                                                f"[Thread-{thread_id}] No progress update needed: {page_max_ts} <= {current_max}"
                                            )
                                else:
                                    logger.warning(f"[Thread-{thread_id}] No valid timestamp values found in candles")
                            else:
                                logger.warning(f"[Thread-{thread_id}] Unexpected candle format: {type(candles[0])}")
                        except (IndexError, TypeError) as e:
                            logger.error(f"[Thread-{thread_id}] Error processing candle timestamps: {e}")

                    # Check if this is the last page
                    if len(candles) < chunk_size:
                        logger.info(f"[Thread-{thread_id}] Found last page: {current_page} with {len(candles)} candles")
                        found_last_page.set()
                    fail = False

                except Exception as e:
                    fail = True
                    logger.error(f"[Thread-{thread_id}] Error fetching page {current_page}: {e}")
                    # Si arrêt demandé, sortir même en cas d'erreur
                    if stop_event.is_set():
                        break

        # Start workers
        threads = []
        logger.info(f"Starting 5 worker threads for {symbol} {timeframe}")
        for i in range(5):  # 5 threads in parallel
            t = threading.Thread(target=worker, name=f"Worker-{i}")
            t.daemon = True
            t.start()
            threads.append(t)
            logger.debug(f"Started thread {i}: {t.name}")

        try:
            # Wait for all threads to finish
            for i, t in enumerate(threads):
                logger.debug(f"Waiting for thread {i}: {t.name}")
                while t.is_alive():
                    t.join(timeout=0.5)  # Petit timeout pour vérifier périodiquement stop_event
                    # Si un arrêt est demandé et qu'on attend encore des threads,
                    # on ne veut pas bloquer indéfiniment
                    if stop_event.is_set():
                        logger.debug(f"Stop requested while waiting for thread {i}")
                        break
                logger.debug(f"Thread {i}: {t.name} completed or timed out")
        except KeyboardInterrupt:
            # Si un autre KeyboardInterrupt se produit pendant l'attente des threads
            logger.warning("Second interrupt received, force stopping...")
            stop_event.set()
        finally:
            # Restaurer le gestionnaire de signal original
            signal.signal(signal.SIGINT, original_sigint_handler)

        # Si arrêt demandé, informer l'utilisateur
        if stop_event.is_set():
            logger.warning("Opération interrompue par l'utilisateur. Résultat partiel possible.")

        logger.info(f"All worker threads completed or stopped. Fetched {len(results)} pages")

        # Ensure progress bar completes or closes on interrupt
        with pbar_lock:
            if not stop_event.is_set() and max_fetched_ts < end_ts:
                remaining = end_ts - max_fetched_ts
                pbar.update(remaining)
                logger.debug(f"Updated final progress: +{remaining}")
            pbar.close()

        # Combine results in order
        total_candles = 0
        for page in sorted(results.keys()):
            page_candles = len(results[page])
            all_candles.extend(results[page])
            total_candles += page_candles
            logger.debug(f"Added {page_candles} candles from page {page}")

        logger.info(f"Total candles combined: {total_candles} from {len(results)} pages")

        # Reset logging level if changed for this operation
        if log_level is not None:
            logger.setLevel(old_level)

        # Create DataFrame
        if headers:
            return pd.DataFrame(all_candles, columns=headers)
        return pd.DataFrame(all_candles)

    def stream_candles(
        self,
        symbol: str,
        timeframe: str,
        start_ts: int,
        end_ts: int,
        chunk_size: int = 10_000,
    ) -> Iterator[List[Dict[str, Any]]]:
        """
        Stream candle data from the API using pagination (generator).
        """
        logger.info(f"Streaming {symbol} {timeframe} data from {start_ts} to {end_ts}")

        # Get actual available timestamp range
        available_min, available_max = self.fetch_timestamp_range(symbol, timeframe)

        if available_min is not None and available_max is not None:
            # Adjust requested range to available data
            actual_start = max(start_ts, available_min)
            actual_end = min(end_ts, available_max)

            if actual_start > actual_end:
                logger.warning(f"No data available in requested range: {start_ts} to {end_ts}")
                return

            if actual_start != start_ts or actual_end != end_ts:
                logger.info(f"Adjusting request to available data range: {actual_start} to {actual_end}")
                start_ts = actual_start
                end_ts = actual_end

        page: int = 1
        while True:
            params: Dict[str, Any] = {
                "ticker": symbol,
                "timeframe": timeframe,
                "from": start_ts,
                "to": end_ts,
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

    async def stream_raw_candles(
        self,
        symbol: str,
        timeframe: str,
        chunk_size: int = 200,
    ) -> AsyncIterator[Any]:
        """
        Stream raw candle data using SSE from the API dump raw endpoint.
        """
        url = f"{self.api_url}/candles/dump/raw"
        params = {"ticker": symbol, "timeframe": timeframe, "chunkSize": chunk_size}
        complete_url = f"{url}?{requests.compat.urlencode(params)}"
        # Asynchronously stream SSE events
        async for event in aiosseclient(complete_url, headers={"Accept": "text/event-stream"}):
            if event.event == "raw_chunk":
                try:
                    rows = json.loads(event.data)
                except json.JSONDecodeError:
                    logger.error(f"Error decoding raw_chunk data: {event.data}")
                    continue
                for row in rows:
                    yield row.values()
