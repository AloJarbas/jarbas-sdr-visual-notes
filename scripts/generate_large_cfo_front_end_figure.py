#!/usr/bin/env python3
from __future__ import annotations

import math
from collections import defaultdict
from pathlib import Path

from large_cfo_front_end import SweepRow, alias_limit_normalized, sweep_normalized_cfo, write_csv
from svg_layout import add_wrapped_text, export_png_from_svg, svg_root, text, text_block

REPO = Path(__file__).resolve().parents[1]
SVG_OUT = REPO / 'assets/2026-05-19-large-cfo-front-end-boundary.svg'
PNG_OUT = REPO / 'assets/2026-05-19-large-cfo-front-end-boundary.png'
CSV_OUT = REPO / 'assets/2026-05-19-large-cfo-front-end-boundary.csv'

WIDTH = 1900
HEIGHT = 1900
SPS_VALUES = [1, 2, 4]
NORMALIZED_CFO_VALUES = [round(step * 0.01, 2) for step in range(0, 66)]
EXAMPLE_CFO = 0.30


def line(x1: float, y1: float, x2: float, y2: float, stroke: str, width: float = 2.0, opacity: float = 1.0, dash: str | None = None) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}" stroke-linecap="round"{dash_attr}/>'


def circle(x: float, y: float, r: float, fill: str, opacity: float = 1.0, stroke: str | None = None, stroke_width: float = 0.0) -> str:
    stroke_attr = '' if stroke is None else f' stroke="{stroke}" stroke-width="{stroke_width:.1f}"'
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" opacity="{opacity}"{stroke_attr}/>'


def rounded_rect(x: float, y: float, w: float, h: float, fill: str, stroke: str | None = None, stroke_width: float = 0.0, opacity: float = 1.0, rx: float = 16.0) -> str:
    stroke_attr = '' if stroke is None else f' stroke="{stroke}" stroke-width="{stroke_width:.1f}"'
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}" fill="{fill}" opacity="{opacity}"{stroke_attr}/>'


def polyline(points: list[tuple[float, float]], stroke: str, width: float = 3.0) -> str:
    path = ' '.join(f'{x:.1f},{y:.1f}' for x, y in points)
    return f'<polyline points="{path}" fill="none" stroke="{stroke}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>'


def segmented_points(rows: list[SweepRow], jump_threshold: float = 0.14) -> list[list[SweepRow]]:
    if not rows:
        return []
    segments: list[list[SweepRow]] = [[rows[0]]]
    for row in rows[1:]:
        previous = segments[-1][-1]
        if abs(row.estimated_normalized_cfo - previous.estimated_normalized_cfo) > jump_threshold:
            segments.append([row])
            continue
        segments[-1].append(row)
    return segments


def axis_x(value: float, left: float, width: float, maximum: float) -> float:
    return left + width * (value / maximum)


def axis_y(value: float, top: float, height: float, maximum: float) -> float:
    return top + height - height * (value / maximum)


