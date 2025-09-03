#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import threading
import urllib.request
import subprocess
import time
import platform
import re

# ---------------- مسیر فایل‌ها ----------------
NORMAL_PATH = "normal.txt"
FINAL_PATH = "final.txt"

# ---------------- لینک‌های منابع ----------------
LINKS_RAW = [
    "https://raw.githubusercontent.com/tepo90/online-sshmax98/main/tepo10.txt",
    "https://raw.githubusercontent.com/tepo90/online-sshmax98/main/tepo20.txt",
    "https://raw.githubusercontent.com/tepo90/online-sshmax98/main/tepo30.txt",
    "https://raw.githubusercontent.com/tepo90/online-sshmax98/main/tepo40.txt",
    "https://raw.githubusercontent.com/tepo90/online-sshmax98/main/tepo50.txt",
]

# ---------------- تابع دریافت محتوا ----------------
def fetch_url_lines(url):
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return [line.decode().strip() for line in resp.readlines() if line.strip()]
    except Exception as e:
        print(f"[ERROR] Cannot fetch {url}: {e}")
        return []

# ---------------- پینگ واقعی ----------------
def ping(host, count=1, timeout=1):
    param_count = "-n" if platform.system().lower() == "windows" else "-c"
    param_timeout = "-w" if platform.system().lower() == "windows" else "-W"
    try:
        cmd = ["ping", param_count, str(count), param_timeout, str(timeout), host]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output = result.stdout
        match = re.findall(r'time[=<]?\s*(\d+\.?\d*)', output)
        if match:
            # میانگین پینگ
            times = [float(m) for m in match]
            return sum(times)/len(times)
    except:
        pass
    return float('inf')

# ---------------- پردازش پینگ با چند بار تست ----------------
def ping_stage(configs, max_threads=20, ping_count=3):
    results = []
    lock = threading.Lock()
    threads = []

    def worker(cfg_line):
        try:
            cfg = json.loads(cfg_line)
            outbounds = cfg.get("outbounds", [])
            if outbounds:
                addr = outbounds[0].get("settings", {}).get("vnext", [{}])[0].get("address")
                if addr:
                    # میانگین چند پینگ برای پایداری
                    ping_values = [ping(addr) for _ in range(ping_count)]
                    if all(p < float('inf') for p in ping_values):
                        avg_ping = sum(ping_values)/len(ping_values)
                        with lock:
                            cfg["_ping"] = avg_ping
                            results.append(cfg)
        except:
            pass

    for cfg_line in configs:
        t = threading.Thread(target=worker, args=(cfg_line,))
        threads.append(t)
        t.start()
        if len(threads) >= max_threads:
            for th in threads: th.join()
            threads = []

    for t in threads: t.join()

    # حذف تکراری
    unique = {}
    for cfg in results:
        key = cfg.get("remarks")
        if key not in unique:
            unique[key] = cfg
    final_list = list(unique.values())
    final_list.sort(key=lambda x: x.get("_ping", float('inf')))
    return final_list

# ---------------- ذخیره فایل ----------------
def save_configs_file(configs, path):
    with open(path, "w", encoding="utf-8") as f:
        for cfg in configs:
            cfg.pop("_ping", None)
            f.write(json.dumps(cfg, ensure_ascii=False) + "\n")
    print(f"[INFO] Saved {len(configs)} configs to {path}")

# ---------------- فرآیند اصلی بروزرسانی ----------------
def update_all():
    print("[*] Fetching sources...")
    all_configs_raw = []
    for url in LINKS_RAW:
        all_configs_raw.extend(fetch_url_lines(url))
    print(f"[*] Total lines fetched: {len(all_configs_raw)}")

    # مرحله اول پینگ → normal.txt
    print("[*] Stage 1: First ping check (basic filtering)...")
    stage1_configs = ping_stage(all_configs_raw, ping_count=1)
    save_configs_file(stage1_configs, NORMAL_PATH)

    # مرحله دوم پینگ دقیق و پایداری → final.txt
    print("[*] Stage 2: Detailed ping stability check...")
    normal_lines = [json.dumps(cfg, ensure_ascii=False) for cfg in stage1_configs]
    stage2_configs = ping_stage(normal_lines, ping_count=3)  # میانگین 3 پینگ
    # فیلتر پینگ ≤ 1200
    stage2_configs = [cfg for cfg in stage2_configs if cfg.get("_ping", float('inf')) <= 1200]
    save_configs_file(stage2_configs, FINAL_PATH)
    print(f"[✅] Update complete. {len(stage2_configs)} configs in final.txt")

# ---------------- Main ----------------
if __name__ == "__main__":
    print("[*] Starting auto-updater with stable ping checks...")
    while True:
        start_time = time.time()
        update_all()
        print(f"[*] Next update in 1 hour. Elapsed: {time.time() - start_time:.2f}s\n")
        time.sleep(3600)
