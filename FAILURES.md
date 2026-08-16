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
