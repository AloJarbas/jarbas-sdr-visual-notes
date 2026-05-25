#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from svg_layout import add_wrapped_text, export_png_from_svg, svg_root, text
from waveform_carrier_front_ends import (
    BandEdgeClosedLoopRow,
    study_band_edge_closed_loop_spacing_sweep,
    write_band_edge_closed_loop_csv,
)

REPO = Path(__file__).resolve().parents[1]
SVG_OUT = REPO / 'assets/2026-05-24-band-edge-spacing-boundary.svg'
PNG_OUT = REPO / 'assets/2026-05-24-band-edge-spacing-boundary.png'
CSV_OUT = REPO / 'assets/2026-05-24-band-edge-spacing-boundary.csv'

WIDTH = 2140
HEIGHT = 1640
SAMPLES_PER_SYMBOL = 4
SYMBOL_COUNT = 3072
ROLLOFF = 0.35
TAP_COUNT = 63
ADJACENT_POWER_DB = 0.0
BLOCK_SYMBOLS = 96
LOOP_GAIN = 0.02
TAIL_BLOCK_COUNT = 8
SETTLE_THRESHOLD = 0.05
CHANNEL_SPACINGS = [round(0.80 + 0.01 * idx, 2) for idx in range(86)]

DESIGN_COLORS = {
    'proxy_bandpass': '#93c5fd',
    'gnuradio_half_sine': '#fda4af',
}
DESIGN_LABELS = {
    'proxy_bandpass': 'Current proxy bandpass',
    'gnuradio_half_sine': 'GNU Radio / half-sine style',
}
DESIGN_DASH = {
    'proxy_bandpass': None,
    'gnuradio_half_sine': '12 8',
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
    return f'<rect x="{x - half:.1f}" y="{y - half:.1f}" width="{size:.1f}" height="{size:.1f}" fill="{fill}" opacity="{opacity}" rx="2.0"/>'


def polyline(points: list[tuple[float, float]], stroke: str, width: float = 3.0, opacity: float = 1.0, dash: str | None = None) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ''
    coords = ' '.join(f'{x:.1f},{y:.1f}' for x, y in points)
    return f'<polyline points="{coords}" fill="none" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}" stroke-linecap="round" stroke-linejoin="round"{dash_attr}/>'


def axis_x(value: float, left: float, width: float, minimum: float, maximum: float) -> float:
    return left + width * ((value - minimum) / (maximum - minimum))


def axis_y(value: float, top: float, height: float, minimum: float, maximum: float) -> float:
    return top + height - height * ((value - minimum) / (maximum - minimum))


def row_lookup(rows: list[BandEdgeClosedLoopRow]) -> dict[tuple[str, float], BandEdgeClosedLoopRow]:
    return {(row.design, round(row.channel_spacing, 2)): row for row in rows}


def series_for_design(rows: list[BandEdgeClosedLoopRow], design: str) -> list[BandEdgeClosedLoopRow]:
    return sorted((row for row in rows if row.design == design), key=lambda row: row.channel_spacing)


def first_spacing(rows: list[BandEdgeClosedLoopRow], design: str, predicate) -> float | None:
    for row in series_for_design(rows, design):
        if predicate(row):
            return round(row.channel_spacing, 2)
    return None


def first_crossover_spacing(rows: list[BandEdgeClosedLoopRow]) -> float | None:
    lookup = row_lookup(rows)
    for spacing in CHANNEL_SPACINGS:
        proxy = lookup[('proxy_bandpass', spacing)]
        half_sine = lookup[('gnuradio_half_sine', spacing)]
        if half_sine.tail_mean_abs_residual_cfo <= proxy.tail_mean_abs_residual_cfo:
            return spacing
    return None


def draw_chart_frame(
    svg: list[str],
    *,
    left: float,
    top: float,
    width: float,
    height: float,
    x_ticks: list[float],
    y_ticks: list[float],
    x_label: str,
    y_label: str,
    y_min: float,
    y_max: float,
    percent_y: bool = False,
) -> None:
    svg.append(line(left, top + height, left + width, top + height, '#5d7fa3', 2.2))
    svg.append(line(left, top, left, top + height, '#5d7fa3', 2.2))
    for value in x_ticks:
        x = axis_x(value, left, width, CHANNEL_SPACINGS[0], CHANNEL_SPACINGS[-1])
        svg.append(line(x, top + height - 6.0, x, top + height + 6.0, '#5d7fa3', 1.4))
        svg.append(text(x, top + height + 26.0, f'{value:.2f}', 'tiny', 'middle'))
        if value not in (x_ticks[0], x_ticks[-1]):
            svg.append(line(x, top, x, top + height, '#27415a', 1.0, 0.8, '4 8'))
    for value in y_ticks:
        y = axis_y(value, top, height, y_min, y_max)
        svg.append(line(left - 6.0, y, left + 6.0, y, '#5d7fa3', 1.4))
        label = f'{value:.0%}' if percent_y else f'{value:.2f}'
        svg.append(text(left - 18.0, y + 4.0, label, 'tiny', 'end'))
        if value not in (y_ticks[0], y_ticks[-1]):
            svg.append(line(left, y, left + width, y, '#27415a', 1.0, 0.8, '4 8'))
    svg.append(text(left + width / 2.0, top + height + 56.0, x_label, 'tiny', 'middle'))
    svg.append(text(left + 4.0, top - 12.0, y_label, 'tiny'))


def draw_series(svg: list[str], rows: list[BandEdgeClosedLoopRow], *, left: float, top: float, width: float, height: float, y_min: float, y_max: float, value_getter) -> None:
    for design in ['proxy_bandpass', 'gnuradio_half_sine']:
        series = series_for_design(rows, design)
        points = [
            (
                axis_x(row.channel_spacing, left, width, CHANNEL_SPACINGS[0], CHANNEL_SPACINGS[-1]),
                axis_y(value_getter(row), top, height, y_min, y_max),
            )
            for row in series
        ]
        svg.append(polyline(points, DESIGN_COLORS[design], 3.2, 1.0, DESIGN_DASH[design]))
        for idx in range(0, len(points), 5):
            x, y = points[idx]
            if design == 'proxy_bandpass':
                svg.append(circle(x, y, 4.8, DESIGN_COLORS[design]))
            else:
                svg.append(square(x, y, 8.6, DESIGN_COLORS[design]))


def draw_boundary_marker(svg: list[str], *, left: float, top: float, width: float, height: float, spacing: float | None, label_text: str, color: str) -> None:
    if spacing is None:
        return
    x = axis_x(spacing, left, width, CHANNEL_SPACINGS[0], CHANNEL_SPACINGS[-1])
    svg.append(line(x, top, x, top + height, color, 2.0, 0.95, '8 8'))
    svg.append(rounded_rect(x - 94.0, top + 16.0, 188.0, 34.0, '#13263b', color, 1.2, 1.0, 10.0))
    svg.append(text(x, top + 38.0, label_text, 'tiny', 'middle'))


def legend(svg: list[str], left: float, top: float) -> None:
    svg.append(rounded_rect(left, top, 390.0, 76.0, '#13263b', '#4f8cc9', 1.4, 1.0, 12.0))
    svg.append(line(left + 22.0, top + 28.0, left + 82.0, top + 28.0, DESIGN_COLORS['proxy_bandpass'], 2.8))
    svg.append(circle(left + 52.0, top + 28.0, 5.0, DESIGN_COLORS['proxy_bandpass']))
    svg.append(text(left + 96.0, top + 32.0, DESIGN_LABELS['proxy_bandpass'], 'tiny'))
    svg.append(line(left + 22.0, top + 52.0, left + 82.0, top + 52.0, DESIGN_COLORS['gnuradio_half_sine'], 2.8, 1.0, DESIGN_DASH['gnuradio_half_sine']))
    svg.append(square(left + 52.0, top + 52.0, 9.0, DESIGN_COLORS['gnuradio_half_sine']))
    svg.append(text(left + 96.0, top + 56.0, DESIGN_LABELS['gnuradio_half_sine'], 'tiny'))


def top_panel(svg: list[str], rows: list[BandEdgeClosedLoopRow], settle_spacing: float | None, crossover_spacing: float | None) -> None:
    lookup = row_lookup(rows)
    spacing_100 = lookup[('proxy_bandpass', 1.00)], lookup[('gnuradio_half_sine', 1.00)]
    settle_rows = (lookup[('proxy_bandpass', settle_spacing)], lookup[('gnuradio_half_sine', settle_spacing)]) if settle_spacing is not None else None
    crossover_rows = (lookup[('proxy_bandpass', crossover_spacing)], lookup[('gnuradio_half_sine', crossover_spacing)]) if crossover_spacing is not None else None

    left = 60.0
    top = 148.0
    width = 2020.0
    height = 332.0
    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 24.0, top + 38.0, 'The spacing sweep split one fuzzy “boundary” into two clean ones', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 74.0,
        'Same bounded loop as the last adjacent-channel note: SRRC QPSK, 4 samples/symbol, 63-tap band-edge filters, one blockwise loop with gain 0.02, and adjacent power fixed at 0 dB. The only knob moving now is channel spacing.',
        'small',
        max_width=1930.0,
        font_size=16.0,
        line_height=21.0,
    )

    cards = [
        (
            left + 28.0,
            '#341c12',
            '#facc15',
            '1.00 R_s: half-sine is still the worse loop',
            f'Proxy averages {spacing_100[0].tail_mean_abs_residual_cfo:.4f} R_s with {spacing_100[0].tail_within_threshold_fraction:.0%} of the tail inside ±{SETTLE_THRESHOLD:.2f} R_s. Half-sine averages {spacing_100[1].tail_mean_abs_residual_cfo:.4f} R_s with only {spacing_100[1].tail_within_threshold_fraction:.0%}.',
        ),
        (
            left + 690.0,
            '#173126',
            '#4ade80',
            f'{settle_spacing:.2f} R_s: half-sine gets back inside the settle band' if settle_spacing is not None else 'Settle-band boundary',
            f'At about {settle_spacing:.2f} R_s, every tail block is back inside ±{SETTLE_THRESHOLD:.2f} R_s for the half-sine lane, even though its mean pull is still higher than the proxy lane.' if settle_rows is not None else 'No settle-band boundary found in the tested spacing set.',
        ),
        (
            left + 1352.0,
            '#14263a',
            '#93c5fd',
            f'{crossover_spacing:.2f} R_s: the residual ranking finally flips' if crossover_spacing is not None else 'Residual crossover',
            f'Only around {crossover_spacing:.2f} R_s does the half-sine mean tail pull ({crossover_rows[1].tail_mean_abs_residual_cfo:.4f} R_s) edge below the proxy value ({crossover_rows[0].tail_mean_abs_residual_cfo:.4f} R_s).' if crossover_rows is not None else 'The mean-residual ranking never flipped in the tested spacing set.',
        ),
    ]
    for card_left, fill, stroke, title_text, body in cards:
        svg.append(rounded_rect(card_left, top + 166.0, 640.0, 126.0, fill, stroke, 1.8, 1.0, 16.0))
        svg.append(text(card_left + 18.0, top + 194.0, title_text, 'label'))
        add_wrapped_text(svg, card_left + 18.0, top + 220.0, body, 'tiny', max_width=594.0, font_size=14.0, line_height=18.0)


