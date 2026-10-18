"""Provider-neutral payment verification primitives. No provider success is trusted from the browser."""
import hashlib,hmac,json
class PaymentProviderNotConfigured(RuntimeError):pass
def verify_razorpay_payment(order_id,payment_id,signature,secret):
    if not secret:raise PaymentProviderNotConfigured('Live payment provider is not configured')
    expected=hmac.new(secret.encode(),f'{order_id}|{payment_id}'.encode(),hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected,signature)
def verify_razorpay_webhook(payload,signature,secret):
    if not secret:raise PaymentProviderNotConfigured('Live payment provider is not configured')
    return hmac.compare_digest(hmac.new(secret.encode(),payload,hashlib.sha256).hexdigest(),signature)
def canonical_payload_hash(payload):return hashlib.sha256(payload if isinstance(payload,bytes) else json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
