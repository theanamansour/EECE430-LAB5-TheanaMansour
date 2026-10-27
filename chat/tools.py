from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from .models import Item


def _find_item(name):
    """Find an item, accepting a simple plural such as 'notebooks'."""
    item = Item.objects.filter(name__iexact=name).first()
    if item is None and name.lower().endswith("s"):
        item = Item.objects.filter(name__iexact=name[:-1]).first()
    return item


def check_stock(name):
    """Look up how many of an item we have and its price."""
    if not isinstance(name, str) or not name.strip():
        return {"error": "Item name cannot be empty."}
    name = name.strip()
    item = Item.objects.filter(name__iexact=name).first()
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}
    return {
        "name": item.name,
        "quantity": item.quantity,
        "price": format(item.price, ".2f"),
    }


def calculate_price(name, quantity=1, percentage_change=0):
    """Calculate a quantity's price after a percentage increase or decrease."""
    if not isinstance(name, str) or not name.strip():
        return {"error": "Item name cannot be empty."}
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
        return {"error": "Quantity must be a positive integer."}
    if isinstance(percentage_change, bool):
        return {"error": "Percentage change must be a number no lower than -100."}

    try:
        percentage = Decimal(str(percentage_change))
    except (InvalidOperation, TypeError, ValueError):
        return {"error": "Percentage change must be a number no lower than -100."}
    if not percentage.is_finite() or percentage < Decimal("-100"):
        return {"error": "Percentage change must be a number no lower than -100."}

    name = name.strip()
    item = _find_item(name)
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}

    money = Decimal("0.01")
    multiplier = Decimal("1") + percentage / Decimal("100")
    adjusted_unit_price = (item.price * multiplier).quantize(
        money, rounding=ROUND_HALF_UP
    )
    total = (adjusted_unit_price * quantity).quantize(money, rounding=ROUND_HALF_UP)

    return {
        "name": item.name,
        "requested_quantity": quantity,
        "quantity_in_stock": item.quantity,
        "enough_stock": quantity <= item.quantity,
        "original_unit_price": format(item.price, ".2f"),
        "percentage_change": format(percentage, "f"),
        "adjusted_unit_price": format(adjusted_unit_price, ".2f"),
        "total": format(total, ".2f"),
    }


def list_items():
    """Return every item in the inventory."""
    items = Item.objects.all()
    return {
        "items": [
            {
                "name": i.name,
                "quantity": i.quantity,
                "price": format(i.price, ".2f"),
            }
            for i in items
        ]
    }


def add_item(name, quantity, price=None):
    """Create a new item, or add to an existing one's stock."""
    if not isinstance(name, str) or not name.strip():
        return {"error": "Item name cannot be empty."}
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
        return {"error": "Quantity must be a positive integer."}
    name = name.strip()
    if len(name) > 100:
        return {"error": "Item name must be 100 characters or fewer."}

    price_value = None
    if price is not None:
        if isinstance(price, bool):
            return {"error": "Price must be a non-negative number."}
        try:
            price_value = Decimal(str(price))
        except (InvalidOperation, TypeError, ValueError):
            return {"error": "Price must be a non-negative number."}
        if not price_value.is_finite() or price_value < 0:
            return {"error": "Price must be a non-negative number."}
        try:
            price_value = price_value.quantize(Decimal("0.01"))
        except InvalidOperation:
            return {"error": "Price must be a non-negative number."}
        if price_value > Decimal("99999999.99"):
            return {"error": "Price must be no more than 99999999.99."}

    item = Item.objects.filter(name__iexact=name).first()
    if item is not None:
        item.quantity += quantity
        if price_value is not None:
            item.price = price_value
        item.save()
        return {
            "name": item.name,
            "quantity": item.quantity,
            "price": format(item.price, ".2f"),
            "created": False,
        }
    item = Item.objects.create(
        name=name,
        quantity=quantity,
        price=price_value if price_value is not None else 0,
    )
    return {
        "name": item.name,
        "quantity": item.quantity,
        "price": format(item.price, ".2f"),
        "created": True,
    }


def update_price(name, price):
    """Update the unit price of an existing item."""
    if not isinstance(name, str) or not name.strip():
        return {"error": "Item name cannot be empty."}
    name = name.strip()

    if isinstance(price, bool):
        return {"error": "Price must be a non-negative number."}
    try:
        price_value = Decimal(str(price))
    except (InvalidOperation, TypeError, ValueError):
        return {"error": "Price must be a non-negative number."}
    if not price_value.is_finite() or price_value < 0:
        return {"error": "Price must be a non-negative number."}
    try:
        price_value = price_value.quantize(Decimal("0.01"))
    except InvalidOperation:
        return {"error": "Price must be a non-negative number."}
    if price_value > Decimal("99999999.99"):
        return {"error": "Price must be no more than 99999999.99."}

    item = Item.objects.filter(name__iexact=name).first()
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}
    item.price = price_value
    item.save()
    return {
        "name": item.name,
        "quantity": item.quantity,
        "price": format(item.price, ".2f"),
    }


