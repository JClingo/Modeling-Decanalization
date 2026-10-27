# Primary traversal factor — author clarification, 26 October 2026

The author confirmed: “We want to use the factor 1 (same pre/during/post) for
analysis, then, as that was the original plan.” This supersedes the previous
recommendation to retain factor 0 as the primary HRL condition.

The primary HRL comparison is therefore **CDR factor 1 versus CCC**, with one
count per actual tile entry before, during and after decanalization. The
existing recanalization operation, `n <- floor(n / 2)`, remains in place once
at the phase transition. Equal increment rates do not imply equal count levels
or equal physical conditions: physical and predicted losses are still removed
during phase 2, and the trial's initial homeostatic state is restored at phase
boundaries. Policy weights remain fixed.

Use the already completed 250-trial factor-1 HRL batch and its existing
250-trial CCC control. Factors 0, 2, 4 and 7 are sensitivity conditions. This
choice follows the author's stated design intent; it is not an estimate of an
optimal factor. The clarification was recorded after the factor sweep results
were available. The sweep's original `plasticity/ANALYSIS_PLAN.md` and its
hashed inputs remain unchanged; this document records the subsequent decision.

The authoritative HRL tables, figures and statistical report are in
`primary-factor1/`. They cover all nine recorded outcomes, using Welch
comparisons and Holm adjustment across the nine HRL outcomes separately in
each phase. Paired and baseline-change analyses remain sensitivity checks.
This is an HRL-only family; it does not silently reuse the former 18-test
family as if matching factor-1 NF data existed.

**NF status:** the available corrected NF CDR batch used factor 0. It remains
separate reference evidence. It must not be described as a factor-1 result or
used as a matching second objective in the factor-1 primary experiment. A
matching NF factor-1 evaluation and a joint multiplicity plan are needed before
making joint primary claims under the same counting protocol. No new policy
training is needed merely to change the evaluation factor.

The earlier root-level factor-0 tables and reports, the frozen sweep plan and
the previously generated ZIP archives are retained as historical records.
