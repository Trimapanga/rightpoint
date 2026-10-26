"""File storage that keeps uploads in the database instead of on local disk."""

import mimetypes
import posixpath
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from django.utils.encoding import filepath_to_uri

# Vercel caps a function response at 4.5 MB, and phone photos are often bigger,
# so large pictures are scaled down on the way in.
MAX_IMAGE_EDGE = 2000
SHRINK_ABOVE_BYTES = 1_500_000
FORMATS = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}


def shrink_image(data, name):
    """Return `data` re-encoded smaller when it is a large raster image, else unchanged."""
    image_format = FORMATS.get(posixpath.splitext(name)[1].lower())
    if not image_format:
        return data
    from PIL import Image, ImageOps

    try:
        image = Image.open(BytesIO(data))
        too_wide = max(image.size) > MAX_IMAGE_EDGE
        if not too_wide and len(data) <= SHRINK_ABOVE_BYTES:
            return data
        image = ImageOps.exif_transpose(image)
        image.thumbnail((MAX_IMAGE_EDGE, MAX_IMAGE_EDGE))
        if image_format == "JPEG" and image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        out = BytesIO()
        options = {"optimize": True} if image_format == "PNG" else {"quality": 85}
        image.save(out, image_format, **options)
    except Exception:  # not a readable image: keep the original bytes
        return data
    shrunk = out.getvalue()
    return shrunk if len(shrunk) < len(data) else data


@deconstructible
class DatabaseStorage(Storage):
    def __init__(self, base_url="/media/"):
        self.base_url = base_url

    @staticmethod
    def _model():
        from core.models import StoredFile

        return StoredFile

    def _open(self, name, mode="rb"):
        row = self._model().objects.get(name=name)
        file = ContentFile(bytes(row.content), name=name)
        return file

    def _save(self, name, content):
        content.seek(0)
        data = shrink_image(content.read(), name)
        content_type = getattr(content, "content_type", None) or mimetypes.guess_type(name)[0] or ""
        self._model().objects.update_or_create(
            name=name,
            defaults={"content": data, "content_type": content_type[:100], "size": len(data)},
        )
        return name

    def delete(self, name):
        self._model().objects.filter(name=name).delete()

    def exists(self, name):
        return self._model().objects.filter(name=name).exists()

    def size(self, name):
        return self._model().objects.values_list("size", flat=True).get(name=name)

    def url(self, name):
        return self.base_url + filepath_to_uri(name)

    def get_modified_time(self, name):
        return self._model().objects.values_list("updated_at", flat=True).get(name=name)

    def listdir(self, path):
        prefix = path.rstrip("/") + "/" if path else ""
        directories, files = set(), []
        for name in self._model().objects.filter(name__startswith=prefix).values_list("name", flat=True):
            head, _, tail = name[len(prefix):].partition("/")
            if tail:
                directories.add(head)
            else:
                files.append(head)
        return sorted(directories), files
