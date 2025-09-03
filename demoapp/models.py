import uuid
from datetime import timedelta
from django.contrib.auth.models import User

from django.core.validators import (
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
)
from django.utils.timezone import now as timezone_now, localdate as timezone_date

import random
import string
import pandas as pd
from decimal import Decimal
from django.db.models import (
    PROTECT,
    BooleanField,
    CharField,
    DateTimeField,
    FloatField,
    ForeignKey,
    Model,
    OneToOneField,
    PositiveIntegerField,
    UUIDField,
    DateField,
    ImageField,
    JSONField,
    ManyToManyField,
    UniqueConstraint,
    TextField,
    Sum,
    Subquery,
    OuterRef,
    DecimalField,
    F,
    BigIntegerField,
    FileField,
    CASCADE,
)
from typing import Collection, Optional
import pytz
from django.template.loader import render_to_string
from django.conf import settings
from datetime import date
from django.db.models import Q
import functools
import qrcode
from django.template import engines
from django.utils import timezone
from django_countries.fields import CountryField
from easy_thumbnails.fields import ThumbnailerImageField
from phonenumber_field.modelfields import PhoneNumberField
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ValidationError as SerializerValidationError
from .exceptions import NegativeQuantityError
from django.db.models.signals import post_save
from django.dispatch import receiver
import re
from django.contrib.postgres.indexes import GinIndex  # GinIndex

from django.db import models, transaction, connection

from .abstract_models import (
    AbstractAddress,
    AbstractAdjustmentField,
    AbstractBankAccount,
    AbstractBlankAddress,
    AbstractDocument,
    AbstractGenericEntityField,
    ApprovalField,
    ArchiveField,
    ContactPerson,
    CreateUpdate,
    CreateUpdateStatus,
    InventoryItem,
    Particular,
)

from .model_helpers import (
     attach_qr,
    blake2s_digest,
    create_code,
    create_qr_code,
    future_date_check,
    hash_text,
    limit_to_active,
    limit_to_approved,
    limit_to_unarchived,
    past_date_check,
    path_and_rename,
    random_alphanum,
    random_pin,
    timezone_date,
)

from .utils import _prefix_from_name, _next_running
from django.contrib.auth.models import Permission, Group
from django.contrib.postgres.search import SearchVector
from .taxonomies import (
    DynamicEnumType,
    UnitCategory,
    TaxType,
    TradePartnerType,
    GSTTreatment, 
    IndiaGstSegment, 
    serialize, 
    DocumentType, 
    Status , 
    AdjustmentType,
    TermType,
    DispatchMode,
    IncoTerm,
    UserLocale,
    )
from django.db.utils import IntegrityError
from typing import Collection
from django.utils import timezone
from datetime import timedelta

from .custom_fields import (
    GSTField,
    PercentField,
    PositiveFloatField,
    UpperCharField,
)

django_engine = engines["django"]


# If Entity model is in this file:
# from .models import Entity
class ReportingTenant(Model):
    """
    Auto-created from Entity.
    - Name: auto = Entity.name
    - Status: 'Active'
    - Short Code: first 3 of Entity.name + running 3 digits (e.g., ABC001)
    One-to-one with Entity (one reporting-tenant per entity).
    """
 #   entity = OneToOneField('Entity', on_delete=CASCADE, related_name='reporting_tenant')
    name = CharField(max_length=255)
    status = CharField(max_length=20, default='Active')
    short_code = CharField(max_length=6, unique=True)

    def __str__(self):
        return self.name


class Tenant(Model):
    """
    Auto-created alongside ReportingTenant.
    - Name: auto = Entity.name
    - Status: 'Active'
    - Short Code: first 3 of Entity.name + running 3 digits (independent series)
    Many tenants can exist under a ReportingTenant if you ever need to expand.
    """
    reporting_tenant = ForeignKey(ReportingTenant, on_delete= PROTECT, related_name='tenants')
    name = CharField(max_length=255)
    status = CharField(max_length=20, default='Active')
    short_code = CharField(max_length=6, unique=True)

    def __str__(self):
        return self.name

# Creating reporting tenant and tenant with Entinty
# @receiver(post_save, sender='yourapp.Entity')  # ← replace 'yourapp' with your Django app label
# def create_reporting_and_tenant(sender, instance, created, **kwargs):
#     if not created:
#         return
#     prefix = _prefix_from_name(instance.name)

#     # Reporting Tenant
#     rt = ReportingTenant.objects.create(
#         entity=instance,
#         name=instance.name,
#         status='Active',
#         short_code=_next_running(ReportingTenant, prefix),
#     )

#     # Default Tenant under the Reporting Tenant
#     Tenant.objects.create(
#         reporting_tenant=rt,
#         name=instance.name,
#         status='Active',
#         short_code=_next_running(Tenant, prefix),
#     )


# Simplified enums
class UserAccountType:
    USER_ACCOUNT = "user"
    ADMIN_ACCOUNT = "admin"
    choices = [(USER_ACCOUNT, "User"), (ADMIN_ACCOUNT, "Admin")]

# class UserLocale:
#     EN_IN = "en_IN"
#     EN_US = "en_US"
#     choices = [(EN_IN, "English (India)"), (EN_US, "English (US)")]


# Create your models here.

class UserProfile(Model):
    
    uid = UUIDField(default=uuid.uuid4, unique=True)
    tenant = ForeignKey(Tenant, on_delete=PROTECT
        #, limit_choices_to=limit_to_active
    )
    user = OneToOneField(to=User, on_delete=PROTECT)
    country = CharField(max_length=2, choices=list(CountryField().choices), default="IN")
    account_type = CharField(max_length=32, choices=UserAccountType.choices, default=UserAccountType.USER_ACCOUNT)
    
    # require_biometrics_for_login = BooleanField(default=False)
    # limit_login_to_three_devices = BooleanField(default=False)
    phone_number = PhoneNumberField(blank=True)
    whatsapp_number = PhoneNumberField(blank=True)
    profile_picture = ThumbnailerImageField(blank=True, null=True)
    signature = ThumbnailerImageField(blank=True, null=True)

    # gender = ForeignKey(
    #     to="DynamicEnum",
    #     on_delete=PROTECT,
    #     limit_choices_to={"enum": DynamicEnumType.GENDER},
    #     related_name="gender_user_profile",
    #     blank=True,
    #     null=True,
    # )

    gender = CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])

    # department = ForeignKey(
    #     to="Department", on_delete=PROTECT, blank=True, null=True
    # )
    department = CharField(max_length=50, null=True, blank=True)

    # designation = ForeignKey(
    #     to="DynamicEnum",
    #     on_delete=PROTECT,
    #     limit_choices_to={"enum": DynamicEnumType.DESIGNATION},
    #     related_name="designation_user_profile",
    #     blank=True,
    #     null=True,
    # )
    designation = CharField(max_length=50, null=True, blank=True)


    locale = CharField(
        max_length=32, choices=UserLocale.choices, default=UserLocale.EN_IN
    )
    # Email OTP related fields (uncomment if you implement)
    # email_otp = PositiveIntegerField(validators=[MaxValueValidator(999999), MinValueValidator(100000)], default=random_pin)
    # email_otp_sent = DateTimeField(null=True, blank=True)
    # email_verified = BooleanField(default=False)

    def __str__(self):
        return f"{self.user}"

    @property
    def last_login(self):
        return (
            self.user.last_login.strftime("%c")
            if self.user.last_login
            else "-"
        )

    @property
    def account_type_display(self):
        return self.get_account_type_display()

    @property
    def full_name(self):
        return self.user.get_full_name()

    @property
    def country_display(self):
        return self.get_country_display()
    
    @property
    def gender_display(self):
        return self.get_gender_display()
    
    @property
    def designation_display(self):
        return self.designation  # or just return self.designation directly

    # def request_password_reset(self):
    #     now = timezone.now()
    #     delta = now - timedelta(minutes=10)
    #     recent = PasswordResetRequest.objects.filter(
    #         user=self.user, created__range=(delta, now)
    #     )
    #     if recent.exists():
    #         logger.info("Request less than 10 minutes old exists.")
    #         return
    #     PasswordResetRequest.objects.create(user=self.user)

    # def generate_email_otp(self):
    #     self.email_otp = random_pin()
    #     self.email_otp_sent = timezone.now()
    #     self.save()

    #     # Send email with OTP
    #     self.send_otp_email()

    # def send_otp_email(self):
    #     try:
    #         print("mailer name", self.user.email)
    #         recipient_list = self.user.email
    #         context = {"CODE": self.email_otp}
    #         safe_send_email(
    #             "common/email-verify",
    #             context,
    #             "Instructions to verify your SatmaCE email",
    #             (recipient_list,),
    #         )
    #         print("Email sent successfully.")
    #     except Exception as e:
    #         print(f"Failed to send email: {e}")
    #         raise ValidationError("Email sending error")

    # def verify_email_otp(self, otp):
    #     if not self.email_otp_sent:
    #         return False
    #     expiry_time = self.email_otp_sent + timedelta(minutes=10)
    #     if timezone.now() > expiry_time:
    #         return False

    #     if str(self.email_otp) == str(otp):
    #         self.email_verified = True
    #         self.save()
    #         return True
    #     return False





# class Address(CreateUpdateStatus, AbstractAddress, ArchiveField):
class Address(AbstractAddress, ArchiveField):
    tenant = ForeignKey(
        Tenant, on_delete=PROTECT 
        #, limit_choices_to=limit_to_active
    )

    def __str__(self):
        return f"{self.address_line} / {self.postal_code}"


# class Currency(CreateUpdateStatus):
class Currency(Model):  
    country = CharField(
        max_length=2, choices=list(CountryField().choices), unique=True
    )
    name = CharField(max_length=255)
    symbol = CharField(max_length=32)
    is_base = BooleanField(default=False)
    fraction_unit = CharField(max_length=255, blank=True)
    fraction_conversion = FloatField(
        default=100,
        validators=[MinValueValidator(0.0)],
        help_text="Example: Put 100 from INR to Paise conversion",
        blank=True,
    ) 
    iso_code = UpperCharField(max_length=3, validators=[MinLengthValidator(3)])
    conversion_rate = FloatField(validators=[MinValueValidator(0.0)])
   

    def __str__(self):
        return f"{self.name} / {self.country}"

    @property
    def country_display(self):
        return self.get_country_display()



# class Entity(CreateUpdateStatus, ArchiveField, AbstractGenericEntityField):
class Entity(ArchiveField, AbstractGenericEntityField):
   
    registered_address = ForeignKey(
        to="Address",
        on_delete=PROTECT,
        related_name="registered_address_entity",
        blank=True,
        null=True,
    )
    currency = ForeignKey(
        to="Currency", on_delete=PROTECT, related_name="currency_entity"
    )

    logo = ThumbnailerImageField(upload_to='entity_logos/', blank=True, null=True)

    contact_name = CharField(max_length=255, null=True)
    bank_details = JSONField(blank=True, null=True)  # Could store bank info in JSON


    tenant = ForeignKey(
        Tenant, on_delete=PROTECT, blank=True, null=True
        # , limit_choices_to=limit_to_active
    )

    
    
    # reporting_currency = ForeignKey(
    #     to="Currency",
    #     related_name="reporting_currency_entity",
    #     blank=True,
    #     null=True,
    # )
    
    # communication_address = ForeignKey(
    #     to="Address",
    #     on_delete=PROTECT,
    #     related_name="communication_address_entity",
    #     blank=True,
    #     null=True,
    # )
    # tally_company_mapping = CharField(null=True, blank=True)
    # tally_url = CharField(null=True, blank=True)
    # documents = Man
    #     on_delete=PROTECT,yToManyField(to="common.Document", blank=True)
    # zoho_orgranization_id = CharField(max_length=255, blank=True)
    # zoho_client_id = CharField(max_length=255, blank=True)
    # zoho_client_secret_id = CharField(max_length=255, blank=True)
    # zoho_refresh_token = CharField(max_length=255, blank=True)
    # satma_iot_label = TextField(blank=True, default=SATMA_IOT_DEFAULT_LABEL)
    # default_zoho_gst_id = CharField(max_length=255, blank=True)
    # default_zoho_igst_id = CharField(max_length=255, blank=True)
    # enable_sales_bill_zoho = BooleanField(default=False)
    # gst_rates = JSONField(default=dict, blank=True)
    # igst_rates = JSONField(default=dict, blank=True)
    # use_zoho_batch_feature = BooleanField(default=True)

    class Meta:
        unique_together = (("short_name", "tenant"),)

    
    def __str__(self):
        return f"{self.name} / {self.short_name}"

    # @property
    # def is_tally_compatible(self) -> bool:
    #     return self.tally_company_mapping is not None

    # @property
    # def has_zoho(self):
    #     return bool(self.zoho_refresh_token)



class DynamicEnum(CreateUpdateStatus):
    name = CharField(max_length=255)
    code = CharField(max_length=255, blank=True)
    enum = CharField(max_length=128, choices=DynamicEnumType.choices)
    tenants = ManyToManyField(to="Tenant")

    def __str__(self):
        return f"{self.name}"

    @property
    def enum_display(self):
        return self.get_enum_display()

class Document(AbstractDocument):
    tenant = ForeignKey(
        Tenant, on_delete=PROTECT, 
        # limit_choices_to=limit_to_active
    )

    def __str__(self):
        return f"{self.document_name} / {self.tenant}"

class EntityUserAccess(models.Model):
    uid = UUIDField(default=uuid.uuid4)
    entity = ForeignKey(to=Entity, on_delete=PROTECT)
    user = ForeignKey(to=User, on_delete=PROTECT)
   # permissions = ManyToManyField(to=Permission, blank=True)
  #  groups = ManyToManyField(to=Group, blank=True)

    def __str__(self):
        return f"{self.user} / {self.entity}"

    class Meta:
        unique_together = (
            (
                "user",
                "entity",
            ),
        )

    def validate_unique(self, exclude: Collection[str] | None = ...) -> None:
        if self.pk is None:
            qs = EntityUserAccess.objects.filter(
                user=self.user,
                entity=self.entity,
            )
            if qs.exists():
                raise ValidationError(
                    {
                        "entity": "An entry for this User and Entity already exists"
                    }
                )
        return super().validate_unique(exclude)

    def save(self, **kwargs):
        self.validate_unique(None)
        super(EntityUserAccess, self).save(**kwargs)

# def default_expiry_date():
#     return (timezone.now() + timedelta(days=365*100)).date()

class Center(CreateUpdateStatus, ArchiveField, AbstractAddress):
    # --- Old Meta (commented out) ---
    # class Meta:
    #     unique_together = (
    #         "name",
    #         "tenant",
    #     )
    #     indexes = [
    #         GinIndex(
    #             SearchVector("name", config="english"), name="center_name_gin"
    #         ),
    #     ]

    class Meta:
        unique_together = (("short_name", "tenant"),)
        indexes = [
            GinIndex(
                SearchVector("name", config="english"), name="center_name_gin"
            ),
        ]

    tenant = ForeignKey(
        Tenant, on_delete=PROTECT,
         # limit_choices_to=limit_to_active
    )
    name = CharField(max_length=255)
    short_name = UpperCharField(max_length=16)
    code = UpperCharField(max_length=32, blank=True)
    #start_date = DateField(default=timezone.now)
    start_date = models.DateField(default=timezone.localdate)
    # end_date = DateField(default=timezone.now)
    end_date = models.DateField(default=timezone.localdate)
    gst_effective_date = DateField(
        validators=[past_date_check], blank=True, null=True
    )
    gstin = GSTField(verbose_name="GSTIN", blank=True)

    # --- Old factory license fields (commented out) ---
    # factory_license_number = CharField(max_length=255, blank=True)
    # factory_license_date = DateField(
    #     validators=[past_date_check], blank=True, null=True
    # )
    # factory_license_expiry_date = DateField(blank=True, null=True)

    # --- Updated with defaults ---
    factory_license_number = CharField(max_length=255, blank=True, default="9999999999")
    # factory_license_date = DateField(
    #     validators=[past_date_check],
    #     default=timezone.now,
    # )
    # factory_license_expiry_date = DateField(
    #     default=lambda: timezone.now().date() + timedelta(days=365*100)
    # )
    factory_license_expiry_date = models.DateField( null=True, blank= True)
    entity = ForeignKey(to="Entity", on_delete=PROTECT)
    gst_certificates = ManyToManyField(to="Document", blank=True)
