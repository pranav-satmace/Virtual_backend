import uuid
from datetime import timedelta
from django.contrib.auth.models import User

from django.core.validators import (
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
)
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
)


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
#from .models import Collection
from django.contrib.postgres.search import SearchVector
from .taxonomies import DynamicEnumType
#from .taxonomies import DynamicEnum
from django.db.utils import IntegrityError
from typing import Collection

from .custom_fields import (
    GSTField,
    PercentField,
    PositiveFloatField,
    UpperCharField,
)
# External/internal helpers (replace with your logic or leave commented)
# from common.communications import safe_send_email
# from common.model_helpers import limit_to_active, random_pin
# from common.taxonomies import DynamicEnumType, UserAccountType, UserLocale

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
        Tenant, on_delete=PROTECT
        #, limit_choices_to=limit_to_active
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
        Tenant, on_delete=PROTECT, limit_choices_to=limit_to_active
    )

    def __str__(self):
        return f"{self.document_name} / {self.tenant}"

class EntityUserAccess(models.Model):
    uid = UUIDField(default=uuid.uuid4)
    entity = ForeignKey(to=Entity, on_delete=PROTECT)
    user = ForeignKey(to=User, on_delete=PROTECT)
    permissions = ManyToManyField(to=Permission, blank=True)
    groups = ManyToManyField(to=Group, blank=True)

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
    start_date = DateField(default=timezone.now)
    end_date = DateField(default=timezone.now)
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
    factory_license_date = DateField(
        validators=[past_date_check],
        default=timezone.now,
    )
    # factory_license_expiry_date = DateField(
    #     default=lambda: timezone.now().date() + timedelta(days=365*100)
    # )

    factory_license_expiry_date = DateField(
    default=timezone.now().date() + timedelta(days=365*100)
    )
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
    tally_mapping_name = CharField(max_length=255, blank=True, default="")
    external_ids = JSONField(blank=True, default=dict)
    error_message = JSONField(blank=True, default=dict)

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


class CenterParticular(Particular):
    center = ForeignKey(to="Center", on_delete=PROTECT)

