# What did not work

An honest log. Added to as things break, not written retrospectively once everything works.

---

## Line-based parsing assumed the area and its time were on the same line

**What was tried.** The first parser read each line of the page's visible text and expected an area name and a time range together, as they appear in a written sentence ("Borrowdale 0900-1300").

**What happened.** Every notice in a table produced zero records. HTML tables flatten to one cell per line, so the parser saw a bare area name (no time, skipped) followed by a bare time range (no area, discarded). On the test fixture it found 5 possible notices and parsed 0 of them.

**Why it matters.** It would have failed silently in production. The run would have reported "0 new records" and looked like a quiet day rather than a broken parser. The only reason it was caught before launch is that the fixture test asserted specific expected areas rather than just "some notices were found".

**The fix.** The parser now carries a candidate area forward from the previous line and pairs it with a following time-only line, guarded by a plausibility check so boilerplate cannot become an area name. The check is deliberately conservative: a missed notice shows up in `unparsed` and is fixable, a garbage record in the public dataset is not.

**The lesson, which generalises.** Assert on content, never on counts. A test that checks "more than zero notices were parsed" would have passed against a parser that was inventing them.
