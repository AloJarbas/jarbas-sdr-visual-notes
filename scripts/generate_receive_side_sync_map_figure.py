#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from svg_layout import add_wrapped_text, export_png_from_svg, svg_root, text, text_block, wrap_text

REPO = Path(__file__).resolve().parents[1]
SVG_OUT = REPO / 'assets/2026-05-16-receive-side-synchronization-map.svg'
PNG_OUT = REPO / 'assets/2026-05-16-receive-side-synchronization-map.png'

WIDTH = 1920
HEIGHT = 980
BOX_TOP = 214.0
BOX_W = 320.0
BOX_H = 300.0
BOX_GAP = 25.0
LEFT = 50.0
UNRESOLVED_TOP = 548.0
UNRESOLVED_H = 128.0


STAGES = [
    {
        'number': '1',
        'title': 'Pulse shaping + matched filter',
        'question': 'Is the waveform concentrated enough that symbol structure becomes readable?',
        'fixes': [
            'limits bandwidth and concentrates symbol energy',
            'improves SNR at the matched filter output',
            'makes later eye and constellation views meaningful',
        ],
        'output': 'oversampled matched-filter waveform',
        'unresolved': [
            'does not choose the sample instant',
            'does not remove common carrier rotation',
        ],
        'link': 'pulse-shaping-matched-filtering.md',
        'fill': '#11263a',
        'stroke': '#5aa9e6',
        'accent': '#7dd3fc',
    },
    {
        'number': '2',
        'title': 'Timing recovery',
        'question': 'When should the receiver take one useful sample for each symbol?',
        'fixes': [
            'finds the eye opening / symbol center',
            'reduces the stream toward one sample per symbol',
            'shrinks timing error into a smaller residual correction job',
        ],
        'output': 'symbol-rate samples',
        'unresolved': [
            'the sampled constellation can still spin',
            'carrier phase and frequency error remain',
        ],
        'link': 'symbol-timing-and-eye-opening.md',
        'fill': '#142b22',
        'stroke': '#4ade80',
        'accent': '#86efac',
    },
    {
        'number': '3',
        'title': 'Carrier acquisition',
        'question': 'How do we remove the big common rotation before slicing is trustworthy?',
        'fixes': [
            'uses coarse or symmetry-based logic first',
            'gets the QPSK cloud near a usable orientation',
            'shrinks the problem before fine tracking starts',
        ],
        'output': 'coarse derotation, stable modulo 90°',
        'unresolved': [
            'residual phase can still be too large',
            'QPSK quadrant labeling is still ambiguous',
        ],
        'link': 'carrier-recovery-after-timing.md',
        'fill': '#2e2413',
        'stroke': '#f59e0b',
        'accent': '#fbbf24',
    },
    {
        'number': '4',
        'title': 'Lock detection + handoff',
        'question': 'Has acquisition settled enough to trust fine tracking?',
        'fixes': [
            'checks stability and residual error separately',
            'switches from coarse search to near-lock tracking',
            'tells the receiver when decisions are credible',
        ],
        'output': 'near-lock tracked constellation',
        'unresolved': [
            'carrier can look locked while labels are wrong',
            'this is handoff logic, not label resolution',
        ],
        'link': 'carrier-lock-detection-and-handoff.md',
        'fill': '#31182a',
        'stroke': '#f472b6',
        'accent': '#f9a8d4',
    },
    {
        'number': '5',
        'title': 'Ambiguity resolution',
        'question': 'Which QPSK labeling is correct, or how do we stop caring?',
        'fixes': [
            'uses unique words or differential encoding',
            'resolves or sidesteps the final 90° label ambiguity',
            'makes the symbol labels payload-usable',
        ],
        'output': 'stable labeled symbols',
        'unresolved': [
            'does not replace carrier recovery itself',
            'other receive jobs still exist beyond this map',
        ],
        'link': 'qpsk-phase-ambiguity-resolution.md',
        'fill': '#19263a',
        'stroke': '#c084fc',
        'accent': '#d8b4fe',
    },
]

def rect(x: float, y: float, w: float, h: float, fill: str, stroke: str | None = None, stroke_width: float = 0.0, opacity: float = 1.0, rx: float = 18.0) -> str:
    stroke_attr = '' if stroke is None else f' stroke="{stroke}" stroke-width="{stroke_width:.1f}"'
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}" fill="{fill}" opacity="{opacity}"{stroke_attr}/>'


