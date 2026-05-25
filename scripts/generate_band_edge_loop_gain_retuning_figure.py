#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from svg_layout import add_wrapped_text, export_png_from_svg, svg_root, text
from waveform_carrier_front_ends import (
    BandEdgeClosedLoopRow,
    study_band_edge_closed_loop_gain_sweep,
    write_band_edge_closed_loop_csv,
)

REPO = Path(__file__).resolve().parents[1]
SVG_OUT = REPO / 'assets/2026-05-24-band-edge-loop-gain-retuning.svg'
PNG_OUT = REPO / 'assets/2026-05-24-band-edge-loop-gain-retuning.png'
CSV_OUT = REPO / 'assets/2026-05-24-band-edge-loop-gain-retuning.csv'

WIDTH = 2140
HEIGHT = 1780
SAMPLES_PER_SYMBOL = 4
SYMBOL_COUNT = 3072
ROLLOFF = 0.35
TAP_COUNT = 63
CHANNEL_SPACING = 1.24
ADJACENT_POWER_DB = 0.0
BLOCK_SYMBOLS = 96
TAIL_BLOCK_COUNT = 8
SETTLE_THRESHOLD = 0.05
LOOP_GAINS = [0.0005, 0.0010, 0.0015, 0.0020, 0.0030, 0.0040, 0.0050, 0.0060, 0.0080, 0.0100, 0.0120, 0.0150, 0.0180, 0.0200, 0.0220, 0.0240]
LOW_GAIN = 0.0020
BASE_GAIN = 0.0200

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
    return {(row.design, round(row.loop_gain, 4)): row for row in rows}


def series_for_design(rows: list[BandEdgeClosedLoopRow], design: str) -> list[BandEdgeClosedLoopRow]:
    return sorted((row for row in rows if row.design == design), key=lambda row: row.loop_gain)


def first_loss_gain(rows: list[BandEdgeClosedLoopRow], design: str) -> float | None:
    for row in series_for_design(rows, design):
        if row.tail_within_threshold_fraction < 1.0:
            return round(row.loop_gain, 4)
    return None


def residual_ratio_series(rows: list[BandEdgeClosedLoopRow]) -> list[tuple[float, float]]:
    lookup = row_lookup(rows)
    out: list[tuple[float, float]] = []
    for gain in LOOP_GAINS:
        proxy = lookup[('proxy_bandpass', round(gain, 4))]
        half_sine = lookup[('gnuradio_half_sine', round(gain, 4))]
        out.append((gain, half_sine.tail_mean_abs_residual_cfo / proxy.tail_mean_abs_residual_cfo))
    return out


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
    y_format: str = 'float',
) -> None:
    x_min = LOOP_GAINS[0]
    x_max = LOOP_GAINS[-1]
    svg.append(line(left, top + height, left + width, top + height, '#5d7fa3', 2.2))
    svg.append(line(left, top, left, top + height, '#5d7fa3', 2.2))
    for value in x_ticks:
        x = axis_x(value, left, width, x_min, x_max)
        svg.append(line(x, top + height - 6.0, x, top + height + 6.0, '#5d7fa3', 1.4))
        svg.append(text(x, top + height + 26.0, f'{value:.3f}', 'tiny', 'middle'))
        if value not in (x_ticks[0], x_ticks[-1]):
            svg.append(line(x, top, x, top + height, '#27415a', 1.0, 0.8, '4 8'))
    for value in y_ticks:
        y = axis_y(value, top, height, y_min, y_max)
        svg.append(line(left - 6.0, y, left + 6.0, y, '#5d7fa3', 1.4))
        if percent_y:
            label = f'{value:.0%}'
        elif y_format == 'int':
            label = f'{value:.0f}'
        else:
            label = f'{value:.3f}' if y_max <= 0.1 else f'{value:.2f}'
        svg.append(text(left - 18.0, y + 4.0, label, 'tiny', 'end'))
        if value not in (y_ticks[0], y_ticks[-1]):
            svg.append(line(left, y, left + width, y, '#27415a', 1.0, 0.8, '4 8'))
    svg.append(text(left + width / 2.0, top + height + 56.0, x_label, 'tiny', 'middle'))
    svg.append(text(left + 4.0, top - 12.0, y_label, 'tiny'))


