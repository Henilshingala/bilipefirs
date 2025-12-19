import base64
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import format_html
from io import BytesIO
from django.core.files.storage import default_storage

def encode_image_base64(image_path):
    try:
        with default_storage.open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print("Error encoding image:", e)
        return None

def send_order_email(user_email, subject, order, order_items):
    encoded_images = {}
    for item in order_items:
        if item.product.product_image:
            image_path = item.product.product_image.name
            encoded_images[item.product.id] = encode_image_base64(image_path)


    message = render_to_string('app/order_email_template.html', {
        'user': order.user,
        'order': order,
        'order_items': order_items,
        'encoded_images': encoded_images,
    })

    send_mail(
        subject,
        '',
        settings.EMAIL_HOST_USER,
        [user_email],
        fail_silently=False,
        html_message=message
    )
