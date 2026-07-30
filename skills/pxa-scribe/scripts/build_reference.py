#!/usr/bin/env python3
"""建置 scribe 的 SP-reference.docx（pandoc 樣式範本）
中文＝微軟正黑體、英數/公式旁文＝Times New Roman；A4；含頁首 STRN 佔位與頁尾頁碼。
從 pandoc 預設 reference.docx 出發，改寫 styles.xml、sectPr、加 header/footer。
"""
import re, shutil, subprocess, zipfile, os, sys

SRC = "ref-default.docx"
OUT = "SP-reference.docx"
WORK = "refbuild"

EA = "微軟正黑體"      # East Asian font
LAT = "Times New Roman"  # Latin font
NAVY = "1F3864"          # heading color
STEEL = "3A5A89"
GRAY = "595959"
LINE = "BFBFBF"
SHADE_HDR = "DCE6F1"     # table header shading
SHADE_NOTE = "EEF4FB"    # callout shading

if not os.path.exists(SRC):
    with open(SRC, "wb") as f:
        f.write(subprocess.run(["pandoc", "--print-default-data-file", "reference.docx"],
                               capture_output=True, check=True).stdout)

if os.path.exists(WORK):
    shutil.rmtree(WORK)
os.makedirs(WORK)
subprocess.run(["unzip", "-oq", SRC, "-d", WORK], check=True)

sp = os.path.join(WORK, "word", "styles.xml")
xml = open(sp, encoding="utf-8").read()

def set_style(styleid, body):
    """Replace the whole <w:style ... w:styleId="X">...</w:style> block."""
    global xml
    pat = re.compile(r'<w:style [^>]*w:styleId="%s"[^>]*>.*?</w:style>' % styleid, re.S)
    assert pat.search(xml), styleid
    xml = pat.sub(body, xml, count=1)

RF = f'<w:rFonts w:ascii="{LAT}" w:hAnsi="{LAT}" w:eastAsia="{EA}" w:cs="{LAT}"/>'

set_style("Normal", f'''<w:style w:type="paragraph" w:default="1" w:styleId="Normal">
<w:name w:val="Normal"/><w:qFormat/>
<w:pPr><w:spacing w:before="0" w:after="120" w:line="276" w:lineRule="auto"/><w:jc w:val="both"/></w:pPr>
<w:rPr>{RF}<w:sz w:val="22"/><w:szCs w:val="22"/><w:lang w:val="en-US" w:eastAsia="zh-TW"/></w:rPr>
</w:style>''')

set_style("Heading1", f'''<w:style w:type="paragraph" w:styleId="Heading1">
<w:name w:val="Heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:qFormat/>
<w:pPr><w:keepNext/><w:spacing w:before="240" w:after="240"/><w:jc w:val="center"/><w:outlineLvl w:val="0"/></w:pPr>
<w:rPr>{RF}<w:b/><w:sz w:val="40"/><w:szCs w:val="40"/><w:color w:val="{NAVY}"/></w:rPr>
</w:style>''')

set_style("Heading2", f'''<w:style w:type="paragraph" w:styleId="Heading2">
<w:name w:val="Heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:qFormat/>
<w:pPr><w:keepNext/><w:pBdr><w:bottom w:val="single" w:sz="12" w:space="4" w:color="{NAVY}"/></w:pBdr><w:spacing w:before="320" w:after="160"/><w:jc w:val="left"/><w:outlineLvl w:val="1"/></w:pPr>
<w:rPr>{RF}<w:b/><w:sz w:val="30"/><w:szCs w:val="30"/><w:color w:val="{NAVY}"/></w:rPr>
</w:style>''')

set_style("Heading3", f'''<w:style w:type="paragraph" w:styleId="Heading3">
<w:name w:val="Heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:qFormat/>
<w:pPr><w:keepNext/><w:spacing w:before="240" w:after="120"/><w:jc w:val="left"/><w:outlineLvl w:val="2"/></w:pPr>
<w:rPr>{RF}<w:b/><w:sz w:val="26"/><w:szCs w:val="26"/><w:color w:val="{STEEL}"/></w:rPr>
</w:style>''')

set_style("Heading4", f'''<w:style w:type="paragraph" w:styleId="Heading4">
<w:name w:val="Heading 4"/><w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:qFormat/>
<w:pPr><w:keepNext/><w:spacing w:before="200" w:after="100"/><w:jc w:val="left"/><w:outlineLvl w:val="3"/></w:pPr>
<w:rPr>{RF}<w:b/><w:sz w:val="24"/><w:szCs w:val="24"/><w:color w:val="{GRAY}"/></w:rPr>
</w:style>''')

set_style("BlockText", f'''<w:style w:type="paragraph" w:styleId="BlockText">
<w:name w:val="Block Text"/><w:basedOn w:val="Normal"/><w:qFormat/>
<w:pPr><w:pBdr><w:left w:val="single" w:sz="18" w:space="8" w:color="{STEEL}"/></w:pBdr>
<w:shd w:val="clear" w:color="auto" w:fill="{SHADE_NOTE}"/><w:spacing w:before="60" w:after="60"/><w:ind w:left="360" w:right="240"/></w:pPr>
<w:rPr>{RF}<w:sz w:val="21"/><w:szCs w:val="21"/><w:color w:val="333F50"/></w:rPr>
</w:style>''')

set_style("Compact", f'''<w:style w:type="paragraph" w:styleId="Compact">
<w:name w:val="Compact"/><w:basedOn w:val="BodyText"/><w:qFormat/>
<w:pPr><w:spacing w:before="20" w:after="20"/><w:jc w:val="left"/></w:pPr>
<w:rPr>{RF}<w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>
</w:style>''')

