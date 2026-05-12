#!/usr/bin/env python3
"""Parse saved Finax Transactions HTML into tax-friendly summaries."""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


EUR_TO_BGN = 1.95583


ISIN_COUNTRIES_BG = {
    "DE": "Германия",
    "IE": "Ирландия",
    "LU": "Люксембург",
    "US": "САЩ",
}


@dataclass
class Trade:
    index: int
    date: date
    isin: str
    kind: str
    shares: float
    price: float
    value: float


@dataclass
class Dividend:
    date: date
    name: str
    amount_eur: float


def parse_eur(value: str) -> float:
    cleaned = (
        value.replace("€", "")
        .replace("\xa0", " ")
        .replace(" ", "")
        .replace(",", ".")
        .strip()
    )
    return float(cleaned)


def clean_cells(chunk: str) -> list[str]:
    cells = re.findall(r'<div class="[^"]*?">(.*?)</div>', chunk, re.S)
    cells = [re.sub(r"<[^>]+>", "", cell) for cell in cells]
    cells = [html.unescape(cell).replace("\xa0", " ").strip() for cell in cells]
    return [" ".join(cell.split()) for cell in cells if cell.strip()]


def parse_transactions(path: Path) -> tuple[list[Trade], list[Dividend]]:
    text = path.read_text(errors="ignore")
    marker = '<div class="flex flex-row gap-8 items-center border-b border-[#D2D1D1] py-4 finax-font-standard ">'
    parts = text.split(marker)
    trades: list[Trade] = []
    dividends: list[Dividend] = []

    for index, part in enumerate(parts[1:]):
        cells = clean_cells(part[:2500])
        if len(cells) >= 6 and cells[2] in {"BUY", "SELL"}:
            trades.append(
                Trade(
                    index=index,
                    date=datetime.strptime(cells[0], "%d.%m.%Y").date(),
                    isin=cells[1],
                    kind=cells[2],
                    shares=float(cells[3].replace(",", ".")),
                    price=parse_eur(cells[4]),
                    value=abs(parse_eur(cells[5])),
                )
            )
        elif len(cells) >= 4 and re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", cells[0]) and cells[1] == "DIVIDEND":
            dividends.append(
                Dividend(
                    date=datetime.strptime(cells[0], "%d.%m.%Y").date(),
                    name=cells[2],
                    amount_eur=parse_eur(cells[3]),
                )
            )

    return trades, dividends


