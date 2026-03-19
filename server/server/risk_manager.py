import os

class RiskManager:
    @staticmethod
    def validate_entry(webhook_data: dict) -> tuple[bool, str]:
        """Pre-trade validation before sending order to Delta"""
        required = ["symbol", "side", "qty", "price", "type", "strategy_id"]
        for field in required:
            if field not in webhook_data:
                return False, f"Missing field: {field}"
        
        # Validate strategy ID
        expected_id = os.getenv("STRATEGY_ID")
        if webhook_data.get("strategy_id") != expected_id:
            return False, "Invalid strategy_id"
        
        # Validate qty > 0
        try:
            qty = float(webhook_data["qty"])
            if qty <= 0:
                return False, "Qty must be > 0"
        except (ValueError, TypeError):
            return False, "Invalid qty format"
        
        # Validate price > 0
        try:
            price = float(webhook_data["price"])
            if price <= 0:
                return False, "Price must be > 0"
        except (ValueError, TypeError):
            return False, "Invalid price format"
        
        return True, "OK"
