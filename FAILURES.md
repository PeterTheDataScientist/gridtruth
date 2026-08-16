# What did not work

An honest log. Added to as things break, not written retrospectively once everything works.

---

## Line-based parsing assumed the area and its time were on the same line

**What was tried.** The first parser read each line of the page's visible text and expected an area name and a time range together, as they appear in a written sentence ("Borrowdale 0900-1300").

**What happened.** Every notice in a table produced zero records. HTML tables flatten to one cell per line, so the parser saw a bare area name (no time, skipped) followed by a bare time range (no area, discarded). On the test fixture it found 5 possible notices and parsed 0 of them.

**Why it matters.** It would have failed silently in production. The run would have reported "0 new records" and looked like a quiet day rather than a broken parser. The only reason it was caught before launch is that the fixture test asserted specific expected areas rather than just "some notices were found".

**The fix.** The parser now carries a candidate area forward from the previous line and pairs it with a following time-only line, guarded by a plausibility check so boilerplate cannot become an area name. The check is deliberately conservative: a missed notice shows up in `unparsed` and is fixable, a garbage record in the public dataset is not.

**The lesson, which generalises.** Assert on content, never on counts. A test that checks "more than zero notices were parsed" would have passed against a parser that was inventing them.

---

## Lint passed locally and failed on CI, and the thing it caught was real

**What was tried.** `ruff>=0.6` in the dev extras, relying on ruff's default rule selection.

**What happened.** `ruff check src tests` passed locally and failed on the first CI run with 8 errors. The two environments had resolved different ruff versions, and the newer one's defaults included rules the older one did not.

**Why it matters, and it is not the lint.** The rule that fired was DTZ001, naive `datetime` construction. That is a real defect in this project specifically. Load shedding notices are published in Harare local time. NASA Black Marble granules are in UTC. Every verification join in this codebase crosses those two clocks, and a naive datetime makes that join silently wrong by two hours: an outage announced for 22:00 local would be compared against the satellite pass for 22:00 UTC, which is midnight local. The comparison would still produce a number, and the number would be nonsense.

**The fix, in two parts.**

1. The project is now timezone-aware end to end. `HARARE` is defined once, notice times are parsed as Harare local, and a naive `fallback_date` is coerced rather than accepted. Records serialise with an explicit offset (`2026-08-14T22:00:00+02:00`).
2. The ruff version is pinned and the rule set is named explicitly in `pyproject.toml` rather than inherited from whatever defaults the resolved version happens to ship. DTZ is in that set on purpose, with a comment saying why.

**The lesson.** An unpinned linter is a linter whose behaviour is decided by the release calendar. But the CI failure was still worth having: a stricter environment than the local one found a genuine bug on the first run, before a single real record had been written. Do not treat a red CI as noise to be silenced.


---

## The first live run produced exactly one record, and it was a sentence about geysers

**What was tried.** Point the parser at the three ZETDC pages and see what comes back.

**What happened.** Two pages produced nothing. The load shedding FAQ produced one notice:

> area: "Why are bills not going down despite all the shedding?"
> window: 2026-08-16 12:00 to 22:00 (+02:00)

The source line was a paragraph explaining that a geyser "contributes about 60-70% of the total bill". The time-range regex matched `60-70`, and `_to_time` wrapped it with `% 24` into a perfectly plausible 12:00 to 22:00 outage window. Nothing in the record looked malformed. It would have gone into a public dataset and stayed there.

**Why it happened.** The regex was written to be permissive so that unusual real formats would still match, and there was no validation step behind it. `page 3-4`, `sections 1-2` and any percentage range would all have produced outages.

**The fix.** A validation pass between matching and accepting. A bare small-number range is only a time if it says so: a colon or full stop, an am/pm marker, or the 4-digit HHMM form utility notices use. A range followed by `%` is rejected outright. Written hours above 23 and minutes above 59 are rejected before wrapping, not after. The real FAQ paragraph is now a regression test, verbatim.

**The second finding, which matters more than the bug.** With the false positive gone, the live run returns **zero notices from all three sources**, and mining the page links confirms why: ZETDC publishes no load shedding schedule anywhere on its website. The premise the project was built on, "the utility publishes notices we can archive", is false.

That is not a reason to stop. It reframes the work. An archive of announcements nobody makes is worthless, but a continuous public record showing that no schedule is published, alongside satellite observation of the cuts that happen regardless, is a stronger artefact than the original plan. The monitoring log became the primary dataset and the public page leads with the absence rather than hiding it.

**The lesson.** Test against the real source early, before building anything on top of an assumption about it. A synthetic fixture proved the parser worked. Only the live run proved there was nothing to parse.
