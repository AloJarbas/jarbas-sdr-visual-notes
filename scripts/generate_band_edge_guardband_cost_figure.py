#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from svg_layout import add_wrapped_text, export_png_from_svg, svg_root, text
from waveform_carrier_front_ends import (
    BandEdgeGuardbandCostRow,
    sweep_band_edge_guardband_cost_comparison,
    write_band_edge_guardband_cost_csv,
)

REPO = Path(__file__).resolve().parents[1]
SVG_OUT = REPO / 'assets/2026-05-22-band-edge-guardband-cost-comparison.svg'
PNG_OUT = REPO / 'assets/2026-05-22-band-edge-guardband-cost-comparison.png'
CSV_OUT = REPO / 'assets/2026-05-22-band-edge-guardband-cost-comparison.csv'

WIDTH = 2140
HEIGHT = 1660
SAMPLES_PER_SYMBOL = 4
SYMBOL_COUNT = 1024
SEED = 19
TRIM = 160
ROLLOFFS = [0.05, 0.20, 0.35, 0.50]
TAP_COUNTS = [63, 127, 255]
CHANNEL_SPACINGS = [0.55 + 0.05 * idx for idx in range(24)]
REFERENCE_SPACING = 1.0
CAPTURE_THRESHOLD = 0.05
COLORS = {
    63: '#fda4af',
    127: '#93c5fd',
    255: '#4ade80',
}
DESIGN_LABELS = {
    'proxy_bandpass': 'Current proxy bandpass',
    'gnuradio_half_sine': 'GNU Radio / half-sine style',
}
DESIGN_DASH = {
    'proxy_bandpass': None,
    'gnuradio_half_sine': '10 8',
}


def line(x1: float, y1: float, x2: float, y2: float, stroke: str, width: float = 2.0, opacity: float = 1.0, dash: str | None = None) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}" stroke-linecap="round"{dash_attr}/>'


def rounded_rect(x: float, y: float, w: float, h: float, fill: str, stroke: str | None = None, stroke_width: float = 0.0, opacity: float = 1.0, rx: float = 18.0) -> str:
    stroke_attr = '' if stroke is None else f' stroke="{stroke}" stroke-width="{stroke_width:.1f}"'
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}" fill="{fill}" opacity="{opacity}"{stroke_attr}/>'


def circle(x: float, y: float, r: float, fill: str, opacity: float = 1.0) -> str:
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" opacity="{opacity}"/>'


def square(x: float, y: float, size: float, fill: str, opacity: float = 1.0) -> str:
    half = size / 2.0
    return f'<rect x="{x - half:.1f}" y="{y - half:.1f}" width="{size:.1f}" height="{size:.1f}" fill="{fill}" opacity="{opacity}" rx="1.5"/>'


def polyline(points: list[tuple[float, float]], stroke: str, width: float = 3.0, opacity: float = 1.0, dash: str | None = None) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ''
    coords = ' '.join(f'{x:.1f},{y:.1f}' for x, y in points)
    return f'<polyline points="{coords}" fill="none" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}" stroke-linecap="round" stroke-linejoin="round"{dash_attr}/>'


def axis_x(value: float, left: float, width: float, minimum: float, maximum: float) -> float:
    return left + width * ((value - minimum) / (maximum - minimum))


def axis_y(value: float, top: float, height: float, minimum: float, maximum: float) -> float:
    return top + height - height * ((value - minimum) / (maximum - minimum))


def row_lookup(rows: list[BandEdgeGuardbandCostRow]) -> dict[tuple[str, int, float], BandEdgeGuardbandCostRow]:
    return {(row.design, row.tap_count, row.rolloff): row for row in rows}


