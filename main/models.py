from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField

# Placeholder image URL used when Cloudinary is not configured
PLACEHOLDER_IMAGE = "https://placehold.co/400x400/e2e8f0/64748b?text=No+Image"

class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    contact = models.CharField(max_length=11)

    def __str__(self):
        return self.name


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('Electronics', 'Electronics'),
        ('Fashion', 'Fashion'),
        ('Clothing', 'Clothing'),
        ('Shoes', 'Shoes'),
        ('Mobiles', 'Mobiles'),
        ('Laptops', 'Laptops'),
        ('Watches', 'Watches'),
        ('Beauty', 'Beauty'),
        ('Furniture', 'Furniture'),
        ('Groceries', 'Groceries'),
        ('Sports', 'Sports'),
        ('Books', 'Books'),
        ('Toys', 'Toys'),
        ('Kitchen', 'Kitchen'),
        ('Accessories', 'Accessories'),
        ('Poultry', 'Poultry'),       # <-- Naya choice joda
        ('Branding', 'Branding'),     # <-- Naya choice joda
    ]

    name = models.CharField(max_length=100)
    price = models.FloatField()
    description = models.TextField()
    image = CloudinaryField('image', blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    category = models.CharField(
        max_length=100,
        choices=CATEGORY_CHOICES
    )
    discount_percentage = models.FloatField(default=0, help_text="Discount in percentage")

    def __str__(self):
        return self.name
    
    @property
    def image_url(self):
        """Safely return image URL with a placeholder fallback."""
        try:
            if self.image:
                return self.image.url
        except Exception:
            pass
        return PLACEHOLDER_IMAGE

    @property
    def discounted_price(self):
        """Calculate price after discount"""
        discount_amount = (self.price * self.discount_percentage) / 100
        return self.price - discount_amount

    @property
    def discount_amount(self):
        return self.price - self.discounted_price


class Cart(models.Model):
    quantity = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(Customer, on_delete=models.CASCADE)

    @property
    def subtotal(self):
        return self.product.discounted_price * self.quantity

    @property
    def original_subtotal(self):
        return self.product.price * self.quantity

    @property
    def discount_amount(self):
        return self.original_subtotal - self.subtotal


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    total_amount = models.IntegerField()
    payment_method = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=50, default="Pending")
    order_status = models.CharField(max_length=50, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.IntegerField()
    subtotal = models.IntegerField()
    discount_percentage = models.FloatField(default=0)
    discount_amount = models.FloatField(default=0)

    @property
    def original_subtotal(self):
        return self.price * self.quantity

    @property
    def discounted_unit_price(self):
        if self.quantity <= 0:
            return self.price
        return self.subtotal / self.quantity

    @property
    def effective_discount_amount(self):
        if self.discount_amount:
            return self.discount_amount
        return max(self.original_subtotal - self.subtotal, 0)

    @property
    def effective_discount_percentage(self):
        if self.discount_percentage:
            return self.discount_percentage
        if self.original_subtotal <= 0:
            return 0
        return (self.effective_discount_amount / self.original_subtotal) * 100


class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=200)
    payment_method = models.CharField(max_length=50)
    amount = models.IntegerField()
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Order #{self.order.id} - ₹{self.amount}"


class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()

    def __str__(self):
        return self.name



