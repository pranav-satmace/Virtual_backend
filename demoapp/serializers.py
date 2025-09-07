from django.contrib.auth.models import User
from rest_framework import serializers
from .models import UserProfile
from .models import ReportingTenant
from .models import Tenant
from .models import Address, Currency, Entity
from .models import Center, Warehouse
from datetime import datetime
from .models import Item
from .models import TradePartner, TradePartnerAddress, TradePartnerBankAccount
from .models import GoodsReceiptNote, GrnLineItem, Packaging, Vehicle, Driver, SerialMaster, Counter,DispatchOrder

from phonenumber_field.serializerfields import PhoneNumberField
from django_countries.serializer_fields import CountryField
from django.utils.timezone import now

from .utils import _prefix_from_name, _next_running  


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)  # accept password but don't show it in response

    class Meta:
        model = User
        fields = ["id", "username", "email", "is_staff", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)  # hash the password
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


# UserProfile serializer
class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()  # Nested user
    country = CountryField()  # Serializes country to string
    phone_number = PhoneNumberField(required=False, allow_null=True)
    whatsapp_number = PhoneNumberField(required=False, allow_null=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = UserProfile
        fields = [
            'uid', 'tenant', 'user', 'country', 'account_type',
            'phone_number', 'whatsapp_number', 'profile_picture',
            'signature', 'gender',
            'department', 'designation', 'locale'
        ]

    # Create nested user + profile
    def create(self, validated_data):
        user_data = validated_data.pop("user")
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        profile = UserProfile.objects.create(user=user, **validated_data)
        return profile

    # Update nested user + profile
    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", None)
        if user_data:
            user_serializer = UserSerializer(
                instance=instance.user, data=user_data, partial=True
            )
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    


class TenantSetupSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)

    def create(self, validated_data):
        name = validated_data['name']
        # generate short codes + save ReportingTenant and Tenant
        rt = ReportingTenant.objects.create(
            name=name,
            status="Active",
            short_code=_next_running(ReportingTenant, _prefix_from_name(name))
        )
        tenant = Tenant.objects.create(
            reporting_tenant=rt,
            name=name,
            status="Active",
            short_code=_next_running(Tenant, _prefix_from_name(name))
        )
        return {"reporting_tenant": rt, "tenant": tenant}

    def to_representation(self, instance):
        return {
            "reporting_tenant": {
                "id": instance["reporting_tenant"].id,
                "name": instance["reporting_tenant"].name,
                "short_code": instance["reporting_tenant"].short_code,
            },
            "tenant": {
                "id": instance["tenant"].id,
                "name": instance["tenant"].name,
                "short_code": instance["tenant"].short_code,
            }
        }


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = "__all__"
#        read_only_fields = ["is_active", "is_archived"]

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"
        read_only_fields = ["tenant"]  # 👈 tenant user se nahi aayega


    # def create(self, validated_data):
    #     if validated_data.get("places_api_json") is None:
    #         validated_data["places_api_json"] = {}
    #     return super().create(validated_data)
class EntitySerializer(serializers.ModelSerializer):
    registered_address = AddressSerializer()
    currency = CurrencySerializer(read_only=True)
    currency_id = serializers.PrimaryKeyRelatedField(
        queryset=Currency.objects.all(),
        source="currency",
        write_only=True
    )

    class Meta:
        model = Entity
        fields = [
            "id",
            "name",
            "registered_address",
            "currency",
            "currency_id",
            "short_name",
            "logo",
            "contact_name",
            "bank_details",
        ]
        read_only_fields = ["short_name", "tenant", "is_archived"]
 
    def create(self, validated_data):   # ✅ ab sahi jagah indent
        request = self.context.get("request")
        user = request.user
        profile = user.userprofile

        # Pop nested address
        registered_address_data = validated_data.pop("registered_address", None)
        currency = validated_data.pop("currency", None)

        address = None
        if registered_address_data:
            address = Address.objects.create(
                **registered_address_data,
                tenant=profile.tenant   # initially temp tenant
            )

        entity_name = validated_data.get("name")
        prefix = _prefix_from_name(entity_name)
        short_name = _next_running(Entity, prefix, field="short_name")

        # 🔥 If profile has only TEMP Tenant → create new ReportingTenant + Tenant
        if profile.tenant and profile.tenant.name == "TEMP Tenant":
            rt = ReportingTenant.objects.create(
                name=entity_name,
                status="Active",
                short_code=_next_running(ReportingTenant, prefix),
            )
            tenant = Tenant.objects.create(
                reporting_tenant=rt,
                name=entity_name,
                status="Active",
                short_code=_next_running(Tenant, prefix),
            )

            # 👇 update userprofile to actual tenant
            profile.tenant = tenant
            profile.save()
        else:
            # already has a proper tenant
            tenant = profile.tenant

        entity = Entity.objects.create(
            **validated_data,
            registered_address=address,
            currency=currency,
            short_name=short_name,
            tenant=tenant
        )

        return entity

