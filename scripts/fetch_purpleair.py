#!/usr/bin/env python3
"""Fetch Portland-area PurpleAir sensors and keep ~7 days of hourly AQI history.

Usage: fetch_purpleair.py PREV_JSON OUT_JSON   (needs env PURPLEAIR_API_KEY)
"""
import json, os, sys, time, urllib.parse, urllib.request

API = "https://api.purpleair.com/v1/sensors"
BBOX = {"nwlng": -122.85, "nwlat": 45.65, "selng": -122.47, "selat": 45.43}
KEEP_SECONDS = 7 * 86400
HISTORY_STEP = 3300  # add a history point roughly once an hour

# US EPA PM2.5 -> AQI breakpoints (2024)
BREAKS = [(0, 9, 0, 50), (9.1, 35.4, 51, 100), (35.5, 55.4, 101, 150),
          (55.5, 125.4, 151, 200), (125.5, 225.4, 201, 300), (225.5, 500, 301, 500)]


def pm_to_aqi(c):
    if c is None:
        return None
    c = max(0.0, int(c * 10) / 10)
    for lo, hi, a_lo, a_hi in BREAKS:
        if c <= hi:
            return round((a_hi - a_lo) / (hi - lo) * (c - lo) + a_lo)
    return 500


def epa_correct(cf1, rh):
    """EPA correction for PurpleAir PM2.5 (cf_1) using humidity."""
    if cf1 is None:
        return None
    if rh is None:
        return cf1
    return 0.524 * cf1 - 0.0862 * rh + 5.75 if cf1 < 343 else cf1


def main():
    prev_path, out_path = sys.argv[1], sys.argv[2]
    key = os.environ["PURPLEAIR_API_KEY"]

    try:
        with open(prev_path) as f:
            prev = {s["id"]: s for s in json.load(f).get("sensors", [])}
    except Exception:
        prev = {}

    params = {"fields": "name,latitude,longitude,pm2.5_cf_1,humidity",
              "location_type": 0, "max_age": 3600, **BBOX}
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params),
                                 headers={"X-API-Key": key})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)

    ix = data["fields"].index
    now = int(time.time())
    sensors = []
    for row in data["data"]:
        sid = row[ix("sensor_index")]
        lat, lon = row[ix("latitude")], row[ix("longitude")]
        pm = epa_correct(row[ix("pm2.5_cf_1")], row[ix("humidity")])
        aqi = pm_to_aqi(pm)
        if lat is None or lon is None or aqi is None:
            continue
        hist = [h for h in prev.get(sid, {}).get("hist", []) if h[0] >= now - KEEP_SECONDS]
        if not hist or now - hist[-1][0] >= HISTORY_STEP:
            hist.append([now, aqi])
        sensors.append({"id": sid, "name": row[ix("name")], "lat": lat, "lon": lon,
                        "aqi": aqi, "pm": round(pm, 1), "hist": hist})

    with open(out_path, "w") as f:
        json.dump({"updated": now, "sensors": sensors}, f, separators=(",", ":"))
    print(f"Wrote {len(sensors)} sensors")


if __name__ == "__main__":
    main()
