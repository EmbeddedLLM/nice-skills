#!/usr/bin/env python3
"""Validate top-left form boxes before creating annotations or review images.

fields.json: {"pages":[{"page_number":1,"pdf_width":612,"pdf_height":792}],
 "form_fields":[{"page_number":1,"description":"Name",
 "label_bounding_box":[20,20,70,40],"entry_bounding_box":[80,20,200,40],
 "entry_text":{"text":"Ada","font_size":10}}]}
Use image_width/image_height instead for pixel boxes. Font size is always points;
include pdf_width/pdf_height as well to check font fit for pixel coordinates,
and set units="pixels" on that page. This schema differs from place_text_by_boxes.
"""
import argparse
import json
import math


def positive(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value) and value > 0


def page_size(page):
    units = page.get('units', 'points' if 'pdf_width' in page else 'pixels')
    if units not in ('points','pixels'):
        raise ValueError('Page units must be points or pixels')
    keys = ('pdf_width','pdf_height') if units == 'points' else ('image_width','image_height')
    width,height = (page.get(k) for k in keys)
    if not positive(width) or not positive(height):
        raise ValueError(f'Page dimensions {keys} must be positive finite numbers')
    return width,height,units


def check(data):
    errors, pages, boxes = [], {}, []
    if not isinstance(data,dict) or not isinstance(data.get('pages'),list) or not isinstance(data.get('form_fields'),list):
        raise ValueError('Expected pages and form_fields arrays')
    for page in data['pages']:
        number = page.get('page_number')
        if type(number) is not int or number < 1 or number in pages:
            raise ValueError('Page numbers must be unique positive integers')
        page_size(page)
        pages[number] = page
    for i,field in enumerate(data['form_fields']):
        number = field.get('page_number')
        if type(number) is not int or number not in pages:
            raise ValueError(f'Field {i} refers to an unknown page')
        page = pages[number]
        width,height,units = page_size(page)
        for kind in ('label','entry'):
            box = field.get(kind+'_bounding_box')
            if kind == 'label' and box is None:
                continue
            if (not isinstance(box,list) or len(box)!=4 or
                any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in box)):
                errors.append(f'Field {i} {kind}: expected four finite coordinates'); continue
            x0,y0,x1,y1 = box
            if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
                errors.append(f'Field {i} {kind}: reversed, empty, or out-of-page box'); continue
            boxes.append((number,i,kind,box))
            if kind == 'entry' and 'entry_text' in field:
                text = field['entry_text']
                if not isinstance(text,dict) or not isinstance(text.get('text',''),str):
                    errors.append(f'Field {i}: entry_text.text must be a string'); continue
                fs = text.get('font_size',14)
                if not positive(fs):
                    errors.append(f'Field {i}: font_size must be positive and finite'); continue
                point_height = y1-y0
                if units == 'pixels':
                    if not positive(page.get('pdf_height')):
                        errors.append(f'Field {i}: pixel font-fit checking requires pdf_height'); continue
                    point_height *= page['pdf_height']/height
                if text.get('text') and fs > point_height:
                    errors.append(f'Field {i}: entry box is shorter than font size in points')
    for n,i,kind,a in boxes:
        for m,j,other,b in boxes:
            if (i,kind) >= (j,other) or n!=m:
                continue
            if max(a[0],b[0]) < min(a[2],b[2]) and max(a[1],b[1]) < min(a[3],b[3]):
                errors.append(f'Page {n}: field {i} {kind} overlaps field {j} {other}')
    return errors


def get_bounding_box_messages(stream):
    data = json.load(stream)
    errors = check(data)
    return ['FAILURE: '+e for e in errors] or ['SUCCESS: All bounding boxes are valid']


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('fields_json')
    a = p.parse_args()
    try:
        with open(a.fields_json) as stream:
            messages = get_bounding_box_messages(stream)
        print('\n'.join(messages))
        return 1 if any(m.startswith('FAILURE') for m in messages) else 0
    except (ValueError,TypeError,KeyError,OSError) as exc:
        p.exit(2,f'Error: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
