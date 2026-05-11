from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('cart/', views.cart_detail, name='cart_detail'),
path('cart/add/<int:variant_id>/', views.cart_add, name='cart_add'),
path('cart/add-detail/<int:product_id>/', views.cart_add_detail, name='cart_add_detail'),
path('checkout/', views.order_create, name='order_create'),
]