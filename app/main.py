import os
import shutil
import sqlite3
import datetime
from pathlib import Path
from typing import Optional, List

import io
import csv
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Request, Response
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.database import (
    get_db, init_db, generate_next_invoice_number, generate_next_quote_number,
    generate_next_challan_number, get_financial_year
)
from app.models import (
    CompanySettingsModel, CustomerModel, ProductModel,
    InvoiceCreateModel, QuotationCreateModel,
    DeliveryChallanCreateModel, DeliveryChallanItemModel
)
from app.utils.number_to_words import indian_number_to_words
from app.utils.qrcode_gen import generate_upi_qr_base64
from app.utils.backup import create_backup, list_backups, restore_backup, BACKUP_DIR

app = FastAPI(title="Open Business ERP - Billing & Quotation System")

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
def on_startup():
    init_db()
    # Create an auto-backup snapshot on startup
    create_backup(label="startup")

@app.get("/manifest.json")
def get_manifest():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM company_settings WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    settings = dict(row or {})
    name = settings.get("name", "Open Business ERP")
    tagline = settings.get("tagline", "Billing & Quotation System")
    logo = settings.get("logo_url") or "/static/images/logo.png"
    return {
        "name": f"{name} ERP",
        "short_name": name[:15],
        "description": tagline or "Billing & ERP System",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0f172a",
        "theme_color": "#2563eb",
        "icons": [
            {
                "src": logo,
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": logo,
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }

@app.get("/", response_class=FileResponse)
def serve_index():
    return FileResponse("app/static/index.html")

# ----------------- DASHBOARD API -----------------

@app.get("/api/dashboard")
def get_dashboard_data():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(grand_total), 0) FROM invoices")
    inv_count, total_sales = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*) FROM invoices WHERE status = 'Unpaid'")
    unpaid_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM quotations")
    quote_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM customers")
    customer_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]
    
    # Recent 5 invoices
    cursor.execute("""
        SELECT id, invoice_no, invoice_date, customer_name, grand_total, status 
        FROM invoices ORDER BY id DESC LIMIT 5
    """)
    recent_invoices = [dict(r) for r in cursor.fetchall()]
    
    # Recent 5 quotations
    cursor.execute("""
        SELECT id, quote_no, quote_date, customer_name, grand_total, status 
        FROM quotations ORDER BY id DESC LIMIT 5
    """)
    recent_quotes = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    return {
        "total_sales": round(total_sales, 2),
        "invoice_count": inv_count,
        "unpaid_count": unpaid_count,
        "quote_count": quote_count,
        "customer_count": customer_count,
        "product_count": product_count,
        "recent_invoices": recent_invoices,
        "recent_quotes": recent_quotes
    }

# ----------------- COMPANY SETTINGS API -----------------

@app.get("/api/settings")
def get_settings():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM company_settings WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Settings not found")
    return dict(row)

@app.put("/api/settings")
def update_settings(settings: CompanySettingsModel):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE company_settings SET
            name = ?, tagline = ?, address = ?, phone = ?, email = ?,
            gstin = ?, state = ?, state_code = ?, bank_name = ?, branch = ?,
            account_no = ?, ifsc = ?, upi_address = ?, upi_name = ?,
            invoice_prefix = ?, quotation_prefix = ?, challan_prefix = ?,
            terms_invoice = ?, terms_quotation = ?, terms_challan = ?,
            logo_url = ?
        WHERE id = 1
    """, (
        settings.name, settings.tagline or "", settings.address, settings.phone, settings.email,
        settings.gstin, settings.state, settings.state_code, settings.bank_name, settings.branch,
        settings.account_no, settings.ifsc, settings.upi_address, settings.upi_name,
        settings.invoice_prefix, settings.quotation_prefix, settings.challan_prefix,
        settings.terms_invoice or "", settings.terms_quotation or "", settings.terms_challan or "",
        settings.logo_url or "/static/images/logo.png"
    ))
    conn.commit()
    conn.close()
    return {"message": "Company settings updated successfully"}

# ----------------- CUSTOMERS API -----------------

@app.get("/api/customers")
def get_customers():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers ORDER BY name ASC")
    customers = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return customers

@app.post("/api/customers")
def create_customer(customer: CustomerModel):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO customers (name, contact_person, phone, email, address, city, state, state_code, gstin)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        customer.name, customer.contact_person or "", customer.phone or "", customer.email or "",
        customer.address, customer.city or "", customer.state, customer.state_code, customer.gstin
    ))
    conn.commit()
    cust_id = cursor.lastrowid
    conn.close()
    return {"id": cust_id, "message": "Customer added successfully"}

@app.put("/api/customers/{id}")
def update_customer(id: int, customer: CustomerModel):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE customers SET
            name = ?, contact_person = ?, phone = ?, email = ?,
            address = ?, city = ?, state = ?, state_code = ?, gstin = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        customer.name, customer.contact_person or "", customer.phone or "", customer.email or "",
        customer.address, customer.city or "", customer.state, customer.state_code, customer.gstin, id
    ))
    conn.commit()
    conn.close()
    return {"message": "Customer updated successfully"}

@app.delete("/api/customers/{id}")
def delete_customer(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customers WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"message": "Customer deleted successfully"}

# ----------------- PRODUCTS API -----------------

@app.get("/api/products")
def get_products():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products ORDER BY name ASC")
    products = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return products

@app.post("/api/products")
def create_product(product: ProductModel):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products (name, category, hsn_code, unit, default_rate, gst_rate, description, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        product.name, product.category or "Medical Equipment", product.hsn_code,
        product.unit, product.default_rate, product.gst_rate,
        product.description or "", product.image_url or ""
    ))
    conn.commit()
    prod_id = cursor.lastrowid
    conn.close()
    return {"id": prod_id, "message": "Product added successfully"}

@app.put("/api/products/{id}")
def update_product(id: int, product: ProductModel):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE products SET
            name = ?, category = ?, hsn_code = ?, unit = ?,
            default_rate = ?, gst_rate = ?, description = ?, image_url = ?
        WHERE id = ?
    """, (
        product.name, product.category or "Medical Equipment", product.hsn_code,
        product.unit, product.default_rate, product.gst_rate,
        product.description or "", product.image_url or "", id
    ))
    conn.commit()
    conn.close()
    return {"message": "Product updated successfully"}

@app.delete("/api/products/{id}")
def delete_product(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"message": "Product deleted successfully"}

@app.post("/api/products/upload-image")
async def upload_product_image(file: UploadFile = File(...)):
    uploads_dir = Path("app/static/images/products")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"upload_{int(datetime.datetime.now().timestamp())}_{file.filename}"
    filepath = uploads_dir / filename
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"image_url": f"/static/images/products/{filename}"}

# ----------------- INVOICES API -----------------

@app.get("/api/invoices/next-number")
def get_next_invoice_number():
    conn = get_db()
    next_no = generate_next_invoice_number(conn)
    conn.close()
    return {"next_invoice_no": next_no}

@app.get("/api/invoices")
def get_invoices():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM invoices ORDER BY id DESC")
    invoices = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return invoices

