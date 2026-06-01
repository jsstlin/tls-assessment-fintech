# TLS Security Assessment Testbed for Fintech Payment Systems

> **Paper:** *Security Risk Assessment of TLS Configurations in Fintech Payment Systems: A Comparative Analysis of TLS 1.2 and TLS 1.3*
> **Conference:** ICSCCT 2026
> **Authors:** Quoc Hung Nguyen, Thien Khanh Phan, Bao Tran Tran Huynh, Anh Ngoc Bui, Thuy Linh Nguyen Ngoc
> **Affiliation:** University of Economics Ho Chi Minh City (UEH), Vietnam

---

## Abstract

Misconfigured TLS deployments remain a persistent yet under-studied threat in Fintech payment infrastructure. This paper proposes a four-phase, threat-model-driven framework for assessing TLS configurations in payment APIs, comparing TLS 1.2 and TLS 1.3 through controlled experimentation. Results show that **TLS 1.3 eliminates 2 critical and 2 medium-severity vulnerabilities** found in TLS 1.2, reduces average handshake latency by **26–40%**, and increases peak throughput by **26%**. A supplementary scan of ten Vietnamese Fintech services reveals that 20% still lack TLS 1.3 support and 30% omit HSTS headers.

---

## Research Contributions

1. A **payment-specific threat model** targeting MITM attacks at the TLS transport layer, structured around protocol downgrade, cipher exploitation, and HSTS/OCSP bypass vectors.
2. A **reproducible, containerised testbed** enabling side-by-side comparison of TLS 1.2 and TLS 1.3 under controlled conditions, with shared certificate to isolate protocol behavior.
3. A **framework positioned against NIST SP 800-52r2, PCI DSS v4.0.1, and OWASP guidelines**, demonstrating that compliance-driven assessments alone miss configuration-specific risks — only a threat-model approach captures them. The framework adds threat-model scoring and load-based performance evaluation, two dimensions absent from all three standards.

---

## Four-Phase Assessment Framework

The framework is **threat-model-driven**: Phase 1 defines the adversary model that steers all subsequent phases.

```
Phase 1 – Threat Modelling              Phase 2 – Testbed Construction
  • MITM adversary model                  • Docker: Nginx TLS 1.2 endpoint
  • Protocol downgrade vector             • Docker: Nginx TLS 1.3 endpoint
  • Cipher exploitation vector            • FastAPI payment backend
  • HSTS/OCSP bypass vector               • Shared RSA-2048/SHA-256 certificate

Phase 3 – Multi-tool Scanning           Phase 4 – Risk Classification & Compliance
  • testssl.sh (vulnerability scan)       • Severity: Critical / High / Med / Low
  • SSLyze (cert & protocol analysis)     • Map findings to threat model (Ph. 1)
  • Locust (performance under load)       • NIST SP 800-52r2 / PCI DSS v4.0.1 / OWASP
  • Qualys SSL Labs (real-world scan)     • DevSecOps remediation output
```

---

## System Architecture

```
                        ┌────────────────────────────────────────┐
                        │         Docker Network (tls-net)       │
                        │                                        │
  Scanner / Locust ─────┤──► nginx-tls12 (:8443)  ─┐             │
                        │                            ├──► FastAPI│
  Scanner / Locust ─────┤──► nginx-tls13 (:9443)  ─┘  Backend    │
                        │                         (:8000)        │
                        │   testssl-scanner (sidecar)            │
                        └────────────────────────────────────────┘
```

| Service | Image | Role |
|---|---|---|
| `payment-api` | Custom FastAPI | Payment API: `POST /api/login`, `GET /api/balance`, `POST /api/transfer` |
| `nginx-tls12` | nginx:1.25-alpine | TLS 1.2-only reverse proxy (port 8443) |
| `nginx-tls13` | nginx:1.25-alpine | TLS 1.3-only reverse proxy (port 9443) |
| `testssl-scanner` | drwetter/testssl.sh | In-network security scanner sidecar |

**Locust traffic distribution:** 50% `GET /api/balance` · 30% `POST /api/login` · 20% `POST /api/transfer`

### TLS Configuration Parameters

