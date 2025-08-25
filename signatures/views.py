from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count
from django.utils.translation import gettext as _
from django.http import FileResponse
from .models import Document, Signee, Signature
from .forms import DocumentForm, SignatureUploadForm, SigneeForm
from .utils import send_next_invite, send_final_mail, slugify_filename


@login_required
def document_list(request):
    documents = Document.objects.all().order_by('-uploaded_at')
    return render(request, 'document_list.html', {'documents': documents})


@login_required
def document_create(request):
    signees = Signee.objects.annotate(num_signatures=Count('signature')).order_by('-num_signatures')

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.save()
            i = 1
            for signee in signees:
                include = request.POST.get(f'include_{signee.pk}') == 'on'
                already_signed = request.POST.get(f'signed_{signee.pk}') == 'on'
                position = request.POST.get(f'position_{signee.pk}') or i
                if include:
                    Signature.objects.create(
                        document=document,
                        signee=signee,
                        position=int(position),
                        signed=already_signed,
                        signed_file=document.filename,
                    )
                    i += 1
            send_next_invite(document)
            messages.success(request, _('Document has been saved and the first invite was sent.'))
            return redirect('document_list')
    else:
        form = DocumentForm()

    return render(request, 'document_form.html', {
        'form': form,
        'signees': signees
    })


@login_required
def add_signee(request):
    if request.method == 'POST':
        form = SigneeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('New signee added.'))
            return redirect('document_create')
    else:
        form = SigneeForm()
    return render(request, 'add_signee.html', {'form': form})


def sign_document(request, token):
    signature = get_object_or_404(Signature, token=token)
    if signature.signed:
        messages.info(request, _('You\'ve already signed this document.'))
        return redirect('home')

    if request.method == 'POST':
        form = SignatureUploadForm(request.POST, request.FILES)
        if form.is_valid():
            signature.mark_signed(file=form.cleaned_data['signed_file'])
            if signature.document.all_signed():
                signature.document.status = 'signed'
                signature.document.filename = signature.signed_file # type: ignore
                signature.document.save()
                send_final_mail(signature.document)
            else:
                send_next_invite(signature.document)
            messages.success(request, _('Thank you for the signature.'))
            return redirect('home')
    else:
        form = SignatureUploadForm()
    return render(request, 'sign_document.html', {'form': form, 'sig': signature})

@login_required
def download_document(request, pk):
    document = get_object_or_404(Document, pk=pk)
    response = FileResponse(document.filename, as_attachment=True, filename=slugify_filename(document.filename.name, document.name, signed=True))
    return response
