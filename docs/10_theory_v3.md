# 10 — Formal core, round 3 (what round 2 taught)

Round 2 (docs/07_theory_v2.md, v2/PROTOCOL_V2.md) failed on the two held-out domains with dated published
changes (bike share: DoD 0.07 primary endpoint; mortgages: 0.34), while it was perfect on the domain without
them (airlines: 1.00). The failure analysis (on round-2 data, now development data) found three violations of
the assumptions behind Theorem 2 and Proposition 7, not tuning problems. Each is fixed by a statement below.

## Proposition 8 (superseded layouts carry no evidence)

Let the source publish layouts σ_1, …, σ_k at events e_1 < … < e_k ≤ p (the current period). The correct
adapter for p is A*_p, which need only satisfy A*_p ∘ σ_k = s. Whether A_p can read σ_j for j < k is
irrelevant to its correctness at p: for any adapter A that is correct on σ_k there is an adapter A′, equal to A on
the support of σ_k and failing on σ_j, that is also correct. Hence a test whose outcome depends on A's behaviour
on σ_j (j < k) cannot be a consistent test of correctness at p.

*Consequence for the method.* A forced component is judged only at the latest published change touching its
columns (per column, through column-level lineage); its failure to read earlier layouts is not evidence.
In round 2, discarding only these flags from the saved decisions lowers DoD's false-blame rate on the mortgage
domain from 0.65 to 0.42 and on the bike-share domain from 0.91 to 0.65 (post hoc, from saved records; v3/analysis/posthoc_r2.py).

## Proposition 9 (validity of a rollback counterfactual)

Theorem 2 requires the reference version θ⁰_c to be valid on the current inputs. If θ⁰_c maps a semantic value
that the current version produces to *missing* (it cannot parse the new layout), its output is not a draw from
the correct pipeline's law, and the effect test (deployed-model accuracy with c rolled back) compares the current
version with a broken counterfactual. A reference version is therefore treated as invalid — like a rollback that
raises — when, on the columns where the two versions differ, it produces more missing values than the current
version.

## Proposition 10 (introduced missingness is world-robust evidence)

Let k be a semantic field the provider always defines (P_D[s(W)_k defined] = 1 for every world distribution D
the provider can produce: e.g. a trip has a start time). This is a support invariant in the sense of Lemma 1 with
region A = {k defined}. If a component's output has k missing on a fraction ρ of records while the inputs it
reads k from are defined there, the component maps those records out of A; under (I) this happens with
probability 0 for a correct component, whatever the world does. A missing-rate increase of the output relative to
the reference period that is not present in the component's inputs is therefore evidence of a defect that needs
no history and no smoothness assumption.

The rule is applied where no change could be judged otherwise (no readable history before the latest change).
It does not apply to fields the provider stops publishing (their sources become missing too, so the increase is
inherited) or to categories never seen before (the encoding step is not a source-coupled candidate unless it
changed).

## History that cannot be read

When the deployed versions cannot read the periods before a change (a layout used only between two changes),
Proposition 7 has no sample to work with. The method then abstains from the smoothness test for that change
instead of reporting an error (round 2 treated it as an error, i.e. as evidence of a defect). Abstention moves
the decision to Propositions 9 and 10 and to the rollback and effect tests. History the archive simply does not
have (a source that starts shortly before the change) is a different matter: the test then uses the transitions
that exist, down to one, as DoD did, and its false-flag bound is correspondingly weaker (Proposition 7). (This
distinction was added before the round-3 freeze, after DoD-3 lost the stale section tables on the news development
domain, whose archive starts in 2012.)

## What this predicts for round 3 (pre-registered in v3/PROTOCOL_V3.md)

On fresh held-out domains with successive published changes, DoD-3 has far lower false blame than DoD and
DoD-2 at no loss on internal defects (identical behaviour when there is no published change).