| Parameter | TLS 1.2 Endpoint | TLS 1.3 Endpoint |
|---|---|---|
| Protocol | TLS 1.2 only | TLS 1.3 only |
| Cipher Suites | ECDHE-RSA-AES256-GCM-SHA384, ECDHE-RSA-AES128-GCM-SHA256, ECDHE-RSA-CHACHA20-POLY1305, DHE-RSA-AES256-SHA256, **DES-CBC3-SHA** | TLS_AES_256_GCM_SHA384, TLS_CHACHA20_POLY1305_SHA256, TLS_AES_128_GCM_SHA256 |
| Forward Secrecy | Config-dependent (ECDHE/DHE) | Enforced by protocol |
| HSTS | `max-age=31536000` | `max-age=31536000; preload` |
| OCSP Stapling | Enabled | Enabled |
| Certificate | RSA-2048, SHA-256 (shared) | RSA-2048, SHA-256 (shared) |
| 0-RTT Early Data | N/A | Disabled (replay risk) |

> Both endpoints share the same RSA-2048/SHA-256 certificate to isolate protocol behavior from certificate variables.

---

## Key Results

### Vulnerability Scan (testssl.sh)

| Severity | TLS 1.2 | TLS 1.3 |
|---|---|---|
| Critical | 2 | 0 |
| Medium | 2 | 0 |
| Low | 1 | 0 |
| OK | 28 | 31 |
| **Total** | **33** | **31** |

The 2 Critical findings in TLS 1.2 both originate from `DES-CBC3-SHA`: acceptance of 3DES and the resulting Sweet32 exposure. The 2 Medium findings concern HTTP compression (BREACH) and use of a non-AEAD CBC cipher suite. TLS 1.3 eliminates all four by design — these are architectural guarantees, not configuration choices.

### Cipher Suite Risk Classification

| Cipher Suite | Protocol | AEAD | Forward Secrecy | Risk |
|---|---|---|---|---|
| TLS_AES_256_GCM_SHA384 | 1.3 | ✓ | ✓ | None |
| TLS_CHACHA20_POLY1305_SHA256 | 1.3 | ✓ | ✓ | None |
| TLS_AES_128_GCM_SHA256 | 1.3 | ✓ | ✓ | None |
| ECDHE-RSA-AES256-GCM-SHA384 | 1.2 | ✓ | ✓ | None |
| ECDHE-RSA-AES128-GCM-SHA256 | 1.2 | ✓ | ✓ | None |
| ECDHE-RSA-CHACHA20-POLY1305 | 1.2 | ✓ | ✓ | None |
| DHE-RSA-AES256-SHA256 | 1.2 | ✗ | ✓ | **Medium** |
| DES-CBC3-SHA | 1.2 | ✗ | ✗ | **Critical** |

### Handshake Latency and Throughput (Locust Load Tests)

| Users | TLS | Avg (ms) | P95 (ms) | P99 (ms) | RPS | Fail % |
|---|---|---|---|---|---|---|
| 50 | 1.2 | 19.6 | 44 | 68 | 221.2 | 0.02 |
| 50 | 1.3 | **14.4** | **30** | **53** | 179.1 | 0.12 |
| 100 | 1.2 | 24.7 | 56 | 87 | 367.8 | 0.18 |
| 100 | 1.3 | **16.3** | **38** | **58** | 329.6 | 0.28 |
| 200 | 1.2 | 30.6 | 68 | 105 | 565.0 | 0.06 |
| 200 | 1.3 | **20.7** | **44** | **68** | 437.0 | 0.01 |
| 500 | 1.2 | 55.4 | 119 | 178 | 746.6 | 0.71 |
| 500 | 1.3 | **33.4** | **73** | **109** | **941.4** | 0.79 |

TLS 1.3 outperforms TLS 1.2 in latency at all concurrency levels (−26.5% at 50 users, −39.7% at 500 users), attributable to the 1-RTT vs. 2-RTT handshake. **Note:** at 50 users, TLS 1.3 shows lower throughput (179.1 vs. 221.2 RPS) despite its latency advantage — this is because the connection-reuse rate is low at minimal concurrency, where TLS 1.3's key exchange overhead is not yet amortised across enough parallel sessions. This reverses as concurrency scales: at 500 users TLS 1.3 achieves 941 RPS versus 747 RPS (+26.1%).

