#!/usr/bin/env python3
from __future__ import annotations

import csv
from dataclasses import dataclass
import math
import random
from pathlib import Path

from svg_layout import add_wrapped_text, export_png_from_svg, svg_root, text, text_block, wrap_text

REPO = Path(__file__).resolve().parents[1]
SVG_OUT = REPO / 'assets/2026-05-16-carrier-lock-detection-and-handoff.svg'
PNG_OUT = REPO / 'assets/2026-05-16-carrier-lock-detection-and-handoff.png'
CSV_OUT = REPO / 'assets/2026-05-16-carrier-lock-detection-metrics.csv'

WIDTH = 1660
HEIGHT = 860
PANEL_TOP = 170.0
PANEL_H = 610.0
PANEL_W = 500.0
PANEL_LEFTS = [40.0, 580.0, 1120.0]
QPSK_ANGLES = [math.pi / 4.0 + k * math.pi / 2.0 for k in range(4)]
WINDOW_COLORS = ['#60a5fa', '#22c55e', '#f59e0b', '#f97316']


@dataclass(frozen=True)
class StateSpec:
    key: str
    label: str
    phase_offset_deg: float
    phase_ramp_rad: float
    noise_std: float
    seed: int
    read: str


@dataclass(frozen=True)
class StateMetrics:
    spec: StateSpec
    iq_balance: float
    rho4: float
    delta4_deg: float
    costas_residual: float


STATES = [
    StateSpec('acquire', 'spinning unlock', 0.0, 0.08, 0.03, 11, 'still rotating; acquisition not done'),
    StateSpec('candidate', 'stable but 35° off', 35.0, 0.0, 0.03, 13, 'stable modulo 90°, but still too far for clean DD tracking'),
    StateSpec('track', 'near lock', 6.0, 0.0, 0.03, 17, 'stable and close enough for fine tracking'),
    StateSpec('ambiguity', 'quadrant-stable +90°', 90.0, 0.0, 0.03, 19, 'carrier-locked modulo 90°, labeling still ambiguous'),
]


def line(x1: float, y1: float, x2: float, y2: float, stroke: str, width: float = 2.0, opacity: float = 1.0, dash: str | None = None) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}" stroke-linecap="round"{dash_attr}/>'


def circle(x: float, y: float, r: float, fill: str, opacity: float = 1.0, stroke: str | None = None, stroke_width: float = 0.0) -> str:
    stroke_attr = '' if stroke is None else f' stroke="{stroke}" stroke-width="{stroke_width:.1f}"'
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" opacity="{opacity}"{stroke_attr}/>'


def rect(x: float, y: float, w: float, h: float, fill: str, stroke: str | None = None, stroke_width: float = 0.0, opacity: float = 1.0, rx: float = 14.0) -> str:
    stroke_attr = '' if stroke is None else f' stroke="{stroke}" stroke-width="{stroke_width:.1f}"'
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}" fill="{fill}" opacity="{opacity}"{stroke_attr}/>'


def polyline(points: list[tuple[float, float]], stroke: str, width: float = 2.5, opacity: float = 0.8, dash: str | None = None) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ''
    coords = ' '.join(f'{x:.1f},{y:.1f}' for x, y in points)
    return f'<polyline points="{coords}" fill="none" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}" stroke-linecap="round" stroke-linejoin="round"{dash_attr}/>'


def panel(svg: list[str], left: float, title: str, subtitle: str) -> None:
    svg.append(rect(left, PANEL_TOP, PANEL_W, PANEL_H, '#122131', '#5e7fa3', 2.0, 1.0, 18.0))
    title_lines = wrap_text(title, max_width=PANEL_W - 44.0, font_size=18)
    svg.append(text_block(left + 22.0, PANEL_TOP + 34.0, title_lines, 'label', 22.0))
    subtitle_y = PANEL_TOP + 34.0 + 22.0 * max(len(title_lines), 1) + 8.0
    add_wrapped_text(svg, left + 22.0, subtitle_y, subtitle, 'small', max_width=PANEL_W - 44.0, font_size=15, line_height=20)


def qpsk_symbols(count: int, *, seed: int = 7) -> list[complex]:
    rng = random.Random(seed)
    return [complex(math.cos(angle), math.sin(angle)) for angle in (rng.choice(QPSK_ANGLES) for _ in range(count))]


