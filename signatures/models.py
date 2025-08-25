from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext as _
import uuid
from .utils import slugify_filename

STATUS_CHOICES = [
    ('pending', _('Pending')),
    ('signed', _('Signed')),
    ('archived', _('Archived'))
]

def make_token():
    return uuid.uuid4().hex


class Document(models.Model):
    name = models.CharField(max_length=250)
    comment = models.CharField(max_length=500, blank=True)
    filename = models.FileField(upload_to='documents/originals')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_documents')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return _('Document no. {number} - {name}').format(number=self.pk, name=self.name)

    def all_signed(self):
        return not self.signatures.filter(signed=False).exists() # type: ignore


class Signee(models.Model):
    name = models.CharField(max_length=250)
    email = models.EmailField(unique=True)

    def __str__(self):
        return f'{self.name} <{self.email}>'


class Signature(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='signatures')
    signee = models.ForeignKey(Signee, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()
    signed = models.BooleanField(default=False)
    signed_at = models.DateTimeField(null=True, blank=True)
    token = models.CharField(max_length=64, unique=True, default=make_token)
    signed_file = models.FileField(upload_to='documents/signatures', null=True, blank=True)
    last_invite_sent_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['position']
        unique_together = ('document', 'position')

    def __str__(self):
        return _('{document}: {signee} (pos {position})').format(document=self.document, signee=self.signee, position=self.position)

    def mark_signed(self, file=None):
        self.signed = True
        self.signed_at = timezone.now()
        if file:
            self.signed_file.save(f'doc{self.document.pk}_signee{self.signee.pk}_{slugify_filename(file.name, self.document.name)}', file)
        self.save()
