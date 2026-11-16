#!/usr/bin/env python3
"""Build a native, editable PowerPoint deck from slides/lecture.md.

Marp's --pptx output renders every slide as a picture. This script rebuilds the deck from the
Markdown with real PowerPoint text boxes, tables and shapes in the style of slides/themes/aica.css,
and copies the speaker notes. It understands the Markdown subset the deck uses: headings,
paragraphs, bullet/numbered lists, tables, blockquotes, fenced code, the `cols` and `cards` HTML
blocks, and the Marp `header`, `class` and `paginate` directives.

Usage:  python scripts/build_editable_pptx.py [slides/lecture.md] [dist/lecture-editable.pptx]
Needs:  pip install -r scripts/requirements-slides.txt   (Pillow measures text so layouts fit)
"""
from __future__ import annotations

import html
import os
import re
import sys
import uuid
from pathlib import Path

from lxml import etree
from PIL import ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.oxml.ns import qn
from pptx.util import Pt

ROOT = Path(__file__).resolve().parents[1]

# Design tokens, in points (slide is 960 x 540 pt = 1280 x 720 px).
BLUE, TEAL, TEAL_TXT = '0078D4', '14B8A6', '0E8F82'
PURPLE, AMBER, AMBER_TXT = '7454B7', 'D98E04', 'B26A00'
NAVY, SLATE, GRAY = '0B1730', '33465C', '5C6B7C'
CARD, PANEL, LINE, ROWLINE, CODEBG, WHITE = 'F7FAFD', 'EAF3FB', 'C9DAEA', 'E3ECF5', 'EEF3F8', 'FFFFFF'
STRIPES = [(BLUE, BLUE), (TEAL, TEAL_TXT), (PURPLE, PURPLE), (AMBER, AMBER_TXT)]  # (stripe, label text)
BODY, DISPLAY, MONO = 'Aptos', 'Aptos Display', 'Consolas'
W, H, MX = 960, 540, 40
CW = W - 2 * MX
FOOT_Y, CONTENT_BOTTOM = 510, 498
LS = 1.2      # default line spacing multiple
SAFE = 0.96   # measure against a slightly narrower box so PowerPoint never wraps more than we planned
BR = '\n'


def emu(pt: float) -> int:
    return int(round(pt * 12700))


def rgb(hex_: str) -> RGBColor:
    return RGBColor.from_string(hex_)


# --------------------------------------------------------------------------- text measurement
class Metrics:
    """Measures text with the real font files (falls back to similar fonts, then to an estimate)."""

    FALLBACK = {
        BODY: ['Aptos', 'Segoe UI', 'Arial', 'DejaVu Sans'],
        DISPLAY: ['Aptos Display', 'Aptos', 'Segoe UI', 'Arial', 'DejaVu Sans'],
        MONO: ['Consolas', 'Cascadia Mono', 'Courier New', 'DejaVu Sans Mono'],
    }

    def __init__(self) -> None:
        self.files: dict[tuple[str, str], str] = {}
        self.cache: dict[tuple, ImageFont.FreeTypeFont | None] = {}
        local = Path(os.environ.get('LOCALAPPDATA', Path.home()))
        dirs = [local / 'Microsoft/FontCache/4/CloudFonts',          # Office cloud fonts (Aptos)
                Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts',
                local / 'Microsoft/Windows/Fonts',
                Path('/Library/Fonts'), Path.home() / 'Library/Fonts', Path('/usr/share/fonts')]
        for d in dirs:
            if not d.is_dir():
                continue
            for f in d.rglob('*'):
                if f.suffix.lower() not in ('.ttf', '.otf', '.ttc'):
                    continue
                try:
                    fam, style = ImageFont.truetype(str(f), 12).getname()
                except Exception:
                    continue
                self.files.setdefault((fam, style), str(f))

    def font(self, family: str, bold: bool, italic: bool):
        key = (family, bold, italic)
        if key not in self.cache:
            want = (('Bold ' if bold else '') + ('Italic' if italic else '')).strip() or 'Regular'
            found = None
            for fam in self.FALLBACK.get(family, [family]):
                for style in (want, 'Bold' if bold else 'Regular', 'Regular'):
                    if (fam, style) in self.files:
                        found = ImageFont.truetype(self.files[(fam, style)], 200)
                        break
                if found:
                    break
            self.cache[key] = found
        return self.cache[key]

    def width(self, text: str, family: str, size: float, bold=False, italic=False) -> float:
        f = self.font(family, bold, italic)
        if f is None:
            return len(text) * size * (0.6 if family == MONO else 0.53)
        return f.getlength(text) * size / 200


