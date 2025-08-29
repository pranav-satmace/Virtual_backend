from django.contrib.auth.models import User
from rest_framework import serializers
from .models import UserProfile
from .models import ReportingTenant
from .models import Tenant
from .models import Address, Currency, Entity
from .models import Center, Warehouse
from datetime import datetime
from .models import Item

from phonenumber_field.serializerfields import PhoneNumberField
from django_countries.serializer_fields import CountryField

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
            'signature', 'gender', 'department', 'designation', 'locale'
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

    # def create(self, validated_data):
    #     if validated_data.get("places_api_json") is None:
    #         validated_data["places_api_json"] = {}
    #     return super().create(validated_data)

class EntitySerializer(serializers.ModelSerializer):
    # registered_address = AddressSerializer(read_only=True)
    registered_address = AddressSerializer()
    # registered_address = AddressSerializer(required=False)
    # registered_address = AddressSerializer()
    currency = CurrencySerializer(read_only=True)

    # registered_address_id = serializers.PrimaryKeyRelatedField(
    #     queryset=Address.objects.all(),
    #     source="registered_address",
    #     write_only=True,
    #     required=False,
    #     allow_null=True
    # )

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
            # "registered_address_id",
            "currency",
            "currency_id",
            "short_name",
            "logo",
            "contact_name",
            "bank_details",
            # "is_active",  # Fix: take from CreateUpdateStatus
        ]
        read_only_fields = ["short_name", "is_archived"]

    def create(self, validated_data):
        # Pop nested fields
        registered_address_data = validated_data.pop("registered_address", None)
        # if registered_address_data:
        #     if registered_address_data.get("places_api_json") is None:
        #         registered_address_data["places_api_json"] = {}
        #     address = Address.objects.create(**registered_address_data)

        currency = validated_data.pop("currency", None)

        # Create Address instance if data exists
        address = None
        if registered_address_data:
            address = Address.objects.create(**registered_address_data)

        # Auto-create ReportingTenant + Tenant
        entity_name = validated_data.get("name")
        prefix = _prefix_from_name(entity_name)

        rt = ReportingTenant.objects.create(
            name=entity_name,
            status="Active",
            short_code=_next_running(ReportingTenant, prefix)
        )

        tenant = Tenant.objects.create(
            reporting_tenant=rt,
            name=entity_name,
            status="Active",
            short_code=_next_running(Tenant, prefix)
        )

        # Auto-generate short_name for Entity
        short_name = _next_running(Entity, prefix, field="short_name")

        # Save Entity
        entity = Entity.objects.create(
            **validated_data,
            registered_address=address,  # assign created Address
            currency=currency,
            short_name=short_name,
            tenant=tenant
        )

        return entity

class CenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Center
        fields = "__all__"
        read_only_fields = ["short_name", "is_archived", "is_active", "code"]




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