#    processes = ManyToManyField(to="common.Process", blank=True)
    factory_license_issuing_agency = ForeignKey(
        to="DynamicEnum",
        on_delete=PROTECT,
        limit_choices_to={
            "enum": DynamicEnumType.FACTORY_LICENCE_ISSUING_AGENCY
        },
        blank=True,
        null=True,
    )
    licence_issuer= CharField(max_length=60, default="State Registration")
    # tally_mapping_name = CharField(max_length=255, blank=True, default="")
    # external_ids = JSONField(blank=True, default=dict)
    # error_message = JSONField(blank=True, default=dict)

    def allow_create(self, user):
        entity_obj = EntityUserAccess.objects.filter(
            user=user,
            entity=self.entity,
            permissions__codename="create_center",
        ).first()
        return True if entity_obj else False

    @property
    def yet_to_apply_for_gstin(self):
        return not self.gstin

    @property
    def factory_license_issuing_agency_display(self):
        return (
            self.factory_license_issuing_agency.name
            if self.factory_license_issuing_agency
            else "State Registration"  # ✅ default
        )

    def __str__(self):
        return self.name

    def clean(self):
        validation_dict = {}
        if (
            self.start_date
            and self.end_date
            and self.start_date > self.end_date
        ):
            validation_dict[
                "end_date"
            ] = "The end date cannot be less than start date."
        if (
            self.factory_license_date
            and self.factory_license_expiry_date
            and self.factory_license_date > self.factory_license_expiry_date
        ):
            validation_dict[
                "factory_license_expiry_date"
            ] = "The expiry date cannot be less than license date."
        if self.gstin and not self.gst_effective_date:
            validation_dict["gst_effective_date"] = "This field is required."
        if self.gst_effective_date and not self.gstin:
            validation_dict["gstin"] = "This field is required."

        if validation_dict:
            raise ValidationError(validation_dict)

    def save(self, **kwargs):
        try:
            if self.pk is None:
                self.tally_mapping_name = self.name

                #  Auto-generate short_name if missing
                if not self.short_name:
                    prefix = _prefix_from_name(self.entity.name)
                    self.short_name = _next_running(Center, prefix, field="short_name")

                # Default issuer if missing
                if not self.factory_license_issuing_agency:
                    self.factory_license_issuing_agency = DynamicEnum.objects.filter(
                        enum=DynamicEnumType.FACTORY_LICENCE_ISSUING_AGENCY,
                        name="State Registration",
                    ).first()

            if not self.code:
                self.code = create_code("CNT", self.start_date)

            super(Center, self).save(**kwargs)
        except IntegrityError:
            raise SerializerValidationError(
                {
                    "short_name": [
                        ("Center with this short name already exists.")
                    ]
                }
            )



class Warehouse(CreateUpdateStatus, ArchiveField):
    tenant = ForeignKey(
        Tenant, on_delete=PROTECT
        #, limit_choices_to=limit_to_active
    )
    center = models.ForeignKey("Center", on_delete=models.PROTECT, null=True, blank=True)

    name = CharField(max_length=255, blank=True)
    short_name = UpperCharField(max_length=16, blank=True)
  #  prefix = CharField(max_length=8, blank=True)
   # center = ForeignKey(to="Center", on_delete=PROTECT)
   # tally_mapping_name = CharField(max_length=255, blank=True, default="")
   # external_ids = JSONField(blank=True, default=dict)
   # error_message = JSONField(blank=True, default=dict)

    # def allow_create(self, user):
    #     entity_obj = EntityUserAccess.objects.filter(
    #         user=user,
    #         entity=self.center.entity,
    #         permissions__codename="create_warehouse",
    #     ).first()
    #     return True if entity_obj else False

    class Meta:
        unique_together = (("name", "tenant"),)
        indexes = [
            GinIndex(
                SearchVector("name", config="english"),
                name="warehouse_name_gin",
            ),
        ]

    def __str__(self):
        return self.name

    # def save(self, **kwargs):
    #     try:
    #         if self.pk is None:
    #             self.tally_mapping_name = self.name
    #         super(Warehouse, self).save(**kwargs)
    #     except IntegrityError:
    #         raise SerializerValidationError(
    #             {
    #                 "short_name": "Warehouse with this short name already exists."
    #             }
    #         )
    def save(self, **kwargs):
        try:
            if self.pk is None:
                # --- Auto-set warehouse name from Center ---
                if not self.name:
                    self.name = self.center.name

                # --- Auto-generate short_name from Center name ---
                if not self.short_name:
                    prefix = _prefix_from_name(self.center.name)
                    self.short_name = _next_running(Warehouse, prefix, field="short_name")

                self.tally_mapping_name = self.name

            super(Warehouse, self).save(**kwargs)
        except IntegrityError:
            raise SerializerValidationError(
                {"short_name": "Warehouse with this short name already exists."}
            )   


class UnitOfMeasurement(CreateUpdateStatus):
    name = CharField(max_length=255)
    unique_quantity_code = UpperCharField(max_length=3, unique=True)
    conversion_rate = FloatField(
        validators=[MinValueValidator(0.0)],
        help_text="Conversion Rate to primary unit",
    )
    is_primary_unit = BooleanField(default=False)
    category = CharField(choices=UnitCategory.choices, max_length=32)
    tally_mapping_name = CharField(max_length=255, blank=True, default="")

    @property
    def category_display(self):
        return self.get_category_display()

    def __str__(self):
        return f"{self.name} / {self.unique_quantity_code}"

    class Meta:
        constraints = [
            UniqueConstraint(
                "category",
                condition=Q(is_primary_unit=True),
                name="ensure_one_primary_true_for_category",
            ),
        ]

    def clean(self):
        if self.conversion_rate == 0:
            raise ValidationError(
                {"conversion_rate": "Conversion rate cannot be zero."}
            )
        if self.is_primary_unit and self.conversion_rate != 1:
            raise ValidationError(
                {
                    "conversion_rate": "Conversion rate should be 1 for primary units."
                }
            )

    def save(self, **kwargs):
        if self.pk is None:
            self.tally_mapping_name = self.unique_quantity_code
        super(UnitOfMeasurement, self).save(**kwargs)


class Tax(CreateUpdateStatus):
    name = CharField(max_length=255)
    rate = PercentField()
    country = CharField(
        max_length=2, choices=list(CountryField().choices), default="IN"
    )
    type = CharField(max_length=8, choices=TaxType.choices)
    external_ids = JSONField(blank=True, default=dict)
    tally_mapping_name = CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return f"{self.name} / {self.rate}"

    @property
    def country_display(self):
        return self.get_country_display()

    @property
    def type_display(self):
        return self.get_type_display()

    def save(self, **kwargs):
        if self.pk is None:
            self.tally_mapping_name = self.name
        super(Tax, self).save(**kwargs)


class TaxGroup(CreateUpdateStatus):
    name = CharField(max_length=255)
    taxes = ManyToManyField(to="Tax")
    external_ids = JSONField(blank=True, default=dict)
    tally_mapping_name = CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return self.name

    @property
    def tax_total(self):
        return sum((tax.rate) for tax in self.taxes.all())

    def save(self, **kwargs):
        if self.pk is None:
            self.tally_mapping_name = self.name
        super(TaxGroup, self).save(**kwargs)



class Item(CreateUpdateStatus, ArchiveField):
     # Required Fields
    name = CharField(max_length=255)
    type = ForeignKey(
        to="DynamicEnum",
        on_delete=PROTECT,
        limit_choices_to={"enum": DynamicEnumType.MATERIAL_TYPE},
        related_name="type_item",
    )# Item Type
    image = ThumbnailerImageField(blank=True, null=True)
    hsn_or_sac_code = CharField(max_length=8)
    is_rcm_applicable = BooleanField(default=False)
    is_epr_applicable = BooleanField(default=False)
    unit = ForeignKey(
        to="UnitOfMeasurement", on_delete=PROTECT, related_name="unit_item"
    )  # UOM

    inter_state_gst = ForeignKey(
        to="TaxGroup", on_delete=PROTECT, related_name="inter_state_gst_item"
    )
    intra_state_gst = ForeignKey(
        to="TaxGroup", on_delete=PROTECT, related_name="intra_state_gst_item"
    )
    intra_ut_gst = ForeignKey(
        to="TaxGroup",
        on_delete=PROTECT,
        related_name="intra_ut_gst_item",
        blank=True,
        null=True,
    )
    tenant = ForeignKey(
        Tenant, on_delete=PROTECT
        # , limit_choices_to=limit_to_active
    )
    
    code = UpperCharField(max_length=32, unique=True, blank=True, null=True)
    # description = TextField(blank=True)
    # is_system_item = BooleanField(blank=True, default=False)
    # invoice_sales_item_description = TextField(blank=True)
    # consumable = BooleanField(default=False)
    # purchasable = BooleanField(default=False)
    # segregatable = BooleanField(default=False)
    # qc_required = BooleanField(default=False)
    # is_recycled = BooleanField(default=False)
    # cc_item = ForeignKey(
    #     to="CarbonCreditItem", on_delete=PROTECT, null=True, blank=True
    # )
    # ecommerce = BooleanField(default=False)
    # saleable = BooleanField(default=False)
    # packing_required = BooleanField(default=False)
    
    # tcs_percent = PercentField()
    # unit_conversion_rate = FloatField(blank=True, null=True)
    # sale_price = FloatField(default=0)
    # sale_price_variance_percent = PercentField()
    # prev_buy_price = FloatField(blank=True, null=True)
    # buy_price = FloatField(default=0)
    # buy_price_variance_percent = PercentField()
    # min_order_quantity = FloatField(blank=True, null=True)
    # max_order_quantity = FloatField(blank=True, null=True)
    # reorder_quantity = FloatField(blank=True, null=True)
    # lead_time_in_days = PositiveIntegerField(blank=True, null=True)
    # quantity_variance_percent = PercentField(blank=True, null=True)
    # party_reference_item_code = CharField(max_length=32, blank=True)
    # is_recommended = BooleanField(default=False)
    # quality_checked_date = DateField(blank=True, null=True)
    # quality_rating = PositiveIntegerField(
    #     default=0, validators=[MinValueValidator(0), MaxValueValidator(5)]
    # )
    # quality_remarks = TextField(blank=True)
    
    # level = ForeignKey(
    #     to="DynamicEnum",
    #     on_delete=PROTECT,
    #     limit_choices_to={"enum": DynamicEnumType.ITEM_LEVEL},
    #     related_name="level_item",
    #     blank=True,
    #     null=True,
    # )
    # storage_type = ForeignKey(
    #     to="DynamicEnum",
    #     on_delete=PROTECT,
    #     limit_choices_to={"enum": DynamicEnumType.ITEM_STORAGE_TYPE},
    #     related_name="storage_type_item",
    #     blank=True,
    #     null=True,
    # )
    # next_process = ForeignKey(
    #     to="DynamicEnum",
    #     on_delete=PROTECT,
    #     limit_choices_to={"enum": DynamicEnumType.ITEM_NEXT_PROCESS},
    #     related_name="next_process_item",
    #     blank=True,
    #     null=True,
    # )
    
    
    # coa_sales = ForeignKey(
    #     to="ChartOfAccount",
    #     on_delete=PROTECT,
    #     related_name="coa_sales_item",
    #     blank=True,
    #     null=True,
    # )
    # coa_purchase = ForeignKey(
    #     to="ChartOfAccount",
    #     on_delete=PROTECT,
    #     related_name="coa_purchase_item",
    #     blank=True,
    #     null=True,
    # )
    # coa_inventory = ForeignKey(
    #     to="ChartOfAccount",
    #     on_delete=PROTECT,
    #     related_name="coa_inventory_item",
    #     blank=True,
    #     null=True,
    # )
    
    # unit_category = CharField(choices=UnitCategory.choices, max_length=32)
    # alternate_unit = ForeignKey(
    #     to="UnitOfMeasurement",
    #     on_delete=PROTECT,
    #     related_name="alternate_unit_item",
    #     blank=True,
    #     null=True,
    # )

    # category = ForeignKey(
    #     to="DynamicEnum",
    #     on_delete=PROTECT,
    #     limit_choices_to={"enum": DynamicEnumType.ITEM_CATEGORY},
    #     related_name="category_item",
    #     blank=True,
    #     null=True,
    # )
    # item_sub_category = ForeignKey(
    #     to="ItemSubCategory", on_delete=PROTECT, blank=True, null=True
    # )
    # quality_check_type = ForeignKey(
    #     to="DynamicEnum",
    #     on_delete=PROTECT,
    #     limit_choices_to={"enum": DynamicEnumType.QC_TYPE},
    #     related_name="quality_check_type_item",
    #     blank=True,
    #     null=True,
    # )
    # quality_checked_by = ForeignKey(
    #     to=User, on_delete=PROTECT, blank=True, null=True
    # )
    # quality_checked_report_documents = ManyToManyField(
    #     to="common.Document", blank=True
    # )
    
    
    # hsn_code = ForeignKey(
    #     to="HarmonizedSystemName", on_delete=PROTECT, null=True
    # )

    # epr_type = ForeignKey(
    #     to="DynamicEnum",
    #     on_delete=PROTECT,
    #     limit_choices_to={"enum": DynamicEnumType.EPR_TYPE},
    #     related_name="epr_type_item",
    #     blank=True,
    #     null=True,
    # )
    # selection_count = PositiveIntegerField(default=0)
    # external_ids = JSONField(blank=True, default=dict)
    # tally_mapping_name = CharField(max_length=255, blank=True, default="")
    # error_message = CharField(max_length=255, blank=True, default="")
    # zoho_entity_error_message = JSONField(blank=True, default=dict)
    # search_vector = SearchVectorField(blank=True, null=True)

    class Meta:
        unique_together = (
            "name",
            "tenant",
        )
        indexes = [
            GinIndex(
                SearchVector("name", config="english"),
                name="search_vector_item_name",
            )
        ]

    def __str__(self):
        return self.name

    def save(self, **kwargs):
        if not self.code:
            self.code = create_code("ITM")
        # if not self.description:
        #     self.description = self.name
        # if not self.alternate_unit:
        #     self.unit_conversion_rate = 0
        self.validate_unique(None)
        super(Item, self).save(**kwargs)

    # @property
    # def segregated_quantity(self):
    #     return SegregationOut.objects.filter(item=self).aggregate(
    #         total_quantity=Sum("quantity", default=0)
    #     ).get("total_quantity", 0) - Bale.objects.filter(
    #         bale_set__item=self
    #     ).aggregate(
    #         total_quantity=Sum("quantity", default=0)
    #     ).get(
    #         "total_quantity", 0
    #     )

    @property
    def type_display(self):
        return self.type.name

    @property
    def unit_category_display(self):
        return self.get_unit_category_display()

    @property
    def level_display(self):
        return self.level.name

    @property
    def storage_type_display(self):
        return self.storage_type.name

    @property
    def next_process_display(self):
        return self.next_process.name

    @property
    def quality_check_type_display(self):
        return self.quality_check_type.name

    def validate_unique(self, exclude: Collection[str] | None = ...) -> None:
        if self.pk is None:
            qs = Item.objects.filter(
                name=self.name,
                tenant=self.tenant,
            )
            if qs.exists():
                raise ValidationError(
                    {"name": "An Item with the same name already exists"}
                )
        return super().validate_unique(exclude)

    def clean(self):
        if self.consumable and (
            self.purchasable
            or self.ecommerce
            or self.saleable
            or self.qc_required
        ):
            raise ValidationError(
                {
                    "consumable": "'Consumable' field cannot be true if any"
                    " of the 'Purchasable' or 'E-commerce' or "
                    "'Salable' or 'QC Required' is true"
                }
            )
        if (
            self.min_order_quantity
            and self.max_order_quantity
            and self.min_order_quantity > self.max_order_quantity
        ):
            raise ValidationError(
                {
                    "min_order_quantity": "Minimum Quantity cannot be less "
                    "than Maximum Quantity."
                }
            )



