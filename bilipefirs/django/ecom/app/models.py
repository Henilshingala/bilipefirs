from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .utils import send_order_email
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import threading

STATE_CHOICES = (
    ('Andhra Pradesh', 'Andhra Pradesh'),
    ('Arunachal Pradesh', 'Arunachal Pradesh'),
    ('Assam', 'Assam'),
    ('Bihar', 'Bihar'),
    ('Chhattisgarh', 'Chhattisgarh'),
    ('Goa', 'Goa'),
    ('Gujarat', 'Gujarat'),
    ('Haryana', 'Haryana'),
    ('Himachal Pradesh', 'Himachal Pradesh'),
    ('Jharkhand', 'Jharkhand'),
    ('Karnataka', 'Karnataka'),
    ('Kerala', 'Kerala'),
    ('Madhya Pradesh', 'Madhya Pradesh'),
    ('Maharashtra', 'Maharashtra'),
    ('Manipur', 'Manipur'),
    ('Meghalaya', 'Meghalaya'),
    ('Mizoram', 'Mizoram'),
    ('Nagaland', 'Nagaland'),
    ('Odisha', 'Odisha'),
    ('Punjab', 'Punjab'),
    ('Rajasthan', 'Rajasthan'),
    ('Sikkim', 'Sikkim'),
    ('Tamil Nadu', 'Tamil Nadu'),
    ('Telangana', 'Telangana'),
    ('Tripura', 'Tripura'),
    ('Uttar Pradesh', 'Uttar Pradesh'),
    ('Uttarakhand', 'Uttarakhand'),
    ('West Bengal', 'West Bengal')
)
CATEGORY_CHOICES = (
    ('bg', 'Bugatti'),
    ('lb', 'Lamborghini'),
    ('fr', 'Ferrari'),
    ('rr', 'Rolls-Royce'),
    ('pc', 'Porsche'),
    ('ml', 'McLaren'),
)

class Product(models.Model):
    title = models.CharField(max_length=100)
    selling_price = models.FloatField()
    discounted_price = models.FloatField()
    description = models.TextField()
    composition = models.TextField(default='', blank=True)
    prodapp = models.TextField(default='', blank=True)
    product_image = models.ImageField(upload_to='product', default='default_product.jpg')
    category = models.CharField(max_length=2, choices=CATEGORY_CHOICES)  

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-discounted_price']
        verbose_name = "Product"
        verbose_name_plural = "Products"

class Customer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    country = models.CharField(max_length=50, default='India',null=False)
    full_name = models.CharField(max_length=200, help_text='First and Last name',null=False)
    mobile = models.CharField(max_length=15, help_text='Mobile number',null=False)
    pincode = models.CharField(max_length=6, help_text='6 digits code',null=False)
    house_no = models.CharField(max_length=200, help_text='Flat, House no., Building, Company, Apartment',null=False)
    street = models.CharField(max_length=200, help_text='Area, Street, Sector, Village',null=False)
    landmark = models.CharField(max_length=200, blank=True, null=True, help_text='Landmark (Optional)')
    city = models.CharField(max_length=50, help_text='Town/City',null=False)
    state = models.CharField(choices=STATE_CHOICES, max_length=100, help_text='Choose a state',null=False)

    def __str__(self):
        return f"{self.full_name or 'No Name'} - {self.city or 'No City'}"

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"



class Pincode(models.Model):
    pincode = models.CharField(max_length=6, unique=True)
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.pincode} - {self.district}, {self.state}"


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_cost(self):
        return self.quantity * self.product.discounted_price

    class Meta:
        verbose_name = "Cart"
        verbose_name_plural = "Carts"
        unique_together = ('user', 'product')  

STATUS_CHOICES = (
    ('Accepted', 'Accepted'),
    ('Packed', 'Packed'),
    ('On The Way', 'On The Way'),
    ('Delivered', 'Delivered'),
    ('Cancel', 'Cancel'),
    ('Pending', 'Pending'),
)

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True)
    total = models.FloatField(null=-True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=50, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Order ID: {self.id}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.FloatField(null=True)
    quantity = models.IntegerField(null=True)

    def __str__(self):
        return f"{self.quantity} of {self.product.title}"
    
class CryptoPayment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, null=True)
    transaction_hash = models.CharField(max_length=100)
    from_address = models.CharField(max_length=42)
    amount = models.DecimalField(max_digits=18, decimal_places=8)
    eth_amount = models.DecimalField(max_digits=18, decimal_places=8)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='pending')
    
    def __str__(self):
        return f"Payment {self.transaction_hash[:10]}... for Order {self.order.id if self.order else 'None'}"
    
    class Meta:
        verbose_name = "Crypto Payment"
        verbose_name_plural = "Crypto Payments"

        
class OrderPlaced(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    ordered_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    payment = models.ForeignKey(CryptoPayment, on_delete=models.CASCADE, null=True, blank=True) 

    @property
    def total_cost(self):
        return self.quantity * self.product.discounted_price

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"
    
@receiver(post_save, sender=Order)
def handle_order_status_change(sender, instance, created, **kwargs):
    if not created and instance.status == 'Delivered':
        order_items = OrderItem.objects.filter(order=instance)
        
        payment = CryptoPayment.objects.filter(order=instance).first()  

        for order_item in order_items:
            OrderPlaced.objects.create(
                user=instance.user,
                customer=instance.customer,
                product=order_item.product,
                quantity=order_item.quantity,
                ordered_date=instance.created_at,  
                status=instance.status,
                payment=payment 
            )
        order_items.delete()

    
@receiver(post_save, sender=Order)
def send_order_status_email(sender, instance, **kwargs):
    order_items = OrderItem.objects.filter(order=instance) 
    subject = f"Your Order {instance.id} Status Update"

    send_order_email(instance.user.email, subject, instance, order_items) 

class DiscountCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    current_uses = models.PositiveIntegerField(default=0)
    minimum_order_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )

    def is_valid(self, order_amount=None):
        now = timezone.now()
        
        if not self.is_active:
            return False, "This discount code is not active"
            
        if self.valid_until and now > self.valid_until:
            return False, "This discount code has expired"
            
        if self.max_uses and self.current_uses >= self.max_uses:
            return False, "This discount code has reached its usage limit"
            
        if self.minimum_order_amount and order_amount and order_amount < self.minimum_order_amount:
            return False, f"Order must be at least ₹{self.minimum_order_amount} to use this code"
            
        return True, "Valid"

    def __str__(self):
        return f"{self.code} - {self.discount_percentage}% off"

    class Meta:
        app_label = 'app'

@receiver(post_save, sender='app.Order')
def handle_order_creation(sender, instance, created, **kwargs):
    """Clear discount after order creation"""
    if created:
        request = getattr(threading.current_thread(), 'request', None)
        if request:
            request.session.pop('discount_percentage', None)
            request.session.pop('discount_code', None)
            request.session.modified = True

        # Send order confirmation email
        order_items = OrderItem.objects.filter(order=instance)
        subject = f"Your Order {instance.id} Status Update"
        send_order_email(instance.user.email, subject, instance, order_items)

