# Prototype vs Dev — score comparison (raw scores)

| Q ref | Sample | Sample text (excerpt) | Prototype TA | Prototype CQ | Dev TA | Dev CQ |
|---|---|---|---|---|---|---|
| W-B1-20260401093929 (music) | 1 — Jehovah / baptism | "music is something most people enjoy in their daily lives I personly enjoy listening to music in my leisure time .it really good because it helps me relax. It helps in come back in good moods from a stressful day. At times when i listen to spiritual songs they make me to think about my God and close to him … Like on time whrn iwas going to be baptised anf there ws a song i that i kept memorising on i broke into tears of joy …" | **73** | **58** | 50 | 67 |
| W-B1-20260401093929 (music) | 2 — Listicle | "Listening to music is considered a hobby which relieves stress among people. Music helps process feelings that cannot be expressed. While doing exercise in gym or out door activities, music blocks distractions and makes these activities faster. … Music helps in cultural identity, basing on the type of music played. It reveals where one comes from for example amapiano and kadongo kamu. … Music is also used as a political tool for searching votes." | **70** | **42** | 78 | 56 |
| W-B1-20260401081828 (work) | 1 — Bernard at BIP | "How Work and Jobs have changed. The way people work today has greatly changed from the past as a result of technological inventions. Long time ago, most job plannings were focussed on fixed working hours and communication passed through memos and physical meetigs … Today, technology has done key tranformationns at the work place, with communications passed via emails, workers performing tasks virtually andmeetigs extensivelly organised through zoom … This has been witnessed by Benard at BIP who is able to study and workk at the same time …" | TBD | TBD | 90 / 100 ⚠ | 58 / 100 ⚠ |
| W-B1-20260401081828 (work) | 2 — Agriculture (fragment) | "these changes have been caused by imorovement in technology, change in edication and the growth of globalizatioo. as a result, the way people work, the kind of kobs available and the skills needed have all changed significantely … in the past most people worked in agriculture farming ann manual labor Today technology has transformed the workplace. machnes and computers now do many tasks that people used to do by hand …" (79 words, fragment ending) | TBD | TBD | 39 / 44 / 39 | 17 / 14 / 25 ⚠ |

⚠ = two Dev runs of the same essay returned different scores (variance issue — 42-point CQ swing on Bernard).

## Notes

- All scores are **raw**, before the calibration table.
- Prototype scores for the work/jobs question (Sample 1 Bernard, Sample 2 agriculture) are TBD — pending run from your local prototype.
- Music samples used the original prototype runs from this session.
- Where two Dev numbers appear separated by `/`, those are two different runs of the same essay showing the variance.

## Patterns so far

| Observation | Evidence |
|---|---|
| Dev TA is stable on weak/fragment essays; CQ less so | Agriculture across 3 runs: TA 39/44/39 (5-pt swing), CQ 17/14/25 (11-pt swing) |
| Dev is **unstable** on strong essays | Bernard: TA 90→100, **CQ 58→100** across runs |
| Dev under-scores TA on personal essays with grammar errors | Music Sample 1 (Jehovah): Dev TA=50 vs prototype 73 |
| Dev over-scores CQ on listicle essays | Music Sample 2: Dev CQ=56 vs prototype 42 |

## What's missing

- Prototype run on work/jobs samples
- Multi-run variance test on Dev (re-run same sample 5× to measure within-essay variance)
- Confirmation Dev API call uses `temperature: 0`
