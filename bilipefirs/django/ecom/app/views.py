from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, Http404
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from decimal import Decimal
from web3 import Web3
import json
from django.contrib.auth import views as auth_views
from .models import Product, Customer, Cart, CryptoPayment, Order, OrderItem, OrderPlaced, DiscountCode
from .forms import CustomerRegistrationForm, CustomerProfileForm, LoginForm, DiscountCodeForm
from .utils import send_order_email
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
import logging
from .models import Pincode

def home(request):
    return render(request, 'app/home.html')

def about(request):
    return render(request, 'app/about.html')

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('full-name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        email_subject = f"New contact form submission: {subject}"
        email_message = f"Name: {name}\nEmail: {email}\nSubject: {subject}\nMessage: {message}"
        try:
            send_mail(email_subject, email_message, settings.DEFAULT_FROM_EMAIL, [settings.EMAIL_HOST_USER], fail_silently=False)
            messages.success(request, "Your message has been sent successfully!")
            return redirect('contact')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
    return render(request, 'app/contact.html')

def contact_success(request):
    return render(request, 'app/contact_success.html')

class CustomerRegistrationView(View):
    def get(self, request):
        form = CustomerRegistrationForm()
        return render(request, 'app/customerregistration.html', {'form': form})

    def post(self, request):
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Congratulations! User registration successful.")
            return redirect('login')
        else:
            messages.warning(request, "Oops! Invalid input data.")
        return render(request, 'app/customerregistration.html', {'form': form})

class LoginView(View):
    def get(self, request):
        form = LoginForm()
        return render(request, 'app/login.html', {'form': form})

    def post(self, request):
        form = LoginForm(request=request, data=request.POST)
        if form.is_valid():
            uname = form.cleaned_data['username']
            upass = form.cleaned_data['password']
            user = authenticate(username=uname, password=upass)
            if user is not None:
                login(request, user)
                messages.success(request, "Logged in successfully!")
                return redirect('profile')
        messages.warning(request, "Invalid username or password.")
        return render(request, 'app/login.html', {'form': form})


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        customer, created = Customer.objects.get_or_create(user=request.user)
        form = CustomerProfileForm()
        context = {
            'form': form,
            'title': 'Add Address' if created else 'Update Address'
        }
        return render(request, 'app/profile.html', context)

    def post(self, request):
        customer, created = Customer.objects.get_or_create(user=request.user)
        form = CustomerProfileForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('address')
        context = {
            'form': form,
            'title': 'Add Address' if created else 'Update Address'
        }
        return render(request, 'app/profile.html', context)

class AddressListView(LoginRequiredMixin, View):
    def get(self, request):
        addresses = Customer.objects.filter(user=request.user)
        return render(request, 'app/address.html', {
            'addresses': addresses,
            'title': 'My Addresses'
        })


def get_pincode_details(request):
    pincode = request.GET.get('pincode')
    if pincode and len(pincode) == 6:
        try:
            pincode_data = Pincode.objects.get(pincode=pincode)
            return JsonResponse({
                'success': True,
                'district': pincode_data.district,
                'state': pincode_data.state
            })
        except Pincode.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid Pincode'})
    return JsonResponse({'success': False, 'message': 'Enter a valid 6-digit pincode'})


class UpdateAddressView(LoginRequiredMixin, View):
    def get(self, request, pk):
        address = get_object_or_404(Customer, pk=pk, user=request.user)
        form = CustomerProfileForm(instance=address)
        return render(request, 'app/updateAddress.html', {
            'form': form,
            'title': 'Update Address'
        })

    def post(self, request, pk):
        address = get_object_or_404(Customer, pk=pk, user=request.user)
        form = CustomerProfileForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "Address updated successfully!")
            return redirect('address')
        return render(request, 'app/updateAddress.html', {
            'form': form,
            'title': 'Update Address'
        })

class CategoryView(View):
    def get(self, request, val):
        products = Product.objects.filter(category=val)

        if products.exists():
            title = products.first().category
        else:
            title = "No Products Available"
            messages.warning(request, "No products found for this category.")

        context = {'products': products, 'title': title}
        return render(request, 'app/category.html', context)

class ProductDetail(View):
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        context = {'product': product}
        return render(request, 'app/productdetail.html', context)

@login_required
def add_to_cart(request):
    if request.method == 'GET':
        prod_id = request.GET.get('prod_id')
        product = Product.objects.get(id=prod_id)
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': 1}
        )
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        return redirect('/cart')