def draw_series(svg: list[str], rows: list[BandEdgeClosedLoopRow], *, left: float, top: float, width: float, height: float, y_min: float, y_max: float, value_getter) -> None:
    x_min = LOOP_GAINS[0]
    x_max = LOOP_GAINS[-1]
    for design in ['proxy_bandpass', 'gnuradio_half_sine']:
        series = series_for_design(rows, design)
        points = [
            (
                axis_x(row.loop_gain, left, width, x_min, x_max),
                axis_y(value_getter(row), top, height, y_min, y_max),
            )
            for row in series
        ]
        svg.append(polyline(points, DESIGN_COLORS[design], 3.2, 1.0, DESIGN_DASH[design]))
        for x, y in points:
            if design == 'proxy_bandpass':
                svg.append(circle(x, y, 4.8, DESIGN_COLORS[design]))
            else:
                svg.append(square(x, y, 8.6, DESIGN_COLORS[design]))


def draw_ratio_series(svg: list[str], series: list[tuple[float, float]], *, left: float, top: float, width: float, height: float, y_min: float, y_max: float) -> None:
    x_min = LOOP_GAINS[0]
    x_max = LOOP_GAINS[-1]
    points = [
        (
            axis_x(loop_gain, left, width, x_min, x_max),
            axis_y(ratio, top, height, y_min, y_max),
        )
        for loop_gain, ratio in series
    ]
    svg.append(polyline(points, '#facc15', 3.2))
    for x, y in points:
        svg.append(circle(x, y, 4.6, '#facc15'))


def draw_vertical_marker(svg: list[str], *, left: float, top: float, width: float, height: float, gain: float | None, label_text: str, color: str, y_offset: float = 18.0) -> None:
    if gain is None:
        return
    x = axis_x(gain, left, width, LOOP_GAINS[0], LOOP_GAINS[-1])
    rect_x = min(max(x - 94.0, left + 8.0), left + width - 196.0)
    svg.append(line(x, top, x, top + height, color, 2.0, 0.95, '8 8'))
    svg.append(rounded_rect(rect_x, top + y_offset, 188.0, 34.0, '#13263b', color, 1.2, 1.0, 10.0))
    svg.append(text(rect_x + 94.0, top + y_offset + 22.0, label_text, 'tiny', 'middle'))


def legend(svg: list[str], left: float, top: float) -> None:
    svg.append(rounded_rect(left, top, 390.0, 76.0, '#13263b', '#4f8cc9', 1.4, 1.0, 12.0))
    svg.append(line(left + 22.0, top + 28.0, left + 82.0, top + 28.0, DESIGN_COLORS['proxy_bandpass'], 2.8))
    svg.append(circle(left + 52.0, top + 28.0, 5.0, DESIGN_COLORS['proxy_bandpass']))
    svg.append(text(left + 96.0, top + 32.0, DESIGN_LABELS['proxy_bandpass'], 'tiny'))
    svg.append(line(left + 22.0, top + 52.0, left + 82.0, top + 52.0, DESIGN_COLORS['gnuradio_half_sine'], 2.8, 1.0, DESIGN_DASH['gnuradio_half_sine']))
    svg.append(square(left + 52.0, top + 52.0, 9.0, DESIGN_COLORS['gnuradio_half_sine']))
    svg.append(text(left + 96.0, top + 56.0, DESIGN_LABELS['gnuradio_half_sine'], 'tiny'))


