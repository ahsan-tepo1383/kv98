# -*- coding: utf-8 -*-
import os
import json
import urllib.request
import base64

# ---------------- مسیر فایل‌های منابع ----------------
TEXT_PATH = "tepo98.txt"
JSON_PATH = "tepo98.json"
YAML_PATH = "tepo98.yaml"

# ---------------- لینک منابع روی گیت‌هاب ----------------
LINK_PATH = [
    "https://raw.githubusercontent.com/tepo18/tepo1398/main/tepo98.txt",
    "https://raw.githubusercontent.com/tepo18/tepo1398/main/tepo98.json",
    "https://raw.githubusercontent.com/tepo18/tepo1398/main/tepo98.yaml"
]

# ---------------- مسیر خروجی نهایی ----------------
FIN_PATH = "final.txt"

# ---------------- هدر ثابت برای هر ساب ----------------
FILE_HEADER_TEXT = "//profile-title: base64:2YfZhduM2LTZhyDZgdi52KfZhCDwn5iO8J+YjvCfmI4gaGFtZWRwNzE="

# ---------------- خواندن محتوا از منابع ----------------
def read_sources():
    contents = []
    for link in LINK_PATH:
        try:
            with urllib.request.urlopen(link) as response:
                data = response.read().decode("utf-8")
                contents.append(data)
        except Exception as e:
            print(f"Failed to read {link}: {e}")
    return contents

# ---------------- پردازش محتوا (حذف خطوط خالی و کپی هدر) ----------------
def process_contents(contents):
    final_list = [FILE_HEADER_TEXT + "\n"]
    for content in contents:
        lines = content.splitlines()
        for line in lines:
            line = line.strip()
            if line:  # حذف خطوط خالی
                final_list.append(line + "\n")
    return final_list

# ---------------- نوشتن خروجی نهایی ----------------
def write_final(final_list):
    with open(FIN_PATH, "w", encoding="utf-8") as f:
        f.writelines(final_list)
    print(f"Final output saved to {FIN_PATH}")

# ---------------- اجرای اصلی ----------------
if __name__ == "__main__":
    sources = read_sources()
    final_content = process_contents(sources)
    write_final(final_content)
