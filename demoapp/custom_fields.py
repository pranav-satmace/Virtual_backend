# Standard Library

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import CharField, FloatField
from django.utils.translation import gettext as _

from .model_helpers import gstin_check, pan_check


class UpperCharField(CharField):
    def get_prep_value(self, value):
        if value:
            return super(UpperCharField, self).get_prep_value(value).upper()
        else:
            return value


class PercentField(FloatField):
    default_validators = [MinValueValidator(0.0), MaxValueValidator(1.0)]
    description = _("Percent field")

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("default", 0)
        super().__init__(*args, **kwargs)


class PositiveFloatField(FloatField):
    default_validators = [MinValueValidator(0.0)]
    description = _("Positive field")


class GSTField(CharField):
    default_validators = [gstin_check]
    description = _("Goods and Services Tax")

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 15)
        super().__init__(*args, **kwargs)


class PANField(CharField):
    default_validators = [pan_check]
    description = _("Permanent account number")

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 10)
        super().__init__(*args, **kwargs)
