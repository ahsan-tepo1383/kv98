import os
import json
import requests
import base64
import threading
import time
from concurrent.futures import ThreadPoolExecutor

# ======== تنظیمات =========
# مسیر فایل‌های ورودی و خروجی
INPUT_FILES = {
    "txt": "tepo98.txt",
    "json": "tepo98.json",
    "yaml": "tepo98.yaml"
}
OUTPUT_FILES = {
    "txt": "final.txt",
    "json": "final.json",
    "yaml": "final.yaml"
}

# لینک‌های ساب منبع (می‌توانی اضافه یا کم کنی)
LINK_PATH = [
    "https://raw.githubusercontent.com/tepo18/tepo1398/main/tepo98.txt",
    "https://raw.githubusercontent.com/tepo18/tepo1398/main/tepo98.json",
    "https://raw.githubusercontent.com/tepo18/tepo1398/main/tepo98.yaml"
]

# تست URL برای چک کردن کانفیگ‌ها
TEST_URL = "https://www.gstatic.com/generate_204"

# تعداد thread برای بررسی همزمان
MAX_THREADS = 5

# ======== توابع =========

def fetch_link(link):
    try:
        r = requests.get(link, timeout=10)
        if r.status_code == 200:
            return r.text.splitlines()
    except:
        return []
    return []

def validate_config_line(line: str) -> bool:
    """
    بررسی اعتبار کانفیگ
    - فرمت اصلی
    - base64 decode برای vmess
    - بررسی عدم خالی بودن و پین صفر
    """
    line = line.strip()
    if not line:
        return False
    if line.startswith("vmess://"):
        try:
            encoded = line[8:]
            padded = encoded + '=' * (-len(encoded) % 4)
            decoded = base64.b64decode(padded).decode('utf-8')
            data = json.loads(decoded)
            if not data.get("id"):
                return False
        except:
            return False
    # سایر پروتکل‌ها هم می‌توان بررسی مشابه داشت
    return True

def check_file(lines):
    valid = []
    for line in lines:
        if validate_config_line(line):
            valid.append(line)
    return valid

def update_file(input_file, output_file):
    # خواندن محتوا از لینک‌ها
    all_lines = []
    for link in LINK_PATH:
        all_lines += fetch_link(link)
    
    # خواندن محتوا محلی
    if os.path.exists(input_file):
        with open(input_file, "r") as f:
            all_lines += f.read().splitlines()
    
    # حذف خطوط خالی و تکراری
    all_lines = list(dict.fromkeys(all_lines))
    
    # بررسی اعتبار کانفیگ‌ها با thread
    valid_lines = []
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        future = [executor.submit(validate_config_line, l) for l in all_lines]
        for i, f in enumerate(future):
            if f.result():
                valid_lines.append(all_lines[i])
    
    # ذخیره در خروجی
    with open(output_file, "w") as f:
        for line in valid_lines:
            f.write(line + "\n")
    print(f"Updated: {output_file}, {len(valid_lines)} valid configs.")

# ======== اجرای اصلی =========
if __name__ == "__main__":
    for key in INPUT_FILES:
        update_file(INPUT_FILES[key], OUTPUT_FILES[key])
    print("All files updated successfully!")
