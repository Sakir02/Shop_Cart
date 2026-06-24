from django.contrib import admin
from .models import Customer, Product, Cart ,Order, OrderItem, Payment,Contact

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):

    list_display = [
        "id",
        "name",
        "email",
        "contact"
    ]

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "category", "price", "stock"]
    list_filter = ["category"]
    search_fields = ["name", "category"]

admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)
admin.site.register(Contact)