def top_panel(svg: list[str], rows: list[BandEdgeClosedLoopRow], loss_gain: float | None) -> None:
    lookup = row_lookup(rows)
    low_proxy = lookup[('proxy_bandpass', round(LOW_GAIN, 4))]
    low_half = lookup[('gnuradio_half_sine', round(LOW_GAIN, 4))]
    base_proxy = lookup[('proxy_bandpass', round(BASE_GAIN, 4))]
    base_half = lookup[('gnuradio_half_sine', round(BASE_GAIN, 4))]
    loss_half = lookup[('gnuradio_half_sine', round(loss_gain, 4))] if loss_gain is not None else None

    left = 60.0
    top = 148.0
    width = 2020.0
    height = 330.0
    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 24.0, top + 38.0, 'At the first settle-point spacing, gain retuning mostly rescales the same adjacent-pull gap', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 74.0,
        'This pass keeps spacing fixed at 1.24 R_s, adjacent power fixed at 0 dB, and sweeps only loop gain. The question is whether retuning can make the half-sine lane stop being the worse loop, or whether spacing geometry is still doing most of the work.',
        'small',
        max_width=1930.0,
        font_size=16.0,
        line_height=21.0,
    )

    cards = [
        (
            left + 28.0,
            '#173126',
            '#4ade80',
            'Lower gain helps both loops, but not equally',
            f'At gain {LOW_GAIN:.3f}, proxy tail pull is {low_proxy.tail_mean_abs_residual_cfo:.4f} R_s and half-sine is {low_half.tail_mean_abs_residual_cfo:.4f} R_s. That is already much calmer than the {BASE_GAIN:.3f} baseline, but half-sine is still about {low_half.tail_mean_abs_residual_cfo / low_proxy.tail_mean_abs_residual_cfo:.1f}x worse.',
        ),
        (
            left + 690.0,
            '#14263a',
            '#93c5fd',
            'The original 0.020 baseline was not a fluke',
            f'At gain {BASE_GAIN:.3f}, proxy stays at {base_proxy.tail_mean_abs_residual_cfo:.4f} R_s with 100% of the tail inside ±{SETTLE_THRESHOLD:.2f} R_s, while half-sine is {base_half.tail_mean_abs_residual_cfo:.4f} R_s. The residual ranking never flips anywhere in the tested gain set.',
        ),
        (
            left + 1352.0,
            '#341c12',
            '#facc15',
            f'By about {loss_gain:.3f}, half-sine starts losing the settle band' if loss_gain is not None else 'Settle-band loss',
            f'At gain {loss_gain:.3f}, the half-sine lane falls to {loss_half.tail_within_threshold_fraction:.0%} of tail blocks inside ±{SETTLE_THRESHOLD:.2f} R_s, while the proxy lane is still at 100%.' if loss_half is not None else 'The half-sine lane never lost the settle band in the tested gain set.',
        ),
    ]
    for card_left, fill, stroke, title_text, body in cards:
        svg.append(rounded_rect(card_left, top + 164.0, 640.0, 128.0, fill, stroke, 1.8, 1.0, 16.0))
        svg.append(text(card_left + 18.0, top + 192.0, title_text, 'label'))
        add_wrapped_text(svg, card_left + 18.0, top + 218.0, body, 'tiny', max_width=594.0, font_size=14.0, line_height=18.0)