def impaired_samples(symbols: list[complex], spec: StateSpec) -> list[complex]:
    rng = random.Random(spec.seed)
    phase_offset = math.radians(spec.phase_offset_deg)
    samples: list[complex] = []
    for index, symbol in enumerate(symbols):
        theta = phase_offset + spec.phase_ramp_rad * index
        rotated = symbol * complex(math.cos(theta), math.sin(theta))
        noise = complex(rng.gauss(0.0, spec.noise_std), rng.gauss(0.0, spec.noise_std))
        samples.append(rotated + noise)
    return samples


def normalized_phase(z: complex) -> complex:
    magnitude = abs(z)
    if magnitude <= 1e-12:
        return 1.0 + 0.0j
    return z / magnitude


def rho4_metric(samples: list[complex]) -> float:
    phasor = sum(normalized_phase(sample) ** 4 for sample in samples) / len(samples)
    return abs(phasor)


def delta4_deg(samples: list[complex]) -> float:
    midpoint = len(samples) // 2
    first = sum(normalized_phase(sample) ** 4 for sample in samples[:midpoint]) / midpoint
    second = sum(normalized_phase(sample) ** 4 for sample in samples[midpoint:]) / (len(samples) - midpoint)
    delta = math.atan2((second / first).imag, (second / first).real)
    return abs(math.degrees(delta))


def iq_balance_metric(samples: list[complex]) -> float:
    denom = sum(abs(sample) for sample in samples) / len(samples)
    if denom <= 1e-12:
        return 0.0
    return abs(sum(abs(sample.real) - abs(sample.imag) for sample in samples) / len(samples)) / denom


def costas_residual_metric(samples: list[complex]) -> float:
    residuals: list[float] = []
    for sample in samples:
        magnitude = abs(sample)
        if magnitude <= 1e-12:
            continue
        i = sample.real
        q = sample.imag
        sign_i = 1.0 if i >= 0.0 else -1.0
        sign_q = 1.0 if q >= 0.0 else -1.0
        residuals.append(abs(sign_q * i - sign_i * q) / magnitude)
    return sum(residuals) / len(residuals)


def build_metrics(symbols: list[complex]) -> dict[str, StateMetrics]:
    states: dict[str, StateMetrics] = {}
    for spec in STATES:
        samples = impaired_samples(symbols, spec)
        states[spec.key] = StateMetrics(
            spec=spec,
            iq_balance=iq_balance_metric(samples),
            rho4=rho4_metric(samples),
            delta4_deg=delta4_deg(samples),
            costas_residual=costas_residual_metric(samples),
        )
    return states


def iq_to_xy(cx: float, cy: float, scale: float, z: complex) -> tuple[float, float]:
    return cx + z.real * scale, cy - z.imag * scale


def draw_constellation_axes(svg: list[str], cx: float, cy: float, radius: float) -> None:
    svg.append(line(cx - radius - 24.0, cy, cx + radius + 24.0, cy, '#35506a', 2.0))
    svg.append(line(cx, cy - radius - 24.0, cx, cy + radius + 24.0, '#35506a', 2.0))
    svg.append(circle(cx, cy, radius, 'none', 1.0, '#284055', 2.0))
    for angle in QPSK_ANGLES:
        px, py = iq_to_xy(cx, cy, radius, complex(math.cos(angle), math.sin(angle)))
        svg.append(circle(px, py, 12.0, 'none', 1.0, '#3d556e', 1.8))
    svg.append(text(cx + radius + 14.0, cy - 8.0, 'I', 'axislabel'))
    svg.append(text(cx + 10.0, cy - radius - 14.0, 'Q', 'axislabel'))


def scatter_window(svg: list[str], cx: float, cy: float, radius: float, samples: list[complex], color: str, *, size: float = 4.8, opacity: float = 0.85) -> None:
    scale = radius * 0.92
    for sample in samples:
        point = sample / max(abs(sample), 1e-12)
        px, py = iq_to_xy(cx, cy, scale, point)
        svg.append(circle(px, py, size, color, opacity))


def metric_bar(svg: list[str], left: float, y: float, width: float, label_text: str, value: float, max_value: float, fill: str, value_text: str) -> None:
    svg.append(text(left, y - 6.0, label_text, 'tiny'))
    svg.append(rect(left, y + 6.0, width, 12.0, '#203244', '#35506a', 1.0, 1.0, 6.0))
    usable = 0.0 if max_value <= 0.0 else max(0.0, min(value / max_value, 1.0)) * width
    svg.append(rect(left, y + 6.0, usable, 12.0, fill, None, 0.0, 0.95, 6.0))
    svg.append(text(left + width + 16.0, y + 18.0, value_text, 'tiny'))


