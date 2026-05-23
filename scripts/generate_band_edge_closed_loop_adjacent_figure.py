#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from svg_layout import add_wrapped_text, export_png_from_svg, svg_root, text
from waveform_carrier_front_ends import (
    BandEdgeClosedLoopRow,
    study_band_edge_closed_loop_adjacent_pull,
    write_band_edge_closed_loop_csv,
)

REPO = Path(__file__).resolve().parents[1]
SVG_OUT = REPO / 'assets/2026-05-23-band-edge-closed-loop-adjacent-pull.svg'
PNG_OUT = REPO / 'assets/2026-05-23-band-edge-closed-loop-adjacent-pull.png'
CSV_OUT = REPO / 'assets/2026-05-23-band-edge-closed-loop-adjacent-pull.csv'

WIDTH = 2140
HEIGHT = 1600
SAMPLES_PER_SYMBOL = 4
SYMBOL_COUNT = 3072
ROLLOFF = 0.35
TAP_COUNT = 63
CHANNEL_SPACING = 1.0
BLOCK_SYMBOLS = 96
LOOP_GAIN = 0.02
TAIL_BLOCK_COUNT = 8
SETTLE_THRESHOLD = 0.05
ADJACENT_POWERS_DB = [-12.0, -6.0, 0.0, 6.0]

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
CATEGORY_LABELS = ['desired only', '-12 dB', '-6 dB', '0 dB', '+6 dB']


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


def category_sort_key(row: BandEdgeClosedLoopRow) -> float:
    return -999.0 if not row.adjacent_enabled else row.adjacent_relative_power_db


def category_label(row: BandEdgeClosedLoopRow) -> str:
    return 'desired only' if not row.adjacent_enabled else f'{row.adjacent_relative_power_db:+.0f} dB'.replace('+0 dB', '0 dB')


def grouped_rows(rows: list[BandEdgeClosedLoopRow]) -> dict[str, list[BandEdgeClosedLoopRow]]:
    grouped: dict[str, list[BandEdgeClosedLoopRow]] = {}
    for row in rows:
        grouped.setdefault(row.design, []).append(row)
    return {design: sorted(series, key=category_sort_key) for design, series in grouped.items()}


def row_lookup(rows: list[BandEdgeClosedLoopRow]) -> dict[tuple[str, str], BandEdgeClosedLoopRow]:
    return {(row.design, category_label(row)): row for row in rows}


def category_positions(left: float, width: float) -> dict[str, float]:
    gap = width / (len(CATEGORY_LABELS) - 1)
    return {label: left + idx * gap for idx, label in enumerate(CATEGORY_LABELS)}


def axis_y(value: float, top: float, height: float, minimum: float, maximum: float) -> float:
    return top + height - height * ((value - minimum) / (maximum - minimum))


def draw_chart_frame(
    svg: list[str],
    *,
    left: float,
    top: float,
    width: float,
    height: float,
    y_min: float,
    y_max: float,
    y_ticks: list[float],
    y_label: str,
    threshold: float | None = None,
    threshold_label: str | None = None,
) -> dict[str, float]:
    x_positions = category_positions(left, width)
    svg.append(line(left, top + height, left + width, top + height, '#5d7fa3', 2.2))
    svg.append(line(left, top, left, top + height, '#5d7fa3', 2.2))
    for label, x in x_positions.items():
        svg.append(line(x, top + height - 6.0, x, top + height + 6.0, '#5d7fa3', 1.4))
        svg.append(text(x, top + height + 28.0, label, 'tiny', 'middle'))
        if label not in ('desired only', '+6 dB'):
            svg.append(line(x, top, x, top + height, '#27415a', 1.0, 0.7, '4 8'))
    for tick in y_ticks:
        y = axis_y(tick, top, height, y_min, y_max)
        label = f'{tick:.2f}' if y_max <= 1.0 else f'{tick:.0%}'
        svg.append(line(left - 6.0, y, left + 6.0, y, '#5d7fa3', 1.4))
        svg.append(text(left - 18.0, y + 4.0, label, 'tiny', 'end'))
        if tick not in (y_ticks[0], y_ticks[-1]):
            svg.append(line(left, y, left + width, y, '#27415a', 1.0, 0.7, '4 8'))
    if threshold is not None:
        y = axis_y(threshold, top, height, y_min, y_max)
        svg.append(line(left, y, left + width, y, '#facc15', 2.0, 0.9, '10 8'))
        if threshold_label:
            svg.append(text(left + width - 10.0, y - 8.0, threshold_label, 'tiny', 'end'))
    svg.append(text(left + 4.0, top - 14.0, y_label, 'tiny'))
    return x_positions


