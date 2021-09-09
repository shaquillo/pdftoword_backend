from os import name
from django.http.response import HttpResponse
from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import logging

import re
from datetime import datetime
import subprocess
from django.utils.functional import empty

from rest_framework.decorators import api_view
from rest_framework.response import Response

from pdf2docx import parse, converter
from ocrmypdf import ocr
import pdftotree
from bs4 import BeautifulSoup as bs
from pdfkit import from_file
from django_selenium_pdfmaker.modules import PDFMaker
import pypandoc
from htmldocx import HtmlToDocx
from cssutils import parseStyle


# Create your views here.

logger = logging.getLogger(__name__)

fs = FileSystemStorage(location = settings.MEDIA_ROOT)

html_to_doc_parser = HtmlToDocx()

px2pt_factor = 1.333333

@api_view(['POST'])
def pdftoword(request):
    logger.info('call to pdftoword')
    if request.data['filename']:
        base_file_path = settings.MEDIA_ROOT + '/' + request.data['filename']
        file_path = base_file_path + '.pdf'  ## considering that the file has .pdf at the end
        doc_file_name = base_file_path + '.docx' 
        
        parse(pdf_file=file_path, docx_file=doc_file_name)
        # converter(file_path, doc_file_name)

        try :
            with open(doc_file_name, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/msword')
                response['Content-Disposition'] = 'attachment; filename="' + doc_file_name + '"'

                return response
        except Exception as e:
            logger.info('Error when opening file')
            print(e)
            return Response({'message': 'Could not open or find doc file'})
                
    return Response({'message': 'Need to pass filename'})


@api_view(['GET'])
def getpdf(request):
    logger.info('call to getpdf')

    if request.query_params['filename']:
        filename = request.query_params['filename']
        pdf_file_path = settings.MEDIA_ROOT + '/' + filename
        logger.info('pdf_file_path: ' + pdf_file_path)

        
        try :
            with open(pdf_file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="' + filename + '"'

                return response
        except Exception as e:
            logger.info('Error when opening file')
            print(e)
            return Response({'message': 'Could not open or find doc file'})
        
    return Response({'message': 'No pdf file passed in form data'})


@api_view(['POST'])
def uploadAndOCRFile(request):
    logger.info('Call to upload and ocr on pdf file')
    if request.FILES['pdf']:
        pdf_file = request.FILES['pdf']

        now = datetime.now()
        dt_string = now.strftime("%d-%m-%Y_%H-%M-%S")
        saved_filename = 'f' + dt_string + '.pdf'

        fs.save(content=pdf_file, name=saved_filename)

        return Response({'message': 'file saved', 'filename': saved_filename})

    return Response({'message': 'No pdf file passed in form data'})


@api_view(['POST'])
def pdf2html(request):
    logger.info('call to pdf2html')
    if request.data['filename']:
        base_file_path = settings.MEDIA_ROOT + '/' + request.data['filename']
        file_path = base_file_path + '.pdf'  ## considering that the file has .pdf at the end
        html_file_name = base_file_path + '.html' 
        
        pdftotree.parse(file_path, html_path=html_file_name)

        try :
            with open(html_file_name, 'rb') as f:
                response = HttpResponse(f.read(), content_type='text/html')
                response['Content-Disposition'] = 'attachment; filename="' + html_file_name + '"'

                return response
        except Exception as e:
            logger.info('Error when opening file')
            print(e)
            return Response({'message': 'Could not open or find file'})
                
    return Response({'message': 'Need to pass filename'})


@api_view(['POST'])
def pdf2htmlEX(request):
    logger.info('call to pdf2htmlEX')
    if request.data['filename']:
        base_file_path = settings.MEDIA_ROOT + '/' + request.data['filename']
        file_path = base_file_path + '.pdf'  ## considering that the file has .pdf at the end
        save_file_path = 'media/' + request.data['filename'] + '.html'
        html_file_name = base_file_path + '.html' 
        
        subprocess.call("pdf2htmlEX " + file_path + " " + save_file_path, shell=True)   ## or subprocess.call(["pdf2htmlEX", file_path, html_file_name], shell=False)

        html = open(html_file_name)
        soup = bs(html, 'html.parser')

        script = "window.onload = function(){var inputs = []; var i = 0; "
        pages = soup.select("div[class^=pf]")

        for i in range(1, len(pages) + 1):
            script += "document.getElementById('pf"+ str(i) +"').onclick = function clickEvent(e) { if(!inputs.includes(e.target.id) && !e.target.classList.contains('t')){ var rect = document.getElementById('pf"+ str(i) +"').getBoundingClientRect();let x = e.clientX - rect.left;let y = e.clientY - rect.top;console.log('Left? : ' + x + ' ; Top? : ' + y + '.');const errorElem = document.createElement('input');errorElem.style.top = y.toString()+'px';errorElem.style.left =x.toString()+'px';errorElem.style.position = 'absolute';errorElem.placeholder = 'enter text';errorElem.id = 'input' + i;errorElem.value = '';errorElem.style.minWidth = '60px';i+=1;const divElem = document.createElement('div');function createDiv(){if(document.getElementById(errorElem.id).value !== ''){divElem.style.top = errorElem.style.top;divElem.style.left = errorElem.style.left;divElem.style.position = 'absolute';divElem.style.fontSize = '15px';divElem.id = errorElem.id;divElem.innerHTML = errorElem.value;divElem.onclick = function(e){divElem.draggable = 'false';divElem.contentEditable = 'true';};divElem.onmousemove = function(e){if(document.activeElement !== divElem){divElem.draggable = 'true';divElem.contentEditable = 'false';}};document.getElementById('pf" + str(i) + "').appendChild(divElem);function drag_start(event) {var style = window.getComputedStyle(event.target, null);event.dataTransfer.setData('text/plain',(parseInt(style.getPropertyValue('left'),10) - event.clientX) + ',' + (parseInt(style.getPropertyValue('top'),10) - event.clientY) +  ',' + divElem.id);} function drag_over(event) { event.preventDefault(); return false; } function drop(event) { var offset = event.dataTransfer.getData('text/plain').split(',');var elem = document.getElementById(offset[2]);elem.style.left = (event.clientX + parseInt(offset[0],10)) + 'px';elem.style.top = (event.clientY + parseInt(offset[1],10)) + 'px';event.preventDefault();return false;} divElem.addEventListener('dragstart',drag_start,false); document.body.addEventListener('dragover',drag_over,false); document.body.addEventListener('drop',drop,false); }errorElem.remove();} errorElem.onblur = (e) => {createDiv();};errorElem.addEventListener('keydown', (e) =>{if(e.key === 'Enter'){createDiv();}}); errorElem.addEventListener('input', resizeInput);resizeInput.call(errorElem);function resizeInput() {this.style.width = this.value.length + 'ch';}document.getElementById('pf"+ str(i) +"').appendChild(errorElem);inputs.push(errorElem.id);}};"

        script += "}"

        for div in soup.select('div[class*="t "]'):
            div['contentEditable'] = 'true'
        
        script_tag = soup.new_tag('script')
        script_tag.string = script

        soup.html.body.append(script_tag)

        with open(html_file_name, 'w') as f:
            f.write(str(soup))

        try :
            with open(html_file_name, 'rb') as f:
                response = HttpResponse(f.read(), content_type='text/html')
                response['Content-Disposition'] = 'attachment; filename="' + html_file_name + '"'

                return response
        except Exception as e:
            logger.info('Error when opening file')
            print(e)
            return Response({'message': 'Could not open or find file'})
                
    return Response({'message': 'Need to pass filename'})


@api_view(['POST'])
def saveEditedFile(request):
    logger.info('call to saveEditedFile')
    if request.FILES['html']:
        html_file = request.FILES['html']
        print(html_file.name)
        filename = html_file.name[:-5] + '.pdf'
        pdf_file_path = settings.MEDIA_ROOT + '/' + filename
        html_file_path = settings.MEDIA_ROOT + '/' + html_file.name

        if(fs.exists(html_file.name)):
            fs.delete(html_file.name)
        fs.save(content=html_file, name=html_file.name)


        ## changing position values and font-size values before converting to pdf
        html = open(html_file_path)
        soup = bs(html, 'html.parser')

        for empty_input in soup.select('input[id^="input"]'):
            empty_input.clear()

        for new_text_div in soup.select('div[id^="input"]'):
            style = parseStyle(new_text_div['style'])
            style['left'] = "{:.6f}pt".format(float(style['left'][:-2])*px2pt_factor)
            style['top'] = "{:.6f}pt".format(float(style['top'][:-2])*px2pt_factor)
            style['font-size'] = "{:.6f}pt".format(float(style['font-size'][:-2])*px2pt_factor)
            new_text_div['style'] = style.cssText

        with open(html_file_path, 'w') as f:
            f.write(str(soup))

        from_file(settings.MEDIA_ROOT + '/' + html_file.name, pdf_file_path)    # add
        # subprocess.call("ocrmypdf " + pdf_file_path + " " + pdf_file_path + " --force-ocr", shell=True)

        # subprocess.call("pandoc " + settings.MEDIA_ROOT + '/' + html_file.name + " -o " + pdf_file_path, shell=True)

        # html_to_doc_parser.parse_html_file(settings.MEDIA_ROOT + '/' + html_file.name, docx_file_path)
        # subprocess.call("pandoc " + settings.MEDIA_ROOT + '/' + html_file.name + " -o " + docx_file_path, shell=True)
        # subprocess.call("pandoc " + docx_file_path + " -o " + pdf_file_path, shell=True)

        # return 'done'

        try :
            with open(pdf_file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="' + filename + '"'

                return response
        except Exception as e:
            logger.info('Error when opening file')
            print(e)
            return Response({'message': 'Could not open or find doc file'})
        
    return Response({'message': 'No pdf file passed in form data'})


@api_view(['POST'])
def saveEditedPdf(request):
    logger.info('Call to save edited pdf')
    if request.FILES['pdf']:
        pdf_file = request.FILES['pdf']
        filename = pdf_file.name
        pdf_file_path = settings.MEDIA_ROOT + '/' +  filename

        if fs.exists(filename):
            fs.delete(filename)
        fs.save(content=pdf_file, name=filename)

        try :
            with open(pdf_file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="' + filename + '"'

                return response
        except Exception as e:
            logger.info('Error when opening file')
            print(e)
            return Response({'message': 'Could not open or find doc file'})

    return Response({'message': 'No pdf file passed in form data'})
