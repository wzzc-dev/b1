#!/usr/bin/env python3

import pandas as pd
from datetime import datetime

CURRENT_DATE = datetime.now().strftime("%Y%m%d")

DARK_RED = "#E74C3C"
LIGHT_RED = "#FFCCCB"


def with_color(x):
    if x < -5:
        return f'<span style="background-color: {DARK_RED}">**{x:.2f}**</span>'
    if x < 0 and x > -5:
        return f'<span style="background-color: {LIGHT_RED}">**{x:.2f}**</span>'

    return f"{x:.2f}"


df = pd.read_csv(
    f"output/{CURRENT_DATE}.csv",
    dtype={
        "代码": str,
        "J值": float,
    },
)

adjust = {
    "qfq": "前复权",
    "hfq": "后复权",
}
period = {
    "daily": "日线",
    "weekly": "周线",
    "monthly": "月线",
}

daily_date = df[df["周期"] == "daily"]["日期"].iloc[0]
weekly_date = df[df["周期"] == "weekly"]["日期"].iloc[0]
monthly_date = df[df["周期"] == "monthly"]["日期"].iloc[0]

# 调整表格列名
df["复权"] = df["复权"].map(adjust)
df["周期"] = df["周期"].map(period)
df.pop("复权")


# 为负J值上色
df["J值"] = df["J值"].apply(with_color)


# 确保 "周期" 按 ["日线", "周线", "月线"] 排序
df["周期"] = pd.Categorical(df["周期"], categories=["日线", "周线", "月线"], ordered=True)

# 透视表格，保持原顺序
df_pivot = df.pivot(index=["代码", "名称"], columns="周期", values=["收盘", "J值"])
df_pivot.columns = [f"{col[1]}_{col[0]}" for col in df_pivot.columns]  # 重命名列
df_pivot.reset_index(inplace=True)

# 使用 merge 还原原始顺序（按 "代码" 和 "名称" 在原始 df 里的出现顺序）
df_ordered = df[["代码", "名称"]].drop_duplicates().merge(df_pivot, on=["代码", "名称"], how="left")

# 选出负值的行
filtered_df = df_ordered[df_ordered.apply(lambda row: row.map(lambda x: isinstance(x, str) and "**" in x)).any(axis=1)]


def print_md(df):
    from pathlib import Path
    symbols_file = Path("symbols.txt")
    MAPPDING = {}
    with open(symbols_file, 'r', encoding='utf-8') as f:
        for line in f:
            symbol, _, short_name = line.strip().split(',')
            # 这里简单取名称的前两个字作为简称，可根据实际需求调整
            MAPPDING[symbol] = short_name

    if df.empty:
        return """
<table>
    <thead>
        <tr>
        <th>名称</th>
        <th>指标</th>
        <th>日线</th>
        <th>周线</th>
        <th>月线</th>
        </tr>
    </thead>
    <tbody>
        <tr>
        <td colspan="6" align="center">暂无</td>
        </tr>
    </tbody>
</table>

        """

    markdown = "| 名称 | 指标 | 日线 | 周线 | 月线 |\n"
    markdown += "|:----:|:----:|:----:|:----:|:----:|\n"
    for _, row in df.iterrows():
        markdown += f"| &emsp;&emsp; {MAPPDING[row['代码']]} &emsp;&emsp; | 收盘价<br>J值 | {row['日线_收盘']}<br>{row['日线_J值']} | {row['周线_收盘']}<br>{row['周线_J值']} | {row['月线_收盘']}<br>{row['月线_J值']} |\n"
    return markdown


HEADER = """
<style>
 table {
   margin: 0 auto;
 }
 h1 {
  text-align: center;
 }
td:nth-child(1),  
td:nth-child(2) { 
  vertical-align: middle !important;
  white-space: nowrap;
}

td:nth-child(1) span,  
td:nth-child(2) span {
  display: inline-block;
  vertical-align: middle;
}

tr:nth-child(even) {
  background-color: #f2f2f2;
}
</style>
"""

NOTICE = f"""
<div style="text-align: center;">
<span style="color: gray; font-size: 10px;"> 日线 {daily_date} / 周线 {weekly_date} / 月线 {monthly_date} </span>
</div>
"""

with open(f"output/index.md", "w") as f:
    f.write(HEADER)

    f.write(NOTICE)

    f.write("\n# B1\n")
    f.write(print_md(filtered_df))

    f.write("\n\n---\n\n")

    f.write("\n# 所有阵容\n")
    f.write(print_md(df_ordered))

with open(f"output/index.md") as f:
    print(f.read())

import markdown

# 读取 Markdown 文件
with open('output/index.md', 'r', encoding='utf-8') as f:
    md_content = f.read()

# 将 Markdown 内容转换为 HTML
html_content = markdown.markdown(md_content, extensions=['tables'])

# 将 HTML 内容写入新文件
with open('output/index.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print('Markdown 文件已成功转换为 HTML 文件。')