# --------------------------------------------------------------------------- inline Markdown
class Run:
    __slots__ = ('text', 'bold', 'italic', 'code', 'color', 'link')

    def __init__(self, text, bold=False, italic=False, code=False, color=None, link=None):
        self.text, self.bold, self.italic, self.code, self.color, self.link = text, bold, italic, code, color, link


INLINE = re.compile(r'(`[^`]+`|<code>.*?</code>|\*\*|\*|<span class="muted">|</span>'
                    r'|</?(?:b|strong|i|em)>|<br\s*/?>|\n)')
EMAIL = re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+\w')


def parse_inline(s: str) -> list[Run]:
    out: list[Run] = []
    bold = italic = False
    colors: list[str | None] = [None]
    for part in INLINE.split(s):
        if not part:
            continue
        if len(part) > 1 and part[0] == part[-1] == '`':
            out.append(Run(part[1:-1], bold, italic, code=True))
        elif part.startswith('<code>'):
            out.append(Run(html.unescape(part[6:-7]), bold, italic, code=True))
        elif part == '**':
            bold = not bold
        elif part == '*':
            italic = not italic
        elif part in ('<b>', '<strong>', '</b>', '</strong>'):
            bold = not part.startswith('</')
        elif part in ('<i>', '<em>', '</i>', '</em>'):
            italic = not part.startswith('</')
        elif part == '<span class="muted">':
            colors.append(GRAY)
        elif part == '</span>':
            if len(colors) > 1:
                colors.pop()
        elif part == BR or part.startswith('<br'):
            out.append(Run(BR))
        else:
            text, pos = html.unescape(part), 0
            for m in EMAIL.finditer(text):
                if m.start() > pos:
                    out.append(Run(text[pos:m.start()], bold, italic, color=colors[-1]))
                out.append(Run(m.group(), bold, italic, link='mailto:' + m.group()))
                pos = m.end()
            if pos < len(text):
                out.append(Run(text[pos:], bold, italic, color=colors[-1]))
    return out


# --------------------------------------------------------------------------- block Markdown
LIST_RE = re.compile(r'^(\s*)([-*]|(\d+)\.)\s+(.*)$')


def split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip('|').split('|')]


def parse_blocks(lines: list[str]) -> list[dict]:
    blocks: list[dict] = []
    i, n = 0, len(lines)

    def starts_block(line: str) -> bool:
        s = line.strip()
        return not s or s.startswith(('```', '#', '|', '>', '<div', '</div')) or bool(LIST_RE.match(line))

    while i < n:
        line, s = lines[i], lines[i].strip()
        if not s:
            i += 1
        elif s.startswith('```'):
            j, body = i + 1, []
            while j < n and not lines[j].strip().startswith('```'):
                body.append(lines[j].rstrip())
                j += 1
            blocks.append({'t': 'code', 'lines': body})
            i = j + 1
        elif s == '<div class="cols">':
            cols, cur, depth, i = [], None, 0, i + 1
            while i < n:
                t = lines[i].strip()
                i += 1
                if t == '<div>':
                    depth += 1
                    if depth == 1:
                        cur = []
                        continue
                elif t == '</div>':
                    if depth == 0:
                        break
                    depth -= 1
                    if depth == 0:
                        cols.append(parse_blocks(cur))
                        cur = None
                        continue
                if cur is not None:
                    cur.append(lines[i - 1])
            blocks.append({'t': 'cols', 'cols': cols})
        elif s == '<div class="cards">':
            j, items = i + 1, []
            while j < n and lines[j].strip() != '</div>':
                m = re.search(r'<span class="label">(.*?)</span><b>(.*?)</b><p>(.*?)</p>', lines[j])
                if m:
                    items.append(m.groups())
                j += 1
            blocks.append({'t': 'cards', 'items': items})
            i = j + 1
        elif s.startswith(('<div', '</div')):
            i += 1
        elif s.startswith('#'):
            m = re.match(r'^(#+)\s+(.*)$', s)
            blocks.append({'t': 'h', 'level': len(m.group(1)), 'text': m.group(2)})
            i += 1
        elif s.startswith('|'):
            rows = []
            while i < n and lines[i].strip().startswith('|'):
                rows.append(split_row(lines[i]))
                i += 1
            align = ['c' if c.startswith(':') and c.endswith(':') else 'r' if c.endswith(':') else 'l'
                     for c in rows[1]]
            blocks.append({'t': 'table', 'head': rows[0], 'rows': rows[2:], 'align': align})
        elif s.startswith('>'):
            buf = []
            while i < n and lines[i].strip().startswith('>'):
                buf.append(re.sub(r'^\s*>\s?', '', lines[i]))
                i += 1
            blocks.append({'t': 'quote', 'paras': [p for p in '\n'.join(buf).split('\n\n') if p.strip()]})
        elif LIST_RE.match(line):
            items = []
            while i < n and lines[i].strip():
                m = LIST_RE.match(lines[i])
                if m:
                    items.append({'level': 0 if len(m.group(1)) < 2 else 1,
                                  'num': int(m.group(3)) if m.group(3) else None, 'text': m.group(4)})
                elif items:
                    items[-1]['text'] += BR + lines[i].strip()   # Marp renders soft breaks as <br>
                i += 1
            blocks.append({'t': 'list', 'items': items})
        else:
            buf = []
            while i < n and not starts_block(lines[i]):
                buf.append(lines[i].strip())
                i += 1
            blocks.append({'t': 'p', 'text': BR.join(buf)})
    return blocks


