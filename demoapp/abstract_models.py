# Standard Library
import uuid

#import requests
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import IntegrityError
from django.db.models import (
    PROTECT,
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    EmailField,
    FileField,
    FloatField,
    ForeignKey,
    IntegerField,
    JSONField,
    Model,
    PositiveIntegerField,
    TextField,
    URLField,
    UUIDField,
)
from django_countries.fields import CountryField
from easy_thumbnails.fields import ThumbnailerImageField
from loguru import logger
from phonenumber_field.modelfields import PhoneNumberField
from rest_framework.serializers import (
    ValidationError as SerializerValidationError,
)

from .custom_fields import (
    PercentField,
    PositiveFloatField,
    UpperCharField,
)
from .model_helpers import pan_check, past_date_check, timezone_date
from .taxonomies import (
    AdjustmentType,
    DynamicEnumType,
    EntityType,
    MSMEType,
    Status,
)


class CreateUpdate(Model):
    uid = UUIDField(default=uuid.uuid4, unique=True)
    created = DateTimeField(auto_now_add=True)
    updated = DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CreateUpdateStatus(CreateUpdate):
    is_active = BooleanField(default=True)

    class Meta:
        abstract = True


class ArchiveField(Model):
    is_archived = BooleanField(default=False)

    class Meta:
        abstract = True


class ApprovalField(Model):
    status = CharField(
        max_length=32,
        default=Status.DRAFT,
        choices=Status.choices,
    )
    approve_datetime = DateTimeField(blank=True, null=True)
    approved_by = ForeignKey(to=User, on_delete=PROTECT, blank=True, null=True)

    class Meta:
        abstract = True

    @property
    def is_approved(self):
        return self.status == Status.APPROVED

    @property
    def status_display(self):
        return self.get_status_display()


class AbstractDocument(Model):
    document_name = CharField(max_length=255, blank=True, null=True)
    document = FileField()
    remarks = TextField(blank=True)

    class Meta:
        abstract = True


class AbstractImage(Model):
    image_name = CharField(max_length=255, blank=True, null=True)
    image = ThumbnailerImageField()
    remarks = TextField(blank=True)

    class Meta:
        abstract = True


class AbstractBankAccount(Model):
    account_number = CharField(max_length=32)
    ifsc_code = CharField(
        max_length=11,
        validators=[MinLengthValidator(11)],
        verbose_name="IFSC Code",
        help_text=(
            "This will auto generate Bank Name, Branch "
            "(if not custom-entered), MICR, Swift Code"
        ),
    )
    bank_name = CharField(max_length=255, blank=True)
    swift_code = CharField(max_length=255, blank=True)
    micr = CharField(max_length=255, blank=True)
    branch = CharField(max_length=512, blank=True)
    intermediate_bank_name = CharField(max_length=255, blank=True)
    intermediate_bank_swift_code = CharField(max_length=255, blank=True)
    upi_id = CharField(max_length=512, blank=True)
    upi_number = PhoneNumberField(blank=True)
    account_type = ForeignKey(
        to="DynamicEnum",
        on_delete=PROTECT,
        limit_choices_to={"enum": DynamicEnumType.BANK_ACCOUNT_TYPE},
    )
    currency = ForeignKey(
        to="Currency",
        on_delete=PROTECT,
        related_name="currency_abstract_bank_account",
    )
    intermediate_bank_currency = ForeignKey(
        to="Currency",
        on_delete=PROTECT,
        related_name="intermediate_bank_currency_abstract_bank_account",
        blank=True,
        null=True,
    )
    upi_currency = ForeignKey(
        to="Currency",
        on_delete=PROTECT,
        related_name="upi_currency_abstract_bank_account",
        blank=True,
        null=True,
    )

    class Meta:
        abstract = True

    @property
    def account_type_display(self):
        return self.account_type.name

    def __str__(self):
        return f"{self.account_number} / {self.bank_name}"

        # def clean(self):
        #     try:
        #         response = requests.get(
        #             f"https://ifsc.razorpay.com/{self.ifsc_code}", timeout=10
        #         )
        #     except requests.RequestException as exc:
        #         logger.exception(exc)
        #         raise ValidationError({"ifsc_code": "IFSC Service error"})

        #     if not response.ok:
        #         raise ValidationError({"ifsc_code": response.text})

        #     response = response.json()
        #     if not self.branch:
        #         self.branch = (
        #             response["BRANCH"].title() if response["BRANCH"] else "NA"
        #         )
        #     self.bank_name = response["BANK"].title() if response["BANK"] else "NA"
        #     self.swift_code = (
        #         response["SWIFT"].title() if response["SWIFT"] else "NA"
        #     )
        #     self.micr = response["MICR"] if response["MICR"] else "NA"
        return self


class AbstractAddress(Model):
    address_line = TextField()
    latitude = FloatField(blank=True)
    longitude = FloatField(blank=True)
    postal_code = IntegerField(blank=True, null=True)
    city = CharField(max_length=255, blank=True)
    state = CharField(max_length=255, blank=True)
    country = CharField(
        max_length=2, choices=list(CountryField().choices), default="IN"
    )
    #places_api_json = JSONField(default=dict, blank=True, null=True)
