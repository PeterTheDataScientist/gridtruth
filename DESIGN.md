# Design

## The question

Zimbabwe's utility publishes load shedding notices. Nobody knows how closely reality follows them. That gap is the whole project: not "when is the power going off" but "does the announcement mean anything".

Answering it needs three independent signals, and their disagreement is the product.

| Signal | Source | What it tells you | How it fails |
|---|---|---|---|
| Announced | ZETDC notices | What was promised | Published irregularly, format changes, can be withdrawn |
| Reported | Crowdsourced | What people experienced | Sparse, self-selected, poisonable |
| Observed | NASA Black Marble night lights | What a satellite saw | Coarse, cloud-blocked, moon-sensitive |

No single one is trustworthy. Two agreeing against the third is informative. That is the design.

## Architecture

```
GitHub Actions (cron)
  └─ fetch      → content-addressed snapshot in data/raw/
     └─ parse   → Notice records
        └─ store → append-only JSONL, dedup by content hash
                     ↓
Night-lights job (separate schedule, NASA Earthdata)
  └─ VNP46A2 daily granule → per-area radiance → Observation records
                     ↓
              derived index (monthly, per suburb)
                     ↓
        Cloudflare Worker API → Cloudflare Pages front end
```

Everything before the API runs on GitHub Actions, which is free and unlimited on public repositories. There is no server to pay for and nothing to remember to renew.

## Decisions, and what was rejected

**The dataset is JSONL in git, not a database.** Git history is the provenance record, every change is diffable, cloning gets you the whole archive with no credentials, and it costs nothing. Rejected: Postgres on a free tier, because free Postgres tiers pause on inactivity or expire (Render's free database is deleted 30 days after creation), and a dataset that can silently vanish is not a dataset. Migration threshold: when `data/processed/` exceeds roughly 200 MB or a single file exceeds 50 MB, raw snapshots move to object storage and the repo keeps only the processed records.

**Records are content-addressed.** A record's id is a hash of area, start, end and source. Re-running ingestion cannot duplicate rows, so the schedule can be aggressive without corrupting the archive, and a re-fetch that changes the snapshot hash does not create phantom records. This is tested, not assumed.

**The parser fails loudly and partially.** Anything that looks like a notice but cannot be read is returned in `unparsed` and counted in the run report. A run that produces zero notices because the page changed is then distinguishable from a run that produced zero because there were none. Rejected: a strict parser that raises on unexpected input, because one format change would stop collection entirely, and the archive is the asset.

**Areas are normalised conservatively.** Known spelling variants collapse (Mt / Mount). Fuzzy matching does not happen. A wrong join silently corrupts a suburb's history; a missed join is visible and fixable later.

**Raw bytes are kept forever.** Reparsing the entire history after a parser fix has to be possible. Snapshots are content-addressed so an unchanged page costs nothing to keep.

## What can break the verification signal

Written up front because these determine whether the central claim survives.

**Spatial resolution.** VNP46A2 is roughly 500 m per pixel. Small suburbs are a handful of pixels. Per-suburb per-night verdicts are not defensible; suburb-month aggregates are. The repository reports observations nightly and confidence only monthly.

**Cloud.** The rainy season removes whole weeks. The product ships a mandatory quality flag per pixel per night; flagged pixels are excluded rather than imputed, and the excluded fraction is reported alongside every index value.

**Moon.** Lunar illumination changes background radiance by more than the effect being measured. VNP46A2 is already lunar-BRDF corrected, which handles the bulk of it. Residual lunar sensitivity is checked by regressing residuals on lunar phase and reporting the coefficient.

**Baseline contamination.** This is the hardest one. If a suburb is shed most nights, a rolling-mean baseline is itself a shed baseline and the departure vanishes. The baseline is therefore built from nights the schedule says the area was not shed, using an upper envelope of comparable nights rather than a mean. That is an assumption, so its effect gets an ablation and every headline number carries its sensitivity to the baseline definition.

**Generators and other light sources.** A suburb with widespread generator or solar backup dims less. This biases toward under-detecting outages in wealthier areas, which is a systematic bias with a socioeconomic gradient and must be stated wherever results are published, not buried.

**No ground truth in Zimbabwe.** Which is why the method is calibrated in South Africa first, where the utility's own published stage history provides a large labelled set, and only then applied here. Error rates are measured where labels exist and carried across with that caveat attached.

## Refresh loop

The project is designed to keep working with no attention.

- Ingestion runs on a GitHub Actions schedule. Public repo, so the minutes are free and unlimited.
- A heartbeat ping fires on every successful run. A missed heartbeat raises an alert, so a silently dead cron becomes a loud one.
- Scheduled workflows are disabled by GitHub after 60 days of repository inactivity, so a separate monthly job commits a timestamp to keep the repo active. This is a real failure mode that kills many scheduled scrapers quietly.
- Cron fires at an odd minute rather than on the hour, because scheduled runs at the top of the hour are queued and can drift by half an hour or more.

## Privacy

Crowdsourced reports store an area and a timestamp. No account, no phone number, no precise location, no device identifier. The published dataset contains no personal data of any kind, which is both the right default and the thing that makes the CC BY release possible without qualification.
