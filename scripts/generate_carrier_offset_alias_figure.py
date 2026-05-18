#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
import random
from dataclasses import dataclass
from pathlib import Path

from svg_layout import add_wrapped_text, export_png_from_svg, svg_root, text, text_block

REPO = Path(__file__).resolve().parents[1]
SVG_OUT = REPO / 'assets/2026-05-17-carrier-offset-pull-in-alias.svg'
PNG_OUT = REPO / 'assets/2026-05-17-carrier-offset-pull-in-alias.png'
CSV_OUT = REPO / 'assets/2026-05-17-carrier-offset-pull-in-alias.csv'

WIDTH = 1200
HEIGHT = 1840
QPSK_ANGLES = [math.pi / 4.0 + k * math.pi / 2.0 for k in range(4)]
REGIME_ROWS = [
    (0.200, 0.057, 0.057, 0.2002, 1.000, 'loop alone is already fine'),
    (0.350, 0.278, 0.057, 0.3493, 1.000, 'coarse help clearly matters'),
    (0.700, 0.426, 0.057, 0.6995, 1.000, 'still inside the 4th-power window'),
    (0.785, 0.425, 0.057, 0.7850, 1.000, 'right at the edge; still honest here'),
    (0.790, 0.427, 0.057, -0.7808, 0.250, 'alias just kicked in'),
    (0.850, 0.427, 0.057, -0.7215, 0.250, 'farther past the cliff'),
]


@dataclass(frozen=True)
class CloudSpec:
    key: str
    label: str
    phase_jitter: float
    radius_jitter: float
    noise: float
    seed: int


CLOUDS = {
    'phase_only': CloudSpec('phase_only', 'phase-only tracking @ +0.35', 0.38, 0.08, 0.035, 11),
    'coarse_track': CloudSpec('coarse_track', 'coarse + Costas @ +0.35', 0.07, 0.05, 0.025, 17),
    'alias_clean': CloudSpec('alias_clean', 'aliased coarse estimate @ +0.79', 0.06, 0.05, 0.025, 23),
}


def line(x1: float, y1: float, x2: float, y2: float, stroke: str, width: float = 2.0, opacity: float = 1.0, dash: str | None = None) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}" stroke-linecap="round"{dash_attr}/>'


def circle(x: float, y: float, r: float, fill: str, opacity: float = 1.0, stroke: str | None = None, stroke_width: float = 0.0) -> str:
    stroke_attr = '' if stroke is None else f' stroke="{stroke}" stroke-width="{stroke_width:.1f}"'
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" opacity="{opacity}"{stroke_attr}/>'


def rounded_rect(x: float, y: float, w: float, h: float, fill: str, stroke: str | None = None, stroke_width: float = 0.0, opacity: float = 1.0, rx: float = 16.0) -> str:
    stroke_attr = '' if stroke is None else f' stroke="{stroke}" stroke-width="{stroke_width:.1f}"'
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}" fill="{fill}" opacity="{opacity}"{stroke_attr}/>'


def iq_to_xy(cx: float, cy: float, scale: float, z: complex) -> tuple[float, float]:
    return cx + z.real * scale, cy - z.imag * scale


def draw_axes(svg: list[str], cx: float, cy: float, radius: float) -> None:
    svg.append(line(cx - radius - 18.0, cy, cx + radius + 18.0, cy, '#385169', 2.0))
    svg.append(line(cx, cy - radius - 18.0, cx, cy + radius + 18.0, '#385169', 2.0))
    svg.append(circle(cx, cy, radius, 'none', 1.0, '#294155', 2.0))
    for angle in QPSK_ANGLES:
        px, py = iq_to_xy(cx, cy, radius, complex(math.cos(angle), math.sin(angle)))
        svg.append(circle(px, py, 10.0, 'none', 1.0, '#45637e', 1.8))
    svg.append(text(cx + radius + 12.0, cy - 6.0, 'I', 'axislabel'))
    svg.append(text(cx + 8.0, cy - radius - 14.0, 'Q', 'axislabel'))