### Real-World Vietnamese Fintech Snapshot (Qualys SSL Labs)

| Service | Grade | TLS 1.2 | TLS 1.3 | HSTS | FS | OCSP Stapling | Known Vulns |
|---|---|---|---|---|---|---|---|
| MoMo | A | ✓ | ✓ | ✓ | ✓ | ✓ | None |
| VNPay | A | ✓ | ✓ | ✓ | ✓ | ✗ | None |
| ZaloPay | **A+** | ✓ | ✓ | ✓ | ✓ | ✓ | None |
| VietQR | **B** | ✓ | ✗ | ✗ | ✓ | ✗ | None |
| Vietcombank | A− | ✓ | ✓ | ✓ | ✓ | ✓ | None |
| Techcombank | A | ✓ | ✓ | ✓ | ✓ | ✓ | None |
| MB Bank | A− | ✓ | ✓ | ✗ | ✓ | ✗ | None |
| VPBank | **B** | ✓ | ✗ | ✗ | ✓ | ✗ | None |
| TPBank | A | ✓ | ✓ | ✓ | ✓ | ✓ | None |
| ACB | A− | ✓ | ✓ | ✓ | ✓ | ✗ | None |

**20%** of services lack TLS 1.3 · **30%** omit HSTS · **50%** lack OCSP stapling.

---

## Prerequisites

| Requirement | Version |
|---|---|
| Docker Desktop | 24.x+ |
| Python | 3.10+ |
| OpenSSL | 1.1.1+ |
| `mkcert` *(optional)* | any |

---

## Quickstart

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Run the full experiment pipeline (~10 minutes)
bash run-all.sh
```

The script runs all 6 steps automatically: certificate generation → Docker testbed → testssl.sh scans → SSLyze scans → Locust load tests (8 rounds) → chart generation.

---

## Project Structure

```
.
├── run-all.sh                  # One-click full pipeline
├── docker-compose.yml          # Service definitions
├── requirements.txt            # Python dependencies
├── backend/                    # FastAPI payment API
│   └── Dockerfile
├── nginx/
│   └── conf.d/
│       ├── tls12.conf          # TLS 1.2-only Nginx config
│       └── tls13.conf          # TLS 1.3-only Nginx config
├── certs/                      # Generated certificates (git-ignored)
├── scripts/
│   ├── locustfile.py           # Load test scenarios (balance, login, transaction)
│   ├── analyze-results.py      # Chart & table generation
│   └── scan-ssllabs.py         # Optional: real-world Qualys scan
└── results/                    # All outputs (git-ignored)
    ├── testssl_tls1{2,3}.json
    ├── sslyze_tls1{2,3}.json
    ├── locust_tls1{2,3}_u{50,100,200,500}_stats.csv
    └── charts/                 # Publication-ready PNG figures
```

---

## Reproducing Paper Figures Only

To regenerate all charts from existing result files without re-running scans:

```bash
python3 scripts/analyze-results.py
```

To run the optional Qualys SSL Labs scan against real-world Vietnamese Fintech endpoints:

```bash
python3 scripts/scan-ssllabs.py
```

---

## Cleanup

```bash
docker compose down
rm -rf certs/ results/     # optional
```

---

## Citation

```bibtex
@inproceedings{nguyen2026tls,
  title     = {Security Risk Assessment of {TLS} Configurations in {Fintech} Payment Systems:
               A Comparative Analysis of {TLS} 1.2 and {TLS} 1.3},
  author    = {Nguyen, Quoc Hung and Phan, Thien Khanh and Tran Huynh, Bao Tran
               and Bui, Anh Ngoc and Nguyen Ngoc, Thuy Linh},
  booktitle = {Proceedings of the International Conference on Smart Computing
               and Communication Technologies (ICSCCT)},
  year      = {2026},
  address   = {Vietnam}
}
```

---

## Acknowledgement

This research is supported by the University of Economics Ho Chi Minh City (UEH), Ho Chi Minh City, Vietnam.
