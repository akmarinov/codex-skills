---
name: bg-tax-filing
description: "Bulgarian NRA annual personal income tax filing workflow. Use when preparing, checking, or correcting a Bulgarian tax declaration from broker, ETF, stock, crypto, rent, dividend, sale, or foreign-asset documents; deciding which NRA appendices to use; extracting data from broker PDFs/HTML/CSV; generating Appendix 8 import files; or estimating missed tax and compliance risk by year."
---

# BG Tax Filing

## Ground Rules

- Treat this as high-stakes tax/legal work: verify current-year rules from official NRA/law sources before giving filing instructions.
- Make concrete date assumptions explicit: tax year, filing deadline, and whether dates are past or future.
- Separate facts extracted from documents from legal interpretation.
- Do not optimize for concealment. If the user asks about missed prior years, quantify tax exposure and recommend voluntary correction/consulting NRA or a tax professional.
- Preserve user files. Create new derived workbooks/reports instead of overwriting originals.

## Core Workflow

1. Identify the tax year, country of tax residence, platforms, and document paths.
2. Inventory documents with `rg --files`, then extract structured data:
   - PDFs: try `pdftotext`; if unavailable use Python `pypdf`.
   - HTML exports: parse with Python or bundled scripts.
   - XLSX imports: inspect the zipped XML if `openpyxl` is unavailable.
3. Classify every item into a filing bucket:
   - Rent from Bulgarian real estate: Appendix 4, code `401`, with 10% statutory expenses.
   - Foreign shares/ETF holdings at 31 Dec: Appendix 8, Part I.
   - Foreign permanent establishment/base/real estate: Appendix 8, Part II.
   - Foreign dividends/liquidation proceeds: Appendix 8, Part III.
   - Taxable sales of assets/financial instruments and crypto: Appendix 5.
   - Non-taxable regulated-market sales: usually Appendix 13 if reporting them voluntarily/informationally.
   - Crypto only held, with no sale/exchange/spend/staking: normally no appendix.
4. Reconcile holdings:
   - For Appendix 8 Part I, use acquisition date and acquisition cost, not year-end market value.
   - If a position has multiple lots, prefer importing one row per remaining lot/date.
   - For broker summaries, compare computed remaining quantities against year-end positions before producing an import file.
5. Calculate dividends:
   - Convert EUR to BGN at fixed `1.95583`.
   - For other currencies, use BNB fixing for the payment date and cite how the rate was obtained.
   - For foreign dividends, default tax is 5% unless an applicable treaty/tax-credit method changes the result.
6. Calculate sales:
   - Use FIFO unless documents or Bulgarian rules require another method.
   - Compute proceeds, acquisition cost, fees when allowed, gain/loss, and tax only on positive taxable gains.
   - For EU/EEA regulated-market securities, verify execution venue before treating gains as non-taxable.
7. Produce a filing pack:
   - Appendix-by-appendix instructions.
   - Tables ready for NRA portal entry.
   - Import-ready XLSX/CSV when the portal accepts imports.
   - A "not filed" list for items intentionally excluded, with rationale.
   - Residual risks and missing documents.

## Appendix 8 Practical Notes

- Part I is informational for shares and fund units held abroad as of 31 Dec. It asks for kind, country, count, acquisition date/year, acquisition cost in original currency, and BGN equivalent.
- Use `Акции` for company shares and `Дялове` for ETF/UCITS/fund units.
- The country is usually the issuer/fund domicile country from ISIN, not the broker country.
- Part II is only for foreign permanent establishment, fixed base, or foreign real estate. Leave it blank for ordinary broker/crypto holdings.
- Part III code `8141` is for foreign dividends. If no foreign tax was withheld and no double-tax method is applied, method code `3` is usually appropriate; column 12 is 5% of the BGN gross income for that row.

## Broker Patterns

- Finax/ETFmatic:
  - Monthly/yearly statements may show holdings and market values, but not full acquisition cost.
  - Use the Transactions page/export for all-time `BUY`/`SELL` rows.
  - Run `scripts/parse_finax_transactions.py` on saved Finax transaction HTML to compute open lots, Appendix 8 Part I rows, dividends, and FIFO realized gains.
- IBKR:
  - Use Activity Statement, Dividend Report, Tax Documents, and Flex Query if many trades exist.
  - Open Positions alone is not enough for Appendix 8 Part I if acquisition cost/date are missing.
- Revolut:
  - Stock P&L reports with zero sells do not prove holdings/dividends.
  - Crypto statements with no transactions/staking usually produce no filing entry.

## Bundled Resources

- Read [references/bulgaria-nra.md](references/bulgaria-nra.md) when giving Bulgarian NRA portal instructions, especially Appendix 8 column mapping and risk notes.
- Use `scripts/parse_finax_transactions.py` for saved Finax transaction HTML exports:

```bash
python3 scripts/parse_finax_transactions.py path/to/Transactions.html --tax-year 2025 --out-dir /tmp/bg-tax
```

The script writes `finax-appendix8-part1.csv`, `finax-open-lots.csv`, `finax-dividends.csv`, `finax-realized-sales.csv`, and `finax-summary.json`.
