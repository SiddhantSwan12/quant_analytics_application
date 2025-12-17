import asyncio
import json
import logging
import threading
import time
from datetime import datetime
import websockets
from typing import List, Callable, Optional
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketDataClient:
    def __init__(self, storage_engine, symbols: List[str], mode: str = 'LIVE', replay_file: Optional[str] = None):
        self.storage = storage_engine
        self.symbols = [s.lower() for s in symbols]
        self.mode = mode.upper()
        self.replay_file = replay_file
        self.running = False
        self.thread = None
        self._loop = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info(f"Market Data Client started in {self.mode} mode.")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        logger.info("Market Data Client stopped.")

    def _run_loop(self):
        if self.mode == 'LIVE':
            asyncio.run(self._live_ingestion())
        elif self.mode == 'REPLAY':
            self._replay_ingestion()

    async def _live_ingestion(self):
        base_url = "wss://fstream.binance.com/stream?streams="
        streams = "/".join([f"{s}@trade" for s in self.symbols])
        url = f"{base_url}{streams}"

        logger.info(f"Connecting to {url}")

        while self.running:
            try:
                async with websockets.connect(url) as ws:
                    logger.info("Connected to Binance Futures WS")
                    while self.running:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        if 'data' in data:
                            self._process_trade_msg(data['data'])
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await asyncio.sleep(5)

    def _process_trade_msg(self, trade: dict):
        
        normalized = {
            'symbol': trade['s'],
            'ts': datetime.fromtimestamp(trade['T'] / 1000.0).isoformat(),
            'price': float(trade['p']),
            'size': float(trade['q'])
        }
        print(f"TICK: {normalized['symbol']} @ {normalized['price']} ({normalized['size']})")
        self.storage.store_tick(normalized)

    def _replay_ingestion(self):
        """
        Simulates a live feed from a file.
        Format: NDJSON or CSV
        """
        if not self.replay_file:
            logger.error("No replay file provided.")
            return

        logger.info(f"Starting replay from {self.replay_file}")
        
        try:
            
            with open(self.replay_file, 'r') as f:
                for line in f:
                    if not self.running:
                        break
                    
                    try:
                        record = json.loads(line)
                        if 'e' in record and record['e'] == 'trade':
                             self._process_trade_msg(record)
                        else:
                             self.storage.store_tick(record)
                        
                        
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Replay error: {e}")
            
        logger.info("Replay finished.")
