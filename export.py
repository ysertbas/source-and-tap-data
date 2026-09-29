#!/usr/bin/env python3
"""
Builds towns.csv, town_systems.csv and systems.csv for the published dataset.

Reads (read-only) from the Source & Tap site repo:
  src/data/towns.json, src/data/systems.json, overrides.json

measurements.csv lives in this repo and is hand-verified; this script only reads
it to decide systems.csv's pfas_results_in_ccr flag. It is never rewritten.

Usage:
  python3 export.py --site ../source-and-tap --out .
"""
import argparse, csv, json, re, sys
from pathlib import Path

SITE_BASE = "https://sourceandtap.com"
STATE = "NJ"
POPULATION_SOURCE = "U.S. Census Bureau PEP Vintage 2025 (July 1, 2025)"
CCR_REPORT_YEAR = "2025"
# build_site_data.py TOWN_VERIFIED: service share checked by hand against utility sources
BASIS_MANUAL = "manual_verification"
BASIS_OVERLAP = "census_population_overlap"

# "NJ AMERICAN WATER - PENNS GROVE (NJ1707001, %86); PENNSVILLE TWSP. WATER DEPART. (NJ1708001, %14)"
OTHER_SYSTEM_RE = re.compile(r"^(?P<name>.+?)\s*\((?P<pwsid>[A-Z]{2}\d+),\s*%(?P<pct>[\d.]+)\)$")
DISPLAY_RE = re.compile(r"^(New Jersey American Water|Aqua New Jersey), (?P<rest>.+) system$")
OWNER_RAW = {"New Jersey American Water": "NJ AMERICAN WATER", "Aqua New Jersey": "AQUA NJ"}


def page_url(slug):
    # src/pages/nj/[slug].astro + astro.config.mjs trailingSlash: "always"
    return f"{SITE_BASE}/nj/{slug}/"


def operator(display_name):
    m = DISPLAY_RE.match(display_name)
    return m.group(1) if m else ""


def epa_name_from_display(display_name):
    """Invert build_site_data.py system_display() to recover the EPA name.

    system_display("NJ AMERICAN WATER - PENNS GROVE") -> "New Jersey American Water, Penns Grove system"
    so the reverse is the owner prefix plus the upper-cased remainder. The one EPA
    name that also appears raw in towns.json (NJ1707001) is used to check this.
    """
    m = DISPLAY_RE.match(display_name)
    if not m:
        return display_name.upper()
    rest = m.group("rest").replace(" / ", "/")  # system_display re-spaces slashes
    return f"{OWNER_RAW[m.group(1)]} - {rest.upper()}"


def parse_other_systems(text):
    out = []
    for part in text.split(";"):
        part = part.strip()
        if not part:
            continue
        m = OTHER_SYSTEM_RE.match(part)
        if not m:
            sys.exit(f"[export] ERROR: could not parse other_systems entry: {part!r}")
        out.append((m.group("name").strip(), m.group("pwsid"), round(float(m.group("pct")) / 100, 4)))
    return out


