#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from svg_layout import add_wrapped_text, export_png_from_svg, svg_root, text
from waveform_carrier_front_ends import FrontEndSweepRow, alias_limit_normalized, sweep_front_ends, write_csv

REPO = Path(__file__).resolve().parents[1]
SVG_OUT = REPO / 'assets/2026-05-19-oversampled-fourth-power-vs-band-edge-fll.svg'
PNG_OUT = REPO / 'assets/2026-05-19-oversampled-fourth-power-vs-band-edge-fll.png'
CSV_OUT = REPO / 'assets/2026-05-19-oversampled-fourth-power-vs-band-edge-fll.csv'

WIDTH = 1900
HEIGHT = 1880
SAMPLES_PER_SYMBOL = 4
ROLLOFFS = [0.05, 0.20, 0.35, 0.50]
NORMALIZED_CFO_VALUES = [round(-0.55 + idx * 0.025, 3) for idx in range(45)]
FOURTH_POWER_LIMIT = alias_limit_normalized(SAMPLES_PER_SYMBOL)
COLORS = {
    0.05: '#fda4af',
    0.20: '#93c5fd',
    0.35: '#facc15',
    0.50: '#4ade80',
}


def line(x1: float, y1: float, x2: float, y2: float, stroke: str, width: float = 2.0, opacity: float = 1.0, dash: str | None = None) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}" stroke-linecap="round"{dash_attr}/>'


def rounded_rect(x: float, y: float, w: float, h: float, fill: str, stroke: str | None = None, stroke_width: float = 0.0, opacity: float = 1.0, rx: float = 18.0) -> str:
    stroke_attr = '' if stroke is None else f' stroke="{stroke}" stroke-width="{stroke_width:.1f}"'
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}" fill="{fill}" opacity="{opacity}"{stroke_attr}/>'


def circle(x: float, y: float, r: float, fill: str, opacity: float = 1.0) -> str:
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" opacity="{opacity}"/>'


def polyline(points: list[tuple[float, float]], stroke: str, width: float = 3.0, opacity: float = 1.0) -> str:
    coords = ' '.join(f'{x:.1f},{y:.1f}' for x, y in points)
    return f'<polyline points="{coords}" fill="none" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}" stroke-linecap="round" stroke-linejoin="round"/>'


def axis_x(value: float, left: float, width: float, minimum: float, maximum: float) -> float:
    return left + width * ((value - minimum) / (maximum - minimum))


def axis_y(value: float, top: float, height: float, minimum: float, maximum: float) -> float:
    return top + height - height * ((value - minimum) / (maximum - minimum))


def grouped_rows(rows: list[FrontEndSweepRow]) -> dict[float, list[FrontEndSweepRow]]:
    grouped: dict[float, list[FrontEndSweepRow]] = defaultdict(list)
    for row in rows:
        grouped[row.rolloff].append(row)
    return {rolloff: sorted(series, key=lambda row: row.normalized_cfo) for rolloff, series in grouped.items()}


