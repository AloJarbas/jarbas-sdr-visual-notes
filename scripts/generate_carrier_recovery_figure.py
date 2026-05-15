#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path

from svg_layout import add_wrapped_text, export_png_from_svg, svg_root, text, text_block, wrap_text

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / 'assets/2026-05-14-carrier-recovery-after-timing.svg'
PNG_OUT = REPO / 'assets/2026-05-14-carrier-recovery-after-timing.png'

PANEL_W = 420.0
PANEL_H = 470.0
PANEL_TOP = 170.0
PANEL_LEFTS = [40.0, 510.0, 980.0]
CENTER_Y = PANEL_TOP + 228.0
RADIUS = 102.0

TIME_PHASES = [0.10, 0.28, 0.46, 0.64]
TIME_COLORS = ['#60a5fa', '#22c55e', '#f59e0b', '#f97316']
IDEAL_QPSK = [math.pi / 4.0 + k * math.pi / 2.0 for k in range(4)]


def line(x1: float, y1: float, x2: float, y2: float, stroke: str, width: float = 2.0, opacity: float = 1.0, dash: str | None = None) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}"{dash_attr}/>'


def circle(x: float, y: float, r: float, fill: str, opacity: float = 1.0, stroke: str | None = None, stroke_width: float = 0.0) -> str:
    stroke_attr = '' if stroke is None else f' stroke="{stroke}" stroke-width="{stroke_width:.1f}"'
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" opacity="{opacity}"{stroke_attr}/>'


def panel(svg: list[str], left: float, title: str, subtitle: str) -> None:
    svg.append(f'<rect x="{left:.1f}" y="{PANEL_TOP:.1f}" width="{PANEL_W:.1f}" height="{PANEL_H:.1f}" class="panel"/>')
    title_lines = wrap_text(title, max_width=PANEL_W - 44.0, font_size=18)
    svg.append(text_block(left + 22.0, PANEL_TOP + 34.0, title_lines, 'label', 22.0))
    subtitle_y = PANEL_TOP + 34.0 + 22.0 * max(len(title_lines), 1) + 8.0
    add_wrapped_text(svg, left + 22.0, subtitle_y, subtitle, 'small', max_width=PANEL_W - 44.0, font_size=15, line_height=20)


def iq_to_xy(left: float, z: complex, scale: float = RADIUS) -> tuple[float, float]:
    cx = left + PANEL_W / 2.0
    cy = CENTER_Y
    return cx + z.real * scale, cy - z.imag * scale


def draw_axes(svg: list[str], left: float, show_circle: bool = True) -> None:
    cx = left + PANEL_W / 2.0
    cy = CENTER_Y
    svg.append(line(cx - 136.0, cy, cx + 136.0, cy, '#35506a', 2.0, 1.0))
    svg.append(line(cx, cy - 136.0, cx, cy + 136.0, '#35506a', 2.0, 1.0))
    if show_circle:
        svg.append(circle(cx, cy, RADIUS, 'none', 1.0, '#284055', 2.0))
    svg.append(text(cx + 126.0, cy - 10.0, 'I', 'axislabel'))
    svg.append(text(cx + 10.0, cy - 120.0, 'Q', 'axislabel'))


def polyline(points: list[tuple[float, float]], stroke: str, width: float = 2.5, opacity: float = 0.8, dash: str | None = None) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ''
    coords = ' '.join(f'{x:.1f},{y:.1f}' for x, y in points)
    return f'<polyline points="{coords}" fill="none" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}" stroke-linecap="round" stroke-linejoin="round"{dash_attr}/>'


def add_time_legend(svg: list[str], left: float, y: float) -> None:
    svg.append(text(left + 22.0, y, 'time snapshots', 'tiny'))
    x = left + 144.0
    for idx, color in enumerate(TIME_COLORS):
        svg.append(circle(x + idx * 32.0, y - 5.0, 6.0, color))
        svg.append(text(x + idx * 32.0, y + 16.0, f't{idx}', 'micro', 'middle'))


def panel_one(svg: list[str], left: float) -> None:
    draw_axes(svg, left)
    add_time_legend(svg, left, PANEL_TOP + 108.0)

    for base_angle in IDEAL_QPSK:
        pts = [iq_to_xy(left, complex(math.cos(base_angle + phi), math.sin(base_angle + phi))) for phi in TIME_PHASES]
        svg.append(polyline(pts, '#7dd3fc', width=2.0, opacity=0.28))

    for color, phi in zip(TIME_COLORS, TIME_PHASES):
        for base_angle in IDEAL_QPSK:
            z = complex(math.cos(base_angle + phi), math.sin(base_angle + phi))
            x, y = iq_to_xy(left, z)
            svg.append(circle(x, y, 7.0, color, 0.95))

    cx = left + PANEL_W / 2.0
    cy = CENTER_Y
    svg.append(polyline([(cx + 80.0, cy - 72.0), (cx + 98.0, cy - 46.0), (cx + 70.0, cy - 44.0)], '#f8fafc', width=2.0, opacity=0.9))
    add_wrapped_text(
        svg,
        left + 22.0,
        PANEL_TOP + 392.0,
        'Timing is right, but the whole constellation still rotates. That remaining motion is carrier phase or frequency error.',
        'tiny',
        max_width=PANEL_W - 44.0,
        font_size=14,
        line_height=20,
    )


