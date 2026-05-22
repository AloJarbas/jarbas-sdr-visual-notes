#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from svg_layout import add_wrapped_text, export_png_from_svg, svg_root, text
from waveform_carrier_front_ends import (
    BandEdgeDesignComparisonRow,
    sweep_band_edge_design_comparison,
    write_band_edge_design_comparison_csv,
)

REPO = Path(__file__).resolve().parents[1]
SVG_OUT = REPO / 'assets/2026-05-22-band-edge-filter-design-comparison.svg'
PNG_OUT = REPO / 'assets/2026-05-22-band-edge-filter-design-comparison.png'
CSV_OUT = REPO / 'assets/2026-05-22-band-edge-filter-design-comparison.csv'

WIDTH = 2140
HEIGHT = 1580
SAMPLES_PER_SYMBOL = 4
SYMBOL_COUNT = 1024
SEED = 19
TRIM = 160
ROLLOFFS = [0.05, 0.20, 0.35, 0.50]
TAP_COUNTS = [63, 127, 255]
COLORS = {
    63: '#fda4af',
    127: '#93c5fd',
    255: '#4ade80',
}
DESIGN_LABELS = {
    'proxy_bandpass': 'Current proxy bandpass',
    'gnuradio_half_sine': 'GNU Radio / half-sine style',
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


def row_lookup(rows: list[BandEdgeDesignComparisonRow]) -> dict[tuple[str, int, float], BandEdgeDesignComparisonRow]:
    return {(row.design, row.tap_count, row.rolloff): row for row in rows}


def grouped_rows(rows: list[BandEdgeDesignComparisonRow]) -> dict[str, dict[int, list[BandEdgeDesignComparisonRow]]]:
    grouped: dict[str, dict[int, list[BandEdgeDesignComparisonRow]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[row.design][row.tap_count].append(row)
    return {
        design: {tap_count: sorted(series, key=lambda item: item.rolloff) for tap_count, series in tap_map.items()}
        for design, tap_map in grouped.items()
    }


def draw_chart_frame(svg: list[str], *, left: float, top: float, width: float, height: float, x_min: float, x_max: float, y_min: float, y_max: float, x_ticks: list[float], y_ticks: list[float], x_label: str, y_label: str, target_y: float | None = None, target_label: str | None = None) -> None:
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
        svg.append(text(left - 18.0, y + 4.0, f'{value:.2f}', 'tiny', 'end'))
        if value not in (y_ticks[0], y_ticks[-1]):
            svg.append(line(left, y, left + width, y, '#27415a', 1.0, 0.8, '4 8'))
    if target_y is not None:
        y = axis_y(target_y, top, height, y_min, y_max)
        svg.append(line(left, y, left + width, y, '#facc15', 2.0, 0.85, '8 8'))
        if target_label:
            svg.append(text(left + width - 10.0, y - 10.0, target_label, 'tiny', 'end'))
    svg.append(text(left + width / 2.0, top + height + 58.0, x_label, 'tiny', 'middle'))
    svg.append(text(left - 72.0, top + height / 2.0, y_label, 'tiny', 'middle'))


def top_panel(svg: list[str], rows: list[BandEdgeDesignComparisonRow]) -> None:
    left = 60.0
    top = 150.0
    width = 1860.0
    height = 290.0
    lookup = row_lookup(rows)

    proxy_63 = lookup[('proxy_bandpass', 63, 0.35)].central_slope_wrt_deltaf_over_Rs
    proxy_255 = lookup[('proxy_bandpass', 255, 0.35)].central_slope_wrt_deltaf_over_Rs
    gr_63 = lookup[('gnuradio_half_sine', 63, 0.35)].central_slope_wrt_deltaf_over_Rs
    low_alpha_gr = lookup[('gnuradio_half_sine', 63, 0.05)].central_slope_wrt_deltaf_over_Rs

    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 26.0, top + 42.0, 'The remaining band-edge question was filter shape, not just tap count', 'label'))
    add_wrapped_text(
        svg,
        left + 26.0,
        top + 78.0,
        'The earlier slope note showed that raw imbalance and normalized near-lock slope are different objects. This follow-up checks the next narrower question: does the current boxy proxy understate the normalized slope simply because its filter shape is too crude compared with the GNU Radio / fred harris half-sine construction?',
        'small',
        max_width=1790.0,
        font_size=16.0,
        line_height=21.0,
    )

    cards = [
        (
            left + 28.0,
            '#3a1018',
            '#fda4af',
            'Current proxy really is filter-limited',
            f'At α = 0.35, the 63-tap proxy only reaches slope {proxy_63:.3f}. It does not get close to the normalized target until about 255 taps ({proxy_255:.3f}).',
        ),
        (
            left + 650.0,
            '#11263d',
            '#93c5fd',
            'GNU Radio-style shape fixes most of it fast',
            f'At the same α = 0.35, the 63-tap half-sine style already lands at slope {gr_63:.3f}. That is the practical comparison this pass needed.',
        ),
        (
            left + 1238.0,
            '#142f23',
            '#4ade80',
            'The tiny-roll-off caveat survives',
            f'Even the half-sine design stays soft at α = 0.05 (slope {low_alpha_gr:.3f}). Small excess bandwidth is still a genuinely weaker case, not just a plotting artifact.',
        ),
    ]
    for card_left, fill, stroke, title_text, body in cards:
        svg.append(rounded_rect(card_left, top + 138.0, 590.0, 118.0, fill, stroke, 1.8, 1.0, 16.0))
        svg.append(text(card_left + 18.0, top + 168.0, title_text, 'label'))
        add_wrapped_text(svg, card_left + 18.0, top + 198.0, body, 'tiny', max_width=520.0, font_size=14.0, line_height=18.0)


def design_panel(svg: list[str], rows: list[BandEdgeDesignComparisonRow], *, design: str, left: float, top: float, width: float, height: float) -> None:
    chart_left = left + 100.0
    chart_top = top + 126.0
    chart_width = width - 170.0
    chart_height = 408.0
    grouped = grouped_rows(rows)[design]

    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 24.0, top + 36.0, DESIGN_LABELS[design], 'label'))
    if design == 'proxy_bandpass':
        body = 'Same bounded setup as the previous note, but now plotted explicitly as one design family. It gets the branch intuition right, yet short filters understate the normalized near-lock slope unless the roll-off is large or the tap count is long.'
    else:
        body = 'This uses the GNU Radio / fred harris half-sine style band-edge construction. In the same 4 sps setup it gets much closer to the normalized target slope with modest tap counts, especially once α is at least moderate.'
    add_wrapped_text(svg, left + 24.0, top + 70.0, body, 'small', max_width=width - 110.0, font_size=15.0, line_height=20.0)

    draw_chart_frame(
        svg,
        left=chart_left,
        top=chart_top,
        width=chart_width,
        height=chart_height,
        x_min=0.05,
        x_max=0.50,
        y_min=0.0,
        y_max=1.10,
        x_ticks=ROLLOFFS,
        y_ticks=[0.00, 0.20, 0.40, 0.60, 0.80, 1.00],
        x_label='SRRC roll-off  α',
        y_label='near-lock slope',
        target_y=1.0,
        target_label='slope ≈ 1',
    )

    for tap_count, series in grouped.items():
        points = [
            (axis_x(row.rolloff, chart_left, chart_width, 0.05, 0.50), axis_y(row.central_slope_wrt_deltaf_over_Rs, chart_top, chart_height, 0.0, 1.10))
            for row in series
        ]
        svg.append(polyline(points, COLORS[tap_count], 3.0))
        for x, y in points:
            svg.append(circle(x, y, 5.0, COLORS[tap_count]))

    legend_left = left + 24.0
    legend_top = top + 572.0
    svg.append(rounded_rect(legend_left, legend_top, 292.0, 78.0, '#13263b', '#4f8cc9', 1.4, 1.0, 12.0))
    for idx, tap_count in enumerate(TAP_COUNTS):
        y = legend_top + 26.0 + idx * 18.0
        svg.append(circle(legend_left + 18.0, y - 4.0, 5.0, COLORS[tap_count]))
        svg.append(text(legend_left + 32.0, y, f'{tap_count}-tap filters', 'tiny'))


