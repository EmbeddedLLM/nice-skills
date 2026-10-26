#!/usr/bin/env python3
"""Add editable FreeText annotations using validated top-left form boxes.

For permanent page text use place_text_by_boxes.py instead. Supports unrotated,
zero-origin, uncropped PDF pages; normalize other page geometries first.
"""
import argparse
import json
import re
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from pypdf.annotations import FreeText
from check_bounding_boxes import check, page_size


def fill_pdf_form(input_pdf_path, fields_json_path, output_pdf_path):
    output = Path(output_pdf_path)
    if output.exists() or output.is_symlink():
        raise ValueError('Choose a new output path')
    with open(fields_json_path) as stream:
        data = json.load(stream)
    errors = check(data)
    if errors:
        raise ValueError('; '.join(errors))
    reader = PdfReader(input_pdf_path)
    pages = {p['page_number']:p for p in data['pages']}
    for number,info in pages.items():
        if number > len(reader.pages):
            raise ValueError(f'PDF has no page {number}')
        page = reader.pages[number-1]
        if page.rotation or tuple(page.mediabox[:2])!=(0,0) or list(page.cropbox)!=list(page.mediabox):
            raise ValueError('Normalize rotated/cropped/offset page boxes before annotation placement')
        width,height,units = page_size(info)
        if units == 'points' and (abs(width-float(page.mediabox.width))>0.1 or abs(height-float(page.mediabox.height))>0.1):
            raise ValueError('Point dimensions must match the PDF page')
        if units == 'pixels' and abs(width/height-float(page.mediabox.width/page.mediabox.height))>0.01*width/height:
            raise ValueError('Image aspect ratio must match the PDF page')
        if units == 'pixels' and abs(info.get('pdf_height',float(page.mediabox.height))-float(page.mediabox.height))>0.1:
            raise ValueError('pdf_height must match the PDF for font-fit checking')
    writer = PdfWriter(clone_from=reader)
    for f in data['form_fields']:
        entry = f.get('entry_text',{})
        text = entry.get('text','')
        if not text:
            continue
        number = f['page_number']; page = reader.pages[number-1]
        width,height,_ = page_size(pages[number])
        pw,ph = float(page.mediabox.width),float(page.mediabox.height)
        x0,y0,x1,y1 = f['entry_bounding_box']
        rect = (x0*pw/width,ph-y1*ph/height,x1*pw/width,ph-y0*ph/height)
        color = entry.get('font_color','000000')
        if not re.fullmatch(r'[0-9A-Fa-f]{6}',color):
            raise ValueError('font_color must be six hex digits')
        annotation = FreeText(text=text,rect=rect,font=entry.get('font','Helvetica'),
                              font_size=f"{entry.get('font_size',14)}pt",font_color=color,
                              border_color=None,background_color=None)
        writer.add_annotation(page_number=number-1,annotation=annotation)
    with output.open('xb') as stream:
        writer.write(stream)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input_pdf'); p.add_argument('fields_json'); p.add_argument('output_pdf')
    a = p.parse_args()
    try:
        fill_pdf_form(a.input_pdf,a.fields_json,a.output_pdf)
    except Exception as exc:
        p.exit(1,f'Error: {exc}\n')
