# Round 4: the identifiability boundary as a decision rule

Written after round 3 and an external review, before round 4 was frozen (v4/PROTOCOL_V4.md).

## Theorem 2, refined
Replacing a changed component c by its specification θ*_c (all other components at their current versions)

- may change c's own output on its current inputs: c is a *locally effective* defect;
- may change the final pipeline output on the current records: c is an *effective* defect (the ground truth).

For an unforced component (θ*_c = θ⁰_c) and deterministic components with archived inputs:

- (a) the rollback test (θ⁰_c on c's current inputs vs c's current output) returns *differ* iff c is locally
  effective;
- (b) local effectiveness is necessary for effectiveness;
- (c) c is effective iff, in addition, the propagation test (the downstream subgraph at its current versions on
  the rolled-back output, final outputs compared) returns *differ*;
- (d) with no forced change in the change set, sequential topological rollback yields the specification's output.

Rounds 1-3 used the rollback test alone. In their records, a *differ* verdict on an unforced component was
followed by an effective defect in all but one case (a timestamp-resolution defect from a library upgrade, in a
case with a second, consequential defect upstream; its difference did not reach the final output;
runs/posthoc_local_vs_e2e.json).

## Touched components and Proposition 11
A component is *touched* in a case if, by column-level lineage, it reads directly or through upstream components a
column named by a published change in the case's period range. Whether a touched component is forced is a property
of the new encoding (Theorem 3), so its rollback cannot be trusted; an untouched component is unforced as long as
the change record is complete.

**Proposition 11.** Under the conditions of Theorem 2 and an accurate change record (every forced component is
touched), the rule

1. list every touched component as *unverified*;
2. fix a changed untouched component iff its rollback and propagation tests both differ (*verified defect*);
3. clear every other component (*healthy*); components whose tests cannot run are unverified

(a) never fixes a component that is not an effective defect, (b) never leaves a consequential defect neither fixed
nor unverified, (c) is correct whenever no component is touched, and (d) cannot shorten its unverified list without
side information: for every touched component there are two configurations, indistinguishable by monitoring and
re-execution, in one of which it is a consequential defect and in the other a correct adaptation.

Proof: paper, Appendix A.

## DoD-4
`v4/code/dod/methods_v4.py`. Implements the rule; the pipeline's output step (the model's fitted encoder, versioned
with the model and changed only by retraining) is never touched. Unverified components carry DoD-3's evidence as a
label (`suspect` / `no evidence`) for ranking; `dod4_lite` omits it. Retraining follows DoD-3.

## What round 4 tests
Proposition 11 makes H15-H17 predictions; the experiment tests whether its assumptions hold on real multi-table
pipelines (accurate change records from profiles of the published files, column lineage, deterministic and
reproducible execution across library environments), and measures the price of soundness: coverage and the review
load, and how well DoD-3's evidence ranks the review list (H19).
