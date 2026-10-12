import os
import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.database import init_db, get_db, generate_next_invoice_number, generate_next_quote_number
from app.utils.number_to_words import indian_number_to_words
from app.utils.qrcode_gen import generate_upi_qr_base64
from app.utils.backup import create_backup, list_backups

class TestOpenBusinessERP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def test_number_to_words(self):
        self.assertEqual(indian_number_to_words(58500.00), "Rupees Fifty Eight Thousand Five Hundred Only.")
        self.assertEqual(indian_number_to_words(1195000.00), "Rupees Eleven Lakh Ninety Five Thousand Only.")
        self.assertEqual(indian_number_to_words(209523.81), "Rupees Two Lakh Nine Thousand Five Hundred Twenty Three and Eighty One Paise Only.")

    def test_qr_code_generation(self):
        qr_uri = generate_upi_qr_base64("company@upi", "Your Company Name", 50000.00, "INV/26-27/001")
        self.assertTrue(qr_uri.startswith("data:image/png;base64,"))
        self.assertGreater(len(qr_uri), 100)

    def test_next_numbers(self):
        conn = get_db()
        next_inv = generate_next_invoice_number(conn)
        next_quote = generate_next_quote_number(conn)
        conn.close()
        
        self.assertTrue(next_inv.startswith("INV/"))
        self.assertTrue(next_quote.startswith("QT/"))
        print(f"Generated Next Invoice: {next_inv}, Next Quote: {next_quote}")

    def test_dashboard_api(self):
        response = self.client.get("/api/dashboard")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_sales", data)
        self.assertIn("invoice_count", data)
        self.assertGreaterEqual(data["invoice_count"], 1)
        self.assertGreaterEqual(data["quote_count"], 1)

    def test_invoice_print_view(self):
        invoices = self.client.get("/api/invoices").json()
        self.assertGreaterEqual(len(invoices), 1)
        inv = invoices[0]
        response = self.client.get(f"/invoice/print/{inv['id']}")
        self.assertEqual(response.status_code, 200)
        html = response.text
        self.assertIn("TAX INVOICE", html)
        self.assertIn(inv["invoice_no"], html)
        self.assertIn(inv["customer_name"], html)
        self.assertIn("Rupees", html)

    def test_quotation_print_view(self):
        quotes = self.client.get("/api/quotations").json()
        self.assertGreaterEqual(len(quotes), 1)
        q = quotes[0]
        response = self.client.get(f"/quotation/print/{q['id']}")
        self.assertEqual(response.status_code, 200)
        html = response.text
        self.assertIn("QUOTATION ESTIMATE", html)
        self.assertIn(q["quote_no"], html)
        self.assertIn(q["customer_name"], html)
        self.assertIn("Product Visual Specifications", html)

    def test_backup_system(self):
        path = create_backup("unit_test")
        self.assertTrue(os.path.exists(path))
        backups = list_backups()
        self.assertGreaterEqual(len(backups), 1)

    def test_create_and_edit_invoice_service_inclusive(self):
        # Create Service Invoice with Tax Inclusive Rate
        # ₹10,500 inclusive of 5% GST -> Base: 10,000.00, CGST: 250.00, SGST: 250.00, Total: 10,500.00
        payload = {
            "invoice_date": "22-09-2026",
            "due_date": "07-10-2026",
            "invoice_type": "Services",
            "customer_name": "City Care Hospital",
            "customer_address": "Medical College Road, Gorakhpur",
            "customer_gstin": "09AAAAA0000A1Z5",
            "customer_state": "Uttar Pradesh",
            "is_interstate": False,
            "terms": "Annual Maintenance Contract",
            "status": "Unpaid",
            "items": [
                {
                    "description": "Annual Maintenance Service for RMS X-Ray (SN: XR9921)",
                    "item_type": "Service",
                    "hsn_code": "9987",
                    "qty": 1.0,
                    "unit": "Job",
                    "rate": 10000.0,
                    "gst_rate": 5.0,
                    "amount": 10000.0,
                    "is_tax_inclusive": True
                }
            ]
        }
        res = self.client.post("/api/invoices", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        inv_id = data["id"]

        # Verify Created
        inv_detail = self.client.get(f"/api/invoices/{inv_id}").json()
        self.assertEqual(inv_detail["invoice_type"], "Services")
        self.assertEqual(inv_detail["subtotal"], 10000.0)
        self.assertEqual(inv_detail["cgst_amount"], 250.0)
        self.assertEqual(inv_detail["sgst_amount"], 250.0)
        self.assertEqual(inv_detail["grand_total"], 10500.0)

        # Edit the invoice with PUT
        payload["items"][0]["rate"] = 20000.0
        payload["items"][0]["amount"] = 20000.0
        update_res = self.client.put(f"/api/invoices/{inv_id}", json=payload)
        self.assertEqual(update_res.status_code, 200)

        # Verify Updated
        inv_updated = self.client.get(f"/api/invoices/{inv_id}").json()
        self.assertEqual(inv_updated["subtotal"], 20000.0)
        self.assertEqual(inv_updated["cgst_amount"], 500.0)
        self.assertEqual(inv_updated["sgst_amount"], 500.0)
        self.assertEqual(inv_updated["grand_total"], 21000.0)

    def test_delivery_challan_crud_and_conversion(self):
        # 1. Test next challan number
        next_res = self.client.get("/api/challans/next-number")
        self.assertEqual(next_res.status_code, 200)
        next_no = next_res.json()["next_challan_no"]
        self.assertTrue(next_no.startswith("DC/"))

        # 2. Create Delivery Challan
        challan_payload = {
            "challan_date": "22-09-2026",
            "customer_name": "Apex Trauma & Heart Centre",
            "customer_address": "Medical Road, Gorakhpur",
            "customer_gstin": "09ABCDE1234F1Z5",
            "customer_state": "Uttar Pradesh",
            "reason_for_transport": "Supply for Installation & Commissioning",
            "transporter_name": "Direct Vehicle",
            "vehicle_no": "UP 53 AB 5678",
            "e_way_bill_no": "191029384756",
            "terms": "Goods sent for hospital installation under Rule 55.",
            "status": "Dispatched",
            "items": [
                {
                    "description": "RMS Digital 100 mA Mobile X Ray Machine with trolly (SN: XR-2026-88)",
                    "hsn_code": "9022",
                    "qty": 1.0,
                    "unit": "Pcs",
                    "approx_rate": 209523.81,
                    "approx_amount": 209523.81
                }
            ]
        }
        create_res = self.client.post("/api/challans", json=challan_payload)
        self.assertEqual(create_res.status_code, 200)
        c_data = create_res.json()
        c_id = c_data["id"]
        c_no = c_data["challan_no"]

        # 3. Retrieve detail
        detail_res = self.client.get(f"/api/challans/{c_id}")
        self.assertEqual(detail_res.status_code, 200)
        detail = detail_res.json()
        self.assertEqual(detail["customer_name"], "Apex Trauma & Heart Centre")
        self.assertEqual(detail["vehicle_no"], "UP 53 AB 5678")
        self.assertEqual(detail["approx_total"], 209523.81)
        self.assertEqual(len(detail["items"]), 1)

        # 4. Print layout
        print_res = self.client.get(f"/challan/print/{c_id}")
        self.assertEqual(print_res.status_code, 200)
        html = print_res.text
        self.assertIn("DELIVERY CHALLAN", html)
        self.assertIn("Rule 55 of CGST Rules", html)
        self.assertIn(c_no, html)
        self.assertIn("Apex Trauma & Heart Centre", html)
        self.assertIn("Receiver's Signature & Hospital Seal", html)

        # 5. Convert to Tax Invoice
        conv_res = self.client.post(f"/api/challans/{c_id}/convert-to-invoice")
        self.assertEqual(conv_res.status_code, 200)
        conv_data = conv_res.json()
        inv_id = conv_data["invoice_id"]
        self.assertIsNotNone(inv_id)

        # Verify challan status updated to Invoiced
        c_after = self.client.get(f"/api/challans/{c_id}").json()
        self.assertEqual(c_after["status"], "Invoiced")
        self.assertEqual(c_after["invoice_id"], inv_id)

        # Verify generated invoice
        inv_detail = self.client.get(f"/api/invoices/{inv_id}").json()
        self.assertEqual(inv_detail["customer_name"], "Apex Trauma & Heart Centre")
        self.assertEqual(inv_detail["vehicle_no"], "UP 53 AB 5678")
        self.assertEqual(len(inv_detail["items"]), 1)

    def test_gst_summary_and_csv_reports(self):
        # 1. Summary API
        summary_res = self.client.get("/api/reports/gst-summary")
        self.assertEqual(summary_res.status_code, 200)
        data = summary_res.json()
        self.assertIn("total_taxable", data)
        self.assertIn("total_cgst", data)
        self.assertIn("total_sgst", data)
        self.assertIn("total_tax", data)
        self.assertIn("b2b_invoices", data)
        self.assertIn("b2cs_invoices", data)
        self.assertIn("hsn_summary", data)

        # 2. GSTR-1 CSV
        gstr1_res = self.client.get("/api/reports/gstr1-csv")
        self.assertEqual(gstr1_res.status_code, 200)
        self.assertEqual(gstr1_res.headers["content-type"], "text/csv; charset=utf-8")
        csv_text = gstr1_res.text
        self.assertIn("GSTR-1 SUMMARY REPORT", csv_text)
        self.assertIn("TABLE 4: B2B INVOICES", csv_text)
        self.assertIn("TABLE 7: B2CS", csv_text)
        self.assertIn("TABLE 12: HSN/SAC SUMMARY", csv_text)

        # 3. Sales Register CSV
        sales_res = self.client.get("/api/reports/sales-register-csv")
        self.assertEqual(sales_res.status_code, 200)
        self.assertEqual(sales_res.headers["content-type"], "text/csv; charset=utf-8")
        sales_csv = sales_res.text
        self.assertIn("Invoice No", sales_csv)
        self.assertIn("Customer / Hospital", sales_csv)
        self.assertIn("Taxable Value (INR)", sales_csv)

    def test_company_customization_and_manifest(self):
        # 1. Fetch current settings
        res = self.client.get("/api/settings")
        self.assertEqual(res.status_code, 200)
        curr_settings = res.json()
        
        # 2. Update settings to a custom company
        new_payload = dict(curr_settings)
        new_payload["name"] = "Apex Global Industrial Ltd"
        new_payload["tagline"] = "Advanced Engineering & Automation"
        new_payload["invoice_prefix"] = "AGI/"
        new_payload["quotation_prefix"] = "AGI/Q-"
        new_payload["challan_prefix"] = "AGI/DC-"
        
        update_res = self.client.put("/api/settings", json=new_payload)
        self.assertEqual(update_res.status_code, 200)
        
        # 3. Verify next invoice number uses new custom prefix
        inv_no_res = self.client.get("/api/invoices/next-number")
        self.assertEqual(inv_no_res.status_code, 200)
        self.assertTrue(inv_no_res.json()["next_invoice_no"].startswith("AGI/"))

        # 4. Verify manifest endpoint returns custom company name
        manifest_res = self.client.get("/manifest.json")
        self.assertEqual(manifest_res.status_code, 200)
        m_data = manifest_res.json()
        self.assertIn("Apex Global Industrial Ltd", m_data["name"])

        # 5. Test logo reset endpoint
        reset_res = self.client.post("/api/settings/reset-logo")
        self.assertEqual(reset_res.status_code, 200)

        # 6. Revert back to original settings
        self.client.put("/api/settings", json=curr_settings)

    @classmethod
    def tearDownClass(cls):
        from pathlib import Path
        for b in Path("data/backups").glob("*.db"):
            b.unlink(missing_ok=True)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM invoices WHERE id > 1")
        cursor.execute("DELETE FROM invoice_items WHERE invoice_id > 1")
        cursor.execute("DELETE FROM delivery_challans")
        cursor.execute("DELETE FROM delivery_challan_items")
        conn.commit()
        conn.close()

if __name__ == "__main__":
    unittest.main()

