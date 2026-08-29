import requests
import socket
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TELEGRAM_TOKEN = "8633891826:AAGwlt8LIOK0aiByAyQDmw23q21bsmeAm28"
CHAT_ID = "1436101177"
DOMAINS = ["nar.az", "azercell.com"]
FILE_NAME = "super_known_hosts.txt"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Telegram xətası: {e}")

def get_crtsh_subdomains(domain):
    subdomains = set()
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            data = response.json()
            for entry in data:
                name_value = entry.get('name_value', '')
                for sub in name_value.split('\n'):
                    sub = sub.strip().lower()
                    if sub.endswith(domain) and '*' not in sub:
                        subdomains.add(sub)
    except Exception:
        pass
    return subdomains

def get_hackertarget_subdomains(domain):
    subdomains = set()
    url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200 and "API count exceeded" not in response.text:
            for line in response.text.split('\n'):
                if ',' in line:
                    sub = line.split(',')[0].strip().lower()
                    if sub.endswith(domain):
                        subdomains.add(sub)
    except Exception:
        pass
    return subdomains

def check_host_status(host):
    status_info = "DNS Mövcuddur"
    try:
        res = requests.get(f"https://{host}", timeout=4, verify=False)
        status_info = f"HTTP Status: {res.status_code}"
    except:
        try:
            socket.gethostbyname(host)
            status_info = "DNS Açıq (TCP/Tunnel üçün uyğun ola bilər)"
        except:
            status_info = "Cavab yoxdur"
    return status_info

def load_known_hosts():
    if not os.path.exists(FILE_NAME):
        return set()
    with open(FILE_NAME, "r") as f:
        return set(line.strip() for line in f if line.strip())

def save_known_hosts(hosts):
    with open(FILE_NAME, "w") as f:
        for host in sorted(hosts):
            f.write(host + "\n")

if __name__ == "__main__":
    print("[🔥] GitHub Actions Host Scanner işə düşdü...")
    current_hosts = set()
    
    for dom in DOMAINS:
        crt_subs = get_crtsh_subdomains(dom)
        ht_subs = get_hackertarget_subdomains(dom)
        current_hosts.update(crt_subs)
        current_hosts.update(ht_subs)
    
    known_hosts = load_known_hosts()
    
    if not known_hosts:
        save_known_hosts(current_hosts)
        print(f"[*] İlkin baza yaradıldı. Cəmi {len(current_hosts)} host qeydə alındı.")
    else:
        new_hosts = current_hosts - known_hosts
        if new_hosts:
            print(f"[+] {len(new_hosts)} yeni host tapıldı!")
            for nh in new_hosts:
                status = check_host_status(nh)
                msg = f"🚨 **YENİ HOST AŞKAR OLUNDU!**\n\n🌐 Host: `{nh}`\n⚡ Vəziyyət: `{status}`"
                send_telegram(msg)
            save_known_hosts(current_hosts)
        else:
            print("[*] Yeni host tapılmadı.")
  
