import os
from typing import Any
from django import forms
from django.utils.translation import gettext as _
from django.utils.text import slugify
from .models import Document, Signee
from .utils import slugify_filename


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['name', 'filename', 'comment']
        labels = {
            'name': _('Document name'),
            'filename': _('File'),
            'comment': _('Comment'),
        }

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        data = self.data
        errors = []
        positions = {}        
        included = []
        signed = []
        specified_positions = 0

        for key in data:
            if key.startswith('include_'):
                included.append(int(key.split('_')[1]))
            if key.startswith('signed_'):
                signed.append(int(key.split('_')[1]))
            if key.startswith('position_') and data[key]:
                specified_positions += 1

        for pk in signed:
            if pk not in included:
                errors.append(_('Signee {pk} cannot be marked as \'already signed\' without being included.').format(pk=pk))

        expected_positions = list(range(1, len(included) + 1))
        got_positions = sorted(positions.values())
        if specified_positions != 0 and got_positions != expected_positions:
            errors.append(_('Positions must be consecutive from 1 to {max_pos}.').format(max_pos=len(included)))
        if specified_positions != 0 and specified_positions != len(included):
            errors.append(_('Positions must be spcified for all or for none.'))
        if len(included) == 0 or len(included) == len(signed):
            errors.append(_('You need to add at least one signee that didn\'t sign the document yet.'))

        if errors:
            raise forms.ValidationError(errors)
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        file = self.cleaned_data.get('filename')
        if file:
            file.name = slugify_filename(file.name, instance.name)
            instance.filename = file
        if commit:
            instance.save()
        return instance


class SignatureUploadForm(forms.Form):
    signed_file = forms.FileField()


class SigneeForm(forms.ModelForm):
    class Meta:
        model = Signee
        fields = ['name', 'email']
