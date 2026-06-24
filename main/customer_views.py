import json
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.contrib import messages
from .models import User,Product, Customer, Cart, Order, OrderItem, Payment ,Contact 
# ==========================================
# Home & Info Pages
# ==========================================
def home(request):
    products = Product.objects.all().order_by("-id")[:6]
    most_selling_product = (
        Product.objects.annotate(sold_quantity=Sum("orderitem__quantity"))
        .filter(sold_quantity__isnull=False)
        .order_by("-sold_quantity", "-id")
        .first()
    )

    if not most_selling_product:
        most_selling_product = products.first()

    return render(request, "home.html", {
        "products": products,
        "most_selling_product": most_selling_product,
    })

def product(request):
    search = request.GET.get("search")
    category = request.GET.get("category")
    sort = request.GET.get("sort")

    products = Product.objects.all()

    if search:
        products = products.filter(name__icontains=search)

    if category:
        products = products.filter(category=category)

    if sort == "low":
        products = products.order_by("price")
    elif sort == "high":
        products = products.order_by("-price")
    elif sort == "latest":
        products = products.order_by("-id")

    # Fixed: Use your actual Product model's choices attribute if available
    category_choices = getattr(Product, 'CATEGORY_CHOICES', [])

    return render(request, "product.html", {
        "products": products,
        "categories": category_choices
    })

def product_detail(request, id):
    product_instance = get_object_or_404(Product, id=id)    
    return render(request, "product-page.html", {"product": product_instance})

def category(request):
    category_choices = getattr(Product, 'CATEGORY_CHOICES', [])
    return render(request, "category.html", {"categories": category_choices})

def about(request):
    return render(request, "about.html")

def contact(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        subject = request.POST.get("subject", "").strip()
        message = request.POST.get("message", "").strip()

        errors = []
        if not name or len(name) < 3:
            errors.append("Name must be at least 3 characters")
        if not email or "@" not in email:
            errors.append("Valid email is required")
        if not subject or len(subject) < 5:
            errors.append("Subject must be at least 5 characters")
        if not message or len(message) < 10:
            errors.append("Message must be at least 10 characters")

        if errors:
            return render(request, "contact.html", {"errors": errors})

        print(f"Contact Form: Name={name}, Email={email}, Subject={subject}, Message={message}")
        return render(request, "contact.html", {"success": "Thank you! Your message has been sent."})

    return render(request, "contact.html")
# ==========================================
# Fixed Authentication System
# ==========================================
def login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Admin Login Override
        if email == "admin@gmail.com" and password == "123":
            request.session["admin"] = True
            request.session["admin_name"] = "Admin"
            return redirect("/admin-home/")

        # User Login - Fixed to query Customer instead of the non-existent User model
        try:
            userdata = Customer.objects.get(email=email, password=password) 

            # Save User Session
            request.session["user_id"] = userdata.id 
            request.session["user_name"] = userdata.name 

            return redirect("/")
        except Customer.DoesNotExist:
            return render(request, "login.html", {
                "msg": "Invalid email or password"
            })

    return render(request, "login.html")

def register(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()
        address = request.POST.get("address", "").strip()
        phone = request.POST.get("phone", "").strip()

        errors = []
        if not name or len(name) < 3:
            errors.append("Name must be at least 3 characters")
        if not email or "@" not in email:
            errors.append("Valid email is required")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters")
        if password != confirm_password:
            errors.append("Passwords do not match")
        if not phone or len(phone) < 10:
            errors.append("Valid phone number is required")

        if errors:
            return render(request, "register.html", {"errors": errors})

        if Customer.objects.filter(email=email).exists():
            return render(request, "register.html", {
                "error": "Email already exists"
            })

        Customer.objects.create(
            name=name,
            email=email,
            password=password,
            address=address,
            contact=phone
        )
        return redirect("login") 

    return render(request, "register.html")

def logout(request):
    request.session.flush() 
    return redirect("login") 
# ==========================================
# Cart & Checkout System
# ==========================================
def cart(request):
    user_id = request.session.get("user_id") 
    if not user_id:
        return redirect("login") 

    user_instance = get_object_or_404(Customer, id=user_id) 
    cart_items = Cart.objects.filter(user=user_instance).select_related("product") 

    # Dynamic calculation for total price
    total = sum(item.subtotal for item in cart_items)
    original_total = sum(item.original_subtotal for item in cart_items)
    total_discount = sum(item.discount_amount for item in cart_items)

    # === FIX: Navbar ke liye Total Quantity Count Session me save kariye ===
    request.session["cart_count"] = sum(item.quantity for item in cart_items) 

    return render(request, "addtocart.html", {
        "cart_items": cart_items,
        "total": total,
        "original_total": original_total,
        "total_discount": total_discount,
        "customer": user_instance,
    })

def addtocart(request, id):
    user_id = request.session.get("user_id") 

    if not user_id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest': 
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        return redirect("login") 

    user_instance = get_object_or_404(Customer, id=user_id) 
    product_instance = get_object_or_404(Product, id=id) 

    quantity = 1
    if request.method == "POST":
        if request.content_type == 'application/json': 
            try:
                data = json.loads(request.body) 
                quantity = int(data.get("quantity", 1)) 
            except json.JSONDecodeError:
                pass
        else:
            quantity = int(request.POST.get("quantity", 1)) 

    if quantity < 1:
        quantity = 1

    existing_quantity = Cart.objects.filter(
        user=user_instance,
        product=product_instance
    ).values_list("quantity", flat=True).first() or 0

    if product_instance.stock <= 0 or existing_quantity + quantity > product_instance.stock:
        message = f"Only {product_instance.stock} item(s) available for {product_instance.name}."
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': message}, status=400)
        messages.error(request, message)
        return redirect("product_detail", id=product_instance.id)

    cart_item, created = Cart.objects.get_or_create( 
        user=user_instance,
        product=product_instance,
        defaults={"quantity": quantity}
    )

    if not created:
        cart_item.quantity += quantity 
        cart_item.save() 

    # === FIX: Naya total count nikal kar session sync karein ===
    all_items = Cart.objects.filter(user=user_instance)
    request.session["cart_count"] = sum(item.quantity for item in all_items)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest': 
        return JsonResponse({
            'success': True,
            'quantity': cart_item.quantity,
            'subtotal': getattr(cart_item, 'subtotal', 0),
            'original_subtotal': getattr(cart_item, 'original_subtotal', 0),
            'discount_amount': getattr(cart_item, 'discount_amount', 0),
            'global_cart_count': request.session["cart_count"] # AJAX verification update ke liye
        })

    return redirect("cart")

def remove_from_cart(request, id):
    user_id = request.session.get("user_id") 
    if not user_id:
        return redirect("login") 

    cart_item = get_object_or_404(Cart, id=id, user_id=user_id) 

    if cart_item.quantity > 1:
        cart_item.quantity -= 1 
        cart_item.save() 
        deleted = False
    else:
        cart_item.delete() 
        deleted = True

    # === FIX: Kam karne ke baad wapas naya total count nikal kar session sync karein ===
    all_items = Cart.objects.filter(user_id=user_id)
    request.session["cart_count"] = sum(item.quantity for item in all_items)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            "success": True,
            "deleted": deleted,
            "quantity": 0 if deleted else cart_item.quantity,
            "subtotal": 0 if deleted else cart_item.subtotal,
            "original_subtotal": 0 if deleted else cart_item.original_subtotal,
            "discount_amount": 0 if deleted else cart_item.discount_amount,
            "global_cart_count": request.session["cart_count"],
        })

    return redirect("cart") 