class TradePartnerCategory(CreateUpdateStatus):
    type = CharField(max_length=32, choices=TradePartnerType.choices)
    category = CharField(max_length=255)

    def __str__(self):
        return f"{self.type} / {self.category}"

    @property
    def type_display(self):
        return self.get_type_display()



class TradePartnerEntity(CreateUpdateStatus):
    trade_partner = ForeignKey("TradePartner", on_delete=PROTECT)
    entity = ForeignKey(Entity, on_delete=PROTECT)
    # customer_zoho_id = models.CharField(blank=True, null=True, max_length=255)
    # vendor_zoho_id = models.CharField(blank=True, null=True, max_length=255)
    # customer_address_zoho_id = models.CharField(
    #     blank=True, null=True, max_length=255
    # )
    # vendor_address_zoho_id = models.CharField(
    #     blank=True, null=True, max_length=255
    # )

    class Meta:
        unique_together = (("trade_partner", "entity"),)

    def __str__(self):
        return f"{self.trade_partner} / {self.entity}"


class TradePartner( CreateUpdateStatus, ArchiveField, AbstractGenericEntityField):
    system_code = CharField(
        max_length=16,
        unique=True,
        default=functools.partial(random_alphanum, 16, mix_case=True),
    )
    # is_related_party = BooleanField(default=False)
    # is_registered = BooleanField(default=False)
    is_customer = BooleanField(default=False)
    is_vendor = BooleanField(default=True)
    display_picture = ThumbnailerImageField(blank=True, null=True)
 
    tenant = ForeignKey(
        Tenant, on_delete=PROTECT
        #, limit_choices_to=limit_to_active
    )
    # pan_number = CharField(max_length=20, blank=True)   
    # pan_date = DateField(blank=True, null=True)         

    # date_of_incorpotion = DateField(
    #     help_text="Put date of birth if an Individual.", blank=True, null=True
    # )
    # referred_by = CharField(max_length=255, blank=True)
    # referred_by_contact = CharField(max_length=255, blank=True)
    # comment = TextField(blank=True)
    # school = CharField(max_length=512, blank=True)
    # field_of_study = CharField(max_length=512, blank=True)
    # grade = CharField(max_length=512, blank=True)
    # question_1 = TextField(
    #     help_text="How does our commitment to responsible sourcing align with your values?",
    #     blank=True,
    # )
    # question_2 = TextField(
    #     help_text="What specific aspects of our sourcing approach do you appreciate the most?",
    #     blank=True,
    # )
    # question_3 = TextField(
    #     help_text="What are the areas where you think we could enhance our responsible sourcing efforts?",
    #     blank=True,
    # )
    # question_4 = TextField(
    #     help_text="Share any suggestions or ideas to further improve our sustainability practices.",
    #     blank=True,
    # )
    # category = ForeignKey(
    #     to="TradePartnerCategory", on_delete=PROTECT, blank=True, null=True
    # )
    # vendor_group = ForeignKey(
    #     to="DynamicEnum",
    #     on_delete=PROTECT,
    #     limit_choices_to={"enum": DynamicEnumType.VENDOR_GROUP},
    #     related_name="vendor_group_trade_partner",
    #     blank=True,
    #     null=True,
    # )
    # gender = ForeignKey(
    #     to="DynamicEnum",
    #     on_delete=PROTECT,
    #     limit_choices_to={"enum": DynamicEnumType.GENDER},
    #     related_name="gender_trade_partner",
    #     blank=True,
    #     null=True,
    # )
    # degree = ForeignKey(
    #     to="DynamicEnum",
    #     on_delete=PROTECT,
    #     limit_choices_to={"enum": DynamicEnumType.DEGREE},
    #     related_name="degree_trade_partner",
    #     blank=True,
    #     null=True,
    # )
    # kyc = OneToOneField(to="KYC", on_delete=PROTECT, blank=True, null=True)
    # documents = ManyToManyField(
    #     to="common.Document",
    #     related_name="documents_trade_partner",
    #     blank=True,
    # )
    transaction_currency = ForeignKey(to="Currency", on_delete=PROTECT)
    entity = ForeignKey(
        Entity,
        on_delete=PROTECT,
        #limit_choices_to=limit_to_active,
        blank=True,
        null=True,
    )
    # external_ids = JSONField(blank=True, default=dict)
    # tally_mapping_name = CharField(max_length=255, blank=True, default="")
    linked_entities = ManyToManyField(
        Entity,
        through="TradePartnerEntity",
        blank=True,
        related_name="linked_trade_partners",
    )
    # zoho_customer_error_message = JSONField(blank=True, default=dict)
    # zoho_vendor_error_message = JSONField(blank=True, default=dict)

    class Meta:
        unique_together = (("short_name", "tenant"),)
        indexes = [
            GinIndex(
                SearchVector("name", config="english"),
                name="trade_partner_name_gin",
            ),
        ]
        constraints = []   # remove extra unique constraint if any

    # def allow_create(self, user):
    #     entity_obj = EntityUserAccess.objects.filter(
    #         user=user,
    #         entity=self.entity,
    #         permissions__codename="create_tradepartner",
    #     ).first()
    #     return True if entity_obj else False

    # @property
    # def address_gstin(self):
    #     for address in self.tradepartneraddress_set.all():
    #         if address.gstin:
    #             return address.gstin
    #     return "-"

    # @property
    # def vendor_group_display(self):
    #     return self.vendor_group.name

    # @property
    # def gender_display(self):
    #     return self.gender.name

    # @property
    # def degree_display(self):
    #     return self.degree.name

    def __str__(self):
        return self.name

    # def save(self, **kwargs):
    #     if self.pk is None:
    #         self.tally_mapping_name = self.name
    #     super(TradePartner, self).save(**kwargs)

    # def save(self, *args, **kwargs):
    #     # Auto-generate short_name if not provided
    #     if not self.short_name:
    #         self.short_name = f"TP-{uuid.uuid4().hex[:6].upper()}"

    #     # Auto-fill tally_mapping_name (if you keep that field)
    #     if not getattr(self, "tally_mapping_name", None):
    #         self.tally_mapping_name = self.name

    #     super().save(*args, **kwargs)
    
    # def save(self, *args, **kwargs):
    #     if not self.short_name:
    #         # get first 4 letters of name (uppercase)
    #         name_part = (self.name[:4].upper() if self.name else "TP")
            
    #         # generate 4-digit random number
    #         random_part = "".join(random.choices(string.digits, k=4))
            
    #         # combine
    #         self.short_name = f"{name_part}{random_part}"
            
    #         # ensure uniqueness
    #         while TradePartner.objects.filter(short_name=self.short_name, tenant=self.tenant).exists():
    #             random_part = "".join(random.choices(string.digits, k=4))
    #             self.short_name = f"{name_part}{random_part}"

    #     super().save(*args, **kwargs)
    
    def save(self, *args, **kwargs):
        if not self.short_name:
            name_part = (self.name[:4].upper() if self.name else "TP")
            
            # generate until unique
            while True:
                random_part = "".join(random.choices(string.digits, k=4))
                short_name_candidate = f"{name_part}{random_part}"
                if not TradePartner.objects.filter(
                    short_name=short_name_candidate, tenant=self.tenant
                ).exists():
                    self.short_name = short_name_candidate
                    break

        super().save(*args, **kwargs)

class TradePartnerAddress(CreateUpdateStatus, AbstractAddress):
#    qr_code_image = ThumbnailerImageField(blank=True, null=True)
    gst_effective_date = DateField(
        validators=[past_date_check], blank=True, null=True
    )
    gstin = GSTField(verbose_name="GSTIN", blank=True)
    # gst_certificates = ManyToManyField(
    #     to="common.Document",
    #     blank=True,
    # )
    trade_partner = ForeignKey(to="TradePartner", on_delete=PROTECT)
    # qr_code = OneToOneField(
    #     QRCode,
    #     on_delete=PROTECT,
    #     limit_choices_to=dict(inventory_type=QRCodeType.TPA),
    # )
    external_ids = JSONField(blank=True, default=dict)
    gst_treatment = CharField(
        max_length=32, blank=True, choices=GSTTreatment.choices
    )
    is_billing = BooleanField(default=False)
    is_shipping = BooleanField(default=False)
    # is_notify_copy = BooleanField(default=False)
    # is_consignee = BooleanField(default=False)

    def __str__(self):
        return f"{self.address_line} / {self.trade_partner}"

    # @property
    # def type_display(self):
    #     return self.get_type_display()

    # @property
    # def yet_to_apply_for_gstin(self):
    #     return not self.gstin

    # def allow_create(self, user):
    #     entity_obj = EntityUserAccess.objects.filter(
    #         user=user,
    #         entity=self.trade_partner.entity,
    #         permissions__codename="create_tradepartneraddress",
    #     ).first()
    #     return True if entity_obj else False

    def save(self, **kwargs):
        validation_dict = {}
        if self.gstin and not self.gst_effective_date:
            validation_dict["gst_effective_date"] = "This field is required."
        if self.gst_effective_date and not self.gstin:
            validation_dict["gstin"] = "This field is required."

        if validation_dict:
            raise SerializerValidationError(validation_dict)

        # if not self.qr_code_id:
        #     qr_code = QRCode(
        #         inventory_type=QRCodeType.TPA,
        #         tenant=self.trade_partner.tenant,
        #     )
        #     qr_code.save()
        #     self.qr_code = qr_code
        super(TradePartnerAddress, self).save(**kwargs)
    
class TradePartnerBankAccount(CreateUpdateStatus, AbstractBankAccount):
    trade_partner = ForeignKey(
        TradePartner, on_delete=PROTECT, limit_choices_to=limit_to_active
    )
    currency = ForeignKey(
        to="Currency",
        on_delete=PROTECT,
        related_name="currency_trade_partner_bank_account",
    )
    # intermediate_bank_currency = ForeignKey(
    #     to="Currency",
    #     on_delete=PROTECT,
    #     related_name="intermediate_bank_currency_trade_partner_bank_account",
    #     blank=True,
    #     null=True,
    # )
    # upi_currency = ForeignKey(
    #     to="Currency",
    #     on_delete=PROTECT,
    #     related_name="upi_currency_trade_partner_bank_account",
    #     blank=True,
    #     null=True,
    # )

    # def allow_create(self, user):
    #     entity_obj = EntityUserAccess.objects.filter(
    #         user=user,
    #         entity=self.trade_partner.entity,
    #         permissions__codename="create_tradepartnerbankaccount",
    #     ).first()
    #     return True if entity_obj else False

    # @property
    # def account_type_display(self):
    #     return self.account_type.name

    def clean(self):
        if self.currency and getattr(self.currency, "country", None) == "IN":
            if not self.account_number or len(str(self.account_number)) != 16:
                raise ValidationError(
                    {
                        "account_number": "Account number must be exactly 16 digits for Indian currency."
                    }
                )

    def save(self, **kwargs):
        super(TradePartnerBankAccount, self).save(**kwargs)




# SerialMaster = A list of individual product units with unique serial numbers.
class SerialMaster(CreateUpdate):
    entity = ForeignKey(to="Entity", on_delete=PROTECT)
    prefix = CharField(max_length=32, blank=True, default="")
    document_type = CharField(max_length=32, choices=DocumentType.choices)

    def __str__(self):
        return f"{self.entity} / {self.prefix} / {self.document_type}"

    def generate_prefix(self, date_: date):
        return date_.strftime(self.prefix).upper()

    @property
    def document_type_display(self):
        return self.get_document_type_display()


# Counter → generates sequential numbers for documents/transactions.
class Counter(CreateUpdate):
    tenant = ForeignKey(to=Tenant, on_delete=PROTECT)
    document_type = CharField(max_length=32, choices=DocumentType.choices)
    counter = BigIntegerField(default=0)

    # def generate_suffix(self):
    #     tenant_id = self.tenant.id
    #     with transaction.atomic():
    #         # Get the current value of the counter for this tenant
    #         cursor = connection.cursor()
    #         cursor.execute(
    #             """
    #             UPDATE common_counter
    #             SET counter = counter + 1
    #             WHERE tenant_id = %s
    #             AND document_type = %s
    #             RETURNING counter
    #         """,
    #             [tenant_id, self.document_type],
    #         )
    #         serial_number = cursor.fetchone()[0]
    #         return serial_number
    def generate_suffix(self):
        tenant_id = self.tenant.id
        table = self._meta.db_table  # dynamically gets the real table name
        with transaction.atomic():
            cursor = connection.cursor()
            cursor.execute(
                f"""
                UPDATE {table}
                SET counter = counter + 1
                WHERE tenant_id = %s
                AND document_type = %s
                RETURNING counter
                """,
                [tenant_id, self.document_type],
            )
            serial_number = cursor.fetchone()[0]
            return serial_number

class Packaging(CreateUpdateStatus, ArchiveField):
    name = CharField(max_length=128, blank=True)
    tenant = ForeignKey(
        Tenant, on_delete=PROTECT, limit_choices_to=limit_to_active
    )
    unit = ForeignKey(UnitOfMeasurement, on_delete=PROTECT)
    capacity = PositiveFloatField()

    def __str__(self):
        return f"{self.tenant} / {self.name} / {self.unit}"

class InventoryQueueRecord(CreateUpdate):
    item = ForeignKey(to=Item, on_delete=CASCADE)
    warehouse = ForeignKey(to=Warehouse, on_delete=CASCADE)
    packaging = ForeignKey(
        to=Packaging, on_delete=CASCADE, blank=True, null=True
    )
    unit_category = CharField(choices=UnitCategory.choices, max_length=32)
    quality_checked = BooleanField(default=False)
#    qr_code = OneToOneField(to=QRCode, on_delete=CASCADE)
    timestamp = DateTimeField(auto_now_add=True)
    quantity = DecimalField(default=0, max_digits=16, decimal_places=2)
    on_hold = BooleanField(default=False)

    def __str__(self):
        return f"{self.item} / {self.warehouse} / {self.packaging} / {self.unit_category} / {self.quality_checked}"

    def save(self, **kwargs):
        if self.quantity < 0:
            raise NegativeQuantityError(
                quantity=self.quantity,
                message="Cannot set negative quantities in a queue record",
            )
        super(InventoryQueueRecord, self).save(**kwargs)



class Vehicle(CreateUpdateStatus, ArchiveField):
    tenant = ForeignKey(
        Tenant, on_delete=PROTECT, limit_choices_to=limit_to_active
    )
    vehicle_number = CharField(max_length=100)
    vehicle_photo = ThumbnailerImageField(blank=True, null=True)
    make = CharField(max_length=255, blank=True)
    manufacturer = CharField(max_length=255, blank=True)
    model = CharField(max_length=255, blank=True)
    date_of_issue = DateField(blank=True, null=True)
    end_of_life = DateField(blank=True, null=True)
    gross_weight = PositiveFloatField(blank=True, null=True)
    allowed_total_weight = PositiveFloatField()
    insurer = CharField(max_length=255, blank=True, null=True)
    insurance_number = CharField(max_length=255, blank=True, null=True)
    insurance_end_date = DateField(
        validators=[future_date_check], blank=True, null=True
    )
    puc_end_date = DateField(
        validators=[future_date_check], blank=True, null=True
    )
    road_permit_number = CharField(max_length=255, blank=True)
    issued_by_road_agency = CharField(max_length=255, blank=True)
    permit_expiry_date = DateField(
        validators=[future_date_check], blank=True, null=True
    )
    headlights_working = BooleanField(default=False)
    reverse_horn_working = BooleanField(default=False)
    turn_signal_working = BooleanField(default=False)
    brake_system_working = BooleanField(default=False)
    tyre_pressure_adequate = BooleanField(default=False)
    documents = ManyToManyField(to="Document", blank=True)

    def __str__(self):
        return self.vehicle_number

    class Meta:
        indexes = [
            GinIndex(
                SearchVector("vehicle_number", config="english"),
                name="vehicle_number_gin",
            ),
        ]