def panel_acquire(svg: list[str], left: float, samples: list[complex], metrics: StateMetrics) -> None:
    cx = left + PANEL_W / 2.0
    cy = PANEL_TOP + 276.0
    radius = 138.0
    draw_constellation_axes(svg, cx, cy, radius)
    window_len = 24
    starts = [24, 112, 224, 336]
    svg.append(text(left + 22.0, PANEL_TOP + 136.0, 'four windows from the same spinning stream', 'tiny'))
    for color, start in zip(WINDOW_COLORS, starts):
        scatter_window(svg, cx, cy, radius, samples[start:start + window_len], color)
    legend_x = left + 22.0
    for idx, color in enumerate(WINDOW_COLORS):
        y = PANEL_TOP + 504.0 + idx * 22.0
        svg.append(circle(legend_x + 6.0, y - 4.0, 6.0, color))
        svg.append(text(legend_x + 20.0, y, f'window {idx + 1}', 'micro'))

    callout_x = left + 218.0
    svg.append(rect(callout_x, PANEL_TOP + 470.0, 248.0, 108.0, '#102033', '#35506a', 1.8, 1.0, 16.0))
    metric_bar(svg, callout_x + 18.0, PANEL_TOP + 496.0, 120.0, 'rho4', metrics.rho4, 1.0, '#60a5fa', f'{metrics.rho4:.3f}')
    metric_bar(svg, callout_x + 18.0, PANEL_TOP + 526.0, 120.0, 'delta4', metrics.delta4_deg, 30.0, '#f59e0b', f'{metrics.delta4_deg:.1f}°')
    metric_bar(svg, callout_x + 18.0, PANEL_TOP + 556.0, 120.0, 'Costas residual', metrics.costas_residual, 1.0, '#f97316', f'{metrics.costas_residual:.3f}')
    add_wrapped_text(
        svg,
        left + 22.0,
        PANEL_TOP + 608.0,
        'Low rho4 and a big mod-90 drift mean the collapsed QPSK phase is still sliding. Stay in acquisition.',
        'tiny',
        max_width=PANEL_W - 44.0,
        font_size=14,
        line_height=20,
    )


def panel_candidate_vs_track(svg: list[str], left: float, candidate_samples: list[complex], track_samples: list[complex], candidate_metrics: StateMetrics, track_metrics: StateMetrics) -> None:
    centers = [left + 150.0, left + 350.0]
    labels = [('candidate lock', candidate_samples, candidate_metrics), ('track-ready', track_samples, track_metrics)]
    radius = 82.0
    for cx, (label_text, samples, metrics) in zip(centers, labels):
        cy = PANEL_TOP + 258.0
        draw_constellation_axes(svg, cx, cy, radius)
        scatter_window(svg, cx, cy, radius, samples[120:184], '#f8fafc', size=4.6, opacity=0.78)
        svg.append(text(cx, PANEL_TOP + 378.0, label_text, 'label', 'middle'))
        metric_bar(svg, cx - 74.0, PANEL_TOP + 396.0, 112.0, 'rho4', metrics.rho4, 1.0, '#60a5fa', f'{metrics.rho4:.3f}')
        metric_bar(svg, cx - 74.0, PANEL_TOP + 428.0, 112.0, 'delta4', metrics.delta4_deg, 10.0, '#22c55e', f'{metrics.delta4_deg:.2f}°')
        metric_bar(svg, cx - 74.0, PANEL_TOP + 460.0, 112.0, 'Costas residual', metrics.costas_residual, 1.0, '#f97316', f'{metrics.costas_residual:.3f}')

    svg.append(line(left + 250.0, PANEL_TOP + 190.0, left + 250.0, PANEL_TOP + 528.0, '#284055', 2.0, 0.9, '6 8'))
    add_wrapped_text(
        svg,
        left + 22.0,
        PANEL_TOP + 546.0,
        'Both clouds are stable modulo 90°, so rho4 stays high. The handoff question is the residual: if it is still large, the loop is not yet in the clean decision-directed region.',
        'tiny',
        max_width=PANEL_W - 44.0,
        font_size=14,
        line_height=20,
    )