def delete_cart_item(request, id):
    user_id = request.session.get("user_id") 
    if not user_id:
        return redirect("login") 

    cart_item = get_object_or_404(Cart, id=id, user_id=user_id) 
    cart_item.delete() 

    # === FIX: Delete karne ke baad bache huye items ka sum session me sync karein ===
    all_items = Cart.objects.filter(user_id=user_id)
    request.session["cart_count"] = sum(item.quantity for item in all_items)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            "success": True,
            "deleted": True,
            "global_cart_count": request.session["cart_count"],
        })

    return redirect("cart")
# ==========================================
# Robust Checkout System
# ==========================================
def checkout(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    current_customer = get_object_or_404(Customer, id=user_id)
    cart_items = Cart.objects.filter(user=current_customer).select_related("product")

    if request.method == "POST":
        customer_name = request.POST.get("name", "").strip()
        customer_email = request.POST.get("email", "").strip()
        customer_phone = request.POST.get("phone", "").strip()
        customer_address = request.POST.get("address", "").strip()

        errors = []
        if not customer_name or len(customer_name) < 3:
            errors.append("Name must be at least 3 characters")
        if not customer_email or "@" not in customer_email:
            errors.append("Valid email is required")
        if not customer_phone or len(customer_phone) < 10:
            errors.append("Valid phone number is required")
        if not customer_address:
            errors.append("Address is required")
        if (
            customer_email != current_customer.email
            and Customer.objects.filter(email=customer_email).exclude(id=current_customer.id).exists()
        ):
            errors.append("This email is already used by another customer")

        if errors:
            return render(request, 'checkout.html', {
                'customer': current_customer,
                'total': sum(item.subtotal for item in cart_items),
                'original_total': sum(item.original_subtotal for item in cart_items),
                'total_discount': sum(item.discount_amount for item in cart_items),
                'cart_count': sum(item.quantity for item in cart_items),
                'errors': errors
            })

        current_customer.name = customer_name
        current_customer.email = customer_email
        current_customer.contact = customer_phone
        current_customer.address = customer_address
        current_customer.save()

        if not cart_items.exists():
            messages.warning(request, "Your cart is empty!")
            return redirect('cart')

        for item in cart_items:
            if item.product.stock <= 0:
                messages.error(request, f"{item.product.name} is out of stock.")
                return redirect("cart")
            if item.quantity > item.product.stock:
                messages.error(
                    request,
                    f"Only {item.product.stock} item(s) available for {item.product.name}. Please update your cart."
                )
                return redirect("cart")

        total_amount = sum(item.subtotal for item in cart_items)
        auth_user, _ = User.objects.get_or_create(
            username=current_customer.email,
            defaults={
                "email": current_customer.email,
                "first_name": current_customer.name,
            }
        )

        order = Order.objects.create(
            user=auth_user,
            name=current_customer.name,
            email=current_customer.email,
            phone=current_customer.contact,
            address=current_customer.address,
            total_amount=int(total_amount),
            order_status="Pending",
            payment_status="Pending",
            payment_method="COD"
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
                subtotal=item.subtotal,
                discount_percentage=item.product.discount_percentage,
                discount_amount=item.discount_amount,
            )

        return redirect('payment', id=order.id)

    # === GET Request Handling ===
    if not cart_items.exists():
        messages.warning(request, "Your cart is empty! Add items before checking out.")
        return redirect('cart')

    total = sum(item.subtotal for item in cart_items)
    original_total = sum(item.original_subtotal for item in cart_items)
    total_discount = sum(item.discount_amount for item in cart_items)
    cart_count = sum(item.quantity for item in cart_items)

    return render(request, 'checkout.html', {
        'customer': current_customer,
        'total': total,
        'original_total': original_total,
        'total_discount': total_discount,
        'cart_count': cart_count
    })
# ==========================================
# Fixed Payment Logic View
# ==========================================
def payment(request, id):
    # Fetch base target records
    order = get_object_or_404(Order, id=id)
    order_items = OrderItem.objects.filter(order=order).select_related('product')
    
    original_total = sum(item.original_subtotal for item in order_items)
    total_discount = sum(item.effective_discount_amount for item in order_items)

    if request.method == "POST":
        payment_method = request.POST.get("payment_method", "COD")

        try:
            # Open database runtime transaction lock block
            with transaction.atomic():
                
                # Fetch order items again inside the transaction, locking the related products
                # This blocks other threads from evaluating stale inventory metrics concurrently
                locked_items = OrderItem.objects.filter(order=order).select_related('product').select_for_update()
                
                for item in locked_items:
                    product = item.product
                    
                    # Safe validation against runtime locked state values
                    if product.stock <= 0:
                        messages.error(request, f"{product.name} is out of stock.")
                        return redirect("cart")
                        
                    if item.quantity > product.stock:
                        messages.error(
                            request,
                            f"Only {product.stock} item(s) available for {product.name}."
                        )
                        return redirect("cart")

                    # ATOMIC DECREMENT: Modifies the record at SQL execution layer directly
                    product.stock = F('stock') - item.quantity
                    product.save(update_fields=["stock"])

                # Create audit ledger payment record directly from trusted DB order pricing metrics
                Payment.objects.create(
                    order=order,
                    payment_id=f"PAY-{order.id}-TXT",
                    payment_method=payment_method,
                    amount=order.total_amount,  # Trusted server attribute calculation value used
                    status="Completed",
                    created_at=order.created_at
                )

                # Update transactional status parameters
                order.payment_status = "Completed"
                order.order_status = "Accepted"
                order.save()

                # Clean cart via linked customer mapping data structures [cite: 777]
                Cart.objects.filter(user__email=order.email).delete()

            return redirect('success')

        except Exception as e:
            # If any failure occurs inside the atomic block, everything rolls back seamlessly
            messages.error(request, "A transaction processing error occurred. Please try again.")
            return redirect("cart")

    return render(request, 'payment.html', {
        'order': order,
        'order_items': order_items,
        'original_total': original_total,
        'total_discount': total_discount,
    })

def success(request):
    return render(request, "success.html")

def myorder(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    customer = get_object_or_404(Customer, id=user_id)
    raw_orders = (
        Order.objects.filter(email=customer.email, payment_status="Completed")
        .prefetch_related("orderitem_set__product")
        .order_by("-created_at")
    )

    # Calculate total length
    total_count = raw_orders.count()
    
    # Attach a custom attribute 'customer_seq_num' to each order record in-memory
    # Because they are sorted newest first, index 0 gets total_count, index 1 gets total_count - 1, etc.
    for index, order in enumerate(raw_orders):
        order.customer_seq_num = total_count - index

    return render(request, "myorder.html", {"orders": raw_orders})

def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        Contact.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )

        return redirect("contact")

    return render(request, "contact.html")