class VehicleImage(Model):
    image = ThumbnailerImageField()
    vehicle = ForeignKey(to="Vehicle", on_delete=PROTECT)


class VehicleWeight(Model):
    gross_weight = FloatField(default=0.0)
    gross_image = ThumbnailerImageField(blank=True)
    tare_weight = FloatField(default=0.0)
    tare_image = ThumbnailerImageField(blank=True)
    net_weight = FloatField(default=0.0)
    net_image = ThumbnailerImageField(blank=True)
    center_weight = FloatField(default=0.0)
    center_weight_image = ThumbnailerImageField(blank=True)



class Driver(CreateUpdateStatus, ArchiveField):
    class Meta:
        unique_together = (
            "name",
            "tenant",
        )

    tenant = ForeignKey(
        Tenant, on_delete=PROTECT, limit_choices_to=limit_to_active
    )
    license_number = CharField(max_length=100)
    name = CharField(max_length=255)
    phone_number = PhoneNumberField(blank=True)
    driver_photo = ThumbnailerImageField(blank=True, null=True)
    date_of_birth = DateField()
    license_issuing_authority = CharField(max_length=255, blank=True)
    license_issue_date = DateField(blank=True, null=True)
    license_photo = ThumbnailerImageField(blank=True, null=True)
    insurance_number = CharField(max_length=255, blank=True)
    two_wheeler_light = BooleanField(default=False)
    two_wheeler_any = BooleanField(default=False)
    four_wheeler_light = BooleanField(default=False)
    four_wheeler_any = BooleanField(default=False)
    commercial_truck = BooleanField(default=False)
    commercial_trailer = BooleanField(default=False)
    commercial_forklift = BooleanField(default=False)

    def __str__(self):
        return f"{self.name} / {self.license_number}"



class GoodsReceiptNote(
    CreateUpdate, AbstractBlankAddress, ArchiveField, ApprovalField
):
#    TEMPLATE = "common/transaction/grn.html"
    tenant = ForeignKey(
        Tenant, on_delete=PROTECT
        #, limit_choices_to=limit_to_active
    )
    grn_number = UpperCharField(max_length=32, blank=True)
    prefixed_grn_number = UpperCharField(max_length=32, blank=True, null=True)
    grn_date = DateField()
    is_qced = BooleanField(default=False)
    delivery_challan_number = CharField(max_length=255, blank=True)
    delivery_challan_date = DateField(blank=True, null=True)
    gross_weight_by_trade_partner = PositiveFloatField(blank=True, null=True)
    gross_weight_by_us = PositiveFloatField(blank=True, null=True)
    tare_weight_by_trade_partner = PositiveFloatField(blank=True, null=True)
    tare_weight_by_us = PositiveFloatField(blank=True, null=True)
    center_weight_slip_by_trade_partner = PositiveFloatField(
        blank=True, null=True
    )
    center_weight_slip_by_us = PositiveFloatField(blank=True, null=True)
    trade_partner_bill_number = CharField(max_length=255, blank=True)
    trade_partner_documents = ManyToManyField(
        to="Document",
        related_name="trade_partner_documents_goods_receipt_note",
        blank=True,
    )
    center_documents = ManyToManyField(
        to="Document",
        related_name="center_documents_goods_receipt_note",
        blank=True,
    )
    trade_partner_bill_date = DateField(blank=True, null=True)
    trade_partner_bill_documents = ManyToManyField(
        to="Document",
        related_name="trade_partner_bill_documents_goods_receipt_note",
        blank=True,
    )
    e_way_bill_number = CharField(max_length=255, blank=True)
    e_way_bill_date = DateField(blank=True, null=True)
    e_way_bill_documents = ManyToManyField(
        to="Document",
        related_name="e_way_bill_documents_goods_receipt_note",
        blank=True,
    )
    manifest_number = CharField(max_length=255, blank=True)
    manifest_date = DateField(blank=True, null=True)
    manifest_image = ThumbnailerImageField(blank=True, null=True)
    transaction_rating = CharField(max_length=255, blank=True)
    is_system_grn = BooleanField(
        default=False,
        help_text="System generated grn used for reclassification of items and other purposes",
    )
    traced_path_image = ThumbnailerImageField(blank=True, null=True)
    total_distance = FloatField(blank=True, null=True)
    total_time_taken = FloatField(blank=True, null=True)
    remarks = TextField(blank=True)
    delivered_on_time = BooleanField(default=False)
    quality_check_passed = BooleanField(default=False)
    good_condition = BooleanField(default=False)
    temperature_control_maintained = BooleanField(default=False)
    secure_packing = BooleanField(default=False)
    received_intact = BooleanField(default=False)
    # qr_code_image = ThumbnailerImageField(blank=True, null=True)
    # qr_code = OneToOneField(
    #     QRCode,
    #     on_delete=PROTECT,
    #     limit_choices_to=dict(inventory_type=QRCodeType.GRN),
    # )

    trade_partner = ForeignKey(
        to="TradePartner", on_delete=PROTECT
        # , limit_choices_to=limit_to_active
    )
    billing_address = ForeignKey(
        to="TradePartnerAddress",
        on_delete=PROTECT,
        related_name="goods_receipt_note_billing_address",
        limit_choices_to={**limit_to_active(), "is_billing": True},
        blank=True,
        null=True,
    )
    shipping_address = ForeignKey(
        to="TradePartnerAddress",
        on_delete=PROTECT,
        related_name="goods_receipt_note_shipping_address",
        limit_choices_to={**limit_to_active(), "is_shipping": True},
        blank=True,
        null=True,
    )
    warehouse = ForeignKey(
        to="Warehouse", on_delete=PROTECT, limit_choices_to=limit_to_active
    )
    vehicle = ForeignKey(
        to="Vehicle",
        on_delete=PROTECT,
     #   limit_choices_to=limit_to_active,
        blank=True,
        null=True,
    )
    driver = ForeignKey(
        to="Driver",
        on_delete=PROTECT,
     #   limit_choices_to=limit_to_active,
        blank=True,
        null=True,
    )
    transaction_currency = ForeignKey(
        to="Currency", on_delete=PROTECT
        #, limit_choices_to=limit_to_active
    )
    purchase_order = ForeignKey(
        to="PurchaseOrder",
        on_delete=PROTECT,
    #    limit_choices_to=limit_to_approved,
        blank=True,
        null=True,
    )
    dispatch_order = OneToOneField(
        to="DispatchOrder",
        on_delete=PROTECT,
  #      limit_choices_to=limit_to_approved,
        blank=True,
        null=True,
    )
    approved_documents = ManyToManyField(Document, blank=True)
    lorry_receipt_number = CharField(max_length=255, blank=True)
    lorry_receipt_date = DateField(blank=True, null=True)
    lorry_receipt_documents = ManyToManyField(
        to="Document",
        related_name="lorry_receipt_documents_goods_receipt_note",
        blank=True,
    )
    transporter_name = CharField(max_length=255, blank=True)

    class Meta:
        unique_together = (("grn_number", "tenant"),)
        permissions = [
            ("approve_goodsreceiptnote", "Can approve the goods receipt note"),
        ]
        indexes = [
            GinIndex(
                SearchVector("prefixed_grn_number", config="english"),
                name="grn_number_gin",
            ),
            GinIndex(
                SearchVector("e_way_bill_number", config="english"),
                name="grn_eway_gin",
            ),
        ]

    def allow_create(self, user):
        entity_obj = EntityUserAccess.objects.filter(
            user=user,
            entity=self.warehouse.center.entity,
            permissions__codename="create_goodsreceiptnote",
        ).first()
        return True if entity_obj else False

    @property
    def get_entity_id(self):
        if not self.pk:
            return None
        return self.warehouse.center.entity.id

    @property
    def vehicle_number(self):
        return self.vehicle.vehicle_number if self.vehicle else "-"

    @property
    def india_gst_segment(self):
        return (
            IndiaGstSegment.WITHIN_STATE
            if self.billing_address
            and self.billing_address.state.lower() == self.warehouse.center.state.lower()
            else IndiaGstSegment.OUTSIDE_STATE
        )

    @property
    def india_union_territory(self):
        return (
            self.india_gst_segment == IndiaGstSegment.WITHIN_STATE
            and self.billing_address.is_india_union_territory
        )

    @property
    def has_same_unit_category(self):
        return self.grnlineitem_set.distinct("unit__category").count() == 1

    @property
    def total_quantity(self):
        if self.has_same_unit_category:
            return self.grnlineitem_set.aggregate(
                total_quantity=Sum("quantity", default=0)
            ).get("total_quantity", 0)
        return 0

    @property
    def displayable_total_quantity_maximum(self):
        result = (
            self.grnlineitem_set.values("unit__category")
            .annotate(
                total_quantity=Sum("quantity"),
                primary_unit=Subquery(
                    UnitOfMeasurement.objects.filter(
                        category=OuterRef("unit__category"),
                        is_primary_unit=True,
                    ).values("unique_quantity_code")[:1]
                ),
            )
            .order_by("-total_quantity")
        )
        if not result.exists():
            return "-"
        max_entry = result.first()
        return f"{max_entry.get('total_quantity')} {max_entry.get('primary_unit')}"

    @property
    def displayable_number_of_additional_uoms(self):
        result = (
            self.grnlineitem_set.values("unit__category")
            .annotate(
                total_quantity=Sum("quantity"),
                primary_unit=Subquery(
                    UnitOfMeasurement.objects.filter(
                        category=OuterRef("unit__category"),
                        is_primary_unit=True,
                    ).values("unique_quantity_code")[:1]
                ),
            )
            .order_by("-total_quantity")
        )
        if not result.exists() or len(result) == 1:
            return ""
        return f"+ {len(result) - 1} more.."

    def unit(self):
        if self.has_same_unit_category:
            if line_item := self.grnlineitem_set.first():
                return UnitOfMeasurement.objects.filter(
                    is_primary_unit=True, category=line_item.unit.category
                ).first()
        return None

    @property
    def quantity_left(self):
        if self.has_same_unit_category:
            return sum([x.quantity_left for x in self.grnlineitem_set.all()])
        return 0

    def consumed_quantity(self):
        if self.has_same_unit_category:
            return Decimal(str(self.total_quantity)) - self.quantity_left
        return 0

    @property
    def total_amount(self):
        return sum([x.net_total for x in self.grnlineitem_set.all()])

    def __str__(self):
        return self.grn_number

    @property
    def total_grn_line_item_quantity(self):
        grn_total = []
        for category in serialize(UnitCategory):
            unit = UnitOfMeasurement.objects.filter(
                category=category["value"], is_primary_unit=True
            ).first()
            quantity = (
                self.grnlineitem_set.filter(unit__category=category["value"])
                .aggregate(total_quantity=Sum("quantity", default=0))
                .get("total_quantity", 0)
            )
            if quantity and unit:
                grn_total.append(
                    dict(
                        quantity=quantity,
                        unit=unit.unique_quantity_code if unit else "",
                        heading=f"{category['name']} Total",
                    )
                )
        return grn_total
    
    # The next three properties incorrectly used self.aggregate() and/or referenced non-existent fields.
    # @property
    # def total_grn_gross_weight(self):
    #     gross_total = []
    #     for category in serialize(UnitCategory):
    #         unit = UnitOfMeasurement.objects.filter(
    #             category=category["value"], is_primary_unit=True
    #         ).first()
    #         quantity = self.aggregate(
    #             gross_quantity=Sum("gross_weight_by_us", default=0)
    #         ).get("gross_quantity", 0)
    #         if quantity and unit:
    #             gross_total.append(
    #                 dict(
    #                     quantity=quantity,
    #                     unit=unit.unique_quantity_code if unit else "",
    #                     heading=f"{category['name']} Total",
    #                 )
    #             )
    #     return gross_total

    # @property
    # def total_grn_tare_weight(self):
    #     tare_total = []
    #     for category in serialize(UnitCategory):
    #         unit = UnitOfMeasurement.objects.filter(
    #             category=category["value"], is_primary_unit=True
    #         ).first()
    #         quantity = self.aggregate(
    #             tare_quantity=Sum("tare_weight_by_us", default=0)
    #         ).get("tare_quantity", 0)
    #         if quantity and unit:
    #             tare_total.append(
    #                 dict(
    #                     quantity=quantity,
    #                     unit=unit.unique_quantity_code if unit else "",
    #                     heading=f"{category['name']} Total",
    #                 )
    #             )
    #     return tare_total

    # @property
    # def total_grn_net_weight(self):
    #     net_total = []
    #     for category in serialize(UnitCategory):
    #         unit = UnitOfMeasurement.objects.filter(
    #             category=category["value"], is_primary_unit=True
    #         ).first()
    #         quantity = self.aggregate(
    #             total_net=sum(F("gross_weight") - F("tare_weight"))
    #         ).get("total_net", 0)
    #         if quantity and unit:
    #             net_total.append(
    #                 dict(
    #                     quantity=quantity,
    #                     unit=unit.unique_quantity_code if unit else "",
    #                     heading=f"{category['name']} Total",
    #                 )
    #             )
    #     return net_total

    @property
    def total_per_quantity(self):
        return sum(line.per_quantity for line in self.grnlineitem_set.all())

    @property
    def total_rate(self):
        return sum(line.rate for line in self.grnlineitem_set.all())

    @property
    def total_post_tax_value(self):
        return sum(line.post_tax_total for line in self.grnlineitem_set.all())

    @property
    def total_pre_tax_value(self):
        return sum(line.net_total for line in self.grnlineitem_set.all())

    # Incorrect: self.aggregate(...) on a model instance — comment out.
    # @property
    # def total_gross_weight(self):
    #     return (
    #         self.aggregate(total_gross=sum("gross_weight_by_us"))[
    #             "total_gross"
    #         ]
    #         or 0
    #     )

    # @property
    # def total_tare_weight(self):
    #     return (
    #         self.aggregate(total_tare=sum("tare_weight_by_us"))["total_tare"]
    #         or 0
    #     )

    # @property
    # def total_net_weight(self):
    #     return (
    #         self.aggregate(
    #             total_net=sum(F("gross_weight") - F("tare_weight"))
    #         )["total_net"]
    #         or 0
    #     )

    @property
    def get_readable_status(self):
        return self.status.capitalize()

    @property
    def net_weight_by_trade_partner(self):
        if (
            not self.gross_weight_by_trade_partner
            or not self.tare_weight_by_trade_partner
        ):
            return 0
        return (
            self.gross_weight_by_trade_partner
            - self.tare_weight_by_trade_partner
        )

    @property
    def net_weight_by_us(self):
        if not self.gross_weight_by_us or not self.tare_weight_by_us:
            return 0
        return self.gross_weight_by_us - self.tare_weight_by_us

    def clean(self):
        validation_dict = {}

        weight_message = "This should be not greater than gross weight."
        if (
            self.gross_weight_by_trade_partner
            and self.tare_weight_by_trade_partner
            and self.gross_weight_by_trade_partner
            < self.tare_weight_by_trade_partner
        ):
            validation_dict["tare_weight_by_trade_partner"] = weight_message
        if (
            self.gross_weight_by_us
            and self.tare_weight_by_us
            and self.gross_weight_by_us < self.tare_weight_by_us
        ):
            validation_dict["tare_weight_by_us"] = weight_message

        if (
            self.dispatch_order
            and self.dispatch_order.dispatch_date > self.grn_date
        ):
            validation_dict[
                "grn_date"
            ] = "This date cannot be less than Dispatch Order Date."

        if validation_dict:
            raise ValidationError(validation_dict)

    def save(self, **kwargs):
        """Auto-set GRN numbers and date"""
        with transaction.atomic():
            if not self.grn_date:
                self.grn_date = timezone_date()

            if not self.prefixed_grn_number:
                count = GoodsReceiptNote.objects.count() + 1
                self.prefixed_grn_number = f"TXN-{timezone_now().year}-{count:04d}"

            if not self.grn_number:
                count = GoodsReceiptNote.objects.count() + 1
                self.grn_number = f"GRN-{count:04d}"

            # Persist to DB
            super().save(**kwargs)

    # def save(self, **kwargs):
    #     """
    #     Override save to set defaults, but make sure to call super().save()
    #     """
    #     with transaction.atomic():
    #         # Default GRN date
    #         if not self.grn_date:
    #             self.grn_date = timezone_date()

    #         # Auto-generate prefixed GRN number
    #         if not self.prefixed_grn_number:
    #             # Example simple logic (replace with your SerialMaster/Counter if needed)
    #             count = GoodsReceiptNote.objects.count() + 1
    #             self.prefixed_grn_number = f"TXN-{timezone_now().year}-{count:04d}"

    #         # Auto-generate GRN number
    #         if not self.grn_number:
    #             count = GoodsReceiptNote.objects.count() + 1
    #             self.grn_number = f"GRN-{count:04d}"

    #         # 🚀 This actually saves it to DB
    #         super().save(**kwargs)

    # def save(self, **kwargs):
    #     with transaction.atomic():
    #         if not self.grn_date:
    #             self.grn_date = timezone_date()
    #         if not self.prefixed_grn_number:
    #             serial_master = SerialMaster.objects.filter(
    #                 entity=self.warehouse.center.entity,
    #                 document_type=DocumentType.GRN,
    #             ).first()
    #             prefix = (
    #                 ""
    #                 if not serial_master
    #                 else serial_master.generate_prefix(self.grn_date)
    #             )
    #             counter: Counter = Counter.objects.filter(
    #                 tenant=self.tenant,
    #                 document_type=DocumentType.GRN,
    #             ).first()
    #             if not counter:
    #                 raise ValueError(
    #                     "Counter instance doesn't exist. Fix this"
    #                 )
    #             suffix = counter.generate_suffix()
    #             self.prefixed_grn_number = (
    #                 f"{prefix}-{suffix}" if prefix else suffix
    #             )


            # if not self.grn_number:
            #     max_retries = 5
            #     retries = 0
            #     while retries < max_retries:
            #         self.grn_number = create_code(
            #             QRCodeType.GRN, self.grn_date
            #         )
            #         if (
            #             not QRCode.objects.filter(
            #                 code=self.grn_number, tenant=self.tenant
            #             )
            #             .exclude(pk=self.pk)
            #             .exists()
            #         ):
            #             break
            #         retries += 1
            #         print(
            #             f"Retrying QR Code generation ({retries}/{max_retries})"
            #         )
            
            
            
            
            # if not hasattr(self, "transaction_currency"):
            #     self.transaction_currency = (
            #         self.trade_partner.transaction_currency
            #     )



            # if not self.qr_code_id:
            #     qr_code = QRCode(
            #         inventory_type=QRCodeType.GRN,
            #         tenant=self.tenant,
            #         code=self.grn_number,
            #     )
            #     qr_code.save()
            #     self.qr_code = qr_code
            # super(GoodsReceiptNote, self).save(**kwargs)

    @property
    def either_city(self) -> Optional[str]:
        if self.shipping_address:
            return self.shipping_address.city
        if self.billing_address:
            return self.billing_address.city

    def get_context_data(self) -> dict:
        now = timezone.now()
        ist_timezone = pytz.timezone("Asia/Kolkata")
        ist_now = now.astimezone(ist_timezone)
        return dict(
            grn=self,
            pdf_name=self.pdf_name,
            grn_line_items=self.grnlineitem_set.all(),
            current_time=ist_now.strftime("%B %d %Y, %I:%M %p"),
            combined_documents=list(self.trade_partner_documents.all())
            + list(self.center_documents.all()),
        )

    # def pdf_name(self) -> str:
    #     return f"{self.grn_number} {self.grn_date}"

    # def create_for_sending(self, request=None):
    #     ctx = self.get_context_data()
    #     html_string = render_to_string(self.TEMPLATE, ctx)
    #     template = django_engine.from_string(html_string)
    #     markup = template.render(ctx)

    #     css = settings.BASE_DIR / "global_static" / "css" / "transaction.css"

    #     return HTML(string=markup, base_url=settings.BASE_URL).write_pdf(
    #         stylesheets=[CSS(css)]
    #     )


