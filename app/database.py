import sqlite3
import datetime
from pathlib import Path

DB_PATH = Path("data/erp.db")

def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_financial_year(dt: datetime.date = None) -> str:
    """
    Returns financial year in YY-YY format (e.g. 26-27 for FY 2026-2027, starting April 1).
    """
    if dt is None:
        dt = datetime.date.today()
    year = dt.year
    if dt.month >= 4:
        # April or later -> current year to next year
        y1 = year % 100
        y2 = (year + 1) % 100
    else:
        # Before April -> previous year to current year
        y1 = (year - 1) % 100
        y2 = year % 100
    return f"{y1:02d}-{y2:02d}"

def generate_next_invoice_number(conn) -> str:
    fy = get_financial_year()
    cursor = conn.cursor()
    cursor.execute("SELECT invoice_prefix FROM company_settings WHERE id = 1")
    row = cursor.fetchone()
    raw_prefix = row["invoice_prefix"] if row and row["invoice_prefix"] else "INV/"
    if not (raw_prefix.endswith('/') or raw_prefix.endswith('-')):
        raw_prefix += '/'
    prefix = f"{raw_prefix}{fy}/"

    cursor.execute("""
        SELECT invoice_no FROM invoices 
        WHERE financial_year = ? 
        ORDER BY id DESC
    """, (fy,))
    rows = cursor.fetchall()
    
    max_num = 0
    for row in rows:
        inv_no = row["invoice_no"]
        if inv_no.startswith(prefix):
            try:
                num_part = int(inv_no[len(prefix):])
                if num_part > max_num:
                    max_num = num_part
            except ValueError:
                pass
    
    next_num = max_num + 1
    return f"{prefix}{next_num:03d}"

def generate_next_quote_number(conn) -> str:
    fy = get_financial_year()
    cursor = conn.cursor()
    cursor.execute("SELECT quotation_prefix FROM company_settings WHERE id = 1")
    row = cursor.fetchone()
    raw_prefix = row["quotation_prefix"] if row and row["quotation_prefix"] else "QT/"
    if not (raw_prefix.endswith('/') or raw_prefix.endswith('-')):
        raw_prefix += '/'
    prefix = f"{raw_prefix}{fy}/"

    cursor.execute("""
        SELECT quote_no FROM quotations 
        WHERE financial_year = ? 
        ORDER BY id DESC
    """, (fy,))
    rows = cursor.fetchall()
    
    max_num = 0
    for row in rows:
        q_no = row["quote_no"]
        if q_no.startswith(prefix):
            try:
                num_part = int(q_no[len(prefix):])
                if num_part > max_num:
                    max_num = num_part
            except ValueError:
                pass
                
    next_num = max_num + 1
    return f"{prefix}{next_num:03d}"