def grouped_rows(rows: list[BandEdgeGuardbandCostRow]) -> dict[str, dict[int, list[BandEdgeGuardbandCostRow]]]:
    grouped: dict[str, dict[int, list[BandEdgeGuardbandCostRow]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[row.design][row.tap_count].append(row)
    return {
        design: {tap_count: sorted(series, key=lambda item: item.rolloff) for tap_count, series in tap_map.items()}
        for design, tap_map in grouped.items()
    }


def draw_chart_frame(svg: list[str], *, left: float, top: float, width: float, height: float, x_min: float, x_max: float, y_min: float, y_max: float, x_ticks: list[float], y_ticks: list[float], x_label: str, y_label: str) -> None:
    svg.append(line(left, top + height, left + width, top + height, '#5d7fa3', 2.2))
    svg.append(line(left, top, left, top + height, '#5d7fa3', 2.2))
    for value in x_ticks:
        x = axis_x(value, left, width, x_min, x_max)
        svg.append(line(x, top + height - 6.0, x, top + height + 6.0, '#5d7fa3', 1.4))
        svg.append(text(x, top + height + 26.0, f'{value:.2f}', 'tiny', 'middle'))
        if value not in (x_ticks[0], x_ticks[-1]):
            svg.append(line(x, top, x, top + height, '#27415a', 1.0, 0.8, '4 8'))
    for value in y_ticks:
        y = axis_y(value, top, height, y_min, y_max)
        svg.append(line(left - 6.0, y, left + 6.0, y, '#5d7fa3', 1.4))
        label = f'{value:.2f}' if y_max <= 2.0 else f'{value:.0f}%'
        svg.append(text(left - 18.0, y + 4.0, label, 'tiny', 'end'))
        if value not in (y_ticks[0], y_ticks[-1]):
            svg.append(line(left, y, left + width, y, '#27415a', 1.0, 0.8, '4 8'))
    svg.append(text(left + width / 2.0, top + height + 58.0, x_label, 'tiny', 'middle'))
    svg.append(text(left + 4.0, top - 12.0, y_label, 'tiny'))


def metric_panel(
    svg: list[str],
    rows: list[BandEdgeGuardbandCostRow],
    *,
    left: float,
    top: float,
    width: float,
    height: float,
    title_text: str,
    body: str,
    y_min: float,
    y_max: float,
    y_ticks: list[float],
    y_label: str,
    value_getter,
    value_formatter,
) -> None:
    chart_left = left + 102.0
    chart_top = top + 126.0
    chart_width = width - 166.0
    chart_height = 352.0
    grouped = grouped_rows(rows)

    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 24.0, top + 36.0, title_text, 'label'))
    add_wrapped_text(svg, left + 24.0, top + 70.0, body, 'small', max_width=width - 110.0, font_size=15.0, line_height=20.0)

    draw_chart_frame(
        svg,
        left=chart_left,
        top=chart_top,
        width=chart_width,
        height=chart_height,
        x_min=0.05,
        x_max=0.50,
        y_min=y_min,
        y_max=y_max,
        x_ticks=ROLLOFFS,
        y_ticks=y_ticks,
        x_label='SRRC roll-off  α',
        y_label=y_label,
    )

    for design, tap_map in grouped.items():
        for tap_count, series in tap_map.items():
            points = [
                (
                    axis_x(row.rolloff, chart_left, chart_width, 0.05, 0.50),
                    axis_y(value_getter(row), chart_top, chart_height, y_min, y_max),
                )
                for row in series
            ]
            svg.append(polyline(points, COLORS[tap_count], 3.0, 1.0, DESIGN_DASH[design]))
            for x, y in points:
                if design == 'proxy_bandpass':
                    svg.append(circle(x, y, 5.0, COLORS[tap_count]))
                else:
                    svg.append(square(x, y, 9.0, COLORS[tap_count]))

    legend_left = left + 24.0
    legend_top = top + 516.0
    svg.append(rounded_rect(legend_left, legend_top, 356.0, 110.0, '#13263b', '#4f8cc9', 1.4, 1.0, 12.0))
    for idx, tap_count in enumerate(TAP_COUNTS):
        y = legend_top + 26.0 + idx * 18.0
        svg.append(circle(legend_left + 18.0, y - 4.0, 5.0, COLORS[tap_count]))
        svg.append(text(legend_left + 32.0, y, f'{tap_count}-tap filters', 'tiny'))
    style_y = legend_top + 86.0
    svg.append(line(legend_left + 190.0, style_y - 6.0, legend_left + 238.0, style_y - 6.0, '#dbeafe', 2.6))
    svg.append(circle(legend_left + 214.0, style_y - 6.0, 4.5, '#dbeafe'))
    svg.append(text(legend_left + 248.0, style_y - 2.0, DESIGN_LABELS['proxy_bandpass'], 'tiny'))
    svg.append(line(legend_left + 190.0, style_y + 14.0, legend_left + 238.0, style_y + 14.0, '#dbeafe', 2.6, 1.0, DESIGN_DASH['gnuradio_half_sine']))
    svg.append(square(legend_left + 214.0, style_y + 14.0, 8.0, '#dbeafe'))
    svg.append(text(legend_left + 248.0, style_y + 18.0, DESIGN_LABELS['gnuradio_half_sine'], 'tiny'))

    lookup = row_lookup(rows)
    key = ('gnuradio_half_sine', 63, 0.35)
    value = value_getter(lookup[key])
    svg.append(text(left + width - 18.0, legend_top + 28.0, value_formatter(value), 'tiny', 'end'))


