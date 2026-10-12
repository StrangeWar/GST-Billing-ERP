# 🏢 Open Business ERP - Local Billing, Quotation & Inventory System

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite3-003B57.svg)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Privacy First](https://img.shields.io/badge/Privacy-100%25%20Offline%20Local-success.svg)](#-data-privacy--backup-protection)

An ultra-fast, local, privacy-first **Business ERP Billing, Quotation & Inventory Management System** built with **Python (FastAPI)** and a modern Single-Page Web UI.

Designed to be **100% white-label and open source** — anyone can clone this repository, input their own **company name, logo, GSTIN/tax registration, bank details, and numbering prefixes**, and start issuing professional GST invoices and quotations in seconds!

---

## 🌟 Highlights

- **Zero Cloud Subscriptions**: No monthly fees, no vendor lock-in. Your data stays 100% private on your own computer.
- **1-Click Launch**: Double-click `Start_ERP.bat` on Windows or run `./start_erp.sh` on Linux/macOS.
- **Native Desktop App (PWA)**: Installable directly into Windows/macOS with your company's own logo and desktop icon.
- **100% White-Label**: Easily customize company name, address, logo, document series prefixes (`INV/`, `QT/`, `DC/`), bank account, and offline UPI QR codes via the built-in Settings UI.
- **Automated Indian GST Engine**: Automatically computes and splits **CGST + SGST** (intrastate) and **IGST** (interstate), with numbers converted to Indian currency words (Lakhs/Crores).
- **Rule 55 Delivery Challans**: Full support for transport & demonstration challans with 1-click invoice conversion.
- **Data Protection**: Automated snapshot backups on startup and upon every invoice/quote creation, with 1-click instant restore.

---

## 🚀 Quick Start

### Windows (1-Click Launch)
1. Double-click **`Start_ERP.bat`**.
2. It will automatically check dependencies, start the server, and open your browser at **`http://localhost:8000`**.
3. **Install as Desktop App**: Click the install icon in your browser's address bar (Chrome, Edge, or Brave) to run it as an independent desktop application on your Windows Taskbar!

### Linux / macOS
```bash
# Clone the repository
git clone https://github.com/your-username/open-business-erp.git
cd open-business-erp

# Make launcher executable and run
chmod +x start_erp.sh
./start_erp.sh
```

### Manual Installation
```bash
# 1. Create and activate virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch server
uvicorn app.main:app --host 127.0.0.1 --port 8000
```
Open your browser and navigate to **`http://localhost:8000`**.

---

## 🎨 How to Customize for Your Company (White-Label Setup)

You do **not** need to edit code to rebrand the ERP for your business:

1. Open the ERP at `http://localhost:8000`.
2. Click **Settings** in the left sidebar.
3. Configure your business details:
   - **Company Logo**: Click **Change / Upload Logo** (supports PNG, JPG, WebP, SVG). A preview immediately displays across the sidebar and on all printed documents. You can also click **Reset to Default** at any time.
   - **Company Profile**: Enter your **Company Name**, **Tagline**, **Registered Address**, **Phone**, **Email**, and **GSTIN / Tax ID**.
   - **State Code Auto-Fill**: Typing your 15-digit GSTIN automatically extracts and sets your State Code (e.g. `09` for UP, `27` for Maharashtra, `07` for Delhi).
   - **Document Numbering Prefixes**:
     - *Invoice Prefix*: e.g. `INV/` generates `INV/26-27/001`
     - *Quotation Prefix*: e.g. `QT/` generates `QT/26-27/001`
     - *Delivery Challan Prefix*: e.g. `DC/` generates `DC/26-27/001`
   - **Bank & UPI Details**: Enter your Bank Name, Branch, Account No, IFSC, and UPI Virtual Payment Address (e.g. `company@upi`).
     > **Instant UPI QR**: The ERP automatically renders an offline UPI payment QR code with the exact invoice amount on every printed invoice!
   - **Default Terms & Conditions**: Set your standard delivery terms and warranty conditions for Invoices, Quotes, and Challans.
4. Click **Save Settings** — all invoices, quotations, reports, and your desktop app update immediately!

---

## 🛠️ Features & Modules

### 1. 🧾 Tax Invoices
- **Auto-Sequential Numbering**: Generates sequential invoices per financial year based on your custom prefix.
- **Dual GST Calculations**: Handles intrastate CGST/SGST splits and interstate IGST automatically based on customer state.
- **Serial Number (SN) Tracking**: Track equipment, machine, or hardware serial numbers on each line item.
- **Tax-Inclusive or Exclusive**: Toggle per item whether rate includes GST or is tax-exclusive.
- **Indian Currency in Words**: Automatically converts amounts (e.g. *Rupees Fifty Eight Thousand Five Hundred Only.*).
- **Pixel-Perfect PDF / Print**: Download client-side PDF with one click or print cleanly to A4 paper.

### 2. 📋 Quotations & Estimates
- Sequential quote numbering (e.g. `QT/26-27/001`).
- Page 1: Comprehensive financial quote, HSN codes, GST summary, payment & delivery terms.
- Page 2: **Product Visual Specifications** catalog displaying pictures, model names, and descriptions of quoted products.
- **1-Click Invoice Conversion**: Convert accepted quotations into active Tax Invoices with a single click.

### 3. 🚚 Delivery Challans (Rule 55 Compliant)
- Issue statutory Delivery Challans for goods transported for demonstration, installation, or approval under Rule 55 of CGST Rules, 2017.
- Capture Transporter Name, Vehicle Number, and E-Way Bill Number.
- **1-Click Invoicing**: Convert completed delivery challans directly into final Tax Invoices.

### 4. 📊 GST Reports & Filing Export
- **GSTR-1 Summary**: Real-time totals for Table 4 (B2B), Table 7 (B2CS), and Table 12 (HSN/SAC summary).
- **1-Click CSV Exports**: Download audit-ready CSV spreadsheets for GSTR-1 and the Sales Register.

### 5. 👥 Customer & Product Catalog
- **Customer Directory**: Store business names, contact persons, phone numbers, addresses, and GSTINs for instant autofill.
- **Product & Service Catalog**: Manage items with default HSN/SAC codes, default rates, GST tax brackets, and product images.

### 6. 🛡️ Data Privacy & Backup Protection
- **Offline & Self-Contained**: Stored entirely in a single portable SQLite database file (`data/erp.db`).
- **Live Snapshots**: Automated timestamped backups created on startup, on invoice creation, and on quotations.
- **1-Click Restore**: Easily download backups to a USB pen drive or upload a `.db` backup file to restore your entire business database on a new laptop in seconds.

---

## 📁 System Architecture & Directory Structure

```text
├── app/
│   ├── database.py         # SQLite schema, migrations, FY number generators
│   ├── main.py             # FastAPI REST endpoints, print layouts & PWA manifest
│   ├── models.py           # Pydantic data models & validation
│   ├── static/             # Frontend Single-Page App (HTML, Tailwind CSS, Lucide, JS)
│   │   ├── css/            # Print styles & responsive styling
│   │   ├── images/         # Default logos, product catalog images
│   │   ├── js/             # Client application logic (app.js, html2pdf)
│   │   ├── index.html      # Main Single-Page Application interface
│   │   └── manifest.json   # Desktop PWA configuration
│   └── utils/
│       ├── backup.py       # Live SQLite backup & restore engine
│       ├── number_to_words.py # Indian numbering currency formatter
│       └── qrcode_gen.py   # Offline base64 UPI QR code generator
├── data/
│   ├── erp.db              # Portable SQLite database (git-ignored)
│   └── backups/            # Timestamped database snapshots (git-ignored)
├── apply_logo.py           # Helper script to apply any image as company logo
├── generate_default_logo.py # Generates clean default open-source logo
├── requirements.txt        # Python library dependencies
├── Start_ERP.bat           # 1-Click launcher for Windows
├── start_erp.sh            # 1-Click launcher for Linux / macOS
├── test_erp.py             # Automated unit test suite
├── LICENSE                 # MIT License
└── README.md
```

---

## 🧪 Running Tests

To verify database integrity, numbering series, GST calculations, and API endpoints, run the included test suite:

```bash
python test_erp.py
```

All tests run against a local instance and validate invoice creation, UPI QR generation, number-to-words conversion, delivery challan lifecycle, and custom company settings.

---

## 🤝 Contributing

Contributions, feature requests, and improvements are welcome!
1. Fork this repository.
2. Create a feature branch (`git checkout -b feature/NewFeature`).
3. Commit your changes (`git commit -m 'Add NewFeature'`).
4. Push to the branch (`git push origin feature/NewFeature`).
5. Open a Pull Request.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) — you are free to use, modify, distribute, and white-label this software for personal or commercial use.