def residual_panel(svg: list[str], rows: list[BandEdgeClosedLoopRow], settle_spacing: float | None, crossover_spacing: float | None) -> None:
    left = 60.0
    top = 536.0
    width = 980.0
    height = 720.0
    chart_left = left + 90.0
    chart_top = top + 128.0
    chart_width = width - 152.0
    chart_height = 424.0

    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 24.0, top + 36.0, 'Mean tail residual CFO versus spacing', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 70.0,
        'Lower is better. The half-sine lane improves rapidly as the neighbor moves away, but it does not actually beat the proxy on this metric until the spacing is much larger than the first “track-ready again” point.',
        'small',
        max_width=884.0,
        font_size=15.0,
        line_height=20.0,
    )

    draw_chart_frame(
        svg,
        left=chart_left,
        top=chart_top,
        width=chart_width,
        height=chart_height,
        x_ticks=[0.80, 1.00, 1.20, 1.40, 1.60],
        y_ticks=[0.00, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12],
        x_label='channel spacing  (Δf / R_s)',
        y_label='mean |tail residual CFO|  (Δf / R_s)',
        y_min=0.0,
        y_max=0.12,
    )
    draw_series(
        svg,
        rows,
        left=chart_left,
        top=chart_top,
        width=chart_width,
        height=chart_height,
        y_min=0.0,
        y_max=0.12,
        value_getter=lambda row: row.tail_mean_abs_residual_cfo,
    )
    draw_boundary_marker(svg, left=chart_left, top=chart_top, width=chart_width, height=chart_height, spacing=settle_spacing, label_text=f'full settle band ≈ {settle_spacing:.2f} R_s' if settle_spacing is not None else '', color='#4ade80')
    draw_boundary_marker(svg, left=chart_left, top=chart_top, width=chart_width, height=chart_height, spacing=crossover_spacing, label_text=f'residual flip ≈ {crossover_spacing:.2f} R_s' if crossover_spacing is not None else '', color='#facc15')
    legend(svg, left + 24.0, top + 606.0)