def state_box(svg: list[str], x: float, y: float, w: float, title_text: str, lines: list[str], fill: str, stroke: str) -> None:
    svg.append(rect(x, y, w, 110.0, fill, stroke, 2.0, 1.0, 16.0))
    svg.append(text(x + 18.0, y + 28.0, title_text, 'label'))
    svg.append(text_block(x + 18.0, y + 54.0, lines, 'tiny', 18.0))


def arrow(svg: list[str], x1: float, y1: float, x2: float, y2: float, stroke: str) -> None:
    svg.append(line(x1, y1, x2, y2, stroke, 3.0))
    angle = math.atan2(y2 - y1, x2 - x1)
    for delta in (-0.45, 0.45):
        back_x = x2 - 12.0 * math.cos(angle + delta)
        back_y = y2 - 12.0 * math.sin(angle + delta)
        svg.append(line(x2, y2, back_x, back_y, stroke, 3.0))


def panel_state_machine(svg: list[str], left: float, ambiguity_samples: list[complex], ambiguity_metrics: StateMetrics, candidate_metrics: StateMetrics) -> None:
    box_y = PANEL_TOP + 154.0
    state_box(svg, left + 22.0, box_y, 136.0, 'Acquire', ['rho4 low', 'delta4 large', 'keep coarse search alive'], '#102033', '#35506a')
    state_box(svg, left + 182.0, box_y, 150.0, 'Candidate lock', ['rho4 high', 'delta4 small', 'residual still high'], '#13263b', '#4f8cc9')
    state_box(svg, left + 356.0, box_y, 122.0, 'Track', ['rho4 high', 'delta4 small', 'residual low'], '#143225', '#22c55e')
    arrow(svg, left + 162.0, box_y + 55.0, left + 176.0, box_y + 55.0, '#60a5fa')
    arrow(svg, left + 338.0, box_y + 55.0, left + 350.0, box_y + 55.0, '#60a5fa')

    badge_y = PANEL_TOP + 314.0
    svg.append(rect(left + 22.0, badge_y, PANEL_W - 44.0, 76.0, '#3b0f1b', '#f472b6', 2.0, 1.0, 16.0))
    svg.append(text(left + 40.0, badge_y + 28.0, 'Quadrant labeling still unresolved', 'label'))
    add_wrapped_text(
        svg,
        left + 40.0,
        badge_y + 52.0,
        'A QPSK loop can look carrier-locked modulo 90° and still carry the wrong absolute labels. See qpsk-phase-ambiguity-resolution.md.',
        'tiny',
        max_width=PANEL_W - 80.0,
        font_size=14,
        line_height=18,
    )

    iq_box_y = PANEL_TOP + 414.0
    svg.append(rect(left + 22.0, iq_box_y, 224.0, 150.0, '#102033', '#35506a', 1.8, 1.0, 16.0))
    svg.append(text(left + 40.0, iq_box_y + 28.0, 'Do not lead with |I|-|Q|', 'label'))
    add_wrapped_text(
        svg,
        left + 40.0,
        iq_box_y + 56.0,
        'Raw arm balance stays small for both the 35°-off candidate-lock case and the +90° ambiguity case. It is a weak public discriminator here.',
        'tiny',
        max_width=190.0,
        font_size=14,
        line_height=18,
    )
    metric_bar(svg, left + 40.0, iq_box_y + 108.0, 116.0, 'candidate lock', candidate_metrics.iq_balance, 0.05, '#94a3b8', f'{candidate_metrics.iq_balance:.3f}')
    metric_bar(svg, left + 40.0, iq_box_y + 134.0, 116.0, 'quadrant +90°', ambiguity_metrics.iq_balance, 0.05, '#94a3b8', f'{ambiguity_metrics.iq_balance:.3f}')

    cx = left + 360.0
    cy = PANEL_TOP + 494.0
    radius = 82.0
    draw_constellation_axes(svg, cx, cy, radius)
    scatter_window(svg, cx, cy, radius, ambiguity_samples[120:184], '#f8fafc', size=4.6, opacity=0.8)
    svg.append(text(cx, PANEL_TOP + 610.0, 'locked modulo 90°', 'label', 'middle'))
    metric_bar(svg, left + 268.0, PANEL_TOP + 628.0, 116.0, 'rho4', ambiguity_metrics.rho4, 1.0, '#60a5fa', f'{ambiguity_metrics.rho4:.3f}')
    metric_bar(svg, left + 268.0, PANEL_TOP + 656.0, 116.0, 'residual', ambiguity_metrics.costas_residual, 1.0, '#22c55e', f'{ambiguity_metrics.costas_residual:.3f}')


