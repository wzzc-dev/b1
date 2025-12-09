#!/usr/bin/env python3

from datetime import datetime, timedelta
import akshare as ak
import stock_pandas as spd
import pandas as pd
from types import SimpleNamespace
from pathlib import Path
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# 启用代理设置（如果需要）
# import os
# PROXY = '127.0.0.1:20171'
# os.environ["HTTP_PROXY"] = PROXY
# os.environ["HTTPS_PROXY"] = PROXY

# 设置重试机制
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("https://", adapter)
session.mount("http://", adapter)

# 将akshare的requests会话替换为带有重试机制的会话
ak._session = session


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

# 函数映射 - 使用腾讯数据源替代东方财富
FUNC_MAPPING = {
    "A_STOCK": ak.stock_zh_a_hist_tx,
    "HK_STOCK": ak.stock_hk_hist,
    "FUND_ETF": ak.fund_etf_hist_em,
}

# 假设文本文件名为 symbols.txt，位于项目根目录
symbols_file = Path("symbols.txt")
SYMBOLS = {}
with open(symbols_file, 'r', encoding='utf-8') as f:
    for line in f:
        parts = line.strip().split(',')
        if len(parts) == 3:
            symbol, type, name = parts
            SYMBOLS[symbol] = (type, name)
        else:
            print(f"跳过无效行: {line.strip()}")


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
        retry_count = 0
        max_retries = 3
        success = False
        while retry_count < max_retries:
            try:
                # 根据不同的数据源调整参数
                if type == "A_STOCK":
                    # 腾讯数据源需要带市场标识和连字符的日期格式
                    # 添加市场标识前缀
                    if args.symbol.startswith("6"):
                        # 上海证券交易所股票
                        symbol_with_market = f"sh{args.symbol}"
                    else:
                        # 深圳证券交易所股票
                        symbol_with_market = f"sz{args.symbol}"
                    # 腾讯数据源需要带连字符的日期格式
                    start_date = f"{args.start_date[:4]}-{args.start_date[4:6]}-{args.start_date[6:]}"
                    end_date = f"{args.end_date[:4]}-{args.end_date[4:6]}-{args.end_date[6:]}"
                    df = func(symbol=symbol_with_market, start_date=start_date, end_date=end_date, adjust=args.adjust)
                elif type == "HK_STOCK":
                    # 港股函数不接受timeout参数
                    df = func(symbol=args.symbol, period=args.period, start_date=args.start_date, end_date=args.end_date, adjust=args.adjust)
                else:
                    # 基金函数接受timeout参数
                    df = func(symbol=args.symbol, period=args.period, start_date=args.start_date, end_date=args.end_date, adjust=args.adjust, timeout=30)
                success = True
                break
            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout, TypeError) as e:
                retry_count += 1
                print(f"连接错误，正在重试 ({retry_count}/{max_retries}): {e}")
                time.sleep(5 * retry_count)  # 指数退避
                if retry_count == max_retries:
                    print(f"多次重试失败，跳过 {args.symbol} {args.period}")
        
        if not success:
            continue
            
        # 先检查数据结构
        print(f"数据列名: {list(df.columns)}")
        
        # 确保我们有必要的列
        required_columns = ["日期", "开盘", "最高", "最低", "收盘", "成交量"]
        
        # 如果是腾讯数据源，列名可能已经是英文的
        if all(col in df.columns for col in ["date", "open", "high", "low", "close"]):
            # 重命名列名为中文，以便与其他代码兼容
            rename_dict = {
                "date": "日期",
                "open": "开盘",
                "high": "最高",
                "low": "最低",
                "close": "收盘"
            }
            # 处理成交量列，腾讯数据源返回的是amount
            if "amount" in df.columns:
                rename_dict["amount"] = "成交量"
            elif "volume" in df.columns:
                rename_dict["volume"] = "成交量"
            
            df.rename(columns=rename_dict, inplace=True)
        
        # 创建stock_pandas对象
        sdf = spd.StockDataFrame(df)
        
        # 添加必要的别名
        sdf.alias("date", "日期")
        sdf.alias("open", "开盘")
        sdf.alias("high", "最高")
        sdf.alias("low", "最低")
        sdf.alias("close", "收盘")
        sdf.alias("volume", "成交量")
        
        # 计算KDJ指标
        sdf["kdj.j"]
        
        # 添加代码和名称
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
