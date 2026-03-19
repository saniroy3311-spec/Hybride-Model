import time
import threading
from state import PositionState
from delta_engine import DeltaEngine

class TrailingEngine:
    def __init__(self, delta_engine: DeltaEngine):
        self.delta = delta_engine
        self.running = False
        self.thread = None

    def start(self, symbol, entry_price, entry_atr, sl_dist, tp_dist, side, qty, order_id):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(
            target=self._run,
            args=(symbol, entry_price, entry_atr, sl_dist, tp_dist, side, qty, order_id),
            daemon=True
        )
        self.thread.start()

    def _run(self, symbol, entry_price, entry_atr, sl_dist, tp_dist, side, qty, order_id):
        atr = float(entry_atr)
        stages = [1.0, 2.0, 3.0, 4.0, 5.0]  # Configurable via input
        current_stage = 0
        max_profit = 0.0

        while self.running and PositionState.is_open():
            # Fetch current mark price (simplified - extend with real API call)
            current_price = self._get_mark_price(symbol)
            if not current_price:
                time.sleep(1)
                continue

            # Calculate profit
            if side == "buy":
                profit = (current_price - entry_price) * qty
                unrealized_sl = entry_price - (sl_dist * atr)
            else:
                profit = (entry_price - current_price) * qty
                unrealized_sl = entry_price + (sl_dist * atr)

            # Track max profit for trailing
            if profit > max_profit:
                max_profit = profit

            # Advance trail stages
            for i, stage in enumerate(stages[current_stage+1:], start=current_stage+1):
                if max_profit >= stage * atr * qty:
                    current_stage = i
                    # Move SL to breakeven + stage offset
                    if side == "buy":
                        new_sl = entry_price + (stage * atr * 0.5)  # 50% trail
                    else:
                        new_sl = entry_price - (stage * atr * 0.5)
                    self.delta.update_stop_loss(order_id, symbol, new_sl)
                    PositionState.update_trail(current_stage, max_profit)
                    print(f"🔄 Trail Stage {current_stage} | New SL: {new_sl}")
                    break

            # Check TP hit
            if (side == "buy" and current_price >= entry_price + tp_dist * atr) or \
               (side == "sell" and current_price <= entry_price - tp_dist * atr):
                print(f"✅ TP Hit @ {current_price}")
                self.stop()
                break

            # Check SL hit (safety)
            if (side == "buy" and current_price <= unrealized_sl) or \
               (side == "sell" and current_price >= unrealized_sl):
                print(f"🛑 SL Hit @ {current_price}")
                self.stop()
                break

            time.sleep(1)  # Update every second

    def _get_mark_price(self, symbol):
        # TODO: Replace with real Delta API mark price endpoint
        # For now, return None to skip iteration (placeholder)
        return None

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