def top_panel(svg: list[str], rows: list[FrontEndSweepRow]) -> None:
    left = 60.0
    top = 160.0
    width = 1780.0
    height = 340.0
    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 26.0, top + 40.0, 'Two coarse front ends, two different contracts', 'label'))
    add_wrapped_text(
        svg,
        left + 26.0,
        top + 72.0,
        'Both of these belong before late-stage Costas tracking. Oversampled 4th-power recovery still uses PSK symmetry. Band-edge logic uses excess-bandwidth asymmetry in the pulse-shaped waveform instead.',
        'small',
        max_width=1700.0,
        font_size=16.0,
        line_height=21.0,
    )

    cards = [
        (
            left + 28.0,
            '#3a1018',
            '#fda4af',
            'Oversampled 4th-power',
            'needs',
            'PSK rotational symmetry and enough sample rate before decimation',
            'The roll-off sweep barely moves the estimate while the CFO stays inside the 4 sps alias limit.',
        ),
        (
            left + 616.0,
            '#11263d',
            '#93c5fd',
            'Band-edge discriminator',
            'needs',
            'excess bandwidth, oversampling, and a pulse shape with visible band edges',
            'The same CFO produces a much stronger clue as roll-off grows, because the edge energy itself grows.',
        ),
        (
            left + 1204.0,
            '#142f23',
            '#4ade80',
            'Known-structure branch',
            'keep named',
            'preamble, pilots, or correlation targets',
            'Real and often stronger in packet systems, but outside this bounded blind-front-end comparison.',
        ),
    ]
    for card_left, fill, stroke, title_text, kicker, body, summary in cards:
        svg.append(rounded_rect(card_left, top + 120.0, 548.0, 184.0, fill, stroke, 1.8, 1.0, 16.0))
        svg.append(text(card_left + 18.0, top + 150.0, title_text, 'label'))
        svg.append(text(card_left + 18.0, top + 178.0, kicker, 'micro'))
        add_wrapped_text(svg, card_left + 18.0, top + 206.0, body, 'tiny', max_width=510.0, font_size=14.0, line_height=18.0)
        add_wrapped_text(svg, card_left + 18.0, top + 252.0, summary, 'tiny', max_width=510.0, font_size=14.0, line_height=18.0)



def fourth_power_panel(svg: list[str], rows: list[FrontEndSweepRow]) -> None:
    left = 60.0
    top = 548.0
    width = 870.0
    height = 640.0
    chart_left = left + 96.0
    chart_top = top + 118.0
    chart_width = 694.0
    chart_height = 398.0
    minimum = -0.55
    maximum = 0.55

    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 24.0, top + 36.0, '1. Oversampled 4th-power stays mostly indifferent to roll-off', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 68.0,
        'All four SRRC waveforms use 4 samples per symbol. Inside the ±0.50 R_s alias window, the 4th-power estimate stays close to the identity line across the whole roll-off sweep.',
        'small',
        max_width=808.0,
        font_size=15.0,
        line_height=20.0,
    )

    svg.append(line(chart_left, chart_top + chart_height, chart_left + chart_width, chart_top + chart_height, '#5d7fa3', 2.2))
    svg.append(line(chart_left, chart_top, chart_left, chart_top + chart_height, '#5d7fa3', 2.2))
    for tick in range(-5, 6):
        value = tick * 0.1
        x = axis_x(value, chart_left, chart_width, minimum, maximum)
        y = axis_y(value, chart_top, chart_height, minimum, maximum)
        svg.append(line(x, chart_top + chart_height - 6.0, x, chart_top + chart_height + 6.0, '#5d7fa3', 1.5))
        svg.append(text(x, chart_top + chart_height + 26.0, f'{value:+.1f}', 'tiny', 'middle'))
        svg.append(line(chart_left - 6.0, y, chart_left + 6.0, y, '#5d7fa3', 1.5))
        svg.append(text(chart_left - 18.0, y + 4.0, f'{value:+.1f}', 'tiny', 'end'))
        if tick not in (-5, 5):
            svg.append(line(x, chart_top, x, chart_top + chart_height, '#27415a', 1.0, 0.8, '4 8'))
            svg.append(line(chart_left, y, chart_left + chart_width, y, '#27415a', 1.0, 0.8, '4 8'))

    identity = [
        (axis_x(value, chart_left, chart_width, minimum, maximum), axis_y(value, chart_top, chart_height, minimum, maximum))
        for value in (minimum, -0.3, -0.1, 0.1, 0.3, maximum)
    ]
    svg.append(polyline(identity, '#dce7f3', 2.2, 0.95))
    svg.append(text(chart_left + chart_width - 10.0, chart_top + 18.0, 'identity', 'tiny', 'end'))

    limit_left = axis_x(-FOURTH_POWER_LIMIT, chart_left, chart_width, minimum, maximum)
    limit_right = axis_x(FOURTH_POWER_LIMIT, chart_left, chart_width, minimum, maximum)
    svg.append(line(limit_left, chart_top, limit_left, chart_top + chart_height, '#f59e0b', 2.0, 0.8, '7 7'))
    svg.append(line(limit_right, chart_top, limit_right, chart_top + chart_height, '#f59e0b', 2.0, 0.8, '7 7'))
    svg.append(text(limit_left, chart_top + 18.0, '-0.50', 'tiny', 'middle'))
    svg.append(text(limit_right, chart_top + 18.0, '+0.50', 'tiny', 'middle'))

    for rolloff, series in grouped_rows(rows).items():
        points = [
            (axis_x(row.normalized_cfo, chart_left, chart_width, minimum, maximum), axis_y(row.fourth_power_estimate, chart_top, chart_height, minimum, maximum))
            for row in series
        ]
        svg.append(polyline(points, COLORS[rolloff], 3.0))

    legend_left = left + 582.0
    legend_top = top + 540.0
    svg.append(rounded_rect(legend_left, legend_top, 248.0, 72.0, '#13263b', '#4f8cc9', 1.4, 1.0, 12.0))
    for idx, rolloff in enumerate(ROLLOFFS):
        y = legend_top + 24.0 + idx * 14.0
        svg.append(circle(legend_left + 18.0, y - 4.0, 5.0, COLORS[rolloff]))
        svg.append(text(legend_left + 32.0, y, f'SRRC α = {rolloff:.2f}', 'tiny'))

    svg.append(text(chart_left + chart_width / 2.0, chart_top + chart_height + 60.0, 'true normalized CFO  Δf / R_s', 'tiny', 'middle'))
    svg.append(text(chart_left - 62.0, chart_top + chart_height / 2.0, '4th-power estimate', 'tiny', 'middle'))

    honest_rows = [row for row in rows if abs(row.normalized_cfo) <= FOURTH_POWER_LIMIT]
    worst_honest_error = max(row.fourth_power_absolute_error for row in honest_rows)
    summary = rounded_rect(left + 22.0, top + 540.0, 520.0, 72.0, '#13263b', '#4f8cc9', 1.4, 1.0, 12.0)
    svg.append(summary)
    add_wrapped_text(
        svg,
        left + 42.0,
        top + 570.0,
        f'Worst absolute 4th-power error inside the 4 sps alias window is only {worst_honest_error:.3f} R_s in this sweep. The curves nearly sit on top of one another.',
        'tiny',
        max_width=476.0,
        font_size=13.5,
        line_height=17.0,
    )


