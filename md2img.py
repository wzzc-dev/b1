#!/usr/bin/env python3
import requests
from datetime import datetime, timedelta


def next_workday(date):
    next_day = date + timedelta(days=1)
    while next_day.weekday() >= 5:  # 5=Saturday, 6=Sunday
        next_day += timedelta(days=1)
    return next_day


CURRENT_DATE = datetime.now().strftime("%Y%m%d")
HEADER = next_workday(datetime.now()).strftime("%Y-%m-%d") + " B1早报"
FOOTER = "我有B1就不说"
API_URL = "http://127.0.0.1:3000/api/generatePosterImage"


def read_markdown_content(file_path):
    with open(file_path) as f:
        return f.read()


def markdown_to_image_url(markdown, header="", footer=""):
    json_data = {"markdown": markdown, "header": header, "footer": footer}
    response = requests.post(API_URL, json=json_data)

    if response.status_code == 200:
        return response.json()["url"]
    else:
        raise ValueError(f"请求失败，状态码: {response.status_code}")


def save_image(url):
    response = requests.get(url)

    if response.status_code == 200:
        with open(f"output/{CURRENT_DATE}.jpg", "wb") as file:
            file.write(response.content)
    else:
        raise ValueError(f"请求失败，状态码: {response.status_code}")


print(f"API_URL: {API_URL}")
print(f"HEADER: {HEADER}")
print(f"FOOTER: {FOOTER}")
content = read_markdown_content(f"output/{CURRENT_DATE}.md")
url = markdown_to_image_url(content, header=HEADER, footer=FOOTER)
print(url)
save_image(url)

print(f"done {CURRENT_DATE}")