#places_api_json = JSONField(blank=True, null=False)  # likely this setup


    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.address_line} / {self.postal_code}"
    
    @property
    def country_display(self):
        return self.get_country_display()
    # @property
    # def state_short_name(self):
    #     address = self.places_api_json.get("address_component", []) or []
    #     for entry in address:
    #         types = entry.get("types", [])
    #         if "administrative_area_level_1" in types:
    #             return entry.get("short_name", "")
    #     return ""
    # @property
    def is_india_union_territory(self):
        union_territories = ["AN", "CH", "DH", "DL", "JK", "LA", "LD", "PY"]
        return self.state_short_name in union_territories and self.country == "IN"

    # @property
    # def country_display(self):
    #     return self.get_country_display()

    # @property
    # def state_short_name(self):
    #     address = self.places_api_json.get("address_component", [])
    #     for entry in address:
    #         types = entry.get("types", [])
    #         if "administrative_area_level_1" not in types:
    #             continue
    #         return entry.get("short_name", "")
    #     return ""

    # @property
    # def is_india_union_territory(self):
    #     union_territories = ["AN", "CH", "DH", "DL", "JK", "LA", "LD", "PY"]
    #     return (
    #         True
    #         if self.state_short_name in union_territories
    #         and self.country == "IN"
    #         else False
    #     )


class AbstractBlankAddress(Model):
    address_line = TextField(blank=True)
    latitude = FloatField(blank=True, null=True)
    longitude = FloatField(blank=True, null=True)
    postal_code = IntegerField(blank=True, null=True)
    city = CharField(max_length=255, blank=True)
    state = CharField(max_length=255, blank=True)
    country = CharField(
        max_length=2, choices=list(CountryField().choices), blank=True
    )
    places_api_json = JSONField(default=dict, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.address_line} / {self.postal_code}"

    @property
    def country_display(self):
        return self.get_country_display()

    @property
    def state_short_name(self):
        address = self.places_api_json.get("address_component", [])
        for entry in address:
            types = entry.get("types", [])
            if "administrative_area_level_1" not in types:
                continue
            return entry.get("short_name", "")
        return ""

    @property
    def is_india_union_territory(self):
        union_territories = ["AN", "CH", "DH", "DL", "JK", "LA", "LD", "PY"]
        return (
            True
            if self.state_short_name in union_territories
            and self.country == "IN"
            else False
        )


class AbstractGenericEntityField(Model):
    name = CharField(max_length=255)
    short_name = UpperCharField(max_length=16)
    phone_number = PhoneNumberField()
    email = EmailField(max_length=255, blank=True)
    secondary_phone_number = PhoneNumberField(blank=True)
    secondary_email = EmailField(max_length=255, blank=True)
    fax = CharField(max_length=255, blank=True)
    website = URLField(blank=True)
    country = CharField(
        max_length=2, choices=list(CountryField().choices), default="IN"
    )
    number_of_dependent = PositiveIntegerField(default=0)
    entity_type = CharField(max_length=16, choices=EntityType.choices)
    registration_number = CharField(max_length=255, blank=True, null=True)
    registration_number_effective_date = DateField(
        validators=[past_date_check], blank=True, null=True
    )
    tax_number = CharField(
        max_length=32, help_text="PAN for Indian Entities", blank=True
    )
    tax_number_effective_date = DateField(
        validators=[past_date_check], blank=True, null=True
    )
    tax_number_front_image = ThumbnailerImageField(blank=True, null=True)
    tax_number_back_image = ThumbnailerImageField(blank=True, null=True)
    aadhar_number = CharField(
        max_length=255, help_text="Addhar Number for Individual", blank=True
    )
    aadhar_number_effective_date = DateField(
        validators=[past_date_check], blank=True, null=True
    )
    aadhar_number_front_image = ThumbnailerImageField(blank=True, null=True)
    aadhar_number_back_image = ThumbnailerImageField(blank=True, null=True)
    msme = CharField(max_length=255, blank=True)
    msme_effective_date = DateField(
        validators=[past_date_check], blank=True, null=True
    )
    msme_type = CharField(max_length=32, blank=True, choices=MSMEType.choices)
    ie_code = CharField(max_length=255, verbose_name="IE Code", blank=True)
    ie_code_effective_date = DateField(
        validators=[past_date_check],
        verbose_name="IE Code Effective Date",
        blank=True,
        null=True,
    )
    description = TextField(blank=True)

    class Meta:
        abstract = True

    @property
    def country_display(self):
        return self.get_country_display()

    @property
    def entity_type_display(self):
        return self.get_entity_type_display()

    @property
    def msme_type_display(self):
        return self.get_msme_type_display()

    def clean(self, **kwargs):
        errors = {}
        if self.entity_type:
            if self.entity_type not in [EntityType.INDIVIDUAL, EntityType.NGO]:
                errors.update(
                    {
                        field: "This field is required for this entity type."
                        for field in [
                            "tax_number",
                            "tax_number_effective_date",
                        ]
                        if not getattr(self, field)
                    }
                )

            if self.entity_type in [
                EntityType.PRIVATE,
                EntityType.PUBLIC,
                EntityType.LLP,
            ]:
                required_registration_fields = [
                    "registration_number",
                    "registration_number_effective_date",
                ]
                errors.update(
                    {
                        field: "This field is required for this entity type."
                        for field in required_registration_fields
                        if not getattr(self, field)
                    }
                )

        if self.country == "IN":
            if self.msme:
                required_msme_fields = [
                    "msme",
                    "msme_effective_date",
                    "msme_type",
                ]
                errors.update(
                    {
                        field: "This field is required for this entity type."
                        for field in required_msme_fields
                        if not getattr(self, field)
                    }
                )

            if self.tax_number and not pan_check(self.tax_number):
                errors["tax_number"] = "Invalid Pan"

        if errors:
            raise ValidationError(errors)

        return self

    def save(self, **kwargs):
        try:
            super(AbstractGenericEntityField, self).save(**kwargs)
        except IntegrityError as exc:
            logger.exception(exc)
            raise SerializerValidationError(
                {"short_name": ["Data with this short name already exists."]}
            )