def band_edge_panel(svg: list[str], rows: list[FrontEndSweepRow]) -> None:
    left = 970.0
    top = 548.0
    width = 870.0
    height = 640.0
    chart_left = left + 96.0
    chart_top = top + 118.0
    chart_width = 694.0
    chart_height = 398.0
    x_min = -0.12
    x_max = 0.12
    y_min = -0.085
    y_max = 0.085

    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 24.0, top + 36.0, '2. Band-edge clue needs roll-off', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 68.0,
        'This panel keeps the same 4 sps waveform but reads a bounded band-edge imbalance instead of a symmetry-based CFO estimate. Higher roll-off gives the discriminator more edge energy to work with.',
        'small',
        max_width=808.0,
        font_size=15.0,
        line_height=20.0,
    )

    svg.append(line(chart_left, chart_top + chart_height, chart_left + chart_width, chart_top + chart_height, '#5d7fa3', 2.2))
    svg.append(line(chart_left, chart_top, chart_left, chart_top + chart_height, '#5d7fa3', 2.2))
    for tick in range(-6, 7):
        value = tick * 0.02
        x = axis_x(value, chart_left, chart_width, x_min, x_max)
        svg.append(line(x, chart_top + chart_height - 6.0, x, chart_top + chart_height + 6.0, '#5d7fa3', 1.5))
        svg.append(text(x, chart_top + chart_height + 26.0, f'{value:+.02f}', 'tiny', 'middle'))
        if tick not in (-6, 6):
            svg.append(line(x, chart_top, x, chart_top + chart_height, '#27415a', 1.0, 0.8, '4 8'))
    for tick in range(-8, 9):
        value = tick * 0.01
        y = axis_y(value, chart_top, chart_height, y_min, y_max)
        if y < chart_top or y > chart_top + chart_height:
            continue
        svg.append(line(chart_left - 6.0, y, chart_left + 6.0, y, '#5d7fa3', 1.5))
        svg.append(text(chart_left - 18.0, y + 4.0, f'{value:+.02f}', 'tiny', 'end'))
        if tick not in (-8, 8):
            svg.append(line(chart_left, y, chart_left + chart_width, y, '#27415a', 1.0, 0.8, '4 8'))

    zero_y = axis_y(0.0, chart_top, chart_height, y_min, y_max)
    svg.append(line(chart_left, zero_y, chart_left + chart_width, zero_y, '#dce7f3', 1.8, 0.9, '8 8'))
    svg.append(text(chart_left + chart_width - 10.0, zero_y - 10.0, 'zero imbalance', 'tiny', 'end'))

    for rolloff, series in grouped_rows(rows).items():
        clipped = [row for row in series if x_min <= row.normalized_cfo <= x_max]
        points = [
            (axis_x(row.normalized_cfo, chart_left, chart_width, x_min, x_max), axis_y(row.band_edge_imbalance, chart_top, chart_height, y_min, y_max))
            for row in clipped
        ]
        svg.append(polyline(points, COLORS[rolloff], 3.0))

    svg.append(text(chart_left + chart_width / 2.0, chart_top + chart_height + 60.0, 'true normalized CFO  Δf / R_s', 'tiny', 'middle'))
    svg.append(text(chart_left - 74.0, chart_top + chart_height / 2.0, 'band-edge imbalance', 'tiny', 'middle'))

    legend_left = left + 594.0
    legend_top = top + 540.0
    svg.append(rounded_rect(legend_left, legend_top, 236.0, 72.0, '#13263b', '#4f8cc9', 1.4, 1.0, 12.0))
    for idx, rolloff in enumerate(ROLLOFFS):
        y = legend_top + 24.0 + idx * 14.0
        svg.append(circle(legend_left + 18.0, y - 4.0, 5.0, COLORS[rolloff]))
        svg.append(text(legend_left + 32.0, y, f'SRRC α = {rolloff:.2f}', 'tiny'))

    point_rows = {row.rolloff: row for row in rows if abs(row.normalized_cfo - 0.1) < 1.0e-9}
    slope_card = rounded_rect(left + 22.0, top + 540.0, 530.0, 72.0, '#13263b', '#4f8cc9', 1.4, 1.0, 12.0)
    svg.append(slope_card)
    add_wrapped_text(
        svg,
        left + 42.0,
        top + 570.0,
        f'At Δf / R_s = 0.10, the imbalance grows from {point_rows[0.05].band_edge_imbalance:.003f} at α = 0.05 to {point_rows[0.50].band_edge_imbalance:.003f} at α = 0.50. That extra slope is exactly what excess bandwidth buys.',
        'tiny',
        max_width=486.0,
        font_size=13.5,
        line_height=17.0,
    )


