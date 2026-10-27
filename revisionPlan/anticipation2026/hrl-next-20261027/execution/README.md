The user authorized using more local compute on 27 October 2026. The original
scientific protocol and live primary process remain unchanged. This bounded
acceleration runs one additional independent native workflow for absolute-error
training seed 3401, using the same profile, initialization seed, environment
seed, two-million-transition budget and three-pool checkpoint selection.
Socket 48780 is separate from the primary process's 48760.

`parallel_seed.py` imports the frozen pipeline without changing its source.
Its status writer and socket override are local to its own Python process.
It stores the run under `next-parallel-reward-absolute-3401` so that an incomplete
attempt cannot block the primary pipeline. After verified completion, it may
publish `next-reward-absolute-3401` as a directory symlink to the completed run.
The existing pipeline then reuses the same selection receipt. All absolute
checkpoint/evaluation paths remain valid and the record identifies the actual
run directory. Publishing is restricted to when the primary process is still
safely earlier in the reward stage. If it has caught up, the helper leaves its
result unpublished and the primary attempt remains authoritative.

Launch requires at least 25% system-wide memory headroom reported by
`memory_pressure -Q`. A watchdog stops only the extra job's native processes
after two consecutive readings below 15%. It checks process command lines to
avoid signaling reused PIDs. Incomplete evidence remains preserved; the primary
pipeline can still train the missing seed normally. No other applications are
closed and no learning or simulation parameters change.

`parallel_plan.json`, `parallel_process.json`, `parallel_status.json` and
`resource_history.jsonl` record the execution change. `published_alias.json`
confirms successful reuse when applicable. CPU headroom suggested that a second
workflow could help; the actual wall-time benefit remains to be measured.
