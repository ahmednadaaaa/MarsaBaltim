from django.urls import path
from . import views

app_name = 'owners'

urlpatterns = [
    # HTML portal page (SPA)
    path('', views.OwnerPortalView.as_view(), name='portal'),

    # Auth API
    path('api/register/', views.OwnerRegisterView.as_view()),
    path('api/login/',    views.OwnerLoginView.as_view()),
    path('api/logout/',   views.OwnerLogoutView.as_view()),
    path('api/me/',       views.OwnerMeView.as_view()),

    # Properties API
    path('api/properties/',
         views.OwnerPropertiesView.as_view()),
    path('api/properties/<int:pk>/',
         views.OwnerPropertyDetailView.as_view()),
    path('api/properties/<int:pk>/images/',
         views.OwnerImageUploadView.as_view()),
    path('api/properties/<int:pk>/images/<int:img_id>/',
         views.OwnerImageUploadView.as_view()),
    path('properties/<int:pk>/edit-images/',
         views.OwnerPropertyEditImagesView.as_view(), name='owner-edit-images'),

    # Accounting API
    path('api/accounts/', views.OwnerAccountListView.as_view()),
    path('api/accounts/<int:pk>/', views.OwnerAccountDetailView.as_view()),
    path('api/accounts/transaction/<str:transaction_type>/', views.OwnerTransactionView.as_view()),
    path('api/accounts/transaction/<str:transaction_type>/<int:pk>/', views.OwnerTransactionDetailView.as_view()),
]
