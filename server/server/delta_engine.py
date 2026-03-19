import requests
import hmac
import hashlib
import time
import os
from dotenv import load_dotenv

load_dotenv()

class DeltaEngine:
    def __init__(self):
        self.api_key = os.getenv("DELTA_API_KEY")
        self.api_secret = os.getenv("DELTA_API_SECRET")
        self.base_url = "https://api.delta.exchange" if os.getenv("USE_TESTNET") == "false" else "https://testnet-api.delta.exchange"
        self.headers = {"X-DELTA-API-KEY": self.api_key}

    def _sign(self, method, path, body=""):
        timestamp = str(int(time.time()))
        message = timestamp + method + path + body
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature, timestamp

    def place_limit_order(self, symbol, side, qty, price, stop_loss=None, take_profit=None):
        path = "/v2/orders"
        payload = {
            "product_id": self._get_product_id(symbol),
            "side": side,
            "order_type": "limit",
            "price": str(price),
            "quantity": str(qty),
            "post_only": True
        }
        import json
        body = json.dumps(payload, separators=(',', ':'))
        sig, ts = self._sign("POST", path, body)
        headers = self.headers | {
            "X-DELTA-SIGNATURE": sig,
            "X-DELTA-TIMESTAMP": ts,
            "Content-Type": "application/json"
        }
        resp = requests.post(self.base_url + path, headers=headers, data=body)
        return resp.json()

    def update_stop_loss(self, order_id, symbol, new_sl_price):
        path = f"/v2/orders/{order_id}/modify"
        payload = {
            "product_id": self._get_product_id(symbol),
            "stop_loss": str(new_sl_price)
        }
        import json
        body = json.dumps(payload, separators=(',', ':'))
        sig, ts = self._sign("PUT", path, body)
        headers = self.headers | {
            "X-DELTA-SIGNATURE": sig,
            "X-DELTA-TIMESTAMP": ts,
            "Content-Type": "application/json"
        }
        resp = requests.put(self.base_url + path, headers=headers, data=body)
        return resp.json()

    def cancel_order(self, order_id):
        path = f"/v2/orders/{order_id}/cancel"
        sig, ts = self._sign("POST", path)
        headers = self.headers | {
            "X-DELTA-SIGNATURE": sig,
            "X-DELTA-TIMESTAMP": ts
        }
        resp = requests.post(self.base_url + path, headers=headers)
        return resp.json()

    def _get_product_id(self, symbol):
        # Map common symbols to Delta product IDs (extend as needed)
        mapping = {
            "BTCUSD.P": "1",
            "ETHUSD.P": "2",
            "BTCUSD": "10",
            "ETHUSD": "11"
        }
        return mapping.get(symbol, "1")