def share(v):
    return repr(round(float(v), 4))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="../source-and-tap", help="path to the site repo (read-only)")
    ap.add_argument("--out", default=".", help="where to write the CSVs")
    a = ap.parse_args()
    site, out = Path(a.site), Path(a.out)

    towns = json.loads((site / "src/data/towns.json").read_text(encoding="utf-8"))
    systems = json.loads((site / "src/data/systems.json").read_text(encoding="utf-8"))
    overrides = json.loads((site / "overrides.json").read_text(encoding="utf-8"))
    by_pwsid = {s["pwsid"]: s for s in systems}

    # overrides.json is the site's hand-verification file; every system it names must still exist
    for pid in overrides:
        if pid.startswith("_") or pid == "source_links":
            continue
        if pid not in by_pwsid:
            print(f"[export] WARNING: overrides.json has {pid}, which is not in systems.json")

    # EPA names: raw strings out of towns.json where available, otherwise reconstructed
    epa_names, reconstructed = {}, []
    for t in towns:
        for name, pid, _ in parse_other_systems(t["other_systems"] or ""):
            if epa_names.setdefault(pid, name) != name:
                print(f"[export] WARNING: two EPA names for {pid}: {epa_names[pid]!r} vs {name!r}")
    for s in systems:
        guess = epa_name_from_display(s["name"])
        if s["pwsid"] in epa_names:
            if epa_names[s["pwsid"]] != guess:
                print(f"[export] WARNING: {s['pwsid']} EPA name {epa_names[s['pwsid']]!r} != reconstruction {guess!r}")
        else:
            epa_names[s["pwsid"]] = guess
            reconstructed.append(s["pwsid"])

    ordered = sorted(towns, key=lambda t: (t["name"], t["county"]))

    # towns.csv
    with open(out / "towns.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["town", "official_name", "county", "state", "census_geoid", "population",
                    "population_source", "primary_pwsid", "page_url"])
        for t in ordered:
            w.writerow([t["name"], t["official_name"], t["county"], STATE, str(t["muni_geoid"]),
                        t["population"], POPULATION_SOURCE, t["pwsid"], page_url(t["slug"])])

    # town_systems.csv
    with open(out / "town_systems.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["census_geoid", "pwsid", "epa_system_name", "service_share", "share_basis"])
        for t in ordered:
            # service_verified is set for exactly the build_site_data.py TOWN_VERIFIED towns
            basis = BASIS_MANUAL if t.get("service_verified") else BASIS_OVERLAP
            rows = parse_other_systems(t["other_systems"] or "")
            if not rows:
                rows = [(epa_names.get(t["pwsid"], ""), t["pwsid"], t["primary_share"])]
            else:
                primary = [r for r in rows if r[1] == t["pwsid"]]
                if not primary:
                    sys.exit(f"[export] ERROR: {t['name']}: primary {t['pwsid']} not in other_systems")
                if abs(primary[0][2] - t["primary_share"]) > 1e-6:
                    print(f"[export] WARNING: {t['name']}: other_systems share {primary[0][2]} "
                          f"!= primary_share {t['primary_share']}")
            for name, pid, sh in rows:
                w.writerow([str(t["muni_geoid"]), pid, epa_names.get(pid, name), share(sh), basis])

    # systems.csv: only systems that serve a town as its primary system
    primary_ids = {t["pwsid"] for t in towns}
    measured = {r["pwsid"] for r in csv.DictReader(open(out / "measurements.csv", encoding="utf-8"))}
    with open(out / "systems.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pwsid", "system_name", "operator", "ccr_url", "ccr_report_year", "pfas_results_in_ccr"])
        for pid in sorted(primary_ids):
            s = by_pwsid.get(pid)
            if s is None:
                sys.exit(f"[export] ERROR: primary system {pid} missing from systems.json")
            url = (s["ccr_url"] or "").strip()
            if url and not url.startswith(("http://", "https://")):
                url = "https://" + url.lstrip("/")
            w.writerow([pid, s["name"], operator(s["name"]), url, CCR_REPORT_YEAR,
                        "true" if pid in measured else "false"])

    # --- checks ---
    print()
    ts = list(csv.DictReader(open(out / "town_systems.csv", encoding="utf-8")))
    sy = list(csv.DictReader(open(out / "systems.csv", encoding="utf-8")))
    print(f"1. towns.csv rows: {len(ordered)} {'OK' if len(ordered) == 41 else 'NOT 41'}")

    sums = {}
    for r in ts:
        sums[r["census_geoid"]] = sums.get(r["census_geoid"], 0) + float(r["service_share"])
    bad = {g: v for g, v in sums.items() if abs(v - 1.0) > 0.005}
    print(f"2. share sums per census_geoid: {len(sums)} geoids, "
          + ("all ~1.0 OK" if not bad else f"OFF: {bad}"))

    in_systems = {r["pwsid"] for r in sy}
    missing = sorted(measured - in_systems)
    print(f"3. measurements pwsids in systems.csv: {len(measured)} distinct, "
          + ("all present OK" if not missing else f"MISSING: {missing}"))

    print(f"   town_systems.csv rows: {len(ts)} | systems.csv rows: {len(sy)}")
    print(f"   manual_verification rows: {sum(1 for r in ts if r['share_basis'] == BASIS_MANUAL)}")
    print(f"   EPA names reconstructed from the site display name: {len(reconstructed)}/{len(sy)}")


if __name__ == "__main__":
    main()
