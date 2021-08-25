from django.http.response import HttpResponse
from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import logging

import re
from datetime import datetime
import subprocess

from rest_framework.decorators import api_view
from rest_framework.response import Response

from pdf2docx import parse, converter
from ocrmypdf import ocr
import pdftotree
from bs4 import BeautifulSoup as bs
from pdfkit import from_file

# Create your views here.

logger = logging.getLogger(__name__)

fs = FileSystemStorage(location = settings.MEDIA_ROOT)

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
        for div in soup.select('div[class*="t "]'):
            div['contentEditable'] = 'true'

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
        filename = html_file.name[:-5] + '.pdf'
        pdf_file_path = settings.MEDIA_ROOT + '/' + filename

        fs.save(content=html_file, name=html_file.name)
        from_file(settings.MEDIA_ROOT + '/' + html_file.name, pdf_file_path)

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