def qpsk_cloud(spec: CloudSpec, count: int = 180) -> list[complex]:
    rng = random.Random(spec.seed)
    points: list[complex] = []
    for _ in range(count):
        angle = rng.choice(QPSK_ANGLES)
        jitter = rng.gauss(0.0, spec.phase_jitter)
        radius = 1.0 + rng.gauss(0.0, spec.radius_jitter)
        sample = complex(math.cos(angle + jitter), math.sin(angle + jitter)) * radius
        sample += complex(rng.gauss(0.0, spec.noise), rng.gauss(0.0, spec.noise))
        points.append(sample)
    return points


def scatter(svg: list[str], cx: float, cy: float, radius: float, points: list[complex], fill: str, size: float = 4.4, opacity: float = 0.8) -> None:
    scale = radius * 0.80
    for point in points:
        magnitude = abs(point)
        if magnitude > 1.08:
            point = point / magnitude * 1.08
        px, py = iq_to_xy(cx, cy, scale, point)
        svg.append(circle(px, py, size, fill, opacity))


def metric_chip(svg: list[str], x: float, y: float, label_text: str, value_text: str, fill: str) -> None:
    svg.append(rounded_rect(x, y, 204.0, 36.0, fill, '#4f708f', 1.2, 1.0, 10.0))
    svg.append(text(x + 14.0, y + 23.0, label_text, 'tiny'))
    svg.append(text(x + 190.0, y + 23.0, value_text, 'tiny', 'end'))


def regime_strip(svg: list[str]) -> None:
    left = 60.0
    top = 168.0
    width = 1080.0
    height = 190.0
    axis_y = top + 112.0
    max_offset = 1.0
    loop_limit = 0.25
    alias_limit = math.pi / 4.0

    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0, 1.0, 18.0))
    svg.append(text(left + 24.0, top + 32.0, '1. Offset regimes that actually matter', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 62.0,
        'The loop owns the center. A 4th-power coarse estimate widens the handoff band. Past π/4, that coarse estimate aliases.',
        'small',
        max_width=880.0,
        font_size=15.0,
        line_height=20.0,
    )

    bar_left = left + 24.0
    bar_top = top + 88.0
    bar_w = width - 48.0
    bar_h = 28.0

    def xpos(value: float) -> float:
        return bar_left + (value / max_offset) * bar_w

    svg.append(rounded_rect(bar_left, bar_top, xpos(loop_limit) - bar_left, bar_h, '#163825', None, 0.0, 1.0, 14.0))
    svg.append(rounded_rect(xpos(loop_limit), bar_top, xpos(alias_limit) - xpos(loop_limit), bar_h, '#113154', None, 0.0, 1.0, 14.0))
    svg.append(rounded_rect(xpos(alias_limit), bar_top, bar_left + bar_w - xpos(alias_limit), bar_h, '#44151f', None, 0.0, 1.0, 14.0))
    svg.append(text(bar_left + 16.0, bar_top + 19.0, 'loop alone', 'micro'))
    svg.append(text(xpos(loop_limit) + 16.0, bar_top + 19.0, 'coarse-help handoff', 'micro'))
    svg.append(text(xpos(alias_limit) + 16.0, bar_top + 19.0, 'alias cliff', 'micro'))

    svg.append(line(bar_left, axis_y, bar_left + bar_w, axis_y, '#5d7fa3', 2.5))
    for tick in (0.0, 0.25, 0.5, 0.75, 1.0):
        x = xpos(tick)
        svg.append(line(x, axis_y - 8.0, x, axis_y + 8.0, '#5d7fa3', 2.0))
        svg.append(text(x, axis_y + 28.0, f'{tick:.2f}', 'tiny', 'middle'))
    svg.append(text(bar_left + bar_w / 2.0, axis_y + 54.0, 'frequency offset (rad/sample)', 'tiny', 'middle'))

    svg.append(line(xpos(alias_limit), bar_top - 10.0, xpos(alias_limit), axis_y + 14.0, '#fda4af', 2.0, 0.9, '5 6'))
    svg.append(text(xpos(alias_limit), top + 168.0, 'π/4 ≈ 0.785', 'tiny', 'middle'))

    markers = [
        (0.20, '#4ade80', '+0.20', top + 64.0),
        (0.35, '#93c5fd', '+0.35', top + 48.0),
        (0.785, '#fde68a', '+0.785', top + 64.0),
        (0.790, '#fb7185', '+0.790', top + 38.0),
    ]
    for value, color, label_text, marker_y in markers:
        x = xpos(value)
        svg.append(line(x, marker_y + 8.0, x, bar_top - 2.0, color, 2.0))
        svg.append(circle(x, marker_y, 6.0, color, 1.0, '#0b1621', 1.0))
        svg.append(text(x, marker_y - 12.0, label_text, 'tiny', 'middle'))


def comparison_panel(svg: list[str], left: float, top: float, width: float, height: float) -> None:
    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0, 1.0, 18.0))
    svg.append(text(left + 24.0, top + 32.0, '2. Medium offset: this is where coarse help earns its keep', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 60.0,
        'At +0.35 rad/sample, the loop-alone path is no longer a clean story. The 4th-power estimate gets the residual back into the decision-directed neighborhood.',
        'small',
        max_width=width - 48.0,
        font_size=15.0,
        line_height=20.0,
    )

    clouds = [('phase_only', left + 290.0), ('coarse_track', left + 790.0)]
    radius = 98.0
    for key, cx in clouds:
        cy = top + 208.0
        spec = CLOUDS[key]
        draw_axes(svg, cx, cy, radius)
        scatter(svg, cx, cy, radius, qpsk_cloud(spec), '#f8fafc', 4.3, 0.8)
        svg.append(text(cx, top + 332.0, spec.label, 'micro', 'middle'))

    metric_chip(svg, left + 164.0, top + 358.0, 'phase-only', 'RMS 0.278', '#2a1820')
    metric_chip(svg, left + 376.0, top + 358.0, 'coarse + tracking', 'RMS 0.057', '#142f23')
    metric_chip(svg, left + 588.0, top + 358.0, 'coarse estimate', '+0.3493', '#11263d')
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 410.0,
        'This is the honest public use-case for the front end: not magic CFO immunity, just enough coarse help to make the handoff viable again.',
        'tiny',
        max_width=width - 48.0,
        font_size=14.0,
        line_height=19.0,
    )


