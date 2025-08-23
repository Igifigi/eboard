from django.contrib import admin
from .models import Document, Signee, Signature

admin.site.register(Document)
admin.site.register(Signee)
admin.site.register(Signature)
