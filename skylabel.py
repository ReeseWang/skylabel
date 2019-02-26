#!/usr/bin/env python3

import argparse
import urllib.parse
import qrcode
import qrcode.image.svg
import os
import sys
import shutil
import csv
from subprocess import run


urlPrefix = 'https://wiki.thu-skyworks.org/'

texPreamable = '''
\\documentclass{minimal}
\\usepackage[UTF8]{ctex}
\\usepackage{hyperref}
\\usepackage{graphicx}
\\usepackage{tikz}
\\usepackage{svg}
'''

texEnd = '\\end{tikzpicture}\n\\end{document}'


def runtex(jobname):
    p = run(['xelatex', '-shell-escape', '-interaction=nonstopmode',
             '-output-directory=./temp', '-halt-on-error',
             './temp/' + jobname + '.tex'], stdout=sys.stdout,
            stderr=sys.stderr, encoding='utf-8')
    assert(p.returncode == 0)


class skylabel:
    NEW_CELL = 0
    NEW_PAGE = 1
    NEW_ROW = 2

    def new(self):
        self.counter += 1
        # Time to start a new row
        if self.currentcol % self.matrix[0] == 0:
            # to start a new page
            if self.currentrow % self.matrix[1] == 0:
                self.currentrow = 1
                self.currentcol = 1
                if self.counter != 1:
                    return self.NEW_PAGE
                else:
                    return self.NEW_CELL
            else:
                self.currentcol = 1
                self.currentrow += 1
                return self.NEW_ROW
        else:
            self.currentcol += 1
            return self.NEW_CELL

    def __init__(
            self, pagesize, qrsize, layout, logowidth, logooffset, textoffset,
            textsize, defaultPara, labelsize, matrix=(1, 1),
            cellsep=(0, 0)):
        self.pagesize = pagesize
        self.qrsize = qrsize
        self.layout = layout
        self.logowidth = logowidth
        self.logooffset = logooffset
        self.textoffset = textoffset
        self.textsize = textsize
        self.matrix = matrix
        self.cellsep = cellsep
        self.defaultPara = defaultPara
        self.labelsize = labelsize
        self.counter = 0
        self.currentrow = 0
        self.currentcol = 0

    def genQRImg(self, customUrl, content):
        if customUrl:
            qrstr = urllib.parse.quote(content)
        else:
            qrstr = urlPrefix + urllib.parse.quote(content)
        factory = qrcode.image.svg.SvgPathImage
        qrcode.make(qrstr, image_factory=factory).save(
            './temp/qr{}.svg'.format(self.counter))

    def genTexPreamable(self):
        return texPreamable + '''\\usepackage[papersize={{{s[0]}mm, {s[1]}mm\
}}]{{geometry}}\n'''.format(s=self.pagesize) + '''\\linespread{0.9}
\\begin{document}
\\begin{tikzpicture}[remember picture, overlay, shift=(current page.north west)]
'''

    def genCell(self, customUrl, para):
        res = self.new()
        if res == self.NEW_PAGE:
            ret = '\\end{tikzpicture}\\newpage' + \
                '\\begin{tikzpicture}[remember picture, overlay, shift=' + \
                '(current page.north west)]\n'
        else:
            ret = ''
        if self.layout == 'A':
            self.genQRImg(customUrl, para[1])
            ret += '\\node (qrcode{}) at ({}mm, -{}mm) [anchor=center] '.\
                format(
                    self.counter,
                    0.5 * self.labelsize[0] +
                    (self.currentcol-1)*self.cellsep[0],
                    0.5 * self.labelsize[0] +
                    (self.currentrow-1)*self.cellsep[1]
                )
            ret += '{{\\includesvg[width={}mm]{{./temp/qr{}}}}};\n'.\
                format(self.qrsize, self.counter)
            ret += '''\\node[anchor=north,inner sep=0,shift={{({s[0]}mm,\
{s[1]}mm)}}] (logo{c}) at (qrcode{c}.south) {{\\includegraphics[width={w}mm]\
{{20110623skyworkslogo}}}};\n'''.format(s=self.logooffset,
                                        c=self.counter,
                                        w=self.logowidth)
            ret += '''\\node[anchor=north,inner sep=0,shift={{({s[0]}mm,\
{s[1]}mm)}}] (text{c}) at (logo{c}.south) {{\\{size}\\sffamily {text}}};
'''.format(s=self.textoffset, c=self.counter, size=self.textsize, text=para[0])
            pass
        elif self.layout == 'B':
            self.genQRImg(customUrl, para[1])
            ret += '''\\node (qrcode{}) at ({}mm, -{}mm) \
[inner sep=0,anchor=center] '''.format(
                    self.counter,
                    0.5 * self.labelsize[0] +
                    (self.currentcol-1)*self.cellsep[0],
                    0.5 * self.labelsize[0] +
                    (self.currentrow-1)*self.cellsep[1]
                )
            ret += '{{\\includesvg[width={}mm]{{./temp/qr{}}}}};\n'.\
                format(self.qrsize, self.counter) + '\\baselineskip=2mm\n'
            ret += '''\\path (qrcode{c}.south west) -- \
node[inner sep=0,midway,anchor=west,align=center,font=\\sffamily\\{size}] \
(logo{c}) {{天空\\\\工场}} (qrcode{c}.south west |- (0mm,-{s}mm);
'''.format(c=self.counter,
                size=self.textsize,
                s=self.labelsize[1] + (self.currentrow-1) * self.cellsep[1])
            ret += '''\\path (logo{c}.east) -- node\
[midway,anchor=center,font=\\{size}\\sffamily,align=center] (text{c}) \
{{{text}}} (logo{c}.east -| qrcode{c}.east);
'''.format(c=self.counter,
                size=self.textsize,
                text=para[0])
            pass

        return ret
        pass


