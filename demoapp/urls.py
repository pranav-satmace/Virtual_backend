# demoapp/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, UserProfileViewSet, TenantSetupViewSet, EntityViewSet
from .views import CenterViewSet
from .views import WarehouseViewSet
from .views import ItemViewSet
from .views import TradePartnerViewSet, DispatchOrderViewSet
from .views import GoodsReceiptNoteViewSet, GrnLineItemViewSet
from .views_auth import RegisterWithEmailView, VerifyEmailOTPView, PatchedTokenObtainPairView, LogoutView
from rest_framework_simplejwt.views import TokenRefreshView

router= DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'userprofiles',UserProfileViewSet,basename='userpofile')
router.register(r'setup-tenant', TenantSetupViewSet, basename='setup-tenant')  
# router.register(r'addresses', AddressViewSet, basename='address')
# router.register(r'currencies', CurrencyViewSet, basename='currency')
router.register(r'entities', EntityViewSet, basename='entity')
router.register(r'centers', CenterViewSet)
router.register(r'warehouses', WarehouseViewSet)
router.register(r'items', ItemViewSet, basename='item')
router.register(r"trade-partners", TradePartnerViewSet, basename="trade-partner")
router.register(r"grn-header", GoodsReceiptNoteViewSet, basename="grn-header")
router.register(r"grn-detail", GrnLineItemViewSet, basename="grn-detail")
router.register(r"dispatch-order", DispatchOrderViewSet, basename="dispatch-order")


from .views import WarehouseViewSet

urlpatterns = [ 
    # Classic CBV URL for users (GET + POST)
   # path("users/", UserListCreateView.as_view(), name="user-list-create"),

    # Router URLs for UserProfile (list, create, retrieve, update, delete)
    path('', include(router.urls)),

    # 🔐 Auth endpoints
    path('api/auth/register/', RegisterWithEmailView.as_view(), name='register'),
    path('api/auth/verify-email/', VerifyEmailOTPView.as_view(), name='verify-email'),
    path('api/auth/token/', PatchedTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/logout/', LogoutView.as_view(), name='logout'),

]
