#!/usr/bin/env python3
"""Scan Vietnamese Fintech endpoints via SSL Labs API."""
import requests, json, time, os, sys
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results"); os.makedirs(R, exist_ok=True)
API = "https://api.ssllabs.com/api/v3"
TARGETS = [
    {"name":"MoMo","host":"momo.vn"},{"name":"VNPay","host":"vnpay.vn"},
    {"name":"ZaloPay","host":"zalopay.vn"},{"name":"VietQR","host":"vietqr.net"},
    {"name":"Vietcombank","host":"vietcombank.com.vn"},{"name":"Techcombank","host":"techcombank.com.vn"},
    {"name":"MB Bank","host":"mbbank.com.vn"},{"name":"VPBank","host":"vpbank.com.vn"},
    {"name":"TPBank","host":"tpb.vn"},{"name":"ACB","host":"acb.com.vn"},
]
results = []
for i, t in enumerate(TARGETS):
    print(f"[{i+1}/{len(TARGETS)}] Scanning {t['name']} ({t['host']})...")
    for attempt in range(20):
        try:
            r = requests.get(f"{API}/analyze", params={"host":t["host"],"fromCache":"on","maxAge":24,"all":"done"}, timeout=30)
            if r.status_code == 429: time.sleep(60); continue
            d = r.json(); status = d.get("status")
            if status == "READY":
                ep = d.get("endpoints",[{}])[0]; det = ep.get("details",{})
                protos = [f"{p['name']} {p['version']}" for p in det.get("protocols",[])]
                results.append({"service_name":t["name"],"host":t["host"],"grade":ep.get("grade","?"),
                    "tls12_supported":any("1.2" in p for p in protos),"tls13_supported":any("1.3" in p for p in protos),
                    "legacy_tls":any("1.0" in p or "1.1" in p for p in protos),
                    "hsts":det.get("hstsPolicy",{}).get("status")=="present",
                    "forward_secrecy":det.get("forwardSecrecy",0)>=2})
                print(f"  ✅ Grade: {ep.get('grade','?')}"); break
            elif status in ("DNS","IN_PROGRESS"): time.sleep(15)
            else: print(f"  ❌ {status}"); break
        except Exception as e: print(f"  Error: {e}"); time.sleep(10)
    if i < len(TARGETS)-1: time.sleep(5)
with open(f"{R}/ssllabs_results.json","w") as f: json.dump(results,f,indent=2)
print(f"\n✅ Results saved: {R}/ssllabs_results.json")
