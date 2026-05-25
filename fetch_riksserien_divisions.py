# -*- coding: utf-8 -*-
"""
Hämtar divisionerna för Riksserien 2025/2026 från Nakka API
"""
import sys
import requests
import json
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = 'https://tk2-228-23746.vs.sakura.ne.jp/n01/tournament/'
LGID = 'lg_UUtS_2240'

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
})

# Prova GET med lgid som query param
print("=== GET requests ===")
get_urls = [
    f"{BASE_URL}n01_tournament.php?cmd=get_lg_info&lgid={LGID}",
    f"{BASE_URL}n01_tournament.php?cmd=get_tdid_list&lgid={LGID}",
    f"{BASE_URL}n01_tournament.php?lgid={LGID}",
    f"{BASE_URL}n01_online_t.php?cmd=get_setdata&lgid={LGID}",
    f"https://tk2-228-23746.vs.sakura.ne.jp/n01/tournament/n01_tournament.php?cmd=get_lg_schedule&lgid={LGID}&div=0",
]

for url in get_urls:
    try:
        r = session.get(url, timeout=15)
        print(f"\nGET {url[-80:]}")
        print(f"  Status: {r.status_code}, Len: {len(r.text)}")
        if r.text.strip():
            print(f"  Response: {r.text[:400]}")
    except Exception as e:
        print(f"  Error: {e}")

# Prova POST med lgid
print("\n=== POST med lgid ===")
post_cmds = ['get_lg_schedule', 'get_lg_info', 'get_lg_div_list', 'get_lg_tournaments']
for cmd in post_cmds:
    try:
        r = session.post(BASE_URL + 'n01_tournament.php',
                        json={'cmd': cmd, 'lgid': LGID, 'div': 0},
                        timeout=15)
        print(f"\nPOST cmd={cmd}")
        print(f"  Status: {r.status_code}, Len: {len(r.text)}")
        if r.text.strip():
            print(f"  Response: {r.text[:400]}")
    except Exception as e:
        print(f"  Error: {e}")
