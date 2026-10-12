from typing import List, Optional
from pydantic import BaseModel, Field

class CompanySettingsModel(BaseModel):
    name: str = "Your Company Name"
    tagline: Optional[str] = "Commercial & Billing Solutions"
    address: str = "123 Business Street, City, State - Pin Code"
    phone: str = "+91 9876543210"
    email: str = "contact@example.com"
    gstin: str = "09AAAAA0000A1Z5"
    state: str = "Uttar Pradesh"
    state_code: str = "09"
    bank_name: str = "State Bank of India"
    branch: str = "Main Branch"
    account_no: str = "000000000000"
    ifsc: str = "SBIN0000000"
    upi_address: str = "merchant@upi"
    upi_name: str = "Your Company Name"
    invoice_prefix: str = "INV/"
    quotation_prefix: str = "QT/"
    challan_prefix: str = "DC/"
    terms_invoice: Optional[str] = "Thank you for your business!"
    terms_quotation: Optional[str] = ""
    terms_challan: Optional[str] = ""
    logo_url: Optional[str] = "/static/images/logo.png"

class CustomerModel(BaseModel):
    name: str
    contact_person: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    address: str
    city: Optional[str] = ""
    state: str = "Uttar Pradesh"
    state_code: str = "09"
    gstin: str = "N/A"

class ProductModel(BaseModel):
    name: str
    category: Optional[str] = "Medical Equipment"
    hsn_code: str = "9018"
    unit: str = "Pcs"
    default_rate: float = 0.0
    gst_rate: float = 5.0
    description: Optional[str] = ""
    image_url: Optional[str] = ""
    is_tax_inclusive: bool = False

class InvoiceItemModel(BaseModel):
    product_id: Optional[int] = None
    description: str
    hsn_code: str = "9018"
    qty: float = 1.0
    unit: str = "Pcs"
    rate: float
    gst_rate: float = 5.0
    amount: float
    item_type: str = "Goods"
    is_tax_inclusive: bool = False

class InvoiceCreateModel(BaseModel):
    invoice_no: Optional[str] = None
    invoice_date: str
    due_date: Optional[str] = ""
    customer_id: Optional[int] = None
    customer_name: str
    customer_address: str
    customer_gstin: str = "N/A"
    customer_state: str = "Uttar Pradesh"
    is_interstate: bool = False
    items: List[InvoiceItemModel]
    terms: Optional[str] = ""
    status: str = "Unpaid"
    invoice_type: str = "Goods"
    quotation_id: Optional[int] = None
    e_way_bill_no: Optional[str] = ""
    vehicle_no: Optional[str] = ""
    transporter_name: Optional[str] = ""
    po_no: Optional[str] = ""
    po_date: Optional[str] = ""

class QuotationItemModel(BaseModel):
    product_id: Optional[int] = None
    description: str
    hsn_code: str = "9018"
    qty: float = 1.0
    unit: str = "Pcs"
    rate: float
    gst_rate: float = 5.0
    amount: float
    product_image_url: Optional[str] = ""
    item_type: str = "Goods"
    is_tax_inclusive: bool = False

class QuotationCreateModel(BaseModel):
    quote_no: Optional[str] = None
    quote_date: str
    valid_until: Optional[str] = ""
    customer_id: Optional[int] = None
    customer_name: str
    customer_address: str
    customer_gstin: str = "N/A"
    customer_state: str = "Uttar Pradesh"
    is_interstate: bool = False
    items: List[QuotationItemModel]
    terms: Optional[str] = ""
    status: str = "Active"
    invoice_type: str = "Goods"

class DeliveryChallanItemModel(BaseModel):
    product_id: Optional[int] = None
    description: str
    hsn_code: str = "9018"
    qty: float = 1.0
    unit: str = "Pcs"
    approx_rate: float = 0.0
    approx_amount: float = 0.0

class DeliveryChallanCreateModel(BaseModel):
    challan_no: Optional[str] = None
    challan_date: str
    customer_id: Optional[int] = None
    customer_name: str
    customer_address: str
    customer_gstin: str = "N/A"
    customer_state: str = "Uttar Pradesh"
    reason_for_transport: str = "Supply for Installation & Commissioning"
    transporter_name: Optional[str] = ""
    vehicle_no: Optional[str] = ""
    e_way_bill_no: Optional[str] = ""
    terms: Optional[str] = ""
    status: str = "Dispatched"
    items: List[DeliveryChallanItemModel]