def settle_panel(svg: list[str], rows: list[BandEdgeClosedLoopRow], settle_spacing: float | None, crossover_spacing: float | None) -> None:
    left = 1100.0
    top = 536.0
    width = 980.0
    height = 720.0
    chart_left = left + 90.0
    chart_top = top + 128.0
    chart_width = width - 152.0
    chart_height = 424.0

    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 24.0, top + 36.0, 'How much of the tail stays inside ±0.05 R_s?', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 70.0,
        'This is the same bounded settle-quality summary as before: count the last eight loop blocks and ask what fraction stay inside the ±0.05 R_s band. Here the first sharp boundary arrives earlier than the mean-residual crossover.',
        'small',
        max_width=884.0,
        font_size=15.0,
        line_height=20.0,
    )

    draw_chart_frame(
        svg,
        left=chart_left,
        top=chart_top,
        width=chart_width,
        height=chart_height,
        x_ticks=[0.80, 1.00, 1.20, 1.40, 1.60],
        y_ticks=[0.00, 0.25, 0.50, 0.75, 1.00],
        x_label='channel spacing  (Δf / R_s)',
        y_label='tail fraction inside ±0.05 R_s',
        y_min=0.0,
        y_max=1.0,
        percent_y=True,
    )
    draw_series(
        svg,
        rows,
        left=chart_left,
        top=chart_top,
        width=chart_width,
        height=chart_height,
        y_min=0.0,
        y_max=1.0,
        value_getter=lambda row: row.tail_within_threshold_fraction,
    )
    draw_boundary_marker(svg, left=chart_left, top=chart_top, width=chart_width, height=chart_height, spacing=settle_spacing, label_text=f'full settle band ≈ {settle_spacing:.2f} R_s' if settle_spacing is not None else '', color='#4ade80')
    draw_boundary_marker(svg, left=chart_left, top=chart_top, width=chart_width, height=chart_height, spacing=crossover_spacing, label_text=f'residual flip ≈ {crossover_spacing:.2f} R_s' if crossover_spacing is not None else '', color='#facc15')
    legend(svg, left + 24.0, top + 606.0)


