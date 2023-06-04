import requests
import websocket
import time
import logging
logging.basicConfig(level=logging.INFO)

# WebSocket Stream Client
from binance.websocket.spot.websocket_stream import SpotWebsocketStreamClient

def message_handler(_, message):
    logging.info(message)


logging.info("opening ws connection")
my_client = SpotWebsocketStreamClient(on_message=message_handler)

# Subscribe to a single symbol stream
my_client.agg_trade(symbol="btcusdt")
time.sleep(5)
logging.info("closing ws connection")
my_client.stop()