def bottom_panel(svg: list[str], rows: list[BandEdgeDesignComparisonRow]) -> None:
    left = 60.0
    top = 1160.0
    width = 1860.0
    height = 360.0
    lookup = row_lookup(rows)
    proxy = lookup[('proxy_bandpass', 63, 0.20)].central_slope_wrt_deltaf_over_Rs
    gr = lookup[('gnuradio_half_sine', 63, 0.20)].central_slope_wrt_deltaf_over_Rs
    ratio = gr / max(proxy, 1.0e-9)

    svg.append(rounded_rect(left, top, width, height, '#102031', '#5d7fa3', 2.0))
    svg.append(text(left + 24.0, top + 36.0, 'What this changes in the repo', 'label'))
    add_wrapped_text(
        svg,
        left + 24.0,
        top + 70.0,
        'The repo can now say something tighter than before. The previous raw-imbalance note remains the intuition view. The 2026-05-20 slope note remains the calibration correction. This pass closes the next loophole by showing that the current proxy filter shape itself is responsible for much of the remaining moderate-roll-off underestimation.',
        'small',
        max_width=1620.0,
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
                'The raw band-edge imbalance panel still belongs in the repo as the first intuition picture.',
                'The small-roll-off case remains genuinely weak even after the filter shape gets better.',
            ],
        ),
        (
            left + 646.0,
            '#173126',
            '#4ade80',
            'New claim',
            [
                f'At α = 0.20 and 63 taps, the half-sine style reaches {gr:.3f} versus {proxy:.3f} for the proxy — about {ratio:.1f}× more near-lock slope in this bounded setup.',
                'So the next public wording should stop treating the old proxy as if it were already a faithful band-edge implementation.',
            ],
        ),
        (
            left + 1228.0,
            '#341c12',
            '#facc15',
            'Next bounded move',
            [
                'If SDR gets one more turn, measure the guardband / adjacent-channel cost of the wider half-sine design instead of repeating more slope sweeps.',
                'Otherwise this branch is honest enough to stop and the queue can move on.',
            ],
        ),
    ]
    for column_left, fill, stroke, title_text, bullets in columns:
        svg.append(rounded_rect(column_left, top + 126.0, 568.0, 182.0, fill, stroke, 1.8, 1.0, 16.0))
        svg.append(text(column_left + 18.0, top + 158.0, title_text, 'label'))
        for idx, bullet in enumerate(bullets):
            y = top + 198.0 + idx * 74.0
            svg.append(circle(column_left + 20.0, y - 4.0, 4.5, stroke))
            add_wrapped_text(svg, column_left + 36.0, y, bullet, 'tiny', max_width=472.0, font_size=14.0, line_height=18.0)