@login_required
def show_cart(request):
    cart = Cart.objects.filter(user=request.user)
    amount = float('0.00')

    for item in cart:
        amount += float(str(item.quantity)) * item.product.discounted_price

    gst_rate = float('0.28')
    cess_rate = float('0.20')

    gst = amount * gst_rate
    cess = amount * cess_rate
    total_tax = gst + cess

    shipping = float('100000.00')
    totalamount = amount + total_tax + shipping

    context = {
        'cart': cart,
        'amount': amount,
        'total_tax': total_tax,
        'totalamount': totalamount
    }
    return render(request, 'app/addtocart.html', context)

@login_required
def plus_cart(request):
    if request.method == 'GET':
        prod_id = request.GET.get('prod_id')
        cart_item = Cart.objects.get(Q(product=prod_id) & Q(user=request.user))
        cart_item.quantity += 1
        cart_item.save()

        amount = float('0.00')
        cart = Cart.objects.filter(user=request.user)
        for item in cart:
            amount += float(str(item.quantity)) * item.product.discounted_price

        tax_rate = float('0.48')
        total_tax = amount * tax_rate
        totalamount = amount + total_tax + float('10.00')

        return JsonResponse({
            'quantity': cart_item.quantity,
            'amount': str(amount),
            'totalamount': str(totalamount)
        })

@login_required
def minus_cart(request):
    if request.method == 'GET':
        prod_id = request.GET.get('prod_id')
        cart_item = Cart.objects.get(Q(product=prod_id) & Q(user=request.user))
        cart_item.quantity -= 1

        if cart_item.quantity <= 0:
            cart_item.delete()
            quantity = 0
        else:
            cart_item.save()
            quantity = cart_item.quantity

        amount = float('0.00')
        cart = Cart.objects.filter(user=request.user)
        for item in cart:
            amount += float(str(item.quantity)) * item.product.discounted_price

        tax_rate = float('0.48')
        total_tax = amount * tax_rate
        totalamount = amount + total_tax + float('10.00')

        return JsonResponse({
            'quantity': quantity,
            'amount': str(amount),
            'totalamount': str(totalamount)
        })

@login_required
def remove_cart(request):
    if request.method == 'GET':
        prod_id = request.GET.get('prod_id')
        try:
            cart_item = Cart.objects.get(Q(product=prod_id) & Q(user=request.user))
            cart_item.delete()

            amount = float('0.00')
            cart = Cart.objects.filter(user=request.user)
            for item in cart:
                amount += float(str(item.quantity)) * item.product.discounted_price

            tax_rate = float('0.48')
            total_tax = amount * tax_rate
            totalamount = amount + total_tax + float('10.00')

            return JsonResponse({
                'success': True,
                'amount': str(amount),
                'totalamount': str(totalamount)
            })
        except Cart.DoesNotExist:
            return JsonResponse({'success': False})


logger = logging.getLogger(__name__)

def clear_discount_session(request):
    """Helper function to clear discount related session data"""
    request.session.pop('discount_percentage', None)
    request.session.pop('discount_code', None)
    request.session.modified = True

def checkout_view(request):
    request.session['on_checkout'] = True
    context = {
        'form': DiscountCodeForm(),
    }
    return render(request, 'checkout.html', context)

@require_http_methods(["POST"])
def apply_discount(request):
    if request.method == 'POST':
        discount_code = request.POST.get('discount_code', '').strip()

        # Rate limiting
        cache_key = f'discount_attempts_{request.user.id}'
        attempts = cache.get(cache_key, 0)

        if attempts >= 5:  # Limit to 5 attempts per 15 minutes
            messages.error(request, 'Too many attempts. Please try again later.')
            return redirect('checkout')

        cache.set(cache_key, attempts + 1, 10)  # 15 minutes expiry

        try:
            discount = DiscountCode.objects.select_for_update().get(
                code=discount_code
            )

            # Get cart total
            cart_total = Decimal(request.session.get('cart_total', '0'))

            # Validate discount
            is_valid, message = discount.is_valid(cart_total)
            if not is_valid:
                messages.error(request, message)
                return redirect('checkout')

            # Apply discount
            discount.current_uses += 1
            discount.save()

            request.session['discount_percentage'] = float(discount.discount_percentage)
            request.session['discount_code'] = discount_code

            messages.success(
                request,
                f'Discount of {discount.discount_percentage}% applied!'
            )

            logger.info(
                f"Discount code {discount_code} applied successfully "
                f"for user {request.user.id}"
            )

        except DiscountCode.DoesNotExist:
            messages.error(request, 'Invalid discount code')
            logger.warning(
                f"Invalid discount code attempt: {discount_code} "
                f"by user {request.user.id}"
            )
        except Exception as e:
            messages.error(request, 'An error occurred. Please try again.')
            logger.error(
                f"Error applying discount code: {str(e)} "
                f"for user {request.user.id}"
            )

        return redirect('checkout')