def top_panel(svg: list[str], rows: list[BandEdgeGuardbandCostRow]) -> None:
    left = 60.0
    top = 146.0
    width = 2020.0
    height = 314.0
    lookup = row_lookup(rows)

    proxy_020 = lookup[('proxy_bandpass', 63, 0.20)]
    half_020 = lookup[('gnuradio_half_sine', 63, 0.20)]
    proxy_035 = lookup[('proxy_bandpass', 63, 0.35)]
    half_035 = lookup[('gnuradio_half_sine', 63, 0.35)]
    proxy_035_long = lookup[('proxy_bandpass', 255, 0.35)]
    half_035_long = lookup[('gnuradio_half_sine', 255, 0.35)]

    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 26.0, top + 42.0, 'The next band-edge question was the cost of the wider half-sine design', 'label'))
    add_wrapped_text(
        svg,
        left + 26.0,
        top + 78.0,
        'The previous note closed the slope loophole: the GNU Radio / fred harris half-sine construction gets much closer to the normalized near-lock target than the old proxy. This pass checks the price of that fix by measuring how much adjacent-channel energy the band-edge filters keep capturing and how much center spacing is needed before that pickup falls below 5%.',
        'small',
        max_width=1940.0,
        font_size=16.0,
        line_height=21.0,
    )

    cards = [
        (
            left + 28.0,
            '#3a1018',
            '#fda4af',
            'α = 0.20, 63 taps: sharper slope is much less selective',
            f'Proxy slope {proxy_020.central_slope_wrt_deltaf_over_Rs:.3f} needs {proxy_020.spacing_for_capture_below_threshold:.2f} R_s for ≤5% pickup. Half-sine slope {half_020.central_slope_wrt_deltaf_over_Rs:.3f} needs {half_020.spacing_for_capture_below_threshold:.2f} R_s.',
        ),
        (
            left + 690.0,
            '#11263d',
            '#93c5fd',
            'α = 0.35, 63 taps: the tradeoff stays real',
            f'At 1.0 R_s spacing, proxy pickup is {proxy_035.adjacent_capture_at_reference_spacing:.1%}. Half-sine pickup is {half_035.adjacent_capture_at_reference_spacing:.1%}. The slope fix is real, and so is the spill cost.',
        ),
        (
            left + 1352.0,
            '#142f23',
            '#4ade80',
            'Tap count mostly moves slope, not spacing threshold',
            f'At α = 0.35 the proxy rises from slope {proxy_035.central_slope_wrt_deltaf_over_Rs:.3f} to {proxy_035_long.central_slope_wrt_deltaf_over_Rs:.3f}, but the ≤5% spacing stays {proxy_035.spacing_for_capture_below_threshold:.2f} → {proxy_035_long.spacing_for_capture_below_threshold:.2f} R_s. Half-sine stays {half_035.spacing_for_capture_below_threshold:.2f} → {half_035_long.spacing_for_capture_below_threshold:.2f} R_s too.',
        ),
    ]
    for card_left, fill, stroke, title_text, body in cards:
        svg.append(rounded_rect(card_left, top + 156.0, 640.0, 126.0, fill, stroke, 1.8, 1.0, 16.0))
        svg.append(text(card_left + 18.0, top + 186.0, title_text, 'label'))
        add_wrapped_text(svg, card_left + 18.0, top + 214.0, body, 'tiny', max_width=584.0, font_size=14.0, line_height=18.0)


def bottom_panel(svg: list[str], rows: list[BandEdgeGuardbandCostRow]) -> None:
    left = 60.0
    top = 1322.0
    width = 2020.0
    height = 270.0
    lookup = row_lookup(rows)
    proxy = lookup[('proxy_bandpass', 63, 0.35)]
    half = lookup[('gnuradio_half_sine', 63, 0.35)]
    ratio = half.adjacent_capture_at_reference_spacing / max(proxy.adjacent_capture_at_reference_spacing, 1.0e-9)

    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 24.0, top + 36.0, 'What this changes in the repo', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 72.0,
        'The repo can now stop treating the half-sine upgrade as a free correction. It is a real implementation fix for moderate-roll-off slope, but it also keeps listening farther into a nearby channel. In this bounded setup at α = 0.35 and 63 taps, the half-sine design lifts the slope from '
        f'{proxy.central_slope_wrt_deltaf_over_Rs:.3f} to {half.central_slope_wrt_deltaf_over_Rs:.3f}, while the adjacent pickup at 1.0 R_s rises by about {ratio:.1f}× and the ≤5% spacing widens from '
        f'{proxy.spacing_for_capture_below_threshold:.2f} R_s to {half.spacing_for_capture_below_threshold:.2f} R_s.',
        'small',
        max_width=1880.0,
        font_size=15.0,
        line_height=20.0,
    )
    columns = [
        (
            left + 28.0,
            '#14263a',
            '#93c5fd',
            'Keep',
            [
                'The slope note still stands: the old proxy was understating moderate-roll-off near-lock gain.',
                'Small roll-off still stays weak even after the design improves.',
            ],
        ),
        (
            left + 690.0,
            '#173126',
            '#4ade80',
            'New claim',
            [
                'Half-sine is a slope-versus-selectivity tradeoff, not a free cleanup pass.',
                'In this bounded study, guardband cost is set more by design family than by tap count.',
            ],
        ),
        (
            left + 1352.0,
            '#341c12',
            '#facc15',
            'Next bounded move',
            [
                'If this branch gets one more turn, measure the same tradeoff in closed-loop behavior or with an explicit adjacent interferer level.',
                'Otherwise this is enough to stop pretending the better slope came for free.',
            ],
        ),
    ]
    for card_left, fill, stroke, title_text, bullets in columns:
        svg.append(rounded_rect(card_left, top + 126.0, 640.0, 112.0, fill, stroke, 1.8, 1.0, 16.0))
        svg.append(text(card_left + 18.0, top + 154.0, title_text, 'label'))
        for idx, bullet in enumerate(bullets):
            add_wrapped_text(svg, card_left + 18.0, top + 180.0 + idx * 24.0, f'• {bullet}', 'tiny', max_width=600.0, font_size=14.0, line_height=18.0)