def draw_series(
    svg: list[str],
    rows: list[BandEdgeClosedLoopRow],
    *,
    left: float,
    top: float,
    width: float,
    height: float,
    y_min: float,
    y_max: float,
    value_getter,
) -> None:
    x_positions = category_positions(left, width)
    for design, series in grouped_rows(rows).items():
        points = [
            (x_positions[category_label(row)], axis_y(value_getter(row), top, height, y_min, y_max))
            for row in series
        ]
        svg.append(polyline(points, DESIGN_COLORS[design], 3.4, 1.0, DESIGN_DASH[design]))
        for x, y in points:
            if design == 'proxy_bandpass':
                svg.append(circle(x, y, 5.5, DESIGN_COLORS[design]))
            else:
                svg.append(square(x, y, 10.0, DESIGN_COLORS[design]))


def legend(svg: list[str], left: float, top: float) -> None:
    svg.append(rounded_rect(left, top, 390.0, 76.0, '#13263b', '#4f8cc9', 1.4, 1.0, 12.0))
    svg.append(line(left + 22.0, top + 28.0, left + 82.0, top + 28.0, DESIGN_COLORS['proxy_bandpass'], 2.8))
    svg.append(circle(left + 52.0, top + 28.0, 5.0, DESIGN_COLORS['proxy_bandpass']))
    svg.append(text(left + 96.0, top + 32.0, DESIGN_LABELS['proxy_bandpass'], 'tiny'))
    svg.append(line(left + 22.0, top + 52.0, left + 82.0, top + 52.0, DESIGN_COLORS['gnuradio_half_sine'], 2.8, 1.0, DESIGN_DASH['gnuradio_half_sine']))
    svg.append(square(left + 52.0, top + 52.0, 9.0, DESIGN_COLORS['gnuradio_half_sine']))
    svg.append(text(left + 96.0, top + 56.0, DESIGN_LABELS['gnuradio_half_sine'], 'tiny'))


def summary_cards(svg: list[str], rows: list[BandEdgeClosedLoopRow]) -> None:
    lookup = row_lookup(rows)
    proxy_off = lookup[('proxy_bandpass', 'desired only')]
    half_off = lookup[('gnuradio_half_sine', 'desired only')]
    proxy_zero = lookup[('proxy_bandpass', '0 dB')]
    half_zero = lookup[('gnuradio_half_sine', '0 dB')]
    proxy_six = lookup[('proxy_bandpass', '+6 dB')]
    half_six = lookup[('gnuradio_half_sine', '+6 dB')]

    left = 60.0
    top = 148.0
    width = 2020.0
    height = 332.0
    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 24.0, top + 38.0, 'One bounded loop test was enough to turn the static tradeoff into a real receiver claim', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 74.0,
        'Same waveform setup as the guardband note: SRRC QPSK, 4 samples/symbol, 63-tap band-edge filters, one adjacent interferer at 1.0 R_s spacing, and one simple blockwise frequency loop. The loop starts at the right carrier. The only job here is to watch how far the adjacent channel pulls it away.',
        'small',
        max_width=1930.0,
        font_size=16.0,
        line_height=21.0,
    )

    cards = [
        (
            left + 28.0,
            '#14263a',
            '#93c5fd',
            'Desired only: both loops stay near zero',
            f'Proxy tail pull is {proxy_off.tail_mean_abs_residual_cfo:.4f} R_s and half-sine is {half_off.tail_mean_abs_residual_cfo:.4f} R_s. The wider detector is not noisy by itself in this bounded case.',
        ),
        (
            left + 690.0,
            '#341c12',
            '#facc15',
            '0 dB adjacent: the half-sine slope win turns into larger pull',
            f'Proxy still averages {proxy_zero.tail_mean_abs_residual_cfo:.3f} R_s with {proxy_zero.tail_within_threshold_fraction:.0%} of the tail inside ±{SETTLE_THRESHOLD:.2f} R_s. Half-sine jumps to {half_zero.tail_mean_abs_residual_cfo:.3f} R_s and drops to {half_zero.tail_within_threshold_fraction:.0%}.',
        ),
        (
            left + 1352.0,
            '#3a1018',
            '#fda4af',
            '+6 dB adjacent: both are stressed, but not equally',
            f'Proxy reaches {proxy_six.tail_mean_abs_residual_cfo:.3f} R_s. Half-sine reaches {half_six.tail_mean_abs_residual_cfo:.3f} R_s with detector output still averaging {half_six.tail_mean_abs_detector_output:.3f}. The wide lane keeps listening harder into the neighbor.',
        ),
    ]
    for card_left, fill, stroke, title_text, body in cards:
        svg.append(rounded_rect(card_left, top + 166.0, 640.0, 126.0, fill, stroke, 1.8, 1.0, 16.0))
        svg.append(text(card_left + 18.0, top + 194.0, title_text, 'label'))
        add_wrapped_text(svg, card_left + 18.0, top + 220.0, body, 'tiny', max_width=594.0, font_size=14.0, line_height=18.0)


