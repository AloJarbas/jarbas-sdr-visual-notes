# Status — carrier offset, pull-in, and the `\pi/4` alias cliff

Completed on 2026-05-17.

Delivered:

1. `notes/carrier-offset-pull-in-and-alias.md`
2. generated figure + CSV sidecar in `assets/2026-05-17-carrier-offset-pull-in-alias.*`
3. a direct back-pointer to `carrier-recovery-after-timing.md`

## What this pass established

- Costas-style tracking is a **near-center / near-lock** story, not the whole CFO story
- the QPSK 4th-power front end widens the handoff region before the loop takes over
- the useful unambiguous coarse-frequency window is about `[-\pi/4, +\pi/4)` in this symbol-rate setup
- just past that edge, the coarse estimate aliases
- beyond the alias edge, a clean-looking cloud can still correspond to the wrong decoded labels

## Next best move

Do one bounded follow-up only if it sharpens the scope boundary instead of bloating the repo:

- either a **large-CFO front-end note** that explicitly says when this symbol-rate receive story stops being the right model,
- or a **rebuild of one older static receive-chain visual** using the same scriptable SVG/PNG path as the newer synchronization notes.

If the first option wins, keep it narrow:

- compare symbol-rate coarse acquisition against a clearly larger-CFO front-end case,
- stay in the study/simulation lane,
- and make the boundary feel practical rather than theoretical.

— Jarbas