def parse_deck(text: str) -> tuple[dict, list[dict]]:
    text = text.replace('\r\n', '\n')
    m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    front = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(':')
        front[k.strip()] = v.strip().strip('"\'')
    chunks, cur, fence = [], [], False
    for line in text[m.end():].split('\n'):
        if line.strip().startswith('```'):
            fence = not fence
        if line.strip() == '---' and not fence:
            chunks.append(cur)
            cur = []
        else:
            cur.append(line)
    chunks.append(cur)

    glob = {'header': front.get('header', ''), 'footer': front.get('footer', ''),
            'class': front.get('class', ''), 'paginate': front.get('paginate', 'false')}
    slides = []
    for chunk in chunks:
        local, notes = {}, []

        def grab(mm):
            c = mm.group(1).strip()
            d = re.match(r'^(_?)(header|footer|class|paginate)\s*:\s*(.*)$', c, re.S)
            if d:
                (local if d.group(1) else glob)[d.group(2)] = d.group(3).strip().strip('"\'')
            else:
                notes.append(c)
            return ''

        src = re.sub(r'<!--(.*?)-->', grab, '\n'.join(chunk), flags=re.S)
        if not src.strip() and not notes:
            continue
        slides.append({**glob, **local, 'blocks': parse_blocks(src.split('\n')), 'notes': '\n\n'.join(notes)})
    return front, slides


# --------------------------------------------------------------------------- rendering primitives
# A "para" is a dict: runs, size, plus optional family, bold, italic, color, strong_color, caps,
# spc (letter spacing, pt), ls (line spacing multiple), after (space after, pt), align,
# bullet ('dot' | 'num'), level, marL, hang, start, nohl (no highlight on inline code).

