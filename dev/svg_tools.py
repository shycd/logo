#!/usr/bin/env python3
"""Helpers for regenerating SHYCD.svg (see dev/regenerate.sh).

  preclean   <in.svg> <out.svg>   drop Inkscape-only elements (namedview, metadata, flowRoot)
  restructure <in.svg> <out.svg>  give the flattened drawing descriptive ids, presentation
                                  attributes and the copyright header
"""
import sys
from lxml import etree

SVG = 'http://www.w3.org/2000/svg'
SODI = 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd'
NS = '{%s}' % SVG
SIZE = '185.098'  # mm, page fitted to the ring
HEADER = ('<!-- SHYCD logo (2011), vectorized 2019. Copyright © 2011 SHYCD, Carlos Andrés Planchón Prestes. '
          'License: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). All text converted to paths '
          '(font: TypeWrong). Editable source with live text: dev/SHYCD_editable.svg -->')
LEAVES = ('path2', 'path4', 'path6', 'path8', 'path10', 'path12', 'path14', 'path16',
          'path18', 'path20', 'path22', 'path24', 'path26', 'path28', 'path30')


def preclean(src, dst):
    tree = etree.parse(src)
    for el in list(tree.getroot().iter()):
        if not isinstance(el.tag, str):
            continue
        q = etree.QName(el)
        if (q.namespace == SVG and q.localname in ('flowRoot', 'metadata')) or \
           (q.namespace == SODI and q.localname == 'namedview'):
            el.getparent().remove(el)
    tree.write(dst, xml_declaration=True, encoding='UTF-8')


def restructure(src, dst):
    parser = etree.XMLParser(remove_blank_text=True)
    old = etree.parse(src, parser).getroot()
    byid = {el.get('id'): el for el in old.iter() if el.get('id')}
    d = lambda i: byid[i].get('d')

    root = etree.Element(NS + 'svg', nsmap={None: SVG})
    for k, v in (('width', SIZE + 'mm'), ('height', SIZE + 'mm'), ('viewBox', f'0 0 {SIZE} {SIZE}'),
                 ('version', '1.1'), ('role', 'img'), ('aria-labelledby', 'shycd-title')):
        root.set(k, v)
    title = etree.SubElement(root, NS + 'title'); title.set('id', 'shycd-title'); title.text = 'SHYCD logo'

    def path(parent, id_, dd, **attrs):
        p = etree.SubElement(parent, NS + 'path'); p.set('id', id_)
        for k, v in attrs.items():
            p.set(k.replace('_', '-'), v)
        p.set('d', dd)

    path(root, 'shycd-ring', d('path3524-3'), fill='#02b0f4')
    laurel = etree.SubElement(root, NS + 'g'); laurel.set('id', 'shycd-laurel'); laurel.set('fill', '#008000')
    for n, i in enumerate(LEAVES, 1):
        path(laurel, f'shycd-leaf{n}', d(i))
    path(root, 'shycd-aureola', d('path7561'), fill='#fdff9a', fill_rule='evenodd')
    path(root, 'shycd-glider', d('rect1746-7'), fill='#02b0f4')
    path(root, 'shycd-wordmark', d('text4828-7-0'), fill='#ffcc00', aria_label='S.H.Y.C.D')

    known = set(LEAVES) | {'path3524-3', 'path7561', 'rect1746-7', 'text4828-7-0', 'wordmark-arc'}
    missing = [el.get('id') for el in old.iter(NS + 'path') if el.get('id') not in known]
    if missing:
        sys.exit(f'unexpected paths in the drawing: {missing}')

    xml = etree.tostring(etree.ElementTree(root), pretty_print=True, xml_declaration=True, encoding='UTF-8').decode()
    head, body = xml.split('\n', 1)
    open(dst, 'w', encoding='utf-8').write(head + '\n' + HEADER + '\n' + body)


if __name__ == '__main__':
    cmd, src, dst = sys.argv[1:4]
    {'preclean': preclean, 'restructure': restructure}[cmd](src, dst)
