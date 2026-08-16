# Evaluation

**Nothing here is filled in yet.** The file exists before the results do, so the evaluation design is fixed before any number is known. That ordering is the point: a method chosen after seeing which one gives the nicer answer is not a measurement.

## The pre-registered gate

South Africa is the validation bed, because it is the only country in the region with a large public archive of announced load shedding stages at known times. That gives labelled nights: stage 4 and above means widespread scheduled outages; stage 0 means none.

**The gate.** Compare `dark_share` on labelled high-stage nights against labelled stage-0 nights, on held-out cities.

- If the separation reaches **AUC 0.70 or better**, the light measurement carries information about load shedding and city-level reporting proceeds.
- If it does not, the electricity interpretation is withdrawn publicly and the project ships as what it demonstrably is: an open record of how African cities' night-time brightness varies against their own baselines. That is still a dataset nobody else publishes.

This threshold is fixed now, before the comparison has been run once.

## What gets measured

**1. Discrimination.** ROC AUC of `dark_share` against labelled outage nights, reported with a bootstrap confidence interval, on cities excluded from any tuning.

**2. The confound decomposition.** How much of the variance in `dark_share` is explained by lunar phase, by footprint coverage as a cloud proxy, and by season, before any electricity claim is made. If cloud and moon explain most of it, that is the finding.

**3. Sensitivity to the method's own parameters.** Every headline number recomputed across:
- envelope percentile 75, 90, 95
- lit threshold floor 0.5, 1.0, 2.0 nW/cm2/sr
- dark threshold 0.3, 0.5, 0.7 of normal

Reported as a range, not a point. If a city's rank moves materially across that grid, its rank is not a result.

**4. Stability.** Does a city's figure for a past period change when recomputed with more recent data? For a fixed global envelope it will, which is the growth confound in Objection 5. The size of that drift is measured rather than assumed small.

## Slices, always reported

Per city. Per month. Per lunar-phase band. Per coverage band. Per city footprint size in pixels. A single headline with no slices hides precisely the failure modes that matter, so the headline is never published alone.

## Uncertainty

Every published `dark_share` carries a bootstrap confidence interval over nights. Where two cities' intervals overlap, the published statement is that they cannot be distinguished. No ranking is presented as ordinal where the intervals do not support it.

## Failure cases

Every published result links to the specific city-nights where the method disagreed with the South African labels, with the underlying pixel statistics. Not a count of failures, the failures themselves.

## Held-out design

**Cities are held out, never nights.** Holding out nights leaks, because a city's envelope is estimated from its own other nights, so the model would be evaluated on cities it had effectively been fitted to. Entire cities are excluded from any parameter choice and used only for the final measurement.