def residual_panel(svg: list[str], rows: list[BandEdgeClosedLoopRow]) -> None:
    left = 60.0
    top = 536.0
    width = 980.0
    height = 700.0
    chart_left = left + 86.0
    chart_top = top + 124.0
    chart_width = width - 146.0
    chart_height = 414.0
    lookup = row_lookup(rows)
    proxy = lookup[('proxy_bandpass', '0 dB')]
    half_sine = lookup[('gnuradio_half_sine', '0 dB')]

    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 24.0, top + 36.0, 'Tail carrier pull versus adjacent power', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 70.0,
        'The y-axis is the mean |residual CFO| over the last eight loop blocks. The dashed line marks the same ±0.05 R_s band used for the settle-quality panel.',
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
        y_min=0.0,
        y_max=0.22,
        y_ticks=[0.0, 0.05, 0.10, 0.15, 0.20],
        y_label='mean |tail residual CFO|  (Δf / R_s)',
        threshold=SETTLE_THRESHOLD,
        threshold_label='±0.05 R_s band',
    )
    draw_series(
        svg,
        rows,
        left=chart_left,
        top=chart_top,
        width=chart_width,
        height=chart_height,
        y_min=0.0,
        y_max=0.22,
        value_getter=lambda row: row.tail_mean_abs_residual_cfo,
    )
    legend(svg, left + 24.0, top + 598.0)

    svg.append(rounded_rect(left + 430.0, top + 566.0, 516.0, 94.0, '#13263b', '#4f8cc9', 1.4, 1.0, 12.0))
    add_wrapped_text(
        svg,
        left + 448.0,
        top + 594.0,
        f'At 0 dB adjacent power, the same loop gain pulls the proxy lane to {proxy.tail_mean_abs_residual_cfo:.3f} R_s but the half-sine lane to {half_sine.tail_mean_abs_residual_cfo:.3f} R_s. That is not a cosmetic redraw of the static detector bias; it is a loop-level shift.',
        'tiny',
        max_width=480.0,
        font_size=14.0,
        line_height=18.0,
    )


def settle_panel(svg: list[str], rows: list[BandEdgeClosedLoopRow]) -> None:
    left = 1100.0
    top = 536.0
    width = 980.0
    height = 700.0
    chart_left = left + 86.0
    chart_top = top + 124.0
    chart_width = width - 146.0
    chart_height = 414.0
    lookup = row_lookup(rows)
    proxy_zero = lookup[('proxy_bandpass', '0 dB')]
    half_zero = lookup[('gnuradio_half_sine', '0 dB')]

    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 24.0, top + 36.0, 'How much of the tail stays inside ±0.05 R_s?', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 70.0,
        'This stays deliberately simple. For each case, count the last eight loop blocks and ask what fraction remain inside the ±0.05 R_s track-ready band. It is not BER; it is a bounded settle-quality summary.',
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
        y_min=0.0,
        y_max=1.0,
        y_ticks=[0.0, 0.25, 0.50, 0.75, 1.0],
        y_label='tail fraction inside ±0.05 R_s',
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
    legend(svg, left + 24.0, top + 598.0)

    svg.append(rounded_rect(left + 430.0, top + 566.0, 516.0, 94.0, '#13263b', '#4f8cc9', 1.4, 1.0, 12.0))
    add_wrapped_text(
        svg,
        left + 448.0,
        top + 594.0,
        f'At 0 dB adjacent power, proxy stays inside the band for {proxy_zero.tail_within_threshold_fraction:.0%} of the tail while half-sine drops to {half_zero.tail_within_threshold_fraction:.0%}. The isolated-signal slope fix is real, but it is not the more robust adjacent-channel loop under this bounded stress.',
        'tiny',
        max_width=480.0,
        font_size=14.0,
        line_height=18.0,
    )


