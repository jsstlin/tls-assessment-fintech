#!/usr/bin/env python3
"""Generate publication-ready charts from scan results."""
import json, csv, glob, os, sys
try:
    import pandas as pd; import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; import seaborn as sns
except ImportError:
    os.system(f"{sys.executable} -m pip install pandas matplotlib seaborn --quiet")
    import pandas as pd; import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; import seaborn as sns

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
C = os.path.join(R, "charts"); os.makedirs(C, exist_ok=True)
sns.set_theme(style="whitegrid", font_scale=1.1)
COL = {"TLS 1.2": "#E74C3C", "TLS 1.3": "#2ECC71"}

# Fig 1: Severity
for ver, label in [("tls12","TLS 1.2"),("tls13","TLS 1.3")]:
    f = glob.glob(f"{R}/testssl_{ver}*.json")
    if f:
        with open(f[-1]) as fh: data = json.load(fh)
        print(f"{label}: " + str({s: sum(1 for x in data if x.get("severity")==s) for s in ["CRITICAL","MEDIUM","LOW","OK"]}))

# Fig 2-4: Latency
records = []
for pat in ["locust_tls12_u*_stats.csv","locust_tls13_u*_stats.csv"]:
    for fp in sorted(glob.glob(f"{R}/{pat}")):
        bn = os.path.basename(fp).replace("_stats.csv","").split("_")
        ver = "TLS 1.2" if "tls12" in bn[1] else "TLS 1.3"
        users = int(bn[2].replace("u",""))
        df = pd.read_csv(fp); agg = df[df["Name"]=="Aggregated"]
        if agg.empty: agg = df.iloc[-1:]
        records.append({"TLS Version":ver,"Concurrent Users":users,"Avg Latency (ms)":agg["Average Response Time"].values[0],
            "P50 (ms)":agg.get("50%",agg.get("Median Response Time",pd.Series([0]))).values[0],
            "P95 (ms)":agg.get("95%",pd.Series([0])).values[0],"P99 (ms)":agg.get("99%",pd.Series([0])).values[0],
            "Requests/s":agg["Requests/s"].values[0]})

if records:
    df = pd.DataFrame(records)
    fig, ax = plt.subplots(figsize=(10,6))
    for v, g in df.groupby("TLS Version"):
        g2 = g.sort_values("Concurrent Users")
        ax.plot(g2["Concurrent Users"], g2["Avg Latency (ms)"], marker="o", linewidth=2.5, markersize=8, color=COL[v], label=v)
    ax.set_xlabel("Concurrent Users"); ax.set_ylabel("Average Latency (ms)")
    ax.set_title("TLS Handshake + Response Latency Under Load", fontsize=14, fontweight="bold")
    ax.legend(fontsize=12); plt.tight_layout(); plt.savefig(f"{C}/fig2_latency_vs_users.png", dpi=300); plt.close()

    fig, ax = plt.subplots(figsize=(10,6))
    for v, g in df.groupby("TLS Version"):
        g2 = g.sort_values("Concurrent Users")
        ax.plot(g2["Concurrent Users"], g2["Requests/s"], marker="s", linewidth=2.5, markersize=8, color=COL[v], label=v)
    ax.set_xlabel("Concurrent Users"); ax.set_ylabel("Throughput (req/s)")
    ax.set_title("Throughput: TLS 1.2 vs TLS 1.3", fontsize=14, fontweight="bold")
    ax.legend(); plt.tight_layout(); plt.savefig(f"{C}/fig4_throughput.png", dpi=300); plt.close()

    df.to_csv(f"{R}/latency_summary.csv", index=False)
    print(f"✅ Charts saved in {C}/")
else:
    print("⚠ No Locust CSV files found")

# Fig 5: SSL Labs
sf = f"{R}/ssllabs_results.json"
if os.path.exists(sf):
    with open(sf) as fh: sd = json.load(fh)
    grades = pd.Series([s["grade"] for s in sd]).value_counts().sort_index()
    gc = {"A+":"#1ABC9C","A":"#2ECC71","A-":"#82E0AA","B":"#F1C40F"}
    fig, ax = plt.subplots(figsize=(8,5))
    grades.plot(kind="bar", ax=ax, color=[gc.get(g,"#95A5A6") for g in grades.index], edgecolor="black")
    ax.set_title("SSL Labs Grade — Vietnamese Fintech", fontsize=13, fontweight="bold")
    ax.set_ylabel("Count"); plt.tight_layout(); plt.savefig(f"{C}/fig5_ssllabs_grades.png", dpi=300); plt.close()

print("🎉 Analysis complete!")
