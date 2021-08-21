from django.http.response import HttpResponse
from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import logging

import re
from datetime import datetime

from rest_framework.decorators import api_view
from rest_framework.response import Response

from pdf2docx import parse
from ocrmypdf import ocr

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