@app.get("/api/invoices/{id}")
def get_invoice_detail(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM invoices WHERE id = ?", (id,))
    inv = cursor.fetchone()
    if not inv:
        conn.close()
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    cursor.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (id,))
    items = [dict(r) for r in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM company_settings WHERE id = 1")
    settings = dict(cursor.fetchone())
    
    conn.close()
    
    inv_dict = dict(inv)
    inv_dict["items"] = items
    inv_dict["settings"] = settings
    return inv_dict

@app.post("/api/invoices")
def create_invoice(invoice: InvoiceCreateModel):
    conn = get_db()
    cursor = conn.cursor()
    
    fy = get_financial_year()
    inv_no = invoice.invoice_no or generate_next_invoice_number(conn)
    
    subtotal = sum(item.amount for item in invoice.items)
    
    cursor.execute("SELECT state FROM company_settings WHERE id = 1")
    comp_state = cursor.fetchone()[0]
    is_interstate = (invoice.customer_state.strip().lower() != comp_state.strip().lower())
    
    cgst_amount = 0.0
    sgst_amount = 0.0
    igst_amount = 0.0
    
    for item in invoice.items:
        tax_val = item.amount * (item.gst_rate / 100.0)
        if is_interstate:
            igst_amount += tax_val
        else:
            cgst_amount += tax_val / 2.0
            sgst_amount += tax_val / 2.0
            
    subtotal = round(subtotal, 2)
    cgst_amount = round(cgst_amount, 2)
    sgst_amount = round(sgst_amount, 2)
    igst_amount = round(igst_amount, 2)
    grand_total = round(subtotal + cgst_amount + sgst_amount + igst_amount, 2)
    
    amount_words = indian_number_to_words(grand_total)
    
    cursor.execute("""
        INSERT INTO invoices (
            invoice_no, financial_year, invoice_date, due_date, customer_id, customer_name,
            customer_address, customer_gstin, customer_state, is_interstate,
            subtotal, cgst_amount, sgst_amount, igst_amount, grand_total, amount_in_words,
            terms, status, invoice_type, quotation_id,
            e_way_bill_no, vehicle_no, transporter_name, po_no, po_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        inv_no, fy, invoice.invoice_date, invoice.due_date or "",
        invoice.customer_id, invoice.customer_name, invoice.customer_address,
        invoice.customer_gstin, invoice.customer_state, 1 if is_interstate else 0,
        subtotal, cgst_amount, sgst_amount, igst_amount, grand_total, amount_words,
        invoice.terms or "Thank you for your business!", invoice.status,
        invoice.invoice_type, invoice.quotation_id,
        invoice.e_way_bill_no or "", invoice.vehicle_no or "",
        invoice.transporter_name or "", invoice.po_no or "", invoice.po_date or ""
    ))
    inv_id = cursor.lastrowid
    
    for item in invoice.items:
        cursor.execute("""
            INSERT INTO invoice_items (
                invoice_id, product_id, description, hsn_code, qty, unit, rate, gst_rate, amount, item_type, is_tax_inclusive
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            inv_id, item.product_id, item.description, item.hsn_code,
            item.qty, item.unit, item.rate, item.gst_rate, item.amount,
            item.item_type, 1 if item.is_tax_inclusive else 0
        ))
        
    conn.commit()
    conn.close()
    
    create_backup(label="invoice_created")
    return {"id": inv_id, "invoice_no": inv_no, "message": "Invoice created successfully"}

@app.put("/api/invoices/{id}")
def update_invoice(id: int, invoice: InvoiceCreateModel):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT invoice_no FROM invoices WHERE id = ?", (id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    inv_no = invoice.invoice_no or existing["invoice_no"]
    subtotal = sum(item.amount for item in invoice.items)
    
    cursor.execute("SELECT state FROM company_settings WHERE id = 1")
    comp_state = cursor.fetchone()[0]
    is_interstate = (invoice.customer_state.strip().lower() != comp_state.strip().lower())
    
    cgst_amount = 0.0
    sgst_amount = 0.0
    igst_amount = 0.0
    
    for item in invoice.items:
        tax_val = item.amount * (item.gst_rate / 100.0)
        if is_interstate:
            igst_amount += tax_val
        else:
            cgst_amount += tax_val / 2.0
            sgst_amount += tax_val / 2.0
            
    subtotal = round(subtotal, 2)
    cgst_amount = round(cgst_amount, 2)
    sgst_amount = round(sgst_amount, 2)
    igst_amount = round(igst_amount, 2)
    grand_total = round(subtotal + cgst_amount + sgst_amount + igst_amount, 2)
    amount_words = indian_number_to_words(grand_total)
    
    cursor.execute("""
        UPDATE invoices SET
            invoice_no = ?, invoice_date = ?, due_date = ?, customer_id = ?,
            customer_name = ?, customer_address = ?, customer_gstin = ?,
            customer_state = ?, is_interstate = ?, subtotal = ?, cgst_amount = ?,
            sgst_amount = ?, igst_amount = ?, grand_total = ?, amount_in_words = ?,
            terms = ?, status = ?, invoice_type = ?,
            e_way_bill_no = ?, vehicle_no = ?, transporter_name = ?, po_no = ?, po_date = ?
        WHERE id = ?
    """, (
        inv_no, invoice.invoice_date, invoice.due_date or "", invoice.customer_id,
        invoice.customer_name, invoice.customer_address, invoice.customer_gstin,
        invoice.customer_state, 1 if is_interstate else 0, subtotal, cgst_amount,
        sgst_amount, igst_amount, grand_total, amount_words,
        invoice.terms or "Thank you for your business!", invoice.status,
        invoice.invoice_type,
        invoice.e_way_bill_no or "", invoice.vehicle_no or "",
        invoice.transporter_name or "", invoice.po_no or "", invoice.po_date or "",
        id
    ))
    
    # Replace items
    cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (id,))
    for item in invoice.items:
        cursor.execute("""
            INSERT INTO invoice_items (
                invoice_id, product_id, description, hsn_code, qty, unit, rate, gst_rate, amount, item_type, is_tax_inclusive
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            id, item.product_id, item.description, item.hsn_code,
            item.qty, item.unit, item.rate, item.gst_rate, item.amount,
            item.item_type, 1 if item.is_tax_inclusive else 0
        ))
        
    conn.commit()
    conn.close()
    
    create_backup(label="invoice_updated")
    return {"id": id, "invoice_no": inv_no, "message": "Invoice updated successfully"}

@app.put("/api/invoices/{id}/status")
def update_invoice_status(id: int, status: str = Form(...)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE invoices SET status = ? WHERE id = ?", (status, id))
    conn.commit()
    conn.close()
    return {"message": "Invoice status updated"}

@app.delete("/api/invoices/{id}")
def delete_invoice(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (id,))
    cursor.execute("DELETE FROM invoices WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"message": "Invoice deleted successfully"}

# ----------------- QUOTATIONS API -----------------

@app.get("/api/quotations/next-number")
def get_next_quote_number():
    conn = get_db()
    next_no = generate_next_quote_number(conn)
    conn.close()
    return {"next_quote_no": next_no}

@app.get("/api/quotations")
def get_quotations():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quotations ORDER BY id DESC")
    quotes = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return quotes

@app.get("/api/quotations/{id}")
def get_quotation_detail(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quotations WHERE id = ?", (id,))
    quote = cursor.fetchone()
    if not quote:
        conn.close()
        raise HTTPException(status_code=404, detail="Quotation not found")
        
    cursor.execute("SELECT * FROM quotation_items WHERE quotation_id = ?", (id,))
    items = [dict(r) for r in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM company_settings WHERE id = 1")
    settings = dict(cursor.fetchone())
    
    conn.close()
    
    q_dict = dict(quote)
    q_dict["items"] = items
    q_dict["settings"] = settings
    return q_dict

@app.post("/api/quotations")
def create_quotation(quote: QuotationCreateModel):
    conn = get_db()
    cursor = conn.cursor()
    
    fy = get_financial_year()
    quote_no = quote.quote_no or generate_next_quote_number(conn)
    
    subtotal = sum(item.amount for item in quote.items)
    
    cursor.execute("SELECT state FROM company_settings WHERE id = 1")
    comp_state = cursor.fetchone()[0]
    is_interstate = (quote.customer_state.strip().lower() != comp_state.strip().lower())
    
    cgst_amount = 0.0
    sgst_amount = 0.0
    igst_amount = 0.0
    
    for item in quote.items:
        tax_val = item.amount * (item.gst_rate / 100.0)
        if is_interstate:
            igst_amount += tax_val
        else:
            cgst_amount += tax_val / 2.0
            sgst_amount += tax_val / 2.0
            
    subtotal = round(subtotal, 2)
    cgst_amount = round(cgst_amount, 2)
    sgst_amount = round(sgst_amount, 2)
    igst_amount = round(igst_amount, 2)
    grand_total = round(subtotal + cgst_amount + sgst_amount + igst_amount, 2)
    
    amount_words = indian_number_to_words(grand_total)
    
    cursor.execute("""
        INSERT INTO quotations (
            quote_no, financial_year, quote_date, valid_until, customer_id, customer_name,
            customer_address, customer_gstin, customer_state, is_interstate,
            subtotal, cgst_amount, sgst_amount, igst_amount, grand_total, amount_in_words,
            terms, status, invoice_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        quote_no, fy, quote.quote_date, quote.valid_until or "",
        quote.customer_id, quote.customer_name, quote.customer_address,
        quote.customer_gstin, quote.customer_state, 1 if is_interstate else 0,
        subtotal, cgst_amount, sgst_amount, igst_amount, grand_total, amount_words,
        quote.terms or "", quote.status, quote.invoice_type
    ))
    q_id = cursor.lastrowid
    
    for item in quote.items:
        cursor.execute("""
            INSERT INTO quotation_items (
                quotation_id, product_id, description, hsn_code, qty, unit, rate, gst_rate, amount,
                product_image_url, item_type, is_tax_inclusive
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            q_id, item.product_id, item.description, item.hsn_code,
            item.qty, item.unit, item.rate, item.gst_rate, item.amount,
            item.product_image_url or "", item.item_type, 1 if item.is_tax_inclusive else 0
        ))
        
    conn.commit()
    conn.close()
    
    create_backup(label="quote_created")
    return {"id": q_id, "quote_no": quote_no, "message": "Quotation created successfully"}

@app.put("/api/quotations/{id}")
def update_quotation(id: int, quote: QuotationCreateModel):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT quote_no FROM quotations WHERE id = ?", (id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Quotation not found")
        
    quote_no = quote.quote_no or existing["quote_no"]
    subtotal = sum(item.amount for item in quote.items)
    
    cursor.execute("SELECT state FROM company_settings WHERE id = 1")
    comp_state = cursor.fetchone()[0]
    is_interstate = (quote.customer_state.strip().lower() != comp_state.strip().lower())
    
    cgst_amount = 0.0
    sgst_amount = 0.0
    igst_amount = 0.0
    
    for item in quote.items:
        tax_val = item.amount * (item.gst_rate / 100.0)
        if is_interstate:
            igst_amount += tax_val
        else:
            cgst_amount += tax_val / 2.0
            sgst_amount += tax_val / 2.0
            
    subtotal = round(subtotal, 2)
    cgst_amount = round(cgst_amount, 2)
    sgst_amount = round(sgst_amount, 2)
    igst_amount = round(igst_amount, 2)
    grand_total = round(subtotal + cgst_amount + sgst_amount + igst_amount, 2)
    amount_words = indian_number_to_words(grand_total)
    
    cursor.execute("""
        UPDATE quotations SET
            quote_no = ?, quote_date = ?, valid_until = ?, customer_id = ?,
            customer_name = ?, customer_address = ?, customer_gstin = ?,
            customer_state = ?, is_interstate = ?, subtotal = ?, cgst_amount = ?,
            sgst_amount = ?, igst_amount = ?, grand_total = ?, amount_in_words = ?,
            terms = ?, status = ?, invoice_type = ?
        WHERE id = ?
    """, (
        quote_no, quote.quote_date, quote.valid_until or "", quote.customer_id,
        quote.customer_name, quote.customer_address, quote.customer_gstin,
        quote.customer_state, 1 if is_interstate else 0, subtotal, cgst_amount,
        sgst_amount, igst_amount, grand_total, amount_words,
        quote.terms or "", quote.status, quote.invoice_type, id
    ))
    
    cursor.execute("DELETE FROM quotation_items WHERE quotation_id = ?", (id,))
    for item in quote.items:
        cursor.execute("""
            INSERT INTO quotation_items (
                quotation_id, product_id, description, hsn_code, qty, unit, rate, gst_rate, amount,
                product_image_url, item_type, is_tax_inclusive
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            id, item.product_id, item.description, item.hsn_code,
            item.qty, item.unit, item.rate, item.gst_rate, item.amount,
            item.product_image_url or "", item.item_type, 1 if item.is_tax_inclusive else 0
        ))
        
    conn.commit()
    conn.close()
    
    create_backup(label="quote_updated")
    return {"id": id, "quote_no": quote_no, "message": "Quotation updated successfully"}

