import re, sys, os
from bs4 import BeautifulSoup, NavigableString, Tag
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT, WD_BREAK
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from PIL import Image

PARTS = ['p1.html','p1b.html','p2.html','p3.html','p4.html']
CONTENT_W = 6.0  # inches usable (8.5 - 1.5 - 1.0)
IMG_SCALE = float(os.environ.get('IMG_SCALE','0.82'))
COLW = {5: [0.11, 0.33, 0.24, 0.16, 0.10], 3: [0.22, 0.39, 0.39]}
SP = float(os.environ.get('SP','0.75'))

def new_doc():
    d = Document()
    s = d.sections[0]
    s.page_width, s.page_height = Inches(8.5), Inches(11)
    s.left_margin  = Inches(1.5)
    s.right_margin = Inches(1.0)
    s.top_margin   = Inches(1.0)
    s.bottom_margin= Inches(1.0)
    n = d.styles['Normal']
    n.font.name = 'Times New Roman'
    n.font.size = Pt(12)
    n.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    pf = n.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.space_after = Pt(6)
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return d

def para(d, align=None, before=0, after=6, spacing=WD_LINE_SPACING.ONE_POINT_FIVE,
         keep_next=False, indent=None, hanging=None):
    p = d.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing_rule = spacing
    pf.space_before = Pt(before); pf.space_after = Pt(after)
    if align is not None: pf.alignment = align
    if keep_next: pf.keep_with_next = True
    if indent is not None: pf.left_indent = Inches(indent)
    if hanging is not None: pf.first_line_indent = Inches(-hanging)
    return p

def emit_inline(p, node, bold=False, italic=False, size=None, sub=False, sup=False):
    for ch in node.children:
        if isinstance(ch, NavigableString):
            t = str(ch)
            if not t: continue
            r = p.add_run(t)
            r.bold, r.italic = bold, italic
            if size: r.font.size = Pt(size)
            if sub: r.font.subscript = True
            if sup: r.font.superscript = True
        elif isinstance(ch, Tag):
            if ch.name == 'br':
                p.add_run().add_break(); continue
            b = bold or ch.name in ('b','strong','th')
            i = italic or ch.name in ('i','em')
            sb = sub or ch.name == 'sub'
            sp = sup or ch.name == 'sup'
            emit_inline(p, ch, b, i, size, sb, sp)

def add_image(d, src, frac):
    im = Image.open(src); ar = im.height / im.width
    # very wide, short plates cost almost no vertical space: keep them full width
    sc = 1.0 if ar < 0.20 else IMG_SCALE
    w = Inches(CONTENT_W * frac * sc)
    h = Emu(int(w * ar))
    maxh = Inches(float(os.environ.get('MAXH','4.6')))
    if h > maxh:
        h = maxh; w = Emu(int(maxh / ar))
    p = para(d, WD_ALIGN_PARAGRAPH.CENTER, before=10*SP, after=4,
             spacing=WD_LINE_SPACING.SINGLE, keep_next=True)
    p.add_run().add_picture(src, width=w, height=h)
    return p

def set_borders(table):
    tbl = table._tbl
    pr = tbl.tblPr
    borders = OxmlElement('w:tblBorders')
    for edge in ('top','left','bottom','right','insideH','insideV'):
        e = OxmlElement('w:'+edge)
        e.set(qn('w:val'),'single'); e.set(qn('w:sz'),'8')
        e.set(qn('w:space'),'0');    e.set(qn('w:color'),'000000')
        borders.append(e)
    pr.append(borders)

