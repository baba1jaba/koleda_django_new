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
path('cart/remove/<int:variant_id>/', views.cart_remove, name='cart_remove'),
path('about/', views.about_page, name='about_page'),
path('profile/', views.profile_view, name='profile'),
path('order/repeat/<int:order_id>/', views.order_repeat, name='order_repeat'),
]
