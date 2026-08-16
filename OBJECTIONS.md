# Objections

The strongest arguments against this project, written before launch. Each one gets the honest answer or the honest concession. Where the answer is a concession, it is marked as one.

---

## 1. "Night lights cannot resolve a suburb. Your signal is noise."

**The objection.** VNP46A2 is roughly 500 m per pixel. Harare suburbs are a few pixels across. Cloud cover in the rainy season removes entire weeks. Moon phase changes background radiance by more than the effect you are looking for. The signal-to-noise ratio makes any per-suburb, per-night claim indefensible.

**The answer, partly a concession.** Per-suburb, per-night is the wrong unit and this project should not claim it. The defensible unit is a suburb-month reliability rate built from many nights, where the per-night noise averages out and the moon and cloud terms enter as covariates rather than confounds. Black Marble's VNP46A2 is already lunar-BRDF corrected, which removes the largest term, and the product ships a mandatory quality flag per pixel per night that marks cloud contamination for exclusion.

The honest position: **a single night's verdict is a hypothesis, a month of nights is a measurement.** The repository will report per-night observations because they are the raw data, and will only publish confidence intervals at the monthly aggregate. Anything stated more strongly than that is over-claiming.

**Pre-registered test.** Before publishing any reliability index, run the method on nights where the outcome is independently known, and report the false positive and false negative rate. If the method cannot separate a known 6-hour outage from a normal night at better than chance on the validation set, the verification claim is withdrawn and the project ships as a schedule archive only.

## 2. "You are validating a method on a country with no ground truth."

**The objection.** You have nothing to check your verification against. Zimbabwe has no reliable independent record of which outages happened. So you can never know if your method works, which makes the whole thing unfalsifiable.

**The answer.** Correct, and it is the reason the method gets validated in South Africa first, not Zimbabwe. South Africa has a well documented public archive of national load shedding stages with times, published by the utility itself. That is a large labelled dataset for exactly this problem: announced outage windows, at known times, in known places. The method is calibrated and its error rates measured there, then applied to Zimbabwe.

This inverts the usual order and it is the single most important design decision in the project. Validate where labels exist. Deploy where they do not.

**Note on sources.** The South African labels come from the utility's own published stage history. Third-party apps that resell schedule data have their own terms of use, and their archives are not used.

## 3. "This is a scraper with a satellite bolted on. The satellite part is decoration."

**The objection.** The valuable output is a structured archive of notices, which is a scraping exercise. The night-lights layer is there to make it sound like research.

**The concession, and the answer.** The archive genuinely is valuable on its own and would justify the project without any satellite work. That is why it ships first and why the repo is honest that verification is unproven at launch.

But the verification is what makes it a contribution rather than a utility. A schedule archive tells you what was promised. It has nothing to say about the gap between promise and delivery, which is the only question anyone actually has. And the method generalises: any utility anywhere that publishes a schedule can be audited the same way, which is a paper, not a scraper.

## 4. "ZETDC will just stop publishing, or block you."

**The objection.** The moment this becomes visible, the source disappears and the project dies.

**The answer, partly a concession.** Real risk, and it cannot be fully mitigated. Three things reduce it. The raw snapshots are committed permanently, so whatever has been collected survives regardless. The crowdsourced report channel does not depend on the utility at all. And the night-lights layer is entirely independent of any publication by the utility, so if notices stop, the observed-outage series continues and the project simply loses the announced side of the comparison.

The framing also matters. This is not an adversarial project. A utility that publishes accurate schedules comes out of this looking good, and the index is as capable of showing improvement as decline.

## 5. "Crowdsourced outage reports are trivially poisoned."

**The objection.** Anyone can report anything. A handful of motivated users can distort a suburb's numbers.

**The answer.** Which is precisely why crowdsourced reports are never a ground truth in this design. They are a third signal, alongside the announcement and the satellite observation, and their value is in disagreement: a suburb where reports and radiance agree but the schedule does not is the interesting case. Reports are rate-limited, aggregated, and never published as individual claims. No monthly index number depends on them.

