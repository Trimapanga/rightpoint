"""Read an uploaded quotation (PDF or photo) with Claude and return its content
as plain data, so it can be rebuilt as one of our own quotes."""

import base64

import anthropic
from django.conf import settings
from pydantic import BaseModel, Field

MODEL = "claude-opus-5-5"
DOCUMENT_TYPES = {
    "application/pdf": "document",
    "image/png": "image",
    "image/jpeg": "image",
    "image/webp": "image",
    "image/gif": "image",
}
INSTRUCTIONS = """You are reading a quotation written by another company (or an older quote of ours).
Copy its content faithfully so it can be re-issued on our own letterhead.

Rules:
- Customer fields describe who the quote is addressed TO, never the company that wrote it. Leave a field empty when the document does not show it.
- One entry in `lines` per priced row, in document order. Keep the item name short in `description`; put model numbers, specifications and any extra wording from the row in `details`, one fact per line.
- `unit_price` is the price for ONE unit EXCLUDING VAT. If the document only shows VAT-inclusive prices, divide out the VAT rate it states.
- `taxed` is false only for rows the document marks as VAT-exempt or zero-rated.
- `discount_percent` per line only when the row shows one; a document-wide discount goes in the top-level field as a percentage of the subtotal.
- Section headings, subtotals and totals are not lines.
- `terms`: each numbered or bulleted term or condition as its own entry.
- Use 0 or empty strings for anything the document does not state. Do not invent values."""


class ExtractedLine(BaseModel):
    description: str = Field(description="Short item name as printed.")
    details: str = Field(description="Extra specification lines for the item, newline separated. Empty if none.")
    sku: str = Field(description="Part number, model number or SKU if printed. Empty if none.")
    quantity: float
    unit_price: float = Field(description="Price of one unit excluding VAT.")
    discount_percent: float
    taxed: bool


class ExtractedQuote(BaseModel):
    customer_name: str = Field(description="Contact person the quote is addressed to.")
    company: str = Field(description="Organisation the quote is addressed to.")
    email: str
    phone: str
    site_location: str = Field(description="Delivery or installation site, if stated.")
    reference: str = Field(description="The source document's own quote number, if printed.")
    currency: str = Field(description="ISO currency code of the prices, e.g. KES or USD.")
    vat_rate: float = Field(description="VAT percentage the document applies; 0 if none.")
    discount_percent: float = Field(description="Document-wide discount as a percentage of the subtotal.")
    validity_days: int = Field(description="How many days the quote is valid for; 0 if not stated.")
    notes: str = Field(description="Any free-text note to the customer that is not a term.")
    terms: list[str]
    lines: list[ExtractedLine]


class ExtractionError(Exception):
    """Raised with a message safe to show the admin user."""


def extract_quote(data, content_type):
    kind = DOCUMENT_TYPES.get(content_type)
    if not kind:
        raise ExtractionError("Upload a PDF or an image (PNG, JPG, WEBP) of the quote.")
    api_key = getattr(settings, "ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ExtractionError("Quote import needs ANTHROPIC_API_KEY set in the server environment.")

    client = anthropic.Anthropic(api_key=api_key)
    source = {"type": "base64", "media_type": content_type, "data": base64.standard_b64encode(data).decode()}
    try:
        # A policy decline on the main model is retried server-side on a fallback model.
        response = client.beta.messages.parse(
            model=MODEL,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=INSTRUCTIONS,
            messages=[{
                "role": "user",
                "content": [
                    {"type": kind, "source": source},
                    {"type": "text", "text": "Extract this quotation."},
                ],
            }],
            output_format=ExtractedQuote,
        )
    except anthropic.BadRequestError as error:
        raise ExtractionError(f"The document could not be read: {error.message}") from error
    except anthropic.AuthenticationError as error:
        raise ExtractionError("The Anthropic API key was rejected - check ANTHROPIC_API_KEY.") from error
    except anthropic.RateLimitError as error:
        raise ExtractionError("The reading service is busy. Try again in a minute.") from error
    except (anthropic.APIStatusError, anthropic.APIConnectionError) as error:
        raise ExtractionError("The reading service could not be reached. Try again shortly.") from error

    if response.stop_reason == "refusal":
        raise ExtractionError("The document was declined by the reading service.")
    if response.stop_reason == "max_tokens" or response.parsed_output is None:
        raise ExtractionError("The document is too long to read in one go. Split it and upload the parts.")
    return response.parsed_output