def capture_window_panel(svg: list[str]) -> None:
    left = 60.0
    top = 172.0
    width = 1080.0
    height = 316.0
    axis_left = left + 180.0
    axis_width = 820.0
    maximum = 0.65

    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0, 1.0, 18.0))
    svg.append(text(left + 24.0, top + 34.0, '1. The alias limit scales with the sample rate seen by the estimator', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 64.0,
        'For QPSK 4th-power coarse recovery, the honest window is |Δf| < F_s/8. If F_s = L R_s, that becomes |Δf|/R_s < L/8.',
        'small',
        max_width=990.0,
        font_size=15.0,
        line_height=20.0,
    )

    bar_top = top + 108.0
    row_gap = 68.0
    colors = {1: '#fda4af', 2: '#93c5fd', 4: '#4ade80'}
    for idx, samples_per_symbol in enumerate(SPS_VALUES):
        y = bar_top + idx * row_gap
        limit = alias_limit_normalized(samples_per_symbol)
        x0 = axis_left
        x1 = axis_x(limit, axis_left, axis_width, maximum)
        svg.append(text(left + 24.0, y + 17.0, f'{samples_per_symbol} sample/symbol', 'micro'))
        svg.append(rounded_rect(axis_left, y, axis_width, 24.0, '#162433', None, 0.0, 1.0, 12.0))
        svg.append(rounded_rect(axis_left, y, x1 - x0, 24.0, colors[samples_per_symbol], None, 0.0, 0.95, 12.0))
        svg.append(line(x1, y - 6.0, x1, y + 30.0, colors[samples_per_symbol], 2.0, 1.0, '5 5'))
        svg.append(text(axis_left + 8.0, y + 17.0, 'honest coarse window', 'tiny'))
        svg.append(text(x1 + 8.0, y + 17.0, f'limit = {limit:.3f} R_s', 'tiny'))

    axis_y0 = top + 280.0
    svg.append(line(axis_left, axis_y0, axis_left + axis_width, axis_y0, '#5d7fa3', 2.2))
    for tick in range(0, 14):
        value = tick * 0.05
        if value > maximum:
            break
        x = axis_x(value, axis_left, axis_width, maximum)
        svg.append(line(x, axis_y0 - 8.0, x, axis_y0 + 8.0, '#5d7fa3', 1.8))
        svg.append(text(x, axis_y0 + 28.0, f'{value:.2f}', 'tiny', 'middle'))
    svg.append(text(axis_left + axis_width / 2.0, axis_y0 + 54.0, 'normalized CFO  |Δf| / R_s', 'tiny', 'middle'))


def sweep_panel(svg: list[str], rows: list[SweepRow]) -> None:
    left = 60.0
    top = 526.0
    width = 1080.0
    height = 620.0
    chart_left = left + 90.0
    chart_top = top + 116.0
    chart_width = 640.0
    chart_height = 360.0
    maximum = 0.65
    colors = {1: '#fda4af', 2: '#93c5fd', 4: '#4ade80'}

    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0, 1.0, 18.0))
    svg.append(text(left + 24.0, top + 34.0, '2. The same physical CFO can alias at 1 sps and stay honest at 4 sps', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 64.0,
        'This local toy check uses timed QPSK symbols, a hold-model oversampled waveform, and the same 4th-power phase-difference estimator at 1, 2, and 4 samples per symbol.',
        'small',
        max_width=1000.0,
        font_size=15.0,
        line_height=20.0,
    )

    svg.append(line(chart_left, chart_top + chart_height, chart_left + chart_width, chart_top + chart_height, '#5d7fa3', 2.2))
    svg.append(line(chart_left, chart_top, chart_left, chart_top + chart_height, '#5d7fa3', 2.2))
    for tick in range(0, 14):
        value = tick * 0.05
        if value > maximum:
            break
        x = axis_x(value, chart_left, chart_width, maximum)
        y = axis_y(value, chart_top, chart_height, maximum)
        svg.append(line(x, chart_top + chart_height - 6.0, x, chart_top + chart_height + 6.0, '#5d7fa3', 1.5))
        svg.append(text(x, chart_top + chart_height + 24.0, f'{value:.2f}', 'tiny', 'middle'))
        svg.append(line(chart_left - 6.0, y, chart_left + 6.0, y, '#5d7fa3', 1.5))
        svg.append(text(chart_left - 16.0, y + 4.0, f'{value:.2f}', 'tiny', 'end'))
    svg.append(text(chart_left + chart_width / 2.0, chart_top + chart_height + 54.0, 'true normalized CFO  Δf / R_s', 'tiny', 'middle'))
    svg.append(text(chart_left - 56.0, chart_top + chart_height / 2.0, 'estimated Δf / R_s', 'tiny', 'middle'))

    identity = [
        (axis_x(value, chart_left, chart_width, maximum), axis_y(value, chart_top, chart_height, maximum))
        for value in NORMALIZED_CFO_VALUES
    ]
    svg.append(polyline(identity, '#dce7f3', 2.2))
    svg.append(text(chart_left + chart_width - 12.0, chart_top + 18.0, 'identity', 'tiny', 'end'))

    grouped: dict[int, list[SweepRow]] = defaultdict(list)
    for row in rows:
        grouped[row.samples_per_symbol].append(row)
    for samples_per_symbol in SPS_VALUES:
        series = sorted(grouped[samples_per_symbol], key=lambda row: row.normalized_cfo)
        for segment in segmented_points(series):
            points = [
                (
                    axis_x(row.normalized_cfo, chart_left, chart_width, maximum),
                    axis_y(row.estimated_normalized_cfo, chart_top, chart_height, maximum),
                )
                for row in segment
            ]
            svg.append(polyline(points, colors[samples_per_symbol], 3.0))
        legend_y = chart_top + 18.0 + (samples_per_symbol - 1) * 26.0
        svg.append(circle(chart_left + 20.0, legend_y - 4.0, 6.0, colors[samples_per_symbol]))
        svg.append(text(chart_left + 36.0, legend_y, f'{samples_per_symbol} sample/symbol', 'tiny'))

        limit = alias_limit_normalized(samples_per_symbol)
        x_limit = axis_x(limit, chart_left, chart_width, maximum)
        svg.append(line(x_limit, chart_top + 10.0, x_limit, chart_top + chart_height, colors[samples_per_symbol], 1.6, 0.55, '5 6'))

    example_rows = {row.samples_per_symbol: row for row in rows if abs(row.normalized_cfo - EXAMPLE_CFO) < 1e-9}
    card_x = left + 776.0
    card_y = top + 146.0
    svg.append(rounded_rect(card_x, card_y, 282.0, 176.0, '#0f1b29', '#44637d', 1.8, 1.0, 14.0))
    svg.append(text(card_x + 18.0, card_y + 30.0, 'Same CFO, different read', 'label'))
    svg.append(text(card_x + 18.0, card_y + 58.0, f'true Δf / R_s = {EXAMPLE_CFO:.2f}', 'micro'))
    for idx, samples_per_symbol in enumerate((1, 4)):
        row = example_rows[samples_per_symbol]
        y = card_y + 90.0 + idx * 34.0
        svg.append(circle(card_x + 20.0, y - 4.0, 5.5, colors[samples_per_symbol]))
        svg.append(text(card_x + 34.0, y, f'{samples_per_symbol} sps estimate', 'tiny'))
        svg.append(text(card_x + 250.0, y, f'{row.estimated_normalized_cfo:.3f} R_s', 'tiny', 'end'))

    summary_y = top + 512.0
    svg.append(rounded_rect(left + 24.0, summary_y, 1032.0, 80.0, '#13263b', '#4f8cc9', 1.6, 1.0, 14.0))
    add_wrapped_text(
        svg,
        left + 44.0,
        summary_y + 30.0,
        'At Δf / R_s = 0.30, the symbol-rate estimator folds to about 0.05 R_s, while the 4 sps version still returns the right coarse answer. The dashed vertical markers show where each observation rate hits its own honest limit.',
        'tiny',
        max_width=992.0,
        font_size=14.0,
        line_height=18.0,
    )


def pipeline_panel(svg: list[str]) -> None:
    left = 60.0
    top = 1188.0
    width = 1080.0
    height = 514.0
    box_w = 294.0
    box_h = 228.0

    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0, 1.0, 18.0))
    svg.append(text(left + 24.0, top + 34.0, '3. Three honest branches once the symbol-rate view runs out of room', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 64.0,
        'The point is not to inflate this repo into a full modem survey. It is to mark where the current symbol-rate packet ends and which front ends belong earlier in the chain.',
        'small',
        max_width=1000.0,
        font_size=15.0,
        line_height=20.0,
    )

    columns = [
        (
            left + 34.0,
            '#3a1018',
            '#fda4af',
            'Symbol-rate QPSK note',
            'use when',
            'timing is already solved and |Δf| / R_s stays inside about 0.125',
            ['4th-power coarse estimate', 'Costas loop near lock', 'ambiguity fix after that'],
        ),
        (
            left + 393.0,
            '#11263d',
            '#93c5fd',
            'Oversampled waveform front end',
            'use when',
            'you still want a non-data-aided path, but the absolute CFO is too large for the 1 sps view',
            ['4th-power before decimation', 'band-edge FLL if pulse-shape structure helps', 'then hand off to timing and fine tracking'],
        ),
        (
            left + 752.0,
            '#142f23',
            '#4ade80',
            'Pilot or correlation coarse recovery',
            'use when',
            'the packet format can spend known structure to get a stronger early estimate',
            ['preamble-based CFO estimate', 'correlation or pilot locking', 'then normal timing and carrier cleanup'],
        ),
    ]

    for x, fill, stroke, title_text, kicker, body, bullets in columns:
        svg.append(rounded_rect(x, top + 118.0, box_w, box_h, fill, stroke, 1.8, 1.0, 16.0))
        svg.append(text(x + 18.0, top + 148.0, title_text, 'label'))
        svg.append(text(x + 18.0, top + 178.0, kicker, 'micro'))
        add_wrapped_text(
            svg,
            x + 18.0,
            top + 202.0,
            body,
            'tiny',
            max_width=box_w - 36.0,
            font_size=14.0,
            line_height=18.0,
        )
        bullet_y = top + 254.0
        for bullet in bullets:
            svg.append(circle(x + 22.0, bullet_y - 4.0, 3.5, stroke))
            add_wrapped_text(
                svg,
                x + 34.0,
                bullet_y,
                bullet,
                'tiny',
                max_width=box_w - 54.0,
                font_size=14.0,
                line_height=18.0,
            )
            bullet_y += 30.0

    svg.append(line(left + 328.0, top + 222.0, left + 393.0, top + 222.0, '#5d7fa3', 2.4, 1.0, '7 7'))
    svg.append(line(left + 687.0, top + 222.0, left + 752.0, top + 222.0, '#5d7fa3', 2.4, 1.0, '7 7'))

    add_wrapped_text(
        svg,
        left + 24.0,
        top + 376.0,
        'Minimal public reading: the old alias cliff note was never “carrier recovery in general.” It was a bounded symbol-rate card. Once the CFO gets bigger, the receiver needs an earlier front end, not a louder claim about the same late-stage estimator.',
        'small',
        max_width=1000.0,
        font_size=15.0,
        line_height=20.0,
    )
    svg.append(text(left + 24.0, top + 458.0, 'Source rows exported to assets/2026-05-19-large-cfo-front-end-boundary.csv', 'tiny'))


def main() -> None:
    rows = sweep_normalized_cfo(SPS_VALUES, NORMALIZED_CFO_VALUES, symbol_count=192, noise_std=0.012, seed=19)
    write_csv(rows, CSV_OUT)

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
        '  </style>',
        '</defs>',
        rounded_rect(0.0, 0.0, WIDTH, HEIGHT, 'url(#bg)', None, 0.0, 1.0, 0.0),
        '<g transform="translate(290 0)">',
        text(58.0, 60.0, 'When the symbol-rate carrier-recovery story stops being enough', 'title'),
        text_block(
            58.0,
            92.0,
            [
                'The π/4 alias note was always a 1-sample/symbol QPSK card.',
                'This follow-up shows why the honest CFO window scales with observation rate,',
                'and which front ends belong earlier once the symbol-rate view runs out of room.',
            ],
            'subtitle',
            24.0,
        ),
    ]

    capture_window_panel(svg)
    sweep_panel(svg, rows)
    pipeline_panel(svg)

    svg.append('</g>')
    svg.append('</svg>')
    SVG_OUT.parent.mkdir(parents=True, exist_ok=True)
    SVG_OUT.write_text('\n'.join(svg) + '\n')
    export_png_from_svg(SVG_OUT, PNG_OUT, size=1900, dpi=300)

    print(f'WROTE {SVG_OUT}')
    print(f'WROTE {PNG_OUT}')
    print(f'WROTE {CSV_OUT}')


if __name__ == '__main__':
    main()
