#!/usr/bin/env python3
"""Draw red entry / blue label boxes, scaled to a full-page review image.

Uses check_bounding_boxes.py's top-left fields.json schema. Crop the source PDF
first if needed; an arbitrary image crop cannot be aligned without its offsets.
"""
import argparse
import json
from PIL import Image, ImageDraw
from check_bounding_boxes import check, page_size


def create_validation_image(page_number, fields_json_path, input_path, output_path):
    with open(fields_json_path) as stream:
        data = json.load(stream)
    errors = check(data)
    if errors:
        # Invalid placement is precisely what a review image can help diagnose.
        print('\n'.join('WARNING: '+e for e in errors))
    page = next(p for p in data['pages'] if p['page_number']==page_number)
    width,height,_ = page_size(page)
    with Image.open(input_path) as source:
        img = source.convert('RGB')
    if abs(img.width/img.height - width/height) > 0.01*width/height:
        raise ValueError('Image aspect ratio does not match the full page')
    draw = ImageDraw.Draw(img)
    for f in data['form_fields']:
        if f['page_number'] != page_number:
            continue
        for kind,color in [('entry','red'),('label','blue')]:
            box = f.get(kind+'_bounding_box')
            if box is None:
                continue
            coords = [v*(img.width/width if i%2==0 else img.height/height) for i,v in enumerate(box)]
            draw.rectangle(coords,outline=color,width=2)
    img.save(output_path)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('page_number',type=int); p.add_argument('fields_json')
    p.add_argument('input_image'); p.add_argument('output_image')
    a = p.parse_args()
    create_validation_image(a.page_number,a.fields_json,a.input_image,a.output_image)