def generate_next_challan_number(conn) -> str:
    fy = get_financial_year()
    cursor = conn.cursor()
    raw_prefix = "DC/"
    try:
        cursor.execute("SELECT challan_prefix FROM company_settings WHERE id = 1")
        row = cursor.fetchone()
        if row and "challan_prefix" in row.keys() and row["challan_prefix"]:
            raw_prefix = row["challan_prefix"]
    except Exception:
        raw_prefix = "DC/"
    if not (raw_prefix.endswith('/') or raw_prefix.endswith('-')):
        raw_prefix += '/'
    prefix = f"{raw_prefix}{fy}/"

    cursor.execute("""
        SELECT challan_no FROM delivery_challans 
        WHERE financial_year = ? 
        ORDER BY id DESC
    """, (fy,))
    rows = cursor.fetchall()
    
    max_num = 0
    for row in rows:
        c_no = row["challan_no"]
        if c_no.startswith(prefix):
            try:
                num_part = int(c_no[len(prefix):])
                if num_part > max_num:
                    max_num = num_part
            except ValueError:
                pass
                
    next_num = max_num + 1
    return f"{prefix}{next_num:03d}"

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Company Settings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS company_settings (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        tagline TEXT DEFAULT '',
        address TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT NOT NULL,
        gstin TEXT NOT NULL,
        state TEXT NOT NULL,
        state_code TEXT NOT NULL,
        bank_name TEXT NOT NULL,
        branch TEXT NOT NULL,
        account_no TEXT NOT NULL,
        ifsc TEXT NOT NULL,
        upi_address TEXT NOT NULL,
        upi_name TEXT NOT NULL,
        invoice_prefix TEXT DEFAULT 'INV/',
        quotation_prefix TEXT DEFAULT 'QT/',
        challan_prefix TEXT DEFAULT 'DC/',
        terms_invoice TEXT DEFAULT 'Thank you for your business!',
        terms_quotation TEXT DEFAULT '',
        terms_challan TEXT DEFAULT '',
        logo_url TEXT DEFAULT '/static/images/logo.png'
    )
    """)
    
    # 2. Customers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        contact_person TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        email TEXT DEFAULT '',
        address TEXT NOT NULL,
        city TEXT DEFAULT '',
        state TEXT DEFAULT 'Uttar Pradesh',
        state_code TEXT DEFAULT '09',
        gstin TEXT DEFAULT 'N/A',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 3. Products
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT DEFAULT 'Medical Equipment',
        hsn_code TEXT DEFAULT '9018',
        unit TEXT DEFAULT 'Pcs',
        default_rate REAL DEFAULT 0.0,
        gst_rate REAL DEFAULT 5.0,
        description TEXT DEFAULT '',
        image_url TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 4. Invoices
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_no TEXT UNIQUE NOT NULL,
        financial_year TEXT NOT NULL,
        invoice_date TEXT NOT NULL,
        due_date TEXT,
        customer_id INTEGER,
        customer_name TEXT NOT NULL,
        customer_address TEXT NOT NULL,
        customer_gstin TEXT DEFAULT 'N/A',
        customer_state TEXT DEFAULT 'Uttar Pradesh',
        is_interstate INTEGER DEFAULT 0,
        subtotal REAL DEFAULT 0.0,
        cgst_amount REAL DEFAULT 0.0,
        sgst_amount REAL DEFAULT 0.0,
        igst_amount REAL DEFAULT 0.0,
        grand_total REAL DEFAULT 0.0,
        amount_in_words TEXT,
        terms TEXT,
        status TEXT DEFAULT 'Unpaid',
        quotation_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 5. Invoice Items
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        product_id INTEGER,
        description TEXT NOT NULL,
        hsn_code TEXT DEFAULT '9018',
        qty REAL DEFAULT 1,
        unit TEXT DEFAULT 'Pcs',
        rate REAL NOT NULL,
        gst_rate REAL DEFAULT 5.0,
        amount REAL NOT NULL,
        FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
    )
    """)
    
    # 6. Quotations
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quotations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quote_no TEXT UNIQUE NOT NULL,
        financial_year TEXT NOT NULL,
        quote_date TEXT NOT NULL,
        valid_until TEXT,
        customer_id INTEGER,
        customer_name TEXT NOT NULL,
        customer_address TEXT NOT NULL,
        customer_gstin TEXT DEFAULT 'N/A',
        customer_state TEXT DEFAULT 'Uttar Pradesh',
        is_interstate INTEGER DEFAULT 0,
        subtotal REAL DEFAULT 0.0,
        cgst_amount REAL DEFAULT 0.0,
        sgst_amount REAL DEFAULT 0.0,
        igst_amount REAL DEFAULT 0.0,
        grand_total REAL DEFAULT 0.0,
        amount_in_words TEXT,
        terms TEXT,
        status TEXT DEFAULT 'Active',
        converted_invoice_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 7. Quotation Items
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quotation_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quotation_id INTEGER NOT NULL,
        product_id INTEGER,
        description TEXT NOT NULL,
        hsn_code TEXT DEFAULT '9018',
        qty REAL DEFAULT 1,
        unit TEXT DEFAULT 'Pcs',
        rate REAL NOT NULL,
        gst_rate REAL DEFAULT 5.0,
        amount REAL NOT NULL,
        product_image_url TEXT DEFAULT '',
        item_type TEXT DEFAULT 'Goods',
        is_tax_inclusive INTEGER DEFAULT 0,
        FOREIGN KEY (quotation_id) REFERENCES quotations(id) ON DELETE CASCADE
    )
    """)

    # 8. Delivery Challans
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS delivery_challans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        challan_no TEXT UNIQUE NOT NULL,
        financial_year TEXT NOT NULL,
        challan_date TEXT NOT NULL,
        customer_id INTEGER,
        customer_name TEXT NOT NULL,
        customer_address TEXT NOT NULL,
        customer_gstin TEXT DEFAULT 'N/A',
        customer_state TEXT DEFAULT 'Uttar Pradesh',
        reason_for_transport TEXT DEFAULT 'Supply for Installation & Commissioning',
        transporter_name TEXT DEFAULT '',
        vehicle_no TEXT DEFAULT '',
        e_way_bill_no TEXT DEFAULT '',
        approx_total REAL DEFAULT 0.0,
        terms TEXT DEFAULT '',
        status TEXT DEFAULT 'Dispatched',
        invoice_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 9. Delivery Challan Items
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS delivery_challan_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        challan_id INTEGER NOT NULL,
        product_id INTEGER,
        description TEXT NOT NULL,
        hsn_code TEXT DEFAULT '9018',
        qty REAL DEFAULT 1,
        unit TEXT DEFAULT 'Pcs',
        approx_rate REAL DEFAULT 0.0,
        approx_amount REAL DEFAULT 0.0,
        FOREIGN KEY (challan_id) REFERENCES delivery_challans(id) ON DELETE CASCADE
    )
    """)

    # Column Migrations for Existing Databases
    tables_to_migrate = [
        ("invoices", "invoice_type", "TEXT DEFAULT 'Goods'"),
        ("invoices", "e_way_bill_no", "TEXT DEFAULT ''"),
        ("invoices", "vehicle_no", "TEXT DEFAULT ''"),
        ("invoices", "transporter_name", "TEXT DEFAULT ''"),
        ("invoices", "po_no", "TEXT DEFAULT ''"),
        ("invoices", "po_date", "TEXT DEFAULT ''"),
        ("quotations", "invoice_type", "TEXT DEFAULT 'Goods'"),
        ("invoice_items", "item_type", "TEXT DEFAULT 'Goods'"),
        ("invoice_items", "is_tax_inclusive", "INTEGER DEFAULT 0"),
        ("quotation_items", "item_type", "TEXT DEFAULT 'Goods'"),
        ("quotation_items", "is_tax_inclusive", "INTEGER DEFAULT 0"),
        ("products", "is_tax_inclusive", "INTEGER DEFAULT 0"),
        ("company_settings", "challan_prefix", "TEXT DEFAULT 'DC/'"),
        ("company_settings", "terms_challan", "TEXT DEFAULT ''"),
        ("company_settings", "logo_url", "TEXT DEFAULT '/static/images/logo.png'"),
    ]
    for tbl, col, col_def in tables_to_migrate:
        cursor.execute(f"PRAGMA table_info({tbl})")
        existing_cols = [row["name"] for row in cursor.fetchall()]
        if col not in existing_cols:
            try:
                cursor.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {col_def}")
            except Exception as e:
                print(f"Migration error for {tbl}.{col}: {e}")

    
    # Seed Initial Company Settings
    cursor.execute("SELECT COUNT(*) FROM company_settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO company_settings (
            id, name, tagline, address, phone, email, gstin, state, state_code,
            bank_name, branch, account_no, ifsc, upi_address, upi_name,
            invoice_prefix, quotation_prefix, challan_prefix,
            terms_invoice, terms_quotation, terms_challan, logo_url
        ) VALUES (
            1,
            'Your Company Name',
            'Commercial & Billing Solutions',
            '123 Business Street, Industrial Area',
            '+91 9876543210',
            'contact@yourcompany.com',
            '09AAAAA0000A1Z5',
            'Uttar Pradesh',
            '09',
            'State Bank of India',
            'Main Branch',
            '123456789012',
            'SBIN0001234',
            'company@upi',
            'Your Company Name',
            'INV/',
            'QT/',
            'DC/',
            'Thank you for your business!',
            '1. Delivery: Standard delivery period is 2 to 4 weeks.\n2. Payment: 50% advance & 50% against dispatch.',
            '1. The goods transported under this challan are for delivery/installation/demonstration purpose and not by way of sale.\n2. Ownership remains with the supplier until the tax invoice is cleared.',
            '/static/images/logo.png'
        )
        """)
        
    # Seed Initial Customers
    cursor.execute("SELECT COUNT(*) FROM customers")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
        INSERT INTO customers (name, contact_person, phone, email, address, city, state, state_code, gstin)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            ("City Healthcare Hospital", "Dr. Rajesh Sharma", "+91 9876543211", "care@cityhospital.com", "Plot No. 45, Civil Lines, Medical Enclave", "Lucknow", "Uttar Pradesh", "09", "09AAACH1234F1Z1"),
            ("Metro Diagnostics & Imaging Center", "Pooja Verma", "+91 9876543212", "billing@metrodiag.com", "Shop 12-14, Commercial Complex, Sector 18", "Noida", "Uttar Pradesh", "09", "09ABCDE5678G1Z2")
        ])
        
    # Seed Initial Products
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
        INSERT INTO products (name, category, hsn_code, unit, default_rate, gst_rate, description, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            ("Multi-Parameter Patient Monitor (12.1-inch)", "Patient Monitor", "9018", "Pcs", 55000.00, 5.0, "High-precision multi-parameter patient monitor with display and ECG/SpO2 modules", "/static/images/products/patient_monitor.png"),
            ("Mobile 100 mA Diagnostic X-Ray Unit", "X-Ray Equipment", "9022", "Pcs", 210000.00, 5.0, "High-frequency mobile 100 mA X-Ray unit with articulated counter-balanced arm", "/static/images/products/xray_machine.png"),
            ("Digital Radiography Detector & Acquisition Workstation", "Radiography System", "9022", "Pcs", 925000.00, 5.0, "High-resolution flat panel DR detector and image processing software workstation", "/static/images/products/radiography_system.png")
        ])
        
    # Seed Initial Sample Invoice (INV/26-27/001)
    cursor.execute("SELECT COUNT(*) FROM invoices")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO invoices (
            invoice_no, financial_year, invoice_date, due_date, customer_id, customer_name,
            customer_address, customer_gstin, customer_state, is_interstate,
            subtotal, cgst_amount, sgst_amount, igst_amount, grand_total, amount_in_words,
            terms, status
        ) VALUES (
            'INV/26-27/001', '26-27', '04-06-2026', '19-06-2026', 1, 'City Healthcare Hospital',
            'Plot No. 45, Civil Lines, Medical Enclave', '09AAACH1234F1Z1', 'Uttar Pradesh', 0,
            55000.00, 1375.00, 1375.00, 0.0, 57750.00,
            'Rupees Fifty Seven Thousand Seven Hundred Fifty Only.',
            'Thank you for your business!', 'Unpaid'
        )
        """)
        inv_id = cursor.lastrowid
        cursor.execute("""
        INSERT INTO invoice_items (invoice_id, product_id, description, hsn_code, qty, unit, rate, gst_rate, amount)
        VALUES (?, 1, 'Multi-Parameter Patient Monitor (12.1-inch) [SN: PM-2026-001]', '9018', 1, 'Pcs', 55000.00, 5.0, 55000.00)
        """, (inv_id,))

    # Seed Initial Sample Quotation (QT/26-27/001)
    cursor.execute("SELECT COUNT(*) FROM quotations")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO quotations (
            quote_no, financial_year, quote_date, valid_until, customer_id, customer_name,
            customer_address, customer_gstin, customer_state, is_interstate,
            subtotal, cgst_amount, sgst_amount, igst_amount, grand_total, amount_in_words,
            terms, status
        ) VALUES (
            'QT/26-27/001', '26-27', '04-07-2026', '03-08-2026', 2, 'Metro Diagnostics & Imaging Center',
            'Shop 12-14, Commercial Complex, Sector 18', '09ABCDE5678G1Z2', 'Uttar Pradesh', 0,
            1135000.00, 28375.00, 28375.00, 0.0, 1191750.00,
            'Rupees Eleven Lakh Ninety One Thousand Seven Hundred Fifty Only.',
            '1. Delivery: Standard delivery period is 2 to 4 weeks from order confirmation.\n2. Payment: 50% advance & 50% against dispatch in favour of the company.\n3. Warranty: 12 months comprehensive warranty from installation date.',
            'Active'
        )
        """)
        q_id = cursor.lastrowid
        cursor.executemany("""
        INSERT INTO quotation_items (quotation_id, product_id, description, hsn_code, qty, unit, rate, gst_rate, amount, product_image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (q_id, 2, 'Mobile 100 mA Diagnostic X-Ray Unit', '9022', 1, 'Pcs', 210000.00, 5.0, 210000.00, '/static/images/products/xray_machine.png'),
            (q_id, 3, 'Digital Radiography Detector & Acquisition Workstation', '9022', 1, 'Pcs', 925000.00, 5.0, 925000.00, '/static/images/products/radiography_system.png')
        ])

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