def residual_panel(svg: list[str], rows: list[BandEdgeClosedLoopRow], loss_gain: float | None) -> None:
    left = 60.0
    top = 536.0
    width = 980.0
    height = 560.0
    chart_left = left + 90.0
    chart_top = top + 124.0
    chart_width = width - 152.0
    chart_height = 330.0

    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 24.0, top + 36.0, 'Mean tail residual CFO versus loop gain', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 72.0,
        'Reducing gain calms both loops, but the half-sine line stays above the proxy line everywhere. This means the spacing penalty did not turn into a one-parameter tuning problem.',
        'small',
        max_width=910.0,
        font_size=16.0,
        line_height=21.0,
    )
    draw_chart_frame(
        svg,
        left=chart_left,
        top=chart_top,
        width=chart_width,
        height=chart_height,
        x_ticks=[0.002, 0.006, 0.010, 0.014, 0.018, 0.022],
        y_ticks=[0.0, 0.01, 0.02, 0.03, 0.04, 0.05],
        x_label='loop gain',
        y_label='mean tail residual CFO (R_s)',
        y_min=0.0,
        y_max=0.055,
    )
    draw_series(
        svg,
        rows,
        left=chart_left,
        top=chart_top,
        width=chart_width,
        height=chart_height,
        y_min=0.0,
        y_max=0.055,
        value_getter=lambda row: row.tail_mean_abs_residual_cfo,
    )
    draw_vertical_marker(svg, left=chart_left, top=chart_top, width=chart_width, height=chart_height, gain=BASE_GAIN, label_text='0.020 baseline', color='#93c5fd')
    draw_vertical_marker(svg, left=chart_left, top=chart_top, width=chart_width, height=chart_height, gain=loss_gain, label_text='half-sine loses 100%', color='#facc15', y_offset=60.0)
    legend(svg, left + 520.0, top + 92.0)


def settle_panel(svg: list[str], rows: list[BandEdgeClosedLoopRow], loss_gain: float | None) -> None:
    left = 1100.0
    top = 536.0
    width = 980.0
    height = 560.0
    chart_left = left + 90.0
    chart_top = top + 124.0
    chart_width = width - 152.0
    chart_height = 330.0

    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 24.0, top + 36.0, 'Tail fraction inside ±0.05 R_s', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 72.0,
        'The proxy lane keeps every tested gain inside the settle band. The half-sine lane is fine while gain stays modest, then starts dropping tail blocks once the loop is driven harder.',
        'small',
        max_width=910.0,
        font_size=16.0,
        line_height=21.0,
    )
    draw_chart_frame(
        svg,
        left=chart_left,
        top=chart_top,
        width=chart_width,
        height=chart_height,
        x_ticks=[0.002, 0.006, 0.010, 0.014, 0.018, 0.022],
        y_ticks=[0.0, 0.25, 0.5, 0.75, 1.0],
        x_label='loop gain',
        y_label='tail fraction inside threshold',
        y_min=0.0,
        y_max=1.05,
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
        y_max=1.05,
        value_getter=lambda row: row.tail_within_threshold_fraction,
    )
    draw_vertical_marker(svg, left=chart_left, top=chart_top, width=chart_width, height=chart_height, gain=loss_gain, label_text='first loss', color='#facc15')


