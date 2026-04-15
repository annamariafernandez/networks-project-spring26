"""
RTT vs. Speed-of-Light
Networks Assignment — Measurement & Geography

Run with: python rtt_speedoflight.py   (no sudo needed)
Requires: pip install requests matplotlib numpy
"""

import math, time, os, requests, numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import urllib.request

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

TARGETS = {
"Tokyo": {"url": "http://www.google.co.jp", "coords": (35.6762, 139.6503), "continent": "Asia"},
    "São Paulo": {"url": "http://www.google.com.br", "coords": (-23.5505, -46.6333), "continent": "S. America"},
    "Lagos": {"url": "http://www.google.com.ng", "coords": (6.5244, 3.3792), "continent": "Africa"},
    "Frankfurt": {"url": "http://www.google.de", "coords": (50.1109, 8.6821), "continent": "Europe"},
    "Sydney": {"url": "http://www.google.com.au", "coords": (-33.8688, 151.2093), "continent": "Oceania"},
    "Mumbai": {"url": "http://www.google.co.in", "coords": (19.0760, 72.8777), "continent": "Asia"},
    "London": {"url": "http://www.google.co.uk", "coords": (51.5074, -0.1278), "continent": "Europe"},
    "Singapore": {"url": "http://www.google.com.sg", "coords": (1.3521, 103.8198), "continent": "Asia"},

    # NEW TARGETS
    "Sendai": {"url": "http://www.tohoku.ac.jp", "coords": (38.2682, 140.8694), "continent": "Asia"},
    "Seoul": {"url": "http://www.snu.ac.kr", "coords": (37.5665, 126.9780), "continent": "Asia"},
    "New Delhi": {"url": "http://www.iitd.ac.in", "coords": (28.6139, 77.2090), "continent": "Asia"},
    "Santiago": {"url": "http://www.uchile.cl", "coords": (-33.4489, -70.6693), "continent": "S. America"},
    "Johannesburg": {"url": "http://www.wits.ac.za", "coords": (-26.2041, 28.0473), "continent": "Africa"},
    "Berlin": {"url": "http://www.fu-berlin.de", "coords": (52.5200, 13.4050), "continent": "Europe"},
    "London (Imperial)": {"url": "http://www.imperial.ac.uk", "coords": (51.5074, -0.1278), "continent": "Europe"},
    "Canberra": {"url": "http://www.anu.edu.au", "coords": (-35.2809, 149.1300), "continent": "Oceania"},
}

PROBES           = 15
FIBER_SPEED_KM_S = 200_000
FIGURES_DIR      = "figures"

CONTINENT_COLORS = {
    "Asia":      "#e63946",
    "S. America":"#2a9d8f",
    "Africa":    "#e9c46a",
    "Europe":    "#457b9d",
    "Oceania":   "#a8dadc",
}

# ─────────────────────────────────────────────
# TASK 1 — MEASURE RTTs
# ─────────────────────────────────────────────

def measure_rtt(url: str, probes: int = PROBES) -> dict:
    samples = []
    lost = 0

    for _ in range(probes):
        try:
            start = time.perf_counter()
            urllib.request.urlopen(url, timeout=3)
            elapsed_ms = (time.perf_counter() - start) * 1000
            samples.append(elapsed_ms)
        except:
            lost += 1

        time.sleep(0.2)

    if not samples:
        return {
            "min_ms": None,
            "mean_ms": None,
            "median_ms": None,
            "loss_pct": 100.0,
            "samples": []
        }

    return {
        "min_ms": float(np.min(samples)),
        "mean_ms": float(np.mean(samples)),
        "median_ms": float(np.median(samples)),
        "loss_pct": (lost / probes) * 100,
        "samples": samples
    }

 
# ─────────────────────────────────────────────
# TASK 2 — HAVERSINE + INEFFICIENCY
# ─────────────────────────────────────────────