def add_table(d, tbl_tag, fontsize=11):
    rows = tbl_tag.find_all('tr')
    ncol = max(len(r.find_all(['td','th'])) for r in rows)
    t = d.add_table(rows=0, cols=ncol)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    set_borders(t)
    widths = COLW.get(ncol)
    if widths:
        for ci, frac in enumerate(widths):
            for cell in t.columns[ci].cells:
                cell.width = Inches(CONTENT_W * frac)
    for ri, r in enumerate(rows):
        cells = r.find_all(['td','th'])
        row = t.add_row()
        if ri == 0 and r.find('th'):
            trPr = row._tr.get_or_add_trPr()
            hdr = OxmlElement('w:tblHeader'); hdr.set(qn('w:val'),'true')
            trPr.append(hdr)
        for k in range(ncol):
            cell = row.cells[k]
            cell.paragraphs[0]._p.getparent().remove(cell.paragraphs[0]._p)
            p = cell.add_paragraph()
            pf = p.paragraph_format
            pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
            pf.space_before = Pt(3); pf.space_after = Pt(3)
            pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
            if k < len(cells):
                emit_inline(p, cells[k], bold=(cells[k].name=='th'), size=fontsize)
            else:
                p.add_run('')
    para(d, after=8, spacing=WD_LINE_SPACING.SINGLE)
    return t

def page_break(d):
    p = d.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    p.add_run().add_break(WD_BREAK.PAGE)

def add_page_field(p, fmt=None):
    r = p.add_run()
    f1 = OxmlElement('w:fldChar'); f1.set(qn('w:fldCharType'),'begin')
    it = OxmlElement('w:instrText'); it.set(qn('xml:space'),'preserve')
    it.text = ' PAGE  \\* %s ' % (fmt or 'ARABIC')
    f2 = OxmlElement('w:fldChar'); f2.set(qn('w:fldCharType'),'end')
    r._r.append(f1); r._r.append(it); r._r.append(f2)

def footer_number(section, fmt='decimal', start=None):
    section.footer.is_linked_to_previous = False
    fp = section.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    for r in list(fp.runs): r._r.getparent().remove(r._r)
    add_page_field(fp, 'roman' if fmt=='lowerRoman' else 'ARABIC')
    for r in fp.runs:
        r.font.name = 'Times New Roman'; r.font.size = Pt(12)
    sp = section._sectPr
    pg = sp.find(qn('w:pgNumType'))
    if pg is None:
        pg = OxmlElement('w:pgNumType'); sp.append(pg)
    pg.set(qn('w:fmt'), fmt)
    if start is not None:
        pg.set(qn('w:start'), str(start))

def start_body_section(d):
    s = d.add_section(WD_SECTION.NEW_PAGE)
    s.page_width, s.page_height = Inches(8.5), Inches(11)
    s.left_margin  = Inches(1.5); s.right_margin = Inches(1.0)
    s.top_margin   = Inches(1.0); s.bottom_margin= Inches(1.0)
    footer_number(s, 'decimal', 1)
    return s

