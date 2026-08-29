import requests
import socket
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 
TELEGRAM_TOKEN = "8811650010:AAFGCoQ5rMLmu4AjgjxxGeaNQ60WaTVpXeY"
CHAT_ID = "1436101177"

DOMAINS = ["nar.az", "azercell.com"]
CACHE_FILE = "hosts_cache.txt"

def send_telegram(message):
    if not TELEGRAM_TOKEN:
        print("Xəta: Telegram token daxil edilməyib!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, data=payload, timeout=10)
        print(f"Telegram cavabı: {response.text}")
    except Exception as e:
        print(f"Telegram xətası: {e}")

def get_crtsh(domain):
    subdomains = set()
    try:
        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        res = requests.get(url, timeout=20)
        if res.status_code == 200:
            for entry in res.json():
                name = entry.get('name_value', '')
                for sub in name.split('\n'):
                    sub = sub.strip().lower()
                    if sub.endswith(domain) and '*' not in sub:
                        subdomains.add(sub)
    except Exception as e:
        print(f"crt.sh error: {e}")
    return subdomains

def get_hackertarget(domain):
    subdomains = set()
    try:
        url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
        res = requests.get(url, timeout=15)
        if res.status_code == 200 and "API count exceeded" not in res.text:
            for line in res.text.split('\n'):
                if ',' in line:
                    sub = line.split(',')[0].strip().lower()
                    if sub.endswith(domain):
                        subdomains.add(sub)
    except Exception as e:
        print(f"HackerTarget error: {e}")
    return subdomains

def get_alienvault(domain):
    subdomains = set()
    try:
        url = f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns"
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            for record in res.json().get('passive_dns', []):
                hostname = record.get('hostname', '').strip().lower()
                if hostname.endswith(domain) and '*' not in hostname:
                    subdomains.add(hostname)
    except Exception as e:
        print(f"AlienVault error: {e}")
    return subdomains

def get_anubis(domain):
    subdomains = set()
    try:
        url = f"https://jldc.me/anubis/subdomains/{domain}"
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            for sub in res.json():
                sub = sub.strip().lower()
                if sub.endswith(domain) and '*' not in sub:
                    subdomains.add(sub)
    except Exception as e:
        print(f"Anubis error: {e}")
    return subdomains

def check_host_status(host):
    try:
        res = requests.get(f"https://{host}", timeout=3, verify=False)
        if res.status_code < 400:
            return f"HTTP {res.status_code} (Aktiv)"
    except:
        try:
            socket.gethostbyname(host)
            return "DNS Açıq"
        except:
            pass
    return None

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_cache(hosts):
    with open(CACHE_FILE, "w") as f:
        for h in sorted(hosts):
            f.write(h + "\n")

if __name__ == "__main__":
    print("[🔥] Gücləndirilmiş Host Scanner işə düşdü...")
    current_hosts = set()
    
    for dom in DOMAINS:
        print(f"Yoxlanılır: {dom}")
        current_hosts.update(get_crtsh(dom))
        current_hosts.update(get_hackertarget(dom))
        current_hosts.update(get_alienvault(dom))
        current_hosts.update(get_anubis(dom))

    old_hosts = load_cache()
    is_first_run = len(old_hosts) == 0
    
    # Yalnız yeniləri tapırıq
    new_hosts = current_hosts - old_hosts if not is_first_run else current_hosts

    print(f"Ümumi tapılan: {len(current_hosts)}, Yeni tapılan: {len(new_hosts)}")

    if new_hosts or is_first_run:
        title = "🚨 *Nar və Azercell Yeni Hostlar Tapıldı!*" if not is_first_run else "🔥 *İlk Host Tarama Hesabatı*"
        report_lines = [f"{title}\nÜmumi: {len(current_hosts)} | Yeni: {len(new_hosts)}\n"]
        
        target_list = new_hosts if not is_first_run else current_hosts
        active_count = 0
        for host in sorted(target_list):
            status = check_host_status(host)
            if status:
                active_count += 1
                if active_count <= 40:
                    report_lines.append(f"- `{host}` -> {status}")

        msg = "\n".join(report_lines)
        if len(msg) > 4000:
            msg = msg[:3900] + "\n...(çoxluq səbəbilə kəsildi)"
            
        send_telegram(msg)
    else:
        print("Yeni host tapılmadı, Telegram-a mesaj göndərilmədi.")

    save_cache(current_hosts)
    
