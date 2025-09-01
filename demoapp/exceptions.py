from rest_framework.exceptions import ValidationError


class NegativeQuantityError(ValidationError):
    """Custom validation error for negative inventory quantities"""

    def __init__(self, quantity, message="Quantity cannot be negative"):
        self.quantity = quantity
        self.detail = {
            "error": message,
            "quantity_received": float(quantity),
        }
        super().__init__(self.detail)