set_style("TableCaption", f'''<w:style w:type="paragraph" w:styleId="TableCaption">
<w:name w:val="Table Caption"/><w:basedOn w:val="Normal"/><w:qFormat/>
<w:pPr><w:spacing w:before="60" w:after="60"/><w:jc w:val="center"/></w:pPr>
<w:rPr>{RF}<w:i/><w:sz w:val="19"/><w:szCs w:val="19"/><w:color w:val="{GRAY}"/></w:rPr>
</w:style>''')

set_style("Caption", f'''<w:style w:type="paragraph" w:styleId="Caption">
<w:name w:val="Caption"/><w:basedOn w:val="Normal"/><w:qFormat/>
<w:pPr><w:spacing w:before="60" w:after="60"/><w:jc w:val="center"/></w:pPr>
<w:rPr>{RF}<w:i/><w:sz w:val="19"/><w:szCs w:val="19"/><w:color w:val="{GRAY}"/></w:rPr>
</w:style>''')

# Table style: thin gray grid, steel header band, compact cell margins
set_style("Table", f'''<w:style w:type="table" w:styleId="Table">
<w:name w:val="Table"/><w:basedOn w:val="TableNormal"/><w:qFormat/>
<w:tblPr>
<w:tblBorders>
<w:top w:val="single" w:sz="8" w:space="0" w:color="{STEEL}"/>
<w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>
<w:bottom w:val="single" w:sz="8" w:space="0" w:color="{STEEL}"/>
<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>
<w:insideH w:val="single" w:sz="4" w:space="0" w:color="{LINE}"/>
<w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>
</w:tblBorders>
<w:tblCellMar><w:top w:w="45" w:type="dxa"/><w:left w:w="100" w:type="dxa"/><w:bottom w:w="45" w:type="dxa"/><w:right w:w="100" w:type="dxa"/></w:tblCellMar>
</w:tblPr>
<w:tblStylePr w:type="firstRow">
<w:rPr><w:b/><w:color w:val="{NAVY}"/></w:rPr>
<w:tblPr/><w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="{SHADE_HDR}"/>
<w:tcBorders><w:bottom w:val="single" w:sz="8" w:space="0" w:color="{STEEL}"/></w:tcBorders></w:tcPr>
</w:tblStylePr>
</w:style>''')

open(sp, "w", encoding="utf-8").write(xml)

# ---------- document.xml: A4 + margins + header/footer refs ----------
dp = os.path.join(WORK, "word", "document.xml")
doc = open(dp, encoding="utf-8").read()
sect = ('<w:sectPr>'
        '<w:headerReference w:type="default" r:id="rIdHdr1"/>'
        '<w:footerReference w:type="default" r:id="rIdFtr1"/>'
        '<w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1440" w:right="1361" w:bottom="1440" w:left="1361" w:header="720" w:footer="720" w:gutter="0"/>'
        '<w:cols w:space="720"/><w:docGrid w:linePitch="360"/>'
        '</w:sectPr>')
doc = re.sub(r'<w:sectPr\s*/>|<w:sectPr>.*?</w:sectPr>', sect, doc, count=1, flags=re.S)
assert 'rIdHdr1' in doc, 'sectPr injection failed'
open(dp, "w", encoding="utf-8").write(doc)

# ---------- header / footer parts ----------
NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')
hdr = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr {NS}><w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="4" w:space="2" w:color="{LINE}"/></w:pBdr><w:jc w:val="right"/>
<w:rPr>{RF}<w:sz w:val="17"/><w:color w:val="{GRAY}"/></w:rPr></w:pPr>
<w:r><w:rPr>{RF}<w:sz w:val="17"/><w:color w:val="{GRAY}"/></w:rPr><w:t>{{STRN}}</w:t></w:r></w:p></w:hdr>'''
ftr = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr {NS}><w:p><w:pPr><w:jc w:val="center"/><w:rPr>{RF}<w:sz w:val="18"/><w:color w:val="{GRAY}"/></w:rPr></w:pPr>
<w:r><w:rPr>{RF}<w:sz w:val="18"/><w:color w:val="{GRAY}"/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r>
<w:r><w:rPr>{RF}<w:sz w:val="18"/><w:color w:val="{GRAY}"/></w:rPr><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>
<w:r><w:rPr>{RF}<w:sz w:val="18"/><w:color w:val="{GRAY}"/></w:rPr><w:fldChar w:fldCharType="end"/></w:r></w:p></w:ftr>'''
open(os.path.join(WORK, "word", "header1.xml"), "w", encoding="utf-8").write(hdr)
open(os.path.join(WORK, "word", "footer1.xml"), "w", encoding="utf-8").write(ftr)

# rels
rp = os.path.join(WORK, "word", "_rels", "document.xml.rels")
rels = open(rp, encoding="utf-8").read()
add = ('<Relationship Id="rIdHdr1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>'
       '<Relationship Id="rIdFtr1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>')
rels = rels.replace("</Relationships>", add + "</Relationships>")
open(rp, "w", encoding="utf-8").write(rels)

# content types
cp = os.path.join(WORK, "[Content_Types].xml")
ct = open(cp, encoding="utf-8").read()
add = ('<Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>'
       '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>')
ct = ct.replace("</Types>", add + "</Types>")
open(cp, "w", encoding="utf-8").write(ct)

# zip
if os.path.exists(OUT):
    os.remove(OUT)
cwd = os.getcwd()
os.chdir(WORK)
subprocess.run(["zip", "-Xqr", os.path.join(cwd, OUT), "."], check=True)
os.chdir(cwd)
print("built", OUT)
