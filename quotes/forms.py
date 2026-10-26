from django import forms

from quotes.extraction import DOCUMENT_TYPES

MAX_UPLOAD_MB = 20


class QuoteImportForm(forms.Form):
    document = forms.FileField(
        label="Quote to copy",
        help_text=f"PDF, or a clear photo or scan (PNG, JPG, WEBP). Up to {MAX_UPLOAD_MB} MB.",
        widget=forms.ClearableFileInput(attrs={"accept": ",".join(DOCUMENT_TYPES)}),
    )
    use_catalogue_prices = forms.BooleanField(
        label="Use our selling prices where an item matches the catalogue",
        required=False,
        help_text="Leave unticked to keep the prices printed on the uploaded quote.",
    )

    def clean_document(self):
        document = self.cleaned_data["document"]
        if document.size > MAX_UPLOAD_MB * 1024 * 1024:
            raise forms.ValidationError(f"Keep the file under {MAX_UPLOAD_MB} MB.")
        if document.content_type not in DOCUMENT_TYPES:
            raise forms.ValidationError("Upload a PDF or an image (PNG, JPG, WEBP).")
        return document
