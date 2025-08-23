from django.urls import path
from . import views

urlpatterns = [
    path('', views.document_list, name='document_list'),
    path('new/', views.document_create, name='document_create'),
    path('add-signee/', views.add_signee, name='add_signee'),
    path('sign/<str:token>/', views.sign_document, name='sign_document'),
]