def panel_two(svg: list[str], left: float) -> None:
    draw_axes(svg, left)
    add_time_legend(svg, left, PANEL_TOP + 108.0)

    collapsed: list[tuple[float, float]] = []
    for color, phi in zip(TIME_COLORS, TIME_PHASES):
        z = complex(math.cos(math.pi + 4.0 * phi), math.sin(math.pi + 4.0 * phi))
        pt = iq_to_xy(left, z)
        collapsed.append(pt)
        for ring in (18.0, 12.0, 7.0, 3.5):
            svg.append(circle(pt[0], pt[1], ring, color, 0.08))
        svg.append(circle(pt[0], pt[1], 8.0, color, 0.96))

    svg.append(polyline(collapsed, '#f8fafc', width=3.0, opacity=0.8))
    add_wrapped_text(
        svg,
        left + 22.0,
        PANEL_TOP + 372.0,
        '4th power removes the QPSK data phase. The common carrier trend remains, scaled by 4. Good for coarse acquisition; 90° ambiguity remains.',
        'tiny',
        max_width=PANEL_W - 44.0,
        font_size=14,
        line_height=20,
    )


def residual_cloud(base_angle: float) -> list[complex]:
    pts: list[complex] = []
    for idx in range(8):
        radial = 0.92 + 0.015 * ((idx % 3) - 1)
        tangential = 0.03 * math.sin(0.8 * idx + base_angle)
        angle = base_angle + tangential
        pts.append(complex(radial * math.cos(angle), radial * math.sin(angle)))
    return pts


def panel_three(svg: list[str], left: float) -> None:
    draw_axes(svg, left)

    ghost_phi = 0.16
    for base_angle in IDEAL_QPSK:
        ghost = complex(math.cos(base_angle + ghost_phi), math.sin(base_angle + ghost_phi))
        x, y = iq_to_xy(left, ghost)
        svg.append(circle(x, y, 12.0, '#6b7280', 0.15))

    for base_angle in IDEAL_QPSK:
        x0, y0 = iq_to_xy(left, complex(math.cos(base_angle), math.sin(base_angle)))
        svg.append(circle(x0, y0, 18.0, 'none', 1.0, '#35506a', 2.0))
        for pt in residual_cloud(base_angle):
            x, y = iq_to_xy(left, pt)
            svg.append(circle(x, y, 5.0, '#f8fafc', 0.9))
        svg.append(circle(x0, y0, 7.0, '#a78bfa', 0.95))

    svg.append(polyline([(left + 284.0, PANEL_TOP + 176.0), (left + 310.0, PANEL_TOP + 158.0), (left + 314.0, PANEL_TOP + 188.0)], '#c4b5fd', width=3.0, opacity=0.95))
    add_wrapped_text(
        svg,
        left + 22.0,
        PANEL_TOP + 372.0,
        'After coarse alignment, feedback only corrects residual error. That is the Costas / decision-directed sweet spot. Tracking range is smaller than acquisition range.',
        'tiny',
        max_width=PANEL_W - 44.0,
        font_size=14,
        line_height=20,
    )


def main() -> None:
    width, height = 1540, 700
    svg: list[str] = [
        svg_root(width, height),
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
        '    .tiny { font: 500 14px Helvetica, Arial, sans-serif; fill: #9fb3c8; }',
        '    .micro { font: 500 12px Helvetica, Arial, sans-serif; fill: #8aa3bc; }',
        '    .axislabel { font: 600 14px Helvetica, Arial, sans-serif; fill: #dce7f3; }',
        '    .panel { fill: #122131; stroke: #5e7fa3; stroke-width: 2; rx: 18; }',
        '  </style>',
        '</defs>',
        f'<rect width="{width}" height="{height}" fill="url(#bg)"/>',
        text(50.0, 52.0, 'Carrier recovery after timing', 'title'),
    ]
    svg.append(
        text_block(
            50.0,
            82.0,
            [
                'Timing recovery fixes when to sample.',
                'Carrier recovery removes the remaining common rotation.',
            ],
            'subtitle',
            24.0,
        )
    )

    panel(svg, PANEL_LEFTS[0], '1. Timing locked, constellation still rotating', 'Same QPSK symbols at several times after timing is already fixed.')
    panel(svg, PANEL_LEFTS[1], '2. 4th power reveals common phase', 'Each time snapshot collapses to one shared phase point.')
    panel(svg, PANEL_LEFTS[2], '3. Fine tracking holds the lock', 'After coarse correction, feedback only cleans up residual error.')

    panel_one(svg, PANEL_LEFTS[0])
    panel_two(svg, PANEL_LEFTS[1])
    panel_three(svg, PANEL_LEFTS[2])

    add_wrapped_text(
        svg,
        50.0,
        666.0,
        'Acquisition versus tracking is the key split: symmetry-based coarse alignment first, feedback fine tracking second.',
        'small',
        max_width=1380,
        font_size=15,
        line_height=21,
    )
    svg.append('</svg>')

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text('\n'.join(svg) + '\n')
    export_png_from_svg(OUT, PNG_OUT, size=1600, dpi=300)
    print(f'WROTE {OUT}')
    print(f'WROTE {PNG_OUT}')


if __name__ == '__main__':
    main()
