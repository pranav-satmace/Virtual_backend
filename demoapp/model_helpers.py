# Standard Library
import hashlib
import io
import os
import re
import secrets
import string
import uuid
from typing import Any, Callable, Dict, List

import qrcode
from django.core.exceptions import ValidationError
from django.db import connection
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext as _
from PIL import Image
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import CircleModuleDrawer

from .taxonomies import Status

PAN_REGEX = "[A-Z]{3}[CPHFATBLJGE]{1}[A-Z]{1}\d{4}[A-Z]{1}"  # noqa
GSTIN_REGEX = "\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}"  # noqa


def dictfetchall(cursor: Any) -> List[Dict]:
    """
    Return all rows from a cursor as a dict.
    Assume the column names are unique.
    """
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def exec_sql(query, *args):
    with connection.cursor() as cursor:
        cursor.execute(query, args)
        return dictfetchall(cursor)


def gstin_check(value):
    pattern = re.compile(GSTIN_REGEX)
    if pattern.match(value) is None:
        raise ValidationError(_("Invalid GSTIN"), code="invalid_gst_number")


def pan_check(value):
    pattern = re.compile(PAN_REGEX)
    return pattern.match(value) is not None


def timezone_date():
    return timezone.now().date()


def past_date_check(value):
    if value > timezone_date():
        raise ValidationError(
            _("Date cannot be in the future."), params={"value": value}
        )


def future_date_check(value):
    if value < timezone_date():
        raise ValidationError(
            _("Date cannot be in the past."), params={"value": value}
        )


def limit_to_active():
    return {"is_active": True}


def limit_to_approved():
    return {"status": Status.APPROVED}


def limit_to_unarchived():
    return {"is_archived": False}


def create_slug(model, instance, field, slug_field="slug") -> str:
    if type(field) in [list, tuple, set]:
        key = " ".join([str(getattr(instance, x)) for x in field])
    else:
        key = getattr(instance, field)
    slug = slugify(key)
    while True:
        if model.objects.filter(**{slug_field: slug}).exists():
            slug = slug + "-" + random_alphanum(5)
        else:
            break
    return slug


def random_alphanum(size: int = 8, mix_case: bool = False) -> str:
    choice_set = string.ascii_lowercase + string.digits
    if mix_case:
        choice_set += string.ascii_uppercase
    return "".join(secrets.SystemRandom().choices(choice_set, k=size))


def create_random_alphanum(model, size, mix_case, store_field) -> str:
    value = random_alphanum(size, mix_case)
    while True:
        if model.objects.filter(**{store_field: value}).exists():
            value = random_alphanum(size, mix_case)
        else:
            break
    return value


def create_code(prefix: str, dt=None) -> str:
    if not dt:
        dt = timezone_date()
    return f"{prefix}-{uuid.uuid4().hex.upper()[:6]}"


def create_qr_code(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex.upper()[0:6]}"


def random_pin() -> int:
    return secrets.SystemRandom().randint(100000, 999999)


def dict_get_or_insert(dct: dict, key, func: Callable) -> Any:
    if key in dct:
        return dct[key]
    res = func()
    dct[key] = res
    return res


def hash_text(txt: str) -> str:
    return hashlib.sha256(txt.encode("utf-8")).hexdigest()


def blake2s_digest(byt):
    blake = hashlib.blake2s()
    blake.update(byt)
    return blake.hexdigest()


def attach_qr(text: str):
    logo = Image.open("./global_static/images/qr_logo.jpg")
    QRcode = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
    )
    QRcode.add_data(text)
    QRcode.make(fit=True)
    QRimg = QRcode.make_image(
        image_factory=StyledPilImage,
        module_drawer=CircleModuleDrawer(),
    )
    qr_width, qr_height = QRimg.size
    logo_width = int(qr_width * 0.3)
    logo_height = int(qr_height * 0.3)
    logo = logo.resize((logo_width, logo_height), Image.ANTIALIAS)
    pos = (
        (qr_width - logo_width) // 2,
        (qr_height - logo_height) // 2,
    )
    # QRimg.paste(logo, pos)
    bytes_buffer = io.BytesIO()
    QRimg.save(bytes_buffer, "PNG")
    return bytes_buffer


def path_and_rename(instance, filename):
    ext = filename.split(".")[-1]
    # get filename
    if instance.uid:
        filename = "{}.{}".format(instance.uid, ext)
    else:
        # set filename as random string
        filename = "{}.{}".format(uuid.uuid4().hex, ext)
    # return the whole path to the file
    return os.path.join(instance.IMAGE_PATH, filename)
