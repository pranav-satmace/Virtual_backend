from django.shortcuts import render

# Create your views here.
from django.contrib.auth.models import User
from rest_framework import viewsets, permissions
from .serializers import UserSerializer
from rest_framework.permissions import IsAuthenticated
from .serializers import UserProfileSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import TenantSetupSerializer
from .models import ReportingTenant
from .models import Tenant
from .models import Entity
from .serializers import EntitySerializer
from .models import UserProfile
from .models import Center
from .serializers import CenterSerializer
from .models import Warehouse
from .serializers import WarehouseSerializer
from .models import Item
from .serializers import ItemSerializer
from .models import TradePartner, GoodsReceiptNote, GrnLineItem, DispatchOrder
from .serializers import TradePartnerSerializer, GoodsReceiptNoteSerializer, GrnLineItemSerializer, DispatchOrderSerializer

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # permission_classes = [permissions.IsAuthenticated]
    permission_classes = [IsAuthenticated]

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.AllowAny]  # change to IsAuthenticated in production


class TenantSetupViewSet(viewsets.ViewSet):
    """
    A ViewSet that only handles POST to create ReportingTenant + Tenant
    from a single 'name' field.
    """
    def create(self, request):
        serializer = TenantSetupSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            return Response(serializer.to_representation(result), status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def list(self, request):
        reporting_tenants = ReportingTenant.objects.all()
        tenants = Tenant.objects.all()

        data = {
            "reporting_tenants": [
                {
                    "id": rt.id,
                    "name": rt.name,
                    "status": rt.status,
                    "short_code": rt.short_code,
                }
                for rt in reporting_tenants
            ],
            "tenants": [
                {
                    "id": t.id,
                    "reporting_tenant": t.reporting_tenant.id,
                    "name": t.name,
                    "status": t.status,
                    "short_code": t.short_code,
                }
                for t in tenants
            ],
        }
        return Response(data, status=status.HTTP_200_OK)
    


# class AddressViewSet(viewsets.ModelViewSet):
#     queryset = Address.objects.all()
#     serializer_class = AddressSerializer
#     permission_classes = [IsAuthenticated]
#     # filter_backends = [DjangoFilterBackend]
#     # filterset_fields = ["id", "tenant", "city", "state", "country", "is_active", "is_archived"]

# class AddressViewSet(viewsets.ModelViewSet):
#     queryset = Address.objects.all()
#     serializer_class = AddressSerializer
#     permission_classes = [IsAuthenticated]

#     filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
#     filterset_fields = ["id", "uid", "is_active", "is_archived", "city", "state", "country", "tenant"]
#     search_fields = ["address_line", "postal_code", "city", "state", "country"]
#     ordering_fields = ["created", "updated"]

# class CurrencyViewSet(viewsets.ModelViewSet):
#     queryset = Currency.objects.all()
#     serializer_class = CurrencySerializer
#     permission_classes = [IsAuthenticated]


class EntityViewSet(viewsets.ModelViewSet):
    queryset = Entity.objects.all()
    serializer_class = EntitySerializer
    permission_classes = [IsAuthenticated]



class CenterViewSet(viewsets.ModelViewSet):
    queryset = Center.objects.all()
    serializer_class = CenterSerializer
    permission_classes = [IsAuthenticated]



class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated]

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated]

class TradePartnerViewSet(viewsets.ModelViewSet):
    queryset = TradePartner.objects.all()
    serializer_class = TradePartnerSerializer
    permission_classes = [IsAuthenticated]

# Goods Receipt Note (Header)
class GoodsReceiptNoteViewSet(viewsets.ModelViewSet):
    queryset = GoodsReceiptNote.objects.all().order_by("-grn_date")
    serializer_class = GoodsReceiptNoteSerializer
    permission_classes = [IsAuthenticated]


# Grn Line Item (Detail)
class GrnLineItemViewSet(viewsets.ModelViewSet):
    queryset = GrnLineItem.objects.all()
    serializer_class = GrnLineItemSerializer
    permission_classes = [IsAuthenticated]

class DispatchOrderViewSet(viewsets.ModelViewSet):
    queryset = DispatchOrder.objects.all().order_by("-dispatch_date")
    serializer_class = DispatchOrderSerializer
    permission_classes = [IsAuthenticated]