def bottom_panel(svg: list[str]) -> None:
    left = 60.0
    top = 1232.0
    width = 1780.0
    height = 564.0
    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 24.0, top + 36.0, '3. The comparison is about assumptions, not algorithm prestige', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 68.0,
        'A clean receiver note should say which clue the front end is exploiting. This pass stays small on purpose: same 4 sps waveform, same CFO sweep, then one symmetry-based view and one band-edge view.',
        'small',
        max_width=1580.0,
        font_size=15.0,
        line_height=20.0,
    )

    columns = [
        (
            left + 28.0,
            '#14263a',
            '#93c5fd',
            'When oversampled 4th-power is cleaner',
            [
                'pilot-free PSK is still the point',
                'you want continuity with the existing alias-cliff notes',
                'the receiver can estimate before decimation',
                'excess bandwidth is not the main teaching object',
            ],
        ),
        (
            left + 616.0,
            '#173126',
            '#4ade80',
            'When band-edge logic is cleaner',
            [
                'the waveform is oversampled and pulse-shaped',
                'roll-off is real and worth exploiting',
                'symbol decisions are still too early to trust',
                'you want a waveform-domain coarse clue, not a symbol-rate one',
            ],
        ),
        (
            left + 1204.0,
            '#341c12',
            '#facc15',
            'What this sidecar does not try to claim',
            [
                'it does not rank every coarse-carrier front end',
                'it does not replace pilot or preamble methods',
                'it does not model adjacent-channel leakage or a full loop',
                'it only shows why the two blind branches depend on different information',
            ],
        ),
    ]
    for column_left, fill, stroke, title_text, bullets in columns:
        svg.append(rounded_rect(column_left, top + 120.0, 548.0, 296.0, fill, stroke, 1.8, 1.0, 16.0))
        svg.append(text(column_left + 18.0, top + 150.0, title_text, 'label'))
        for idx, bullet in enumerate(bullets):
            y = top + 188.0 + idx * 54.0
            svg.append(circle(column_left + 20.0, y - 4.0, 4.5, stroke))
            add_wrapped_text(svg, column_left + 36.0, y, bullet, 'tiny', max_width=486.0, font_size=14.0, line_height=18.0)

    footer = rounded_rect(left + 24.0, top + 452.0, 1732.0, 82.0, '#13263b', '#4f8cc9', 1.6, 1.0, 14.0)
    svg.append(footer)
    add_wrapped_text(
        svg,
        left + 46.0,
        top + 484.0,
        'Bottom line: oversampled 4th-power and band-edge FLL are not interchangeable coarse loops. One exploits constellation symmetry. The other exploits excess-bandwidth asymmetry. The better front end depends on which clue the receiver can trust.',
        'small',
        max_width=1560.0,
        font_size=15.0,
        line_height=19.0,
    )


