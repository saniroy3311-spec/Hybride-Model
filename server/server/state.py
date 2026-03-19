import threading
from datetime import datetime

class PositionState:
    _lock = threading.RLock()
    _state = {
        "open": False,
        "symbol": None,
        "side": None,
        "entry_price": None,
        "entry_atr": None,
        "qty": None,
        "order_id": None,
        "entry_time": None,
        "trail_stage": 0,
        "max_profit": 0.0
    }

    @classmethod
    def set_open(cls, symbol, side, price, atr, qty, order_id):
        with cls._lock:
            cls._state.update({
                "open": True,
                "symbol": symbol,
                "side": side,
                "entry_price": float(price),
                "entry_atr": float(atr),
                "qty": float(qty),
                "order_id": order_id,
                "entry_time": datetime.utcnow().isoformat(),
                "trail_stage": 0,
                "max_profit": 0.0
            })

    @classmethod
    def set_closed(cls):
        with cls._lock:
            cls._state.update({
                "open": False,
                "symbol": None,
                "side": None,
                "entry_price": None,
                "entry_atr": None,
                "qty": None,
                "order_id": None,
                "entry_time": None,
                "trail_stage": 0,
                "max_profit": 0.0
            })

    @classmethod
    def update_trail(cls, stage, max_profit):
        with cls._lock:
            cls._state["trail_stage"] = stage
            cls._state["max_profit"] = max_profit

    @classmethod
    def get(cls):
        with cls._lock:
            return cls._state.copy()

    @classmethod
    def is_open(cls):
        with cls._lock:
            return cls._state["open"]
