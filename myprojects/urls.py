"""
URL configuration for myprojects project.

The `urlpatterns` list routes URLs to views.
"""

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from main.admin_views import (
    admin_category,
    admin_customers,
    admin_dashboard,
    admin_home,
    admin_orders,
    delete_customer,
    delete_product,
    edit_customer,
    edit_product,
    update_order_status,
    admin_contact,
)
from main.customer_views import (
    about,
    contact,
    home,
    login,
    logout,
    product,
    product_detail,
    register,
    addtocart,
    cart,
    remove_from_cart,
    delete_cart_item,
    checkout,
    success,
    payment,
    myorder,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name="home"),
    path('product/', product, name="product"),
    path('about/', about, name="about"),
    path('contact/', contact, name="contact"),
    path('login/', login, name="login"),
    path('register/', register, name="register"),
    path('logout/', logout, name="logout"),
    path('cart/', cart, name="cart"),
    path('remove_from_cart/<int:id>/', remove_from_cart, name="remove_from_cart"),
    path('delete_cart_item/<int:id>/', delete_cart_item, name="delete_cart_item"),
    path('addtocart/<int:id>/', addtocart, name="addtocart"),
    path('admin-dashboard/', admin_dashboard, name="admin_dashboard"),
    path('admin-home/', admin_home, name="admin_home"),
    path("edit-product/<int:id>/", edit_product, name="edit_product"),
    path("delete-product/<int:id>/", delete_product, name="delete_product"),
    path("admin-orders/", admin_orders, name="admin_orders"),
    path("update-order-status/<int:id>/", update_order_status, name="update_order_status"),
    path("admin-category/", admin_category, name="admin_category"),
    path("admin-customers/", admin_customers, name="admin_customers"),
    path("admin-contact/",admin_contact,name="admin_contact"),
    path("edit-customer/<int:id>/", edit_customer, name="edit_customer"),
    path("delete-customer/<int:id>/", delete_customer, name="delete_customer"),
    path('product-page/<int:id>/', product_detail, name="product_detail"),
    path('checkout/', checkout, name="checkout"),
    path('success/', success, name="success"),
    path('payment/<int:id>/', payment, name="payment"),
    path('myorder/', myorder, name="myorder"),
]

# Media Files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