def main() -> None:
    symbols = qpsk_symbols(512)
    state_samples = {spec.key: impaired_samples(symbols, spec) for spec in STATES}
    metrics = build_metrics(symbols)

    svg: list[str] = [
        svg_root(WIDTH, HEIGHT),
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#071018"/>',
        '    <stop offset="100%" stop-color="#0f1d2b"/>',
        '  </linearGradient>',
        '  <style>',
        '    .title { font: 700 32px Helvetica, Arial, sans-serif; fill: #e6edf3; }',
        '    .subtitle { font: 500 18px Helvetica, Arial, sans-serif; fill: #9fb3c8; }',
        '    .label { font: 700 18px Helvetica, Arial, sans-serif; fill: #dce7f3; }',
        '    .small { font: 500 15px Helvetica, Arial, sans-serif; fill: #9fb3c8; }',
        '    .tiny { font: 500 15px Helvetica, Arial, sans-serif; fill: #b6c7d8; }',
        '    .micro { font: 600 13px Helvetica, Arial, sans-serif; fill: #dce7f3; }',
        '    .axislabel { font: 600 13px Helvetica, Arial, sans-serif; fill: #dce7f3; }',
        '  </style>',
        '</defs>',
        rect(0.0, 0.0, WIDTH, HEIGHT, 'url(#bg)', None, 0.0, 1.0, 0.0),
        text(50.0, 52.0, 'Carrier lock detection and acquisition-to-tracking handoff', 'title'),
        text_block(
            50.0,
            82.0,
            [
                'Acquisition asks whether the QPSK symmetry view has stopped spinning modulo 90°.',
                'Tracking asks whether the remaining phase error is small enough to trust decision-directed feedback.',
            ],
            'subtitle',
            24.0,
        ),
    ]

    panel(svg, PANEL_LEFTS[0], '1. Acquire: the mod-90 view is still moving', 'One spinning stream, sampled in four windows. Low rho4 and large delta4 mean stay in coarse acquisition.')
    panel(svg, PANEL_LEFTS[1], '2. Candidate lock is not the same as track-ready', 'A stable-but-far constellation and a near-lock constellation can both look settled modulo 90°. The residual decides the handoff.')
    panel(svg, PANEL_LEFTS[2], '3. Handoff needs a tiny state machine', 'Acquire, then candidate lock, then track. Carrier lock still does not resolve QPSK quadrant labeling.')

    panel_acquire(svg, PANEL_LEFTS[0], state_samples['acquire'], metrics['acquire'])
    panel_candidate_vs_track(svg, PANEL_LEFTS[1], state_samples['candidate'], state_samples['track'], metrics['candidate'], metrics['track'])
    panel_state_machine(svg, PANEL_LEFTS[2], state_samples['ambiguity'], metrics['ambiguity'], metrics['candidate'])

    add_wrapped_text(
        svg,
        50.0,
        826.0,
        'Do not flatten lock into one threshold. Ask two questions instead: is the mod-90 view stable, and is the remaining residual small enough for tracking?',
        'small',
        max_width=1500.0,
        font_size=15.0,
        line_height=21.0,
    )
    svg.append('</svg>')

    SVG_OUT.parent.mkdir(parents=True, exist_ok=True)
    SVG_OUT.write_text('\n'.join(svg) + '\n')
    export_png_from_svg(SVG_OUT, PNG_OUT, size=1800, dpi=300)

    with CSV_OUT.open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['regime', 'iq_balance', 'rho4', 'delta4_deg', 'costas_residual', 'read'])
        for spec in STATES:
            row = metrics[spec.key]
            writer.writerow(
                [
                    spec.label,
                    f'{row.iq_balance:.6f}',
                    f'{row.rho4:.6f}',
                    f'{row.delta4_deg:.6f}',
                    f'{row.costas_residual:.6f}',
                    spec.read,
                ]
            )

    print(f'WROTE {SVG_OUT}')
    print(f'WROTE {PNG_OUT}')
    print(f'WROTE {CSV_OUT}')


if __name__ == '__main__':
    main()
