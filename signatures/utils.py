
from django.urls import reverse
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext as _
import os


def send_next_invite(document):
    signature = document.signatures.filter(signed=False).order_by('position').first() # gets the first to sign
    if not signature:
        return
    link = settings.SITE_URL + reverse('sign_document', args=[signature.token])

    context = {
        'name': document.name,
        'comment': document.comment or _('none'),
        'sign_link': link,
        'number': document.pk,
        'uploaded_by': document.uploaded_by,
    }
    message = render_to_string('emails/invitation.html', context)

    email = EmailMessage(
        subject=_('Request to sign the document {name}').format(name=document.name),
        body=message,
        from_email=settings.EMAIL_HOST_USER,
        to=[signature.signee.email],
    )
    email.content_subtype = 'html'

    if signature.position == 1:
        email.attach_file(signature.document.filename.path)
    elif signature.position > 1 and len(document.signatures.filter(position=signature.position-1)) != 0:
        email.attach_file(document.signatures.get(position=signature.position-1).signed_file.path)
    else:
        raise ValueError(_('Couldn\'t find attachment.'))

    email.send()

    signature.last_invite_sent_at = timezone.now()
    signature.save()


def send_final_mail(document):
    context = {
        'name': document.name,
        'comment': document.comment or _('none'),
        'number': document.pk,
        'uploaded_by': document.uploaded_by,
    }
    message = render_to_string('emails/invitation.html', context)
    email = EmailMessage(
        subject=_('Document {name} was signed').format(name=document.name),
        body=message,
        from_email=settings.EMAIL_HOST_USER,
        to=[settings.EMAIL_ADMIN],
    )
    email.content_subtype = 'html'

def slugify_filename(filename: str, document_name: str, signed=False) -> str:
    extension = os.path.splitext(filename)[1]
    base = (slugify(document_name) or 'doc') if not signed else (f'{slugify(document_name)}_signed' or 'doc-signed')
    return f'{base}{extension}'