def ratio_panel(svg: list[str], rows: list[BandEdgeClosedLoopRow]) -> None:
    ratios = residual_ratio_series(rows)
    left = 60.0
    top = 1146.0
    width = 2020.0
    height = 560.0
    chart_left = left + 90.0
    chart_top = top + 128.0
    chart_width = width - 152.0
    chart_height = 270.0

    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 24.0, top + 36.0, 'Half-sine / proxy residual ratio stays stubbornly high', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 72.0,
        'This is the key readout. If retuning were really fixing the spacing problem, the residual ratio would bend down toward 1 as gain moved. Instead it sits around 15-16x on the default seeds, which says the detector geometry is still the main story.',
        'small',
        max_width=1930.0,
        font_size=16.0,
        line_height=21.0,
    )
    draw_chart_frame(
        svg,
        left=chart_left,
        top=chart_top,
        width=chart_width,
        height=chart_height,
        x_ticks=[0.002, 0.006, 0.010, 0.014, 0.018, 0.022],
        y_ticks=[0.0, 5.0, 10.0, 15.0, 20.0],
        x_label='loop gain',
        y_label='half-sine residual / proxy residual',
        y_min=0.0,
        y_max=20.0,
        y_format='int',
    )
    draw_ratio_series(
        svg,
        ratios,
        left=chart_left,
        top=chart_top,
        width=chart_width,
        height=chart_height,
        y_min=0.0,
        y_max=20.0,
    )
    low_ratio = next(ratio for gain, ratio in ratios if abs(gain - LOW_GAIN) < 1.0e-12)
    base_ratio = next(ratio for gain, ratio in ratios if abs(gain - BASE_GAIN) < 1.0e-12)
    cards = [
        (
            left + 90.0,
            '#173126',
            '#4ade80',
            f'gain {LOW_GAIN:.3f}: ratio ≈ {low_ratio:.1f}x',
            'Making the loop gentler reduces adjacent pull, but it does not make the half-sine lane competitive.',
        ),
        (
            left + 740.0,
            '#341c12',
            '#facc15',
            f'gain {BASE_GAIN:.3f}: ratio ≈ {base_ratio:.1f}x',
            'The original spacing-boundary baseline already captured the same ordering that the full gain sweep keeps repeating.',
        ),
        (
            left + 1390.0,
            '#14263a',
            '#93c5fd',
            'Queue decision',
            'Stop treating this as a tuning-only question. If the queue returns here, it should be for a fresh geometry change or packaging, not more same-shape gain nudging.',
        ),
    ]
    for card_left, fill, stroke, title_text, body in cards:
        svg.append(rounded_rect(card_left, top + 468.0, 560.0, 68.0, fill, stroke, 1.8, 1.0, 16.0))
        svg.append(text(card_left + 18.0, top + 494.0, title_text, 'label'))
        add_wrapped_text(svg, card_left + 18.0, top + 514.0, body, 'tiny', max_width=520.0, font_size=14.0, line_height=18.0)


def build_figure(rows: list[BandEdgeClosedLoopRow]) -> str:
    loss_gain = first_loss_gain(rows, 'gnuradio_half_sine')
    svg: list[str] = [svg_root(WIDTH, HEIGHT)]
    svg.append(
        '<style>'
        '.bg{fill:#07131f;}'
        '.title{font:700 34px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;fill:#e5eef7;}'
        '.subtitle{font:500 18px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;fill:#9fb3c8;}'
        '.label{font:700 20px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;fill:#e5eef7;}'
        '.small{font:500 16px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;fill:#d6e2f0;}'
        '.tiny{font:500 14px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;fill:#c7d6e6;}'
        '</style>'
    )
    svg.append('<rect class="bg" x="0" y="0" width="2140" height="1780" rx="36"/>')
    svg.append(text(60, 68, 'Band-edge loop-gain retuning at 1.24 R_s', 'title'))
    svg.append(text(60, 102, 'One bounded follow-up: same adjacent-channel setup, fixed spacing at the first settle point, sweep loop gain only.', 'subtitle'))
    top_panel(svg, rows, loss_gain)
    residual_panel(svg, rows, loss_gain)
    settle_panel(svg, rows, loss_gain)
    ratio_panel(svg, rows)
    svg.append('</svg>')
    return ''.join(svg)


def main() -> None:
    rows = study_band_edge_closed_loop_gain_sweep(
        LOOP_GAINS,
        adjacent_relative_power_db=ADJACENT_POWER_DB,
        samples_per_symbol=SAMPLES_PER_SYMBOL,
        symbol_count=SYMBOL_COUNT,
        rolloff=ROLLOFF,
        tap_count=TAP_COUNT,
        channel_spacing=CHANNEL_SPACING,
        block_symbols=BLOCK_SYMBOLS,
        tail_block_count=TAIL_BLOCK_COUNT,
        settle_threshold=SETTLE_THRESHOLD,
    )
    write_band_edge_closed_loop_csv(rows, CSV_OUT)
    SVG_OUT.write_text(build_figure(rows), encoding='utf-8')
    export_png_from_svg(SVG_OUT, PNG_OUT, size=1800)


if __name__ == '__main__':
    main()
