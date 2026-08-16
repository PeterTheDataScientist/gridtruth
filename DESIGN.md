# Design

## The question

Is this place darker than it normally is?

Not "how bright is it" and never "is it brighter than that other place". Absolute night-time brightness across Africa is mostly a map of population density and wealth. It would look authoritative and tell you nothing about electricity.

## Why satellite rather than utilities

Utilities across Africa publish little, publish inconsistently, or publish nothing. Zimbabwe's ZETDC states in its own FAQ that load "will be done outside the programme without notice", and then publishes no programme. An accountability project built on utility disclosure inherits every gap in that disclosure.

The VIIRS Day-Night Band has imaged every square kilometre of Africa every night since January 2012 at 500 m. One instrument, one calibration, no permission required, no country able to opt out. That property, not the imagery itself, is why this is the right basis for a continental record.

## The measurement unit is the city's lit footprint

This is the core decision and it was forced by a bug.

The first version took the median radiance of a fixed 0.3 degree box centred on each city. Cape Town returned 3.6 nW/cm2/sr against Johannesburg's 19.1, implying it was five times dimmer. It is not. Cape Town's box is 27 percent ocean and mountain, so more than a quarter of its pixels sit near zero and the median lands in the dark half. Cape Town's 90th percentile is 28.6 against Johannesburg's 33.4.

The box was measuring coastline.

So the unit became the city's own lit footprint, derived from its own data:

1. Stack every observation of that city's box.
2. Take the **90th percentile per pixel** across nights. That is each pixel's normal lit level. The 90th rather than the max, so one anomalous flare cannot define normal.
3. Keep pixels whose normal level clears `max(1.0 nW/cm2/sr, 15% of the city's own 99th percentile)`. An absolute floor excludes genuinely unlit ground; the relative term means a dim city's core still counts as its core.
4. Every night, compare each lit pixel to **its own** normal level.

Coastal cities, cities against escarpments, and cities with large rural fringes are all corrected by the same mechanism, because the mask comes from the data rather than from a hand-drawn boundary.

## The two published numbers

**`dark_share`** — the fraction of the city's lit footprint that fell below half its own normal level on a given night. This is the headline because it is legible: *what share of the normally-lit city was dark*.

**`lit_share`** — the mean ratio of observed to normal across the footprint, clipped at 1. A smoother measure that catches partial dimming rather than only the pixels crossing a threshold.

Both are bounded, both are relative to that city alone, and neither can be inflated by a city simply being large or rich.

## What can break the signal

Written before results exist, because the failure modes decide whether any number here survives review.

**Moon.** The archive product is not lunar-corrected, and full-moon nights raise apparent radiance across the whole scene. Handled two ways: observations are sampled near new moon (within roughly two days), and the computed lunar phase is stored on every observation so the effect is auditable rather than assumed away. The NASA VNP46A2 product is lunar-corrected and is the upgrade path.

**Cloud.** Cloud removes pixels and, worse, thin cloud dims them without removing them. Observations below 60 percent footprint coverage are discarded outright. This does not solve thin cloud, which is the single largest remaining source of false dimming, and the honest position is that a low single-night reading is more likely weather than a blackout.

**Baseline contamination.** If a city is shed most nights, its "normal" already includes outages and the departure shrinks. Using a 90th-percentile envelope rather than a mean is a partial defence, since it anchors on the brighter tail. It is not a complete one, and the sensitivity of every headline number to the envelope percentile has to be reported.

**Generators and solar.** Backup generation dims less during an outage and tracks wealth. This systematically under-detects outages in richer areas and richer cities. It is a bias with a socioeconomic gradient and it is stated wherever results are published, not buried.

**Growth versus dimming.** A city that electrifies new suburbs raises its own envelope, which mechanically lowers historical `lit_share`. Long time series need the envelope computed on a rolling window rather than the full history. Not yet implemented; the current build uses a single envelope across all observations, which is acceptable over three years and would not be over ten.

## Architecture

```
GitHub Actions (scheduled)
  └─ pipeline/extract.py    windowed COG reads from s3://globalnightlight
     │                      no credentials, ~250 KB per city-night
     └─ pixels.npz          checkpointed per night, resumable
        └─ pipeline/aggregate.py   envelope, footprint mask, per-night stats
           └─ data/places.json     small, committed, CC BY
              └─ docs/index.html   static dashboard, reads the JSON directly
```

Everything before the dashboard runs on GitHub Actions, free and unlimited on public repositories. The dashboard is a single static file with no framework and no build step, so it loads on a cheap phone over mobile data and there is nothing to wake up.

## Decisions, and what was rejected

**The open World Bank archive over NASA's product.** `s3://globalnightlight` needs no account at all, which means anyone can reproduce this from a clean machine. The cost is a roughly four month publication lag and no lunar or cloud correction. NASA VNP46A2 is scientifically cleaner and has a two-day lag, but requires an Earthdata login. Both are supported; the zero-auth path is the default so reproduction has no barrier.

**Google Earth Engine rejected outright** despite being the obvious tool. Its free tier forbids commercial use, fee-for-service work and operational services, which conflicts with the Apache 2.0 and CC BY licensing this project commits to.

**Real time rejected as a goal.** Nothing available gives less than a two-day lag. Reliability is a track-record question, so the lag costs nothing, and promising real time would be an overclaim that invites dismissal of everything else.

**Pixels stored, not summary statistics.** The first pipeline stored medians and had to be re-run from scratch when the method changed. Keeping arrays means a method change is a re-aggregation, not a re-download.
