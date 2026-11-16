"""Characterization tests: they pin CURRENT behavior (including quirks) so a refactor can't change it.

Run:  python -m unittest -v      (from labs/legacy-invoice)
"""
import unittest

import invoice


def item(type_, price, qty, name="item"):
    return {"type": type_, "price": price, "qty": qty, "name": name}


class CalcCharacterizationTests(unittest.TestCase):
    def setUp(self):
        invoice.discount_log.clear()

    def test_small_order_pays_shipping_no_tax_outside_listed_states(self):
        self.assertEqual(invoice.calc([item("book", 10, 2)], "regular", "TX"), 25.99)

    def test_free_shipping_over_50(self):
        self.assertEqual(invoice.calc([item("toy", 60, 1)], "regular", "TX"), 60.0)

    def test_book_bulk_discount_at_10(self):
        self.assertEqual(invoice.calc([item("book", 10, 10)], "regular", "TX"), 90.0)

    def test_food_bulk_discount_at_10(self):
        self.assertEqual(invoice.calc([item("food", 10, 10)], "regular", "TX"), 95.0)

    def test_electronics_quirk_no_discount_at_exactly_10(self):
        # QUIRK: electronics uses `> 10` while other categories use `>= 10`. Preserve it in a refactor.
        self.assertEqual(invoice.calc([item("electronics", 10, 10)], "regular", "TX"), 100.0)

    def test_electronics_discount_above_10(self):
        self.assertEqual(invoice.calc([item("electronics", 10, 11)], "regular", "TX"), 106.7)

    def test_gold_discount_and_florida_tax(self):
        self.assertEqual(invoice.calc([item("toy", 100, 1)], "gold", "FL"), 95.4)

    def test_silver_discount_and_georgia_tax(self):
        self.assertEqual(invoice.calc([item("toy", 100, 1)], "silver", "GA"), 98.8)

    def test_save10_applies_after_customer_discount_only_if_over_100(self):
        self.assertEqual(invoice.calc([item("toy", 120, 1)], "gold", "NY", "SAVE10"), 101.92)
        self.assertEqual(invoice.calc([item("toy", 110, 1)], "gold", "NY", "SAVE10"), 102.96)

    def test_halfship_coupon(self):
        self.assertEqual(invoice.calc([item("toy", 10, 1)], "regular", "TX", "HALFSHIP"), 13.0)

    def test_discount_log_side_effect(self):
        invoice.calc([item("toy", 100, 1)], "gold", "TX")
        invoice.calc([item("toy", 100, 1)], "silver", "TX")
        invoice.calc([item("toy", 100, 1)], "regular", "TX")
        self.assertEqual(invoice.discount_log, [("gold", 90.0), ("silver", 95.0)])

    def test_empty_order(self):
        self.assertEqual(invoice.calc([], "regular", "FL"), 5.99)


class PrintInvoiceCharacterizationTests(unittest.TestCase):
    def test_print_invoice_format(self):
        order = [item("book", 10, 10, "Clean Code"), item("electronics", 5, 2, "USB cable")]
        expected = "\n".join([
            "Clean Code           x 10       90.00",
            "USB cable            x  2       10.00",
            "--------------------------------------",
            "TOTAL                          100.00",
        ])
        self.assertEqual(invoice.print_invoice(order, "regular", "TX"), expected)


if __name__ == "__main__":
    unittest.main()
