# 07 — Formal core, version 2 (source-coupled changes)

Written after the v1 test results (docs/04_dev_log.md, runs/final). Everything here was developed on data already
seen in v1 (ACS, TLC, news); the claims are tested on the v2 held-out domains (Divvy, HMDA, BTS) under protocol v2.

Notation as in docs/05_theory.md. A raw-reading component (an *adapter*) maps published records `R = σ_t(W)` to
semantic records `S = A(R)`. The correct adapter `A*_t` for period `t` satisfies `A*_t ∘ σ_t = s`, where
`s : 𝒲 → 𝒮` is the semantic content the provider publishes. A forced change at an event `e` is one where
`A*_e ≠ A*_{e-1}`.

## Why v1 failed where it failed

Theorem 3 says no re-execution test can certify a forced change without side information. v1 used one piece of side
information, world smoothness at schema boundaries, judged against a *single* ordinary transition. Two problems:

1. A single transition is a poor null. Under exchangeability (below), the probability that the event transition
   is the largest of `m+1` transitions is `1/(m+1)`; with `m = 1` this bound is 1/2 per column.
2. Smoothness is false exactly when the provider's change coincides with a real-world change, because providers
   change schemas *when the world changes* (a new fee needs a new column). In v1, 90 of 93 false blames on the taxi
   test cases came from one such event: the airport fee rose from $1.25 to $1.75 in the quarter the column was
   renamed.

## Assumptions

**(E) Exchangeable ordinary change.** For a column `k` and a correct pipeline, the world-induced change statistics
`J_1, …, J_m` of the `m` transitions preceding an event and `J_e` of the event transition are exchangeable.

**(I) Invariant stability.** An *invariant* of a semantic schema is a measurable `g : 𝒮 → {0, 1}` (1 = violated)
whose violation rate under the correct adapter, `v_t = P_{D_t}[g(s(W)) = 1]`, is small and does not increase at the
event by more than its largest increase over the `m` preceding transitions.

(I) is a statement about the provider's *process* (accounting identities, business rules, timestamp order), not
about the distribution of the world. It is implied, in particular, by:

**Lemma 1 (region invariance).** Let `g = 1[s ∉ A]` for a region `A ⊂ 𝒮` that contains the support of `s(W)`
under every world distribution the provider can produce in both periods (`v_t = 0`). Then (I) holds for every world
shift `D_{e-1} → D_e`, however large, that keeps `s(W)` inside `A`.

*Proof.* `v_e = P_{D_e}[s(W) ∉ A] = 0 = v_{e-1}`. ∎

Example: "the airport fee is non-zero exactly for trips from the airport zones" defines `A`; a fee rise from $1.25
to $1.75 is a large distribution shift of the fee column that stays inside `A`.

## Theorem 5 (invariant evidence for forced changes)

Let `A_e` be the deployed adapter at the event, `Δ = {w : A_e(σ_e(w)) ≠ A*_e(σ_e(w))}` the records it gets wrong,
and `V = {w ∈ Δ : g(A_e(σ_e(w))) = 1, g(s(w)) = 0}` the wrong records it moves out of the invariant region.

(a) *(detection)* The violation rate of the deployed output is `v̂_e ≥ v_e − P(Δ \ V) + P(V)`. If `P(V) > η`,
where `η` bounds the provider-side violation rate change allowed by (I), the deployed adapter is distinguishable
from the correct one by the violation rate alone, for every world distribution satisfying (I). In particular,
when the provider's violation rate is zero (Lemma 1), the adapter is refuted as soon as one record lands in `V`.

(b) *(world-robustness)* Under (I) and a correct adapter, the rule "flag if the violation rate increase at the
event exceeds the largest increase over the `m` preceding transitions" errs only if the event's increase is the
largest of `m+1`; if the increases are exchangeable the false-flag probability is at most `1/(m+1)`; under
Lemma 1 it is zero. Neither bound depends on how much the world's distribution moves.

(c) *(blind defects)* If `P(V) = 0` — the defect maps every record it corrupts into the invariant region (e.g.
scaling all money columns and their total by the same factor, or swapping two summands) — the invariant carries no
evidence, and the configuration is again subject to Theorem 3.

*Proof.* (a) On `w ∉ Δ` the deployed and correct outputs agree; on `V` the deployed output violates while the
correct one does not; on `Δ \ V` the deployed output may or may not violate. Taking expectations gives the bound.
(b) is the rank argument of Proposition 7 applied to the violation-rate increases. (c) On `Δ \ V`, the violation
indicators of the deployed and the correct adapter coincide in law whenever the corrupted records are attainable by
some world distribution (Corollary 1), so no function of the indicators separates them. ∎

**Corollary 2 (excusing a jump).** Let column `k` jump at the event. If an invariant `g` determines `k` given other
columns `z` (its zero pattern or its value: support, sum and difference identities), `g` is intact at the event,
and the `z` columns do not jump themselves, then the jump in `k` is consistent with a correct adapter, whatever the
size of the jump. (Order constraints `a ≤ b` do not determine `k` and cannot excuse a jump.)

## Proposition 7 (history rule for the smoothness test)

Under (E), the rule "flag column `k` if `J_e > max(J_1, …, J_m)`" has false-flag probability at most `1/(m+1)`
for that column; with `L` columns tested at an event, at most `L/(m+1)` by the union bound. Requiring in addition
`J_e > K · median(J_i)` or an absolute floor only lowers the rate. v1's rule compared `J_e` with `K · J_{m}`
(one transition), for which no such bound below 1/2 holds.

## Mining invariants without domain knowledge

The method does not use hand-written invariants. It mines four templates from the archived outputs of the
reference pipeline in the `m+1` periods before the event:

| template | form | example (development data) |
|---|---|---|
| support | `k ≠ 0  ⇔  z ∈ Z` | airport fee non-zero exactly for pickups at JFK/LGA |
| order | `a ≤ b` | start time ≤ end time |
| sum | `t = a + b (+ c)` | elapsed time = taxi-out + air time + taxi-in |
| difference | `d = (b − a)/u` | trip duration = end − start (seconds) |

An invariant is kept if it holds on at least 98% of records in every history period *and* is informative: after
a random permutation of its first column, it is violated at least five times as often (and by at least five points
more). The permutation test removes trivial identities (e.g. "a zero fee is within one unit of the duration in
hours"). Identifiers and the label are excluded.

Lemma 1 says why these templates are the right ones: they define regions of the semantic space that ordinary
world shifts (price levels, demand, mix) do not leave, while adapter defects (missed renames, unit errors,
default-filling, swapped fields, misaligned columns) do.

## What this predicts for v2 (pre-registered in v2/PROTOCOL_V2.md)

- On held-out domains with dated source changes, DoD-2 reduces false blame of correct adapters relative to DoD
  without losing source-coupled defects that move records out of an invariant region.
- Defects that are blind to every mined invariant (Theorem 5c) remain hard; the per-defect results report which
  defects had invariant evidence.

## References to verify

- Exchangeability / rank argument: standard (conformal prediction, e.g. Vovk, Gammerman, Shafer 2005).
