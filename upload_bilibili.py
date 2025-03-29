#!/usr/bin/env python3
from bilibili_api import dynamic, Credential, sync, Picture
from datetime import datetime, timezone, timedelta


def next_workday(date):
    next_day = date + timedelta(days=1)
    while next_day.weekday() >= 5:  # 5=Saturday, 6=Sunday
        next_day += timedelta(days=1)
    return next_day


SESSDATA = "YOUR_SESSDATA"
BILI_JCT = "YOUR_BILI_JCT"
CURRENT_DATE = datetime.now().strftime("%Y%m%d")


async def main():
    # https://nemo2011.github.io/bilibili-api/#/get-credential?id=%e8%8e%b7%e5%8f%96-credential-%e7%b1%bb%e6%89%80%e9%9c%80%e4%bf%a1%e6%81%af
    credential = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT)

    # content
    pic = Picture.from_file(f"output/{CURRENT_DATE}.jpg")

    # 8:20AM post
    utc8 = timezone(timedelta(hours=8))
    fire_ts = next_workday(datetime.now(utc8)).replace(hour=8, minute=20, second=0, microsecond=0)

    # send
    dy = dynamic.BuildDynamic().add_text("").add_image(pic).set_send_time(fire_ts)
    await dynamic.send_dynamic(dy, credential)


sync(main())
