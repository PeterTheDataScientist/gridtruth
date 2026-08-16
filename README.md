# GridWatch ZW

**Zimbabwe's utility says it sheds load "outside the programme without notice". It does not publish the programme. This measures the cuts anyway, from satellite night lights.**

**[Live monitoring page](https://peterthedatascientist.github.io/gridwatch-zw/)**

[![ingest](https://github.com/PeterTheDataScientist/gridwatch-zw/actions/workflows/ingest.yml/badge.svg)](https://github.com/PeterTheDataScientist/gridwatch-zw/actions/workflows/ingest.yml)
[![License: Apache 2.0](https://img.shields.io/badge/code-Apache%202.0-blue.svg)](LICENSE)
[![Data: CC BY 4.0](https://img.shields.io/badge/data-CC%20BY%204.0-green.svg)](data/LICENSE)

---

South Africa has EskomSePush and millions of people use it. Zimbabwe has nothing.

The first live run of this pipeline established why. ZETDC's website publishes **no machine-readable load shedding schedule at all**. Its Important Notices page carries tariffs, connection procedures and a token rollover. Its load shedding FAQ answers the question "Why is ZETDC not sticking to the schedules it advertised?" with the admission that "loading will be done outside the programme without notice".

So the utility states that unannounced load shedding happens, does not publish the programme those cuts depart from, and no public record exists of how often the two diverge. That is a stronger justification for this project than the one it started with, and it is documented in [FAILURES.md](FAILURES.md) rather than quietly designed around.

GridWatch ZW does three things:

1. **Monitors** the sources continuously and records every check, including the ones that find nothing. "Checked, and there was no schedule there" is the current finding, and it is only credible recorded continuously rather than asserted once. If a schedule ever appears it is archived permanently within six hours.
2. **Verifies** each announced outage against NASA Black Marble daily night-light radiance over the same suburb on the same night, so an announcement can be confirmed, contradicted, or found to have happened without being announced at all.
3. **Publishes** a monthly schedule reliability index by suburb.

The dataset is the point. Every day this runs, it becomes harder to replicate and more valuable. There is no other load shedding time series for Zimbabwe.

## Status

Monitoring is live and running every six hours. The satellite verification layer is designed but not built, and `EVALUATION.md` is deliberately empty apart from a pre-registered accuracy gate, so that the method cannot be chosen after seeing which one flatters the result.

There is no accuracy claim anywhere in this repository yet, on purpose. See [OBJECTIONS.md](OBJECTIONS.md) for ten arguments against this work, written before launch rather than after, including the one reality raised on day one.

## The verification idea, in one paragraph

NASA's Black Marble product (VNP46A2) gives daily, atmospherically corrected night-time radiance at roughly 500 m resolution, globally, free. A suburb under load shedding emits measurably less light than the same suburb on a comparable night. The comparison is not "is it dark" but "is it darker than this suburb's own recent baseline, controlling for moon phase, cloud cover and day of week". That turns a claim about a utility's behaviour into an observation problem that needs no cooperation from the utility.

This is the part that can fail, and the honest failure modes are documented in [DESIGN.md](DESIGN.md#what-can-break-the-verification-signal).

## Quick start

```bash
pip install -e ".[dev]"
python -m gridwatch --once     # check every source once and record the result
python -m gridwatch --show     # summarise what the dataset currently holds
pytest                                      # run the tests, no network needed
```

Nothing here needs an API key except the night-lights stage, which needs a free NASA Earthdata login.

## Data

| File | What it is | Licence |
|---|---|---|
| `data/raw/` | Byte-for-byte snapshots of every page fetched, timestamped. Provenance, never edited. | CC BY 4.0 |
| `data/processed/runs.jsonl` | One monitoring observation per source per check. Append only. This is the file that accumulates today. | CC BY 4.0 |
| `data/processed/notices.jsonl` | One parsed outage announcement per line. Append only. Currently empty, which is the finding. | CC BY 4.0 |
| `data/processed/observations.jsonl` | One night-light observation per suburb per night. | CC BY 4.0 |

Append-only JSONL committed to the repository, not a database. That is deliberate: git history is the provenance record, every change is diffable, it costs nothing, and anyone can clone the whole dataset without asking. It moves to object storage when it outgrows a repo, and that threshold is documented in `DESIGN.md`.

## Repository map

```
src/gridwatch/     ingestion, parsing, night-light verification, indexing
data/              the public dataset, append only
tests/             offline tests against saved fixtures
docs/              the public monitoring page, served by GitHub Pages
.github/workflows/ the scheduled pipeline
```

## Documents

- [DESIGN.md](DESIGN.md) — architecture, the decisions and why, what was rejected
- [EVALUATION.md](EVALUATION.md) — the numbers, the method, the held-out design
- [OBJECTIONS.md](OBJECTIONS.md) — the strongest arguments against this work, and the honest answers
- [FAILURES.md](FAILURES.md) — what was tried that did not work

## Licence

Code Apache 2.0. Data CC BY 4.0. Both chosen so that a company can use this without asking anyone's permission, which is the only licensing that leads to adoption.

## Commercial use

The code and data are free forever under the licences above. For hosted deployment, a private feed, or work built on top of this, contact [petermundowa.com](https://petermundowa.com).

## Citation

```bibtex
@software{mundowa_gridwatch_zw,
  author = {Mundowa, Peter Tinashe},
  title  = {GridWatch ZW: verifying Zimbabwe load shedding announcements from satellite night lights},
  url    = {https://github.com/PeterTheDataScientist/gridwatch-zw},
  year   = {2026}
}
```
