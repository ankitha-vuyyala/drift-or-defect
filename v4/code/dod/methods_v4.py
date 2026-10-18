"""Round-4 diagnosis method (DoD-4): the identifiability boundary as a decision rule.

DoD-4 returns three verdicts instead of two. It decides only where re-execution is exact and marks everything else
for review:
  * a changed component that no published source change touches (unforced) is tested by rollback (Theorem 2a); if
    the rolled-back output differs, the pipeline is re-executed with that component rolled back and the final
    outputs compared (propagation test, Theorem 2c). The component is a *verified defect* iff both differ, and
    *healthy* otherwise;
  * every component touched by a published source change in the case's period range (it reads, directly or through
    upstream components, a column the change log names; changed or not; the output step that applies the model's
    fitted encoder is never touched, as that encoder changes only with the model) is *unverified*: no re-execution can
    certify it (Theorem 3). It is listed for review with the evidence DoD-3 collects for it ('suspect' if DoD-3
    would fix it, else 'no evidence'), but never fixed automatically;
  * a changed component whose reference version cannot run on the current inputs, or whose propagation test fails,
    is unverified as well.
Only verified defects are fixed. The retrain decision is DoD-3's.

`dod4_lite` skips DoD-3's evidence (unverified components are labelled 'not assessed'; retrain if the monitored
drop reaches the retrain threshold); its fix set and unverified set are identical to dod4's.
Designed on the round 1-3 domains only (all of them development data from round 4 on); evaluated on the round-4
domains.
"""
from __future__ import annotations

import time

from dod import methods_v3
from dod.core import ExecError, frames_equal
from dod.methods import DELTA_RETRAIN, Decision, _changed, _drop


def _coupled(obs, dom) -> set:
    """Components touched by a published change in the case's period range: a raw table they read, directly or
    upstream, has a change on columns they read (column-level lineage, RAW_COLUMNS). The pipeline's output step is
    excluded: it applies the model's fitted encoder, which is versioned with the model and changed only by
    retraining, so no published change can force a new version of it."""
    pipe = dom.PIPELINE
    order_all = [c["name"] for c in obs.components]
    raw_cols = getattr(dom, "RAW_COLUMNS", {})

    def raw_tables_upstream(c):
        return {i[4:] for u in pipe.upstream(c) for i in pipe.components[u].inputs if i.startswith("raw:")}

    def relevant(c, e):
        if e["table"] not in raw_tables_upstream(c):
            return False
        if c not in raw_cols:
            return True
        return bool(set(raw_cols[c].get(e["table"], [])) & set(e.get("columns", [])))
    return {c for c in order_all if c != pipe.output and any(relevant(c, e) for e in obs.source_events)}


def propagate(tb, c: str) -> dict:
    """Re-execute the pipeline with c rolled back (all other components at their current versions) and compare the
    final output with the current final output. Charged like every re-execution (cached nodes are free)."""
    t0, c0 = time.perf_counter(), tb.ex.charged_s
    try:
        cur = tb.ex.run(tb.case.p1, tb.case.state)
        alt = tb.ex.run(tb.case.p1, tb._rolled([c]))
        res = {"result": "equal" if frames_equal(cur, alt) else "differ"}
    except ExecError as e:
        res = {"result": "error", "error": str(e)[:200]}
    tb._log("propagate", c, res, t0, c0)
    return res


def dod4(obs, tb, dom, use_evidence: bool = True, name: str = "dod4") -> Decision:
    changed = _changed(obs)
    coupled = _coupled(obs, dom)
    base = methods_v3.dod3(obs, tb, dom) if use_evidence else None
    suspects = set(base.fix) if base else set()
    label = (lambda c: "suspect" if c in suspects else "no evidence") if base else (lambda c: "not assessed")
    verified, healthy, local_only, unverified = [], [], [], {}
    for c in [x["name"] for x in obs.components]:          # topological order
        if c in coupled:
            unverified[c] = label(c)
            continue
        if c not in changed:
            continue
        r = tb.rollback(c)
        if r["result"] == "equal":
            healthy.append(c)
        elif r["result"] == "differ":
            p = propagate(tb, c)
            if p["result"] == "differ":
                verified.append(c)
            elif p["result"] == "equal":
                healthy.append(c)
                local_only.append(c)
            else:
                unverified[c] = "propagation failed"
        else:
            unverified[c] = "reference version cannot run"
    retrain = base.retrain if base else _drop(obs) >= DELTA_RETRAIN
    notes = {"verified": verified, "healthy": healthy, "local_only": local_only, "unverified": unverified,
             "coupled": sorted(coupled), "changed": sorted(changed)}
    return Decision(name, sorted(verified), retrain, tb.cost_s, list(tb.calls), notes)


def dod4_lite(obs, tb, dom) -> Decision:
    return dod4(obs, tb, dom, use_evidence=False, name="dod4_lite")


METHODS_V4 = {"dod4": dod4, "dod4_lite": dod4_lite}
