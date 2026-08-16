# GridTruth

**Which African cities go dark, and how often. Measured from orbit, so no utility has to agree to be measured.**

**[Open the dashboard](https://peterthedatascientist.github.io/gridtruth/)**

[![License: Apache 2.0](https://img.shields.io/badge/code-Apache%202.0-blue.svg)](LICENSE)
[![Data: CC BY 4.0](https://img.shields.io/badge/data-CC%20BY%204.0-green.svg)](data/LICENSE)

---

There is no open, comparable record of electricity reliability across Africa. Utilities publish little, publish inconsistently, or publish nothing. Zimbabwe's ZETDC answers the question "Why is ZETDC not sticking to the schedules it advertised?" by stating that load "will be done outside the programme without notice", and then publishes no programme at all.

So this stops asking. The VIIRS Day-Night Band has photographed every square kilometre of Africa every night since January 2012, at 500 m. One instrument, one calibration, no permission required.

## What it measures, and what it refuses to measure

**Every city is compared to its own baseline. Never to another city.**

That distinction is the entire project. A map coloured by absolute brightness is a map of population density and wealth, and it would look authoritative while meaning nothing. What this asks instead is: *is this place darker than it normally is?* That question is answerable for Harare and Lagos and a rural district alike, because each is only ever compared to itself.

The headline number per city is the share of its own baseline brightness it typically sits at. The baseline is the 75th percentile of that city's own observations, so one unusually clear night cannot define it.

## Status: preview, not a finding

Eight observation nights per city across 2024 and 2025, 26 cities. **No cloud masking or lunar correction applied yet.** A very low single reading is more likely to be weather than a blackout.

The method becomes a measurement at hundreds of nights per city with quality flags applied. It is published now because the pipeline works end to end and the data is real, not because the numbers are ready to cite.

## Known bias, stated up front

Generators and rooftop solar dim less during an outage, and they track wealth. This systematically under-detects outages in richer areas. Any published result carries that caveat or it is dishonest.

## Data

| Source | What | Licence | Account |
|---|---|---|---|
| World Bank Light Every Night, `s3://globalnightlight` | Nightly VIIRS DNB radiance, 2012 to Dec 2025, 15 arc-second COGs | Public domain | **none** |
| NASA VNP46A2 via LAADS | Daily, cloud and lunar corrected, ~2 day lag | Open | free Earthdata login |

The open archive needs no credentials at all. Granules are Cloud Optimized GeoTIFFs already on the standard grid, so a geographic window is read over HTTP without downloading the file: a 250 MB granule costs a few hundred kilobytes.

**Real time is not available from any source.** Two days is the floor. Reliability is a track-record question, so that costs nothing.

## Run it

```bash
pip install rasterio numpy
python pipeline/extract.py pipeline/places.json 20250815,20251204 > obs.json
```

No API key. No account.

## Repository map

```
pipeline/   extraction from the open satellite archive
data/       derived per-city series, CC BY 4.0
docs/       the dashboard, served by GitHub Pages
```

## Licence

Code Apache 2.0. Derived data CC BY 4.0. Both chosen so a company can build on this without asking anyone.

## Commercial use

Free forever under the licences above. For hosted deployment, a private feed, or custom regional analysis, contact [petermundowa.com](https://petermundowa.com).

## Citation

```bibtex
@software{mundowa_gridtruth,
  author = {Mundowa, Peter Tinashe},
  title  = {GridTruth: African electricity reliability measured from satellite night lights},
  url    = {https://github.com/PeterTheDataScientist/gridtruth},
  year   = {2026}
}
```
