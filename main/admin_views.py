from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from .models import Product, Customer, Order, Contact


ORDER_STATUS_CHOICES = ["Pending", "Accepted", "Packed", "Shipped", "Delivered", "Cancelled"]
PAYMENT_STATUS_CHOICES = ["Pending", "Completed", "Failed", "Refunded"]


def admin_required(request):
    return request.session.get("admin")


def admin_dashboard(request):

    if not admin_required(request):
        return redirect("login")

    orders = Order.objects.all().order_by("-created_at")
    total_revenue = (
        orders.exclude(order_status="Cancelled")
        .filter(payment_status="Completed")
        .aggregate(total=Sum("total_amount"))["total"] or 0
    )

    context = {
        "total_products": Product.objects.count(),
        "total_customers": Customer.objects.count(),
        "total_orders": orders.count(),
        "pending_orders": orders.filter(order_status="Pending").count(),
        "completed_orders": orders.filter(order_status="Delivered").count(),
        "total_revenue": total_revenue,
        "recent_orders": orders[:8],
    }

    return render(request, "admin-dashboard.html", context)


# Admin Product Dashboard
def admin_home(request):

    # Check admin authentication
    if not admin_required(request):
        return redirect("login")

    # Save Product
    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        price = request.POST.get("price", "").strip()
        stock = request.POST.get("stock", "").strip()
        category = request.POST.get("category", "").strip()
        discount = request.POST.get("discount", "0").strip()
        image = request.FILES.get("image")

        # Validation
        errors = []
        if not name or len(name) < 3:
            errors.append("Product name must be at least 3 characters")
        if not description or len(description) < 10:
            errors.append("Description must be at least 10 characters")
        if not price:
            errors.append("Price is required")
        if stock == "":
            errors.append("Available quantity is required")
        if not category:
            errors.append("Category is required")
        if not image:
            errors.append("Product image is required")

        if errors:
            products = Product.objects.all()
            return render(request, "admin.html", {
                "products": products,
                "categories": Product.CATEGORY_CHOICES,
                "errors": errors
            })

        try:
            price = float(price)
            if price <= 0:
                raise ValueError
        except (ValueError, TypeError):
            products = Product.objects.all()
            return render(request, "admin.html", {
                "products": products,
                "categories": Product.CATEGORY_CHOICES,
                "errors": ["Price must be a positive number"]
            })

        try:
            stock = int(stock)
            if stock < 0:
                raise ValueError
        except (ValueError, TypeError):
            products = Product.objects.all()
            return render(request, "admin.html", {
                "products": products,
                "categories": Product.CATEGORY_CHOICES,
                "errors": ["Available quantity must be zero or more"]
            })

        try:
            discount = float(discount)
            if discount < 0 or discount > 100:
                raise ValueError
        except (ValueError, TypeError):
            products = Product.objects.all()
            return render(request, "admin.html", {
                "products": products,
                "categories": Product.CATEGORY_CHOICES,
                "errors": ["Discount must be a number between 0 and 100"]
            })

        Product.objects.create(
            name=name,
            description=description,
            price=price,
            stock=stock,
            category=category,
            discount_percentage=discount,
            image=image
        )

        return redirect("/admin-home/")

    # Show Products
    products = Product.objects.all()

    return render(request, "admin.html", {
        "products": products,
        "categories": Product.CATEGORY_CHOICES
    })