class Deck:
    def __init__(self, metrics: Metrics, front: dict):
        self.m = metrics
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = emu(W), emu(H)
        self.layout = next(l for l in self.prs.slide_layouts if l.name == 'Title Only')
        self.prs.core_properties.title = front.get('title', '')
        self.prs.core_properties.subject = front.get('description', '')
        self.patch_theme()
        self.warnings: list[str] = []

    def patch_theme(self) -> None:
        """Theme fonts and colors, so new text and hyperlinks typed in PowerPoint match the deck."""
        part = self.prs.slide_master.part.part_related_by(RT.THEME)
        xml = part.blob
        xml = re.sub(rb'(<a:majorFont>\s*<a:latin typeface=")[^"]*', rb'\g<1>Aptos Display', xml)
        xml = re.sub(rb'(<a:minorFont>\s*<a:latin typeface=")[^"]*', rb'\g<1>Aptos', xml)
        for tag, val in ((b'dk2', NAVY), (b'accent1', BLUE), (b'accent2', TEAL), (b'accent3', PURPLE),
                         (b'accent4', AMBER), (b'hlink', BLUE)):
            xml = re.sub(rb'(<a:' + tag + rb'>\s*<a:srgbClr val=")[0-9A-Fa-f]{6}', rb'\g<1>' + val.encode(), xml)
        part._blob = xml

    # ---- measurement
    @staticmethod
    def run_font(r: Run, p: dict):
        if r.code:
            return MONO, p['size'] * 0.9, r.bold or p.get('bold', False), False
        return p.get('family', BODY), p['size'], r.bold or p.get('bold', False), r.italic or p.get('italic', False)

    def words(self, p: dict) -> list:
        """Unbreakable words as [width, trailing-space width], with BR markers."""
        out, cur = [], None
        for r in p['runs']:
            if r.text == BR:
                if cur:
                    out.append(cur)
                cur = None
                out.append(BR)
                continue
            fam, size, b, it = self.run_font(r, p)
            text = r.text.upper() if p.get('caps') else r.text
            for seg in re.findall(r'\S+|\s+', text):
                w = self.m.width(seg, fam, size, b, it) + p.get('spc', 0) * len(seg)
                if seg.isspace():
                    if cur:
                        cur[1] += w
                        out.append(cur)
                        cur = None
                    elif out and out[-1] != BR:
                        out[-1][1] += w
                else:
                    cur = cur or [0.0, 0.0]
                    cur[0] += w
        if cur:
            out.append(cur)
        return out

    def wrap(self, p: dict, width: float) -> tuple[int, float, float]:
        """(line count, widest line, widest word) for a paragraph wrapped at width."""
        lines, x, widest, word = 1, 0.0, 0.0, 0.0
        for wd in self.words(p):
            if wd == BR:
                widest, lines, x = max(widest, x), lines + 1, 0.0
                continue
            w, s = wd
            word = max(word, w)
            if x > 0 and x + w > width:
                widest, lines, x = max(widest, x), lines + 1, 0.0
            x += w + s
        return lines, max(widest, x), word

    def height(self, paras: list[dict], width: float) -> float:
        h = 0.0
        for k, p in enumerate(paras):
            lines = self.wrap(p, (width - p.get('marL', 0)) * SAFE)[0]
            h += lines * p['size'] * p.get('ls', LS)
            if k < len(paras) - 1:
                h += p.get('after', 0)
        return h

    # ---- writing text
    def write(self, tf, paras: list[dict], insets=(0, 0, 0, 0), anchor=MSO_ANCHOR.TOP) -> None:
        tf.word_wrap = True
        tf.auto_size = MSO_AUTO_SIZE.NONE
        tf.vertical_anchor = anchor
        if insets is not None:
            tf.margin_left, tf.margin_right, tf.margin_top, tf.margin_bottom = (emu(v) for v in insets)
        for k, p in enumerate(paras):
            para = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
            para.line_spacing = Pt(p['size'] * p.get('ls', LS))
            para.space_before = Pt(0)
            para.space_after = Pt(p.get('after', 0) if k < len(paras) - 1 else 0)
            para.alignment = {'l': PP_ALIGN.LEFT, 'r': PP_ALIGN.RIGHT, 'c': PP_ALIGN.CENTER}[p.get('align', 'l')]
            pPr = para._p.get_or_add_pPr()
            if p.get('bullet'):
                pPr.set('marL', str(emu(p['marL'])))
                pPr.set('indent', str(-emu(p['hang'])))
                pPr.set('lvl', str(p.get('level', 0)))
                clr = etree.SubElement(pPr, qn('a:buClr'))
                etree.SubElement(clr, qn('a:srgbClr'), val=BLUE)
                if p['bullet'] == 'num':
                    etree.SubElement(pPr, qn('a:buFont'), typeface=BODY)
                    num = etree.SubElement(pPr, qn('a:buAutoNum'), type='arabicPeriod')
                    if p.get('start', 1) != 1:
                        num.set('startAt', str(p['start']))
                else:
                    etree.SubElement(pPr, qn('a:buFont'), typeface='Arial')
                    etree.SubElement(pPr, qn('a:buChar'), char='•' if p.get('level', 0) == 0 else '–')
            else:
                pPr.set('marL', '0')
                pPr.set('indent', '0')
                etree.SubElement(pPr, qn('a:buNone'))
            for r in p['runs']:
                if r.text == BR:
                    para.add_line_break()
                else:
                    run = para.add_run()
                    run.text = r.text
                    self.style(run, r, p)
            etree.SubElement(para._p, qn('a:endParaRPr'), lang='en-US', sz=str(int(p['size'] * 100)))

    def style(self, run, r: Run, p: dict) -> None:
        fam, size, b, it = self.run_font(r, p)
        f = run.font
        f.name, f.size, f.bold, f.italic = fam, Pt(size), b, it
        color = (r.color or (BLUE if r.link else None) or (NAVY if r.code else None)
                 or (p.get('strong_color', NAVY) if r.bold else None) or p.get('color', SLATE))
        f.color.rgb = rgb(color)
        rPr = run._r.get_or_add_rPr()
        if p.get('caps'):
            rPr.set('cap', 'all')
        if p.get('spc'):
            rPr.set('spc', str(int(p['spc'] * 100)))
        if r.code and not p.get('nohl'):
            hl = etree.Element(qn('a:highlight'))
            etree.SubElement(hl, qn('a:srgbClr'), val=CODEBG)
            rPr.find(qn('a:latin')).addprevious(hl)
        if r.link:
            run.hyperlink.address = r.link
            f.underline = False

    # ---- shapes
    def rect(self, slide, x, y, w, h, fill):
        s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, emu(x), emu(y), emu(w), emu(h))
        s.fill.solid()
        s.fill.fore_color.rgb = rgb(fill)
        s.line.fill.background()
        s.shadow.inherit = False
        return s

    def card(self, slide, x, y, w, h, fill, stripe=None, radius=5.0, line=LINE):
        s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, emu(x), emu(y), emu(w), emu(h))
        s.adjustments[0] = min(0.5, radius / min(w, h))
        s.fill.solid()
        s.fill.fore_color.rgb = rgb(fill)
        s.line.color.rgb = rgb(line)
        s.line.width = Pt(0.75)
        s.shadow.inherit = False
        if stripe:
            self.rect(slide, x, y, 5, h, stripe)
        return s

    def textbox(self, slide, x, y, w, h, paras, anchor=MSO_ANCHOR.TOP):
        tb = slide.shapes.add_textbox(emu(x), emu(y), emu(w), emu(max(h, 1)))
        self.write(tb.text_frame, paras, anchor=anchor)
        return tb
    # ---- block layout. Each place_* returns the block height; draw=False only measures.
    @staticmethod
    def styles(small: bool, scale: float) -> dict:
        body = (15 if small else 18.5) * scale
        return {'body': body, 'table': body * 0.78, 'code': body * 0.74, 'gap': body * 0.55}

    def text_paras(self, blocks: list[dict], st: dict) -> list[dict]:
        size, paras = st['body'], []
        for b in blocks:
            if b['t'] == 'p':
                paras.append({'runs': parse_inline(b['text']), 'size': size, 'after': st['gap']})
            elif b['t'] == 'h':
                paras.append({'runs': parse_inline(b['text']), 'size': size * 1.1, 'bold': True,
                              'color': NAVY, 'after': st['gap'] * 0.6})
            elif b['t'] == 'list':
                ordered = b['items'][0]['num'] is not None
                outer = size * (1.5 if ordered else 1.1)
                first = True
                for it in b['items']:
                    num = it['num'] is not None
                    hang = size * (1.5 if num else 1.1)
                    p = {'runs': parse_inline(it['text']), 'size': size, 'after': size * 0.18,
                         'bullet': 'num' if num else 'dot', 'level': it['level'], 'hang': hang,
                         'marL': hang if it['level'] == 0 else outer + hang}
                    if num and first:
                        p['start'], first = it['num'], False
                    paras.append(p)
                paras[-1]['after'] = st['gap']
        return paras

    def flow(self, slide, blocks, x, y, w, st, draw) -> float:
        groups: list[list] = []
        for b in blocks:
            if b['t'] in ('p', 'list', 'h'):
                if groups and groups[-1][0] == 'text':
                    groups[-1][1].append(b)
                else:
                    groups.append(['text', [b]])
            else:
                groups.append([b['t'], b])
        y0 = y
        for k, (kind, b) in enumerate(groups):
            if kind == 'quote' and k:
                y += st['gap'] * 0.3
            y += getattr(self, 'place_' + kind)(slide, b, x, y, w, st, draw)
            if k < len(groups) - 1:
                y += st['gap'] * (1.0 if kind == 'text' else 1.2)
        return y - y0

    def place_text(self, slide, blocks, x, y, w, st, draw):
        paras = self.text_paras(blocks, st)
        h = self.height(paras, w)
        if draw:
            self.textbox(slide, x, y, w, h + 2, paras)
        return h

    def place_quote(self, slide, b, x, y, w, st, draw):
        paras = [{'runs': parse_inline(t), 'size': st['body'], 'color': NAVY, 'after': st['gap'] * 0.5}
                 for t in b['paras']]
        pad = (18, 12, 9, 9)
        h = self.height(paras, w - pad[0] - pad[1]) + pad[2] + pad[3]
        if draw:
            shp = self.card(slide, x, y, w, h, PANEL)
            self.write(shp.text_frame, paras, insets=pad, anchor=MSO_ANCHOR.MIDDLE)
            self.rect(slide, x, y, 5, h, BLUE)
        return h

    def place_code(self, slide, b, x, y, w, st, draw):
        lines, size, pad = b['lines'] or [''], st['code'], (12, 12, 9, 9)
        widest = max(self.m.width(l, MONO, size) for l in lines)
        if widest > (w - pad[0] - pad[1]) * SAFE:
            size *= (w - pad[0] - pad[1]) * SAFE / widest
        paras = [{'runs': [Run(l or ' ')], 'size': size, 'family': MONO, 'color': NAVY, 'ls': 1.25}
                 for l in lines]
        h = len(lines) * size * 1.25 + pad[2] + pad[3]
        if draw:
            shp = self.card(slide, x, y, w, h, WHITE, radius=6)
            self.write(shp.text_frame, paras, insets=pad)
        return h

    def place_table(self, slide, b, x, y, w, st, draw):
        size, ins = st['table'], (8, 8, 4.5, 4.5)
        ncol = len(b['head'])

        def cell(text, header, j):
            if header:
                return {'runs': parse_inline(text), 'size': size * 0.82, 'bold': True, 'caps': True,
                        'spc': 0.3, 'color': BLUE, 'strong_color': BLUE, 'align': b['align'][j]}
            return {'runs': parse_inline(text), 'size': size, 'color': SLATE, 'align': b['align'][j]}

        grid = [[cell(t, True, j) for j, t in enumerate(b['head'])]]
        grid += [[cell(r[j] if j < len(r) else '', False, j) for j in range(ncol)] for r in b['rows']]
        nat = [max(self.wrap(row[j], 1e9)[1] for row in grid) + ins[0] + ins[1] + 2 for j in range(ncol)]
        low = [max(self.wrap(row[j], 1e9)[2] for row in grid) + ins[0] + ins[1] + 2 for j in range(ncol)]
        if sum(nat) <= w:
            widths = [n * w / sum(nat) for n in nat]
        else:
            slack = [n - m for n, m in zip(nat, low)]
            widths = [m + (w - sum(low)) * s / (sum(slack) or 1) for m, s in zip(low, slack)]
        heights = [max(self.height([row[j]], widths[j] - ins[0] - ins[1]) for j in range(ncol)) + ins[2] + ins[3]
                   for row in grid]
        h = sum(heights)
        if draw:
            tbl = slide.shapes.add_table(len(grid), ncol, emu(x), emu(y), emu(w), emu(h)).table
            tbl.first_row = tbl.horz_banding = False
            for j, cw in enumerate(widths):
                tbl.columns[j].width = emu(cw)
            last = len(grid) - 1
            for i, row in enumerate(grid):
                tbl.rows[i].height = emu(heights[i])
                for j, p in enumerate(row):
                    c = tbl.cell(i, j)
                    self.cell_style(c, PANEL if i == 0 else CARD,
                                    top=LINE if i <= 1 else ROWLINE, bottom=LINE if i in (0, last) else ROWLINE,
                                    left=LINE if j == 0 else None, right=LINE if j == ncol - 1 else None)
                    c.margin_left, c.margin_right, c.margin_top, c.margin_bottom = (emu(v) for v in ins)
                    c.vertical_anchor = MSO_ANCHOR.TOP
                    self.write(c.text_frame, [p], insets=None)
        return h

    @staticmethod
    def cell_style(cell, fill, top, bottom, left, right) -> None:
        tcPr = cell._tc.get_or_add_tcPr()
        for child in list(tcPr):
            tcPr.remove(child)
        for tag, col in (('a:lnL', left), ('a:lnR', right), ('a:lnT', top), ('a:lnB', bottom)):
            ln = etree.SubElement(tcPr, qn(tag), w=str(emu(0.75) if col else 0))
            if col:
                etree.SubElement(etree.SubElement(ln, qn('a:solidFill')), qn('a:srgbClr'), val=col)
            else:
                etree.SubElement(ln, qn('a:noFill'))
        etree.SubElement(etree.SubElement(tcPr, qn('a:solidFill')), qn('a:srgbClr'), val=fill)

    def place_cols(self, slide, b, x, y, w, st, draw):
        cols, gap, pad = b['cols'], 16, (18, 13, 11, 9)
        cw = (w - gap * (len(cols) - 1)) / len(cols)
        inner = cw - pad[0] - pad[1]
        h = max(self.flow(None, c, 0, 0, inner, st, False) for c in cols) + pad[2] + pad[3]
        if draw:
            for k, c in enumerate(cols):
                cx = x + k * (cw + gap)
                self.card(slide, cx, y, cw, h, CARD, STRIPES[k % 4][0])
                self.flow(slide, c, cx + pad[0], y + pad[2], inner, st, True)
        return h

    def place_cards(self, slide, b, x, y, w, st, draw):
        items, gap, pad = b['items'], 16, (16, 11, 10, 11)
        cw = (w - gap * (len(items) - 1)) / len(items)

        def paras(k, label, title, body):
            return [{'runs': parse_inline(label), 'size': 8.5, 'bold': True, 'caps': True, 'spc': 0.4,
                     'color': STRIPES[k % 4][1], 'after': 3},
                    {'runs': parse_inline(title), 'size': 15, 'bold': True, 'color': NAVY, 'after': 4},
                    {'runs': parse_inline(body), 'size': 11.25, 'color': SLATE, 'ls': 1.3}]

        h = max(self.height(paras(k, *it), cw - pad[0] - pad[1]) for k, it in enumerate(items)) + pad[2] + pad[3]
        if draw:
            for k, it in enumerate(items):
                cx = x + k * (cw + gap)
                shp = self.card(slide, cx, y, cw, h, CARD)
                self.write(shp.text_frame, paras(k, *it), insets=pad)
                self.rect(slide, cx, y, 5, h, STRIPES[k % 4][0])
        return h
    # ---- slides
    def chrome(self, slide, sd: dict, number: int, lead: bool) -> None:
        self.rect(slide, 0, 0, W, 10, BLUE)
        if sd.get('header'):
            self.textbox(slide, MX, 93 if lead else 24, CW, 14,
                         [{'runs': parse_inline(sd['header']), 'size': 10, 'bold': True, 'caps': True,
                           'spc': 0.4, 'color': BLUE}])
        self.rect(slide, MX, FOOT_Y, CW, 0.75, LINE)
        if sd.get('footer'):
            self.textbox(slide, MX, FOOT_Y + 5, 600, 12,
                         [{'runs': parse_inline(sd['footer']), 'size': 8, 'color': GRAY}])
        if str(sd.get('paginate')).lower() == 'true':
            tb = slide.shapes.add_textbox(emu(W - MX - 100), emu(FOOT_Y + 4), emu(100), emu(13))
            tf = tb.text_frame
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
            para = tf.paragraphs[0]
            para.alignment = PP_ALIGN.RIGHT
            fld = etree.SubElement(para._p, qn('a:fld'), id='{%s}' % str(uuid.uuid4()).upper(), type='slidenum')
            rPr = etree.SubElement(fld, qn('a:rPr'), lang='en-US', sz='900')
            etree.SubElement(etree.SubElement(rPr, qn('a:solidFill')), qn('a:srgbClr'), val=GRAY)
            etree.SubElement(rPr, qn('a:latin'), typeface=BODY)
            etree.SubElement(fld, qn('a:t')).text = str(number)

    def title(self, slide, text: str, x, y, size: float) -> float:
        p = {'runs': parse_inline(text), 'size': size, 'bold': True, 'family': DISPLAY, 'color': NAVY,
             'strong_color': BLUE, 'ls': 1.12}
        h = self.height([p], CW)
        ph = slide.shapes.title
        ph.left, ph.top, ph.width, ph.height = emu(x), emu(y), emu(CW), emu(h + 2)
        self.write(ph.text_frame, [p])
        return h

    def render_lead(self, slide, blocks: list[dict]) -> None:
        y = 112
        for b in blocks:
            if b['t'] == 'h' and b['level'] == 1:
                y += self.title(slide, b['text'], MX, y, 45)
                self.rect(slide, MX, y + 12, 37.5, 5.25, BLUE)
                y += 12 + 5.25 + 15
            elif b['t'] == 'h':
                big = b['level'] == 2
                p = {'runs': parse_inline(b['text']), 'size': 20 if big else 13.5, 'color': SLATE if big else GRAY,
                     'strong_color': NAVY, 'ls': 1.25}
                h = self.height([p], CW)
                self.textbox(slide, MX, y, CW, h + 2, [p])
                y += h + (8 if big else 10)
            elif b['t'] == 'p' and re.fullmatch(r'`[^`]+`', b['text']):
                label = b['text'][1:-1]
                p = {'runs': [Run(label)], 'size': 10, 'bold': True, 'color': BLUE, 'align': 'c'}
                w = self.m.width(label, BODY, 10, True) + 30
                shp = self.card(slide, MX, y + 8, w, 22, WHITE, radius=11)
                self.write(shp.text_frame, [p], insets=(4, 4, 0, 0), anchor=MSO_ANCHOR.MIDDLE)
                y += 8 + 22 + 10
            elif b['t'] == 'cards':
                y += self.place_cards(slide, b, MX, y + 16, CW, None, True) + 16
            else:
                st = self.styles(False, 1.0)
                y += 8
                y += self.flow(slide, [b], MX, y, CW, st, True) + st['gap']

    def render_content(self, slide, blocks: list[dict], small: bool, label: str) -> None:
        y = 49
        if blocks and blocks[0]['t'] == 'h' and blocks[0]['level'] == 1:
            y += self.title(slide, blocks[0]['text'], MX, y, 28) + 13
            blocks = blocks[1:]
        avail = CONTENT_BOTTOM - y
        for scale in (1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6):
            st = self.styles(small, scale)
            need = self.flow(None, blocks, MX, y, CW, st, False)
            if need <= avail:
                break
        else:
            self.warnings.append(f'{label}: content overflows by {need - avail:.0f}pt')
        self.flow(slide, blocks, MX, y, CW, st, True)

    def add(self, sd: dict, number: int) -> None:
        slide = self.prs.slides.add_slide(self.layout)
        classes = sd.get('class', '').split()
        lead = 'lead' in classes
        self.chrome(slide, sd, number, lead)
        label = f'slide {number}'
        if lead:
            self.render_lead(slide, sd['blocks'])
        else:
            self.render_content(slide, sd['blocks'], 'small' in classes, label)
        if not slide.shapes.title.has_text_frame or not slide.shapes.title.text_frame.text:
            slide.shapes.title._element.getparent().remove(slide.shapes.title._element)
        if sd['notes']:
            slide.notes_slide.notes_text_frame.text = sd['notes']


def main(argv: list[str]) -> int:
    src = Path(argv[1]) if len(argv) > 1 else ROOT / 'slides' / 'lecture.md'
    out = Path(argv[2]) if len(argv) > 2 else ROOT / 'dist' / 'lecture-editable.pptx'
    front, slides = parse_deck(src.read_text(encoding='utf-8'))
    metrics = Metrics()
    if metrics.font(BODY, False, False) is None or 'Aptos' not in str(metrics.font(BODY, False, False).getname()):
        print('note: Aptos not found; measuring with a fallback font (layout may be slightly off)')
    deck = Deck(metrics, front)
    for n, sd in enumerate(slides, 1):
        deck.add(sd, n)
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        deck.prs.save(out)
    except PermissionError:
        print(f'error: {out} is open in another program (close it in PowerPoint and re-run)')
        return 1
    for w in deck.warnings:
        print('warning:', w)
    print(f'{src.relative_to(ROOT) if src.is_relative_to(ROOT) else src} => {out} ({len(slides)} slides)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
