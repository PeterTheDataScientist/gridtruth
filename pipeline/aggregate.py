"""Turn stored pixel arrays into per-city series.

The measurement unit is each city's own lit footprint, not the geographic box it
sits in. That distinction is the whole method, for two reasons.

1. A fixed box mixes city with ocean, mountain and farmland in whatever ratio the
   local geography happens to give. Cape Town's box is 27 percent unlit, so its
   box median reads 3.6 nW/cm2/sr against Johannesburg's 19.1, which would say
   Cape Town is five times dimmer. It is not; its 90th percentile is 28.6 against
   Johannesburg's 33.4. The box was measuring coastline, not electricity.

2. Comparing cities on absolute brightness maps population density and wealth.
   Every number here is a city against its own history, never against another city.

So: build a per-pixel envelope from all of a city's observations, keep the pixels
that are lit in that envelope, and ask how far below their own normal they fell.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np

# Approximate lunar phase. Reference new moon 2000-01-06, synodic month 29.530589 d.
_REF = date(2000, 1, 6)
_SYN = 29.530588853

ENVELOPE_PCTL = 90      # per-pixel "normal lit" level, not the max, so one flare cannot set it
LIT_FLOOR = 1.0         # nW/cm2/sr, below this a pixel is not meaningfully lit
LIT_REL = 0.15          # or 15% of the city's own bright end, whichever is higher
DARK_AT = 0.5           # a pixel counts as dark below half its own normal


def lunar_phase(d: str) -> float:
    """0 = new moon, 0.5 = full. Uncorrected VIIRS radiance rises near full moon,
    so this is reported alongside every observation rather than hidden."""
    y, m, dd = int(d[:4]), int(d[4:6]), int(d[6:8])
    return round((((date(y, m, dd) - _REF).days) % _SYN) / _SYN, 3)


def build(pixels_path: str, places_path: str, out_path: str) -> None:
    places = json.load(open(places_path))
    with np.load(pixels_path) as z:
        keys = list(z.files)
        by_city: dict[str, list[tuple[str, np.ndarray]]] = defaultdict(list)
        for k in keys:
            city, d = k.rsplit("|", 1)
            by_city[city].append((d, z[k]))

    out = []
    for city, obs in sorted(by_city.items()):
        obs.sort(key=lambda t: t[0])
        shapes = {a.shape for _, a in obs}
        if len(shapes) > 1:  # window rounding can differ by a pixel between granules
            h = min(s[0] for s in shapes); w = min(s[1] for s in shapes)
            obs = [(d, a[:h, :w]) for d, a in obs]
        stack = np.stack([a for _, a in obs])            # (nights, rows, cols)

        # Per-pixel normal level, ignoring nights where that pixel was masked.
        with np.errstate(invalid="ignore"):
            envelope = np.nanpercentile(stack, ENVELOPE_PCTL, axis=0)

        thresh = max(LIT_FLOOR, LIT_REL * float(np.nanpercentile(envelope, 99)))
        lit = np.isfinite(envelope) & (envelope >= thresh)
        if lit.sum() < 25:            # too small a footprint to say anything
            continue

        env_lit = envelope[lit]
        series = []
        for d, arr in obs:
            vals = arr[lit]
            ok = np.isfinite(vals)
            if ok.sum() < lit.sum() * 0.6:
                continue
            ratio = np.clip(vals[ok] / env_lit[ok], 0, 2)
            series.append({
                "date": d,
                "lit_share": round(float(np.mean(np.clip(ratio, 0, 1))), 3),
                "dark_share": round(float(np.mean(ratio < DARK_AT)), 3),
                "mean_radiance": round(float(np.mean(vals[ok])), 2),
                "moon": lunar_phase(d),
                "coverage": round(float(ok.sum() / lit.sum()), 3),
            })
        if len(series) < 4:
            continue

        dark = [s["dark_share"] for s in series]
        lits = [s["lit_share"] for s in series]
        lon, lat = places[city]
        name, country = [p.strip() for p in city.split(",", 1)]
        out.append({
            "place": city, "city": name, "country": country, "lon": lon, "lat": lat,
            "lit_pixels": int(lit.sum()),
            "normal_radiance": round(float(np.mean(env_lit)), 2),
            "mean_dark_share": round(float(np.mean(dark)), 3),
            "worst_dark_share": round(float(np.max(dark)), 3),
            "mean_lit_share": round(float(np.mean(lits)), 3),
            "n": len(series),
            "series": series,
        })

    out.sort(key=lambda d: -d["mean_dark_share"])
    payload = {
        "generated": date.today().isoformat(),
        "method": (
            "Each city's lit footprint is derived from the 90th-percentile envelope of its "
            "own observations. dark_share is the fraction of that footprint falling below "
            "half its own normal level on a given night. Cities are never compared on "
            "absolute brightness."
        ),
        "params": {"envelope_pctl": ENVELOPE_PCTL, "lit_floor": LIT_FLOOR,
                   "lit_rel": LIT_REL, "dark_at": DARK_AT},
        "places": out,
    }
    Path(out_path).write_text(json.dumps(payload, indent=1))
    print(f"{len(out)} cities, {sum(p['n'] for p in out)} observations -> {out_path}")


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], sys.argv[3])
