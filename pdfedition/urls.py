from django.urls import path

from . import views

urlpatterns = [
    path('pdftoword/', views.pdftoword),
    path('saveandocr/', views.uploadAndOCRFile),
    path('pdf2html/', views.pdf2html),
    path('pdf2htmlEX/', views.pdf2htmlEX),
    path('saveEditedPdf/', views.saveEditedFile)
]
