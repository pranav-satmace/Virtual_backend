import uuid
from datetime import timedelta
from django.contrib.auth.models import User

from django.core.validators import (
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
)
import random
import string

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
   
)
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

from django.db.models.signals import post_save
from django.dispatch import receiver
import re
from django.contrib.postgres.indexes import GinIndex  # GinIndex

from django.db import models

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
from .taxonomies import DynamicEnumType,UnitCategory,  TaxType,TradePartnerType, GSTTreatment
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


# Simplified enums
class UserAccountType:
    USER_ACCOUNT = "user"
    ADMIN_ACCOUNT = "admin"
    choices = [(USER_ACCOUNT, "User"), (ADMIN_ACCOUNT, "Admin")]

class UserLocale:
    EN_IN = "en_IN"
    EN_US = "en_US"
    choices = [(EN_IN, "English (India)"), (EN_US, "English (US)")]


# Create your models here.

class UserProfile(Model):
    
    uid = UUIDField(default=uuid.uuid4, unique=True)
    tenant = CharField(max_length=255)
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
