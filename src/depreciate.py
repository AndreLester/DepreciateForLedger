#!/usr/bin/env python3
"""Generate Ledger transactions for an asset depreciation schedule."""

import codecs
import datetime
import optparse
import os
import platform
import sys

import Depreciation
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta


def _parse_date(value):
    if isinstance(value, datetime.datetime):
        return value
    if isinstance(value, datetime.date):
        return datetime.datetime.combine(value, datetime.time())
    return parse(value)


def _format_date(value):
    try:
        return _parse_date(value).strftime("%Y/%m/%d").strip()
    except (TypeError, ValueError, OverflowError):
        return datetime.date.today().strftime("%Y/%m/%d")


def _period_delta(period_type):
    period_type = period_type.lower().strip()
    if period_type in ("months", "month"):
        return relativedelta(months=1)
    if period_type in ("days", "day"):
        return relativedelta(days=1)
    return relativedelta(years=1)


def generate_transactions(
    method="straight",
    cost=0,
    residual=0,
    asset="Assets:Default Asset",
    expense="Equity:Expenses:Depreciation Expense",
    payment="Assets:Checking",
    periods=10,
    date=None,
    note="Asset Purchase",
    period_type="years",
    currency="$",
):
    """Return Ledger journal entries for an asset and its depreciation.

    ``date`` accepts a date, datetime, or a date string. ``periods`` is the
    number of depreciation entries, and ``period_type`` is days, months, or
    years.
    """
    if cost <= 0:
        raise ValueError("cost must be greater than zero")
    if periods <= 0:
        raise ValueError("periods must be greater than zero")
    if residual < 0 or residual > cost:
        raise ValueError("residual must be between zero and cost")
    if not asset.strip() or not expense.strip() or not payment.strip():
        raise ValueError("asset, expense, and payment accounts are required")

    if date is None:
        date = datetime.date.today()
    start_date = _parse_date(date)
    transactionobj = Depreciation.DepreciationSchedule(
        method, periods, cost, residual
    )
    transactionlist = transactionobj.Schedule()
    newline = "\r\n" if platform.system() == "Windows" else "\n"
    currency = currency.strip()
    note = note.strip()
    asset = asset.strip()

    transactions = [
        _format_date(start_date) + " * " + note,
        "\t" + asset + "\t\t" + currency + str(round(cost, 2)),
        "\t" + payment.strip(),
    ]
    active_date = start_date
    date_delta = _period_delta(period_type)
    for amount in transactionlist:
        active_date += date_delta
        transactions.extend(
            [
                active_date.strftime("%Y/%m/%d") + " * " + note,
                "\t"
                + expense.strip()
                + "\t\t"
                + currency
                + str(amount),
                "\t" + asset + ":Accumulated Depreciation",
            ]
        )
    return newline.join(transactions)


def save_file(transaction, filename):
    filename = os.path.abspath(os.path.expanduser(filename.strip()))
    with codecs.open(filename, "a" if os.path.isfile(filename) else "w", "utf-8") as output:
        if os.path.isfile(filename) and output.tell() > 0:
            output.write("\r\n" if platform.system() == "Windows" else "\n")
        output.write(transaction)
    print("Saved File!")


def main(argv=None):
    desc = "This tool allows you to create a depreciation schedule for Ledger"
    parser = optparse.OptionParser(description=desc)
    todaysdate = datetime.date.today().strftime("%Y/%m/%d")
    accounting = optparse.OptionGroup(parser, "Accounting Options")
    accounting.add_option(
        "--method", "-m", dest="method",
        help="Depreciation method: DDB, SUM, straight, or mixed",
        default="straight", metavar='"straight"'
    )
    accounting.add_option(
        "--cost", "-c", dest="cost", type="float", default=0,
        help="Cost of the asset you want to depreciate", metavar='"1000"'
    )
    accounting.add_option(
        "--periods", "-p", dest="periods", type="int", default=10,
        help="Number of periods to depreciate over", metavar='"10"'
    )
    accounting.add_option(
        "--periodtype", "-t", dest="ptype", default="years",
        help="Type of periods: days, months, or years", metavar='"years"'
    )
    accounting.add_option(
        "--residual", "-r", dest="residual", type="float", default=0,
        help="Residual (scrap) value of the asset", metavar='"100"'
    )
    accounting.add_option(
        "--asset", "-a", dest="asset", default="Assets:Default Asset",
        help="Asset account", metavar='"Assets:Computers"'
    )
    accounting.add_option(
        "--expense", "-e", dest="expense",
        default="Equity:Expenses:Depreciation Expense",
        help="Depreciation expense account"
    )
    accounting.add_option(
        "--payment", "-o", dest="payment", default="Assets:Checking",
        help="Account used to buy the asset"
    )
    accounting.add_option(
        "--date", "-d", dest="date", default=todaysdate,
        help="Date of asset purchase", metavar='"' + todaysdate + '"'
    )
    accounting.add_option(
        "--note", "-n", dest="note", default="Asset Purchase",
        help="Memo line note", metavar='"Asset Purchase"'
    )

    output = optparse.OptionGroup(parser, "Output Options")
    output.add_option(
        "--currency", dest="currency", default="$",
        help="Currency character in output", metavar='"$"'
    )
    output.add_option(
        "--save", "-s", dest="savefile", default="",
        help="Save output to a file", metavar='"<File Path>"'
    )
    parser.add_option_group(accounting)
    parser.add_option_group(output)
    options, _arguments = parser.parse_args(argv)
    try:
        transactions = generate_transactions(
            method=options.method,
            cost=options.cost,
            residual=options.residual,
            asset=options.asset,
            expense=options.expense,
            payment=options.payment,
            periods=options.periods,
            date=options.date,
            note=options.note,
            period_type=options.ptype,
            currency=options.currency,
        )
    except (ValueError, TypeError) as error:
        parser.error(str(error))
    if options.savefile.strip():
        save_file(transactions, options.savefile)
    else:
        print(transactions)
    return 0


if __name__ == "__main__":
    sys.exit(main())