class GrnVehicle(Model):
    vehicle_number = CharField(max_length=128)
    vehicle_make = CharField(max_length=128)
    driver_name = CharField(max_length=128)
    driver_contact = CharField(max_length=128)
    goods_receipt_note = ForeignKey(to="GoodsReceiptNote", on_delete=PROTECT)
    driver_licence_number = CharField(max_length=128)
    gross_weight_by_trade_partner = FloatField()
    gross_weight_by_us = FloatField()
    tare_weight_by_trade_partner = FloatField()
    tare_weight_by_us = FloatField()
    net_weight_by_trade_partner = FloatField()
    net_weight_by_us = FloatField()
    center_weight_slip_by_trade_partner = FloatField()
    center_weight_slip_by_us = FloatField()
    vehicle_photo_front = FileField()
    vehicle_photo_back = FileField()
    vehicle_photo_side = FileField()
    driver_photo = FileField()
    driver_license_photo = FileField()


class GrnLineItem(
    CreateUpdate,
    AbstractBlankAddress,
):
    item = ForeignKey(to="Item", on_delete=PROTECT)
    quantity = PositiveFloatField(default=0)
    rate = PositiveFloatField(default=0)
    packaging = ForeignKey(
        to="Packaging", null=True, blank=True, on_delete=PROTECT
    )
    epr_quantity = PositiveFloatField(blank=True, null=True)
    is_rcm = BooleanField(default=False)
    rcm_code = CharField(max_length=32, blank=True)
    source = ForeignKey(
        to="DynamicEnum",
        on_delete=PROTECT,
        limit_choices_to={"enum": DynamicEnumType.MATERIAL_SOURCE_NAME},
        related_name="source_grn_line_item",
        blank=True,
        null=True,
    )
    goods_receipt_note = ForeignKey(to="GoodsReceiptNote", on_delete=PROTECT)
    documents = ManyToManyField(to="Document", blank=True )
    #, null=True)
    unit = ForeignKey(
        to="UnitOfMeasurement", on_delete=PROTECT, blank=True, null=True
    )
    epr_type = ForeignKey(
        to="DynamicEnum",
        on_delete=PROTECT,
        limit_choices_to={"enum": DynamicEnumType.EPR_TYPE},
        related_name="epr_type_grn_line_item",
        blank=True,
        null=True,
    )
    qc_approved = BooleanField(default=False)
    # purchase_bill = ForeignKey(
    #     to="PurchaseBill",
    #     on_delete=PROTECT,
    #     blank=True,
    #     null=True,
    # )

    bill_quantity = PositiveFloatField(blank=True, null=True)
    bill_rate = PositiveFloatField(blank=True, null=True)
    # purchase_order_item = ForeignKey(
    #     to="PurchaseOrderItem",
    #     on_delete=PROTECT,
    #     blank=True,
    #     null=True,
    # )

    # qr_code = OneToOneField(
    #     QRCode,
    #     on_delete=PROTECT,
    #     limit_choices_to=dict(inventory_type=QRCodeType.GRN_LINE_ITEM),
    # )
    # legacy_qr_code = OneToOneField(
    #     QRCode,
    #     on_delete=PROTECT,
    #     blank=True,
    #     null=True,
    #     related_name="legacy_qr_code_grn_line_item",
    # )
    # trace_qr_codes_file = FileField(max_length=512, blank=True)
    # trace_qr_codes_txt = TextField(blank=True)

    def __str__(self):
        return f"{self.item} / {self.goods_receipt_note}"

    def clean(self):
        if self.unit and self.unit.category != self.item.unit_category:
            raise ValidationError(
                {
                    "unit": "Cannot be in different category from the Item's unit."
                }
            )
        if self.rate_adjustment > self.rate:
            raise ValidationError(
                {"rate_adjustment": "Cannot be greater than the rate."}
            )
        # if (
        #     self.purchase_bill
        #     and self.goods_receipt_note.status != Status.APPROVED
        # ):
        #     raise ValidationError(
        #         {"purchase_bill": "The grn of this item is not approved."}
        #     )

    def save(self, **kwargs):
        if self.is_rcm and not self.rcm_code:
            self.rcm_code = create_code(
                "RCM", self.goods_receipt_note.grn_date
            )
        # if not self.item.is_epr_applicable:
        #     self.epr_quantity = None
        #     self.epr_type = 
        if not getattr(self.item, "is_epr_applicable", False):
            self.epr_quantity = None
            self.epr_type = None

        if not self.unit:
            self.unit = self.item.unit

        # if self.purchase_bill:
        #     self.bill_quantity = (
        #         self.bill_quantity if self.bill_quantity else self.quantity
        #     )
        #     self.bill_rate = self.bill_rate if self.bill_rate else self.rate
        # else:
        #     self.bill_quantity = None
        #     self.bill_rate = None

        # if self.bill_quantity and self.bill_quantity > self.quantity:
        #     raise SerializerValidationError(
        #         {
        #             "bill_quantity": "This cannot be greater than quantity in the Goods Receipt Note."
        #         }
        #     )

        # if purchase_order := self.goods_receipt_note.purchase_order:
        #     purchase_order_item = purchase_order.purchaseorderitem_set.filter(
        #         item=self.item,
        #     ).first()
        #     self.purchase_order_item = purchase_order_item
        # if not self.qr_code_id:
        #     qr_code = QRCode(
        #         inventory_type=QRCodeType.GRN_LINE_ITEM,
        #         tenant=self.goods_receipt_note.tenant,
        #     )
        #     qr_code.save()
        #     self.qr_code = qr_code
        # super(GrnLineItem, self).save(**kwargs)
        super().save(**kwargs)

    # def process_trace_qr_codes(self, commit: bool = True):
    #     counter = 0
    #     success = 0
    #     if self.trace_qr_codes_file:
    #         frame = pd.read_csv(self.trace_qr_codes_file)
    #         for code in frame["codes"].tolist():
    #             counter += 1
    #             sys_qr_code = QRCode.objects.filter(code=code.strip()).first()
    #             if not sys_qr_code:
    #                 logger.debug(f"Skipping {code} [Not in system]")
    #                 continue
    #             trace_source = sys_qr_code.get_code_trace_source()
    #             logger.debug(trace_source)
    #             if not isinstance(trace_source, TraceSource):
    #                 logger.debug(f"Skipping {code} [No Trace Source]")
    #                 continue
    #             trace = InventoryTrace.objects.get_or_create(
    #                 from_qr_code=trace_source.from_qr_code,
    #                 to_qr_code=self.qr_code,
    #                 defaults=dict(
    #                     from_warehouse=trace_source.from_warehouse,
    #                     to_warehouse=self.goods_receipt_note.warehouse,
    #                     from_item=trace_source.from_item,
    #                     to_item=self.item,
    #                     from_packaging=trace_source.from_packaging,
    #                     to_packaging=self.packaging,
    #                     from_unit_category=trace_source.from_unit_category,
    #                     to_unit_category=self.unit.category,
    #                     from_quality_checked=trace_source.from_quality_checked,
    #                     to_quality_checked=False,
    #                     quantity=min(trace_source.quantity, self.quantity),
    #                 ),
    #             )
    #             success += 1
    #             logger.debug(f"Created {trace}")
    #     self.trace_qr_codes_txt = (
    #         f"Able to trace {success} form {counter} codes."
    #     )
    #     if commit:
    #         self.save()

    @property
    def get_entity_id(self):
        if not self.pk:
            return None
        return self.goods_receipt_note.warehouse.center.entity.id

    # @property
    # def qc_approved_status_display(self):
    #     if self.qc_required:
    #         if self.qc_approved:
    #             return "QC Approved"
    #         qc_transactions = self.qualitycontroltransaction_set.all()
    #         if not qc_transactions.filter(
    #             status=Status.APPROVED, final_decision=False
    #         ).exists():
    #             return "QC Pending"
    #         return "QC Failed"
    #     return "QC not required"

    # @property
    # def qc_required(self):
    #     return QualityControlQuestionnaire.objects.filter(
    #         is_active=True,
    #         is_archived=False,
    #         items__in=[self.item],
    #         qc_type=QuestionnaireType.GRN,
    #     ).exists()

    # @property
    # def qc_required_and_approved(self):
    #     return self.qc_approved if self.qc_required else True

    @property
    def has_adjustments(self):
        return self.grnlineitemadjustment_set.exists()

    @property
    def quantity_adjustment(self):
        if not self.id:
            return 0
        return sum(
            adjustment.quantity_adjustment
            for adjustment in self.grnlineitemadjustment_set.all()
        )

    @property
    def rate_adjustment(self):
        if not self.id:
            return 0
        return sum(
            adjustment.rate_adjustment
            for adjustment in self.grnlineitemadjustment_set.all()
        )

    @property
    def tax_group(self):
        return (
            self.item.inter_state_gst
            if self.goods_receipt_note.india_gst_segment
            == IndiaGstSegment.OUTSIDE_STATE
            else self.item.intra_state_gst
        )

    @property
    def tax_total(self):
        partner_has_gst = self.goods_receipt_note.billing_address.gstin
        return (
            0
            if (self.is_rcm or not partner_has_gst)
            else self.tax_rate_calculation
        )

    @property
    def tax_rate_calculation(self):
        tax_value = 0
        for tax in self.tax_group.taxes.all():
            tax_value += tax.rate * self.net_total
        return tax_value

    @property
    def post_tax_total(self):
        return round((self.tax_total + self.net_total), 2)

    @property
    def gross_total(self):
        return self.rate * self.base_quantity

    @property
    def net_total(self):
        return self.base_net_quantity * self.net_rate

    @property
    def base_net_quantity(self):
        return (
            (self.net_quantity / self.unit.conversion_rate)
            if self.unit
            else self.net_quantity
        )

    @property
    def base_quantity(self):
        return (
            (self.quantity / self.unit.conversion_rate)
            if self.unit
            else self.quantity
        )

    @property
    def net_quantity(self):
        return self.quantity - self.quantity_adjustment

    @property
    def net_rate(self):
        return self.rate - self.rate_adjustment

    @property
    def source_display(self):
        return self.source.name if self.source else ""

    @property
    def epr_type_display(self):
        if self.epr_type:
            return self.epr_type.name
        return ""

    @property
    def needs_rcm(self):
        partner_has_gst = self.goods_receipt_note.billing_address.gstin
        center_has_gst = self.goods_receipt_note.warehouse.center.gstin
        item_needs_rcm = self.item.is_rcm_applicable
        return item_needs_rcm and center_has_gst and not partner_has_gst

    @property
    def rcm_total(self):
        return self.tax_rate_calculation if self.is_rcm else 0

    @property
    def bill_total(self):
        return (
            self.bill_base_quantity * self.bill_rate
            if self.bill_base_quantity and self.bill_rate
            else 0
        )

    @property
    def bill_tax_rate_calculation(self):
        tax_value = 0
        for tax in self.tax_group.taxes.all():
            tax_value += tax.rate * self.bill_total
        return tax_value

    @property
    def bill_tax_total(self):
        return 0 if self.is_rcm else self.bill_tax_rate_calculation

    @property
    def bill_post_tax_total(self):
        return self.bill_tax_total + self.bill_total

    @property
    def bill_rcm_total(self):
        return self.bill_tax_rate_calculation if self.is_rcm else 0

    @property
    def bill_base_quantity(self):
        return (
            (self.bill_quantity / self.unit.conversion_rate)
            if self.unit and self.bill_quantity
            else 0
        )

    # @property
    # def quantity_left(self):
    #     queryset = InventoryQueueRecord.objects.filter(
    #         qr_code=self.qr_code,
    #     )
    #     if not queryset.exists():
    #         return 0
    #     queue_record: InventoryQueueRecord = queryset.first()
    #     return Decimal(str(queue_record.quantity))



