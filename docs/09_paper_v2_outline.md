# 09 — Paper v2 outline (benchmark + method)

Working title: **Drift or Defect? A Benchmark and an Interventional Method for Diagnosing Production ML
Degradation**

Pitch: when a deployed model degrades, retraining treats the symptom. We (1) prove which degradations
monitoring can and cannot tell apart, (2) release a benchmark of real public pipelines with dated published
changes, real library upgrades and replays of documented incidents, with ground truth by execution, and (3) give
an interventional method whose one hard case (changes forced by the source) we characterise and partly solve with
source-internal invariants. Results come from two pre-registered rounds; the second round tests the improved method
on six-domain... (three new domains held out).

1. Introduction — the retrain reflex; silent defects; contributions; two pre-registered rounds.
2. Problem and theory — setting; Thm 1 (observational equivalence; validation sees only loud defects); Thm 2
   (rollback identifies unforced defects); Thm 3 (forced changes are not identifiable by re-execution);
   Lemma 1 / Thm 5 (invariant evidence; world-robust; blind defects); Prop 7 (history rule); Prop 4 (ordering).
3. Benchmark — six domains (census, taxi, news; bike share, mortgages, airline), 1,700 cases; defect tiers incl.
   replays of real incidents; ground truth by execution; outcomes of every action; release and replay.
4. Methods — DoD (v1) and DoD-2; baselines incl. LLM agents with the same tools.
5. Protocol — round 1 (v1, frozen 8eab1e0e), round 2 (v2, frozen <digest>); what was seen when.
6. Results — round 1 as pre-registered (H1–H5, incl. the narrowly missed H2 and the taxi failure); round 2
   (H6–H10) on held-out domains; per-domain, per-tier; invariant-blind defects; cost; LLM agents.
7. Related work — data validation, drift detection, root cause analysis, pipeline debugging, invariant mining
   (Daikon, data constraints), causal identifiability.
8. Limitations — sample of pipelines, synthetic-but-realistic defect injection, accuracy as primary metric with
   weak models in some domains, invariants mined only from four templates.
Appendix — proofs; domain details; defect catalogs with incident sources; full tables; evidence index.