def edit_product(request, id):

    if not admin_required(request):
        return redirect("login")

    product = get_object_or_404(Product, id=id)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        price = request.POST.get("price", "").strip()
        stock = request.POST.get("stock", "").strip()
        category = request.POST.get("category", "").strip()
        discount = request.POST.get("discount", "0").strip()
        image = request.FILES.get("image")

        errors = []
        if not name or len(name) < 3:
            errors.append("Product name must be at least 3 characters")
        if not description or len(description) < 10:
            errors.append("Description must be at least 10 characters")
        if not price:
            errors.append("Price is required")
        if stock == "":
            errors.append("Available quantity is required")
        if not category:
            errors.append("Category is required")

        try:
            price = float(price)
            if price <= 0:
                raise ValueError
        except (ValueError, TypeError):
            errors.append("Price must be a positive number")

        try:
            stock = int(stock)
            if stock < 0:
                raise ValueError
        except (ValueError, TypeError):
            errors.append("Available quantity must be zero or more")

        try:
            discount = float(discount)
            if discount < 0 or discount > 100:
                raise ValueError
        except (ValueError, TypeError):
            errors.append("Discount must be a number between 0 and 100")

        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect("admin_home")

        product.name = name
        product.description = description
        product.price = price
        product.stock = stock
        product.category = category
        product.discount_percentage = discount
        if image:
            product.image = image
        product.save()

        messages.success(request, "Product updated successfully.")

    return redirect("admin_home")


def delete_product(request, id):

    if not admin_required(request):
        return redirect("login")

    product = get_object_or_404(Product, id=id)

    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted successfully.")

    return redirect("admin_home")


def delete_product(request, id):

    if not admin_required(request):
        return redirect("login")

    product = get_object_or_404(Product, id=id)

    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted successfully.")

    return redirect("admin_home")


# Admin Category Dashboard
def admin_category(request):

    categories = [
        category for category in Product.CATEGORY_CHOICES
        if category[1] != "Fashion"
    ]

    return render(request, "category.html", {
        "categories": categories
    })


# Admin Customer Dashboard
def admin_customers(request):

    # Check admin authentication
    if not admin_required(request):
        return redirect("login")

    customers = Customer.objects.all()

    return render(request, "admin-customers.html", {
        "customers": customers
    })


# Edit Customer
def edit_customer(request, id):

    # Check admin authentication
    if not admin_required(request):
        return redirect("login")

    customer = Customer.objects.get(id=id)

    if request.method == "POST":

        customer.name = request.POST.get("name")
        customer.email = request.POST.get("email")
        customer.contact = request.POST.get("phone")
        customer.address = request.POST.get("address")

        customer.save()

        return redirect("admin_customers")

    return redirect("admin_customers")


# Delete Customer
def delete_customer(request, id):

    # Check admin authentication
    if not admin_required(request):
        return redirect("login")

    customer = Customer.objects.get(id=id)

    customer.delete()

    return redirect("admin_customers")


def admin_orders(request):

    if not admin_required(request):
        return redirect("login")

    status = request.GET.get("status", "").strip()
    payment = request.GET.get("payment", "").strip()
    search = request.GET.get("search", "").strip()

    orders = Order.objects.all().order_by("-created_at")

    if status:
        orders = orders.filter(order_status=status)
    if payment:
        orders = orders.filter(payment_status=payment)
    if search:
        orders = orders.filter(email__icontains=search) | orders.filter(name__icontains=search)

    context = {
        "orders": orders.prefetch_related("orderitem_set__product"),
        "order_status_choices": ORDER_STATUS_CHOICES,
        "payment_status_choices": PAYMENT_STATUS_CHOICES,
        "selected_status": status,
        "selected_payment": payment,
        "search": search,
    }

    return render(request, "admin-orders.html", context)


def update_order_status(request, id):

    if not admin_required(request):
        return redirect("login")

    order = get_object_or_404(Order, id=id)

    if request.method == "POST":
        order_status = request.POST.get("order_status")
        payment_status = request.POST.get("payment_status")

        if order_status in ORDER_STATUS_CHOICES:
            order.order_status = order_status
        if payment_status in PAYMENT_STATUS_CHOICES:
            order.payment_status = payment_status

        order.save()
        messages.success(request, f"Order #{order.id} updated successfully.")

    return redirect("admin_orders")


def admin_contact(request):

    # Optional admin session check
    if not request.session.get("admin"):
        return redirect("/login/")

    contacts = Contact.objects.all().order_by("-id")

    return render(
        request,
        "admin-contact.html",
        {"contacts": contacts}
    )

