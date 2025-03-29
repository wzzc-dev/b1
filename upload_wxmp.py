#!/usr/bin/env python3
import requests
import json
from datetime import datetime, timedelta
from PIL import Image


def next_workday(date):
    next_day = date + timedelta(days=1)
    while next_day.weekday() >= 5:  # 5=Saturday, 6=Sunday
        next_day += timedelta(days=1)
    return next_day


APPID = "YOUR_APPID"
APPSECRET = "YOUR_APPSECRET"
CURRENT_DATE = datetime.now().strftime("%Y%m%d")
HEADER = next_workday(datetime.now()).strftime("%Y-%m-%d")
IMG_PATH = f"output/{CURRENT_DATE}.jpg"

UPPER_PX = 50


def get_cord_235_1():
    with Image.open(IMG_PATH) as img:
        width, height = img.size
    print(width, height)

    X1 = 0 / width
    Y1 = UPPER_PX / height
    X2 = width / width
    Y2 = (width / 2.35 + UPPER_PX) / height

    return f"{X1:.6f}_{Y1:.6f}_{X2:.6f}_{Y2:.6f}"


# 获取access_token
def get_access_token():
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}"
    response = requests.get(url)
    if int(response.status_code) == 200:
        data = response.json()
        print(data)
        return data.get("access_token")
    else:
        print("获取access_token失败")
        return None


# 上传图片并获取media_id
def upload_image(access_token, image_path):
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}"
    with open(image_path, "rb") as file:
        files = {"media": file}
        response = requests.post(url, files=files)
        if int(response.status_code) == 200:
            data = response.json()
            print(data)
            return data.get("url"), data.get("media_id")
        else:
            print("上传图片失败")
            return None, None


# 创建草稿
def create_draft(access_token, title, author, digest, content, content_source_url, thumb_media_id):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
    data = {
        "articles": [
            {
                "title": title,
                "author": author,
                "digest": digest,
                "content": content,
                "content_source_url": content_source_url,
                "thumb_media_id": thumb_media_id,
                "pic_crop_235_1": get_cord_235_1(),
                "need_open_comment": 0,
                "only_fans_can_comment": 0,
            }
        ]
    }
    print(data)

    # response = requests.post(url, json=data)
    response = requests.post(url, data=bytes(json.dumps(data, ensure_ascii=False), encoding="utf-8"))
    if int(response.status_code) == 200:
        data = response.json()
        print(data)
        return data.get("media_id")
    else:
        print("创建草稿失败")
        return None


# 主函数
def main():
    # 获取access_token
    access_token = get_access_token()
    print(access_token)
    if not access_token:
        raise ValueError("access_token error")

    # 上传图片
    image_url, thumb_media_id = upload_image(access_token, IMG_PATH)
    print(image_url, thumb_media_id)
    if not thumb_media_id:
        raise ValueError("upload_image error")

    # 创建草稿
    title = f"{HEADER} B1早报"
    author = "我有B1就不说"
    digest = ""
    content = f'<img src="{image_url}">'
    content_source_url = ""
    draft_media_id = create_draft(access_token, title, author, digest, content, content_source_url, thumb_media_id)
    print(draft_media_id)
    if not draft_media_id:
        raise ValueError("create_draft error")

    # 写入log
    with open(f"output/{HEADER}.draft", "w") as f:
        f.write(draft_media_id)


if __name__ == "__main__":
    main()