# class EntitySerializer(serializers.ModelSerializer):
#     # registered_address = AddressSerializer(read_only=True)
#     registered_address = AddressSerializer()
#     # registered_address = AddressSerializer(required=False)
#     # registered_address = AddressSerializer()
#     currency = CurrencySerializer(read_only=True)

#     # registered_address_id = serializers.PrimaryKeyRelatedField(
#     #     queryset=Address.objects.all(),
#     #     source="registered_address",
#     #     write_only=True,
#     #     required=False,
#     #     allow_null=True
#     # )

#     currency_id = serializers.PrimaryKeyRelatedField(
#         queryset=Currency.objects.all(),
#         source="currency",
#         write_only=True
#     )

#     class Meta:
#         model = Entity
#         fields = [
#             "id",
#             "name",
#             "registered_address",
#             # "registered_address_id",
#             "currency",
#             "currency_id",
#             "short_name",
#             "logo",
#             "contact_name",
#             "bank_details",
#             # "is_active",  # Fix: take from CreateUpdateStatus
#         ]

#         read_only_fields = ["short_name","tenant", "is_archived"]

#     def create(self, validated_data):
#         # Pop nested fields
#         registered_address_data = validated_data.pop("registered_address", None)
#         # if registered_address_data:
#         #     if registered_address_data.get("places_api_json") is None:
#         #         registered_address_data["places_api_json"] = {}
#         #     address = Address.objects.create(**registered_address_data)

#         currency = validated_data.pop("currency", None)

#         # Create Address instance if data exists
#         address = None
#         if registered_address_data:
#             address = Address.objects.create(**registered_address_data)

#         # Auto-create ReportingTenant + Tenant
#         entity_name = validated_data.get("name")
#         prefix = _prefix_from_name(entity_name)

#         rt = ReportingTenant.objects.create(
#             name=entity_name,
#             status="Active",
#             short_code=_next_running(ReportingTenant, prefix)
#         )

#         tenant = Tenant.objects.create(
#             reporting_tenant=rt,
#             name=entity_name,
#             status="Active",
#             short_code=_next_running(Tenant, prefix)
#         )

#         # Auto-generate short_name for Entity
#         short_name = _next_running(Entity, prefix, field="short_name")

#         # Save Entity
#         entity = Entity.objects.create(
#             **validated_data,
#             registered_address=address,  # assign created Address
#             currency=currency,
#             short_name=short_name,
#             tenant=tenant
#         )

#         return entity

# class CenterSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Center
#         fields = "__all__"
#         read_only_fields = ["short_name", "is_archived", "is_active", "code"]

# class CenterSerializer(serializers.ModelSerializer):
#     tenant_name = serializers.CharField(source="tenant.name", read_only=True)
#     entity_name = serializers.CharField(source="entity.name", read_only=True)
#     center_address = serializers.SerializerMethodField()

#     class Meta:
#         model = Center
#         fields = "__all__"
#         read_only_fields = [
#             "short_name",
#             "is_archived",
#             "is_active",
#             "code",
#             "tenant",
#             "entity",
#             "center_address",
#         ]

#     def get_center_address(self, obj):
#         if obj.center_address:
#             return {
#                 "id": obj.center_address.id,
#                 "line1": obj.center_address.address_line,
#                 "city": obj.center_address.city,
#                 "state": obj.center_address.state,
#                 "country": obj.center_address.country,
#                 "postal_code": obj.center_address.postal_code,
#             }
#         return None

