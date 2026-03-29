import requests
from django.template.loader import render_to_string

def send_otp_email(otp_code, email):
    webhook_url = "https://rabeehasan.online/n8n/webhook/30657344-665f-4bb8-a7ad-a8fa5f87c38f"
    
    subject = 'رمز التحقق من بريدك الإلكتروني'
    html_message = render_to_string('emails/email_code.html', {
        'otp_code': otp_code
    })
    
    payload = {
        "email": email,
        "subject": subject,
        "body": html_message
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Error sending email via n8n: {e}")


def send_new_product_email(store_name, recipients):
    webhook_url = "https://rabeehasan.online/n8n/webhook/30657344-665f-4bb8-a7ad-a8fa5f87c38f"

    subject = f"منتجات جديدة في متجر {store_name}"
    html_message = render_to_string('emails/new_product.html', {
        'store_name': store_name,
    })

    if not recipients:
        return {'sent': 0, 'failed': 0}

    sent = 0
    failed = 0

    for email in recipients:
        payload = {
            "email": email,
            "subject": subject,
            "body": html_message
        }

        try:
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            sent += 1
        except Exception as e:
            failed += 1
            print(f"Error sending new product email to {email}: {e}")

    return {'sent': sent, 'failed': failed}


def send_coupon_email(coupon, customer_name, email, store_name):
    webhook_url = "https://rabeehasan.online/n8n/webhook/30657344-665f-4bb8-a7ad-a8fa5f87c38f"

    subject = f"كوبون مكافأة من متجر {store_name}"
    html_message = render_to_string('emails/coupon.html', {
        'coupon': coupon,
        'customer_name': customer_name,
        'store_name': store_name,
    })

    payload = {
        "email": email,
        "subject": subject,
        "body": html_message
    }

    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error sending coupon email to {email}: {e}")
        return False


def send_order_confirmed_email(order, store_name, vendor_email):
    webhook_url = "https://rabeehasan.online/n8n/webhook/30657344-665f-4bb8-a7ad-a8fa5f87c38f"

    subject = f"تم تأكيد وشحن طلبك من متجر {store_name}"
    html_message = render_to_string('emails/order_confirmed.html', {
        'order': order,
        'store_name': store_name,
        'vendor_email': vendor_email,
    })

    payload = {
        "email": order.email,
        "subject": subject,
        "body": html_message
    }

    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error sending order confirmed email to {order.email}: {e}")
        return False