def bottom_panel(svg: list[str], rows: list[BandEdgeClosedLoopRow], settle_spacing: float | None, crossover_spacing: float | None) -> None:
    lookup = row_lookup(rows)
    point_100 = lookup[('proxy_bandpass', 1.00)], lookup[('gnuradio_half_sine', 1.00)]
    point_settle = (lookup[('proxy_bandpass', settle_spacing)], lookup[('gnuradio_half_sine', settle_spacing)]) if settle_spacing is not None else None
    point_cross = (lookup[('proxy_bandpass', crossover_spacing)], lookup[('gnuradio_half_sine', crossover_spacing)]) if crossover_spacing is not None else None

    left = 60.0
    top = 1308.0
    width = 2020.0
    height = 270.0
    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 24.0, top + 36.0, 'What changed in the queue', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 72.0,
        'The earlier note proved that the half-sine lane lost under the fixed 1.0 R_s stress case. This spacing sweep answers the next sharper question: the ranking does not flip at one magical point unless the metric is named first. Track-ready settle behavior comes back around '
        f'{settle_spacing:.2f} R_s, while the stricter mean-residual ranking does not flip until about {crossover_spacing:.2f} R_s.',
        'small',
        max_width=1880.0,
        font_size=15.0,
        line_height=20.0,
    )

    columns = [
        (
            left + 28.0,
            '#341c12',
            '#facc15',
            'At 1.00 R_s',
            [
                f'Proxy: {point_100[0].tail_mean_abs_residual_cfo:.4f} R_s, {point_100[0].tail_within_threshold_fraction:.0%} inside band.',
                f'Half-sine: {point_100[1].tail_mean_abs_residual_cfo:.4f} R_s, {point_100[1].tail_within_threshold_fraction:.0%} inside band.',
            ],
        ),
        (
            left + 690.0,
            '#173126',
            '#4ade80',
            f'First full settle point ≈ {settle_spacing:.2f} R_s' if point_settle is not None else 'First full settle point',
            [
                f'Half-sine tail fraction reaches {point_settle[1].tail_within_threshold_fraction:.0%} with mean pull {point_settle[1].tail_mean_abs_residual_cfo:.4f} R_s.' if point_settle is not None else 'No full settle point found.',
                f'Proxy is already calm there at {point_settle[0].tail_mean_abs_residual_cfo:.4f} R_s.' if point_settle is not None else '',
            ],
        ),
        (
            left + 1352.0,
            '#14263a',
            '#93c5fd',
            f'Mean-residual flip ≈ {crossover_spacing:.2f} R_s' if point_cross is not None else 'Mean-residual flip',
            [
                f'Half-sine mean pull {point_cross[1].tail_mean_abs_residual_cfo:.4f} R_s finally edges below proxy {point_cross[0].tail_mean_abs_residual_cfo:.4f} R_s.' if point_cross is not None else 'No crossover found.',
                'That is the honest “preference flip” point for this stricter metric.',
            ],
        ),
    ]
    for card_left, fill, stroke, title_text, bullets in columns:
        svg.append(rounded_rect(card_left, top + 126.0, 640.0, 112.0, fill, stroke, 1.8, 1.0, 16.0))
        svg.append(text(card_left + 18.0, top + 152.0, title_text, 'label'))
        visible_bullets = [bullet for bullet in bullets if bullet]
        for idx, bullet in enumerate(visible_bullets):
            add_wrapped_text(svg, card_left + 18.0, top + 178.0 + idx * 24.0, f'• {bullet}', 'tiny', max_width=602.0, font_size=14.0, line_height=18.0)