def build_svg(rows: list[FrontEndSweepRow]) -> str:
    svg: list[str] = [
        svg_root(WIDTH, HEIGHT),
        '<defs><style>'
        '.title { fill: #e6eef8; font: 700 38px Arial, sans-serif; }'
        '.subtitle { fill: #c8d8ea; font: 400 20px Arial, sans-serif; }'
        '.label { fill: #eef4fb; font: 700 24px Arial, sans-serif; }'
        '.small { fill: #d4e1ef; font: 400 17px Arial, sans-serif; }'
        '.micro { fill: #9ac7ff; font: 700 15px Arial, sans-serif; }'
        '.tiny { fill: #d8e4f0; font: 400 14px Arial, sans-serif; }'
        '</style></defs>',
        '<rect width="100%" height="100%" fill="#08111c"/>',
        text(60.0, 72.0, 'Oversampled 4th-power versus band-edge FLL', 'title'),
        text(60.0, 108.0, 'Same pulse-shaped QPSK waveform, same CFO sweep, two different coarse-carrier clues before late-stage tracking.', 'subtitle'),
    ]
    top_panel(svg, rows)
    fourth_power_panel(svg, rows)
    band_edge_panel(svg, rows)
    bottom_panel(svg)
    svg.append('</svg>')
    return '\n'.join(svg) + '\n'


def main() -> None:
    rows = sweep_front_ends(ROLLOFFS, NORMALIZED_CFO_VALUES, samples_per_symbol=SAMPLES_PER_SYMBOL, symbol_count=256, span_symbols=8, seed=19)
    write_csv(rows, CSV_OUT)
    SVG_OUT.write_text(build_svg(rows))
    export_png_from_svg(SVG_OUT, PNG_OUT, size=2200)
    print(f'wrote {SVG_OUT.relative_to(REPO)}')
    print(f'wrote {PNG_OUT.relative_to(REPO)}')
    print(f'wrote {CSV_OUT.relative_to(REPO)}')


if __name__ == '__main__':
    main()
