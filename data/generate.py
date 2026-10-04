#!/usr/bin/env python3
"""Generate reconciliation test data: platform.csv + bank.csv.

200 charges grouped into 8 aggregated deposits, minus fees, minus 3 refunds.
2 differences and 1 out-of-window deposit are seeded on purpose so the flow has
something to catch and classify. Deterministic (fixed seed) so the demo repeats.
"""
import csv
import random
from datetime import date, timedelta

random.seed(42)  # deterministic: same data every run
BASE = date(2026, 1, 6)
FEE_RATE = 0.029  # Stripe-ish

platform, bank = [], []
tx_id = 0


def charge(day, amount):
    global tx_id
    tx_id += 1
    fee = round(amount * FEE_RATE, 2)
    platform.append({"id": f"ch_{tx_id}", "date": day.isoformat(), "type": "charge",
                     "amount": amount, "fee": fee, "ref": f"ord_{tx_id}"})
    return amount - fee


# 8 deposits, ~25 charges each = 200 charges
for d in range(8):
    day = BASE + timedelta(days=d * 3)
    net = 0.0
    for _ in range(25):
        net += charge(day, round(random.uniform(10, 300), 2))
    # 3 refunds total, on the first 3 deposits
    if d < 3:
        global_amt = round(random.uniform(10, 80), 2)
        tx_id += 1
        platform.append({"id": f"re_{tx_id}", "date": day.isoformat(), "type": "refund",
                         "amount": -global_amt, "fee": 0.0, "ref": f"ref_{tx_id}"})
        net -= global_amt

    payout = round(net, 2)
    payout_day = day + timedelta(days=2)

    # seed 2 differences: deposits 4 and 5 land a few cents off
    if d in (4, 5):
        payout += 0.07
    # seed 1 out-of-window: deposit 7 lands 10 days late (> ±3d)
    if d == 7:
        payout_day = day + timedelta(days=10)

    platform.append({"id": f"po_{d}", "date": payout_day.isoformat(), "type": "payout",
                     "amount": round(payout, 2), "fee": 0.0, "ref": f"po_{d}"})
    bank.append({"date": payout_day.isoformat(), "amount": round(payout, 2),
                 "description": f"STRIPE PAYOUT po_{d}"})


def write(path, rows, cols):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def demo():
    charges = [r for r in platform if r["type"] == "charge"]
    refunds = [r for r in platform if r["type"] == "refund"]
    payouts = [r for r in platform if r["type"] == "payout"]
    assert len(charges) == 200, len(charges)
    assert len(refunds) == 3, len(refunds)
    assert len(payouts) == 8 == len(bank)
    # the out-of-window payout is >3 days after its charges
    late = [b for b in bank if b["description"].endswith("po_7")][0]
    assert date.fromisoformat(late["date"]) - (BASE + timedelta(days=21)) > timedelta(days=3)
    print("ok: 200 charges, 3 refunds, 8 deposits, 2 diffs + 1 out-of-window seeded")


if __name__ == "__main__":
    write("platform.csv", platform, ["id", "date", "type", "amount", "fee", "ref"])
    write("bank.csv", bank, ["date", "amount", "description"])
    demo()