def main() -> None:
    rows = study_band_edge_closed_loop_spacing_sweep(
        CHANNEL_SPACINGS,
        adjacent_relative_power_db=ADJACENT_POWER_DB,
        samples_per_symbol=SAMPLES_PER_SYMBOL,
        symbol_count=SYMBOL_COUNT,
        tap_count=TAP_COUNT,
        rolloff=ROLLOFF,
        block_symbols=BLOCK_SYMBOLS,
        loop_gain=LOOP_GAIN,
        tail_block_count=TAIL_BLOCK_COUNT,
        settle_threshold=SETTLE_THRESHOLD,
    )
    write_band_edge_closed_loop_csv(rows, CSV_OUT)

    settle_spacing = first_spacing(
        rows,
        'gnuradio_half_sine',
        lambda row: row.tail_within_threshold_fraction == 1.0,
    )
    crossover_spacing = first_crossover_spacing(rows)

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
        rounded_rect(0.0, 0.0, WIDTH, HEIGHT, '#08111b'),
        rounded_rect(24.0, 24.0, WIDTH - 48.0, HEIGHT - 48.0, '#0d1826', '#1e293b', 2.0, 1.0, 24.0),
        text(60.0, 66.0, 'Band-edge spacing boundary after the first adjacent-loop test', 'title'),
        text(60.0, 98.0, 'At fixed loop gain and fixed 0 dB adjacent power, spacing alone reveals two different boundaries: when the half-sine lane becomes track-ready again, and when it finally stops being the worse loop on mean residual.', 'subtitle'),
    ]

    top_panel(svg, rows, settle_spacing, crossover_spacing)
    residual_panel(svg, rows, settle_spacing, crossover_spacing)
    settle_panel(svg, rows, settle_spacing, crossover_spacing)
    bottom_panel(svg, rows, settle_spacing, crossover_spacing)
    svg.append('</svg>')

    SVG_OUT.write_text('\n'.join(svg) + '\n')
    export_png_from_svg(SVG_OUT, PNG_OUT, size=2200, dpi=300)
    print(f'wrote {SVG_OUT}, {PNG_OUT}, and {CSV_OUT}')


if __name__ == '__main__':
    main()
