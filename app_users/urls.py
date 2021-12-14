from django.urls import path

from .views import *


urlpatterns = [
    path('login/', UserLogin.as_view(), name='login'),
    path('logout/', UserLogout.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('account/', AccountInfoView.as_view(), name='account'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('edit_customer_info/', CustomerEditView.as_view(), name='edit_info'),
    path('upbalance/', TopUpBalanceView.as_view(), name='upbalance'),
    path('pay_order/', PayOrderView.as_view(), name='pay_order')
]