## 6. "Nobody in Zimbabwe can use a web dashboard during load shedding."

**The objection.** The users are, by definition, the people whose power is out. A React dashboard is the wrong artefact.

**The answer, and it changes the roadmap.** This is the best objection on the list. The front end must work on a cheap Android phone over a slow mobile connection, cached offline, and the primary interface should eventually be something that reaches people without a browser session at all. That reorders the roadmap: the public API and a low-bandwidth page come before anything visually ambitious, and a lightweight push channel is a first-class deliverable rather than a nice-to-have.

## 7. "EskomSePush already exists. Build a Zimbabwe clone and skip the science."

**The objection.** The demonstrated demand is for a schedule app. The verification work is a distraction from shipping the thing people want.

**The answer.** A Zimbabwe schedule app is a good product and a weak contribution: it is replicable by anyone in a fortnight, and it produces no asset that compounds. The verification layer is the part nobody else has, it produces a dataset and a method that outlive the app, and it is the reason this can be a paper and a reference rather than a utility.

The app gets built. It is just not the moat.

## 8. "Your baseline is contaminated. Load shedding is so constant that 'normal' already includes outages."

**The objection.** You define an outage as a departure from a suburb's recent baseline. If a suburb is shed most nights, the baseline is a shed baseline and the departure disappears.

**The answer, and it needs work.** Genuine methodological hazard and it is not fully solved. The baseline cannot be a rolling mean of recent nights. It has to be built from nights the schedule says the suburb was not shed, and from the upper envelope of observed radiance rather than the average, on the reasoning that the brightest recent comparable nights approximate the un-shed state. That construction is itself an assumption, so it gets its own ablation in `EVALUATION.md` and the sensitivity of every headline number to the baseline definition is reported.

If the sensitivity turns out to be large, the finding is that the method is unreliable in high-shedding regimes, which is a real and publishable result rather than a failure.

## 9. "One person, no funding, no institutional backing. This will be abandoned in three months."

**The objection.** Solo data projects die. The pipeline breaks silently, nobody notices, and the dataset has a hole in it.

**The answer.** Which is why the refresh loop is infrastructure rather than intention. Ingestion runs on GitHub Actions, which is free and unlimited on public repositories and needs no server anyone has to remember to pay for. A heartbeat monitor fires if a scheduled run does not complete, so a silent failure becomes a loud one. The dataset is append-only in git, so a gap is visible in the history rather than hidden.

That does not guarantee it survives. It does mean that if it stops, everyone can see exactly when and how much data exists, which is more than most projects offer.


---

## 10. "There is nothing to archive. Your premise is false."

**The objection.** The project is built on ZETDC publishing schedules. It does not. The archive will be empty forever, and an empty archive is not a dataset.

**The concession.** Correct on the facts, and it was confirmed by the project's own first live run rather than by a critic. There is no machine-readable schedule on ZETDC's website. The notices file is empty and may stay empty.

**The answer.** The absence is the finding, and recording it continuously is what makes it evidence rather than an anecdote. "I looked once and did not see a schedule" is worth nothing. "Three sources, checked every six hours, no schedule published across N months, here is every timestamped observation" is a documented accountability gap that nobody else has established.

More importantly, it removes the project's dependence on the utility entirely. The satellite layer was originally a way to check announcements. It is now the only way to observe load shedding in Zimbabwe at all, which makes it necessary rather than clever. A cut that is never announced and never recorded did not happen, as far as any dataset in the world is concerned. That is the thing worth fixing.

**What would change my mind.** If schedules turn out to be published somewhere this project is not watching, for example a social account or a regional office, then the monitoring premise is not false, just badly aimed, and the fix is to widen coverage. That is why the public page asks directly for anyone who knows where schedules are actually published to open an issue.
