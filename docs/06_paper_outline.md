# 06 — Paper outline (draft)

Working title: **Is It Model Drift or a Broken Pipeline? Intervention-Based Diagnosis of Production ML Degradation**

1. **Introduction.** Retrain-on-alarm is the default response to a degraded model; many degradations are pipeline
   defects. Monitoring sees only pipeline outputs. Contributions: (i) identifiability results — silent defects are
   observationally equivalent to drift; re-execution resolves internal defects exactly; source-coupled changes
   are the stated limit; (ii) DoD, a cost-aware interventional diagnoser that outputs an action; (iii) a benchmark
   of three executable pipelines with real temporal drift and real, dated source changes, real library-upgrade
   behaviours and documented incident classes; (iv) an evaluation against practitioner monitoring, data
   validation, observational attribution, pipeline-instance debugging, bisection and LLM agents.
2. **Background and related work.** Data validation (TFDV, Deequ, AVH, PrismaDV); monitoring tools; shift
   attribution (Zhang et al., DISDE, WhyShift, hierarchical decompositions); pipeline debugging (BugDoc, AID,
   DataPrism, mlinspect/mlwhatif, SAVAGE); causal RCA and system maps (Paleyes & Lawrence; Leest et al.);
   incident studies.
3. **Problem formulation.** World / source encoding / pipeline versions / spec; actions; consequential defects.
4. **Identifiability.** Theorem 1 + Corollary (image characterisation), Theorem 2 (rollback), Theorem 3 (source
   coupling) + smoothness assumption, Proposition 4 (ordering).
5. **Method.** Candidates, tests (rollback, effect, boundary), ordering, stopping, residual and retrain decision.
6. **Benchmark.** Domains, pipelines (DAG figure), source changes table with dates and evidence, T2 probe table,
   defect catalog, case generation, splits (ACS = development domain; disclosure), ground truth via execution.
7. **Experimental setup.** Baselines and their configuration, matched budgets, metrics, statistics.
8. **Results.** RQ1 silent vs loud for monitoring-only methods (H1). RQ2 action accuracy and outcomes (H2, H4).
   RQ3 cost (H3). RQ4 source-coupled limit (H5). RQ5 LLM agents. Ablations. Negative results as found.
9. **Discussion.** When retraining "works" on corrupted data (fragility); requirements for adoption (archived
   intermediates, reproducible versions, column-level lineage); threats to validity.
10. **Conclusion.**
Appendix: proofs; full defect catalog with sources; per-domain tables; prompts; reproducibility (code hashes,
protocol freeze, replay without keys).
