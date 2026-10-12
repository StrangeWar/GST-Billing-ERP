// Open Business ERP - Client Application Logic

const state = {
    currentTab: 'dashboard',
    dashboard: null,
    invoices: [],
    quotations: [],
    challans: [],
    gstSummary: null,
    customers: [],
    products: [],
    backups: [],
    settings: null,
    currentPreviewUrl: ''
};

// ---------------- THEME / DARK MODE ----------------
function initTheme() {
    const saved = localStorage.getItem('theme');
    if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
        updateThemeIcon(true);
    } else {
        document.documentElement.classList.remove('dark');
        updateThemeIcon(false);
    }
}

function toggleDarkMode() {
    const isDark = document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    updateThemeIcon(isDark);
}

function updateThemeIcon(isDark) {
    const icon = document.getElementById('theme-icon');
    if (icon) {
        icon.setAttribute('data-lucide', isDark ? 'sun' : 'moon');
        if (window.lucide) lucide.createIcons();
    }
}

// ---------------- UTILITIES ----------------
function formatCurrency(val) {
    if (val === undefined || val === null) return '₹0.00';
    return '₹' + Number(val).toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function getTodayFormatted() {
    const d = new Date();
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    return `${day}-${month}-${year}`;
}

function getFutureDateFormatted(days) {
    const d = new Date();
    d.setDate(d.getDate() + days);
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    return `${day}-${month}-${year}`;
}

// ---------------- NAVIGATION & TAB SWITCHING ----------------
function switchTab(tabName) {
    state.currentTab = tabName;
    const tabs = ['dashboard', 'invoices', 'quotations', 'challans', 'reports', 'customers', 'products', 'backups', 'settings'];
    
    tabs.forEach(t => {
        const viewEl = document.getElementById(`view-${t}`);
        const navEl = document.getElementById(`nav-${t}`);
        if (viewEl && navEl) {
            if (t === tabName) {
                viewEl.classList.remove('hidden');
                navEl.className = "nav-btn w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all bg-blue-600 text-white shadow-md";
            } else {
                viewEl.classList.add('hidden');
                navEl.className = "nav-btn w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all text-slate-300 hover:bg-slate-800 hover:text-white";
            }
        }
    });

    const titles = {
        dashboard: 'Dashboard',
        invoices: 'Tax Invoices',
        quotations: 'Quotation Estimates',
        challans: 'Delivery Challans (Rule 55)',
        reports: 'Tax & Accounting (GST Compliance)',
        customers: 'Hospitals & Medical Clients',
        products: 'Medical Equipment Catalog',
        backups: 'Data Backup & Protection',
        settings: 'Company Profile & Bank Details'
    };
    document.getElementById('page-title').innerText = titles[tabName] || 'Dashboard';
    
    if (tabName === 'dashboard') loadDashboard();
    if (tabName === 'invoices') loadInvoices();
    if (tabName === 'quotations') loadQuotations();
    if (tabName === 'challans') loadChallans();
    if (tabName === 'reports') loadGstReports();
    if (tabName === 'customers') loadCustomers();
    if (tabName === 'products') loadProducts();
    if (tabName === 'backups') loadBackups();
    if (tabName === 'settings') loadSettings();

    if (window.lucide) lucide.createIcons();
}

function openModal(id) {
    document.getElementById(id).classList.remove('hidden');
}

function closeModal(id) {
    document.getElementById(id).classList.add('hidden');
    if (id === 'modal-preview') {
        document.title = (state.settings && state.settings.name ? `${state.settings.name} - ERP System` : 'Open Business ERP');
    }
}

// ---------------- IN-APP PREVIEW MODAL ----------------
function previewInvoice(id, invoiceNo) {
    state.currentPreviewUrl = `/invoice/print/${id}`;
    document.getElementById('preview-modal-title').innerText = `Preview Tax Invoice - ${invoiceNo}`;
    const iframe = document.getElementById('preview-iframe');
    iframe.src = state.currentPreviewUrl;
    iframe.onload = () => {
        try {
            if (iframe.contentDocument && iframe.contentDocument.title) {
                document.title = iframe.contentDocument.title;
            }
        } catch(e) {}
    };
    openModal('modal-preview');
}

function previewQuotation(id, quoteNo) {
    state.currentPreviewUrl = `/quotation/print/${id}`;
    document.getElementById('preview-modal-title').innerText = `Preview Quotation Estimate - ${quoteNo}`;
    const iframe = document.getElementById('preview-iframe');
    iframe.src = state.currentPreviewUrl;
    iframe.onload = () => {
        try {
            if (iframe.contentDocument && iframe.contentDocument.title) {
                document.title = iframe.contentDocument.title;
            }
        } catch(e) {}
    };
    openModal('modal-preview');
}

function previewChallan(id, challanNo) {
    state.currentPreviewUrl = `/challan/print/${id}`;
    document.getElementById('preview-modal-title').innerText = `Preview Delivery Challan - ${challanNo}`;
    const iframe = document.getElementById('preview-iframe');
    iframe.src = state.currentPreviewUrl;
    iframe.onload = () => {
        try {
            if (iframe.contentDocument && iframe.contentDocument.title) {
                document.title = iframe.contentDocument.title;
            }
        } catch(e) {}
    };
    openModal('modal-preview');
}

function printFromPreview() {
    const iframe = document.getElementById('preview-iframe');
    if (iframe && iframe.contentWindow) {
        try {
            if (iframe.contentDocument && iframe.contentDocument.title) {
                document.title = iframe.contentDocument.title;
            }
        } catch(e) {}
        iframe.contentWindow.focus();
        iframe.contentWindow.print();
    }
}

async function downloadPdfFromPreview() {
    const iframe = document.getElementById('preview-iframe');
    if (!iframe || !iframe.contentDocument || !iframe.contentDocument.body) {
        alert('Preview document is still loading, please wait a moment.');
        return;
    }

    const downloadBtn = document.getElementById('preview-download-btn');
    let originalHtml = '';
    if (downloadBtn) {
        originalHtml = downloadBtn.innerHTML;
        downloadBtn.innerHTML = '<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin inline mr-1"></i><span>Generating PDF...</span>';
    }

    try {
        if (iframe.contentWindow && typeof iframe.contentWindow.generatePdf === 'function') {
            await iframe.contentWindow.generatePdf();
        } else {
            // Fallback: run html2pdf on targetElement
            const doc = iframe.contentDocument;
            const targetElement = doc.querySelector('.document-sheet') || doc.body;

            let filename = (doc.title || 'Document').trim();
            if (!filename.toLowerCase().endsWith('.pdf')) {
                filename += '.pdf';
            }

            const opt = {
                margin: 0,
                filename: filename,
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { scale: 2, useCORS: true, logging: false, scrollX: 0, scrollY: 0 },
                jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
                pagebreak: { mode: ['css', 'legacy'], before: '.page-break' }
            };

            if (window.html2pdf) {
                await html2pdf().set(opt).from(targetElement).save();
            } else {
                printFromPreview();
            }
        }
    } catch (err) {
        console.error('PDF Generation Error:', err);
        alert('Direct PDF generation encountered an issue. Opening print dialog instead.');
        printFromPreview();
    } finally {
        if (downloadBtn) {
            downloadBtn.innerHTML = originalHtml;
            if (window.lucide) lucide.createIcons();
        }
    }
}

// ---------------- DASHBOARD ----------------
async function loadDashboard() {
    try {
        const res = await fetch('/api/dashboard');
        const data = await res.json();
        state.dashboard = data;

        document.getElementById('dash-total-sales').innerText = formatCurrency(data.total_sales);
        document.getElementById('dash-invoice-count').innerText = data.invoice_count;
        document.getElementById('dash-quote-count').innerText = data.quote_count;
        document.getElementById('dash-customer-count').innerText = data.customer_count;

        const invTbody = document.getElementById('dash-recent-invoices');
        if (data.recent_invoices.length === 0) {
            invTbody.innerHTML = '<tr><td colspan="5" class="p-4 text-center text-slate-400">No invoices yet</td></tr>';
        } else {
            invTbody.innerHTML = data.recent_invoices.map(inv => `
                <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/60 transition">
                    <td class="p-3 font-semibold text-blue-600 dark:text-blue-400">${inv.invoice_no}</td>
                    <td class="p-3 text-slate-700 dark:text-slate-300">${inv.customer_name}</td>
                    <td class="p-3 text-right font-semibold">${formatCurrency(inv.grand_total)}</td>
                    <td class="p-3 text-center">
                        <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${inv.status === 'Paid' ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300' : 'bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300'}">${inv.status}</span>
                    </td>
                    <td class="p-3 text-center space-x-1">
                        <button onclick="previewInvoice(${inv.id}, '${inv.invoice_no}')" class="text-blue-600 dark:text-blue-400 hover:underline font-semibold text-xs">Preview</button>
                    </td>
                </tr>
            `).join('');
        }

        const qTbody = document.getElementById('dash-recent-quotes');
        if (data.recent_quotes.length === 0) {
            qTbody.innerHTML = '<tr><td colspan="5" class="p-4 text-center text-slate-400">No quotations yet</td></tr>';
        } else {
            qTbody.innerHTML = data.recent_quotes.map(q => `
                <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/60 transition">
                    <td class="p-3 font-semibold text-emerald-600 dark:text-emerald-400">${q.quote_no}</td>
                    <td class="p-3 text-slate-700 dark:text-slate-300">${q.customer_name}</td>
                    <td class="p-3 text-right font-semibold">${formatCurrency(q.grand_total)}</td>
                    <td class="p-3 text-center">
                        <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${q.status === 'Converted' ? 'bg-blue-100 dark:bg-blue-950 text-blue-800 dark:text-blue-300' : 'bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-300'}">${q.status}</span>
                    </td>
                    <td class="p-3 text-center space-x-1">
                        <button onclick="previewQuotation(${q.id}, '${q.quote_no}')" class="text-emerald-600 dark:text-emerald-400 hover:underline font-semibold text-xs">Preview</button>
                    </td>
                </tr>
            `).join('');
        }
    } catch (e) {
        console.error('Error loading dashboard:', e);
    }
}

// ---------------- TAX INVOICES ----------------
async function loadInvoices() {
    try {
        const res = await fetch('/api/invoices');
        state.invoices = await res.json();
        renderInvoices(state.invoices);
    } catch (e) {
        console.error('Error loading invoices:', e);
    }
}

function renderInvoices(invoices) {
    const tbody = document.getElementById('invoices-table-body');
    if (!invoices || invoices.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="p-6 text-center text-slate-400">No tax invoices recorded</td></tr>';
        return;
    }

    tbody.innerHTML = invoices.map(inv => `
        <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition">
            <td class="p-3.5 font-bold text-blue-600 dark:text-blue-400">${inv.invoice_no}</td>
            <td class="p-3.5">
                <span class="px-2 py-0.5 rounded text-[10px] font-bold ${inv.invoice_type === 'Services' ? 'bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300' : inv.invoice_type === 'Both' ? 'bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300' : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300'}">
                    ${inv.invoice_type || 'Goods'}
                </span>
            </td>
            <td class="p-3.5 text-slate-600 dark:text-slate-400">${inv.invoice_date}</td>
            <td class="p-3.5 font-medium text-slate-800 dark:text-slate-200">${inv.customer_name}</td>
            <td class="p-3.5 text-slate-600 dark:text-slate-400">${inv.customer_state}</td>
            <td class="p-3.5 text-right font-bold text-slate-900 dark:text-white">${formatCurrency(inv.grand_total)}</td>
            <td class="p-3.5 text-center">
                <button onclick="toggleInvoiceStatus(${inv.id}, '${inv.status}')" class="px-2.5 py-1 rounded-full text-[11px] font-bold transition ${inv.status === 'Paid' ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 hover:bg-emerald-200' : 'bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300 hover:bg-amber-200'}">
                    ${inv.status}
                </button>
            </td>
            <td class="p-3.5 text-center space-x-1.5">
                <button onclick="previewInvoice(${inv.id}, '${inv.invoice_no}')" class="bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 hover:bg-blue-100 px-2.5 py-1 rounded font-semibold text-xs border border-blue-200 dark:border-blue-800">
                    Preview
                </button>
                <button onclick="editInvoice(${inv.id})" class="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-200 px-2 py-1 rounded font-semibold text-xs border border-slate-300 dark:border-slate-700" title="Edit Invoice">
                    <i data-lucide="edit-3" class="w-3.5 h-3.5 inline"></i>
                </button>
                <a href="/invoice/print/${inv.id}" target="_blank" class="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-200 px-2 py-1 rounded font-semibold text-xs border border-slate-300 dark:border-slate-700" title="Print in New Tab">
                    <i data-lucide="printer" class="w-3.5 h-3.5 inline"></i>
                </a>
                <button onclick="deleteInvoice(${inv.id})" class="text-rose-500 hover:text-rose-700 p-1" title="Delete">
                    <i data-lucide="trash-2" class="w-4 h-4 inline"></i>
                </button>
            </td>
        </tr>
    `).join('');
    if (window.lucide) lucide.createIcons();
}

function filterInvoices() {
    const q = document.getElementById('search-invoices').value.toLowerCase();
    const filtered = state.invoices.filter(i => 
        i.invoice_no.toLowerCase().includes(q) || 
        i.customer_name.toLowerCase().includes(q) ||
        i.customer_state.toLowerCase().includes(q)
    );
    renderInvoices(filtered);
}

async function toggleInvoiceStatus(id, currentStatus) {
    const nextStatus = (currentStatus === 'Paid') ? 'Unpaid' : 'Paid';
    const form = new FormData();
    form.append('status', nextStatus);
    await fetch(`/api/invoices/${id}/status`, { method: 'PUT', body: form });
    loadInvoices();
}

async function deleteInvoice(id) {
    if (!confirm('Are you sure you want to delete this invoice?')) return;
    await fetch(`/api/invoices/${id}`, { method: 'DELETE' });
    loadInvoices();
}

async function openNewInvoiceModal() {
    await loadCustomers();
    await loadProducts();
    if (!state.settings) await loadSettings();

    document.getElementById('invoice-form').reset();
    document.getElementById('inv-edit-id').value = '';
    document.getElementById('modal-invoice-title').innerText = 'Create Tax Invoice';
    document.getElementById('inv-type').value = 'Goods';
    document.getElementById('inv-date').value = getTodayFormatted();
    document.getElementById('inv-due-date').value = getFutureDateFormatted(15);
    document.getElementById('inv-terms').value = state.settings?.terms_invoice || 'Thank you for your business!';
    document.getElementById('inv-cust-state').value = state.settings?.state || 'Uttar Pradesh';
    document.getElementById('inv-po-no').value = '';
    document.getElementById('inv-po-date').value = '';
    document.getElementById('inv-eway-bill').value = '';
    document.getElementById('inv-vehicle-no').value = '';
    document.getElementById('inv-transporter').value = '';

    try {
        const nextRes = await fetch('/api/invoices/next-number');
        const nextData = await nextRes.json();
        document.getElementById('inv-no-badge').innerText = `Invoice No: ${nextData.next_invoice_no} (Auto)`;
    } catch(e) {
        document.getElementById('inv-no-badge').innerText = 'Invoice No: Auto-generated';
    }

    const custSelect = document.getElementById('inv-cust-select');
    custSelect.innerHTML = '<option value="">-- Choose Existing or Enter Details --</option>' + 
        state.customers.map(c => `<option value="${c.id}">${c.name} (${c.city || c.state})</option>`).join('');

    document.getElementById('invoice-items-tbody').innerHTML = '';
    addInvoiceItemRow();
    recalcInvoiceTotals();

    openModal('modal-invoice');
    if (window.lucide) lucide.createIcons();
}

async function editInvoice(id) {
    await loadCustomers();
    await loadProducts();
    if (!state.settings) await loadSettings();

    try {
        const res = await fetch(`/api/invoices/${id}`);
        const inv = await res.json();

        document.getElementById('invoice-form').reset();
        document.getElementById('inv-edit-id').value = id;
        document.getElementById('modal-invoice-title').innerText = `Edit Tax Invoice - ${inv.invoice_no}`;
        document.getElementById('inv-no-badge').innerText = `Invoice No: ${inv.invoice_no}`;
        document.getElementById('inv-type').value = inv.invoice_type || 'Goods';
        document.getElementById('inv-date').value = inv.invoice_date;
        document.getElementById('inv-due-date').value = inv.due_date || '';
        document.getElementById('inv-cust-name').value = inv.customer_name;
        document.getElementById('inv-cust-address').value = inv.customer_address;
        document.getElementById('inv-cust-gstin').value = inv.customer_gstin || 'N/A';
        document.getElementById('inv-cust-state').value = inv.customer_state || 'Uttar Pradesh';
        document.getElementById('inv-terms').value = inv.terms || '';
        document.getElementById('inv-po-no').value = inv.po_no || '';
        document.getElementById('inv-po-date').value = inv.po_date || '';
        document.getElementById('inv-eway-bill').value = inv.e_way_bill_no || '';
        document.getElementById('inv-vehicle-no').value = inv.vehicle_no || '';
        document.getElementById('inv-transporter').value = inv.transporter_name || '';

        const custSelect = document.getElementById('inv-cust-select');
        custSelect.innerHTML = '<option value="">-- Choose Existing or Enter Details --</option>' + 
            state.customers.map(c => `<option value="${c.id}" ${c.id == inv.customer_id ? 'selected' : ''}>${c.name} (${c.city || c.state})</option>`).join('');

        const tbody = document.getElementById('invoice-items-tbody');
        tbody.innerHTML = '';
        if (inv.items && inv.items.length > 0) {
            inv.items.forEach(itm => addInvoiceItemRow(itm));
        } else {
            addInvoiceItemRow();
        }

        recalcInvoiceTotals();
        openModal('modal-invoice');
        if (window.lucide) lucide.createIcons();
    } catch (e) {
        alert('Failed to load invoice for editing: ' + e);
    }
}

function onInvoiceTypeChange() {
    const invType = document.getElementById('inv-type').value;
    const rows = document.querySelectorAll('#invoice-items-tbody tr');
    rows.forEach(row => {
        const typeSelect = row.querySelector('.item-type-select');
        if (invType === 'Services') {
            typeSelect.value = 'Service';
            onItemTypeChange(row.id);
        } else if (invType === 'Goods') {
            typeSelect.value = 'Goods';
            onItemTypeChange(row.id);
        }
    });
    recalcInvoiceTotals();
}

function onItemTypeChange(rowId) {
    const row = document.getElementById(rowId);
    const itemType = row.querySelector('.item-type-select').value;
    const hsnInput = row.querySelector('.item-hsn');
    const unitInput = row.querySelector('.item-unit');

    if (itemType === 'Service') {
        if (hsnInput.value === '9018' || hsnInput.value === '9022') hsnInput.value = '9987';
        if (unitInput.value === 'Pcs') unitInput.value = 'Job';
    } else {
        if (hsnInput.value === '9987' || hsnInput.value === '9983') hsnInput.value = '9018';
        if (unitInput.value === 'Job') unitInput.value = 'Pcs';
    }
    recalcInvoiceTotals();
}

function onInvoiceCustomerSelect() {
    const custId = document.getElementById('inv-cust-select').value;
    if (!custId) return;
    const cust = state.customers.find(c => c.id == custId);
    if (cust) {
        document.getElementById('inv-cust-name').value = cust.name;
        document.getElementById('inv-cust-address').value = cust.address;
        document.getElementById('inv-cust-gstin').value = cust.gstin || 'N/A';
        document.getElementById('inv-cust-state').value = cust.state || 'Uttar Pradesh';
        recalcInvoiceTotals();
    }
}

function addInvoiceItemRow(item = null) {
    const tbody = document.getElementById('invoice-items-tbody');
    const rowId = 'inv-row-' + Date.now() + '-' + Math.floor(Math.random()*1000);
    
    const tr = document.createElement('tr');
    tr.id = rowId;
    tr.className = 'hover:bg-slate-50 dark:hover:bg-slate-800/60';

    const prodOptions = state.products.map(p => 
        `<option value="${p.id}" ${item && item.product_id === p.id ? 'selected' : ''}>${p.name}</option>`
    ).join('');

    const itemType = item ? (item.item_type || 'Goods') : (document.getElementById('inv-type').value === 'Services' ? 'Service' : 'Goods');
    const isTaxInclusive = item ? (item.is_tax_inclusive ? true : false) : false;

    tr.innerHTML = `
        <td class="p-2 space-y-1">
            <select onchange="onInvoiceProductSelect('${rowId}')" class="item-prod-select w-full p-1.5 border dark:border-slate-700 rounded bg-white dark:bg-slate-800 dark:text-white text-xs">
                <option value="">-- Select Equipment / Service or Type --</option>
                ${prodOptions}
            </select>
            <input type="text" placeholder="Description with (SN: SerialNumber)" class="item-desc w-full p-1.5 border dark:border-slate-700 rounded dark:bg-slate-800 dark:text-white text-xs font-medium" value="${item ? item.description : ''}">
        </td>
        <td class="p-2 text-center">
            <select onchange="onItemTypeChange('${rowId}')" class="item-type-select w-full p-1.5 border dark:border-slate-700 rounded bg-white dark:bg-slate-800 dark:text-white text-xs font-semibold">
                <option value="Goods" ${itemType === 'Goods' ? 'selected' : ''}>Goods</option>
                <option value="Service" ${itemType === 'Service' ? 'selected' : ''}>Service</option>
            </select>
        </td>
        <td class="p-2">
            <input type="text" class="item-hsn w-full p-1.5 border dark:border-slate-700 rounded dark:bg-slate-800 dark:text-white text-xs text-center" value="${item ? item.hsn_code : (itemType === 'Service' ? '9987' : '9018')}">
        </td>
        <td class="p-2">
            <input type="number" step="1" min="1" oninput="recalcInvoiceTotals()" class="item-qty w-full p-1.5 border dark:border-slate-700 rounded dark:bg-slate-800 dark:text-white text-xs text-center font-semibold" value="${item ? item.qty : 1}">
        </td>
        <td class="p-2">
            <input type="text" class="item-unit w-full p-1.5 border dark:border-slate-700 rounded dark:bg-slate-800 dark:text-white text-xs text-center" value="${item ? item.unit : (itemType === 'Service' ? 'Job' : 'Pcs')}">
        </td>
        <td class="p-2">
            <input type="number" step="0.01" oninput="recalcInvoiceTotals()" class="item-rate w-full p-1.5 border dark:border-slate-700 rounded dark:bg-slate-800 dark:text-white text-xs text-right font-semibold" value="${item ? item.rate : 0}">
        </td>
        <td class="p-2 text-center">
            <select onchange="recalcInvoiceTotals()" class="item-tax-mode w-full p-1.5 border dark:border-slate-700 rounded bg-white dark:bg-slate-800 dark:text-white text-[11px] font-semibold">
                <option value="exclusive" ${!isTaxInclusive ? 'selected' : ''}>Excl. GST</option>
                <option value="inclusive" ${isTaxInclusive ? 'selected' : ''}>Incl. GST</option>
            </select>
        </td>
        <td class="p-2">
            <input type="number" step="0.1" oninput="recalcInvoiceTotals()" class="item-gst w-full p-1.5 border dark:border-slate-700 rounded dark:bg-slate-800 dark:text-white text-xs text-center font-semibold" value="${item ? item.gst_rate : 5.0}">
        </td>
        <td class="p-2 text-right">
            <div class="font-bold text-slate-800 dark:text-slate-200 item-amount">₹0.00</div>
            <div class="text-[10px] text-slate-400 item-tax-note"></div>
        </td>
        <td class="p-2 text-center">
            <button type="button" onclick="document.getElementById('${rowId}').remove(); recalcInvoiceTotals();" class="text-slate-400 hover:text-rose-600">
                <i data-lucide="trash" class="w-3.5 h-3.5 inline"></i>
            </button>
        </td>
    `;
    tbody.appendChild(tr);
    if (window.lucide) lucide.createIcons();
    recalcInvoiceTotals();
}

function onInvoiceProductSelect(rowId) {
    const row = document.getElementById(rowId);
    const prodId = row.querySelector('.item-prod-select').value;
    if (!prodId) return;
    const prod = state.products.find(p => p.id == prodId);
    if (prod) {
        row.querySelector('.item-desc').value = prod.name;
        row.querySelector('.item-hsn').value = prod.hsn_code;
        row.querySelector('.item-unit').value = prod.unit;
        row.querySelector('.item-rate').value = prod.default_rate;
        row.querySelector('.item-gst').value = prod.gst_rate;
        if (prod.is_tax_inclusive) {
            row.querySelector('.item-tax-mode').value = 'inclusive';
        }
        recalcInvoiceTotals();
    }
}

function recalcInvoiceTotals() {
    const rows = document.querySelectorAll('#invoice-items-tbody tr');
    let subtotal = 0;
    let totalTax = 0;

    const custState = (document.getElementById('inv-cust-state').value || '').trim().toLowerCase();
    const compState = (state.settings?.state || 'Uttar Pradesh').trim().toLowerCase();
    const isInterstate = custState && (custState !== compState);

    rows.forEach(row => {
        const qty = parseFloat(row.querySelector('.item-qty').value) || 0;
        const enteredRate = parseFloat(row.querySelector('.item-rate').value) || 0;
        const gstRate = parseFloat(row.querySelector('.item-gst').value) || 0;
        const taxMode = row.querySelector('.item-tax-mode').value;

        let baseAmount = 0;
        let lineTax = 0;

        if (taxMode === 'inclusive') {
            // Entered rate includes GST
            const totalWithTax = enteredRate * qty;
            baseAmount = Math.round((totalWithTax / (1 + gstRate / 100)) * 100) / 100;
            lineTax = Math.round((totalWithTax - baseAmount) * 100) / 100;
            row.querySelector('.item-tax-note').innerText = `Incl: ${formatCurrency(totalWithTax)}`;
        } else {
            // Entered rate is exclusive of GST
            baseAmount = Math.round(qty * enteredRate * 100) / 100;
            lineTax = Math.round((baseAmount * (gstRate / 100)) * 100) / 100;
            row.querySelector('.item-tax-note').innerText = `+ Tax: ${formatCurrency(lineTax)}`;
        }

        row.querySelector('.item-amount').innerText = formatCurrency(baseAmount);
        row.dataset.baseAmount = baseAmount;

        subtotal += baseAmount;
        totalTax += lineTax;
    });

    subtotal = Math.round(subtotal * 100) / 100;
    totalTax = Math.round(totalTax * 100) / 100;
    const grandTotal = Math.round((subtotal + totalTax) * 100) / 100;

    document.getElementById('inv-subtotal').innerText = formatCurrency(subtotal);
    
    if (isInterstate) {
        document.getElementById('inv-cgst-row').classList.add('hidden');
        document.getElementById('inv-sgst-row').classList.add('hidden');
        document.getElementById('inv-igst-row').classList.remove('hidden');
        document.getElementById('inv-igst').innerText = formatCurrency(totalTax);
    } else {
        document.getElementById('inv-cgst-row').classList.remove('hidden');
        document.getElementById('inv-sgst-row').classList.remove('hidden');
        document.getElementById('inv-igst-row').classList.add('hidden');
        document.getElementById('inv-cgst').innerText = formatCurrency(totalTax / 2);
        document.getElementById('inv-sgst').innerText = formatCurrency(totalTax / 2);
    }

    document.getElementById('inv-grand-total').innerText = formatCurrency(grandTotal);
}

async function saveInvoice(e) {
    e.preventDefault();
    const rows = document.querySelectorAll('#invoice-items-tbody tr');
    if (rows.length === 0) {
        alert('Please add at least one line item');
        return;
    }

    const items = [];
    rows.forEach(row => {
        const desc = row.querySelector('.item-desc').value.trim();
        if (desc) {
            const qty = parseFloat(row.querySelector('.item-qty').value) || 1;
            const enteredRate = parseFloat(row.querySelector('.item-rate').value) || 0;
            const gst_rate = parseFloat(row.querySelector('.item-gst').value) || 5;
            const taxMode = row.querySelector('.item-tax-mode').value;
            const is_tax_inclusive = (taxMode === 'inclusive');

            let baseAmount = 0;
            let effectiveRate = enteredRate;

            if (is_tax_inclusive) {
                effectiveRate = Math.round((enteredRate / (1 + gst_rate / 100)) * 100) / 100;
                baseAmount = Math.round(qty * effectiveRate * 100) / 100;
            } else {
                baseAmount = Math.round(qty * enteredRate * 100) / 100;
            }

            items.push({
                product_id: parseInt(row.querySelector('.item-prod-select').value) || null,
                description: desc,
                item_type: row.querySelector('.item-type-select').value || 'Goods',
                hsn_code: row.querySelector('.item-hsn').value || '9018',
                qty,
                unit: row.querySelector('.item-unit').value || 'Pcs',
                rate: effectiveRate,
                gst_rate,
                amount: baseAmount,
                is_tax_inclusive
            });
        }
    });

    if (items.length === 0) {
        alert('Please enter descriptions for line items');
        return;
    }

    const editId = document.getElementById('inv-edit-id').value;
    const payload = {
        invoice_date: document.getElementById('inv-date').value,
        due_date: document.getElementById('inv-due-date').value,
        invoice_type: document.getElementById('inv-type').value,
        customer_id: parseInt(document.getElementById('inv-cust-select').value) || null,
        customer_name: document.getElementById('inv-cust-name').value,
        customer_address: document.getElementById('inv-cust-address').value,
        customer_gstin: document.getElementById('inv-cust-gstin').value || 'N/A',
        customer_state: document.getElementById('inv-cust-state').value || 'Uttar Pradesh',
        terms: document.getElementById('inv-terms').value,
        status: 'Unpaid',
        po_no: document.getElementById('inv-po-no').value.trim(),
        po_date: document.getElementById('inv-po-date').value.trim(),
        e_way_bill_no: document.getElementById('inv-eway-bill').value.trim(),
        vehicle_no: document.getElementById('inv-vehicle-no').value.trim(),
        transporter_name: document.getElementById('inv-transporter').value.trim(),
        items
    };

    try {
        let res, data;
        if (editId) {
            res = await fetch(`/api/invoices/${editId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            data = await res.json();
            alert('Invoice updated successfully');
        } else {
            res = await fetch('/api/invoices', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            data = await res.json();
        }

        closeModal('modal-invoice');
        loadInvoices();
        previewInvoice(data.id, data.invoice_no);
    } catch (e) {
        alert('Error saving invoice: ' + e);
    }
}

// ---------------- QUOTATIONS ----------------
async function loadQuotations() {
    try {
        const res = await fetch('/api/quotations');
        state.quotations = await res.json();
        renderQuotations(state.quotations);
    } catch (e) {
        console.error('Error loading quotations:', e);
    }
}

function renderQuotations(quotes) {
    const tbody = document.getElementById('quotations-table-body');
    if (!quotes || quotes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="p-6 text-center text-slate-400">No quotation estimates recorded</td></tr>';
        return;
    }

    tbody.innerHTML = quotes.map(q => `
        <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition">
            <td class="p-3.5 font-bold text-emerald-600 dark:text-emerald-400">${q.quote_no}</td>
            <td class="p-3.5">
                <span class="px-2 py-0.5 rounded text-[10px] font-bold ${q.invoice_type === 'Services' ? 'bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300' : q.invoice_type === 'Both' ? 'bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300' : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300'}">
                    ${q.invoice_type || 'Goods'}
                </span>
            </td>
            <td class="p-3.5 text-slate-600 dark:text-slate-400">${q.quote_date}</td>
            <td class="p-3.5 text-slate-600 dark:text-slate-400">${q.valid_until || 'N/A'}</td>
            <td class="p-3.5 font-medium text-slate-800 dark:text-slate-200">${q.customer_name}</td>
            <td class="p-3.5 text-right font-bold text-slate-900 dark:text-white">${formatCurrency(q.grand_total)}</td>
            <td class="p-3.5 text-center">
                <span class="px-2.5 py-1 rounded-full text-[11px] font-bold ${q.status === 'Converted' ? 'bg-blue-100 dark:bg-blue-950 text-blue-800 dark:text-blue-300' : 'bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300'}">
                    ${q.status}
                </span>
            </td>
            <td class="p-3.5 text-center space-x-1.5">
                <button onclick="previewQuotation(${q.id}, '${q.quote_no}')" class="bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 px-2.5 py-1 rounded font-semibold text-xs border border-emerald-200 dark:border-emerald-800">
                    Preview
                </button>
                <button onclick="editQuotation(${q.id})" class="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-200 px-2 py-1 rounded font-semibold text-xs border border-slate-300 dark:border-slate-700" title="Edit Quotation">
                    <i data-lucide="edit-3" class="w-3.5 h-3.5 inline"></i>
                </button>
                ${q.status !== 'Converted' ? `
                    <button onclick="convertQuoteToInvoice(${q.id})" class="bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 hover:bg-blue-100 px-2 py-1 rounded font-semibold text-xs border border-blue-200 dark:border-blue-800" title="Convert to Tax Invoice">
                        Convert
                    </button>
                ` : ''}
                <a href="/quotation/print/${q.id}" target="_blank" class="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-200 px-2 py-1 rounded font-semibold text-xs border border-slate-300 dark:border-slate-700" title="Print in New Tab">
                    <i data-lucide="printer" class="w-3.5 h-3.5 inline"></i>
                </a>
                <button onclick="deleteQuotation(${q.id})" class="text-rose-500 hover:text-rose-700 p-1" title="Delete">
                    <i data-lucide="trash-2" class="w-4 h-4 inline"></i>
                </button>
            </td>
        </tr>
    `).join('');
    if (window.lucide) lucide.createIcons();
}

function filterQuotations() {
    const q = document.getElementById('search-quotations').value.toLowerCase();
    const filtered = state.quotations.filter(qt => 
        qt.quote_no.toLowerCase().includes(q) || 
        qt.customer_name.toLowerCase().includes(q)
    );
    renderQuotations(filtered);
}

async function convertQuoteToInvoice(id) {
    if (!confirm('Convert this quotation directly into a Tax Invoice?')) return;
    try {
        const res = await fetch(`/api/quotations/${id}/convert-to-invoice`, { method: 'POST' });
        const data = await res.json();
        alert(data.message);
        loadQuotations();
        previewInvoice(data.invoice_id, data.invoice_no);
    } catch (e) {
        alert('Conversion failed: ' + e);
    }
}

async function deleteQuotation(id) {
    if (!confirm('Delete this quotation?')) return;
    await fetch(`/api/quotations/${id}`, { method: 'DELETE' });
    loadQuotations();
}

async function openNewQuoteModal() {
    await loadCustomers();
    await loadProducts();
    if (!state.settings) await loadSettings();

    document.getElementById('quote-form').reset();
    document.getElementById('quote-edit-id').value = '';
    document.getElementById('modal-quotation-title').innerText = 'Create Quotation Estimate';
    document.getElementById('quote-type').value = 'Goods';
    document.getElementById('quote-date').value = getTodayFormatted();
    document.getElementById('quote-valid-until').value = getFutureDateFormatted(30);
    document.getElementById('quote-terms').value = state.settings?.terms_quotation || 
        (`1. Delivery: Standard delivery period is 2 to 4 weeks.\n2. Payment: 50% payment in advance & balance 50% against dispatch in favor of "${state.settings?.name || 'the supplier'}".`);
    document.getElementById('quote-cust-state').value = state.settings?.state || 'Uttar Pradesh';

    try {
        const nextRes = await fetch('/api/quotations/next-number');
        const nextData = await nextRes.json();
        document.getElementById('quote-no-badge').innerText = `Quote No: ${nextData.next_quote_no} (Auto)`;
    } catch(e) {
        document.getElementById('quote-no-badge').innerText = 'Quote No: Auto-generated';
    }

    const custSelect = document.getElementById('quote-cust-select');
    custSelect.innerHTML = '<option value="">-- Choose Existing or Enter Details --</option>' + 
        state.customers.map(c => `<option value="${c.id}">${c.name} (${c.city || c.state})</option>`).join('');

    document.getElementById('quote-items-tbody').innerHTML = '';
    addQuoteItemRow();
    recalcQuoteTotals();

    openModal('modal-quotation');
    if (window.lucide) lucide.createIcons();
}

async function editQuotation(id) {
    await loadCustomers();
    await loadProducts();
    if (!state.settings) await loadSettings();

    try {
        const res = await fetch(`/api/quotations/${id}`);
        const quote = await res.json();

        document.getElementById('quote-form').reset();
        document.getElementById('quote-edit-id').value = id;
        document.getElementById('modal-quotation-title').innerText = `Edit Quotation Estimate - ${quote.quote_no}`;
        document.getElementById('quote-no-badge').innerText = `Quote No: ${quote.quote_no}`;
        document.getElementById('quote-type').value = quote.invoice_type || 'Goods';
        document.getElementById('quote-date').value = quote.quote_date;
        document.getElementById('quote-valid-until').value = quote.valid_until || '';
        document.getElementById('quote-cust-name').value = quote.customer_name;
        document.getElementById('quote-cust-address').value = quote.customer_address;
        document.getElementById('quote-cust-gstin').value = quote.customer_gstin || 'N/A';
        document.getElementById('quote-cust-state').value = quote.customer_state || 'Uttar Pradesh';
        document.getElementById('quote-terms').value = quote.terms || '';

        const custSelect = document.getElementById('quote-cust-select');
        custSelect.innerHTML = '<option value="">-- Choose Existing or Enter Details --</option>' + 
            state.customers.map(c => `<option value="${c.id}" ${c.id == quote.customer_id ? 'selected' : ''}>${c.name} (${c.city || c.state})</option>`).join('');

        const tbody = document.getElementById('quote-items-tbody');
        tbody.innerHTML = '';
        if (quote.items && quote.items.length > 0) {
            quote.items.forEach(itm => addQuoteItemRow(itm));
        } else {
            addQuoteItemRow();
        }

        recalcQuoteTotals();
        openModal('modal-quotation');
        if (window.lucide) lucide.createIcons();
    } catch (e) {
        alert('Failed to load quotation for editing: ' + e);
    }
}

function onQuoteTypeChange() {
    const qType = document.getElementById('quote-type').value;
    const rows = document.querySelectorAll('#quote-items-tbody tr');
    rows.forEach(row => {
        const typeSelect = row.querySelector('.quote-type-select');
        if (qType === 'Services') {
            typeSelect.value = 'Service';
            onQuoteItemTypeChange(row.id);
        } else if (qType === 'Goods') {
            typeSelect.value = 'Goods';
            onQuoteItemTypeChange(row.id);
        }
    });
    recalcQuoteTotals();
}

function onQuoteItemTypeChange(rowId) {
    const row = document.getElementById(rowId);
    const itemType = row.querySelector('.quote-type-select').value;
    const hsnInput = row.querySelector('.quote-hsn');
    const unitInput = row.querySelector('.quote-unit');

    if (itemType === 'Service') {
        if (hsnInput.value === '9018' || hsnInput.value === '9022') hsnInput.value = '9987';
        if (unitInput.value === 'Pcs') unitInput.value = 'Job';
    } else {
        if (hsnInput.value === '9987' || hsnInput.value === '9983') hsnInput.value = '9022';
        if (unitInput.value === 'Job') unitInput.value = 'Pcs';
    }
    recalcQuoteTotals();
}

function onQuoteCustomerSelect() {
    const custId = document.getElementById('quote-cust-select').value;
    if (!custId) return;
    const cust = state.customers.find(c => c.id == custId);
    if (cust) {
        document.getElementById('quote-cust-name').value = cust.name;
        document.getElementById('quote-cust-address').value = cust.address;
        document.getElementById('quote-cust-gstin').value = cust.gstin || 'N/A';
        document.getElementById('quote-cust-state').value = cust.state || 'Uttar Pradesh';
        recalcQuoteTotals();
    }
}

function addQuoteItemRow(item = null) {
    const tbody = document.getElementById('quote-items-tbody');
    const rowId = 'quote-row-' + Date.now() + '-' + Math.floor(Math.random()*1000);
    
    const tr = document.createElement('tr');
    tr.id = rowId;
    tr.className = 'hover:bg-slate-50 dark:hover:bg-slate-800/60';

    const prodOptions = state.products.map(p => 
        `<option value="${p.id}" ${item && item.product_id === p.id ? 'selected' : ''}>${p.name}</option>`
    ).join('');

    const itemType = item ? (item.item_type || 'Goods') : (document.getElementById('quote-type').value === 'Services' ? 'Service' : 'Goods');
    const isTaxInclusive = item ? (item.is_tax_inclusive ? true : false) : false;

    tr.innerHTML = `
        <td class="p-2 space-y-1">
            <select onchange="onQuoteProductSelect('${rowId}')" class="quote-prod-select w-full p-1.5 border dark:border-slate-700 rounded bg-white dark:bg-slate-800 dark:text-white text-xs">
                <option value="">-- Select Medical Equipment / Service --</option>
                ${prodOptions}
            </select>
            <input type="text" placeholder="Equipment Title & Description" class="quote-desc w-full p-1.5 border dark:border-slate-700 rounded dark:bg-slate-800 dark:text-white text-xs font-medium" value="${item ? item.description : ''}">
            <input type="hidden" class="quote-img-url" value="${item ? (item.product_image_url || '') : ''}">
        </td>
        <td class="p-2 text-center">
            <select onchange="onQuoteItemTypeChange('${rowId}')" class="quote-type-select w-full p-1.5 border dark:border-slate-700 rounded bg-white dark:bg-slate-800 dark:text-white text-xs font-semibold">
                <option value="Goods" ${itemType === 'Goods' ? 'selected' : ''}>Goods</option>
                <option value="Service" ${itemType === 'Service' ? 'selected' : ''}>Service</option>
            </select>
        </td>
        <td class="p-2">
            <input type="text" class="quote-hsn w-full p-1.5 border dark:border-slate-700 rounded dark:bg-slate-800 dark:text-white text-xs text-center" value="${item ? item.hsn_code : (itemType === 'Service' ? '9987' : '9022')}">
        </td>
        <td class="p-2">
            <input type="number" step="1" min="1" oninput="recalcQuoteTotals()" class="quote-qty w-full p-1.5 border dark:border-slate-700 rounded dark:bg-slate-800 dark:text-white text-xs text-center font-semibold" value="${item ? item.qty : 1}">
        </td>
        <td class="p-2">
            <input type="text" class="quote-unit w-full p-1.5 border dark:border-slate-700 rounded dark:bg-slate-800 dark:text-white text-xs text-center" value="${item ? item.unit : (itemType === 'Service' ? 'Job' : 'Pcs')}">
        </td>
        <td class="p-2">
            <input type="number" step="0.01" oninput="recalcQuoteTotals()" class="quote-rate w-full p-1.5 border dark:border-slate-700 rounded dark:bg-slate-800 dark:text-white text-xs text-right font-semibold" value="${item ? item.rate : 0}">
        </td>
        <td class="p-2 text-center">
            <select onchange="recalcQuoteTotals()" class="quote-tax-mode w-full p-1.5 border dark:border-slate-700 rounded bg-white dark:bg-slate-800 dark:text-white text-[11px] font-semibold">
                <option value="exclusive" ${!isTaxInclusive ? 'selected' : ''}>Excl. GST</option>
                <option value="inclusive" ${isTaxInclusive ? 'selected' : ''}>Incl. GST</option>
            </select>
        </td>
        <td class="p-2">
            <input type="number" step="0.1" oninput="recalcQuoteTotals()" class="quote-gst w-full p-1.5 border dark:border-slate-700 rounded dark:bg-slate-800 dark:text-white text-xs text-center font-semibold" value="${item ? item.gst_rate : 5.0}">
        </td>
        <td class="p-2 text-right">
            <div class="font-bold text-slate-800 dark:text-slate-200 quote-amount">₹0.00</div>
            <div class="text-[10px] text-slate-400 quote-tax-note"></div>
        </td>
        <td class="p-2 text-center">
            <button type="button" onclick="document.getElementById('${rowId}').remove(); recalcQuoteTotals();" class="text-slate-400 hover:text-rose-600">
                <i data-lucide="trash" class="w-3.5 h-3.5 inline"></i>
            </button>
        </td>
    `;
    tbody.appendChild(tr);
    if (window.lucide) lucide.createIcons();
    recalcQuoteTotals();
}

function onQuoteProductSelect(rowId) {
    const row = document.getElementById(rowId);
    const prodId = row.querySelector('.quote-prod-select').value;
    if (!prodId) return;
    const prod = state.products.find(p => p.id == prodId);
    if (prod) {
        row.querySelector('.quote-desc').value = prod.name;
        row.querySelector('.quote-hsn').value = prod.hsn_code;
        row.querySelector('.quote-unit').value = prod.unit;
        row.querySelector('.quote-rate').value = prod.default_rate;
        row.querySelector('.quote-gst').value = prod.gst_rate;
        row.querySelector('.quote-img-url').value = prod.image_url || '';
        if (prod.is_tax_inclusive) {
            row.querySelector('.quote-tax-mode').value = 'inclusive';
        }
        recalcQuoteTotals();
    }
}

function recalcQuoteTotals() {
    const rows = document.querySelectorAll('#quote-items-tbody tr');
    let subtotal = 0;
    let totalTax = 0;

    const custState = (document.getElementById('quote-cust-state').value || '').trim().toLowerCase();
    const compState = (state.settings?.state || 'Uttar Pradesh').trim().toLowerCase();
    const isInterstate = custState && (custState !== compState);

    rows.forEach(row => {
        const qty = parseFloat(row.querySelector('.quote-qty').value) || 0;
        const enteredRate = parseFloat(row.querySelector('.quote-rate').value) || 0;
        const gstRate = parseFloat(row.querySelector('.quote-gst').value) || 0;
        const taxMode = row.querySelector('.quote-tax-mode').value;

        let baseAmount = 0;
        let lineTax = 0;

        if (taxMode === 'inclusive') {
            const totalWithTax = enteredRate * qty;
            baseAmount = Math.round((totalWithTax / (1 + gstRate / 100)) * 100) / 100;
            lineTax = Math.round((totalWithTax - baseAmount) * 100) / 100;
            row.querySelector('.quote-tax-note').innerText = `Incl: ${formatCurrency(totalWithTax)}`;
        } else {
            baseAmount = Math.round(qty * enteredRate * 100) / 100;
            lineTax = Math.round((baseAmount * (gstRate / 100)) * 100) / 100;
            row.querySelector('.quote-tax-note').innerText = `+ Tax: ${formatCurrency(lineTax)}`;
        }

        row.querySelector('.quote-amount').innerText = formatCurrency(baseAmount);
        subtotal += baseAmount;
        totalTax += lineTax;
    });

    subtotal = Math.round(subtotal * 100) / 100;
    totalTax = Math.round(totalTax * 100) / 100;
    const grandTotal = Math.round((subtotal + totalTax) * 100) / 100;

    document.getElementById('quote-subtotal').innerText = formatCurrency(subtotal);
    
    if (isInterstate) {
        document.getElementById('quote-cgst-row').classList.add('hidden');
        document.getElementById('quote-sgst-row').classList.add('hidden');
        document.getElementById('quote-igst-row').classList.remove('hidden');
        document.getElementById('quote-igst').innerText = formatCurrency(totalTax);
    } else {
        document.getElementById('quote-cgst-row').classList.remove('hidden');
        document.getElementById('quote-sgst-row').classList.remove('hidden');
        document.getElementById('quote-igst-row').classList.add('hidden');
        document.getElementById('quote-cgst').innerText = formatCurrency(totalTax / 2);
        document.getElementById('quote-sgst').innerText = formatCurrency(totalTax / 2);
    }

    document.getElementById('quote-grand-total').innerText = formatCurrency(grandTotal);
}

async function saveQuotation(e) {
    e.preventDefault();
    const rows = document.querySelectorAll('#quote-items-tbody tr');
    if (rows.length === 0) {
        alert('Please add at least one medical equipment or service item');
        return;
    }

    const items = [];
    rows.forEach(row => {
        const desc = row.querySelector('.quote-desc').value.trim();
        if (desc) {
            const qty = parseFloat(row.querySelector('.quote-qty').value) || 1;
            const enteredRate = parseFloat(row.querySelector('.quote-rate').value) || 0;
            const gst_rate = parseFloat(row.querySelector('.quote-gst').value) || 5;
            const taxMode = row.querySelector('.quote-tax-mode').value;
            const is_tax_inclusive = (taxMode === 'inclusive');

            let baseAmount = 0;
            let effectiveRate = enteredRate;

            if (is_tax_inclusive) {
                effectiveRate = Math.round((enteredRate / (1 + gst_rate / 100)) * 100) / 100;
                baseAmount = Math.round(qty * effectiveRate * 100) / 100;
            } else {
                baseAmount = Math.round(qty * enteredRate * 100) / 100;
            }

            items.push({
                product_id: parseInt(row.querySelector('.quote-prod-select').value) || null,
                description: desc,
                item_type: row.querySelector('.quote-type-select').value || 'Goods',
                hsn_code: row.querySelector('.quote-hsn').value || '9022',
                qty,
                unit: row.querySelector('.quote-unit').value || 'Pcs',
                rate: effectiveRate,
                gst_rate,
                amount: baseAmount,
                product_image_url: row.querySelector('.quote-img-url').value || '',
                is_tax_inclusive
            });
        }
    });

    if (items.length === 0) {
        alert('Please enter descriptions for line items');
        return;
    }

    const editId = document.getElementById('quote-edit-id').value;
    const payload = {
        quote_date: document.getElementById('quote-date').value,
        valid_until: document.getElementById('quote-valid-until').value,
        invoice_type: document.getElementById('quote-type').value,
        customer_id: parseInt(document.getElementById('quote-cust-select').value) || null,
        customer_name: document.getElementById('quote-cust-name').value,
        customer_address: document.getElementById('quote-cust-address').value,
        customer_gstin: document.getElementById('quote-cust-gstin').value || 'N/A',
        customer_state: document.getElementById('quote-cust-state').value || 'Uttar Pradesh',
        terms: document.getElementById('quote-terms').value,
        status: 'Active',
        items
    };

    try {
        let res, data;
        if (editId) {
            res = await fetch(`/api/quotations/${editId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            data = await res.json();
            alert('Quotation updated successfully');
        } else {
            res = await fetch('/api/quotations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            data = await res.json();
        }

        closeModal('modal-quotation');
        loadQuotations();
        previewQuotation(data.id, data.quote_no);
    } catch (e) {
        alert('Error saving quotation: ' + e);
    }
}

// ---------------- DELIVERY CHALLANS ----------------
async function loadChallans() {
    try {
        const res = await fetch('/api/challans');
        state.challans = await res.json();
        renderChallans(state.challans);
    } catch (e) {
        console.error('Error loading challans:', e);
    }
}

function renderChallans(challans) {
    const tbody = document.getElementById('challans-table-body');
    if (!challans || challans.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="p-6 text-center text-slate-400">No delivery challans recorded</td></tr>';
        return;
    }

    tbody.innerHTML = challans.map(c => `
        <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition">
            <td class="p-3.5 font-bold text-amber-600 dark:text-amber-400">${c.challan_no}</td>
            <td class="p-3.5 text-slate-600 dark:text-slate-400">${c.challan_date}</td>
            <td class="p-3.5 font-medium text-slate-800 dark:text-slate-200">${c.customer_name}</td>
            <td class="p-3.5 text-slate-600 dark:text-slate-400 max-w-xs truncate" title="${c.reason_for_transport}">${c.reason_for_transport}</td>
            <td class="p-3.5 text-slate-600 dark:text-slate-400">
                <div>${c.vehicle_no || 'N/A'}</div>
                <div class="text-[10px] text-slate-400">${c.transporter_name || 'Direct'}</div>
            </td>
            <td class="p-3.5 text-right font-bold text-slate-900 dark:text-white">${formatCurrency(c.approx_total)}</td>
            <td class="p-3.5 text-center">
                <span class="px-2.5 py-1 rounded-full text-[11px] font-bold ${
                    c.status === 'Invoiced' ? 'bg-blue-100 dark:bg-blue-950 text-blue-800 dark:text-blue-300' :
                    c.status === 'Delivered' ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300' :
                    'bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300'
                }">
                    ${c.status}
                </span>
            </td>
            <td class="p-3.5 text-center space-x-1.5">
                <button onclick="previewChallan(${c.id}, '${c.challan_no}')" class="bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-300 hover:bg-amber-100 px-2.5 py-1 rounded font-semibold text-xs border border-amber-200 dark:border-amber-800">
                    Preview
                </button>
                ${c.status !== 'Invoiced' ? `
                    <button onclick="convertChallanToInvoice(${c.id})" class="bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 px-2.5 py-1 rounded font-semibold text-xs border border-emerald-200 dark:border-emerald-800" title="Convert to Tax Invoice">
                        Convert
                    </button>
                ` : ''}
                <button onclick="editChallan(${c.id})" class="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-200 px-2 py-1 rounded font-semibold text-xs border border-slate-300 dark:border-slate-700" title="Edit Challan">
                    <i data-lucide="edit-3" class="w-3.5 h-3.5 inline"></i>
                </button>
                <a href="/challan/print/${c.id}" target="_blank" class="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-200 px-2 py-1 rounded font-semibold text-xs border border-slate-300 dark:border-slate-700" title="Print in New Tab">
                    <i data-lucide="printer" class="w-3.5 h-3.5 inline"></i>
                </a>
                <button onclick="deleteChallan(${c.id})" class="text-rose-500 hover:text-rose-700 p-1" title="Delete">
                    <i data-lucide="trash-2" class="w-4 h-4 inline"></i>
                </button>
            </td>
        </tr>
    `).join('');
    if (window.lucide) lucide.createIcons();
}

function filterChallans() {
    const q = document.getElementById('search-challans').value.toLowerCase();
    const filtered = state.challans.filter(c => 
        c.challan_no.toLowerCase().includes(q) || 
        c.customer_name.toLowerCase().includes(q) ||
        (c.reason_for_transport && c.reason_for_transport.toLowerCase().includes(q))
    );
    renderChallans(filtered);
}

async function openNewChallanModal() {
    await loadCustomers();
    await loadProducts();
    if (!state.settings) await loadSettings();

    document.getElementById('challan-form').reset();
    document.getElementById('challan-edit-id').value = '';
    document.getElementById('modal-challan-title').innerText = 'Create Delivery Challan';
    document.getElementById('challan-date').value = getTodayFormatted();
    document.getElementById('challan-reason').value = 'Supply for Installation & Commissioning';
    document.getElementById('challan-terms').value = state.settings?.terms_challan || 
        (`1. The goods transported under this challan are for delivery/installation/demonstration purpose and not by way of sale.\n2. Ownership remains with "${state.settings?.name || 'the supplier'}" until the tax invoice is cleared.`);
    document.getElementById('challan-cust-state').value = state.settings?.state || 'Uttar Pradesh';

    try {
        const nextRes = await fetch('/api/challans/next-number');
        const nextData = await nextRes.json();
        document.getElementById('challan-no-badge').innerText = `Challan No: ${nextData.next_challan_no} (Auto)`;
    } catch(e) {
        document.getElementById('challan-no-badge').innerText = 'Challan No: Auto-generated';
    }

    const custSelect = document.getElementById('challan-cust-select');
    custSelect.innerHTML = '<option value="">-- Choose Existing or Enter Details --</option>' + 
        state.customers.map(c => `<option value="${c.id}">${c.name} (${c.city || c.state})</option>`).join('');

    document.getElementById('challan-items-tbody').innerHTML = '';
    addChallanItemRow();
    recalcChallanTotals();

    openModal('modal-challan');
    if (window.lucide) lucide.createIcons();
}

async function editChallan(id) {
    await loadCustomers();
    await loadProducts();
    if (!state.settings) await loadSettings();

    try {
        const res = await fetch(`/api/challans/${id}`);
        const c = await res.json();

        document.getElementById('challan-form').reset();
        document.getElementById('challan-edit-id').value = id;
        document.getElementById('modal-challan-title').innerText = `Edit Delivery Challan - ${c.challan_no}`;
        document.getElementById('challan-no-badge').innerText = `Challan No: ${c.challan_no}`;
        document.getElementById('challan-date').value = c.challan_date;
        document.getElementById('challan-reason').value = c.reason_for_transport || 'Supply for Installation & Commissioning';
        document.getElementById('challan-status').value = c.status || 'Dispatched';
        document.getElementById('challan-cust-name').value = c.customer_name;
        document.getElementById('challan-cust-address').value = c.customer_address;
        document.getElementById('challan-cust-gstin').value = c.customer_gstin || 'N/A';
        document.getElementById('challan-cust-state').value = c.customer_state || 'Uttar Pradesh';
        document.getElementById('challan-transporter').value = c.transporter_name || '';
        document.getElementById('challan-vehicle-no').value = c.vehicle_no || '';
        document.getElementById('challan-eway-bill').value = c.e_way_bill_no || '';
        document.getElementById('challan-terms').value = c.terms || '';

        const custSelect = document.getElementById('challan-cust-select');
        custSelect.innerHTML = '<option value="">-- Choose Existing or Enter Details --</option>' + 
            state.customers.map(cust => `<option value="${cust.id}" ${cust.id == c.customer_id ? 'selected' : ''}>${cust.name} (${cust.city || cust.state})</option>`).join('');

        const tbody = document.getElementById('challan-items-tbody');
        tbody.innerHTML = '';
        if (c.items && c.items.length > 0) {
            c.items.forEach(itm => addChallanItemRow(itm));
        } else {
            addChallanItemRow();
        }

        recalcChallanTotals();
        openModal('modal-challan');
        if (window.lucide) lucide.createIcons();
    } catch (e) {
        alert('Failed to load delivery challan for editing: ' + e);
    }
}

function onChallanCustomerSelect() {
    const custId = document.getElementById('challan-cust-select').value;
    if (!custId) return;
    const cust = state.customers.find(c => c.id == custId);
    if (cust) {
        document.getElementById('challan-cust-name').value = cust.name;
        document.getElementById('challan-cust-address').value = cust.address;
        document.getElementById('challan-cust-gstin').value = cust.gstin || 'N/A';
        document.getElementById('challan-cust-state').value = cust.state || 'Uttar Pradesh';
    }
}

function addChallanItemRow(item = null) {
    const tbody = document.getElementById('challan-items-tbody');
    const rowId = 'dc-row-' + Date.now() + '-' + Math.floor(Math.random()*1000);

    const tr = document.createElement('tr');
    tr.id = rowId;
    tr.className = 'hover:bg-slate-50 dark:hover:bg-slate-800/60';

    const prodOptions = state.products.map(p => 
        `<option value="${p.id}" ${item && item.product_id === p.id ? 'selected' : ''}>${p.name}</option>`
    ).join('');

    tr.innerHTML = `
        <td class="p-2 space-y-1">
            <select onchange="onChallanProductSelect('${rowId}')" class="challan-prod-select w-full p-1.5 border dark:border-slate-700 rounded bg-white dark:bg-slate-800 dark:text-white text-xs">
                <option value="">-- Select Equipment or Type Details --</option>
                ${prodOptions}
            </select>
            <input type="text" placeholder="Description with (SN: Serial Number)" class="challan-desc w-full p-1.5 border dark:border-slate-700 rounded dark:bg-slate-800 dark:text-white text-xs font-medium" value="${item ? item.description : ''}">
        </td>
        <td class="p-2">
            <input type="text" class="challan-hsn w-full p-1.5 border dark:border-slate-700 rounded dark:bg-slate-800 dark:text-white text-xs text-center" value="${item ? item.hsn_code : '9018'}">
        </td>
        <td class="p-2">
            <input type="number" step="1" min="1" oninput="recalcChallanTotals()" class="challan-qty w-full p-1.5 border dark:border-slate-700 rounded dark:bg-slate-800 dark:text-white text-xs text-center font-semibold" value="${item ? item.qty : 1}">
        </td>
        <td class="p-2">
            <input type="text" class="challan-unit w-full p-1.5 border dark:border-slate-700 rounded dark:bg-slate-800 dark:text-white text-xs text-center" value="${item ? item.unit : 'Pcs'}">
        </td>
        <td class="p-2">
            <input type="number" step="0.01" oninput="recalcChallanTotals()" class="challan-rate w-full p-1.5 border dark:border-slate-700 rounded dark:bg-slate-800 dark:text-white text-xs text-right font-semibold" value="${item ? item.approx_rate : 0}">
        </td>
        <td class="p-2 text-right">
            <div class="font-bold text-slate-800 dark:text-slate-200 challan-amount">₹0.00</div>
        </td>
        <td class="p-2 text-center">
            <button type="button" onclick="document.getElementById('${rowId}').remove(); recalcChallanTotals();" class="text-slate-400 hover:text-rose-600">
                <i data-lucide="trash" class="w-3.5 h-3.5 inline"></i>
            </button>
        </td>
    `;
    tbody.appendChild(tr);
    if (window.lucide) lucide.createIcons();
    recalcChallanTotals();
}

function onChallanProductSelect(rowId) {
    const row = document.getElementById(rowId);
    const prodId = row.querySelector('.challan-prod-select').value;
    if (!prodId) return;
    const prod = state.products.find(p => p.id == prodId);
    if (prod) {
        row.querySelector('.challan-desc').value = prod.name;
        row.querySelector('.challan-hsn').value = prod.hsn_code;
        row.querySelector('.challan-unit').value = prod.unit;
        row.querySelector('.challan-rate').value = prod.default_rate;
        recalcChallanTotals();
    }
}

function recalcChallanTotals() {
    const rows = document.querySelectorAll('#challan-items-tbody tr');
    let approxTotal = 0;

    rows.forEach(row => {
        const qty = parseFloat(row.querySelector('.challan-qty').value) || 0;
        const rate = parseFloat(row.querySelector('.challan-rate').value) || 0;
        const lineTotal = Math.round(qty * rate * 100) / 100;
        row.querySelector('.challan-amount').innerText = formatCurrency(lineTotal);
        approxTotal += lineTotal;
    });

    approxTotal = Math.round(approxTotal * 100) / 100;
    document.getElementById('challan-grand-total').innerText = formatCurrency(approxTotal);
}

async function saveChallan(e) {
    e.preventDefault();
    const rows = document.querySelectorAll('#challan-items-tbody tr');
    if (rows.length === 0) {
        alert('Please add at least one line item to the delivery challan');
        return;
    }

    const items = [];
    rows.forEach(row => {
        const desc = row.querySelector('.challan-desc').value.trim();
        if (desc) {
            const qty = parseFloat(row.querySelector('.challan-qty').value) || 1;
            const rate = parseFloat(row.querySelector('.challan-rate').value) || 0;
            const amount = Math.round(qty * rate * 100) / 100;

            items.push({
                product_id: parseInt(row.querySelector('.challan-prod-select').value) || null,
                description: desc,
                hsn_code: row.querySelector('.challan-hsn').value || '9018',
                qty,
                unit: row.querySelector('.challan-unit').value || 'Pcs',
                approx_rate: rate,
                approx_amount: amount
            });
        }
    });

    if (items.length === 0) {
        alert('Please enter descriptions for line items');
        return;
    }

    const editId = document.getElementById('challan-edit-id').value;
    const payload = {
        challan_date: document.getElementById('challan-date').value,
        reason_for_transport: document.getElementById('challan-reason').value,
        customer_id: parseInt(document.getElementById('challan-cust-select').value) || null,
        customer_name: document.getElementById('challan-cust-name').value,
        customer_address: document.getElementById('challan-cust-address').value,
        customer_gstin: document.getElementById('challan-cust-gstin').value || 'N/A',
        customer_state: document.getElementById('challan-cust-state').value || 'Uttar Pradesh',
        transporter_name: document.getElementById('challan-transporter').value.trim(),
        vehicle_no: document.getElementById('challan-vehicle-no').value.trim(),
        e_way_bill_no: document.getElementById('challan-eway-bill').value.trim(),
        terms: document.getElementById('challan-terms').value,
        status: document.getElementById('challan-status').value,
        items
    };

    try {
        let res, data;
        if (editId) {
            res = await fetch(`/api/challans/${editId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            data = await res.json();
            alert('Delivery Challan updated successfully');
        } else {
            res = await fetch('/api/challans', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            data = await res.json();
        }

        closeModal('modal-challan');
        loadChallans();
        previewChallan(data.id, data.challan_no);
    } catch (e) {
        alert('Error saving delivery challan: ' + e);
    }
}

async function convertChallanToInvoice(id) {
    if (!confirm('Convert this Delivery Challan into a Tax Invoice?')) return;
    try {
        const res = await fetch(`/api/challans/${id}/convert-to-invoice`, { method: 'POST' });
        const data = await res.json();
        alert(data.message || 'Challan converted to Tax Invoice successfully');
        loadChallans();
        switchTab('invoices');
        previewInvoice(data.invoice_id, data.invoice_no);
    } catch (e) {
        alert('Failed to convert challan: ' + e);
    }
}

async function deleteChallan(id) {
    if (!confirm('Are you sure you want to delete this delivery challan?')) return;
    await fetch(`/api/challans/${id}`, { method: 'DELETE' });
    loadChallans();
}

// ---------------- GST & REPORTS ----------------
async function loadGstReports() {
    const fy = document.getElementById('report-fy')?.value || '26-27';
    const fromDate = document.getElementById('report-from-date')?.value || '';
    const toDate = document.getElementById('report-to-date')?.value || '';

    const params = new URLSearchParams();
    if (fy) params.append('financial_year', fy);
    if (fromDate) params.append('from_date', fromDate);
    if (toDate) params.append('to_date', toDate);

    try {
        const res = await fetch(`/api/reports/gst-summary?${params.toString()}`);
        const data = await res.json();
        state.gstSummary = data;
        renderGstReports(data);
    } catch (e) {
        console.error('Error loading GST reports:', e);
    }
}

function renderGstReports(data) {
    if (!data) return;

    document.getElementById('rep-taxable').innerText = formatCurrency(data.total_taxable);
    document.getElementById('rep-cgst').innerText = formatCurrency(data.total_cgst);
    document.getElementById('rep-sgst').innerText = formatCurrency(data.total_sgst);
    document.getElementById('rep-igst').innerText = formatCurrency(data.total_igst);
    document.getElementById('rep-total-tax').innerText = formatCurrency(data.total_tax);

    // Table 4: B2B
    document.getElementById('rep-b2b-count').innerText = `${data.b2b_count} Invoices`;
    const b2bTbody = document.getElementById('rep-b2b-tbody');
    if (!data.b2b_invoices || data.b2b_invoices.length === 0) {
        b2bTbody.innerHTML = '<tr><td colspan="7" class="p-4 text-center text-slate-400">No B2B invoices in this period</td></tr>';
    } else {
        b2bTbody.innerHTML = data.b2b_invoices.map(inv => `
            <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/60 transition">
                <td class="p-3 font-semibold text-blue-600 dark:text-blue-400">${inv.customer_gstin}</td>
                <td class="p-3 font-medium text-slate-800 dark:text-slate-200">${inv.customer_name}</td>
                <td class="p-3">${inv.invoice_no}</td>
                <td class="p-3 text-slate-600 dark:text-slate-400">${inv.invoice_date}</td>
                <td class="p-3">${inv.customer_state}</td>
                <td class="p-3 text-right font-semibold">${formatCurrency(inv.subtotal)}</td>
                <td class="p-3 text-right font-bold">${formatCurrency(inv.grand_total)}</td>
            </tr>
        `).join('');
    }

    // Table 7: B2CS
    document.getElementById('rep-b2cs-count').innerText = `${data.b2cs_count} Invoices`;
    const b2csTbody = document.getElementById('rep-b2cs-tbody');
    if (!data.b2cs_invoices || data.b2cs_invoices.length === 0) {
        b2csTbody.innerHTML = '<tr><td colspan="8" class="p-4 text-center text-slate-400">No B2CS supplies in this period</td></tr>';
    } else {
        b2csTbody.innerHTML = data.b2cs_invoices.map(inv => `
            <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/60 transition">
                <td class="p-3 font-semibold text-indigo-600 dark:text-indigo-400">${inv.invoice_no}</td>
                <td class="p-3 font-medium text-slate-800 dark:text-slate-200">${inv.customer_name}</td>
                <td class="p-3 text-slate-600 dark:text-slate-400">${inv.invoice_date}</td>
                <td class="p-3">${inv.customer_state}</td>
                <td class="p-3 text-right font-semibold">${formatCurrency(inv.subtotal)}</td>
                <td class="p-3 text-right text-slate-600 dark:text-slate-400">${formatCurrency(inv.cgst_amount)}</td>
                <td class="p-3 text-right text-slate-600 dark:text-slate-400">${formatCurrency(inv.sgst_amount)}</td>
                <td class="p-3 text-right font-bold">${formatCurrency(inv.grand_total)}</td>
            </tr>
        `).join('');
    }

    // Table 12: HSN Summary
    const hsnTbody = document.getElementById('rep-hsn-tbody');
    if (!data.hsn_summary || data.hsn_summary.length === 0) {
        hsnTbody.innerHTML = '<tr><td colspan="9" class="p-4 text-center text-slate-400">No HSN data in this period</td></tr>';
    } else {
        hsnTbody.innerHTML = data.hsn_summary.map(h => `
            <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/60 transition">
                <td class="p-3 font-bold text-emerald-600 dark:text-emerald-400">${h.hsn_code}</td>
                <td class="p-3 font-medium text-slate-800 dark:text-slate-200">${h.description}</td>
                <td class="p-3 text-center">${h.unit}</td>
                <td class="p-3 text-center font-semibold">${h.total_qty}</td>
                <td class="p-3 text-right font-semibold">${formatCurrency(h.taxable_value)}</td>
                <td class="p-3 text-right text-slate-600 dark:text-slate-400">${formatCurrency(h.igst_amount)}</td>
                <td class="p-3 text-right text-slate-600 dark:text-slate-400">${formatCurrency(h.cgst_amount)}</td>
                <td class="p-3 text-right text-slate-600 dark:text-slate-400">${formatCurrency(h.sgst_amount)}</td>
                <td class="p-3 text-right font-bold">${formatCurrency(h.total_value)}</td>
            </tr>
        `).join('');
    }
}

function exportGstr1Csv() {
    const fy = document.getElementById('report-fy')?.value || '';
    const fromDate = document.getElementById('report-from-date')?.value || '';
    const toDate = document.getElementById('report-to-date')?.value || '';

    const params = new URLSearchParams();
    if (fy) params.append('financial_year', fy);
    if (fromDate) params.append('from_date', fromDate);
    if (toDate) params.append('to_date', toDate);

    window.location.href = `/api/reports/gstr1-csv?${params.toString()}`;
}

function exportSalesRegisterCsv() {
    const fy = document.getElementById('report-fy')?.value || '';
    const fromDate = document.getElementById('report-from-date')?.value || '';
    const toDate = document.getElementById('report-to-date')?.value || '';

    const params = new URLSearchParams();
    if (fy) params.append('financial_year', fy);
    if (fromDate) params.append('from_date', fromDate);
    if (toDate) params.append('to_date', toDate);

    window.location.href = `/api/reports/sales-register-csv?${params.toString()}`;
}

// ---------------- CUSTOMERS ----------------
async function loadCustomers() {
    try {
        const res = await fetch('/api/customers');
        state.customers = await res.json();
        renderCustomers(state.customers);
    } catch (e) {
        console.error('Error loading customers:', e);
    }
}

function renderCustomers(customers) {
    const grid = document.getElementById('customers-cards-grid');
    if (!customers || customers.length === 0) {
        grid.innerHTML = '<div class="col-span-3 p-8 text-center text-slate-400 bg-white dark:bg-slate-900 rounded-xl border border-dashed dark:border-slate-800">No customers recorded yet</div>';
        return;
    }

    grid.innerHTML = customers.map(c => `
        <div class="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between hover:border-blue-300 dark:hover:border-blue-700 transition">
            <div>
                <div class="flex items-start justify-between">
                    <h4 class="font-bold text-slate-900 dark:text-white text-sm">${c.name}</h4>
                    <span class="text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-semibold px-2 py-0.5 rounded">${c.state_code || '09'}</span>
                </div>
                <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">${c.contact_person ? 'Contact: ' + c.contact_person : ''}</p>
                <p class="text-xs text-slate-700 dark:text-slate-300 mt-2 line-clamp-2">${c.address}</p>
                <div class="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800 text-xs text-slate-500 dark:text-slate-400 flex justify-between">
                    <span>GSTIN: <strong class="text-slate-700 dark:text-slate-300">${c.gstin}</strong></span>
                    <span>${c.city ? c.city + ', ' : ''}${c.state}</span>
                </div>
            </div>
            <div class="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex justify-end space-x-2">
                <button onclick="deleteCustomer(${c.id})" class="text-xs text-rose-600 hover:text-rose-800 font-semibold">Delete</button>
            </div>
        </div>
    `).join('');
}

function filterCustomers() {
    const q = document.getElementById('search-customers').value.toLowerCase();
    const filtered = state.customers.filter(c => 
        c.name.toLowerCase().includes(q) || 
        (c.city && c.city.toLowerCase().includes(q)) ||
        (c.contact_person && c.contact_person.toLowerCase().includes(q))
    );
    renderCustomers(filtered);
}

function openCustomerModal() {
    document.getElementById('customer-form').reset();
    document.getElementById('cust-state').value = 'Uttar Pradesh';
    document.getElementById('cust-gstin').value = 'N/A';
    openModal('modal-customer');
}

async function saveCustomer(e) {
    e.preventDefault();
    const payload = {
        name: document.getElementById('cust-name').value,
        contact_person: document.getElementById('cust-contact').value,
        phone: document.getElementById('cust-phone').value,
        email: document.getElementById('cust-email').value,
        address: document.getElementById('cust-address').value,
        city: document.getElementById('cust-city').value,
        state: document.getElementById('cust-state').value,
        gstin: document.getElementById('cust-gstin').value || 'N/A'
    };

    try {
        await fetch('/api/customers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        closeModal('modal-customer');
        loadCustomers();
    } catch (e) {
        alert('Error saving customer: ' + e);
    }
}

async function deleteCustomer(id) {
    if (!confirm('Are you sure you want to delete this customer?')) return;
    await fetch(`/api/customers/${id}`, { method: 'DELETE' });
    loadCustomers();
}

// ---------------- PRODUCTS ----------------
async function loadProducts() {
    try {
        const res = await fetch('/api/products');
        state.products = await res.json();
        renderProducts(state.products);
    } catch (e) {
        console.error('Error loading products:', e);
    }
}

function renderProducts(products) {
    const grid = document.getElementById('products-cards-grid');
    if (!products || products.length === 0) {
        grid.innerHTML = '<div class="col-span-3 p-8 text-center text-slate-400 bg-white dark:bg-slate-900 rounded-xl border border-dashed dark:border-slate-800">No medical equipment catalog items yet</div>';
        return;
    }

    grid.innerHTML = products.map(p => `
        <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden flex flex-col hover:border-blue-300 dark:hover:border-blue-700 transition">
            <div class="h-40 bg-slate-100 dark:bg-slate-800 flex items-center justify-center p-3">
                <img src="${p.image_url || '/static/images/products/radiography_system.png'}" alt="${p.name}" class="max-h-full max-w-full object-contain">
            </div>
            <div class="p-4 flex-1 flex flex-col justify-between">
                <div>
                    <div class="flex items-start justify-between">
                        <span class="text-[10px] font-bold bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded border border-blue-200 dark:border-blue-800">${p.category || 'Equipment'}</span>
                        <span class="text-[10px] text-slate-500 dark:text-slate-400 font-medium">HSN/SAC: ${p.hsn_code}</span>
                    </div>
                    <h4 class="font-bold text-slate-900 dark:text-white text-sm mt-2">${p.name}</h4>
                    <p class="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">${p.description || ''}</p>
                </div>
                <div class="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                    <div>
                        <span class="text-xs text-slate-400">Default Rate:</span>
                        <div class="font-bold text-slate-900 dark:text-white text-sm">${formatCurrency(p.default_rate)} <span class="text-xs font-normal text-slate-500 dark:text-slate-400">/ ${p.unit}</span></div>
                    </div>
                    <button onclick="deleteProduct(${p.id})" class="text-xs text-rose-600 hover:text-rose-800 font-semibold">Delete</button>
                </div>
            </div>
        </div>
    `).join('');
}

function filterProducts() {
    const q = document.getElementById('search-products').value.toLowerCase();
    const filtered = state.products.filter(p => 
        p.name.toLowerCase().includes(q) || 
        p.hsn_code.includes(q) ||
        (p.category && p.category.toLowerCase().includes(q))
    );
    renderProducts(filtered);
}

function openProductModal() {
    document.getElementById('product-form').reset();
    document.getElementById('prod-category').value = 'Medical Equipment';
    document.getElementById('prod-hsn').value = '9018';
    document.getElementById('prod-gst').value = '5.0';
    document.getElementById('prod-unit').value = 'Pcs';
    document.getElementById('prod-tax-mode').value = 'exclusive';
    openModal('modal-product');
}

async function saveProduct(e) {
    e.preventDefault();
    let imageUrl = '/static/images/products/radiography_system.png';
    
    const fileInput = document.getElementById('prod-image-file');
    if (fileInput.files.length > 0) {
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        try {
            const upRes = await fetch('/api/products/upload-image', { method: 'POST', body: formData });
            const upData = await upRes.json();
            imageUrl = upData.image_url;
        } catch (err) {
            console.warn('Image upload failed, using default', err);
        }
    }

    const payload = {
        name: document.getElementById('prod-name').value,
        category: document.getElementById('prod-category').value,
        hsn_code: document.getElementById('prod-hsn').value,
        default_rate: parseFloat(document.getElementById('prod-rate').value) || 0,
        gst_rate: parseFloat(document.getElementById('prod-gst').value) || 5.0,
        unit: document.getElementById('prod-unit').value,
        description: document.getElementById('prod-desc').value,
        image_url: imageUrl,
        is_tax_inclusive: document.getElementById('prod-tax-mode').value === 'inclusive'
    };

    try {
        await fetch('/api/products', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        closeModal('modal-product');
        loadProducts();
    } catch (e) {
        alert('Error saving product: ' + e);
    }
}

async function deleteProduct(id) {
    if (!confirm('Are you sure you want to delete this equipment?')) return;
    await fetch(`/api/products/${id}`, { method: 'DELETE' });
    loadProducts();
}

// ---------------- BACKUP & RESTORE ----------------
async function loadBackups() {
    try {
        const res = await fetch('/api/backups');
        state.backups = await res.json();
        renderBackups(state.backups);
    } catch (e) {
        console.error('Error loading backups:', e);
    }
}

function renderBackups(backups) {
    const tbody = document.getElementById('backups-table-body');
    if (!backups || backups.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="p-4 text-center text-slate-400">No backup snapshots found</td></tr>';
        return;
    }

    tbody.innerHTML = backups.map(b => `
        <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition">
            <td class="p-3.5 font-semibold text-slate-800 dark:text-slate-200">${b.filename}</td>
            <td class="p-3.5 text-slate-600 dark:text-slate-400">${b.size_kb} KB</td>
            <td class="p-3.5 text-slate-600 dark:text-slate-400">${b.created_at}</td>
            <td class="p-3.5 text-center space-x-2">
                <a href="/api/backups/download/${b.filename}" class="bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 hover:bg-blue-100 px-3 py-1 rounded font-semibold text-xs border border-blue-200 dark:border-blue-800">
                    Download File
                </a>
                <button onclick="restoreBackupFile('${b.filename}')" class="bg-amber-50 dark:bg-amber-950 text-amber-800 dark:text-amber-300 hover:bg-amber-100 px-3 py-1 rounded font-semibold text-xs border border-amber-200 dark:border-amber-800">
                    Restore This
                </button>
            </td>
        </tr>
    `).join('');
}

async function triggerManualBackup() {
    try {
        const res = await fetch('/api/backups/create', { method: 'POST' });
        const data = await res.json();
        alert(data.message);
        loadBackups();
    } catch (e) {
        alert('Failed to create backup: ' + e);
    }
}

async function restoreBackupFile(filename) {
    if (!confirm(`Warning: Restoring "${filename}" will replace your current data with this snapshot. A safety backup will be created automatically. Proceed?`)) return;
    try {
        const res = await fetch(`/api/backups/restore/${filename}`, { method: 'POST' });
        const data = await res.json();
        alert(data.message);
        loadDashboard();
        loadInvoices();
        loadQuotations();
    } catch (e) {
        alert('Restore error: ' + e);
    }
}

async function uploadBackupFile(e) {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    try {
        await fetch('/api/backups/upload', { method: 'POST', body: formData });
        alert('Backup file uploaded! You can now click "Restore This" from the list.');
        loadBackups();
    } catch (err) {
        alert('Failed to upload backup: ' + err);
    }
}

// ---------------- SETTINGS & BRANDING ----------------
function applyBranding(s) {
    if (!s) return;
    const nameEl = document.getElementById('sidebar-company-name');
    if (nameEl) {
        nameEl.textContent = s.name || 'Open ERP';
        nameEl.title = s.name || '';
    }
    const tagEl = document.getElementById('sidebar-company-tagline');
    if (tagEl) {
        tagEl.textContent = s.tagline || 'Billing & Invoicing';
        tagEl.title = s.tagline || '';
    }
    document.title = s.name ? `${s.name} - ERP System` : 'Open Business ERP';

    const timestamp = state.logoTimestamp || Date.now();
    const logoSrc = `/static/images/logo.png?t=${timestamp}`;
    const sideLogo = document.getElementById('sidebar-logo');
    if (sideLogo) sideLogo.src = logoSrc;
    const previewLogo = document.getElementById('settings-logo-preview');
    if (previewLogo) previewLogo.src = logoSrc;
}

function handleGstinInput(input) {
    if (!input) return;
    const val = input.value.trim().toUpperCase();
    input.value = val;
    // GSTIN in India: First 2 digits are state code
    if (val.length >= 2) {
        const potentialCode = val.substring(0, 2);
        if (/^\d{2}$/.test(potentialCode)) {
            const codeInput = document.getElementById('set-state-code');
            if (codeInput) codeInput.value = potentialCode;
        }
    }
}

async function loadSettings() {
    try {
        const res = await fetch('/api/settings');
        state.settings = await res.json();
        const s = state.settings;

        if (document.getElementById('set-name')) document.getElementById('set-name').value = s.name || '';
        if (document.getElementById('set-tagline')) document.getElementById('set-tagline').value = s.tagline || '';
        if (document.getElementById('set-address')) document.getElementById('set-address').value = s.address || '';
        if (document.getElementById('set-phone')) document.getElementById('set-phone').value = s.phone || '';
        if (document.getElementById('set-email')) document.getElementById('set-email').value = s.email || '';
        if (document.getElementById('set-gstin')) document.getElementById('set-gstin').value = s.gstin || '';
        if (document.getElementById('set-state')) document.getElementById('set-state').value = s.state || 'Uttar Pradesh';
        if (document.getElementById('set-state-code')) document.getElementById('set-state-code').value = s.state_code || '09';

        if (document.getElementById('set-invoice-prefix')) document.getElementById('set-invoice-prefix').value = s.invoice_prefix || 'INV/';
        if (document.getElementById('set-quotation-prefix')) document.getElementById('set-quotation-prefix').value = s.quotation_prefix || 'QT/';
        if (document.getElementById('set-challan-prefix')) document.getElementById('set-challan-prefix').value = s.challan_prefix || 'DC/';

        if (document.getElementById('set-bank-name')) document.getElementById('set-bank-name').value = s.bank_name || '';
        if (document.getElementById('set-branch')) document.getElementById('set-branch').value = s.branch || '';
        if (document.getElementById('set-account-no')) document.getElementById('set-account-no').value = s.account_no || '';
        if (document.getElementById('set-ifsc')) document.getElementById('set-ifsc').value = s.ifsc || '';
        if (document.getElementById('set-upi-address')) document.getElementById('set-upi-address').value = s.upi_address || '';
        if (document.getElementById('set-upi-name')) document.getElementById('set-upi-name').value = s.upi_name || '';

        if (document.getElementById('set-terms-invoice')) document.getElementById('set-terms-invoice').value = s.terms_invoice || '';
        if (document.getElementById('set-terms-quotation')) document.getElementById('set-terms-quotation').value = s.terms_quotation || '';
        if (document.getElementById('set-terms-challan')) document.getElementById('set-terms-challan').value = s.terms_challan || '';

        applyBranding(s);
    } catch (e) {
        console.error('Error loading settings:', e);
    }
}

async function uploadLogoFile(e) {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    try {
        const res = await fetch('/api/settings/upload-logo', { method: 'POST', body: formData });
        const data = await res.json();
        state.logoTimestamp = Date.now();
        applyBranding(state.settings);
        alert(data.message);
    } catch (err) {
        alert('Failed to upload logo: ' + err);
    }
}

async function resetLogoToDefault() {
    if (!confirm('Are you sure you want to reset the company logo to the default emblem?')) return;
    try {
        const res = await fetch('/api/settings/reset-logo', { method: 'POST' });
        const data = await res.json();
        state.logoTimestamp = Date.now();
        applyBranding(state.settings);
        alert(data.message);
    } catch (err) {
        alert('Failed to reset logo: ' + err);
    }
}

async function saveSettings(e) {
    e.preventDefault();
    const payload = {
        name: document.getElementById('set-name').value.trim(),
        tagline: document.getElementById('set-tagline').value.trim(),
        address: document.getElementById('set-address').value.trim(),
        phone: document.getElementById('set-phone').value.trim(),
        email: document.getElementById('set-email').value.trim(),
        gstin: document.getElementById('set-gstin').value.trim(),
        state: document.getElementById('set-state').value.trim(),
        state_code: (document.getElementById('set-state-code')?.value || '09').trim(),
        bank_name: document.getElementById('set-bank-name').value.trim(),
        branch: document.getElementById('set-branch').value.trim(),
        account_no: document.getElementById('set-account-no').value.trim(),
        ifsc: document.getElementById('set-ifsc').value.trim(),
        upi_address: document.getElementById('set-upi-address').value.trim(),
        upi_name: document.getElementById('set-upi-name').value.trim(),
        invoice_prefix: (document.getElementById('set-invoice-prefix')?.value || 'INV/').trim(),
        quotation_prefix: (document.getElementById('set-quotation-prefix')?.value || 'QT/').trim(),
        challan_prefix: (document.getElementById('set-challan-prefix')?.value || 'DC/').trim(),
        terms_invoice: document.getElementById('set-terms-invoice').value,
        terms_quotation: document.getElementById('set-terms-quotation').value,
        terms_challan: document.getElementById('set-terms-challan')?.value || '',
        logo_url: state.settings?.logo_url || '/static/images/logo.png'
    };

    try {
        const res = await fetch('/api/settings', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        alert(data.message);
        await loadSettings();
    } catch (e) {
        alert('Error saving settings: ' + e);
    }
}

// ---------------- PWA INSTALLATION & SERVICE WORKER ----------------
let deferredInstallPrompt = null;
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredInstallPrompt = e;
    const container = document.getElementById('pwa-install-container');
    if (container) container.classList.remove('hidden');
});

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    loadSettings();

    const installBtn = document.getElementById('pwa-install-btn');
    if (installBtn) {
        installBtn.addEventListener('click', async () => {
            if (!deferredInstallPrompt) return;
            deferredInstallPrompt.prompt();
            const choice = await deferredInstallPrompt.userChoice;
            if (choice.outcome === 'accepted') {
                document.getElementById('pwa-install-container').classList.add('hidden');
            }
            deferredInstallPrompt = null;
        });
    }

    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/service-worker.js').catch(err => {
            console.log('ServiceWorker registration skipped:', err);
        });
    }

    switchTab('dashboard');
});