class AdjustmentReason(CreateUpdateStatus, ArchiveField):
    name = CharField(max_length=255)
    tenant = ForeignKey(
        Tenant, on_delete=PROTECT, limit_choices_to=limit_to_active
    )
    apply_to_all_trade_partners = BooleanField(default=True)
    trade_partners = ManyToManyField(
        TradePartner, limit_choices_to=limit_to_active
    )
    item = ForeignKey(
        Item, on_delete=PROTECT, limit_choices_to=limit_to_active
    )
    factor_unit = ForeignKey(
        UnitOfMeasurement, on_delete=PROTECT, limit_choices_to=limit_to_active
    )
    applies_on_purchase = BooleanField()
    applies_on_sales = BooleanField()

    def clean(self):
        if self.is_active and (
            not self.applies_on_purchase and not self.applies_on_sales
        ):
            raise ValidationError(
                {
                    "is_active": "Either one of the fields from applies on Purchase or Sales should be ticked."
                }
            )

    def clean(self):
        if self.is_active and (
            not self.applies_on_purchase and not self.applies_on_sales
        ):
            raise ValidationError(
                {
                    "is_active": "Either one of the fields from applies on Purchase or Sales should be ticked."
                }
            )

    def __str__(self) -> str:
        return f"{self.name} / {self.item}"

class AdjustmentReasonFactor(CreateUpdateStatus, AbstractAdjustmentField):
    adjustment_reason = ForeignKey(
        AdjustmentReason, on_delete=PROTECT, limit_choices_to=limit_to_active
    )
    start_range = PositiveFloatField()
    end_range = PositiveFloatField()

    @property
    def range_text(self):
        return f"{self.start_range} {self.factor_unit_code} to {self.end_range} {self.factor_unit_code}"

    @property
    def factor_unit_code(self):
        return self.adjustment_reason.factor_unit.unique_quantity_code

    def __str__(self):
        return f"{self.adjustment_reason} / {self.range_text}"

    def clean(self):
        if self.start_range > self.end_range:
            raise ValidationError(
                {
                    "start_range": "The end range cannot be less than start range."
                }
            )


class GrnLineItemAdjustment(CreateUpdate, AbstractAdjustmentField):
    grn_line_item = ForeignKey(GrnLineItem, on_delete=PROTECT)
    factor_value = PositiveFloatField(default=0)
    adjustment_reason_factor = ForeignKey(
        AdjustmentReasonFactor, on_delete=PROTECT
    )

    @property
    def quantity_adjustment(self):
        return (
            self.grn_line_item.quantity * self.quantity_adjustment_percent
            if self.quantity_adjustment_type == AdjustmentType.PERCENT
            else self.quantity_adjustment_value
        )

    @property
    def rate_adjustment(self):
        return (
            self.grn_line_item.rate * self.rate_adjustment_percent
            if self.rate_adjustment_type == AdjustmentType.PERCENT
            else self.rate_adjustment_value
        )

    def clean(self):
        if (
            self.adjustment_reason_factor
            and self.factor_value
            and (
                self.adjustment_reason_factor.start_range > self.factor_value
                or self.adjustment_reason_factor.end_range < self.factor_value
            )
        ):
            raise ValidationError(
                {
                    "factor_value": [
                        "This factor doesn't fall this in adjustment factor."
                    ]
                }
            )

    def __str__(self):
        return f"{self.grn_line_item} / {self.adjustment_reason_factor}"



class TermAndCondition(CreateUpdateStatus, ArchiveField):
    class Meta:
        unique_together = (
            "name",
            "tenant",
        )

    tenant = ForeignKey(
        Tenant, on_delete=PROTECT, limit_choices_to=limit_to_active
    )
    name = CharField(max_length=255)
    type = CharField(max_length=32, choices=TermType.choices)
    terms = TextField()

    @property
    def type_display(self):
        return self.get_type_display()

    def __str__(self):
        return self.name



class PurchaseOrder(CreateUpdate, ApprovalField):
  #  TEMPLATE = "common/transaction/purchaseorder.html"
    trade_partner = ForeignKey(to=TradePartner, on_delete=PROTECT)
    tolerance_allowance = FloatField(default=0)
    should_disclose_rate = BooleanField(default=False)
    billing_address = ForeignKey(
        to=TradePartnerAddress,
        on_delete=PROTECT,
        limit_choices_to={**limit_to_active(), "is_billing": True},
        blank=True,
        null=True,
    )
    trade_partner_bank_account = ForeignKey(
        to=TradePartnerBankAccount, on_delete=PROTECT, null=True, blank=True
    )
    center = ForeignKey(
        to=Center,
        on_delete=PROTECT,
        null=True,
        blank=True,
    )
    warehouse = ForeignKey(to=Warehouse, on_delete=PROTECT)
    purchase_order_number = TextField(blank=True)
    prefixed_purchase_order_number = CharField(
        max_length=32, blank=True, default=""
    )
    purchase_order_date = DateField(default=timezone_date)
    other_cost = FloatField(default=0)
    transport_cost = FloatField(default=0)
    round_off = FloatField(default=0)
    tcs_percent = FloatField(default=0)
    tds_percent = FloatField(default=0)
    terms_and_conditions = ManyToManyField(
        TermAndCondition,
        blank=True,
        related_name="terms_and_conditions",
    )
    delivery_terms_and_conditions = ManyToManyField(
        TermAndCondition,
        blank=True,
        related_name="delivery_terms_and_conditions",
    )
    remarks = TextField(blank=True)
    # qr_code = OneToOneField(
    #     QRCode,
    #     on_delete=PROTECT,
    #     limit_choices_to=dict(inventory_type=QRCodeType.PURCHASE_ORDER),
    # )
    approved_documents = ManyToManyField(Document, blank=True)

    def allow_create(self, user):
        entity_obj = EntityUserAccess.objects.filter(
            user=user,
            entity=self.center.entity,
            permissions__codename="create_purchaseorder",
        ).first()
        return True if entity_obj else False

    @property
    def get_entity_id(self):
        if not self.pk:
            return None
        return self.center.entity.id

    def __str__(self) -> str:
        return f"{self.purchase_order_number} / {self.trade_partner} / {self.warehouse}"

    def save(self, **kwargs):
        with transaction.atomic():
            # if not self.purchase_order_number:
            #     self.purchase_order_number = create_code(
            #         QRCodeType.PURCHASE_ORDER, self.purchase_order_date
            #     )
            if not self.prefixed_purchase_order_number:
                entity = self.warehouse.center.entity
                serial_master = SerialMaster.objects.filter(
                    entity=entity,
                    document_type=DocumentType.PURCHASE_ORDER,
                ).first()
                prefix = (
                    ""
                    if not serial_master
                    else serial_master.generate_prefix(
                        self.purchase_order_date
                    )
                )
                counter: Counter = Counter.objects.filter(
                    tenant=self.trade_partner.tenant,
                    document_type=DocumentType.PURCHASE_ORDER,
                ).first()
                if not counter:
                    raise ValueError(
                        "Counter instance doesn't exist. Fix this"
                    )
                suffix = counter.generate_suffix()
                self.prefixed_purchase_order_number = (
                    f"{prefix}-{suffix}" if prefix else suffix
                )
            # if not self.qr_code_id:
            #     qr_code = QRCode(
            #         inventory_type=QRCodeType.PURCHASE_ORDER,
            #         tenant=self.warehouse.tenant,
            #         code=self.purchase_order_number,
            #     )
            #     qr_code.save()
            #     self.qr_code = qr_code
            super(PurchaseOrder, self).save(**kwargs)

    @property
    def india_gst_segment(self):
        return (
            IndiaGstSegment.WITHIN_STATE
            if self.warehouse.center.state.lower()
            == self.billing_address.state.lower()
            else IndiaGstSegment.OUTSIDE_STATE
        )

    @property
    def india_union_territory(self) -> bool:
        return (
            self.india_gst_segment == IndiaGstSegment.WITHIN_STATE
            and self.warehouse.center.is_india_union_territory
        )

    @property
    def item_total(self):
        return sum(
            [x.get_post_tax_value for x in self.purchaseorderitem_set.all()]
        )

    @property
    def gross_total_invoice(self):
        return self.item_total + self.other_cost + self.transport_cost

    @property
    def total_tcs(self):
        return self.gross_total_invoice * self.tcs_percent

    @property
    def total_post_tcs(self):
        return self.total_tcs + self.gross_total_invoice

    @property
    def total_tds(self):
        return self.total_post_tcs * self.tds_percent

    @property
    def total_post_tds(self):
        return self.total_post_tcs - self.total_tds

    @property
    def rcm_payable(self):
        return sum([x.rcm_payable for x in self.purchaseorderitem_set.all()])

    @property
    def total_quantity(self):
        return sum(line.quantity for line in self.purchaseorderitem_set.all())

    @property
    def total_received_quantity(self):
        approved_grns = GoodsReceiptNote.objects.filter(
            purchase_order=self, status=Status.APPROVED
        )
        total_received = 0
        for grn in approved_grns:
            total_received += sum(
                grn_line_item.quantity
                for grn_line_item in grn.grnlineitem_set.all()
            )
        return total_received

    @property
    def remaining_quantity(self):
        remaining = self.total_quantity - self.total_received_quantity
        print(f"Remaining Quantity: {remaining}")
        return remaining

    @property
    def total_rate(self):
        return sum(line.rate for line in self.purchaseorderitem_set.all())

    @property
    def total_post_tax_value(self):
        total_value = sum(
            line.get_post_tax_value
            for line in self.purchaseorderitem_set.all()
        )
        return total_value

    @property
    def total_item_quantity(self):
        purchase_total = []
        for category in serialize(UnitCategory):
            unit = UnitOfMeasurement.objects.filter(
                category=category["value"], is_primary_unit=True
            ).first()
            quantity = (
                self.purchaseorderitem_set.filter(
                    unit__category=category["value"]
                )
                .aggregate(total_quantity=Sum("quantity", default=0))
                .get("total_quantity", 0)
            )
            if quantity and unit:
                purchase_total.append(
                    dict(
                        quantity=quantity,
                        unit=unit.unique_quantity_code if unit else "",
                        heading=f"{category['name']} Total",
                    )
                )
        return purchase_total

    @property
    def get_readable_status(self):
        return self.status.capitalize()

    @property
    def conversion_rate_value(self):
        return 1

    def get_context_data(self) -> dict:
        return dict(
            purchase=self,
            pdf_name=self.pdf_name,
            purchase_items=self.purchaseorderitem_set.all(),
        )

    def pdf_name(self) -> str:
        return f"{self.purchase_order_number} {self.purchase_order_date}"

    # def create_for_sending(self, request):
    #     ctx = self.get_context_data()
    #     html_string = render_to_string(self.TEMPLATE, ctx)
    #     template = django_engine.from_string(html_string)
    #     markup = template.render(ctx)

    #     css = settings.BASE_DIR / "global_static" / "css" / "transaction.css"

    #     return HTML(
    #         string=markup, base_url=request.build_absolute_uri()
    #     ).write_pdf(stylesheets=[CSS(css)])



class Port(CreateUpdateStatus, AbstractAddress):
    name = CharField(max_length=255)

    def __str__(self):
        return f"{self.name} / {self.address_line}"

