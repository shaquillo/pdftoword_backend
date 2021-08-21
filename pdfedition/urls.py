from django.urls import path

from . import views

urlpatterns = [
    path('pdftoword/', views.pdftoword),
    path('saveandocr/', views.uploadAndOCRFile)
]
