# demoapp/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, UserProfileViewSet, TenantSetupViewSet, EntityViewSet

router= DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'userprofiles',UserProfileViewSet,basename='userpofile')
router.register(r'setup-tenant', TenantSetupViewSet, basename='setup-tenant')  
# router.register(r'addresses', AddressViewSet, basename='address')
# router.register(r'currencies', CurrencyViewSet, basename='currency')
router.register(r'entities', EntityViewSet, basename='entity')

urlpatterns = [ 
    # Classic CBV URL for users (GET + POST)
   # path("users/", UserListCreateView.as_view(), name="user-list-create"),

    # Router URLs for UserProfile (list, create, retrieve, update, delete)
    path('', include(router.urls)),
]