def bottom_panel(svg: list[str], rows: list[BandEdgeClosedLoopRow]) -> None:
    lookup = row_lookup(rows)
    proxy_off = lookup[('proxy_bandpass', 'desired only')]
    half_off = lookup[('gnuradio_half_sine', 'desired only')]
    proxy_zero = lookup[('proxy_bandpass', '0 dB')]
    half_zero = lookup[('gnuradio_half_sine', '0 dB')]

    left = 60.0
    top = 1288.0
    width = 2020.0
    height = 252.0
    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 24.0, top + 34.0, 'What changed in the repo', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 68.0,
        'The earlier guardband note already showed why the half-sine detector hears more adjacent energy. This pass turns that into the smallest honest loop claim: with the same blockwise loop and the same 1.0 R_s neighbor, both designs stay calm on the desired-only waveform, but once the adjacent channel reaches 0 dB the half-sine lane gets pulled much farther from the true carrier. In this bounded setup the proxy lane averages '
        f'{proxy_zero.tail_mean_abs_residual_cfo:.3f} R_s and keeps {proxy_zero.tail_within_threshold_fraction:.0%} of the tail inside the band, while the half-sine lane averages {half_zero.tail_mean_abs_residual_cfo:.3f} R_s and keeps only {half_zero.tail_within_threshold_fraction:.0%}.',
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
                f'Desired only still looks fine for both designs ({proxy_off.tail_mean_abs_residual_cfo:.4f} and {half_off.tail_mean_abs_residual_cfo:.4f} R_s tail pull). The half-sine lane still wins the isolated-slope check.',
            ],
        ),
        (
            left + 690.0,
            '#173126',
            '#4ade80',
            'New claim',
            [
                'Once the adjacent channel is actually mixed in, the honest comparison becomes loop-level, and under this bounded stress case the wider half-sine lane is not the more robust adjacent-channel loop.',
            ],
        ),
        (
            left + 1352.0,
            '#341c12',
            '#facc15',
            'Clean next move',
            [
                'If this branch gets one more pass, vary spacing or loop gain — not both — and find the first point where the ranking flips instead of broadening into a full modem benchmark.',
            ],
        ),
    ]
    for card_left, fill, stroke, title_text, bullets in columns:
        svg.append(rounded_rect(card_left, top + 110.0, 640.0, 102.0, fill, stroke, 1.8, 1.0, 16.0))
        svg.append(text(card_left + 18.0, top + 132.0, title_text, 'label'))
        for idx, bullet in enumerate(bullets):
            add_wrapped_text(svg, card_left + 18.0, top + 154.0 + idx * 26.0, f'• {bullet}', 'tiny', max_width=602.0, font_size=14.0, line_height=18.0)


def main() -> None:
    rows = study_band_edge_closed_loop_adjacent_pull(
        ADJACENT_POWERS_DB,
        include_desired_only=True,
        samples_per_symbol=SAMPLES_PER_SYMBOL,
        symbol_count=SYMBOL_COUNT,
        tap_count=TAP_COUNT,
        rolloff=ROLLOFF,
        channel_spacing=CHANNEL_SPACING,
        block_symbols=BLOCK_SYMBOLS,
        loop_gain=LOOP_GAIN,
        tail_block_count=TAIL_BLOCK_COUNT,
        settle_threshold=SETTLE_THRESHOLD,
    )
    write_band_edge_closed_loop_csv(rows, CSV_OUT)

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
        text(60.0, 66.0, 'Band-edge closed-loop pull with one adjacent interferer', 'title'),
        text(60.0, 98.0, 'The half-sine path stays honest on isolated slope, but this bounded loop test asks what happens after a nearby QPSK channel is actually mixed in.', 'subtitle'),
    ]

    summary_cards(svg, rows)
    residual_panel(svg, rows)
    settle_panel(svg, rows)
    bottom_panel(svg, rows)
    svg.append('</svg>')

    SVG_OUT.write_text('\n'.join(svg))
    export_png_from_svg(SVG_OUT, PNG_OUT, size=2200, dpi=300)


if __name__ == '__main__':
    main()
