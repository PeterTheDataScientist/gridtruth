# Objections

The strongest arguments against this work, written before launch. Each gets the honest answer or the honest concession, and concessions are marked as such.

This file was rewritten when the project's scope changed from a Zimbabwe schedule archive to a continental measurement. The old objections were answered by reality rather than by argument, which is the point of writing them down.

---

## 1. "Night lights measure light, not electricity. Your headline is a category error."

**The concession, and it is real.** A pixel can be dark because nobody lives there, because it is cloudy, because the moon is down, because a streetlight failed, or because the power is out. VIIRS cannot distinguish these.

**The answer.** Which is why nothing here is called an outage. The published quantity is `dark_share`: the fraction of a city's normally-lit footprint that fell below half its own normal level. That is a statement about observed light and nothing more. The inference to electricity is left to the reader, with the confounds listed on the same page.

The design does two things to make the light measurement itself sound. Each pixel is compared to its own history, so a permanently unlit area never enters. And observations are sampled near new moon with lunar phase recorded, so the largest systematic driver is controlled rather than ignored.

## 2. "Thin cloud will masquerade as a blackout and you cannot tell the difference."

**The concession. This is the biggest unsolved problem in the project.** Cloud that removes pixels is detectable and those observations are discarded. Thin cloud that dims pixels without removing them is not, and it produces exactly the signature of a partial outage.

**What is done.** Observations below 60 percent footprint coverage are discarded. Nothing else, yet.

**What is honest.** A single low reading is more likely weather than a blackout, and the dashboard says so in those words. The signal only becomes a measurement across many nights, where cloud is closer to random and outages are not. The NASA VNP46A2 product ships a per-pixel cloud mask and is the upgrade path; until it is wired in, no single-night claim should be made and none is.

## 3. "You are comparing Lagos to Lilongwe and calling it a result."

**The answer, and it is the whole design.** No absolute brightness comparison appears anywhere. Every number is a city against its own 90th-percentile envelope. Cairo's 52 nW/cm2/sr and Bulawayo's 9.6 never meet.

This is not a detail. A map of Africa coloured by raw radiance is a map of wealth and population density, it looks authoritative, and it is worthless for this question. The rejection of that map is the reason the project can say anything at all.

## 4. "Generators and solar mean you are measuring who can afford backup."

**The concession, unqualified.** Backup generation dims less during an outage, and it tracks wealth both within a city and between countries. This systematically under-detects outages in richer areas.

**What follows from it.** The bias is stated wherever results are published rather than buried in a methods note, because a reader who does not know it will draw the wrong conclusion in a predictable direction. It also means the "which suburb should I move to" use case is the weakest one this project supports: the answer it produces is partly an artefact of who owns a generator. Businesses siting operations, researchers, journalists and lenders are better served, because they can hold the caveat.

## 5. "A city that grows electrification looks like a city that is dimming."

**A real methodological hazard and it is not yet solved.** The envelope is computed across the full observation history. A city that lights new suburbs raises its own envelope, mechanically lowering its historical `lit_share`.

Over three years the effect is small. Over ten it would dominate. The fix is a rolling envelope window rather than a single global one, and it is not implemented. Any statement about long-run trend is unsupported until it is.

## 6. "The archive stops in December 2025, so this is history, not monitoring."

**Correct.** The zero-account archive has roughly a four-month publication lag and currently ends in December 2025.

**The answer.** Reliability is a track-record question. Nobody chooses where to site a factory based on last night. But the objection lands against any framing of this as an operational service, and the dashboard therefore does not claim to tell you whether your power is out now. The NASA daily product closes the gap to two days for anyone who registers, and two days is the floor that exists anywhere.

## 7. "Eight nights per city is a demo you have dressed up as a dataset."

**Concession, and it was true of the first published version.** It is why the page carried, and carries, a prominent statement that nothing on it is a finding.

The current collection samples every lunation from 2022 onward. The honest threshold is not a number I get to pick after seeing the results: before any city-level claim is published, the confidence interval on its `dark_share` has to be reported alongside it, and where that interval spans the difference between cities the claim is that they cannot be distinguished.

## 8. "Nobody asked for this and no utility will acknowledge it."

**Probably true of the utilities, and it does not matter.** The measurement does not require cooperation, which is the entire reason it exists. A utility that improves shows up as improving; the method is not adversarial and has no view.

On demand: the users this is built for are not utilities. They are businesses deciding where to put cold chain or manufacturing, lenders pricing infrastructure risk, researchers who currently have no comparable continental series, and journalists who can presently only report anecdote. None of them can get this anywhere else today.

## 9. "One person, no funding. This dies in three months."

**The answer is infrastructure, not intention.** Collection runs on GitHub Actions, free and unlimited on public repositories, with no server anyone has to remember to pay for. The dataset is committed to the repository, so a gap is visible in the history rather than hidden. Pixel arrays are checkpointed per night, so an interrupted run resumes rather than restarting.

That does not guarantee survival. It guarantees that if it stops, anyone can see exactly when and exactly how much data exists.

## 10. "Your dashboard is prettier than your evidence."

**The sharpest objection on the list, and the one to keep re-asking.** A clean map with confident colours implies more certainty than eight cloudy nights support. Presentation quality and evidence quality are independent, and it is entirely possible to ship a beautiful interface over a weak measurement.

**The mitigation, which is deliberately unsubtle.** The caveat sits in the page body in its own bordered block, not in a footer, and it says "nothing here is a finding" in those words. The README leads with "preview, not a finding". If those ever get quietly softened while the numbers stay thin, this objection has won.
