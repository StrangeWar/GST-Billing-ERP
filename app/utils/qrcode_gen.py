import io
import base64
import urllib.parse
import qrcode
from qrcode.image.pil import PilImage

def generate_upi_qr_base64(
    vpa: str,
    payee_name: str,
    amount: float = None,
    transaction_ref: str = None
) -> str:
    """
    Generates a UPI payment intent QR code as a base64 Data URI string.
    e.g. data:image/png;base64,...
    Works 100% offline without external APIs.
    """
    params = {
        "pa": vpa,
        "pn": payee_name,
        "cu": "INR"
    }
    if amount is not None and amount > 0:
        params["am"] = f"{amount:.2f}"
    if transaction_ref:
        params["tr"] = transaction_ref
        params["tn"] = f"Payment for {transaction_ref}"
        
    query_str = urllib.parse.urlencode(params)
    upi_url = f"upi://pay?{query_str}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(upi_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"

if __name__ == "__main__":
    qr_data = generate_upi_qr_base64("company@upi", "Your Company Name", 50000.0, "INV/26-27/001")
    print("QR Code generated, length:", len(qr_data))
