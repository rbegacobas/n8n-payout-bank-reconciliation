# Stripe payout to bank statement reconciliation with aggregated deposit splitting

An n8n workflow that answers the question every owner has and no dashboard answers:
*which sales make up this one bank deposit?*

## The problem

Stripe and PayPal don't deposit sale by sale. They deposit a net that bundles N
transactions minus fees, refunds and adjustments. The owner sees `$4,812.37` land in
the bank and has no idea which sales it came from. This flow splits each aggregated
deposit back into its parts and reconciles them against the bank statement.

## The chain

1. **Ingest A** — platform transactions (Stripe API or CSV export): charges, fees,
   refunds, adjustments, payouts.
2. **Ingest B** — bank statement CSV.
3. **Normalize** — both sources to one schema: date, amount, currency, reference,
   type, source.
4. **Deposit disaggregation** — each bank deposit is opened against the set of
   transactions that compose it. This is the node that matters.
5. **Matching** — exact by reference first; then by amount within a ±3-day window;
   then approximate by amount within a cent tolerance.
6. **Classify unmatched** — by reason: no bank counterpart, no platform counterpart,
   amount difference, outside window.
7. **Output** — a sheet with three tabs: reconciled, pending, differences.
8. **Summary** — one email/Slack message: total reconciled, total pending, largest
   difference.

## Decisions that show judgment

- Cent tolerance is configurable (currency-conversion rounding).
- Idempotency by transaction id: reprocessing the same file duplicates nothing.
- Refunds are their own signed lines, not adjustments to the original charge.
- Nothing is marked reconciled "by approximation" without recording the criterion used.

## Test data

`python3 data/generate.py` writes `platform.csv` and `bank.csv`:
200 transactions, 8 aggregated deposits, 3 refunds, 2 seeded differences, 1 outside
the date window. The seeded cases must show up classified by reason in tab 3.

## Demo

`demo/` — 2-minute screen recording of a run, subtitled.

## Usage

Import [`workflow.json`](workflow.json) into n8n, point ingest nodes at your CSVs or
Stripe credentials.
