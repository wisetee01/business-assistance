import openai
import json
import re
import uuid
from google import genai
from google.genai.types import Content, Part
from config import settings
from .memory import memory
from .actions import take_order, forward_order_to_company

openai.api_key = settings.openai_api_key
gemini_client = genai.Client(api_key=settings.gemini_api_key)

_part_from_text = Part.from_text

COMPLAINT_CONTACT_INFO = "For complaints --- contact at email wisetee01@gmail.com OR number 08012356678"

def get_ai_response(messages: list[dict], model_name="gpt-3.5-turbo"):
    """Attempts to get a response from OpenAI, falling back to Gemini if necessary."""
    gemini_contents = []
    for message in messages:
        role = "user" if message["role"] == "user" else "model" if message["role"] == "assistant" else "model"
        content_part = _part_from_text(text=message["content"])
        content_item = Content(role=role, parts=[content_part])
        gemini_contents.append(content_item)

    try:
        response = openai.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=200,
        )
        return response.choices.message.content.strip()

    except (openai.RateLimitError, openai.APIError) as e:
        print(f"OpenAI failed ({type(e).__name__}). Falling back to Gemini...")
        gemini_response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=gemini_contents,
            config=genai.types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=200,
            ),
        )
        return gemini_response.text.strip()

def generate_order_number():
    """Generates a unique order number using UUID."""
    return str(uuid.uuid4().int)[:10]


def process_user_input(user_input_data: dict, source: str = "Direct") -> str:
    """Handle user message and return bot response dynamically."""
    system_prompt = f"""
You are a professional business assistant taking orders. Collect all details (item, price, address, customer name, email, phone number, and payment method).
Available payment methods are PayPal, Paystack, and Bank Transfer.
Once a method is chosen, provide specific details (e.g., a link or account number . if its bank transfer bank details in .env should be detect and show it to customer).
After details are provided, the user will upload a payment proof via the website interface.
CRITICAL RULE: Immediately after the user uploads their proof (which the system handles in the backend), you must provide the final confirmation message with the order number. Do not ask any more questions.
"""
    messages = [{"role": "system", "content": system_prompt}]
    for h in memory.history:
        messages.append({"role": "user", "content": h["user"]})
        messages.append({"role": "assistant", "content": h["assistant"]})

    messages.append(user_input_data)
    reply = get_ai_response(messages)

    if "image_url" in user_input_data:
        
        item, price, customer_name, address, email, payment_method, phone_number = extract_entities_from_history(
            memory.history + [{"user": user_input_data["content"], "assistant": "Payment proof uploaded."}]
        )

        order_number = generate_order_number()

    
        take_order(
            item=item,
            customer_name=customer_name,
            address=address,
            email=email,
            payment_method=payment_method,
            source_website=source,
            price_override=price,
            phone_number=phone_number,
            order_number=order_number
        )

        
        forward_order_to_company(
            order_number=order_number,
            details={
                "item": item, "price": price, "customer_name": customer_name,
                "address": address, "email": email, "phone": phone_number,
                "payment_method": payment_method,
                "proof_url": user_input_data["image_url"]
            }
        )

        
        reply = f"Thank you! Your payment proof has been received. Your order number is **{order_number}**. The business owner will verify the payment shortly and process your order."

    
        reply += f"\n\n{COMPLAINT_CONTACT_INFO}"

    memory.add(user_input_data["content"], reply)
    return reply

def extract_entities_from_history(history_list):
    """A helper function to dynamically pull data from the conversation history, including phone number."""
    full_text = " ".join([msg["user"] + " " + msg["assistant"] for msg in history_list]).lower()

    item, price, customer_name, address, email, payment_method, phone_number = None, None, None, None, None, None, None

    phone_match = re.search(r"(\+?\d{1,3}[-.\s\(\)]*?\d{3,4}[-.\s\(\)]*?\d{4,9})", full_text)
    if phone_match: phone_number = phone_match.group(0).strip()

    price_match = re.search(r"[$€]?\s*(\d+(\.\d{1,2})?)", full_text)
    if price_match:
        try:
            price = float(price_match.group(1))
        except ValueError: pass

    if "deliver to" in full_text: address = " ".join(full_text.split("deliver to")[-1].split()[:3])
    elif "my address is" in full_text: address = " ".join(full_text.split("my address is")[-1].split()[:3])

    email_match = re.search(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b", full_text)
    if email_match: email = email_match.group(0)

    if any(w in full_text for w in ["bank", "transfer", "fidelity"]): payment_method = "bank"
    elif "paystack" in full_text: payment_method = "paystack"
    elif "paypal" in full_text: payment_method = "paypal"

    if "pizza" in full_text: item = "Pizza"
    elif "laptop" in full_text: item = "Laptop"

    return item, price, customer_name, address, email, payment_method, phone_number
