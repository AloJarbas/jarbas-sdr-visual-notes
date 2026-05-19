# Status — large-CFO front-end boundary after the symbol-rate packet

Updated on 2026-05-19.

Delivered:

1. `notes/when-symbol-rate-carrier-recovery-stops-being-enough.md`
2. `assets/2026-05-19-large-cfo-front-end-boundary.png`
3. `assets/2026-05-19-large-cfo-front-end-boundary.csv`
4. `notebooks/large_cfo_front_end_boundary.ipynb`
5. `scripts/generate_large_cfo_front_end_figure.py`
6. `notes/2026-05-19-waveform-domain-coarse-carrier-front-ends-research.md`
7. `notes/oversampled-fourth-power-vs-band-edge-fll.md`
8. `assets/2026-05-19-oversampled-fourth-power-vs-band-edge-fll.png`
9. `assets/2026-05-19-oversampled-fourth-power-vs-band-edge-fll.csv`
10. `notebooks/waveform_carrier_front_ends.ipynb`
11. `scripts/generate_waveform_carrier_front_end_figure.py`
12. `scripts/waveform_carrier_front_ends.py`
13. `tests/test_waveform_carrier_front_ends.py`
14. `public-knowledge-repo/notes/coarse-carrier-front-end-choice-card.md`

## What this pass established

- the earlier `\pi/4` alias note is now pinned down as a **1-sample/symbol QPSK symbol-rate** statement, not a generic carrier-recovery law
- the honest 4th-power coarse-frequency window scales with the observation rate: `|\Delta f| < F_s/8 = L R_s / 8`
- a simple local oversampled toy check is enough to make the rate-scaling point visible without bloating the repo into a full modem lab
- the same physical CFO can alias at `1 sps` while staying honest at `4 sps`, so the next receiver move is often an earlier front end rather than a stronger claim about the late-stage estimator
- the two follow-on branches worth naming are:
  - oversampled waveform-domain coarse recovery, including band-edge FLL style logic
  - pilot or correlation-based coarse estimation for receivers that can spend known structure

## What the continuation pass added

- the next honest comparison is no longer "symbol-rate versus large CFO"; it is **oversampled symmetry-based recovery versus waveform-domain band-edge recovery**
- the strongest distinction between those branches is the information source:
  - oversampled 4th-power uses **PSK rotational symmetry**
  - band-edge FLL uses **pulse-shape roll-off asymmetry**
  - preamble/correlation-based recovery uses **known transmitted structure**
- the pilot/correlation branch is real but should stay a decision box, not a full third simulation lane, unless packetized receiver work becomes active again

## What the waveform-domain sidecar established

- the oversampled 4th-power branch really is the same symmetry-based object as before, just moved earlier in the chain
- the band-edge branch is not a prettier version of the same estimator; it depends on excess-bandwidth structure and gets materially stronger as roll-off grows
- the clean comparison sentence is now explicit in the public note: one branch exploits **PSK rotational symmetry**, the other exploits **pulse-shape edge asymmetry**
- the pilot/correlation branch still belongs as a named third box, not as a full third simulation lane unless packetized receiver work becomes active again

## Best next move

If this lane gets one more pass, keep it narrow again.
The strongest follow-up is probably one of these two:

- regenerate one older static receive-side visual with the same rebuildable figure tooling and PNG export path so the older packet stops depending on one-off artwork
- add one small pilot/correlation decision card only if it says something sharper than "known structure helps" and stays clearly separate from the blind-estimator packet

## Avoid next time

- do not reopen the symbol-rate alias note as if it were still unfinished
- do not let this branch sprawl into AGC, equalization, or packet framing
- do not pretend the hold-model sweep is a full waveform receiver study; its job is only to make the sample-rate boundary obvious