class AbstractAdjustmentField(Model):
    quantity_adjustment_type = CharField(
        max_length=16,
        choices=AdjustmentType.choices,
        default=AdjustmentType.PERCENT,
    )
    quantity_adjustment_value = PositiveFloatField(default=0)
    quantity_adjustment_percent = PercentField(default=0)
    rate_adjustment_type = CharField(
        max_length=16,
        choices=AdjustmentType.choices,
        default=AdjustmentType.PERCENT,
    )
    rate_adjustment_value = PositiveFloatField(default=0)
    rate_adjustment_percent = PercentField(default=0)

    @property
    def quantity_adjustment_type_display(self):
        return self.get_quantity_adjustment_type_display()

    @property
    def rate_adjustment_type_display(self):
        return self.get_rate_adjustment_type_display()

    class Meta:
        abstract = True


class ShareHolder(AbstractDocument):
    name = CharField(max_length=255)
    share_certificate_number = CharField(max_length=255)
    number_of_shares = PositiveIntegerField()
    distinctive_number_from = CharField(max_length=255)
    distinctive_number_to = CharField(max_length=255)

    class Meta:
        abstract = True


class ContactPerson(Model):
    name = CharField(max_length=255)
    phone_number = PhoneNumberField(
        blank=True,
        null=True,
    )
    secondary_phone_number = PhoneNumberField(
        blank=True,
        null=True,
    )
    email = EmailField(blank=True)
    fax = CharField(max_length=64, blank=True)
    primary_contact = BooleanField(default=False)
    salutation = ForeignKey(
        to="DynamicEnum",
        on_delete=PROTECT,
        limit_choices_to={"enum": DynamicEnumType.SALUTATION},
        related_name="salutation_contact_person",
        blank=True,
        null=True,
    )
    designation = ForeignKey(
        to="DynamicEnum",
        on_delete=PROTECT,
        limit_choices_to={"enum": DynamicEnumType.DESIGNATION},
        related_name="designation_contact_person",
        blank=True,
        null=True,
    )
    department = ForeignKey(
        to="Department", on_delete=PROTECT, blank=True, null=True
    )

    class Meta:
        abstract = True

    @property
    def salutation_display(self):
        return self.salutation.name

    @property
    def designation_display(self):
        return self.designation.name

    def clean(self) -> None:
        if self.phone_number == self.secondary_phone_number:
            raise ValidationError(
                {
                    "secondary_phone_number": "This cannot be same as Phone number."
                }
            )


class Director(Model):
    name = CharField(max_length=255)
    din = CharField(max_length=255)
    type = CharField(max_length=255)
    appointment_date = DateField()
    resignation_date = DateField(blank=True, null=True)
    reappointment_date = DateField(blank=True, null=True)

    class Meta:
        abstract = True


class Particular(Model):
    name = CharField(max_length=255)
    consultant = CharField(max_length=255)
    start_date = DateField(default=timezone_date)
    end_date = DateField(default=timezone_date)
    details = TextField(blank=True)
    returns = TextField(blank=True)
    other_details = TextField(blank=True)

    class Meta:
        abstract = True

    def clean(self):
        if self.start_date > self.end_date:
            raise ValidationError(
                {"end_date": "The end date cannot be less than start date."}
            )

    def save(self, **kwargs):
        self.full_clean()
        super(Particular, self).save(**kwargs)


class InventoryItem(Model):
    inventory_code = TextField(
        max_length=255,
        blank=True,
    )
    qr_code_image = ThumbnailerImageField(blank=True, null=True)

    class Meta:
        abstract = True
