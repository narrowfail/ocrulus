#!/usr/bin/env python
import uuid
import sys
import os
import subprocess
from PIL import Image, ImageEnhance

# Config
RATIO = 1.5


def transform_image(input_file):
    """
    Rezies and enhances images for the OCR software.
    :param input_file: an image.
    :return: a new image path.
    """
    try:
        img = Image.open(input_file).convert('LA')
        new_size = (int(img.size[0] * RATIO), int(img.size[1] * RATIO))
        img = img.resize(new_size, Image.BILINEAR)
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(7.0)
        output_file = "%s.png" % uuid.uuid1()
        img.save(output_file, "PNG")
        return output_file
    except IOError, ex:
        print "Error: %s" % ex
        return None


def call_ocr(image_path):
    """
    Calls GOCR an open source OCR software.
    :param image_path: an image path.
    :return: plain text.
    """
    proc = subprocess.Popen(['gocr', '%s' % image_path],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    result = proc.communicate()
    return result[0].strip().replace(' ','')


def procces_images(*files):
    """
    Main loop!
    :param files: files to proccess.
    """
    for img_file in files:
        image_path = transform_image(img_file)
        if image_path:
            # Call OCR
            data = call_ocr(image_path)
            print "File: %s - Text: %s" % (img_file, data)
            # Delete temp file!
            os.remove(image_path)


if __name__ == '__main__':
    procces_images(*sys.argv[1:])
