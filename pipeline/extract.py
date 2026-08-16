"""Pull per-city night-light radiance from the open VIIRS archive.

No credentials. Reads windows out of Cloud Optimized GeoTIFFs over HTTP, so a
250 MB granule costs a few hundred kilobytes of transfer.
"""
from __future__ import annotations

import os
import re
import sys
import json
import time
import urllib.request

os.environ.setdefault("AWS_NO_SIGN_REQUEST", "YES")
os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")

import numpy as np
import rasterio
from rasterio.windows import from_bounds

BUCKET = "https://globalnightlight.s3.amazonaws.com/"
VSI = "/vsicurl/" + BUCKET
BOX = 0.15  # degrees either side, so a 0.3 deg box, roughly 33 km


def granules(date: str) -> list[str]:
    """SVDNB radiance keys for one date, YYYYMMDD. Handles both prefix layouts."""
    ym = date[:6]
    for prefix in (f"npp_{ym}/SVDNB_npp_d{date}", f"{ym}/SVDNB_npp_d{date}"):
        url = f"{BUCKET}?list-type=2&prefix={prefix}&max-keys=300"
        try:
            xml = urllib.request.urlopen(url, timeout=90).read().decode()
        except Exception:
            continue
        keys = re.findall(r"<Key>([^<]+rade9\.co\.tif)</Key>", xml)
        if keys:
            return keys
    return []


def sample(date: str, places: dict[str, tuple[float, float]]) -> dict[str, dict]:
    """Median and p90 radiance in a small box around each place, for one night."""
    out: dict[str, dict] = {}
    for key in granules(date):
        if len(out) == len(places):
            break
        try:
            with rasterio.open(VSI + key) as src:
                b = src.bounds
                for name, (lon, lat) in places.items():
                    if name in out:
                        continue
                    # Bands span all longitudes but only a slice of latitude.
                    # Both checks are required; latitude alone matches the wrong side of the world.
                    if not (b.left <= lon <= b.right and b.bottom <= lat <= b.top):
                        continue
                    win = from_bounds(lon - BOX, lat - BOX, lon + BOX, lat + BOX, src.transform)
                    arr = src.read(1, window=win).astype("float64")
                    arr = np.where(arr <= -999, np.nan, arr)
                    valid = int(np.isfinite(arr).sum())
                    if valid < arr.size * 0.5:
                        continue  # mostly cloud or off-swath, not a measurement
                    out[name] = {
                        "median": round(float(np.nanmedian(arr)), 3),
                        "p90": round(float(np.nanpercentile(arr, 90)), 3),
                        "valid_frac": round(valid / arr.size, 3),
                    }
        except Exception:
            continue
    return out


if __name__ == "__main__":
    places = json.load(open(sys.argv[1]))
    dates = sys.argv[2].split(",")
    rows = []
    for d in dates:
        t = time.time()
        got = sample(d, {k: tuple(v) for k, v in places.items()})
        for name, vals in got.items():
            rows.append({"date": d, "place": name, **vals})
        print(f"{d}: {len(got):>2}/{len(places)} places  {time.time()-t:5.1f}s", file=sys.stderr)
    print(json.dumps(rows))