def build(html, outpath, headings_out=None):
    soup = BeautifulSoup(html, 'html.parser')
    d = new_doc()
    headings = []
    nodes = [n for n in soup.children if isinstance(n, Tag)]
    for idx, n in enumerate(nodes):
        cls = ' '.join(n.get('class', []))
        if n.name == 'h1' and 'tp' in cls:
            p = para(d, WD_ALIGN_PARAGRAPH.CENTER, before=0, after=14, spacing=WD_LINE_SPACING.ONE_POINT_FIVE)
            emit_inline(p, n, bold=True, size=16)
        elif n.name == 'p' and 'tpc' in cls:
            p = para(d, WD_ALIGN_PARAGRAPH.CENTER, after=10)
            emit_inline(p, n)
        elif n.name == 'p' and 'sig' in cls:
            p = para(d, WD_ALIGN_PARAGRAPH.LEFT, after=4, spacing=WD_LINE_SPACING.SINGLE)
            emit_inline(p, n)
        elif n.name == 'h2' and ('pre' in cls or 'chap' in cls):
            prev = nodes[idx-1] if idx else None
            prev_chap = prev is not None and prev.name == 'h2' and 'chap' in ' '.join(prev.get('class',[]))
            txt = n.get_text(strip=True)
            if txt == 'CHAPTER ONE':
                start_body_section(d)
            elif not prev_chap:
                page_break(d)
            p = para(d, WD_ALIGN_PARAGRAPH.CENTER, before=0, after=12)
            emit_inline(p, n, bold=True, size=14)
            headings.append((0, n.get_text(strip=True), p))
        elif n.name == 'h3':
            p = para(d, WD_ALIGN_PARAGRAPH.LEFT, before=14, after=6, keep_next=True)
            emit_inline(p, n, bold=True, size=13)
            headings.append((1, n.get_text(strip=True), p))
        elif n.name == 'h4':
            p = para(d, WD_ALIGN_PARAGRAPH.LEFT, before=12, after=5, keep_next=True)
            emit_inline(p, n, bold=True, italic=True)
            headings.append((2, n.get_text(strip=True), p))
        elif n.name == 'figure':
            img = n.find('img')
            st = img.get('style','')
            m = re.search(r'width:\s*(\d+)%', st)
            frac = (int(m.group(1))/100.0) if m else 0.9
            add_image(d, img['src'], frac)
            cap = n.find('figcaption')
            if cap:
                p = para(d, WD_ALIGN_PARAGRAPH.CENTER, before=2, after=16*SP,
                         spacing=WD_LINE_SPACING.SINGLE)
                emit_inline(p, cap, size=11)
        elif n.name == 'table':
            add_table(d, n)
        elif n.name == 'ol':
            for i, li in enumerate(n.find_all('li', recursive=False), 1):
                p = para(d, WD_ALIGN_PARAGRAPH.JUSTIFY, after=6, indent=0.4, hanging=0.4)
                p.add_run('%d.  ' % i)
                emit_inline(p, li)
        elif n.name == 'ul':
            for li in n.find_all('li', recursive=False):
                p = para(d, WD_ALIGN_PARAGRAPH.JUSTIFY, after=6, indent=0.4, hanging=0.4)
                p.add_run('•  ')
                emit_inline(p, li)
        elif n.name == 'div' and 'refs' in cls:
            for sub in n.find_all('p', recursive=False):
                p = para(d, WD_ALIGN_PARAGRAPH.JUSTIFY, after=8,
                         spacing=WD_LINE_SPACING.SINGLE, indent=0.5, hanging=0.5)
                emit_inline(p, sub, size=float(os.environ.get('REFPT','11')))
        elif n.name == 'div' and 'toc' in cls:
            for sub in n.find_all('p', recursive=False):
                lvl = 'l1' in ' '.join(sub.get('class',[]))
                p = para(d, WD_ALIGN_PARAGRAPH.LEFT, after=4,
                         spacing=WD_LINE_SPACING.SINGLE,
                         indent=(0.3 if lvl else 0.0))
                p.paragraph_format.tab_stops.add_tab_stop(
                    Inches(CONTENT_W), WD_TAB_ALIGNMENT.RIGHT)
                emit_inline(p, sub, bold=(not lvl))
        elif n.name == 'p':
            if 'cap' in cls:
                p = para(d, WD_ALIGN_PARAGRAPH.CENTER, before=2, after=16*SP,
                         spacing=WD_LINE_SPACING.SINGLE)
                emit_inline(p, n, size=11)
            elif 'tocmark' in cls:
                pass
            else:
                p = para(d, WD_ALIGN_PARAGRAPH.JUSTIFY, after=8*SP)
                emit_inline(p, n)
    footer_number(d.sections[0], 'lowerRoman', 1)
    d.save(outpath)
    if headings_out is not None:
        headings_out.extend([(l, t) for l, t, _ in headings])
    return d

if __name__ == '__main__':
    html = '\n'.join(open(f).read() for f in PARTS)
    build(html, sys.argv[1] if len(sys.argv)>1 else 'out.docx')
