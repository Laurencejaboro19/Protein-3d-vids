import re, subprocess, sys, os
from build_report import build, PARTS
from pypdf import PdfReader

def read_html():
    return '\n'.join(open(f).read() for f in PARTS)

def topdf(docx, outdir='.'):
    subprocess.run(['libreoffice','--headless','--convert-to','pdf',
                    '--outdir',outdir,docx],
                   check=True, capture_output=True, timeout=600)

def norm(s):
    return re.sub(r'[^a-z0-9]','', s.lower())

# pass 1: numbers unknown -> use placeholder of similar width
html = read_html()
# mask the contents page in pass 1 so heading titles are not found there
def mask(m):
    t = m.group(1)
    return '>' + ('x' * len(t)) + '\t00<'
h1 = re.sub(r'>([^<>\t]+)\t@@PG:[^<>]*?@@<', mask, html)
assert '@@PG:' not in h1, 'masking failed'
build(h1, 'pass1.docx')
topdf('pass1.docx')
r = PdfReader('pass1.pdf')
pages = [norm(p.extract_text() or '') for p in r.pages]
print('pass1 pages:', len(pages))

# find where body (CHAPTER ONE) starts to compute arabic offset
body_start = None
for i, t in enumerate(pages):
    if 'chapterone' in t and 'introductionandliteraturereview' in t:
        body_start = i; break
print('body starts at physical page', body_start+1 if body_start is not None else None)

targets = re.findall(r'@@PG:(.*?)@@', html)
found = {}
for t in targets:
    key = norm(t)
    if not key: continue
    for i, pg in enumerate(pages):
        if key in pg:
            found[t] = i
            break
missing = [t for t in targets if t not in found]
print('located', len(found), 'of', len(targets))
if missing: print('MISSING:', missing[:12])

def label(i):
    if body_start is None or i < body_start:
        n = i + 1
        rom = ['i','ii','iii','iv','v','vi','vii','viii','ix','x','xi','xii','xiii','xiv','xv']
        return rom[n-1] if n <= len(rom) else str(n)
    return str(i - body_start + 1)

out = html
for t in targets:
    out = out.replace('@@PG:%s@@' % t, label(found[t]) if t in found else '')
open('body.html','w').write(out)
build(out, 'De_Novo_Protein_Design_in_Medicine_Seminar.docx')
topdf('De_Novo_Protein_Design_in_Medicine_Seminar.docx')
print('final pages:', len(PdfReader('De_Novo_Protein_Design_in_Medicine_Seminar.pdf').pages))