def fifo_summaries(trades: list[Trade]) -> tuple[dict[str, deque[dict[str, float | date]]], dict[int, dict[str, float]]]:
    lots: dict[str, deque[dict[str, float | date]]] = defaultdict(deque)
    realized: dict[int, dict[str, float]] = defaultdict(lambda: {"proceeds_eur": 0.0, "cost_eur": 0.0, "gain_eur": 0.0, "sell_count": 0.0})

    for trade in sorted(trades, key=lambda item: (item.date, item.index)):
        if trade.kind == "BUY":
            lots[trade.isin].append({"date": trade.date, "shares": trade.shares, "cost": trade.value})
            continue

        remaining = trade.shares
        cost = 0.0
        while remaining > 1e-9 and lots[trade.isin]:
            lot = lots[trade.isin][0]
            lot_shares = float(lot["shares"])
            lot_cost = float(lot["cost"])
            if lot_shares <= remaining + 1e-9:
                cost += lot_cost
                remaining -= lot_shares
                lots[trade.isin].popleft()
            else:
                fraction = remaining / lot_shares
                cost_piece = lot_cost * fraction
                cost += cost_piece
                lot["shares"] = lot_shares - remaining
                lot["cost"] = lot_cost - cost_piece
                remaining = 0.0

        year = trade.date.year
        realized[year]["proceeds_eur"] += trade.value
        realized[year]["cost_eur"] += cost
        realized[year]["gain_eur"] += trade.value - cost
        realized[year]["sell_count"] += 1

    return lots, realized


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def country_for_isin(isin: str) -> str:
    return ISIN_COUNTRIES_BG.get(isin[:2], isin[:2])


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse saved Finax Transactions HTML.")
    parser.add_argument("html", type=Path)
    parser.add_argument("--tax-year", type=int, default=None)
    parser.add_argument("--out-dir", type=Path, default=Path("."))
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    trades, dividends = parse_transactions(args.html)
    lots, realized = fifo_summaries(trades)

    open_lot_rows: list[dict[str, object]] = []
    appendix8_rows: list[dict[str, object]] = []
    for isin, isin_lots in sorted(lots.items()):
        for lot in isin_lots:
            shares = float(lot["shares"])
            if shares <= 1e-8:
                continue
            cost_eur = float(lot["cost"])
            cost_eur_rounded = round(cost_eur, 2)
            cost_bgn_rounded = round(cost_eur_rounded * EUR_TO_BGN, 2)
            lot_date = lot["date"].isoformat()
            open_lot_rows.append(
                {
                    "isin": isin,
                    "date": lot_date,
                    "shares": round(shares, 8),
                    "cost_eur": cost_eur_rounded,
                    "cost_bgn": cost_bgn_rounded,
                }
            )
            appendix8_rows.append(
                {
                    "Вид": "Дялове",
                    "Държава": country_for_isin(isin),
                    "Брой акции": round(shares, 8),
                    "Дата": lot_date,
                    "Обща цена (EUR)": cost_eur_rounded,
                    "Обща цена (BGN)": cost_bgn_rounded,
                }
            )

    dividend_rows: list[dict[str, object]] = []
    for dividend in dividends:
        if args.tax_year is not None and dividend.date.year != args.tax_year:
            continue
        dividend_rows.append(
            {
                "date": dividend.date.isoformat(),
                "year": dividend.date.year,
                "name": dividend.name,
                "amount_eur": round(dividend.amount_eur, 2),
                "amount_bgn": round(dividend.amount_eur * EUR_TO_BGN, 2),
                "tax_bgn_5pct": round(dividend.amount_eur * EUR_TO_BGN * 0.05, 2),
            }
        )

    realized_rows: list[dict[str, object]] = []
    for year, summary in sorted(realized.items()):
        if args.tax_year is not None and year != args.tax_year:
            continue
        gain_eur = summary["gain_eur"]
        realized_rows.append(
            {
                "year": year,
                "sell_count": int(summary["sell_count"]),
                "proceeds_eur": round(summary["proceeds_eur"], 2),
                "cost_eur": round(summary["cost_eur"], 2),
                "gain_eur": round(gain_eur, 2),
                "gain_bgn": round(gain_eur * EUR_TO_BGN, 2),
                "tax_bgn_10pct_if_taxable": round(max(gain_eur * EUR_TO_BGN, 0) * 0.10, 2),
            }
        )

    write_csv(args.out_dir / "finax-open-lots.csv", open_lot_rows, ["isin", "date", "shares", "cost_eur", "cost_bgn"])
    write_csv(args.out_dir / "finax-appendix8-part1.csv", appendix8_rows, ["Вид", "Държава", "Брой акции", "Дата", "Обща цена (EUR)", "Обща цена (BGN)"])
    write_csv(args.out_dir / "finax-dividends.csv", dividend_rows, ["date", "year", "name", "amount_eur", "amount_bgn", "tax_bgn_5pct"])
    write_csv(args.out_dir / "finax-realized-sales.csv", realized_rows, ["year", "sell_count", "proceeds_eur", "cost_eur", "gain_eur", "gain_bgn", "tax_bgn_10pct_if_taxable"])

    summary = {
        "trade_count": len(trades),
        "dividend_count": len(dividends),
        "first_trade": min((trade.date.isoformat() for trade in trades), default=None),
        "last_trade": max((trade.date.isoformat() for trade in trades), default=None),
        "outputs": [
            "finax-open-lots.csv",
            "finax-appendix8-part1.csv",
            "finax-dividends.csv",
            "finax-realized-sales.csv",
        ],
    }
    (args.out_dir / "finax-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