class DispatchOrder(CreateUpdate, ArchiveField, ApprovalField):
    #    TEMPLATE = "common/transaction/dispatchorder.html"
    dispatch_number = UpperCharField(max_length=32, blank=True)
    prefixed_dispatch_number = UpperCharField(
        max_length=32, blank=True, null=True
    )
    dispatch_date = DateField()
    is_external = BooleanField(default=False)
    tenant = ForeignKey(
        Tenant, on_delete=PROTECT
        #, limit_choices_to=limit_to_active
    )
    warehouse = ForeignKey(
        to="Warehouse", on_delete=PROTECT
        #, limit_choices_to=limit_to_active
    )
    trade_partner = ForeignKey(
        to="TradePartner",
        on_delete=PROTECT,
        limit_choices_to={**limit_to_active(), "is_customer": True},
    )
    billing_address = ForeignKey(
        to="TradePartnerAddress",
        on_delete=PROTECT,
        related_name="dispatch_order_billing_address",
        limit_choices_to={**limit_to_active(), "is_billing": True},
        blank=True,
        null=True,
    )
    shipping_address = ForeignKey(
        to="TradePartnerAddress",
        on_delete=PROTECT,
        related_name="dispatch_order_shipping_address",
        limit_choices_to={**limit_to_active(), "is_shipping": True},
        blank=True,
        null=True,
    )
    dispatch_mode = CharField(
        max_length=8, choices=DispatchMode.choices, default=DispatchMode.ROAD
    )
    vehicle = ForeignKey(
        to="Vehicle",
        on_delete=PROTECT,
        limit_choices_to=limit_to_active,
        blank=True,
        null=True,
    )
    driver = ForeignKey(
        to="Driver",
        on_delete=PROTECT,
        limit_choices_to=limit_to_active,
        blank=True,
        null=True,
    )
    traced_path_image = ThumbnailerImageField(blank=True, null=True)
    total_distance = PositiveFloatField(blank=True, null=True)
    total_time_taken = PositiveFloatField(blank=True, null=True)
    remarks = TextField(blank=True)
    delivered_on_time = BooleanField(default=False)
    quality_check_passed = BooleanField(default=False)
    good_condition = BooleanField(default=False)
    temperature_control_maintained = BooleanField(default=False)
    secure_packing = BooleanField(default=False)
    received_intact = BooleanField(default=False)
    e_way_bill_number = CharField(max_length=255, blank=True)
    e_way_bill_date = DateField(blank=True, null=True)
    lorry_receipt_number = CharField(max_length=255, blank=True)
    lorry_receipt_date = DateField(blank=True, null=True)
    sales_order = ForeignKey(
        to="SalesOrder", on_delete=PROTECT, blank=True, null=True
    )
    sales_order_number = CharField(max_length=255, blank=True)
    sales_order_date = DateField(blank=True, null=True)
    trade_partner_order_number = CharField(max_length=255, blank=True)
    trade_partner_order_date = DateField(blank=True, null=True)
    gross_weight_by_trade_partner = PositiveFloatField(blank=True, null=True)
    gross_weight_by_us = PositiveFloatField(blank=True, null=True)
    tare_weight_by_trade_partner = PositiveFloatField(blank=True, null=True)
    tare_weight_by_us = PositiveFloatField(blank=True, null=True)
    inco_terms = CharField(
        max_length=16, choices=IncoTerm.choices, blank=True, null=True
    )
    export_line = CharField(max_length=255, blank=True)
    export_vessel = CharField(max_length=255, blank=True)
    export_container = CharField(max_length=255, blank=True)
    export_house = CharField(max_length=255, blank=True)
    export_house_bill_of_lading_number = CharField(max_length=255, blank=True)
    export_house_bill_of_lading_date = DateField(blank=True, null=True)
    country_of_origin = CharField(
        max_length=8, choices=list(CountryField().choices), blank=True
    )
    port_of_loading = ForeignKey(
        to=Port,
        on_delete=PROTECT,
        related_name="port_of_loading_dispatch_order",
        blank=True,
        null=True,
    )
    port_of_discharge = ForeignKey(
        to=Port,
        on_delete=PROTECT,
        related_name="port_of_discharge_dispatch_order",
        blank=True,
        null=True,
    )
    country_destination = CharField(
        max_length=8, choices=list(CountryField().choices), blank=True
    )
    seal_number = CharField(max_length=255, blank=True)
    seal_date = DateField(blank=True, null=True)
    seal_bill_of_lading_number = CharField(max_length=255, blank=True)
    seal_bill_of_lading_date = DateField(blank=True, null=True)
    term_and_conditions = ManyToManyField(TermAndCondition, blank=True)
    documents = ManyToManyField(
        to=Document, related_name="documents_dispatch_order", blank=True
    )
    sales_order_documents = ManyToManyField(
        to=Document,
        related_name="sales_order_documents_dispatch_order",
        blank=True,
    )
    packaging_documents = ManyToManyField(
        to=Document,
        related_name="packaging_documents_dispatch_order",
        blank=True,
    )
    transportation_documents = ManyToManyField(
        to=Document,
        related_name="transportation_documents_dispatch_order",
        blank=True,
    )
    export_documents = ManyToManyField(
        to=Document,
        related_name="export_documents_dispatch_order",
        blank=True,
    )
    # QR / BALe related fields are intentionally left commented out.
    # qr_code_image = ThumbnailerImageField(blank=True, null=True)
    # qr_code = OneToOneField(
    #     QRCode,
    #     on_delete=PROTECT,
    #     limit_choices_to=dict(inventory_type=QRCodeType.DISPATCH_ORDER),
    # )
    approved_documents = ManyToManyField(Document, blank=True)
    trade_partner_bill_number = CharField(max_length=255, blank=True)
    trade_partner_bill_date = DateField(blank=True, null=True)

    class Meta:
        unique_together = (("dispatch_number", "tenant"),)
        permissions = [
            ("approve_dispatch_order", "Can approve the dispatch order"),
        ]

    def allow_create(self, user):
        entity_obj = EntityUserAccess.objects.filter(
            user=user,
            entity=self.warehouse.center.entity,
            permissions__codename="create_dispatchorder",
        ).first()
        return True if entity_obj else False

    @property
    def get_entity_id(self):
        if not self.pk:
            return None
        return self.warehouse.center.entity.id

    @property
    def dispatch_mode_display(self):
        return self.get_dispatch_mode_display()

    @property
    def inco_terms_display(self):
        return self.get_inco_terms_display()

    @property
    def country_of_origin_display(self):
        return self.get_country_of_origin_display()

    @property
    def country_destination_display(self):
        return self.get_country_destination_display()

    @property
    def net_weight_by_trade_partner(self):
        # avoid mutating attributes that don't exist; treat missing tare as 0 locally
        if not self.gross_weight_by_trade_partner:
            return 0
        tare = self.tare_weight_by_trade_partner or 0
        return self.gross_weight_by_trade_partner - tare

    @property
    def net_weight_by_us(self):
        if not self.gross_weight_by_us:
            return 0
        tare = self.tare_weight_by_us or 0
        return self.gross_weight_by_us - tare

    @property
    def india_gst_segment(self):
        return (
            IndiaGstSegment.WITHIN_STATE
            if self.billing_address
            and self.billing_address.state.lower()
            == self.warehouse.center.state.lower()
            else IndiaGstSegment.OUTSIDE_STATE
        )

    @property
    def total_quantity(self):
        return self.dispatchlineitem_set.aggregate(
            total_quantity=Sum("quantity", default=0)
        ).get("total_quantity", 0)

    @property
    def total_amount(self):
        return sum([x.net_total for x in self.dispatchlineitem_set.all()])

    @property
    def dispatch_place(self):
        return "Center to Trade Partner"

    @property
    def calculate_total_gross_weight(self):
        # The original implementation used QR / Batch / Bale / GRN outputs which are
        # intentionally omitted. The loop that collected per-line QR outputs was
        # commented-out in the original; keep the function but return only calculated
        # totals based on any explicit gross_weight_by_* fields (if present).
        gross_weight_totals = []
        for category in serialize(UnitCategory):
            unit = UnitOfMeasurement.objects.filter(
                category=category["value"], is_primary_unit=True
            ).first()
            total_gross_weight = 0

            # NOTE: Detailed per-QR logic removed because QR / Bale / Batch fields are unused.
            # If you re-enable QR-related fields later, restore the per-line logic here.



          
            if total_gross_weight > 0 and unit:
                gross_weight_totals.append(
                    dict(
                        quantity=total_gross_weight,
                        unit=unit.unique_quantity_code if unit else "",
                        heading=f"{category['name']} Gross Weight Total",
                    )
                )
        return gross_weight_totals

    @property
    def calculate_total_packaging_weight(self):
        # Packaging weight calculation originally relied on QR outputs — kept minimal here.
        packaging_weight_totals = []
        for category in serialize(UnitCategory):
            unit = UnitOfMeasurement.objects.filter(
                category=category["value"], is_primary_unit=True
            ).first()
            total_packaging_weight = 0

            # NOTE: per-QR packaging weight logic removed (related fields are unused).

            if total_packaging_weight > 0 and unit:
                packaging_weight_totals.append(
                    dict(
                        quantity=total_packaging_weight,
                        unit=unit.unique_quantity_code if unit else "",
                        heading=f"{category['name']} Gross Weight Total",
                    )
                )
        return packaging_weight_totals

    @property
    def calculate_total_net_weight(self):
        gross_weight_totals = self.calculate_total_gross_weight
        packaging_weight_totals = self.calculate_total_packaging_weight
        net_weight_totals = []
        packaging_weights_by_category = {
            item["heading"]: item["quantity"] for item in packaging_weight_totals
        }
        for gross_item in gross_weight_totals:
            heading = gross_item["heading"]
            gross_quantity = gross_item["quantity"]
            packaging_quantity = packaging_weights_by_category.get(heading, 0)
            net_quantity = gross_quantity - packaging_quantity
            if net_quantity > 0:
                net_weight_totals.append(
                    dict(
                        quantity=net_quantity,
                        unit=gross_item["unit"],
                        heading=heading.replace("Gross", "Net"),
                    )
                )
        return net_weight_totals

    @property
    def total_quantity_by_category(self):
        total_qty = []
        for category in serialize(UnitCategory):
            unit = UnitOfMeasurement.objects.filter(
                category=category["value"], is_primary_unit=True
            ).first()
            quantity = (
                self.dispatchlineitem_set.filter(
                    unit__category=category["value"]
                )
                .aggregate(total_quantity=Sum("quantity", default=0))
                .get("total_quantity", 0)
            )
            if quantity and unit:
                total_qty.append(
                    dict(
                        quantity=quantity,
                        unit=unit.unique_quantity_code if unit else "",
                        heading=f"{category['name']} Total",
                    )
                )
        return total_qty

    def __str__(self):
        return self.dispatch_number

    def clean(self):
        message = "This address doesn't belong to this trade partner."
        validation_dict = {}
        if (
            self.billing_address
            and self.billing_address.trade_partner != self.trade_partner
        ):
            validation_dict["billing_address"] = message
        if (
            self.shipping_address
            and self.shipping_address.trade_partner != self.trade_partner
        ):
            validation_dict["shipping_address"] = message

        weight_message = "This should be not greater than gross weight."

        sales_order: SalesOrder
        if sales_order := self.sales_order:
            if sales_order.tenant != self.tenant:
                validation_dict["sales_order"] = "Sales Order not found."
            if sales_order.trade_partner != self.trade_partner:
                validation_dict[
                    "sales_order"
                ] = "This sales order doesn't belong to this trade partner."
            if sales_order.warehouse != self.warehouse:
                validation_dict[
                    "sales_order"
                ] = "This sales order doesn't belong to this warehouse."
        if (
            self.gross_weight_by_trade_partner
            and self.tare_weight_by_trade_partner
            and self.gross_weight_by_trade_partner
            < self.tare_weight_by_trade_partner
        ):
            validation_dict["tare_weight_by_trade_partner"] = weight_message

        if (
            self.gross_weight_by_us
            and self.tare_weight_by_us
            and self.gross_weight_by_us < self.tare_weight_by_us
        ):
            validation_dict["tare_weight_by_trade_partner"] = weight_message

        if validation_dict:
            raise ValidationError(validation_dict)

        if self.pk:
            dispatch_order = DispatchOrder.objects.get(pk=self.pk)
            dispatch_line_item_queryset = DispatchLineItem.objects.filter(
                dispatch_order=self,
            )
            if (
                self.warehouse != dispatch_order.warehouse
                and dispatch_line_item_queryset.exists()
            ):
                raise ValidationError(
                    {
                        "warehouse": "This Dispatch Order has Dispatch Line Items. To change the warehouse, please delete the existing Dispatch Line Items."
                    }
                )

    # def save(self, **kwargs):
    #     with transaction.atomic():
    #         if not self.dispatch_date:
    #             self.dispatch_date = timezone_date()
    #         if not self.prefixed_dispatch_number:
    #             with transaction.atomic():
    #                 entity: Entity = self.warehouse.center.entity
    #                 serial_master = SerialMaster.objects.filter(
    #                     entity=entity,
    #                     document_type=DocumentType.DISPATCH_ORDER,
    #                 ).first()
    #                 prefix = (
    #                     ""
    #                     if not serial_master
    #                     else serial_master.generate_prefix(self.dispatch_date)
    #                 )
    #                 counter: Counter = Counter.objects.filter(
    #                     tenant=self.tenant,
    #                     document_type=DocumentType.DISPATCH_ORDER,
    #                 ).first()
    #                 if not counter:
    #                     raise ValueError(
    #                         "Counter instance doesn't exist. Fix this"
    #                     )
    #                 suffix = counter.generate_suffix()
    #                 self.prefixed_dispatch_number = (
    #                     f"{prefix}-{suffix}" if prefix else suffix
    #                 )
    #         # legacy QR / code generation removed (qr_code field unused)
    #         if sales_order := self.sales_order:
    #             self.sales_order_number = sales_order.sales_order_number
    #             self.sales_order_date = sales_order.sales_order_date
    #             self.trade_partner_order_number = (
    #                 sales_order.trade_partner_order_number
    #             )
    #             self.trade_partner_order_date = (
    #                 sales_order.trade_partner_order_date
    #             )
    #         self.full_clean()
    #         super(DispatchOrder, self).save(**kwargs)

    def save(self, **kwargs):
        with transaction.atomic():
            if not self.dispatch_date:
                self.dispatch_date = timezone_date()
            
            if not self.prefixed_dispatch_number:
                entity: Entity = self.warehouse.center.entity
                serial_master = SerialMaster.objects.filter(
                    entity=entity,
                    document_type=DocumentType.DISPATCH_ORDER,
                ).first()
                prefix = (
                    ""
                    if not serial_master
                    else serial_master.generate_prefix(self.dispatch_date)
                    )
                counter, created = Counter.objects.get_or_create(
                    tenant=self.tenant,
                    document_type=DocumentType.DISPATCH_ORDER,
                    defaults={"counter": 0},  # 👈 adjust to match your Counter fields
                    )
                suffix = counter.generate_suffix()
                self.prefixed_dispatch_number = (
                    f"{prefix}-{suffix}" if prefix else suffix
                    )

            if sales_order := self.sales_order:
                self.sales_order_number = sales_order.sales_order_number
                self.sales_order_date = sales_order.sales_order_date
                self.trade_partner_order_number = (
                    sales_order.trade_partner_order_number
                    )
                self.trade_partner_order_date = (
                    sales_order.trade_partner_order_date
                    )
            self.full_clean()
            super(DispatchOrder, self).save(**kwargs)

    def get_context_data(self) -> dict:
        return dict(
            dispatch_order=self,
            pdf_name=self.pdf_name,
            dispatch_line_items=self.dispatchlineitem_set.all(),
        )

    def pdf_name(self) -> str:
        return f"{self.dispatch_number} {self.dispatch_date}"

    # Note: PDF / HTML generation that referenced TEMPLATE is intentionally removed.


class DispatchLineItem(
    CreateUpdate,
):
    dispatch_order = ForeignKey(to="DispatchOrder", on_delete=PROTECT)
    item = ForeignKey(to="Item", on_delete=PROTECT, blank=True, null=True)
    unit = ForeignKey(
        UnitOfMeasurement, on_delete=PROTECT, blank=True, null=True
    )
    packaging = ForeignKey(
        to="Packaging", null=True, blank=True, on_delete=PROTECT
    )
#    bale = ForeignKey(to="Bale", null=True, blank=True, on_delete=PROTECT)
    quantity = PositiveFloatField(default=0)
    rate = FloatField(default=0)
    documents = ManyToManyField(to= "Document", blank=True)
    # sales_bill = ForeignKey(
    #     to="SalesBill",
    #     on_delete=PROTECT,
    #     blank=True,
    #     null=True,
    # )
    bill_quantity = PositiveFloatField(blank=True, null=True)
    bill_rate = PositiveFloatField(blank=True, null=True)
    # consumed_qr_code = ForeignKey(
    #     QRCode,
    #     on_delete=PROTECT,
    #     related_name="dispatch_line_item_consumed_qr_code",
    #     null=True,
    #     blank=True,
    # )
    is_gst_enabled = BooleanField(default=True)
    # Add only for traceability purposes
    # qr_code = OneToOneField(
    #     QRCode,
    #     on_delete=PROTECT,
    #     limit_choices_to=dict(inventory_type=QRCodeType.DISPATCH_LINE_ITEM),
    # )

    class Meta:
        constraints = [
            # UniqueConstraint(
            #     fields=["bale"],
            #     condition=Q(bale__isnull=False),
            #     name="dispatch_bale_partial_unique_25may2025",
            # ),
        ]

    @property
    def get_entity_id(self):
        if not self.pk:
            return None
        return self.dispatch_order.get_entity_id

    @property
    def has_adjustments(self):
        if not self.id:
            return False
        return self.dispatchlineitemadjustment_set.exists()

    @property
    def quantity_adjustment(self):
        if not self.id:
            return 0
        return sum(
            adjustment.quantity_adjustment
            for adjustment in self.dispatchlineitemadjustment_set.all()
        )

    @property
    def rate_adjustment(self):
        if not self.id:
            return 0
        return sum(
            adjustment.rate_adjustment
            for adjustment in self.dispatchlineitemadjustment_set.all()
        )

    @property
    def tax_group(self):
        return (
            self.item.inter_state_gst
            if self.dispatch_order.india_gst_segment
            == IndiaGstSegment.OUTSIDE_STATE
            else self.item.intra_state_gst
        )

    @property
    def tax_total(self):
        if not self.is_gst_enabled:
            return 0
        return 0 if self.is_rcm else self.tax_rate_calculation

    @property
    def tax_rate_calculation(self):
        tax_value = 0
        for tax in self.tax_group.taxes.all():
            tax_value += tax.rate * self.net_total
        return tax_value

    @property
    def post_tax_total(self):
        return self.tax_total + self.net_total

    @property
    def net_total(self):
        return self.base_quantity * self.rate

    @property
    def base_bill_net_quantity(self):
        return (
            (self.bill_net_quantity / self.unit.conversion_rate)
            if self.unit
            else self.bill_net_quantity
        )

    @property
    def base_quantity(self):
        return (
            (self.quantity / self.unit.conversion_rate)
            if self.unit
            else self.quantity
        )

    @property
    def rcm_total(self):
        return self.tax_rate_calculation if self.is_rcm else 0

    @property
    def is_rcm(self):
        return self.item.is_rcm_applicable

    @property
    def bill_total(self):
        return (
            self.bill_base_quantity * self.bill_rate
            if self.bill_base_quantity and self.bill_rate
            else 0
        )

    @property
    def bill_net_quantity(self):
        return (
            (self.bill_quantity - self.quantity_adjustment)
            if self.bill_quantity
            else 0
        )

    @property
    def bill_net_rate(self):
        return (self.bill_rate - self.rate_adjustment) if self.bill_rate else 0

    @property
    def bill_base_quantity(self):
        return (
            (self.bill_net_quantity / self.unit.conversion_rate)
            if self.unit and self.base_bill_net_quantity
            else self.bill_net_quantity
        )

    @property
    def bill_tax_rate_calculation(self):
        tax_value = 0
        for tax in self.tax_group.taxes.all():
            tax_value += tax.rate * self.bill_total
        return tax_value

    @property
    def bill_tax_total(self):
        return self.bill_tax_rate_calculation

    @property
    def bill_post_tax_total(self):
        return self.bill_tax_total + self.bill_total

    def __str__(self):
        return f"{self.item} / {self.dispatch_order}"

    def clean(self):
        if self.unit and self.unit.category != self.item.unit_category:
            raise ValidationError(
                {
                    "unit": [
                        "Cannot be in different category from the Item's unit."
                    ]
                }
            )

    def save(self, **kwargs):
        if not self.unit:
            self.unit = self.item.unit
        if self.sales_bill:
            self.bill_quantity = (
                self.bill_quantity if self.bill_quantity else self.quantity
            )
            self.bill_rate = self.bill_rate if self.bill_rate else self.rate
        else:
            self.bill_quantity = None
            self.bill_rate = None

        if self.bill_quantity and self.bill_quantity > self.quantity:
            raise SerializerValidationError(
                {
                    "bill_quantity": "This cannot be greater than quantity in the Goods Receipt Note."
                }
            )
            if self.id:
                self.dispatchlineitemadjustment_set.all().delete()
        # if not self.qr_code_id:
        #     qr_code = QRCode(
        #         inventory_type=QRCodeType.DISPATCH_LINE_ITEM,
        #         tenant=self.dispatch_order.tenant,
        #         code=str(self.uid),
        #     )
        #     qr_code.save()
        #     self.qr_code = qr_code
        super(DispatchLineItem, self).save(**kwargs)


