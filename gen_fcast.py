#!/usr/bin/env python3

from datetime import datetime, timedelta
import akshare as ak
import stock_pandas as spd
import pandas as pd
from types import SimpleNamespace
from pathlib import Path
import time


# import os
# PROXY = '127.0.0.1:20171'
# os.environ["HTTP_PROXY"] = PROXY
# os.environ["HTTPS_PROXY"] = PROXY


def next_workday(date):
    next_day = date + timedelta(days=1)
    while next_day.weekday() >= 5:  # 5=Saturday, 6=Sunday
        next_day += timedelta(days=1)
    return next_day


THIS_WORKDAY = datetime.now()
NEXT_WORKDAY = next_workday(THIS_WORKDAY)
LAST_DAY_OF_WEEK = NEXT_WORKDAY.weekday() == 0
LAST_DAY_OF_MONTH = NEXT_WORKDAY.month == THIS_WORKDAY.month + 1
CURRENT_DATE = THIS_WORKDAY.strftime("%Y%m%d")


START_DATE = "20230101"
ADJUST = "qfq"
PERIODS = ["daily", "weekly", "monthly"]
LAST_N = {
    "daily": -1,
    "weekly": -1 if LAST_DAY_OF_WEEK else -2,
    "monthly": -1 if LAST_DAY_OF_MONTH else -2,
}
SLEEP_INTERVAL_SEC = 2
FUNC_MAPPING = {
    "FUND_ETF": ak.fund_etf_hist_em,
    "A_STOCK": ak.stock_zh_a_hist,
    "HK_STOCK": ak.stock_hk_hist,
}

SYMBOLS = {
    "01810": ("HK_STOCK", "小米集团-W"),
    "512890": ("FUND_ETF", "红利低波ETF"),
    "600519": ("A_STOCK", "贵州茅台"),
}


dfs = []
for sym, (type, name) in SYMBOLS.items():
    for period in PERIODS:
        args = SimpleNamespace(
            symbol=sym,
            name=name,
            period=period,
            adjust=ADJUST,
            start_date=START_DATE,
            end_date=CURRENT_DATE,
        )
        print(f"{datetime.now()}| {args}")

        func = FUNC_MAPPING[type]
        df = func(symbol=args.symbol, period=args.period, start_date=args.start_date, end_date=args.end_date, adjust=args.adjust)
        sdf = spd.StockDataFrame(df)
        sdf.alias("low", "最低")
        sdf.alias("high", "最高")
        sdf.alias("close", "收盘")
        sdf["kdj.j"]
        sdf["代码"] = args.symbol
        sdf["名称"] = args.name
        sdf["复权"] = args.adjust
        sdf["周期"] = args.period
        columns = {spd.directive_stringify("kdj.j"): "J值"}
        sdf.rename(columns=columns, inplace=True)
        df = sdf[["代码", "名称", "日期", "周期", "复权", "收盘", "J值"]].iloc[LAST_N[period]]

        dfs.append(df)
        time.sleep(SLEEP_INTERVAL_SEC)
df = pd.concat(dfs, axis=1, ignore_index=True).T

filepath = Path(f"output/{args.end_date}.csv")
filepath.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(filepath, index=False)
