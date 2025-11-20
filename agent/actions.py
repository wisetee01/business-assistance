from pymongo import MongoClient
from config import settings
from datetime import datetime
import stripe
import sendgrid
from sendgrid.helpers.mail import Mail
import paypalrestsdk
from paystackapi.transaction import Transaction
from paystackapi import Paystack

client = MongoClient(settings.mongodb_uri)
db = client[settings.db_name]
orders_collection = db[settings.orders_collection]

# Stripe Initialization
if settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key
    print("Stripe functionality enabled.")
else:
    print("Warning: Stripe API key is missing. Stripe functionality disabled.")
    stripe.api_key = None # Explicitly set to None for clearer handling

# PayPal Initialization
if settings.paypal_client_id and settings.paypal_secret:
    paypalrestsdk.configure({
        "mode": "sandbox",  # Change to "live" when production is ready
        "client_id": settings.paypal_client_id,
        "client_secret": settings.paypal_secret
    })
    print("PayPal functionality enabled.")
else:
    print("Warning: PayPal credentials missing. PayPal functionality disabled.")
    paypalrestsdk.configure({"mode": "sandbox", "client_id": None, "client_secret": None}) 


if settings.paystack_secret_key:
    Paystack(secret_key=settings.paystack_secret_key)
    print("Paystack functionality enabled.")
else:
    print("Warning: Paystack secret key is missing. Paystack functionality disabled.")

# SendGrid Initialization
sg = None
if settings.sendgrid_api_key:
    sg = sendgrid.SendGridAPIClient(settings.sendgrid_api_key)
    print("SendGrid functionality enabled.")
else:
    print("Warning: SendGrid API key is missing. Email alerts disabled.")


def send_email_alert(order: dict, source: str, proof_url: str = None) -> None:
    """Send new order alert to business owner, including proof URL."""

    if sg is None:
        print("Email skipped: SendGrid client not configured.")
        return

    html_content = f"""
    <h3>New Order!</h3>
    <p><strong>Order Number:</strong> {order['order_number']}</p>
    <p><strong>Item:</strong> {order['item']}</p>
    <p><strong>Customer:</strong> {order['customer']}</p>
    <p><strong>Phone:</strong> {order['phone_number']}</p>
    <p><strong>Email:</strong> {order['email']}</p>
    <p><strong>Price:</strong> ${order['price']}</p>
    <p><strong>Delivery:</strong> {order['delivery_time']}</p>
    <p><strong>Payment:</strong> {order['payment_method'].title()}</p>
    <p><strong>Source:</strong> {source}</p>
    """
    
    if proof_url:
        html_content += f'<p><strong>Payment Proof:</strong> <a href="{proof_url}">View Proof Image</a></p>'
        subject = f"Order CONFIRMED: {order['order_number']} from {source}"
    else:
        subject = f"New PENDING Order: {order['order_number']} from {source}"

    message = Mail(
        from_email=settings.from_email,
        to_emails=settings.owner_email,
        subject=subject,
        html_content=html_content
    )
    try:
        sg.send(message)
    except Exception as e:
        print(f"Email failed: {e}")


def create_stripe_link(amount: int, order_number: str) -> str:
    """Generate Stripe payment URL."""
    if stripe.api_key is None:
        return None  

    amount_cents = int(amount * 100)
    session = stripe.checkout.sessions.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': f'Order {order_number}'},
                'unit_amount': amount_cents,
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url='https://yourbusiness.com/success',
        cancel_url='https://yourbusiness.com/cancel',
        metadata={'order_number': order_number}
    )
    return session.url


def create_paystack_link(amount: int, email: str, order_number: str) -> str:
    """Generate Paystack payment URL."""
    # Check for the correct key (Paystack, not PayPal)
    if settings.paystack_secret_key is None:
        print("Paystack not configured.")
        return None

    

    amount_kobo = int(amount * 100)
    try:
        response = Transaction.initialize(
            amount=amount_kobo,
            email=email or "customer@example.com",
            reference=order_number,
            callback_url="https://yourbusiness.com/verify"
        )
        return response['data']['authorization_url']
    except Exception as e:
        print(f"Paystack link creation failed: {e}")
        return None