types = {
    '8050A':
    skylabel(
        pagesize=(50, 80),
        qrsize=45, layout='A', logowidth=35, logooffset=(0, -1),
        textsize='LARGE', textoffset=(0, -3.5), labelsize=(50, 80),
        defaultPara=[['天空工场', '天空工场']]),
    '5030A':
    skylabel(
        pagesize=(30, 50),
        qrsize=26, layout='A', logowidth=23, logooffset=(0, -1),
        textsize='large', textoffset=(0, -2.5), labelsize=(30, 50),
        defaultPara=[['天空工场', '天空工场']]),
    '2015TB':  # 20mm x 15mm Triple
    skylabel(
        pagesize=(15, 64),
        qrsize=13, layout='B', logowidth=5, logooffset=(0, 0),
        textsize='tiny', textoffset=(0, 0), matrix=(1, 3), labelsize=(15, 20),
        cellsep=(0, 22), defaultPara=[['天空工场', 'Skyworks1'],
                                      ['天空工场', 'Skyworks2'],
                                      ['天空工场', 'Skyworks3']])
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate a PDF file for printing on adhesive labels with '
        'thermal printer.')
    parser.add_argument(
        '-i',
        metavar='INPUT',
        dest='infile',
        help='Input file name.',
        default='input.csv')
    parser.add_argument(
        '-o',
        metavar='OUTPUT',
        dest='outfile',
        help='Output PDF file name prefix.',
        default='output')
    parser.add_argument(
        '-t',
        metavar='TYPE',
        dest='typeSelected',
        default='8050A',
        choices=types,
        help='Label size and layout.')
    parser.add_argument('-c', '--custom-url', action='store_true')
    parser.add_argument('--generate-examples', action='store_true')
    parser.add_argument('--debug', action='store_true')

    args = parser.parse_args()

    shutil.rmtree('./temp')
    os.makedirs('./temp')
    if args.generate_examples:
        os.makedirs('./examples', exist_ok=True)
        for k, v in types.items():
            tex = v.genTexPreamable()
            for i in range(v.matrix[0] * v.matrix[1]):
                tex += v.genCell(args.custom_url, v.defaultPara[i])
            pass
            tex += texEnd
            with open('./temp/' + k + '.tex', 'w') as f:
                f.write(tex)
            # Run twice to get node positions right.
            runtex(k)
            runtex(k)
            p = run(['pdftopng', './temp/' + k + '.pdf', './examples/' + k],
                    stdout=sys.stdout, stderr=sys.stderr)
            assert(p.returncode == 0)
    else:
        v = types[args.typeSelected]
        tex = v.genTexPreamable()
        with open(args.infile, 'r') as f:
            r = csv.reader(f)
            for i in r:
                print(i)
                tex += v.genCell(args.custom_url, i)
        tex += texEnd
        with open('./temp/' + args.outfile + '.tex', 'w') as f:
            f.write(tex)
        # Run twice
        runtex(args.outfile)
        runtex(args.outfile)
        shutil.copy('./temp/' + args.outfile + '.pdf', './')
