from flask import Flask, request, jsonify
import json
import os
from dotenv import load_dotenv

from state import PositionState
from delta_engine import DeltaEngine
from trailing_engine import TrailingEngine
from risk_manager import RiskManager

load_dotenv()
app = Flask(__name__)

delta = DeltaEngine()
trailer = TrailingEngine(delta)

@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "server": "Shiva Hybrid v6.7",
        "position": PositionState.get()
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        print(f"📥 Webhook received: {json.dumps(data, indent=2)}")
        
        # Validate
        valid, msg = RiskManager.validate_entry(data)
        if not valid:
            return jsonify({"error": msg}), 400
        
        # Reject if position already open
        if PositionState.is_open():
            return jsonify({"error": "Position already open"}), 409
        
        # Parse fields
        symbol = data["symbol"]
        side = data["side"]
        qty = float(data["qty"])
        price = float(data["price"])
        sl_dist = float(data.get("sl_dist", 1.5))
        tp_dist = float(data.get("tp_dist", 3.0))
        atr = float(data.get("atr", 100))
        
        # Place limit order on Delta
        order_resp = delta.place_limit_order(
            symbol=symbol,
            side=side,
            qty=qty,
            price=price,
            stop_loss=price - (sl_dist * atr) if side == "buy" else price + (sl_dist * atr),
            take_profit=price + (tp_dist * atr) if side == "buy" else price - (tp_dist * atr)
        )
        
        if "error" in order_resp:
            return jsonify({"error": order_resp["error"]}), 500
        
        order_id = order_resp.get("result", {}).get("id")
        if not order_id:
            return jsonify({"error": "No order_id in response"}), 500
        
        # Update state
        PositionState.set_open(symbol, side, price, atr, qty, order_id)
        print(f"✅ ENTRY | {side.upper()} {qty} {symbol} @ LIMIT {price} | Order ID: {order_id}")
        
        # Start trailing engine
        trailer.start(symbol, price, atr, sl_dist, tp_dist, side, qty, order_id)
        
        return jsonify({"status": "ok", "order_id": order_id}), 200
        
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
