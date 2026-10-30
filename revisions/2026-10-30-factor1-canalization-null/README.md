# Revision variant: factor-1 result + canalization null (30 October 2026)

These are copies of `modelingDecanalization.tex` and `appendix.tex` with the
revisions applied. The documents at the repository root are unchanged, and
match `HEAD`.

## What this variant does

- **Primary HRL result:** reports the corrected factor-1 package from
  `revisionPlan/anticipation2026/primary-factor1/`: −3.69 [−9.72, 2.35],
  250 trials per arm.
- **NF result:** reported as the separate factor-0 reference.
- **New Results subsection, "Route persistence":** the agent does not
  canalize.
  - The paper's factor-1 policy enters 558 distinct tiles in phase 1, and
    its P1–P2 route overlap is 1.07× chance.
  - It summarizes the redesign and the reduced-design pilot.
- **Methods:**
  - the boundary is described as an antipodal wrap, not toroidal;
  - the description of anticipation is corrected;
  - checkpoint selection is described as it was run;
  - counting is one per entry in every phase;
  - the "two loci" claims are softened.
- **Discussion, Limitations and Conclusions** are rewritten accordingly,
  including the arena-escape fault: 9 of 250 factor-1 trials; excluding them
  gives −4.46 [−10.12, 1.19].
- **Appendix:**
  - HRL checkpoint gather 75 (750k transitions);
  - counted visits per entry 1 / 1, with the NF reference at 1 / 0;
  - selection seeds.

Evidence: `revisionPlan/decanalizationRedesign/` (`NULL_RESULT.md`,
`RECONCILIATION.md`, `MANUSCRIPT_EDITS.md`) and
`revisionPlan/anticipation2026/MANUSCRIPT_EDITS.md`.

## Building

Compile from this folder:

```bash
pdflatex modelingDecanalization.tex
```

The copy adds `\graphicspath{{./}{../../}}`. The new figure
(`figures/factor1-phase-outcomes.png`) is found here, and all other figures
come from the repository's `figures/`. The bibliography is inline, and
`\input{appendix}` picks up this folder's appendix.

The repository's `.gitignore` is an allow-list, so `revisions/` is not
tracked by git.