#     def create(self, validated_data):
#         user = self.context["request"].user
#         tenant = user.userprofile.tenant

#         # ✅ first entity of this tenant (or choose based on request if needed)
#         entity = Entity.objects.filter(tenant=tenant).first()

#         if not entity:
#             raise serializers.ValidationError("No entity found for this tenant.")

#         # ✅ center address same as entity.registered_address
#         validated_data["tenant"] = tenant
#         validated_data["entity"] = entity
#         validated_data["center_address"] = entity.registered_address

#         return super().create(validated_data)

#     def update(self, instance, validated_data):
#         user = self.context["request"].user
#         tenant = user.userprofile.tenant
#         entity = Entity.objects.filter(tenant=tenant).first()

#         validated_data["tenant"] = tenant
#         validated_data["entity"] = entity
#         validated_data["center_address"] = entity.registered_address

#         return super().update(instance, validated_data)

class CenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Center
        fields = "__all__"
        read_only_fields = [
            "short_name",
            "is_archived",
            "is_active",
            "code",
            "tenant",
            "center_address",
            "entity",
        ]
class CenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Center
        fields = "__all__"
        read_only_fields = [
            "short_name",
            "is_archived",
            "is_active",
            "code",
            "tenant",
            "center_address",
            "entity",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        profile = user.userprofile

        entity = Entity.objects.filter(tenant=profile.tenant).first()
        if not entity:
            raise serializers.ValidationError(
                "No entity found for this user. Please create an entity first."
            )

        validated_data["entity"] = entity
        validated_data["tenant"] = entity.tenant
        validated_data["center_address"] = entity.registered_address

        return super().create(validated_data)


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id", "tenant", "center", "name", "short_name"]

    # Optional: prevent passing name/short_name manually if you want auto
    def create(self, validated_data):
        return Warehouse.objects.create(**validated_data)



class ItemSerializer(serializers.ModelSerializer):
    # type_display = serializers.CharField(source='type.name', read_only=True)
    # unit_display = serializers.CharField(source='unit.name', read_only=True)
    # inter_state_gst_display = serializers.CharField(source='inter_state_gst.name', read_only=True)
    # intra_state_gst_display = serializers.CharField(source='intra_state_gst.name', read_only=True)
    # intra_ut_gst_display = serializers.CharField(source='intra_ut_gst.name', read_only=True)

    class Meta:
        model = Item
        fields = "__all__"
        extra_kwargs = {
            "code": {"read_only": True}
        }
        # fields = [
            # "id",
            # "name",
            # "type",
            # "type_display",
            # "image",
            # "hsn_or_sac_code",
            # "is_rcm_applicable",
            # "is_epr_applicable",
            # "unit",
            # "unit_display",
            # "inter_state_gst",
            # "inter_state_gst_display",
            # "intra_state_gst",
            # "intra_state_gst_display",
            # "intra_ut_gst",
            # "intra_ut_gst_display",
            # "created_at",
            # "updated_at",
            # "status",
        # ]


class TradePartnerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradePartnerAddress
        fields = [
            "id",
            "address_line",   # from AbstractAddress
            "postal_code",
            "city",
            "state",
            "country",
            "latitude",
            "longitude",
            "gstin",
            "gst_effective_date",
            "is_billing",
            "is_shipping",
    #        "status",
        ]


class TradePartnerBankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradePartnerBankAccount
        fields = [
            "id",
            "account_number",
            "ifsc_code",      # from AbstractBankAccount
            "bank_name",      # from AbstractBankAccount
            "currency",
            "account_type"
#            "status",
        ]


class TradePartnerSerializer(serializers.ModelSerializer):
    addresses = TradePartnerAddressSerializer(many=True, required=False)
    bank_accounts = TradePartnerBankAccountSerializer(many=True, required=False)

    class Meta:
        model = TradePartner
        fields =  [
            "id",
            "name",
            "phone_number",
            # "status",
            "is_vendor",
            "is_customer",
            "display_picture",
            "tax_number",
            "tax_number_effective_date",
            "transaction_currency",
            "entity",
            "addresses",
            "bank_accounts",
            "tenant",
            #"short_name",
        ]
        # extra_kwargs = {
        #     "short_name": {"required": False, "read_only": True},
        # }
        # # '__all__'

        read_only_fields = ["short_name"]

    def create(self, validated_data):
        addresses_data = validated_data.pop("addresses", [])
        bank_accounts_data = validated_data.pop("bank_accounts", [])
        trade_partner = TradePartner.objects.create(**validated_data)

        for addr in addresses_data:
            TradePartnerAddress.objects.create(trade_partner=trade_partner, **addr)

        for bank in bank_accounts_data:
            TradePartnerBankAccount.objects.create(trade_partner=trade_partner, **bank)

        return trade_partner

    def update(self, instance, validated_data):
        addresses_data = validated_data.pop("addresses", [])
        bank_accounts_data = validated_data.pop("bank_accounts", [])

        # update main fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # replace addresses
        if addresses_data:
            instance.tradepartneraddress_set.all().delete()
            for addr in addresses_data:
                TradePartnerAddress.objects.create(trade_partner=instance, **addr)

        # replace bank accounts
        if bank_accounts_data:
            instance.tradepartnerbankaccount_set.all().delete()
            for bank in bank_accounts_data:
                TradePartnerBankAccount.objects.create(trade_partner=instance, **bank)

        return instance


class GoodsReceiptNoteSerializer(serializers.ModelSerializer):
    trade_partner_name = serializers.CharField(source="trade_partner.name", read_only=True)
    billing_address_text = serializers.CharField(source="billing_address.address_line", read_only=True)
    shipping_address_text = serializers.CharField(source="shipping_address.address_line", read_only=True)
    grn_number = serializers.CharField(required=False, allow_blank=True)
    prefixed_grn_number = serializers.CharField(required=False, allow_blank=True)
    grn_date = serializers.DateField(required=False)

    class Meta:
        model = GoodsReceiptNote
        fields = [
       #     "id",
            "grn_number",                 
            "prefixed_grn_number",        
            "grn_date",                   # GRN Date
            "trade_partner",              # FK
            "trade_partner_name",         # Human-readable
            "billing_address",
            "billing_address_text",
            "shipping_address",
            "shipping_address_text",
            "warehouse",
            "status",
            "tenant",
            "transaction_currency"
           
        ]

    def validate_grn_date(self, value):
        """GRN Date cannot be in future"""
        from django.utils.timezone import now
        if value > now().date():
            raise serializers.ValidationError("GRN Date cannot be in the future.")
        return value

    def create(self, validated_data):
        # """Automatically assign tenant from request user"""
        # request = self.context.get("request")
        # if request and hasattr(request.user, "tenant"):
        #     validated_data["tenant"] = request.user.tenant
        # else:
        #     raise serializers.ValidationError("Tenant is required.")
        return GoodsReceiptNote.objects.create(**validated_data)


class GrnLineItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name", read_only=True)
    source_name = serializers.CharField(source="source.name", read_only=True)

    class Meta:
        model = GrnLineItem
        fields = [
            "id",
            "goods_receipt_note",  # FK to GRN Header
            "item",
            "item_name",
            "quantity",            # Item Quantity
            "rate",                # Item Value
            "documents",           # Material Photos
            "source",              # Material Source (DynamicEnum)
            "source_name",
            
        ]

    # def create(self, validated_data):
    #     line_item = GrnLineItem.objects.create(**validated_data)
    #     return line_item

    def create(self, validated_data):
        documents = validated_data.pop("documents", [])
        line_item = GrnLineItem.objects.create(**validated_data)
        if documents:
            line_item.documents.set(documents)
        return line_item


class DispatchOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model= DispatchOrder
        fields= [
            "id",
            "dispatch_number",
            "prefixed_dispatch_number",
            "dispatch_date",
            "tenant",
            "warehouse",
            "trade_partner",
            "billing_address",
            "shipping_address",
            "dispatch_mode",
          
        ]
    def validate_dispatch_date(self, value):
        """Dispatch Date cannot be in future"""
        from django.utils.timezone import now
        if value > now().date():
            raise serializers.ValidationError("Dispatch  Date cannot be in the future.")
        return value
    def create(self, validated_data):
        return DispatchOrder.objects.create(**validated_data)
