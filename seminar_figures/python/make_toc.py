import re
from bs4 import BeautifulSoup

FRONT = ['DECLARATION','CERTIFICATION','DEDICATION','ACKNOWLEDGEMENTS','ABSTRACT',
         'TABLE OF CONTENTS','LIST OF TABLES','LIST OF FIGURES','LIST OF ABBREVIATIONS']

def entries():
    out = []
    for f in FRONT:
        out.append((0, f))
    chap = None
    for fn in ['p2.html','p3.html','p4.html']:
        soup = BeautifulSoup(open(fn).read(), 'html.parser')
        pend = None
        for n in soup.find_all(['h2','h3','h4']):
            cls = ' '.join(n.get('class', []))
            t = n.get_text(strip=True)
            if n.name == 'h2' and 'chap' in cls:
                if t.startswith('CHAPTER'):
                    pend = t
                elif pend:
                    out.append((0, pend + ': ' + t)); pend = None
                else:
                    out.append((0, t))
            elif n.name == 'h3':
                out.append((1, t))
            elif n.name == 'h4':
                out.append((2, t))
        if pend: out.append((0, pend))
    return out

if __name__ == '__main__':
    es = entries()
    div = ['<div class="toc">']
    for lvl, t in es:
        c = 'l0' if lvl == 0 else 'l1'
        div.append('<p class="%s">%s\t@@PG:%s@@</p>' % (c, t, t))
    div.append('</div>')
    s = open('p1b.html').read()
    s = re.sub(r'<p class="tocmark">TOC_PLACEHOLDER</p>', '\n'.join(div), s)
    s = s.replace('Structures referred to in this seminar', 'Structures referred to in this review')
    open('p1b.html','w').write(s)
    print(len(es), 'entries')
