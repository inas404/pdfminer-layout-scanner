#!/usr/bin/python

import sys
import os
from binascii import b2a_hex


###
### pdf-miner requirements
###

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument, PDFNoOutlines
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTFigure, LTImage, LTChar
from pdfminer.layout import LTContainer, LTPage, LTText, LTLine, LTRect, LTCurve
from pdfminer.layout import LTTextBoxVertical, LTTextGroup

def with_pdf (pdf_doc, fn, pdf_pwd, *args):
    """Open the pdf document, and apply the function, returning the results"""
    result = None
    try:
        # open the pdf file
        fp = open(pdf_doc, 'rb')
        # create a parser object associated with the file object
        parser = PDFParser(fp)
        # create a PDFDocument object that stores the document structure
        doc = PDFDocument(parser)
        # connect the parser and document objects
        parser.set_document(doc)
        # supply the password for initialization
        # doc.initialize(pdf_pwd)

        if doc.is_extractable:
            # apply the function and return the result
            result = fn(doc, *args)

        # close the pdf file
        fp.close()
    except IOError:
        # the file doesn't exist or similar problem
        pass
    return result


### 
### Table of Contents
### 

def _parse_toc (doc):
    """With an open PDFDocument object, get the table of contents (toc) data
    [this is a higher-order function to be passed to with_pdf()]"""
    toc = []
    try:
        outlines = doc.get_outlines()
        for (level,title,dest,a,se) in outlines:
            toc.append( (level, title) )
    except PDFNoOutlines:
        pass
    return toc

def get_toc (pdf_doc, pdf_pwd=''):
    """Return the table of contents (toc), if any, for this pdf file"""
    return with_pdf(pdf_doc, _parse_toc, pdf_pwd)


###
### Extracting Images
###

def write_file (folder, filename, filedata, flags='w'):
    """Write the file data to the folder and filename combination
    (flags: 'w' for write text, 'wb' for write binary, use 'a' instead of 'w' for append)"""
    result = False
    if os.path.isdir(folder):
        try:
            file_obj = open(os.path.join(folder, filename), flags)
            file_obj.write(filedata)
            file_obj.close()
            result = True
        except IOError:
            pass
    return result

def determine_image_type (stream_first_4_bytes):
    """Find out the image file type based on the magic number comparison of the first 4 (or 2) bytes"""
    file_type = None
    bytes_as_hex = b2a_hex(stream_first_4_bytes)
    if bytes_as_hex.startswith('ffd8'):
        file_type = '.jpeg'
    elif bytes_as_hex == '89504e47':
        file_type = '.png'
    elif bytes_as_hex == '47494638':
        file_type = '.gif'
    elif bytes_as_hex.startswith('424d'):
        file_type = '.bmp'
    return file_type

def save_image (lt_image, page_number, images_folder):
    """Try to save the image data from this LTImage object, and return the file name, if successful"""
    result = None
    if lt_image.stream:
        file_stream = lt_image.stream.get_rawdata()
        if file_stream:
            file_ext = determine_image_type(file_stream[0:4])
            if file_ext:
                file_name = ''.join([str(page_number), '_', lt_image.name, file_ext])
                if write_file(images_folder, file_name, file_stream, flags='wb'):
                    result = file_name
    return result


###
### Extracting Text
###

def to_bytestring (s, enc='utf-8'):
    """Convert the given unicode string to a bytestring, using the standard encoding,
    unless it's already a bytestring"""
    if s:
        if isinstance(s, str):
            return s
        else:
            return s.encode(enc)

def update_page_text_hash (h, lt_obj, pct=0.2):
    """Use the bbox x0,x1 values within pct% to produce lists of associated text within the hash"""

    x0 = lt_obj.bbox[0]
    x1 = lt_obj.bbox[2]

    key_found = False
    for k, v in h.items():
        hash_x0 = k[0]
        if x0 >= (hash_x0 * (1.0-pct)) and (hash_x0 * (1.0+pct)) >= x0:
            hash_x1 = k[1]
            if x1 >= (hash_x1 * (1.0-pct)) and (hash_x1 * (1.0+pct)) >= x1:
                # the text inside this LT* object was positioned at the same
                # width as a prior series of text, so it belongs together
                key_found = True
                v.append(to_bytestring(lt_obj.get_text()))
                h[k] = v
    if not key_found:
        # the text, based on width, is a new series,
        # so it gets its own series (entry in the hash)
        h[(x0,x1)] = [to_bytestring(lt_obj.get_text())]

    return h

