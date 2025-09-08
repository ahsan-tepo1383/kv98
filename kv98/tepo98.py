import json
import yaml
import requests
import base64
import re
import logging
import time
from typing import List, Optional, Dict
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# --- فایل‌های ورودی و خروجی ---
SUBS = {
    "sub1": "tepo98.txt",
    "sub2": "tepo98.yaml",
    "sub3": "tepo98.json"
}

OUTPUTS = {
    "sub1": "output/sub1_output.txt",
    "sub2": "output/sub2_output.yaml",
    "sub3": "output/sub3_output.json"
}

UPDATE_INTERVAL = 3600  # بروزرسانی هر ساعت

# --- کلاس ConfigParams ---
class ConfigParams:
    def __init__(self, protocol: str = "", address: str = "", port: int = 0, tag: str = "",
                 id: str = "", alter_id: int = 0, security: str = "", encryption: str = "",
                 type: str = "", host: str = None, path: str = None, flow: str = "",
                 sni: str = "", fp: str = "", alpn: Optional[str] = None, pbk: str = "",
                 sid: str = "", spx: str = "", mode: str = None, tls: bool = False,
                 reality: bool = False, mux: bool = False, fragment: bool = False):
        self.protocol = protocol
        self.address = address
        self.port = port
        self.tag = tag
        self.id = id
        self.alter_id = alter_id
        self.security = security
        self.encryption = encryption
        self.type = type
        self.host = host
        self.path = path
        self.flow = flow
        self.sni = sni
        self.fp = fp
        self.alpn = alpn
        self.pbk = pbk
        self.sid = sid
        self.spx = spx
        self.mode = mode
        self.tls = tls
        self.reality = reality
        self.mux = mux
        self.fragment = fragment

# --- تابع parse query ---
def parse_query_params(query: str) -> Dict[str, str]:
    params = {}
    for pair in query.split("&"):
        if "=" in pair:
            key, value = pair.split("=", 1)
            params[key] = requests.utils.unquote(value)
    return params

# --- تابع parse کانفیگ‌ها ---
def parse_vless(line: str, tag: str) -> ConfigParams:
    query = line.split("?",1)[1] if "?" in line else ""
    params = parse_query_params(query)
    match = re.search(r'vless://([^:]+)@([^:]+):(\d+)', line)
    if match:
        return ConfigParams(
            protocol="vless",
            id=match.group(1),
            address=match.group(2),
            port=int(match.group(3)),
            tag=tag,
            type=params.get("type","tcp"),
            host=params.get("host"),
            path=params.get("path"),
            flow=params.get("flow"),
            sni=params.get("sni"),
            fp=params.get("fp"),
            tls=params.get("security","")=="tls",
            mux=params.get("mux","")=="true",
            fragment=params.get("fragment","")=="true"
        )
    return ConfigParams()

def parse_vmess(line: str, tag: str) -> ConfigParams:
    try:
        encoded = line.split("://")[1]
        padded = encoded + "=" * ((4 - len(encoded) % 4) % 4)
        decoded = base64.b64decode(padded).decode()
        data = json.loads(decoded)
        return ConfigParams(
            protocol="vmess",
            address=data.get("add",""),
            port=int(data.get("port",0)),
            tag=tag,
            id=data.get("id",""),
            alter_id=int(data.get("aid",0)),
            encryption=data.get("scy",""),
            type=data.get("net","tcp"),
            host=data.get("host"),
            path=data.get("path"),
            flow=data.get("flow"),
            sni=data.get("sni"),
            fp=data.get("fp"),
            tls=data.get("tls","")=="tls",
            mux=data.get("mux",False),
            fragment=data.get("fragment",False)
        )
    except:
        return ConfigParams()

def parse_trojan(line: str, tag: str) -> ConfigParams:
    match = re.search(r'trojan://([^@]+)@([^:]+):(\d+)', line)
    if match:
        return ConfigParams(
            protocol="trojan",
            address=match.group(2),
            port=int(match.group(3)),
            tag=tag,
            tls=True
        )
    return ConfigParams()

# TODO: parse_ss, parse_socks, parse_wireguard, parse_hysteria2

def parse_line(line: str, tag: str) -> ConfigParams:
    line = line.strip()
    if line.startswith("vless://"):
        return parse_vless(line, tag)
    elif line.startswith("vmess://"):
        return parse_vmess(line, tag)
    elif line.startswith("trojan://"):
        return parse_trojan(line, tag)
    else:
        return ConfigParams()

# --- Load Files ---
def load_txt(path:str, tag:str):
    try:
        with open(path,"r") as f:
            return [parse_line(l, tag) for l in f if l.strip() and not l.startswith("#")]
    except:
        return []

def load_json(path:str, tag:str):
    try:
        with open(path,"r") as f:
            data = json.load(f)
            return [parse_line(c, tag) for c in data.get("configs",[])]
    except:
        return []

def load_yaml(path:str, tag:str):
    try:
        with open(path,"r") as f:
            data = yaml.safe_load(f)
            return [parse_line(c, tag) for c in data.get("configs",[])]
    except:
        return []

# --- Save Output ---
def save_configs(configs:List[ConfigParams], output_file:str):
    try:
        with open(output_file,"w") as f:
            for c in configs:
                if c.address:
                    if output_file.endswith(".json"):
                        f.write(json.dumps(vars(c))+"\n")
                    elif output_file.endswith(".yaml"):
                        f.write(yaml.dump(vars(c)))
                    else:
                        f.write(f"{c.protocol}://{c.address}:{c.port}#{c.tag}\n")
    except:
        pass

# --- Process Sub ---
def process_sub(tag:str, path:str, output_file:str):
    if path.endswith(".txt"):
        configs = load_txt(path, tag)
    elif path.endswith(".json"):
        configs = load_json(path, tag)
    elif path.endswith(".yaml") or path.endswith(".yml"):
        configs = load_yaml(path, tag)
    else:
        configs = []
    valid = [c for c in configs if c.address]
    save_configs(valid, output_file)
    logging.info(f"{tag}: {len(valid)} valid configs saved to {output_file}")

# --- Auto Update ---
def auto_update():
    while True:
        logging.info("Starting auto-update cycle...")
        for tag, path in SUBS.items():
            process_sub(tag, path, OUTPUTS[tag])
        logging.info(f"Sleeping {UPDATE_INTERVAL} seconds before next update")
        time.sleep(UPDATE_INTERVAL)

# --- Menu ---
def menu():
    while True:
        print("\n--- Worker Checker Menu ---")
        print("1. View sub1 output")
        print("2. View sub2 output")
        print("3. View sub3 output")
        print("4. Update all now")
        print("5. Start auto-update loop")
        print("6. Exit")
        choice = input("Enter choice: ")
        if choice=="1":
            with open(OUTPUTS["sub1"],"r") as f: print(f.read())
        elif choice=="2":
            with open(OUTPUTS["sub2"],"r") as f: print(f.read())
        elif choice=="3":
            with open(OUTPUTS["sub3"],"r") as f: print(f.read())
        elif choice=="4":
            for tag,path in SUBS.items():
                process_sub(tag,path,OUTPUTS[tag])
        elif choice=="5":
            auto_update()
        elif choice=="6":
            break
        else:
            print("Invalid choice!")

if __name__=="__main__":
    menu()