def great_circle_km(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def get_my_location():
    try:
        r = requests.get("https://ipinfo.io/json", timeout=5).json()
        lat, lon = map(float, r["loc"].split(","))
        return lat, lon, r.get("city", "Your Location")
    except:
        return 42.3601, -71.0589, "Boston"


def compute_inefficiency(results, src_lat, src_lon):
    for city, data in results.items():
        lat2, lon2 = data["coords"]

        dist = great_circle_km(src_lat, src_lon, lat2, lon2)
        data["distance_km"] = dist

        theoretical = (dist / FIBER_SPEED_KM_S) * 2 * 1000
        data["theoretical_min_ms"] = theoretical

        med = data.get("median_ms")

        if med is None:
            data["inefficiency_ratio"] = None
            data["high_inefficiency"] = False
        else:
            ratio = med / theoretical
            data["inefficiency_ratio"] = ratio
            data["high_inefficiency"] = ratio > 3.0

    return results


# ─────────────────────────────────────────────
# TASK 3 — PLOTS
# ─────────────────────────────────────────────
def make_plots(results):
    os.makedirs(FIGURES_DIR, exist_ok=True)

    valid = {c: d for c, d in results.items() if d.get("median_ms") is not None}
    cities = sorted(valid, key=lambda c: valid[c]["distance_km"])

    # Figure 1
    fig, ax = plt.subplots(figsize=(11, 6))
    x = np.arange(len(cities))
    width = 0.35

    measured = [valid[c]["median_ms"] for c in cities]
    theoretical = [valid[c]["theoretical_min_ms"] for c in cities]

    ax.bar(x - width/2, measured, width, label="Measured RTT")
    ax.bar(x + width/2, theoretical, width, label="Theoretical RTT")

    ax.set_xticks(x)
    ax.set_xticklabels(cities, rotation=30)
    ax.set_ylabel("RTT (ms)")
    ax.set_title("Measured vs Theoretical RTT")
    ax.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "fig1_rtt_comparison.png"))
    plt.close()

    # Figure 2
    fig, ax = plt.subplots(figsize=(10, 7))

    for city in cities:
        d = valid[city]
        color = CONTINENT_COLORS[d["continent"]]

        ax.scatter(d["distance_km"], d["median_ms"], color=color)
        ax.text(d["distance_km"], d["median_ms"], city, fontsize=8)

    distances = np.linspace(0, max([valid[c]["distance_km"] for c in cities]), 100)
    theoretical_line = (distances / FIBER_SPEED_KM_S) * 2 * 1000

    ax.plot(distances, theoretical_line, linestyle="--", color="black", label="Theoretical Min")

    ax.set_xlabel("Distance (km)")
    ax.set_ylabel("RTT (ms)")
    ax.set_title("RTT vs Distance")

    patches = [mpatches.Patch(color=color, label=cont) for cont, color in CONTINENT_COLORS.items()]
    ax.legend(handles=patches + [mpatches.Patch(color="black", label="Theoretical Min")])

    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "fig2_distance_scatter.png"))
    plt.close()

    print("Figures saved.")


def main():
    src_lat, src_lon, src_city = get_my_location()
    print(f"Your location: {src_city} ({src_lat:.4f}, {src_lon:.4f})\n")

    results = {}
    for city, info in TARGETS.items():
        print(f"Probing {city} ({info['url']}) ...", end=" ", flush=True)
        stats = measure_rtt(info["url"])
        results[city] = {**stats, "coords": info["coords"], "continent": info["continent"]}
        med = stats.get("median_ms")
        print(f"median={med:.1f} ms  loss={stats['loss_pct']:.0f}%" if med else "unreachable")

    results = compute_inefficiency(results, src_lat, src_lon)

    print(f"\n{'City':<14} {'Dist km':>8} {'Median ms':>10} {'Theor. ms':>10} {'Ratio':>7}")
    print("─" * 55)
    for city, d in sorted(results.items(), key=lambda x: x[1].get("distance_km", 0)):
        dist  = d.get("distance_km", 0)
        med   = d.get("median_ms")
        theor = d.get("theoretical_min_ms")
        ratio = d.get("inefficiency_ratio")
        flag  = " ⚠️" if d.get("high_inefficiency") else ""
        print(f"{city:<14} {dist:>8.0f} "
              f"{(f'{med:.1f}' if med else 'N/A'):>10} "
              f"{(f'{theor:.1f}' if theor else 'N/A'):>10} "
              f"{(f'{ratio:.2f}' if ratio else 'N/A'):>7}{flag}")

    make_plots(results)

if __name__ == "__main__":
    main()


