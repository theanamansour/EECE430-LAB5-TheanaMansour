from decimal import Decimal

from django.test import TestCase

from .models import Item
from .tools import (
    add_item,
    calculate_price,
    check_stock,
    list_items,
    remove_stock,
    update_price,
)


class InventoryToolTests(TestCase):
    def setUp(self):
        Item.objects.create(name="Chocolate Bar", quantity=10, price=Decimal("2.50"))

    def test_check_stock_returns_quantity_and_price(self):
        self.assertEqual(
            check_stock("chocolate bar"),
            {"name": "Chocolate Bar", "quantity": 10, "price": "2.50"},
        )

    def test_list_items_returns_price(self):
        self.assertEqual(
            list_items(),
            {
                "items": [
                    {"name": "Chocolate Bar", "quantity": 10, "price": "2.50"}
                ]
            },
        )

    def test_restock_without_price_preserves_existing_price(self):
        result = add_item("Chocolate Bar", 2)
        self.assertEqual(result["quantity"], 12)
        self.assertEqual(result["price"], "2.50")

    def test_new_item_without_price_uses_default(self):
        result = add_item("Nails", 5)
        self.assertEqual(result["price"], "0.00")

    def test_add_item_with_price(self):
        result = add_item("Nails", 5, 1.25)
        self.assertEqual(
            result,
            {"name": "Nails", "quantity": 5, "price": "1.25", "created": True},
        )

    def test_update_price_does_not_change_quantity(self):
        result = update_price("Chocolate Bar", 3.75)
        self.assertEqual(
            result,
            {"name": "Chocolate Bar", "quantity": 10, "price": "3.75"},
        )
        self.assertEqual(Item.objects.get(name="Chocolate Bar").quantity, 10)

    def test_update_price_rejects_invalid_values(self):
        self.assertIn("error", update_price("", 1))
        self.assertIn("error", update_price("Chocolate Bar", -1))
        self.assertIn("error", update_price("Chocolate Bar", "not a number"))
        self.assertIn("error", update_price("Missing Item", 1))
        self.assertEqual(Item.objects.get(name="Chocolate Bar").price, Decimal("2.50"))

    def test_add_item_rejects_invalid_values(self):
        self.assertIn("error", add_item("", 1, 1))
        self.assertIn("error", add_item("Nails", 0, 1))
        self.assertIn("error", add_item("Nails", -1, 1))
        self.assertIn("error", add_item("Nails", 1, -1))
        self.assertIn("error", add_item("Nails", 1, "not a number"))
        self.assertIn("error", add_item("Nails", 1, "100000000"))
        self.assertIn("error", add_item("N" * 101, 1, 1))
        self.assertFalse(Item.objects.filter(name="Nails").exists())

    def test_remove_stock_rejects_invalid_quantity(self):
        self.assertIn("error", remove_stock("Chocolate Bar", 0))
        self.assertIn("error", remove_stock("Chocolate Bar", -1))
        self.assertEqual(Item.objects.get(name="Chocolate Bar").quantity, 10)

    def test_remove_stock_rejects_more_than_available(self):
        result = remove_stock("Chocolate Bar", 11)
        self.assertIn("error", result)
        self.assertEqual(Item.objects.get(name="Chocolate Bar").quantity, 10)

    def test_missing_item_returns_error(self):
        self.assertIn("error", check_stock("Missing Item"))

    def test_vat_calculation_uses_stored_price(self):
        result = check_stock("Chocolate Bar")
        total = Decimal(result["price"]) * 3 * Decimal("1.10")
        self.assertEqual(total, Decimal("8.2500"))

    def test_calculate_price_with_price_upgrade(self):
        Item.objects.create(name="Notebook", quantity=5, price=Decimal("4.20"))

        result = calculate_price("notebooks", 4, 60)

        self.assertEqual(
            result,
            {
                "name": "Notebook",
                "requested_quantity": 4,
                "quantity_in_stock": 5,
                "enough_stock": True,
                "original_unit_price": "4.20",
                "percentage_change": "60",
                "adjusted_unit_price": "6.72",
                "total": "26.88",
            },
        )

    def test_calculate_price_rejects_invalid_values(self):
        self.assertIn("error", calculate_price("Chocolate Bar", 0, 10))
        self.assertIn("error", calculate_price("Chocolate Bar", 1, -101))
        self.assertIn("error", calculate_price("Chocolate Bar", 1, "invalid"))
        self.assertIn("error", calculate_price("Missing Item", 1, 10))

    def test_calculate_price_defaults_to_one_item(self):
        result = calculate_price("Chocolate Bar", percentage_change=10)

        self.assertEqual(result["requested_quantity"], 1)
        self.assertEqual(result["adjusted_unit_price"], "2.75")
        self.assertEqual(result["total"], "2.75")
