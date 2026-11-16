"""Legacy invoice calculator: a deliberately smelly refactoring target.

Known smells (don't tell students up front; let the AI find them):
long function, duplicated branches, magic numbers, global mutable state,
stringly-typed parameters, duplicated logic between functions, `!= None`.

It also contains one behavioral QUIRK that a refactor must *preserve*
(and flag), not silently "fix". See the README.
"""

discount_log = []


def calc(order, customer_type, state, coupon=None):
    total = 0
    for item in order:
        if item["type"] == "book":
            price = item["price"] * item["qty"]
            if item["qty"] >= 10:
                price = price * 0.9
            total = total + price
        elif item["type"] == "food":
            price = item["price"] * item["qty"]
            if item["qty"] >= 10:
                price = price * 0.95
            total = total + price
        elif item["type"] == "electronics":
            price = item["price"] * item["qty"]
            if item["qty"] > 10:
                price = price * 0.97
            total += price
        else:
            price = item["price"] * item["qty"]
            total += price

    if customer_type == "gold":
        total = total - total * 0.1
        discount_log.append(("gold", total))
    elif customer_type == "silver":
        total = total - total * 0.05
        discount_log.append(("silver", total))

    if coupon != None:
        if coupon == "SAVE10":
            if total > 100:
                total = total - 10

    if state == "FL":
        tax = total * 0.06
    elif state == "GA":
        tax = total * 0.04
    elif state == "NY":
        tax = total * 0.04
    else:
        tax = 0

    if total > 50:
        ship = 0
    else:
        ship = 5.99
    if coupon == "HALFSHIP":
        ship = ship / 2

    return round(total + tax + ship, 2)


def print_invoice(order, customer_type, state, coupon=None):
    lines = []
    for item in order:
        price = item["price"] * item["qty"]
        if item["type"] == "book" and item["qty"] >= 10:
            price = price * 0.9
        elif item["type"] == "food" and item["qty"] >= 10:
            price = price * 0.95
        elif item["type"] == "electronics" and item["qty"] > 10:
            price = price * 0.97
        lines.append("%-20s x%3d  %10.2f" % (item["name"], item["qty"], price))
    lines.append("-" * 38)
    lines.append("%-26s %10.2f" % ("TOTAL", calc(order, customer_type, state, coupon)))
    return "\n".join(lines)
