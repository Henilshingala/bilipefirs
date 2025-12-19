from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from .forms import MyPasswordChangeForm
from .views import get_pincode_details 
urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    path('contact/success/', views.contact_success, name='contact_success'),
    path('customer-registration/', views.CustomerRegistrationView.as_view(), name='signup'), 
    path('login/', views.LoginView.as_view(), name='login'),  
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('get-pincode-details/', get_pincode_details, name='get_pincode_details'),
    path('address/', views.AddressListView.as_view(), name='address'),
    path('address/update/<int:pk>/', views.UpdateAddressView.as_view(), name='updateAddress'),
    path('changepassword/', auth_views.PasswordChangeView.as_view(
        template_name='app/changepassword.html',
        form_class=MyPasswordChangeForm,
        success_url='/passwordchangedone/'), name='passwordchange'),
    path('passwordchangedone/', auth_views.PasswordChangeDoneView.as_view(
        template_name='app/passwordchangedone.html'), name='passwordchangedone'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('category/<str:val>/', views.CategoryView.as_view(), name='category'),
    path('product-detail/<int:pk>/', views.ProductDetail.as_view(), name='product-detail'),
    path('cart/', views.show_cart, name='showcart'),
    path('add-to-cart/', views.add_to_cart, name='add-to-cart'),
    path('pluscart/', views.plus_cart, name='pluscart'),
    path('minuscart/', views.minus_cart, name='minuscart'),
    path('removecart/', views.remove_cart, name='removecart'),
    path('apply_discount/', views.apply_discount, name='apply_discount'),
    path('remove_discount/', views.remove_discount, name='remove_discount'),
    path('checkout/', views.checkout.as_view(), name='checkout'),
    path('orders/', views.orders_list, name='orders'),
    path('process-payment/', views.process_payment, name='process_payment'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
