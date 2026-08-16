# Evaluation

**Nothing here is filled in yet.** This file exists before the results do, so the evaluation design is fixed before any number is known. That ordering is the point: a method chosen after seeing which one gives the nicer answer is not a measurement.

## What gets measured

### 1. Ingestion completeness
Against a hand-labelled set of notices collected manually over the first collection period.

- Recall: notices in the manual set that the parser found
- Precision: parsed records that correspond to a real published notice
- Unparsed rate: blocks flagged as possible notices that could not be read

Reported per source. A recall figure with no precision figure is meaningless and neither is published alone.

### 2. Verification accuracy (the one that matters)
Calibrated on South African data, where the utility's own published stage history gives labelled outage windows at known times and places.

- True positive rate: labelled outages the night-light method detects
- False positive rate: non-outage nights flagged as outages
- Detection curve against outage duration: the method almost certainly cannot see a 2-hour cut and should be able to see an 8-hour one. Where that threshold sits is a headline result.
- Breakdown by cloud fraction, lunar phase, and area size in pixels

**Pre-registered gate.** If the method cannot separate a labelled outage of 4 hours or more from a non-outage night at better than 0.70 AUC on held-out areas, the verification claim is withdrawn and the project ships as a schedule archive only. That threshold is fixed now, before any result exists.

### 3. Reliability index stability
- Bootstrap confidence intervals on every published suburb-month value
- Sensitivity of each index value to the baseline definition, reported as a range across baseline methods, not a single number
- Test-retest: does the index for a past month change when recomputed with more recent data

## Slices, always reported

Per suburb. Per month. Per cloud-fraction band. Per outage-duration band. Per area size in pixels. A single headline number with no slices hides exactly the failure modes that matter, so the headline is never published alone.

## Failure cases

Every published result links to the specific nights and areas where the method got it wrong, verbatim, with the underlying radiance series. Not a summary of failures, the failures themselves.

## Held-out design

Areas, not nights, are held out. Holding out nights leaks, because an area's baseline is estimated from its own other nights and the model would be evaluated on areas it had effectively been fitted to. Entire suburbs are excluded from calibration and used only for the final measurement.