def line(x1: float, y1: float, x2: float, y2: float, stroke: str, width: float = 2.5, opacity: float = 1.0, dash: str | None = None) -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width:.1f}" opacity="{opacity}" stroke-linecap="round"{dash_attr}/>'


def circle(x: float, y: float, r: float, fill: str, stroke: str | None = None, stroke_width: float = 0.0) -> str:
    stroke_attr = '' if stroke is None else f' stroke="{stroke}" stroke-width="{stroke_width:.1f}"'
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}"{stroke_attr}/>'


def arrow(svg: list[str], x1: float, y1: float, x2: float, y2: float, stroke: str) -> None:
    svg.append(line(x1, y1, x2, y2, stroke, 3.0, 0.95))
    for back_y in (-8.0, 8.0):
        svg.append(line(x2, y2, x2 - 14.0, y2 + back_y, stroke, 3.0, 0.95))


def bullet_lines(items: list[str], *, max_width: float, font_size: float) -> list[str]:
    prepared: list[str] = []
    for item in items:
        wrapped = wrap_text(item, max_width=max_width - 18.0, font_size=font_size)
        for idx, line_value in enumerate(wrapped):
            prefix = '• ' if idx == 0 else '  '
            prepared.append(prefix + line_value)
    return prepared


def stage_left(index: int) -> float:
    return LEFT + index * (BOX_W + BOX_GAP)


def chip(svg: list[str], x: float, y: float, label: str, fill: str, stroke: str) -> float:
    width = max(150.0, 16.0 + len(label) * 7.2)
    svg.append(rect(x, y, width, 36.0, fill, stroke, 1.5, 1.0, 18.0))
    svg.append(text(x + width / 2.0, y + 24.0, label, 'chip', 'middle'))
    return width


def draw_stage(svg: list[str], index: int, stage: dict[str, object]) -> None:
    left = stage_left(index)
    center_x = left + BOX_W / 2.0
    fill = str(stage['fill'])
    stroke = str(stage['stroke'])
    accent = str(stage['accent'])

    svg.append(rect(left, BOX_TOP, BOX_W, BOX_H, fill, stroke, 2.2, 1.0, 22.0))
    svg.append(circle(left + 28.0, BOX_TOP + 28.0, 18.0, accent, stroke, 1.6))
    svg.append(text(left + 28.0, BOX_TOP + 34.0, str(stage['number']), 'stage_num', 'middle'))
    add_wrapped_text(svg, left + 58.0, BOX_TOP + 34.0, str(stage['title']), 'stage_title', max_width=BOX_W - 104.0, font_size=19, line_height=22)

    svg.append(text(left + 24.0, BOX_TOP + 82.0, 'Main question', 'section'))
    add_wrapped_text(svg, left + 24.0, BOX_TOP + 106.0, str(stage['question']), 'body', max_width=BOX_W - 86.0, font_size=14, line_height=18)

    svg.append(text(left + 24.0, BOX_TOP + 168.0, 'This stage fixes', 'section'))
    svg.append(text_block(left + 24.0, BOX_TOP + 192.0, bullet_lines(list(stage['fixes']), max_width=BOX_W - 48.0, font_size=14), 'small', 17.0))

    svg.append(rect(left + 18.0, BOX_TOP + BOX_H - 58.0, BOX_W - 36.0, 40.0, '#0b1520', accent, 1.2, 0.95, 14.0))
    add_wrapped_text(svg, left + 32.0, BOX_TOP + BOX_H - 32.0, f"Output: {stage['output']}", 'micro', max_width=BOX_W - 92.0, font_size=12, line_height=15)

    svg.append(rect(left, UNRESOLVED_TOP, BOX_W, UNRESOLVED_H, '#0b1520', stroke, 1.8, 1.0, 20.0))
    svg.append(text(left + 24.0, UNRESOLVED_TOP + 32.0, 'Still unresolved', 'section'))
    svg.append(text_block(left + 24.0, UNRESOLVED_TOP + 58.0, bullet_lines(list(stage['unresolved']), max_width=BOX_W - 48.0, font_size=14), 'small', 17.0))

    svg.append(rect(left + 16.0, 688.0, BOX_W - 32.0, 38.0, '#09111a', stroke, 1.2, 0.9, 14.0))
    add_wrapped_text(svg, left + 28.0, 713.0, f"Deeper note: {stage['link']}", 'micro', max_width=BOX_W - 92.0, font_size=12, line_height=14)

    if index < len(STAGES) - 1:
        x1 = left + BOX_W
        x2 = stage_left(index + 1)
        arrow_y = BOX_TOP + 146.0
        arrow(svg, x1 + 8.0, arrow_y, x2 - 8.0, arrow_y, '#7c93aa')

    if index == 0:
        svg.append(text(center_x, 770.0, 'oversampled waveform', 'state_label', 'middle'))
    elif index == 1:
        svg.append(text(center_x, 770.0, 'one useful sample / symbol', 'state_label', 'middle'))
    elif index == 2:
        svg.append(text(center_x, 770.0, 'coarse derotation', 'state_label', 'middle'))
    elif index == 3:
        svg.append(text(center_x, 770.0, 'track-ready view', 'state_label', 'middle'))
    else:
        svg.append(text(center_x, 770.0, 'stable labeled symbols', 'state_label', 'middle'))