def alias_panel(svg: list[str], left: float, top: float, width: float, height: float) -> None:
    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0, 1.0, 18.0))
    svg.append(text(left + 24.0, top + 32.0, '3. Alias warning: the cloud can look fine while the payload is wrong', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 60.0,
        'Just over the π/4 edge, the coarse estimate folds to the wrong side. Geometry alone stops being a trustworthy success metric.',
        'small',
        max_width=width - 48.0,
        font_size=15.0,
        line_height=20.0,
    )

    cx = left + 220.0
    cy = top + 246.0
    radius = 100.0
    draw_axes(svg, cx, cy, radius)
    scatter(svg, cx, cy, radius, qpsk_cloud(CLOUDS['alias_clean']), '#f8fafc', 4.3, 0.8)
    svg.append(text(cx, top + 376.0, CLOUDS['alias_clean'].label, 'micro', 'middle'))

    table_x = left + 488.0
    table_y = top + 126.0
    svg.append(rounded_rect(table_x, table_y, 352.0, 184.0, '#0f1b29', '#44637d', 1.8, 1.0, 14.0))
    svg.append(text(table_x + 18.0, table_y + 28.0, 'Edge check', 'label'))
    svg.append(text(table_x + 18.0, table_y + 56.0, 'offset', 'tiny'))
    svg.append(text(table_x + 128.0, table_y + 56.0, 'coarse est', 'tiny'))
    svg.append(text(table_x + 320.0, table_y + 56.0, 'accuracy', 'tiny', 'end'))
    rows = [
        ('+0.785', '+0.7850', '1.00', '#e5e7eb'),
        ('+0.790', '-0.7808', '0.25', '#fda4af'),
    ]
    for idx, (offset_text, estimate_text, accuracy_text, color) in enumerate(rows):
        y = table_y + 88.0 + idx * 42.0
        svg.append(line(table_x + 16.0, y - 16.0, table_x + 320.0, y - 16.0, '#213549', 1.3))
        svg.append(text(table_x + 18.0, y, offset_text, 'micro'))
        svg.append(text(table_x + 128.0, y, estimate_text, 'micro'))
        svg.append(text(table_x + 320.0, y, accuracy_text, 'micro', 'end'))
        svg.append(circle(table_x + 336.0, y - 6.0, 5.5, color))

    svg.append(rounded_rect(left + 488.0, top + 334.0, 352.0, 108.0, '#3a1018', '#f87171', 1.8, 1.0, 14.0))
    svg.append(text(left + 506.0, top + 362.0, 'Read this literally', 'label'))
    add_wrapped_text(
        svg,
        left + 506.0,
        top + 392.0,
        'clean-looking constellation ≠ correct decoded labels once the coarse estimate aliases',
        'tiny',
        max_width=312.0,
        font_size=14.0,
        line_height=18.0,
    )

    svg.append(rounded_rect(left + 24.0, top + 402.0, 424.0, 72.0, '#13263b', '#4f8cc9', 1.8, 1.0, 14.0))
    svg.append(text(left + 42.0, top + 430.0, 'Back-pointer', 'label'))
    add_wrapped_text(
        svg,
        left + 164.0,
        top + 430.0,
        'carrier-recovery-after-timing.md explains why acquisition and tracking were split in the first place.',
        'tiny',
        max_width=260.0,
        font_size=14.0,
        line_height=18.0,
    )


def write_csv() -> None:
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow([
            'freq_offset_rad_per_sample',
            'phase_only_tracked_rms',
            'coarse_plus_tracking_rms',
            'coarse_freq_estimate',
            'best_constant_rotation_symbol_accuracy',
            'read',
        ])
        for row in REGIME_ROWS:
            writer.writerow(row)


def main() -> None:
    svg: list[str] = [
        svg_root(WIDTH, HEIGHT),
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#071018"/>',
        '    <stop offset="100%" stop-color="#0f1d2b"/>',
        '  </linearGradient>',
        '  <style>',
        '    .title { font: 700 34px Helvetica, Arial, sans-serif; fill: #e6edf3; }',
        '    .subtitle { font: 500 18px Helvetica, Arial, sans-serif; fill: #9fb3c8; }',
        '    .label { font: 700 19px Helvetica, Arial, sans-serif; fill: #dce7f3; }',
        '    .small { font: 500 15px Helvetica, Arial, sans-serif; fill: #a9bfd3; }',
        '    .tiny { font: 500 14px Helvetica, Arial, sans-serif; fill: #b8c8d8; }',
        '    .micro { font: 600 13px Helvetica, Arial, sans-serif; fill: #e2ebf4; }',
        '    .axislabel { font: 600 13px Helvetica, Arial, sans-serif; fill: #e2ebf4; }',
        '  </style>',
        '</defs>',
        rounded_rect(0.0, 0.0, WIDTH, HEIGHT, 'url(#bg)', None, 0.0, 1.0, 0.0),
        text(58.0, 60.0, 'Carrier offset, pull-in, and the π/4 alias cliff', 'title'),
        text_block(
            58.0,
            92.0,
            [
                'The real public split is three regimes:',
                'loop alone near center, coarse-help handoff in the widened pull-in band,',
                'and an alias cliff where clean geometry can still hide wrong decoded labels.',
            ],
            'subtitle',
            24.0,
        ),
    ]

    regime_strip(svg)
    comparison_panel(svg, 60.0, 420.0, 1080.0, 430.0)
    alias_panel(svg, 60.0, 890.0, 1080.0, 500.0)

    add_wrapped_text(
        svg,
        58.0,
        1740.0,
        'Source rows are exported to assets/2026-05-17-carrier-offset-pull-in-alias.csv. Local evidence comes from the bounded QPSK symbol-rate checks in costas-loop-lab and the companion research note.',
        'small',
        max_width=1080.0,
        font_size=15.0,
        line_height=20.0,
    )
    svg.append('</svg>')

    SVG_OUT.parent.mkdir(parents=True, exist_ok=True)
    SVG_OUT.write_text('\n'.join(svg) + '\n')
    export_png_from_svg(SVG_OUT, PNG_OUT, size=1900, dpi=300)
    write_csv()

    print(f'WROTE {SVG_OUT}')
    print(f'WROTE {PNG_OUT}')
    print(f'WROTE {CSV_OUT}')


if __name__ == '__main__':
    main()