def build_svg(rows: list[BandEdgeDesignComparisonRow]) -> str:
    svg: list[str] = [
        svg_root(WIDTH, HEIGHT),
        '<defs><style>'
        '.title { fill: #e6eef8; font: 700 38px Arial, sans-serif; }'
        '.subtitle { fill: #c8d8ea; font: 400 20px Arial, sans-serif; }'
        '.label { fill: #eef4fb; font: 700 24px Arial, sans-serif; }'
        '.small { fill: #d4e1ef; font: 400 17px Arial, sans-serif; }'
        '.tiny { fill: #d8e4f0; font: 400 14px Arial, sans-serif; }'
        '</style></defs>',
        '<rect width="100%" height="100%" fill="#08111c"/>',
        text(60.0, 72.0, 'Band-edge filter design comparison', 'title'),
        text(60.0, 108.0, 'A bounded 4 sps check: the GNU Radio / half-sine shape reaches the normalized slope target much sooner than the current proxy, while α = 0.05 still stays soft.', 'subtitle'),
    ]
    top_panel(svg, rows)
    design_panel(svg, rows, design='proxy_bandpass', left=60.0, top=480.0, width=900.0, height=660.0)
    design_panel(svg, rows, design='gnuradio_half_sine', left=990.0, top=480.0, width=900.0, height=660.0)
    bottom_panel(svg, rows)
    svg.append('</svg>')
    return '\n'.join(svg) + '\n'


def main() -> None:
    rows = sweep_band_edge_design_comparison(
        ROLLOFFS,
        TAP_COUNTS,
        samples_per_symbol=SAMPLES_PER_SYMBOL,
        symbol_count=SYMBOL_COUNT,
        seed=SEED,
        trim=TRIM,
        normalized_cfo_step=0.01,
        reference_cfo=0.10,
    )
    write_band_edge_design_comparison_csv(rows, CSV_OUT)
    SVG_OUT.write_text(build_svg(rows))
    export_png_from_svg(SVG_OUT, PNG_OUT, size=2200)
    print(f'wrote {SVG_OUT.relative_to(REPO)}')
    print(f'wrote {PNG_OUT.relative_to(REPO)}')
    print(f'wrote {CSV_OUT.relative_to(REPO)}')


if __name__ == '__main__':
    main()