@app.post("/api/settings/upload-logo")
async def upload_company_logo(file: UploadFile = File(...)):
    img_dir = Path("app/static/images")
    img_dir.mkdir(parents=True, exist_ok=True)
    logo_path = img_dir / "logo.png"
    
    content = await file.read()
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(content))
        img.save(logo_path, format="PNG")
    except Exception:
        with open(logo_path, "wb") as buffer:
            buffer.write(content)
            
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE company_settings SET logo_url = '/static/images/logo.png' WHERE id = 1")
    conn.commit()
    conn.close()
    
    return {"message": "Company logo updated successfully", "logo_url": "/static/images/logo.png"}

@app.post("/api/settings/reset-logo")
def reset_company_logo():
    img_dir = Path("app/static/images")
    default_logo = img_dir / "default_logo.png"
    logo_path = img_dir / "logo.png"
    if default_logo.exists():
        shutil.copyfile(default_logo, logo_path)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE company_settings SET logo_url = '/static/images/logo.png' WHERE id = 1")
    conn.commit()
    conn.close()
    return {"message": "Logo reset to default successfully", "logo_url": "/static/images/logo.png"}

@app.post("/api/quotations/{id}/convert-to-invoice")
def convert_quotation_to_invoice(id: int):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM quotations WHERE id = ?", (id,))
    quote = cursor.fetchone()
    if not quote:
        conn.close()
        raise HTTPException(status_code=404, detail="Quotation not found")
        
    cursor.execute("SELECT * FROM quotation_items WHERE quotation_id = ?", (id,))
    q_items = cursor.fetchall()
    
    inv_no = generate_next_invoice_number(conn)
    fy = get_financial_year()
    today_str = datetime.date.today().strftime("%d-%m-%Y")
    due_str = (datetime.date.today() + datetime.timedelta(days=15)).strftime("%d-%m-%Y")
    
    cursor.execute("""
        INSERT INTO invoices (
            invoice_no, financial_year, invoice_date, due_date, customer_id, customer_name,
            customer_address, customer_gstin, customer_state, is_interstate,
            subtotal, cgst_amount, sgst_amount, igst_amount, grand_total, amount_in_words,
            terms, status, quotation_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        inv_no, fy, today_str, due_str,
        quote["customer_id"], quote["customer_name"], quote["customer_address"],
        quote["customer_gstin"], quote["customer_state"], quote["is_interstate"],
        quote["subtotal"], quote["cgst_amount"], quote["sgst_amount"], quote["igst_amount"],
        quote["grand_total"], quote["amount_in_words"],
        "Thank you for your business!", "Unpaid", id
    ))
    inv_id = cursor.lastrowid
    
    for item in q_items:
        cursor.execute("""
            INSERT INTO invoice_items (invoice_id, product_id, description, hsn_code, qty, unit, rate, gst_rate, amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            inv_id, item["product_id"], item["description"], item["hsn_code"],
            item["qty"], item["unit"], item["rate"], item["gst_rate"], item["amount"]
        ))
        
    # Mark quote as converted
    cursor.execute("UPDATE quotations SET status = 'Converted', converted_invoice_id = ? WHERE id = ?", (inv_id, id))
    
    conn.commit()
    conn.close()
    
    create_backup(label="quote_converted")
    
    return {"invoice_id": inv_id, "invoice_no": inv_no, "message": "Quotation converted to Tax Invoice successfully"}