def create_paypal_link(amount: int, order_number: str) -> str:
    """Generate PayPal payment URL."""
    if not paypalrestsdk.api.Configuration.client_id: 
        print("PayPal not configured.")
        return None

    amount_str = f"{amount:.2f}"
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {"payment_method": "paypal"},
        "redirect_urls": {
            "return_url": "https://yourbusiness.com/paypal-success",
            "cancel_url": "https://yourbusiness.com/cancel"
        },
        "transactions": [{
            "item_list": {"items": [{"name": order_number, "price": amount_str, "currency": "USD", "quantity": 1}]},
            "amount": {"total": amount_str, "currency": "USD"},
            "description": f"Order {order_number}"
        }]
    })
    if payment.create():
        return [link.href for link in payment.links if link.rel == "approval_url"][0]
    return None


def take_order(
    item: str,
    customer_name: str,
    address: str,
    email: str = "N/A",
    payment_method: str = "auto",
    source_website: str = "Unknown",
    price_override: int = None,
    phone_number: str = "N/A",
    order_number: str = None 
 ) -> str:
    """Save order and return payment instructions."""

    if item is None: return "I need to know what you would like to order before I can proceed."
    if customer_name is None or address is None: return "To finalize your order, I need your name and delivery address."
    if phone_number is None or phone_number == "N/A": return "Please provide a valid phone number for delivery."

    order_id = order_number if order_number is not None else f"TEMP-{datetime.utcnow().timestamp()}"

    price = price_override if price_override is not None else (150 if "premium" in item.lower() else 99)
    delivery_time = "2 hours" if "urgent" in item.lower() else "tomorrow 10 AM"
    
    order = {
        "order_number": order_id, 
        "item": item,
        "customer": customer_name,
        "email": email,
        "phone_number": phone_number,
        "address": address,
        "price": price,
        "delivery_time": delivery_time,
        "status": "pending_payment", 
        "payment_method": payment_method,
        "source_website": source_website,
        "created_at": datetime.utcnow()
    }
    
    orders_collection.insert_one(order)
    
    
    if payment_method == "auto":
        if any(x in source_website.lower() for x in ["ng", "nigeria", "lagos", "abuja"]) or "paystack" in email.lower():
            payment_method = "paystack"
        elif "paypal" in payment_method.lower():
            payment_method = "paypal"
        else:
            payment_method = "stripe"

    
    if payment_method == "bank":
        return f"""
ORDER PLACED!
Order Number: {order_id}
Item: {item}
Price: ${price}
Delivery: {delivery_time}
Phone: {phone_number}

Pay via Bank Transfer:
Bank: {settings.bank_name}
Account Name: {settings.account_name}
Account Number: {settings.account_number}

Please use the upload button below to send your payment proof.
        """.strip()

    elif payment_method == "paystack":
        link = create_paystack_link(price, email, order_id)
        return f"Pay with Paystack (Card/Bank/Mobile): {link or 'Error'}. Please upload proof after paying."

    elif payment_method == "paypal":
        link = create_paypal_link(price, order_id)
        return f"Pay with PayPal: {link or 'Error'}. Please upload proof after paying."

    else:
        link = create_stripe_link(price, order_id)
        return f"Pay with Card (Global): {link}. Please upload proof after paying."


def forward_order_to_company(order_number: str, details: dict):
    """
    Updates the order status and sends the final confirmation email to the owner
    after payment proof is uploaded.
    """
    
    orders_collection.update_one(
        {"order_number": order_number},
        {"$set": {"status": "payment_verified_pending_shipping", "proof_url": details.get("proof_url")}}
    )

    
    order_summary = {
        "order_number": order_number,
        "item": details.get("item"),
        "customer": details.get("customer_name"),
        "phone_number": details.get("phone"),
        "email": details.get("email"),
        "price": details.get("price"),
        "delivery_time": "N/A (check DB)",
        "payment_method": details.get("payment_method"),
    }
    
    
    send_email_alert(order_summary, details.get("source_website", "Unknown"), proof_url=details.get("proof_url"))
    print(f"Order {order_number} finalized and forwarded to company.")