def main() -> None:
    rows = sweep_band_edge_guardband_cost_comparison(
        ROLLOFFS,
        TAP_COUNTS,
        channel_spacings=CHANNEL_SPACINGS,
        capture_threshold=CAPTURE_THRESHOLD,
        reference_spacing=REFERENCE_SPACING,
        samples_per_symbol=SAMPLES_PER_SYMBOL,
        symbol_count=SYMBOL_COUNT,
        seed=SEED,
        trim=TRIM,
    )
    write_band_edge_guardband_cost_csv(rows, CSV_OUT)

    svg = [
        svg_root(WIDTH, HEIGHT),
        '<style>',
        'text { font-family: "Inter", "Helvetica Neue", Arial, sans-serif; }',
        '.title { font: 700 34px "Inter", "Helvetica Neue", Arial, sans-serif; fill: #e2e8f0; }',
        '.subtitle { font: 500 18px "Inter", "Helvetica Neue", Arial, sans-serif; fill: #cbd5e1; }',
        '.label { font: 700 22px "Inter", "Helvetica Neue", Arial, sans-serif; fill: #dbeafe; }',
        '.small { font: 500 16px "Inter", "Helvetica Neue", Arial, sans-serif; fill: #cbd5e1; }',
        '.tiny { font: 500 13px "Inter", "Helvetica Neue", Arial, sans-serif; fill: #cbd5e1; }',
        '</style>',
        rounded_rect(0, 0, WIDTH, HEIGHT, '#08111b'),
        rounded_rect(24, 24, WIDTH - 48, HEIGHT - 48, '#0d1826', '#1e293b', 2.0, 1.0, 24.0),
        text(60.0, 64.0, 'Band-edge filter shape: slope honesty versus guardband cost', 'title'),
        text(60.0, 96.0, 'Same bounded waveform setup as the slope note, but now asking what the wider half-sine design pays in adjacent pickup.', 'subtitle'),
    ]

    top_panel(svg, rows)
    metric_panel(
        svg,
        rows,
        left=60.0,
        top=504.0,
        width=980.0,
        height=760.0,
        title_text='Adjacent pickup at 1.0 R_s spacing',
        body='Each series shows how much energy the lower + upper band-edge filters capture from one adjacent QPSK channel whose center is 1.0 symbol rates away. Higher means worse selectivity.',
        y_min=0.0,
        y_max=0.55,
        y_ticks=[0.00, 0.10, 0.20, 0.30, 0.40, 0.50],
        y_label='captured adjacent energy / input energy',
        value_getter=lambda row: row.adjacent_capture_at_reference_spacing,
        value_formatter=lambda value: f'α = 0.35, 63 taps half-sine: {value:.1%} pickup at 1.0 R_s',
    )
    metric_panel(
        svg,
        rows,
        left=1100.0,
        top=504.0,
        width=980.0,
        height=760.0,
        title_text='Spacing needed for ≤5% pickup',
        body='This is the smallest tested center spacing where the same adjacent channel drops under 5% captured energy. Lower is cheaper on guardband. In this bounded study the design family moves this threshold more than tap count does.',
        y_min=0.5,
        y_max=1.7,
        y_ticks=[0.60, 0.80, 1.00, 1.20, 1.40, 1.60],
        y_label='required spacing  Δf / R_s',
        value_getter=lambda row: row.spacing_for_capture_below_threshold,
        value_formatter=lambda value: f'α = 0.35, 63 taps half-sine: {value:.2f} R_s for ≤5% pickup',
    )
    bottom_panel(svg, rows)
    svg.append('</svg>')

    SVG_OUT.write_text('\n'.join(svg) + '\n')
    export_png_from_svg(SVG_OUT, PNG_OUT, size=2200, dpi=300)
    print(f'wrote {SVG_OUT}, {PNG_OUT}, and {CSV_OUT}')


if __name__ == '__main__':
    main()