idd=0
def map_coordinates(bbox,pgnum,font,size,img_width,img_height,line_spacing):
    # left = x0, top = (50-y1)
    # top = pgnum*50-bbox[3] 
    top = 1.5*(936*pgnum - bbox[3])   #top = 936 - y1
    # left = bbox[0]
    left = 1.8*bbox[0]              #left = x0
    width = 1.8*(bbox[2]-bbox[0])     #width = x1-x0
    
    #write to css file the new id style
    # #outer { 
    #        position: absolute; 
    #        top: 0px; left: 0px; 
    #        width: 200px; 
    #        color: red;
    #      }
    img_width*=1.8
    img_height*=1
    line_spacing*=1.5
    # size*=0.7
    # css = '#id_'+ str(idd) + ' {\n position: absolute;\n top: '+ str(top)+'px; left: ' + str(left) +'px;\n width: '+ str(width) + 'px;\n font-family: \"'+ font+'\";\n font-size: '+ str(size) + 'pt;\nwidth: '+str(img_width)+'px; height: '+str(img_height)+'%;\n}\n'
    css = '#id_'+ str(idd) + ' {\n position: absolute;\n top: '+ str(top)+'px; left: ' + str(left) +'px;\n font-family: \"'+ font+'\";\n font-size: '+ str(size) + 'px;\n line-height: '+str(line_spacing)+'px;\n width: '+str(img_width)+'px;\n height: '+str(img_height)+'%;\n}\n'
    
    f = open('css/mystyle.css','a')
    f.write(css)
    f.close()
    global idd
    idd+=1
    return idd-1

import operator
figs=[]
def parse_lt_objs (lt_objs, page_number, images_folder, text=[]):
    """Iterate through the list of LT* objects and capture the text or image data contained in each"""
    text_content = [] 

    page_text = {} # k=(x0, x1) of the bbox, v=list of text strings within that bbox width (physical column)
    for lt_obj in lt_objs:
        if isinstance(lt_obj, LTImage):
            # an image, so save it to the designated folder, and note its place in the text 
            saved_file = save_image(lt_obj, page_number, images_folder)
            if saved_file:
                # use html style <img /> tag to mark the position of the image within the text
                idd=map_coordinates(lt_obj.bbox,page_number,"",0,lt_obj.width, lt_obj.height,0)
                figs.append((idd,os.path.join(images_folder, saved_file),lt_obj))                
            else:
                print >> sys.stderr, "error image not jpeg on page", page_number
        elif isinstance(lt_obj, LTFigure):
            # LTFigure objects are containers for other LT* objects, so recurse through the children
            parse_lt_objs(lt_obj, page_number, images_folder, text_content)
        elif isinstance(lt_obj,LTTextBox):
            fontname=""
            size=0
            line_spacing = 0
            j = 0
            for x in lt_obj:
                # print('___',x)
                if isinstance(x,LTTextLine):
                    # print('******',x)
                    for y in x:
                        if isinstance(y,LTChar):
                            fontname = y.fontname.split('+')
                            fontname = fontname[len(fontname)-1].strip()
                            size = y.size
                    if j==0 and len(lt_obj)<2:
                        line_spacing=0
                        break
                    elif j==1:
                        line_spacing -= x.bbox[1]
                        break
                    
                    line_spacing = x.bbox[1]
                    j+=1
            idd=map_coordinates(lt_obj.bbox,page_number,fontname,size,lt_obj.width,lt_obj.height,line_spacing)
            figs.append((idd,to_bytestring(lt_obj.get_text()),lt_obj))
        elif isinstance(lt_obj, LTRect) or isinstance(lt_obj, LTLine):
            figs.append((idd,lt_obj.x0,lt_obj.y1,lt_obj.width,lt_obj.height,page_number,lt_obj))

###
### Processing Pages
###

def _parse_pages (doc, images_folder):
    """With an open PDFDocument object, get the pages and parse each one
    [this is a higher-order function to be passed to with_pdf()]"""
    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    text_content = []
    for i, page in enumerate(PDFPage.create_pages(doc)):
        interpreter.process_page(page)
        # receive the LTPage object for this page
        layout = device.get_result()
        # layout is an LTPage object which may contain child objects like LTTextBox, LTFigure, LTImage, etc.
        figs.append((i+1,'p'))
        parse_lt_objs(layout, (i+1), images_folder)

    return figs

def get_pages (pdf_doc, pdf_pwd='', images_folder='img'):
    """Process each of the pages in this pdf file and return a list of strings representing the text found in each page"""
    return with_pdf(pdf_doc, _parse_pages, pdf_pwd, *tuple([images_folder]))