class EntityBankAccount(CreateUpdateStatus, AbstractBankAccount):
    entity = ForeignKey(to="Entity", on_delete=PROTECT)
    currency = ForeignKey(
        to="Currency",
        on_delete=PROTECT,
        related_name="currency_entity_bank_account",
    )
    intermediate_bank_currency = ForeignKey(
        to="Currency",
        on_delete=PROTECT,
        related_name="intermediate_bank_currency_entity_bank_account",
        blank=True,
        null=True,
    )
    upi_currency = ForeignKey(
        to="Currency",
        on_delete=PROTECT,
        related_name="upi_currency_entity_bank_account",
        blank=True,
        null=True,
    )

    @property
    def account_type_display(self):
        return self.account_type.name

    def save(self, **kwargs):
        self.full_clean()
        super(EntityBankAccount, self).save(**kwargs)



class SalesOrder(CreateUpdate, ArchiveField, ApprovalField):
    TEMPLATE = "common/transaction/salesorder.html"
    tenant = ForeignKey(
        Tenant, on_delete=PROTECT, limit_choices_to=limit_to_active
    )
    sales_order_number = CharField(max_length=128)
    prefixed_sales_order_number = CharField(
        max_length=32, blank=True, default=""
    )
    sales_order_date = DateField()
    trade_partner_order_number = CharField(max_length=128)
    trade_partner_order_date = DateField()
    warehouse = ForeignKey(
        Warehouse, on_delete=PROTECT, limit_choices_to=limit_to_active
    )
    trade_partner = ForeignKey(
        TradePartner, on_delete=PROTECT, limit_choices_to=limit_to_active
    )
    billing_address = ForeignKey(
        TradePartnerAddress,
        on_delete=PROTECT,
        related_name="sales_order_billing_address",
        limit_choices_to={**limit_to_active(), "is_billing": True},
    )
    shipping_address = ForeignKey(
        TradePartnerAddress,
        on_delete=PROTECT,
        related_name="sales_order_shipping_address",
        limit_choices_to={**limit_to_active(), "is_shipping": True},
    )
    trade_partner_bank_account = ForeignKey(
        TradePartnerBankAccount,
        on_delete=PROTECT,
        limit_choices_to=limit_to_active,
        null=True,
        blank=True,
    )
    entity_bank_account = ForeignKey(
        EntityBankAccount,
        on_delete=PROTECT,
        limit_choices_to=limit_to_active,
        null=True,
        blank=True,
    )
    other_cost = PositiveFloatField(default=0)
    transport_cost = PositiveFloatField(default=0)
    tcs_percent = PercentField(default=0)
    tds_percent = PercentField(default=0)
    remarks = TextField(blank=True)
    sales_term_and_conditions = ManyToManyField(
        TermAndCondition,
        related_name="sales_order_sales_term_and_conditions",
    )
    payment_term = ForeignKey(
        DynamicEnum,
        on_delete=PROTECT,
        limit_choices_to={"enum": DynamicEnumType.PAYMENT_TERM},
        blank=True,
        null=True,
    )
    payment_term_and_conditions = ManyToManyField(
        TermAndCondition,
        related_name="sales_order_payment_term_and_conditions",
    )
    documents = ManyToManyField(Document, blank=True)
    # qr_code = OneToOneField(
    #     QRCode,
    #     on_delete=PROTECT,
    #     limit_choices_to=dict(inventory_type=QRCodeType.SALES_ORDER),
    # )
    approved_documents = ManyToManyField(
        Document, related_name="sales_order_approved_documents", blank=True
    )

    def allow_create(self, user):
        entity_obj = EntityUserAccess.objects.filter(
            user=user,
            entity=self.trade_partner.entity,
            permissions__codename="create_salesorder",
        ).first()
        return True if entity_obj else False

    @property
    def get_entity_id(self):
        if not self.pk:
            return None
        return self.warehouse.center.entity_id

    def validate_unique(self, exclude: Collection[str] | None = ...) -> None:
        if self.pk is None:
            qs = SalesOrder.objects.filter(
                sales_order_number=self.sales_order_number, tenant=self.tenant
            )
            if qs.exists():
                raise ValidationError(
                    {"sales_order_number": "Sales order number already exists"}
                )

        return super().validate_unique(exclude)

    @property
    def has_usable_line_items_for_work_order(self):
        usable = False
        line_item: SalesOrderLineItem
        for line_item in self.salesorderlineitem_set.all():
            if not line_item.is_used_in_work_order:
                usable = True
                break
        return usable

    @property
    def sales_terms(self):
        return "\n".join(
            [t.terms for t in self.sales_term_and_conditions.all()]
        )

    # @property
    # def payment_terms(self):
    #     return "\n".join(
    #         [t.terms for t in self.payment_term_and_conditions.all()]
    #     )

    @property
    def hsn_post_tax_total(self):
        return sum(
            [x.post_tax_total for x in self.salesorderlineitem_set.all()]
        )

    @property
    def rcm_post_tax_total(self):
        return sum(
            [
                x.post_tax_total
                for x in self.salesorderlineitem_set.filter(is_rcm=True)
            ]
        )

    @property
    def hsn_tax_total(self):
        return sum([x.tax_total for x in self.salesorderlineitem_set.all()])

    @property
    def rcm_tax_total(self):
        return sum(
            [
                x.tax_total
                for x in self.salesorderlineitem_set.filter(is_rcm=True)
            ]
        )

    @property
    def hsn_rate_total(self):
        return sum([x.rate for x in self.salesorderlineitem_set.all()])

    @property
    def rcm_rate_total(self):
        return sum(
            [x.rate for x in self.salesorderlineitem_set.filter(is_rcm=True)]
        )

    @property
    def gross_total_invoice(self):
        return self.item_total + self.other_cost + self.transport_cost

    @property
    def total_invoice(self):
        return int(self.gross_total_invoice)

    @property
    def round_off(self):
        return self.gross_total_invoice % 1

    @property
    def total_tcs(self):
        return self.total_invoice * self.tcs_percent

    @property
    def total_post_tcs(self):
        return self.total_tcs + self.total_invoice

    @property
    def total_tds(self):
        return self.total_post_tcs * self.tds_percent

    @property
    def total_post_tds(self):
        return self.total_post_tcs - self.total_tds

    @property
    def india_gst_segment(self):
        return (
            IndiaGstSegment.WITHIN_STATE
            if self.billing_address
            and self.billing_address.state.lower()
            == self.warehouse.center.state.lower()
            else IndiaGstSegment.OUTSIDE_STATE
        )

    @property
    def india_union_territory(self):
        return (
            self.india_gst_segment == IndiaGstSegment.WITHIN_STATE
            and self.billing_address.is_india_union_territory
        )

    @property
    def payable_rcm(self):
        return sum(
            line_item.rcm_total
            for line_item in self.salesorderlineitem_set.all()
        )

    @property
    def total_quantity(self):
        return self.salesorderlineitem_set.aggregate(
            total_quantity=Sum("quantity", default=0)
        ).get("total_quantity", 0)

    @property
    def total_item_quantity(self):
        sales_total = []
        for category in serialize(UnitCategory):
            unit = UnitOfMeasurement.objects.filter(
                category=category["value"], is_primary_unit=True
            ).first()
            quantity = (
                self.salesorderlineitem_set.filter(
                    unit__category=category["value"]
                )
                .aggregate(total_quantity=Sum("quantity", default=0))
                .get("total_quantity", 0)
            )
            if quantity and unit:
                sales_total.append(
                    dict(
                        quantity=quantity,
                        unit=unit.unique_quantity_code if unit else "",
                        heading=f"{category['name']} Total",
                    )
                )
        return sales_total

    @property
    def total_rcm_item_quantity(self):
        rcm_sales_total = []
        for category in serialize(UnitCategory):
            unit = UnitOfMeasurement.objects.filter(
                category=category["value"], is_primary_unit=True
            ).first()
            quantity = (
                self.salesorderlineitem_set.filter(
                    unit__category=category["value"], is_rcm=True
                )
                .aggregate(total_quantity=Sum("quantity", default=0))
                .get("total_quantity", 0)
            )
            if quantity and unit:
                rcm_sales_total.append(
                    dict(
                        quantity=quantity,
                        unit=unit.unique_quantity_code if unit else "",
                        heading=f"{category['name']} RCM Total",
                    )
                )
        return rcm_sales_total

    def __str__(self) -> str:
        return f"{self.sales_order_number} / {self.trade_partner}"

    def clean(self) -> None:
        validation_dict = {}
        if tenant := self.tenant:
            if self.trade_partner.tenant != tenant:
                validation_dict["trade_partner"] = "No trade partner found."
            if self.warehouse.tenant != tenant:
                validation_dict["warehouse"] = "No warehouse found."
        if self.trade_partner:
            if (
                self.billing_address
                and self.trade_partner != self.billing_address.trade_partner
            ):
                validation_dict[
                    "billing_address"
                ] = "This billing address does not belong to this trade partner."
            if (
                self.shipping_address
                and self.trade_partner != self.shipping_address.trade_partner
            ):
                validation_dict[
                    "shipping_address"
                ] = "This shipping address does not belong to this trade partner."
        # if (
        #     self.bank_account
        #     and self.warehouse
        #     and self.warehouse.center.entity != self.bank_account.entity
        # ):
        #     validation_dict[
        #         "bank_account"
        #     ] = "This bank account does not belong to this warehouse's entity."
        if validation_dict:
            raise ValidationError(validation_dict)
        return super(SalesOrder, self).clean()

    def save(self, **kwargs):
        with transaction.atomic():
            # if not self.sales_order_number:
            #     self.sales_order_number = create_code(
            #         QRCodeType.SALES_ORDER, self.sales_order_date
            #     )
            if not self.prefixed_sales_order_number:
                entity = self.trade_partner.entity
                serial_master = SerialMaster.objects.filter(
                    entity=entity,
                    document_type=DocumentType.SALES_ORDER,
                ).first()
                prefix = (
                    ""
                    if not serial_master
                    else serial_master.generate_prefix(self.sales_order_date)
                )
                counter: Counter = Counter.objects.filter(
                    tenant=self.tenant,
                    document_type=DocumentType.SALES_ORDER,
                ).first()
                if not counter:
                    raise ValueError(
                        "Counter instance doesn't exist. Fix this"
                    )
                suffix = counter.generate_suffix()
                self.prefixed_sales_order_number = (
                    f"{prefix}-{suffix}" if prefix else suffix
                )
            self.validate_unique(None)
            # if not self.qr_code_id:
            #     qr_code = QRCode(
            #         inventory_type=QRCodeType.SALES_ORDER,
            #         tenant=self.tenant,
            #         code=self.sales_order_number,
            #     )
            #     qr_code.save()
            #     self.qr_code = qr_code
            # self.full_clean()
            super(SalesOrder, self).save(**kwargs)

    def get_context_data(self) -> dict:
        return dict(
            sales_order=self,
            pdf_name=self.pdf_name,
            sales_line_items=self.salesorderlineitem_set.all(),
        )

    def pdf_name(self) -> str:
        return f"{self.sales_order_number} {self.sales_order_date}"

    # def create_for_sending(self, request):
    #     ctx = self.get_context_data()
    #     html_string = render_to_string(self.TEMPLATE, ctx)
    #     template = django_engine.from_string(html_string)
    #     markup = template.render(ctx)

    #     css = settings.BASE_DIR / "global_static" / "css" / "transaction.css"

    #     return HTML(
    #         string=markup, base_url=request.build_absolute_uri()
    #     ).write_pdf(stylesheets=[CSS(css)])


class Process(CreateUpdateStatus, ArchiveField):
    tenant = ForeignKey(
        Tenant, on_delete=PROTECT, limit_choices_to=limit_to_active
    )
    name = CharField(max_length=255)
    description = TextField(blank=True)

    def __str__(self):
        return self.name

 
class SalesOrderLineItem(CreateUpdate):
    TRACEABILITY_TEMPLATE = "common/transaction/traceability_report.html"
    sales_order = ForeignKey(
        SalesOrder, on_delete=PROTECT, limit_choices_to=limit_to_unarchived
    )
    item = ForeignKey(
        Item, on_delete=PROTECT, limit_choices_to=limit_to_active
    )
    quantity = PositiveFloatField()
    unit = ForeignKey(
        UnitOfMeasurement, on_delete=PROTECT, limit_choices_to=limit_to_active
    )
    rate = PositiveFloatField()
    packaging = ForeignKey(
        Packaging,
        null=True,
        blank=True,
        on_delete=PROTECT,
        limit_choices_to=limit_to_active,
    )
    expected_delivery_date = DateField(
        validators=[future_date_check], blank=True, null=True
    )
    dispatch_mode = CharField(max_length=8, choices=DispatchMode.choices)
    is_rcm = BooleanField(default=False)
    description = TextField(blank=True)
    process = ForeignKey(
        Process,
        on_delete=PROTECT,
        limit_choices_to=limit_to_active,
        blank=True,
        null=True,
    )
    process_instructions = TextField(blank=True)
    process_documents = ManyToManyField(
        to="Document",
        related_name="sales_order_line_item_process_documents",
        blank=True,
    )
    qc_documents = ManyToManyField(
        to="Document",
        related_name="sales_order_line_item_qc_documents",
        blank=True,
    )

    def allow_create(self, user):
        entity_obj = EntityUserAccess.objects.filter(
            user=user,
            entity=self.sales_order.trade_partner.entity,
            permissions__codename="create_salesorderlineitem",
        ).first()
        return True if entity_obj else False

    @property
    def has_matching_dispatch_line_item(self):
        return DispatchLineItem.objects.filter(
            Q(dispatch_order__sales_order=self.sales_order)
            & Q(item__id=self.item.id)
        ).exists()

    @property
    def get_entity_id(self):
        if not self.pk:
            return None
        return self.sales_order.get_entity_id

    @property
    def is_used_in_work_order(self):
        return hasattr(self, "workorder") and self.workorder is not None

    @property
    def dispatch_mode_display(self):
        return self.get_dispatch_mode_display()

    @property
    def tax_group(self):
        return (
            self.item.inter_state_gst
            if self.sales_order.india_gst_segment
            == IndiaGstSegment.OUTSIDE_STATE
            else self.item.intra_state_gst
        )

    @property
    def tax_total(self):
        return 0 if self.is_rcm else self.tax_rate_calculation

    @property
    def tax_rate_calculation(self):
        tax_value = 0
        for tax in self.tax_group.taxes.all():
            tax_value += tax.rate * self.gross_total
        return tax_value

    @property
    def post_tax_total(self):
        return self.tax_total + self.gross_total

    @property
    def gross_total(self):
        return self.rate * self.base_quantity

    @property
    def base_quantity(self):
        return (
            (self.quantity / self.unit.conversion_rate)
            if self.unit
            else self.quantity
        )

    @property
    def needs_rcm(self):
        partner_has_gst = self.sales_order.billing_address.gstin
        center_has_gst = self.sales_order.warehouse.center.gstin
        item_needs_rcm = self.item.is_rcm_applicable
        return item_needs_rcm and center_has_gst and not partner_has_gst

    @property
    def rcm_total(self):
        return self.tax_rate_calculation if self.is_rcm else 0

    def pdf_name(self) -> str:
        return f"{self.sales_order.sales_order_number}-{self.item.name}"

    def __str__(self):
        return f"{self.item} / {self.sales_order}"

    def clean(self):
        validation_dict = {}
        if tenant := self.sales_order.tenant:
            if self.item and self.item.tenant != tenant:
                validation_dict["item"] = "No item found."
            if self.packaging and self.packaging.tenant != tenant:
                validation_dict["packaging"] = "No packaging found."
            if self.process and self.process.tenant != tenant:
                validation_dict["process"] = "No process found."