@require_http_methods(["POST"])
@csrf_exempt
def remove_discount(request):
    if request.method == "POST":
        try:
            clear_discount_session(request)
            return JsonResponse({"success": True})
        except Exception as e:
            logger.error(f"Error removing discount: {str(e)}")
            return JsonResponse(
                {"success": False, "error": "Failed to remove discount"},
                status=500
            )
    return JsonResponse({"success": False}, status=400)

class checkout(View):
    def get(self, request):
        user = request.user
        add = Customer.objects.filter(user=user)
        cart_items = Cart.objects.filter(user=user)
        cart = Cart.objects.filter(user=user)

        amount = 0
        for p in cart:
            value = p.quantity * p.product.discounted_price
            amount += value

        gst = amount * 0.28
        cess = amount * 0.20
        total_tax = gst + cess

        totalamount = amount + total_tax + 10

        discount_percentage = request.session.get('discount_percentage', 0)

        if discount_percentage:
            discount_amount = totalamount * (discount_percentage / 100)
            totalamount -= discount_amount

        eth_amount = format(totalamount / 300000, '.5f')

        return render(request, 'app/payment.html', {
            'totalamount': totalamount,
            'amount': amount,
            'gst': gst,
            'cess': cess,
            'eth_amount': eth_amount,
            'discount_percentage': discount_percentage,
            'receiver_address': '0x53E1a568929C6D778C1e58D33A5395a76B92741F',
            **locals()
        })
@csrf_exempt
def process_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            transaction_hash = data.get('transactionHash')
            from_address = data.get('fromAddress')
            amount = data.get('amount')
            eth_amount = data.get('eth_amount', 0)
            user = request.user

            cart_items = Cart.objects.filter(user=user)
            if not cart_items.exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Cart is empty'
                }, status=400)


            order = Order.objects.create(
                user=user,
                customer=Customer.objects.filter(user=user).first(),
                total=sum(item.total_cost for item in cart_items),
                status='Accepted'
            )

            payment = CryptoPayment.objects.create(
                user=user,
                order=order,
                transaction_hash=transaction_hash,
                from_address=from_address,
                amount=Decimal(str(amount)),
                eth_amount=Decimal(str(eth_amount)),
                status='completed'
            )

            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    price=cart_item.product.discounted_price,
                    quantity=cart_item.quantity
                )

            cart_items.delete()

            return JsonResponse({
                'status': 'success',
                'message': 'Order processed successfully',
                'redirect_url': f'/order-success/{order.id}/'
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required
def order_success(request, order_id):
    user = request.user
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)
    payment = CryptoPayment.objects.filter(order=order).first()

    context = {
        'order': order,
        'order_items': order_items,
        'payment': payment,
        'customer': order.customer,
        'order_total': order.total,
    }

    subject = "Order Confirmation"
    send_order_email(user.email, subject, order, order_items)
    return render(request, 'app/order_success.html', context)

@login_required
def orders_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-id')
    orders_data = []
    for order in orders:
        order_items = OrderItem.objects.filter(order=order)
        payment = CryptoPayment.objects.filter(order=order).first()

        orders_data.append({
            'order': order,
            'items': order_items,
            'payment': payment,
            'total_items': sum(item.quantity for item in order_items)
        })

    paginator = Paginator(orders_data, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'orders_count': orders.count()
    }

    return render(request, 'app/order_success.html', context)


def place_order(request):
    customer = Customer.objects.get(user=request.user)
    order = Order.objects.create(
        user=request.user,
        customer=customer,
        total=order.total,
        status="Pending"
    )

    subject = "Order Confirmation"
    message = f"Hello {request.user.username},\n\nYour order (ID: {order.id}) has been placed successfully. Thank you for shopping with us!"

    send_order_email(request.user.email, subject, message)