def remove_stock(name, quantity):
    """Take a quantity out of stock."""
    if not isinstance(name, str) or not name.strip():
        return {"error": "Item name cannot be empty."}
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
        return {"error": "Quantity must be a positive integer."}
    name = name.strip()
    item = Item.objects.filter(name__iexact=name).first()
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}
    if quantity > item.quantity:
        return {
            "error": f"Cannot remove {quantity}. Only {item.quantity} in stock.",
            "name": item.name,
            "quantity": item.quantity,
        }
    item.quantity -= quantity
    item.save()
    return {"name": item.name, "quantity": item.quantity}


def delete_item(name):
    """Remove an item from the inventory entirely."""
    if not isinstance(name, str) or not name.strip():
        return {"error": "Item name cannot be empty."}
    name = name.strip()
    item = Item.objects.filter(name__iexact=name).first()
    if item is None:
        return {"error": f"No item named '{name}' exists in the inventory."}
    item.delete()
    return {"deleted": name}


TOOL_DECLARATIONS = [
    {
        "type": "function",
        "name": "check_stock",
        "description": "Look up the current quantity and unit price of a single item in the inventory. Use this whenever the user asks whether something is in stock, how many there are, or how much it costs.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the item, e.g. 'Hammer'.",
                },
            },
            "required": ["name"],
        },
    },
    {
        "type": "function",
        "name": "list_items",
        "description": "Return every item in the inventory with its quantity and unit price. Use this when the user asks what is in stock generally, or asks for a list, rather than about one specific item.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function",
        "name": "add_item",
        "description": "Add stock to the inventory. If the item does not exist it is created; if it already exists the quantity is added to the existing total. A supplied unit price sets the item's price; omitting it preserves an existing price. Use this for restocking and for new deliveries, not for changing a price without adding stock.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the item, e.g. 'Hammer'.",
                },
                "quantity": {
                    "type": "integer",
                    "description": "How many units to add. Must be positive.",
                },
                "price": {
                    "type": "number",
                    "description": "The non-negative price of one unit, e.g. 2.50. Optional.",
                },
            },
            "required": ["name", "quantity"],
        },
    },
    {
        "type": "function",
        "name": "calculate_price",
        "description": "Calculate the total price for a requested quantity using the stored unit price, optionally after a percentage change. Always use this for questions asking for the price or cost of multiple units, or involving a percentage increase, upgrade, markup, tax, discount, or reduction. Pass increases/upgrades/markups/taxes as a positive percentage and discounts/reductions as a negative percentage. For example, a 60% price upgrade is percentage_change=60, while a 20% discount is percentage_change=-20.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The item name, singular or simple plural, e.g. 'Notebook' or 'notebooks'.",
                },
                "quantity": {
                    "type": "integer",
                    "description": "The number of units whose total price is requested. Must be positive. Omit it when the user does not state a quantity; the tool will use one unit.",
                },
                "percentage_change": {
                    "type": "number",
                    "description": "Signed percentage adjustment. Use 60 for a 60% increase/upgrade and -20 for a 20% discount. Use 0 when there is no adjustment.",
                },
            },
            "required": ["name", "percentage_change"],
        },
    },
    {
        "type": "function",
        "name": "update_price",
        "description": "Update the unit price of an existing item without changing its stock quantity. Use this when the user asks to change, set, or correct an item's price without adding stock.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the existing item, e.g. 'Hammer'.",
                },
                "price": {
                    "type": "number",
                    "description": "The new non-negative unit price, e.g. 3.25.",
                },
            },
            "required": ["name", "price"],
        },
    },
    {
        "type": "function",
        "name": "remove_stock",
        "description": "Reduce the quantity of an existing item. Use this when items are sold, shipped or used. This does NOT delete the item; it only lowers the number.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the item, e.g. 'Hammer'.",
                },
                "quantity": {
                    "type": "integer",
                    "description": "How many units to remove. Must be positive.",
                },
            },
            "required": ["name", "quantity"],
        },
    },
    {
        "type": "function",
        "name": "delete_item",
        "description": "Permanently remove an item and its record from the inventory entirely. This is destructive. Only use it when the user clearly wants the item gone, not when they want to reduce its quantity.",
        "parameters": {
            "type": "object",
            "properties": {

                "name": {
                    "type": "string",
                    "description": "The name of the item to delete.",
                },
            },
            "required": ["name"],
        },
    },
]

TOOL_FUNCTIONS = {
    "check_stock": check_stock,
    "calculate_price": calculate_price,
    "list_items": list_items,
    "add_item": add_item,
    "update_price": update_price,
    "remove_stock": remove_stock,
    "delete_item": delete_item,
}
