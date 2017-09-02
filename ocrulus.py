#!/usr/bin/env python
from __future__ import print_function
import uuid
import sys
import os
import subprocess
from PIL import Image
from termcolor import colored
from cusip import is_valid
from pytesseract import image_to_string

# Configuration
RATIO = 3.0
THRESHOLD = 170  # 170
REPLACEMENTS = [('S', 'Z'), ('Z', '2'), ('O', '0'), ('L', '1'),
                ('4', 'A'), ('B', '8'), ('Q', 'O'), ('Q', '0'),
                ('Z', '7'), ('S', '7'), ('Y', '7')]


def transform_image(input_file):
    """
    Rezies and enhances images for the OCR software.
    :param input_file: an image.
    :return: a new image path.
    """
    try:
        img = Image.open(input_file).convert('LA')
        new_size = (int(img.size[0] * RATIO), int(img.size[1] * RATIO))
        img = img.resize(new_size, Image.ANTIALIAS)

        # Threshold
        img = img.point(lambda p: p > THRESHOLD and 255)

        # Blur + Borders?

        output_file = "output/%s.png" % uuid.uuid1()
        img.save(output_file, "PNG")
        return output_file
    except IOError as ex:
        print("Error: %s" % ex)


def call_gocr(image_path):
    """
    Calls GOCR an open source OCR software.
    :param image_path: an image path.
    :return: plain text.
    """
    # tesseract -psm 8 test.png stdout
    proc = subprocess.Popen(
        ['gocr', '%s' % image_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    result = proc.communicate()[0]
    return result.upper().strip().replace(' ', '')[0:9]


def call_tesseract(image_path):
    """
    Calls Tesseract an open source OCR software.
    :param image_path: an image path.
    :return: plain text.
    """
    cnf = '-psm 8'
    result = image_to_string(Image.open(image_path).convert('RGB'), config=cnf)
    return result.upper().strip().replace(' ', '')[0:9]


def ocr_process(image_path):
    """
    Call different OCR software and run common replacements.
    :param image_path: an image path
    :return: information dict
    """
    gocr_output = call_gocr(image_path)
    if is_valid(gocr_output):
        return {'cusip': gocr_output, 'ocr': 'GOCR', 'valid': True}

    # Tesseract
    tesseract_output = call_tesseract(image_path)
    if is_valid(tesseract_output):
        return {'cusip': tesseract_output, 'ocr': 'Tesseract', 'valid': True}

    transformations_output = common_transformations(tesseract_output)
    if is_valid(transformations_output):
        return {'cusip': transformations_output,
                'ocr': 'Tesseract + Transformations',
                'valid': True}

    transformations_output = common_transformations(gocr_output)
    if is_valid(transformations_output):
        return {'cusip': transformations_output,
                'ocr': 'GOCR + Transformations',
                'valid': True}

    return {'cusip': '%s | %s' % (gocr_output, tesseract_output),
            'ocr': 'GOCR | Tesseract',
            'valid': False}


def replace_char(text, index, replacement):
    """
    Like C++ replace
    :param text: A String
    :param index: The index
    :param replacement: Replacement char
    :return: Changed String
    """
    return '%s%s%s' % (text[:index], replacement, text[index + 1:])


def common_transformations(invalid_cusip):
    """
    Apply common string transformations
    :param invalid_cusip: An invalid CUSIP
    :return: CUSIP (Maybe valid)
    """
    # Generate inverse replacements
    common_mistakes = REPLACEMENTS[:]  # Copy
    common_mistakes.extend([(item[::-1]) for item in REPLACEMENTS])

    # Simple replacemente
    for item in common_mistakes:
        for index in range(len(invalid_cusip)):
            if item[0] == invalid_cusip[index]:
                new_cusip = replace_char(invalid_cusip, index, item[1])
                if is_valid(new_cusip):
                    return new_cusip

    # Full replacement
    for item in common_mistakes:
        new_cusip = invalid_cusip.replace(item[0], item[1])
        if is_valid(new_cusip):
            return new_cusip

    return invalid_cusip


def procces_images(*files):
    """
    Main loop!
    :param files: files to proccess.
    """
    counter = 0
    valid = 0
    for img_file in files:
        image_path = transform_image(img_file)
        if image_path:
            counter += 1
            # Call OCR
            result = ocr_process(image_path)
            print("File: %s - CUSIP: %s" % (
                img_file, result['cusip']), end='')
            if result['valid']:
                print(' - Status: ' + colored('Valid', 'green'), end='')
                valid += 1
            else:
                print(' - Status: ' + colored('Invalid!', 'red'), end='')
            print(' - OCR: %s' % result['ocr'])
            # Delete temp file!
            os.remove(image_path)
    print(colored(
        '%s/%s - %s success rate' % (valid, counter, (valid / float(counter))),
        'green'))


if __name__ == '__main__':
    procces_images(*sys.argv[1:])