@app.delete("/api/quotations/{id}")
def delete_quotation(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM quotation_items WHERE quotation_id = ?", (id,))
    cursor.execute("DELETE FROM quotations WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"message": "Quotation deleted successfully"}

# ----------------- DELIVERY CHALLANS API -----------------

@app.get("/api/challans/next-number")
def get_next_challan_number():
    conn = get_db()
    next_no = generate_next_challan_number(conn)
    conn.close()
    return {"next_challan_no": next_no}

@app.get("/api/challans")
def get_challans():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM delivery_challans ORDER BY id DESC")
    challans = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return challans

@app.get("/api/challans/{id}")
def get_challan_detail(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM delivery_challans WHERE id = ?", (id,))
    challan = cursor.fetchone()
    if not challan:
        conn.close()
        raise HTTPException(status_code=404, detail="Delivery Challan not found")
        
    cursor.execute("SELECT * FROM delivery_challan_items WHERE challan_id = ?", (id,))
    items = [dict(r) for r in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM company_settings WHERE id = 1")
    settings = dict(cursor.fetchone())
    conn.close()
    
    c_dict = dict(challan)
    c_dict["items"] = items
    c_dict["settings"] = settings
    return c_dict

@app.post("/api/challans")
def create_challan(challan: DeliveryChallanCreateModel):
    conn = get_db()
    cursor = conn.cursor()
    
    fy = get_financial_year()
    challan_no = challan.challan_no or generate_next_challan_number(conn)
    approx_total = round(sum(item.approx_amount for item in challan.items), 2)
    
    cursor.execute("SELECT * FROM company_settings WHERE id = 1")
    settings = dict(cursor.fetchone() or {})
    company_name = settings.get("name", "the supplier")
    default_challan_terms = settings.get("terms_challan") or f"Goods dispatched on approval / installation. Ownership remains with {company_name} until full payment."

    cursor.execute("""
        INSERT INTO delivery_challans (
            challan_no, financial_year, challan_date, customer_id, customer_name,
            customer_address, customer_gstin, customer_state, reason_for_transport,
            transporter_name, vehicle_no, e_way_bill_no, approx_total, terms, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        challan_no, fy, challan.challan_date, challan.customer_id,
        challan.customer_name, challan.customer_address, challan.customer_gstin,
        challan.customer_state, challan.reason_for_transport,
        challan.transporter_name or "", challan.vehicle_no or "",
        challan.e_way_bill_no or "", approx_total,
        challan.terms or default_challan_terms,
        challan.status
    ))
    c_id = cursor.lastrowid
    
    for item in challan.items:
        cursor.execute("""
            INSERT INTO delivery_challan_items (
                challan_id, product_id, description, hsn_code, qty, unit, approx_rate, approx_amount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            c_id, item.product_id, item.description, item.hsn_code,
            item.qty, item.unit, item.approx_rate, item.approx_amount
        ))
        
    conn.commit()
    conn.close()
    
    create_backup(label="challan_created")
    return {"id": c_id, "challan_no": challan_no, "message": "Delivery Challan created successfully"}

@app.put("/api/challans/{id}")
def update_challan(id: int, challan: DeliveryChallanCreateModel):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT challan_no FROM delivery_challans WHERE id = ?", (id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Delivery Challan not found")
        
    challan_no = challan.challan_no or existing["challan_no"]
    approx_total = round(sum(item.approx_amount for item in challan.items), 2)
    
    cursor.execute("""
        UPDATE delivery_challans SET
            challan_no = ?, challan_date = ?, customer_id = ?, customer_name = ?,
            customer_address = ?, customer_gstin = ?, customer_state = ?,
            reason_for_transport = ?, transporter_name = ?, vehicle_no = ?,
            e_way_bill_no = ?, approx_total = ?, terms = ?, status = ?
        WHERE id = ?
    """, (
        challan_no, challan.challan_date, challan.customer_id,
        challan.customer_name, challan.customer_address, challan.customer_gstin,
        challan.customer_state, challan.reason_for_transport,
        challan.transporter_name or "", challan.vehicle_no or "",
        challan.e_way_bill_no or "", approx_total,
        challan.terms or "", challan.status, id
    ))
    
    cursor.execute("DELETE FROM delivery_challan_items WHERE challan_id = ?", (id,))
    for item in challan.items:
        cursor.execute("""
            INSERT INTO delivery_challan_items (
                challan_id, product_id, description, hsn_code, qty, unit, approx_rate, approx_amount
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            id, item.product_id, item.description, item.hsn_code,
            item.qty, item.unit, item.approx_rate, item.approx_amount
        ))
        
    conn.commit()
    conn.close()
    
    create_backup(label="challan_updated")
    return {"id": id, "challan_no": challan_no, "message": "Delivery Challan updated successfully"}

@app.delete("/api/challans/{id}")
def delete_challan(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM delivery_challan_items WHERE challan_id = ?", (id,))
    cursor.execute("DELETE FROM delivery_challans WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"message": "Delivery Challan deleted successfully"}

@app.post("/api/challans/{id}/convert-to-invoice")
def convert_challan_to_invoice(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM delivery_challans WHERE id = ?", (id,))
    challan = cursor.fetchone()
    if not challan:
        conn.close()
        raise HTTPException(status_code=404, detail="Delivery Challan not found")
        
    cursor.execute("SELECT * FROM delivery_challan_items WHERE challan_id = ?", (id,))
    c_items = cursor.fetchall()
    
    inv_no = generate_next_invoice_number(conn)
    fy = get_financial_year()
    today_str = datetime.date.today().strftime("%d-%m-%Y")
    
    cursor.execute("SELECT state FROM company_settings WHERE id = 1")
    comp_state = cursor.fetchone()[0]
    is_interstate = (challan["customer_state"].strip().lower() != comp_state.strip().lower())
    
    subtotal = 0.0
    cgst_amount = 0.0
    sgst_amount = 0.0
    igst_amount = 0.0
    
    converted_items = []
    for itm in c_items:
        rate = itm["approx_rate"] or 0.0
        qty = itm["qty"] or 1.0
        amt = itm["approx_amount"] or (rate * qty)
        subtotal += amt
        gst_rate = 5.0
        tax = amt * (gst_rate / 100.0)
        if is_interstate:
            igst_amount += tax
        else:
            cgst_amount += tax / 2.0
            sgst_amount += tax / 2.0
        converted_items.append({
            "product_id": itm["product_id"],
            "description": itm["description"],
            "hsn_code": itm["hsn_code"],
            "qty": qty,
            "unit": itm["unit"],
            "rate": rate,
            "gst_rate": gst_rate,
            "amount": amt,
            "item_type": "Goods",
            "is_tax_inclusive": 0
        })
        
    subtotal = round(subtotal, 2)
    cgst_amount = round(cgst_amount, 2)
    sgst_amount = round(sgst_amount, 2)
    igst_amount = round(igst_amount, 2)
    grand_total = round(subtotal + cgst_amount + sgst_amount + igst_amount, 2)
    amount_words = indian_number_to_words(grand_total)
    
    cursor.execute("""
        INSERT INTO invoices (
            invoice_no, financial_year, invoice_date, due_date, customer_id,
            customer_name, customer_address, customer_gstin, customer_state,
            is_interstate, subtotal, cgst_amount, sgst_amount, igst_amount,
            grand_total, amount_in_words, terms, status, invoice_type,
            e_way_bill_no, vehicle_no, transporter_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        inv_no, fy, today_str, "", challan["customer_id"],
        challan["customer_name"], challan["customer_address"], challan["customer_gstin"],
        challan["customer_state"], 1 if is_interstate else 0,
        subtotal, cgst_amount, sgst_amount, igst_amount,
        grand_total, amount_words, "Generated from Delivery Challan " + challan["challan_no"],
        "Unpaid", "Goods",
        challan["e_way_bill_no"], challan["vehicle_no"], challan["transporter_name"]
    ))
    inv_id = cursor.lastrowid
    
    for ci in converted_items:
        cursor.execute("""
            INSERT INTO invoice_items (
                invoice_id, product_id, description, hsn_code, qty, unit, rate, gst_rate, amount, item_type, is_tax_inclusive
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            inv_id, ci["product_id"], ci["description"], ci["hsn_code"],
            ci["qty"], ci["unit"], ci["rate"], ci["gst_rate"], ci["amount"],
            ci["item_type"], ci["is_tax_inclusive"]
        ))
        
    cursor.execute("UPDATE delivery_challans SET status = 'Invoiced', invoice_id = ? WHERE id = ?", (inv_id, id))
    conn.commit()
    conn.close()
    
    create_backup(label="challan_converted")
    return {"message": f"Converted to Invoice {inv_no}", "invoice_id": inv_id, "invoice_no": inv_no}

# ----------------- GST & REPORTS API -----------------

@app.get("/api/reports/gst-summary")
def get_gst_summary(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    financial_year: Optional[str] = None
):
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT * FROM invoices WHERE 1=1"
    params = []
    
    if financial_year:
        query += " AND financial_year = ?"
        params.append(financial_year)
        
    cursor.execute(query + " ORDER BY id DESC", params)
    all_invoices = [dict(r) for r in cursor.fetchall()]
    
    filtered_invoices = []
    for inv in all_invoices:
        inc = True
        try:
            inv_dt = datetime.datetime.strptime(inv["invoice_date"], "%d-%m-%Y").date()
            if from_date:
                f_dt = datetime.datetime.strptime(from_date, "%d-%m-%Y").date()
                if inv_dt < f_dt:
                    inc = False
            if to_date:
                t_dt = datetime.datetime.strptime(to_date, "%d-%m-%Y").date()
                if inv_dt > t_dt:
                    inc = False
        except Exception:
            pass
        if inc:
            filtered_invoices.append(inv)
            
    b2b_invoices = []
    b2cs_invoices = []
    
    total_taxable = 0.0
    total_cgst = 0.0
    total_sgst = 0.0
    total_igst = 0.0
    total_grand = 0.0
    
    inv_ids = [inv["id"] for inv in filtered_invoices]
    
    for inv in filtered_invoices:
        total_taxable += inv["subtotal"]
        total_cgst += inv["cgst_amount"]
        total_sgst += inv["sgst_amount"]
        total_igst += inv["igst_amount"]
        total_grand += inv["grand_total"]
        
        gstin = (inv["customer_gstin"] or "").strip().upper()
        if gstin and gstin != "N/A" and len(gstin) == 15:
            b2b_invoices.append(inv)
        else:
            b2cs_invoices.append(inv)
            
    hsn_summary = []
    if inv_ids:
        placeholders = ",".join("?" * len(inv_ids))
        cursor.execute(f"""
            SELECT 
                it.hsn_code,
                it.description,
                it.unit,
                SUM(it.qty) as total_qty,
                SUM(it.amount) as taxable_value,
                it.gst_rate,
                SUM(it.amount * (it.gst_rate / 100.0)) as total_tax,
                SUM(CASE WHEN inv.is_interstate = 1 THEN it.amount * (it.gst_rate / 100.0) ELSE 0 END) as igst_amount,
                SUM(CASE WHEN inv.is_interstate = 0 THEN (it.amount * (it.gst_rate / 100.0)) / 2.0 ELSE 0 END) as cgst_amount,
                SUM(CASE WHEN inv.is_interstate = 0 THEN (it.amount * (it.gst_rate / 100.0)) / 2.0 ELSE 0 END) as sgst_amount
            FROM invoice_items it
            JOIN invoices inv ON it.invoice_id = inv.id
            WHERE it.invoice_id IN ({placeholders})
            GROUP BY it.hsn_code, it.unit
        """, inv_ids)
        for r in cursor.fetchall():
            row = dict(r)
            row["total_value"] = round(row["taxable_value"] + row["total_tax"], 2)
            row["taxable_value"] = round(row["taxable_value"], 2)
            row["igst_amount"] = round(row["igst_amount"], 2)
            row["cgst_amount"] = round(row["cgst_amount"], 2)
            row["sgst_amount"] = round(row["sgst_amount"], 2)
            hsn_summary.append(row)
            
    conn.close()
    
    return {
        "total_invoices": len(filtered_invoices),
        "total_taxable": round(total_taxable, 2),
        "total_cgst": round(total_cgst, 2),
        "total_sgst": round(total_sgst, 2),
        "total_igst": round(total_igst, 2),
        "total_tax": round(total_cgst + total_sgst + total_igst, 2),
        "total_grand": round(total_grand, 2),
        "b2b_count": len(b2b_invoices),
        "b2cs_count": len(b2cs_invoices),
        "b2b_invoices": b2b_invoices,
        "b2cs_invoices": b2cs_invoices,
        "hsn_summary": hsn_summary
    }

@app.get("/api/reports/gstr1-csv")
def export_gstr1_csv(from_date: Optional[str] = None, to_date: Optional[str] = None, financial_year: Optional[str] = None):
    data = get_gst_summary(from_date, to_date, financial_year)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM company_settings WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    company_name = row["name"] if row and row["name"] else "BUSINESS ERP"

    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["GSTR-1 SUMMARY REPORT", company_name])
    writer.writerow(["Period / FY", financial_year or "All", "Generated On", datetime.date.today().strftime("%d-%m-%Y")])
    writer.writerow(["Total Taxable Turnover", f"INR {data['total_taxable']:.2f}", "Total Tax Collected", f"INR {data['total_tax']:.2f}"])
    writer.writerow([])
    
    writer.writerow(["--- TABLE 4: B2B INVOICES (Taxable Outward Supplies to Registered Persons) ---"])
    writer.writerow([
        "GSTIN/UIN of Recipient", "Receiver Name", "Invoice Number", "Invoice Date",
        "Invoice Value", "Place Of Supply", "Reverse Charge", "Invoice Type",
        "E-Commerce GSTIN", "Rate", "Taxable Value", "Cess Amount"
    ])
    for inv in data["b2b_invoices"]:
        writer.writerow([
            inv["customer_gstin"], inv["customer_name"], inv["invoice_no"], inv["invoice_date"],
            f"{inv['grand_total']:.2f}", inv["customer_state"], "N", "Regular",
            "", "5%", f"{inv['subtotal']:.2f}", "0.00"
        ])
    writer.writerow([])
    
    writer.writerow(["--- TABLE 7: B2CS (B2C Small Supplies to Unregistered Persons) ---"])
    writer.writerow([
        "Type", "Place Of Supply", "Rate", "Applicable % of Tax Rate",
        "Taxable Value", "Cess Amount", "E-Commerce GSTIN"
    ])
    b2cs_by_state = {}
    for inv in data["b2cs_invoices"]:
        st = inv["customer_state"]
        b2cs_by_state[st] = b2cs_by_state.get(st, 0.0) + inv["subtotal"]
    for st, taxable in b2cs_by_state.items():
        writer.writerow(["OE", st, "5%", "", f"{taxable:.2f}", "0.00", ""])
    writer.writerow([])
    
    writer.writerow(["--- TABLE 12: HSN/SAC SUMMARY OF OUTWARD SUPPLIES ---"])
    writer.writerow([
        "HSN", "Description", "UQC", "Total Quantity",
        "Total Value", "Taxable Value", "Integrated Tax Amount",
        "Central Tax Amount", "State/UT Tax Amount", "Cess Amount"
    ])
    for h in data["hsn_summary"]:
        writer.writerow([
            h["hsn_code"], h["description"], h["unit"], h["total_qty"],
            f"{h['total_value']:.2f}", f"{h['taxable_value']:.2f}",
            f"{h['igst_amount']:.2f}", f"{h['cgst_amount']:.2f}", f"{h['sgst_amount']:.2f}", "0.00"
        ])
        
    output.seek(0)
    filename = f"GSTR1_Export_{financial_year or 'All'}_{datetime.date.today().strftime('%Y%m%d')}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/api/reports/sales-register-csv")
def export_sales_register_csv(from_date: Optional[str] = None, to_date: Optional[str] = None, financial_year: Optional[str] = None):
    conn = get_db()
    cursor = conn.cursor()
    
    query = """
        SELECT 
            inv.invoice_no, inv.invoice_date, inv.customer_name, inv.customer_state,
            inv.customer_gstin, inv.po_no, inv.po_date, inv.e_way_bill_no, inv.vehicle_no,
            it.description, it.item_type, it.hsn_code, it.qty, it.unit, it.rate,
            it.gst_rate, it.amount as taxable_amount,
            CASE WHEN inv.is_interstate = 1 THEN it.amount * (it.gst_rate / 100.0) ELSE 0 END as igst,
            CASE WHEN inv.is_interstate = 0 THEN (it.amount * (it.gst_rate / 100.0)) / 2.0 ELSE 0 END as cgst,
            CASE WHEN inv.is_interstate = 0 THEN (it.amount * (it.gst_rate / 100.0)) / 2.0 ELSE 0 END as sgst,
            it.amount + (it.amount * (it.gst_rate / 100.0)) as item_total
        FROM invoice_items it
        JOIN invoices inv ON it.invoice_id = inv.id
        WHERE 1=1
    """
    params = []
    if financial_year:
        query += " AND inv.financial_year = ?"
        params.append(financial_year)
        
    cursor.execute(query + " ORDER BY inv.id DESC, it.id ASC", params)
    rows = cursor.fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Invoice No", "Date", "Customer / Hospital", "State", "GSTIN",
        "PO No", "PO Date", "E-Way Bill No", "Vehicle No",
        "Item Description", "Type", "HSN/SAC", "Qty", "Unit", "Rate (INR)",
        "Taxable Value (INR)", "GST %", "CGST (INR)", "SGST (INR)", "IGST (INR)", "Item Total (INR)"
    ])
    for r in rows:
        writer.writerow([
            r["invoice_no"], r["invoice_date"], r["customer_name"], r["customer_state"], r["customer_gstin"],
            r["po_no"], r["po_date"], r["e_way_bill_no"], r["vehicle_no"],
            r["description"], r["item_type"], r["hsn_code"], r["qty"], r["unit"], f"{r['rate']:.2f}",
            f"{r['taxable_amount']:.2f}", f"{r['gst_rate']}%", f"{r['cgst']:.2f}", f"{r['sgst']:.2f}", f"{r['igst']:.2f}", f"{r['item_total']:.2f}"
        ])
        
    output.seek(0)
    filename = f"Sales_Register_{financial_year or 'All'}_{datetime.date.today().strftime('%Y%m%d')}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ----------------- BACKUP & RESTORE API -----------------

@app.get("/api/backups")
def get_all_backups():
    return list_backups()

@app.post("/api/backups/create")
def trigger_manual_backup():
    filepath = create_backup(label="manual")
    return {"message": "Backup created successfully", "filepath": filepath}

@app.post("/api/backups/restore/{filename}")
def trigger_restore(filename: str):
    success = restore_backup(filename)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to restore backup")
    return {"message": f"Successfully restored database from {filename}"}

@app.get("/api/backups/download/{filename}")
def download_backup_file(filename: str):
    file_path = BACKUP_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Backup file not found")
    return FileResponse(file_path, filename=filename, media_type="application/octet-stream")

@app.post("/api/backups/upload")
async def upload_backup_file(file: UploadFile = File(...)):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"uploaded_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    filepath = BACKUP_DIR / filename
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"message": "Backup file uploaded", "filename": filename}

# ----------------- PRINT & PDF HTML VIEWS -----------------

@app.get("/invoice/print/{id}", response_class=HTMLResponse)
def print_invoice(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM invoices WHERE id = ?", (id,))
    inv = cursor.fetchone()
    if not inv:
        conn.close()
        raise HTTPException(status_code=404, detail="Invoice not found")
    inv = dict(inv)
        
    cursor.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (id,))
    items = cursor.fetchall()
    
    cursor.execute("SELECT * FROM company_settings WHERE id = 1")
    settings = dict(cursor.fetchone())
    conn.close()
    
    # Generate UPI QR Code
    qr_b64 = generate_upi_qr_base64(
        vpa=settings["upi_address"],
        payee_name=settings["upi_name"],
        amount=inv["grand_total"],
        transaction_ref=inv["invoice_no"]
    )
    
    # Build items rows
    items_html = ""
    for idx, itm in enumerate(items, 1):
        items_html += f"""
        <tr>
            <td class="col-sno">{idx}</td>
            <td class="col-desc">
                <div class="item-desc-text">{itm["description"]}</div>
            </td>
            <td class="col-hsn">{itm["hsn_code"]}</td>
            <td class="col-qty">{int(itm["qty"]) if itm["qty"].is_integer() else itm["qty"]} {itm["unit"]}</td>
            <td class="col-rate">₹{itm["rate"]:.2f}</td>
            <td class="col-gst">{int(itm["gst_rate"]) if itm["gst_rate"].is_integer() else itm["gst_rate"]}%</td>
            <td class="col-amount">₹{itm["amount"]:.2f}</td>
        </tr>
        """
        
    # Tax rows (CGST + SGST or IGST)
    if inv["is_interstate"]:
        tax_rows = f"""
        <tr>
            <td class="total-label">Integrated Tax (IGST):</td>
            <td class="total-val">₹{inv["igst_amount"]:.2f}</td>
        </tr>
        """
    else:
        tax_rows = f"""
        <tr>
            <td class="total-label">Central Tax (CGST):</td>
            <td class="total-val">₹{inv["cgst_amount"]:.2f}</td>
        </tr>
        <tr>
            <td class="total-label">State Tax (SGST):</td>
            <td class="total-val">₹{inv["sgst_amount"]:.2f}</td>
        </tr>
        """

    # Generate auto-clean filename for PDF download / browser save
    safe_inv_no = inv["invoice_no"].replace("/", "-")
    safe_cust = "".join(c for c in inv["customer_name"] if c.isalnum() or c in " -_").strip().replace("  ", " ")
    doc_filename = f"{safe_inv_no} - {safe_cust} - Tax Invoice"

    # PO & Transport Details for Tax Invoice
    po_row = ""
    if inv.get("po_no"):
        po_row = f"""
        <tr>
            <td class="meta-label">PO Ref:</td>
            <td class="meta-val">{inv["po_no"]}{f' ({inv["po_date"]})' if inv.get("po_date") else ''}</td>
        </tr>
        """
    transport_box = ""
    if inv.get("e_way_bill_no") or inv.get("vehicle_no") or inv.get("transporter_name"):
        parts = []
        if inv.get("e_way_bill_no"): parts.append(f"<strong>E-Way Bill:</strong> {inv['e_way_bill_no']}")
        if inv.get("vehicle_no"): parts.append(f"<strong>Vehicle:</strong> {inv['vehicle_no']}")
        if inv.get("transporter_name"): parts.append(f"<strong>Transporter:</strong> {inv['transporter_name']}")
        transport_box = f'<div style="margin-top:6px; padding-top:4px; border-top:1px dashed #cbd5e1; font-size:10px; color:#475569;">{" | ".join(parts)}</div>'

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{doc_filename}</title>
    <link rel="stylesheet" href="/static/css/print.css">
    <script src="/static/js/html2pdf.bundle.min.js"></script>
    <script>
        window.generatePdf = async function() {{
            const sheet = document.querySelector('.document-sheet');
            if (!sheet) return;
            let filename = (document.title || 'Tax Invoice').trim();
            if (!filename.toLowerCase().endsWith('.pdf')) filename += '.pdf';

            const noPrint = document.querySelectorAll('.no-print');
            noPrint.forEach(el => el.style.display = 'none');

            const opt = {{
                margin: 0,
                filename: filename,
                image: {{ type: 'jpeg', quality: 0.98 }},
                html2canvas: {{
                    scale: 2,
                    useCORS: true,
                    logging: false,
                    letterRendering: true,
                    scrollY: 0,
                    scrollX: 0
                }},
                jsPDF: {{ unit: 'mm', format: 'a4', orientation: 'portrait' }}
            }};

            try {{
                if (window.html2pdf) {{
                    await html2pdf().set(opt).from(sheet).save();
                }} else {{
                    window.print();
                }}
            }} finally {{
                noPrint.forEach(el => el.style.display = '');
            }}
        }};
    </script>
</head>
<body class="document-body">
    <div class="no-print" style="background:#1e293b; color:white; padding:12px 24px; display:flex; justify-content:space-between; align-items:center; position:sticky; top:0; z-index:1000;">
        <div style="font-weight:600; font-size:14px;">Invoice: {inv["invoice_no"]}</div>
        <div>
            <button onclick="generatePdf()" style="background:#059669; color:white; border:none; padding:8px 18px; border-radius:6px; font-weight:600; cursor:pointer; margin-right:8px;">Download PDF</button>
            <button onclick="window.print()" style="background:#2563eb; color:white; border:none; padding:8px 18px; border-radius:6px; font-weight:600; cursor:pointer; margin-right:8px;">Print / Save as PDF</button>
            <button onclick="window.close()" style="background:#475569; color:white; border:none; padding:8px 16px; border-radius:6px; font-weight:600; cursor:pointer;">Close</button>
        </div>
    </div>

    <div class="document-sheet">
        <!-- Header -->
        <div class="doc-header">
            <div class="doc-brand">
                <img src="/static/images/logo.png" alt="Logo" class="doc-logo" width="62" height="62" style="width:62px !important; height:62px !important; max-width:62px !important; max-height:62px !important; object-fit:contain;">
                <div class="doc-company-info">
                    <h1>{settings["name"]}</h1>
                    <p>{settings["address"]}</p>
                    <p>Phone: {settings["phone"]} | Email: {settings["email"]}</p>
                    <p>GSTIN: {settings["gstin"]} | Registered State: {settings["state"]}</p>
                </div>
            </div>
            <div class="doc-title-block">
                <h2>TAX INVOICE</h2>
                <table class="doc-meta-table">
                    <tr>
                        <td class="meta-label">Date:</td>
                        <td class="meta-val">{inv["invoice_date"]}</td>
                    </tr>
                    <tr>
                        <td class="meta-label">Invoice No:</td>
                        <td class="meta-val">{inv["invoice_no"]}</td>
                    </tr>
                    <tr>
                        <td class="meta-label">Due Date:</td>
                        <td class="meta-val">{inv["due_date"] or "N/A"}</td>
                    </tr>
                    {po_row}
                </table>
            </div>
        </div>

        <div class="divider-line"></div>

        <!-- Info Cards -->
        <div class="info-cards-grid">
            <div class="info-card">
                <div class="info-card-title">Billed To (Recipient)</div>
                <div class="recipient-name">{inv["customer_name"]}</div>
                <p>{inv["customer_address"]}</p>
                <p><strong>GSTIN:</strong> {inv["customer_gstin"]}</p>
                <p><strong>Billing State:</strong> {inv["customer_state"]}</p>
                {transport_box}
            </div>
            <div class="info-card">
                <div class="info-card-title">{settings["name"]} Bank Details</div>
                <p><strong>Bank:</strong> {settings["bank_name"]}</p>
                <p><strong>Branch:</strong> {settings["branch"]}</p>
                <p><strong>A/C No:</strong> {settings["account_no"]}</p>
                <p><strong>IFSC:</strong> {settings["ifsc"]}</p>
                <p><strong>UPI Address:</strong> {settings["upi_address"]}</p>
            </div>
        </div>

        <!-- Items Table -->
        <div class="items-table-wrapper">
            <table class="items-table">
                <thead>
                    <tr>
                        <th class="col-sno">S.No</th>
                        <th class="col-desc">Description of Goods / Services</th>
                        <th class="col-hsn">HSN/SAC</th>
                        <th class="col-qty">Qty / Unit</th>
                        <th class="col-rate">Rate (₹)</th>
                        <th class="col-gst">GST</th>
                        <th class="col-amount">Amount (₹)</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
            </table>
        </div>

        <!-- Bottom Grid: Terms & QR + Totals -->
        <div class="doc-bottom-grid">
            <div class="terms-section">
                <h4>Terms, Conditions & Remarks</h4>
                <div class="terms-content">{inv["terms"]}</div>
                <div class="upi-payment-block">
                    <img src="{qr_b64}" alt="UPI QR" class="upi-qr-img" width="78" height="78" style="width:78px !important; height:78px !important; max-width:78px !important; max-height:78px !important; object-fit:contain;">
                    <div class="upi-info">
                        <div class="upi-title">Scan to Settle Payments via UPI</div>
                        <div class="upi-details">VPA: {settings["upi_address"]}</div>
                        <div class="upi-details">Acc Name: {settings["upi_name"]}</div>
                    </div>
                </div>
            </div>

            <div class="totals-section">
                <table class="totals-table">
                    <tr>
                        <td class="total-label">Subtotal (Excl. Tax):</td>
                        <td class="total-val">₹{inv["subtotal"]:.2f}</td>
                    </tr>
                    {tax_rows}
                    <tr class="grand-total-row">
                        <td class="total-label">Grand Total (INR):</td>
                        <td class="total-val">₹{inv["grand_total"]:.2f}</td>
                    </tr>
                </table>
                <div class="amount-words-box">
                    <span class="words-label">Amount in words:</span> <span class="words-val">{inv["amount_in_words"]}</span>
                </div>
            </div>
        </div>

        <!-- Signature -->
        <div class="doc-footer-signature">
            <div class="for-company">For {settings["name"]}</div>
            <div class="sig-line">Authorized Signatory</div>
        </div>
    </div>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.get("/quotation/print/{id}", response_class=HTMLResponse)
def print_quotation(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quotations WHERE id = ?", (id,))
    quote = cursor.fetchone()
    if not quote:
        conn.close()
        raise HTTPException(status_code=404, detail="Quotation not found")
    quote = dict(quote)
        
    cursor.execute("SELECT * FROM quotation_items WHERE quotation_id = ?", (id,))
    items = cursor.fetchall()
    
    cursor.execute("SELECT * FROM company_settings WHERE id = 1")
    settings = dict(cursor.fetchone())
    conn.close()
    
    qr_b64 = generate_upi_qr_base64(
        vpa=settings["upi_address"],
        payee_name=settings["upi_name"],
        amount=quote["grand_total"],
        transaction_ref=quote["quote_no"]
    )
    
    # Items Rows
    items_html = ""
    visual_cards_html = ""
    
    for idx, itm in enumerate(items, 1):
        items_html += f"""
        <tr>
            <td class="col-sno">{idx}</td>
            <td class="col-desc">
                <div class="item-desc-text">{itm["description"]}</div>
            </td>
            <td class="col-hsn">{itm["hsn_code"]}</td>
            <td class="col-qty">{int(itm["qty"]) if itm["qty"].is_integer() else itm["qty"]} {itm["unit"]}</td>
            <td class="col-rate">₹{itm["rate"]:.2f}</td>
            <td class="col-gst">{int(itm["gst_rate"]) if itm["gst_rate"].is_integer() else itm["gst_rate"]}%</td>
            <td class="col-amount">₹{itm["amount"]:.2f}</td>
        </tr>
        """
        
        # Build Visual Specs Card for Page 2
        img_src = itm["product_image_url"] or "/static/images/products/radiography_system.png"
        visual_cards_html += f"""
        <div class="spec-card">
            <div class="spec-img-container">
                <img src="{img_src}" alt="{itm["description"]}" class="spec-product-img" style="max-width:100% !important; max-height:180px !important; object-fit:contain;">
            </div>
            <div class="spec-product-title">{itm["description"]}</div>
        </div>
        """

    if quote["is_interstate"]:
        tax_rows = f"""
        <tr>
            <td class="total-label">Integrated Tax (IGST):</td>
            <td class="total-val">₹{quote["igst_amount"]:.2f}</td>
        </tr>
        """
    else:
        tax_rows = f"""
        <tr>
            <td class="total-label">Central Tax (CGST):</td>
            <td class="total-val">₹{quote["cgst_amount"]:.2f}</td>
        </tr>
        <tr>
            <td class="total-label">State Tax (SGST):</td>
            <td class="total-val">₹{quote["sgst_amount"]:.2f}</td>
        </tr>
        """

    # Generate auto-clean filename for PDF download / browser save
    safe_q_no = quote["quote_no"].replace("/", "-")
    safe_cust = "".join(c for c in quote["customer_name"] if c.isalnum() or c in " -_").strip().replace("  ", " ")
    doc_filename = f"{safe_q_no} - {safe_cust} - Quotation Estimate"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{doc_filename}</title>
    <link rel="stylesheet" href="/static/css/print.css">
    <script src="/static/js/html2pdf.bundle.min.js"></script>
    <script>
        window.generatePdf = async function() {{
            const sheets = document.querySelectorAll('.document-sheet');
            if (!sheets || sheets.length === 0) return;
            let filename = (document.title || 'Quotation Estimate').trim();
            if (!filename.toLowerCase().endsWith('.pdf')) filename += '.pdf';

            const noPrint = document.querySelectorAll('.no-print');
            noPrint.forEach(el => el.style.display = 'none');

            let renderTarget;
            let createdWrapper = false;
            if (sheets.length === 1) {{
                renderTarget = sheets[0];
            }} else {{
                renderTarget = document.createElement('div');
                renderTarget.style.width = '210mm';
                renderTarget.style.margin = '0 auto';
                renderTarget.style.background = '#ffffff';
                sheets.forEach(s => {{
                    renderTarget.appendChild(s.cloneNode(true));
                }});
                document.body.appendChild(renderTarget);
                createdWrapper = true;
            }}

            const opt = {{
                margin: 0,
                filename: filename,
                image: {{ type: 'jpeg', quality: 0.98 }},
                html2canvas: {{
                    scale: 2,
                    useCORS: true,
                    logging: false,
                    letterRendering: true,
                    scrollY: 0,
                    scrollX: 0
                }},
                jsPDF: {{ unit: 'mm', format: 'a4', orientation: 'portrait' }},
                pagebreak: {{ mode: ['css', 'legacy'], before: '.page-break' }}
            }};

            try {{
                if (window.html2pdf) {{
                    await html2pdf().set(opt).from(renderTarget).save();
                }} else {{
                    window.print();
                }}
            }} finally {{
                noPrint.forEach(el => el.style.display = '');
                if (createdWrapper && renderTarget && renderTarget.parentNode) {{
                    renderTarget.parentNode.removeChild(renderTarget);
                }}
            }}
        }};
    </script>
</head>
<body class="document-body">
    <div class="no-print" style="background:#1e293b; color:white; padding:12px 24px; display:flex; justify-content:space-between; align-items:center; position:sticky; top:0; z-index:1000;">
        <div style="font-weight:600; font-size:14px;">Quotation: {quote["quote_no"]}</div>
        <div>
            <button onclick="generatePdf()" style="background:#059669; color:white; border:none; padding:8px 18px; border-radius:6px; font-weight:600; cursor:pointer; margin-right:8px;">Download PDF</button>
            <button onclick="window.print()" style="background:#2563eb; color:white; border:none; padding:8px 18px; border-radius:6px; font-weight:600; cursor:pointer; margin-right:8px;">Print / Save as PDF</button>
            <button onclick="window.close()" style="background:#475569; color:white; border:none; padding:8px 16px; border-radius:6px; font-weight:600; cursor:pointer;">Close</button>
        </div>
    </div>

    <!-- PAGE 1: Financial Quotation & Terms -->
    <div class="document-sheet">
        <div class="doc-header">
            <div class="doc-brand">
                <img src="/static/images/logo.png" alt="Logo" class="doc-logo" width="62" height="62" style="width:62px !important; height:62px !important; max-width:62px !important; max-height:62px !important; object-fit:contain;">
                <div class="doc-company-info">
                    <h1>{settings["name"]}</h1>
                    <p>{settings["address"]}</p>
                    <p>Phone: {settings["phone"]} | Email: {settings["email"]}</p>
                    <p>GSTIN: {settings["gstin"]} | Registered State: {settings["state"]}</p>
                </div>
            </div>
            <div class="doc-title-block">
                <h2>QUOTATION ESTIMATE</h2>
                <table class="doc-meta-table">
                    <tr>
                        <td class="meta-label">Date:</td>
                        <td class="meta-val">{quote["quote_date"]}</td>
                    </tr>
                    <tr>
                        <td class="meta-label">Quote No:</td>
                        <td class="meta-val">{quote["quote_no"]}</td>
                    </tr>
                    <tr>
                        <td class="meta-label">Valid Until:</td>
                        <td class="meta-val">{quote["valid_until"] or "N/A"}</td>
                    </tr>
                </table>
            </div>
        </div>

        <div class="divider-line"></div>

        <div class="info-cards-grid">
            <div class="info-card">
                <div class="info-card-title">Billed To (Recipient)</div>
                <div class="recipient-name">{quote["customer_name"]}</div>
                <p>{quote["customer_address"]}</p>
                <p><strong>GSTIN:</strong> {quote["customer_gstin"]}</p>
                <p><strong>Billing State:</strong> {quote["customer_state"]}</p>
            </div>
            <div class="info-card">
                <div class="info-card-title">{settings["name"]} Bank Details</div>
                <p><strong>Bank:</strong> {settings["bank_name"]}</p>
                <p><strong>Branch:</strong> {settings["branch"]}</p>
                <p><strong>A/C No:</strong> {settings["account_no"]}</p>
                <p><strong>IFSC:</strong> {settings["ifsc"]}</p>
                <p><strong>UPI Address:</strong> {settings["upi_address"]}</p>
            </div>
        </div>

        <div class="items-table-wrapper">
            <table class="items-table">
                <thead>
                    <tr>
                        <th class="col-sno">S.No</th>
                        <th class="col-desc">Description of Goods / Services</th>
                        <th class="col-hsn">HSN/SAC</th>
                        <th class="col-qty">Qty / Unit</th>
                        <th class="col-rate">Rate (₹)</th>
                        <th class="col-gst">GST</th>
                        <th class="col-amount">Amount (₹)</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
            </table>
        </div>

        <div class="doc-bottom-grid">
            <div class="terms-section">
                <h4>Terms, Conditions & Remarks</h4>
                <div class="terms-content">{quote["terms"]}</div>
                <div class="upi-payment-block">
                    <img src="{qr_b64}" alt="UPI QR" class="upi-qr-img" width="78" height="78" style="width:78px !important; height:78px !important; max-width:78px !important; max-height:78px !important; object-fit:contain;">
                    <div class="upi-info">
                        <div class="upi-title">Scan to Settle Payments via UPI</div>
                        <div class="upi-details">VPA: {settings["upi_address"]}</div>
                        <div class="upi-details">Acc Name: {settings["upi_name"]}</div>
                    </div>
                </div>
            </div>

            <div class="totals-section">
                <table class="totals-table">
                    <tr>
                        <td class="total-label">Subtotal (Excl. Tax):</td>
                        <td class="total-val">₹{quote["subtotal"]:.2f}</td>
                    </tr>
                    {tax_rows}
                    <tr class="grand-total-row">
                        <td class="total-label">Grand Total (INR):</td>
                        <td class="total-val">₹{quote["grand_total"]:.2f}</td>
                    </tr>
                </table>
                <div class="amount-words-box">
                    <span class="words-label">Amount in words:</span> <span class="words-val">{quote["amount_in_words"]}</span>
                </div>
            </div>
        </div>

        <div class="doc-footer-signature">
            <div class="for-company">For {settings["name"]}</div>
            <div class="sig-line">Authorized Signatory</div>
        </div>
    </div>

    <!-- PAGE 2: Product Visual Specifications -->
    <div class="document-sheet page-break">
        <div class="spec-page-title">Product Visual Specifications</div>
        <div class="spec-divider"></div>

        <div class="visual-specs-grid">
            {visual_cards_html}
        </div>
    </div>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.get("/challan/print/{id}", response_class=HTMLResponse)
def print_delivery_challan(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM delivery_challans WHERE id = ?", (id,))
    challan = cursor.fetchone()
    if not challan:
        conn.close()
        raise HTTPException(status_code=404, detail="Delivery Challan not found")
    challan = dict(challan)
        
    cursor.execute("SELECT * FROM delivery_challan_items WHERE challan_id = ?", (id,))
    items = cursor.fetchall()
    
    cursor.execute("SELECT * FROM company_settings WHERE id = 1")
    settings = dict(cursor.fetchone())
    conn.close()
    
    items_html = ""
    for idx, itm in enumerate(items, 1):
        items_html += f"""
        <tr>
            <td class="col-sno">{idx}</td>
            <td class="col-desc">
                <div class="item-desc-text">{itm["description"]}</div>
            </td>
            <td class="col-hsn">{itm["hsn_code"]}</td>
            <td class="col-qty">{int(itm["qty"]) if itm["qty"].is_integer() else itm["qty"]} {itm["unit"]}</td>
            <td class="col-rate">₹{itm["approx_rate"]:.2f}</td>
            <td class="col-amount">₹{itm["approx_amount"]:.2f}</td>
        </tr>
        """
        
    safe_c_no = challan["challan_no"].replace("/", "-")
    safe_cust = "".join(c for c in (challan["customer_name"] or "Customer") if c.isalnum() or c in " -_").strip().replace("  ", " ")
    doc_filename = f"{safe_c_no} - {safe_cust} - Delivery Challan"
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{doc_filename}</title>
    <link rel="stylesheet" href="/static/css/print.css">
    <script src="/static/js/html2pdf.bundle.min.js"></script>
    <script>
        window.generatePdf = async function() {{
            const sheet = document.querySelector('.document-sheet');
            if (!sheet) return;
            let filename = (document.title || 'Delivery Challan').trim();
            if (!filename.toLowerCase().endsWith('.pdf')) filename += '.pdf';

            const noPrint = document.querySelectorAll('.no-print');
            noPrint.forEach(el => el.style.display = 'none');

            const opt = {{
                margin: 0,
                filename: filename,
                image: {{ type: 'jpeg', quality: 0.98 }},
                html2canvas: {{
                    scale: 2,
                    useCORS: true,
                    logging: false,
                    letterRendering: true,
                    scrollY: 0,
                    scrollX: 0
                }},
                jsPDF: {{ unit: 'mm', format: 'a4', orientation: 'portrait' }}
            }};

            try {{
                if (window.html2pdf) {{
                    await html2pdf().set(opt).from(sheet).save();
                }} else {{
                    window.print();
                }}
            }} finally {{
                noPrint.forEach(el => el.style.display = '');
            }}
        }};
    </script>
</head>
<body class="document-body">
    <div class="no-print" style="background:#1e293b; color:white; padding:12px 24px; display:flex; justify-content:space-between; align-items:center; position:sticky; top:0; z-index:1000;">
        <div style="font-weight:600; font-size:14px;">Delivery Challan: {challan["challan_no"]}</div>
        <div>
            <button onclick="generatePdf()" style="background:#059669; color:white; border:none; padding:8px 18px; border-radius:6px; font-weight:600; cursor:pointer; margin-right:8px;">Download PDF</button>
            <button onclick="window.print()" style="background:#2563eb; color:white; border:none; padding:8px 18px; border-radius:6px; font-weight:600; cursor:pointer; margin-right:8px;">Print / Save as PDF</button>
            <button onclick="window.close()" style="background:#475569; color:white; border:none; padding:8px 16px; border-radius:6px; font-weight:600; cursor:pointer;">Close</button>
        </div>
    </div>

    <div class="document-sheet">
        <!-- Header -->
        <div class="doc-header">
            <div class="doc-brand">
                <img src="/static/images/logo.png" alt="Logo" class="doc-logo" width="62" height="62" style="width:62px !important; height:62px !important; max-width:62px !important; max-height:62px !important; object-fit:contain;">
                <div class="doc-company-info">
                    <h1>{settings["name"]}</h1>
                    <p>{settings["address"]}</p>
                    <p>Phone: {settings["phone"]} | Email: {settings["email"]}</p>
                    <p>GSTIN: {settings["gstin"]} | Registered State: {settings["state"]}</p>
                </div>
            </div>
            <div class="doc-title-block">
                <h2>DELIVERY CHALLAN</h2>
                <div style="font-size:10px; color:#64748b; font-weight:600; text-transform:uppercase; margin-bottom:4px;">(Issued under Rule 55 of CGST Rules, 2017)</div>
                <table class="doc-meta-table">
                    <tr>
                        <td class="meta-label">Challan Date:</td>
                        <td class="meta-val">{challan["challan_date"]}</td>
                    </tr>
                    <tr>
                        <td class="meta-label">Challan No:</td>
                        <td class="meta-val">{challan["challan_no"]}</td>
                    </tr>
                    <tr>
                        <td class="meta-label">Purpose:</td>
                        <td class="meta-val">{challan["reason_for_transport"]}</td>
                    </tr>
                </table>
            </div>
        </div>

        <div class="divider-line"></div>

        <!-- Info Cards -->
        <div class="info-cards-grid">
            <div class="info-card">
                <div class="info-card-title">Consignee (Deliver To)</div>
                <div class="recipient-name">{challan["customer_name"]}</div>
                <p>{challan["customer_address"]}</p>
                <p><strong>GSTIN:</strong> {challan["customer_gstin"]}</p>
                <p><strong>Delivery State:</strong> {challan["customer_state"]}</p>
            </div>
            <div class="info-card">
                <div class="info-card-title">Transportation & Dispatch Details</div>
                <p><strong>Reason:</strong> {challan["reason_for_transport"]}</p>
                <p><strong>Transporter:</strong> {challan["transporter_name"] or "Direct Dispatch"}</p>
                <p><strong>Vehicle No:</strong> {challan["vehicle_no"] or "N/A"}</p>
                <p><strong>E-Way Bill No:</strong> {challan["e_way_bill_no"] or "N/A"}</p>
            </div>
        </div>

        <!-- Items Table -->
        <div class="items-table-wrapper">
            <table class="items-table">
                <thead>
                    <tr>
                        <th class="col-sno">S.No</th>
                        <th class="col-desc">Description of Goods / Items (with SN)</th>
                        <th class="col-hsn">HSN Code</th>
                        <th class="col-qty">Qty / Unit</th>
                        <th class="col-rate">Approx Rate (₹)</th>
                        <th class="col-amount">Approx Value (₹)</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
            </table>
        </div>

        <!-- Terms & Dual Signatures -->
        <div class="doc-bottom-grid" style="margin-top:20px;">
            <div class="terms-section" style="width:100%;">
                <h4>Terms & Declaration</h4>
                <div class="terms-content" style="font-size:11px; line-height:1.5;">
                    {challan["terms"] or (settings.get("terms_challan") if settings else "") or f"1. The goods transported under this challan are for delivery/installation/demonstration purpose and not by way of sale. 2. Ownership remains with {settings['name']} until the tax invoice is cleared."}
                </div>
            </div>
        </div>

        <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-top:40px; padding:0 10px;">
            <div style="text-align:center; width:260px;">
                <div style="height:50px;"></div>
                <div style="border-top:1px dashed #94a3b8; padding-top:6px; font-weight:700; font-size:12px; color:#1e293b;">Receiver's Signature & Hospital Seal / Customer Seal</div>
                <div style="font-size:10px; color:#64748b;">(Received above equipment/goods in good condition)</div>
            </div>
            <div style="text-align:center; width:260px;">
                <div style="font-size:11px; font-weight:600; color:#475569; margin-bottom:40px;">For {settings["name"]}</div>
                <div style="border-top:1px solid #1e293b; padding-top:6px; font-weight:700; font-size:12px; color:#1e293b;">Authorized Signatory</div>
            </div>
        </div>
    </div>
</body>
</html>
    """
    return HTMLResponse(content=html_content)
