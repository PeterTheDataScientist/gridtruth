"""Pull per-city night-light pixels from the open VIIRS archive.

No credentials. Reads windows out of Cloud Optimized GeoTIFFs over HTTP, so a
250 MB granule costs a few hundred kilobytes of transfer.

Why this stores pixel arrays rather than a summary statistic
------------------------------------------------------------
The first version took the median of a fixed 0.3 degree box. That is wrong for
any city whose box contains a lot of unlit ground. Cape Town's box is 27 percent
ocean and mountain, so its median landed in the dark half at 3.6 nW/cm2/sr while
Johannesburg read 19.1, implying Cape Town is five times dimmer than Johannesburg.
It is not. Cape Town's 90th percentile is 28.6 against Johannesburg's 33.4.

The unit of measurement has to be the city's own lit footprint, not a square drawn
around its centre. So this stage keeps the pixels and `aggregate.py` derives a
per-city mask from them. Coastal cities, cities against escarpments and cities
with large rural fringes are all handled by the same correction.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

os.environ.setdefault("AWS_NO_SIGN_REQUEST", "YES")
os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")

import numpy as np
import rasterio
from rasterio.windows import from_bounds

BUCKET = "https://globalnightlight.s3.amazonaws.com/"
VSI = "/vsicurl/" + BUCKET
BOX = 0.15  # degrees either side, a 0.3 degree box, roughly 30 km
MIN_VALID = 0.5  # reject an observation if more than half the box is off-swath or masked


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


def sample_night(date: str, places: dict[str, tuple[float, float]]) -> dict[str, np.ndarray]:
    """Pixel array for each place on one night. Missing places simply do not appear."""
    out: dict[str, np.ndarray] = {}
    for key in granules(date):
        if len(out) == len(places):
            break
        try:
            with rasterio.open(VSI + key) as src:
                b = src.bounds
                for name, (lon, lat) in places.items():
                    if name in out:
                        continue
                    # Bands span every longitude but only a slice of latitude.
                    # Both checks are required; latitude alone matches the far side of the world.
                    if not (b.left <= lon <= b.right and b.bottom <= lat <= b.top):
                        continue
                    win = from_bounds(lon - BOX, lat - BOX, lon + BOX, lat + BOX, src.transform)
                    arr = src.read(1, window=win).astype("float32")
                    arr = np.where(arr <= -999, np.nan, arr)
                    if np.isfinite(arr).sum() < arr.size * MIN_VALID:
                        continue
                    out[name] = arr
        except Exception:
            continue
    return out


def main() -> int:
    places_path, dates_arg, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    places = {k: tuple(v) for k, v in json.load(open(places_path)).items()}
    dates = dates_arg.split(",")

    store: dict[str, np.ndarray] = {}
    existing = Path(out_path)
    if existing.exists():
        with np.load(existing) as z:
            store = {k: z[k] for k in z.files}
        print(f"resuming with {len(store)} existing observations", file=sys.stderr)

    for d in dates:
        if any(k.endswith("|" + d) for k in store):
            print(f"{d}: already collected, skipping", file=sys.stderr)
            continue
        t = time.time()
        got = sample_night(d, places)
        for name, arr in got.items():
            store[f"{name}|{d}"] = arr
        print(f"{d}: {len(got):>2}/{len(places)} places  {time.time()-t:5.1f}s", file=sys.stderr)
        np.savez_compressed(out_path, **store)  # checkpoint every night, runs are resumable

    print(f"stored {len(store)} observations to {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