def main() -> None:
    svg: list[str] = [
        svg_root(WIDTH, HEIGHT),
        '<defs>',
        '  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">',
        '    <stop offset="0%" stop-color="#06101a"/>',
        '    <stop offset="100%" stop-color="#0f1d2c"/>',
        '  </linearGradient>',
        '  <style>',
        '    .title { font: 700 34px Helvetica, Arial, sans-serif; fill: #e8eef5; }',
        '    .subtitle { font: 500 18px Helvetica, Arial, sans-serif; fill: #a9bacb; }',
        '    .chip { font: 700 14px Helvetica, Arial, sans-serif; fill: #dce7f3; }',
        '    .stage_num { font: 800 16px Helvetica, Arial, sans-serif; fill: #071018; }',
        '    .stage_title { font: 700 20px Helvetica, Arial, sans-serif; fill: #ebf2f9; }',
        '    .section { font: 700 15px Helvetica, Arial, sans-serif; fill: #eef3f7; }',
        '    .body { font: 500 15px Helvetica, Arial, sans-serif; fill: #c4d2df; }',
        '    .small { font: 500 14px Helvetica, Arial, sans-serif; fill: #b8c7d5; }',
        '    .micro { font: 600 13px Helvetica, Arial, sans-serif; fill: #d7e2ed; }',
        '    .arrowlabel { font: 700 13px Helvetica, Arial, sans-serif; fill: #c8d4e0; }',
        '    .state_label { font: 700 14px Helvetica, Arial, sans-serif; fill: #d7e2ed; }',
        '    .footer { font: 500 16px Helvetica, Arial, sans-serif; fill: #b7c5d3; }',
        '  </style>',
        '</defs>',
        rect(0.0, 0.0, WIDTH, HEIGHT, 'url(#bg)', None, 0.0, 1.0, 0.0),
        text(50.0, 56.0, 'Receive-side synchronization map', 'title'),
        text_block(
            50.0,
            90.0,
            [
                'The clean SDR receive story is not one giant sync block.',
                'Each stage removes one uncertainty and hands a smaller problem to the next stage.',
            ],
            'subtitle',
            24.0,
        ),
    ]

    chip_x = 50.0
    chip_x += chip(svg, chip_x, 132.0, 'QPSK-first public view', '#102033', '#35506a') + 14.0
    chip_x += chip(svg, chip_x, 132.0, 'symbol-rate story after timing', '#13263b', '#4f8cc9') + 14.0
    chip(svg, chip_x, 132.0, 'equalization / packet sync omitted', '#2e2413', '#f59e0b')

    svg.append(line(90.0, 790.0, WIDTH - 90.0, 790.0, '#31465c', 2.0, 0.8, '10 10'))
    add_wrapped_text(
        svg,
        50.0,
        842.0,
        'Read this left to right: make the waveform sample-worthy, choose the sampling instant, remove the big rotation, decide when fine tracking is trustworthy, then resolve the last QPSK label ambiguity.',
        'footer',
        max_width=1520.0,
        font_size=16,
        line_height=22,
    )
    add_wrapped_text(
        svg,
        50.0,
        902.0,
        'Scope boundary: AGC details, equalization, frame sync, and large-CFO front-end recovery stay outside this first symbol-rate map.',
        'footer',
        max_width=1520.0,
        font_size=15,
        line_height=21,
    )

    for index, stage in enumerate(STAGES):
        draw_stage(svg, index, stage)

    svg.append('</svg>')

    SVG_OUT.parent.mkdir(parents=True, exist_ok=True)
    SVG_OUT.write_text('\n'.join(svg) + '\n')
    export_png_from_svg(SVG_OUT, PNG_OUT, size=2200, dpi=300)

    print(f'WROTE {SVG_OUT}')
    print(f'WROTE {PNG_OUT}')


if __name__ == '__main__':
    main()
