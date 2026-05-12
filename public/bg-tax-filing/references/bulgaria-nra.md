# Bulgarian NRA Filing Reference

Use this as a working checklist, not as a substitute for current official guidance. Always browse official NRA/law sources for the filing year before final advice.

## Annual Checks

- Confirm the filing year and deadline for the annual declaration under Art. 50 ZDDFL.
- Confirm the current NRA form labels and appendix numbers.
- Confirm tax rates for dividends, capital gains, rent, and any relevant reliefs.
- Confirm whether a correction deadline has passed. NRA commonly allows one correcting declaration by 30 September of the following year.

## Appendix Selection

- Appendix 4:
  - Rent from immovable property, ordinary individual landlord: code `401`.
  - Taxable base normally reduces gross rent by 10% statutory expenses.
- Appendix 5:
  - Taxable sale/exchange of assets, securities, and crypto.
  - Crypto sale/exchange/spend may be taxable even if no fiat withdrawal occurred.
- Appendix 8:
  - Part I: foreign shares/fund units held at 31 December.
  - Part II: foreign permanent establishment/fixed base/real estate.
  - Part III: foreign dividends/liquidation proceeds and other listed foreign-source final-tax income.
- Appendix 13:
  - Informational reporting for non-taxable income, often used for non-taxable regulated-market securities sales if the user chooses to report them.

## Appendix 8 Part I

Portal/import columns commonly include:

- `Вид`: `Акции` for ordinary company shares, `Дялове` for ETFs/funds.
- `Държава`: issuer/fund domicile. Use ISIN prefix as a first clue, then verify the fund domicile if needed.
- `Брой акции`: quantity held as of 31 December.
- `Дата`: acquisition date/year. For multiple lots, prefer separate rows by acquisition date.
- `Обща цена (EUR)` or other currency: acquisition cost, not market value.
- `Обща цена (BGN)`: converted acquisition cost. EUR uses fixed `1.95583`.

Do not use year-end market value as acquisition cost unless the form/source explicitly asks for market value.

## Appendix 8 Part III Dividends

For ordinary foreign dividends:

- `Код вид доход`: usually `8141`.
- Method code:
  - `1` when using a tax credit method.
  - `2` for exemption with progression.
  - `3` when no double-tax method is applied.
- If foreign withholding tax is zero, columns for tax credit/recognized foreign tax remain zero.
- Column 12 is the Bulgarian final tax due. For ordinary dividends, calculate 5% of BGN gross income unless current rules say otherwise.

## Prior-Year Omissions

Handle missed filings calmly and numerically:

- Split by year and by income type.
- Distinguish informational omissions (holdings) from omitted taxable income (dividends, taxable gains, rent, crypto).
- Estimate missed tax and interest exposure separately from possible administrative fines.
- Criminal-risk thresholds relate to avoided tax, not portfolio value or proceeds. Verify current Penal Code thresholds before giving conclusions.
- Recommend contacting NRA or a tax professional when the correction deadline has passed or avoided tax may be material.

## Source Preference

Prefer these source types:

- NRA official pages and current forms.
- ZDDFL, DOPK, ZANN, and Penal Code text from official or stable legal sources.
- Broker primary documents.

Use blog posts only as secondary explanations and clearly label them as non-authoritative.

