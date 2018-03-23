from django import forms
from django.utils.translation import pgettext_lazy

from ...page.models import Page
from ..product.forms import RichTextField
from ..seo.utils import (
    MIN_DESCRIPTION_LENGTH, MIN_TITLE_LENGTH, SEO_HELP_TEXTS, SEO_LABELS,
    SEO_WIDGETS, prepare_seo_description)


class PageForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['seo_description'].widget.attrs.update({
            'data-bind': self['content'].auto_id,
            'data-materialize': self['content'].html_name,
            'min-recommended-length': MIN_DESCRIPTION_LENGTH})
        self.fields['seo_title'].widget.attrs.update({
            'data-bind': self['title'].auto_id,
            'min-recommended-length': MIN_TITLE_LENGTH})

    class Meta:
        model = Page
        exclude = []
        widgets = {
            'slug': forms.TextInput(attrs={'placeholder': 'example-slug'}),
            **SEO_WIDGETS}
        labels = {
            'is_visible': pgettext_lazy(
                'Visibility status indicator', 'Publish'),
            **SEO_LABELS}
        help_texts = {
            'slug': pgettext_lazy(
                'Form field help text',
                'Slug is being used to create page URL'),
            **SEO_HELP_TEXTS}

    content = RichTextField()

    def clean_slug(self):
        # Make sure slug is not being written to database with uppercase.
        slug = self.cleaned_data.get('slug')
        slug = slug.lower()
        return slug

    def clean_seo_description(self):
        seo_description = prepare_seo_description(
            seo_description=self.cleaned_data['seo_description'],
            html_description=self.data['content'],
            max_length=self.fields['seo_description'].max_length)
        return seo_description
