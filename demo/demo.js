/*
 * Static demo layer for the Grocery Inventory Tracker.
 *
 * The pages are the app's real Jinja templates rendered at build time by
 * scripts/build_demo.py. This script replaces the Flask routes: the inventory
 * lives in localStorage, and the dynamic parts of each page are re-rendered
 * here with the same markup the templates produce.
 */
(function () {
    'use strict';

    const SEED = window.DEMO_SEED;
    const STORE_KEY = 'groceryDemo.v1';
    const FLASH_KEY = 'groceryDemo.flash';
    const page = document.body.dataset.demoPage;
    let memoryStore = null;

    // ---------- dates ----------
    function pad(n) { return String(n).padStart(2, '0'); }
    function isoDate(d) { return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`; }
    function todayIso() { return isoDate(new Date()); }
    function addDays(days) { const d = new Date(); d.setDate(d.getDate() + days); return isoDate(d); }
    function addMonths(months) { const d = new Date(); d.setMonth(d.getMonth() + months); return isoDate(d); }
    function parseIso(s) {
        const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s || '');
        if (!m) return null;
        const t = Date.UTC(+m[1], +m[2] - 1, +m[3]);
        const d = new Date(t);
        return d.getUTCMonth() === +m[2] - 1 ? t : null;
    }
    function daysUntil(s) { return Math.round((parseIso(s) - parseIso(todayIso())) / 86400000); }

    // ---------- storage ----------
    function freshState() {
        const items = SEED.items.map((it, i) => ({
            id: i + 1,
            name: it.name,
            quantity: it.quantity,
            category: it.category,
            notes: it.notes || '',
            purchase_date: addDays(it.purchase_offset),
            expiry_date: it.expiry_offset === null ? null : addDays(it.expiry_offset),
            created: i + 1,
        }));
        return { nextId: items.length + 1, items, settings: { warningDays: SEED.warningDays, notificationsEnabled: true, notificationTime: '09:00' } };
    }
    function load() {
        try {
            const raw = localStorage.getItem(STORE_KEY);
            if (raw) return JSON.parse(raw);
        } catch (e) { /* storage blocked or corrupt: fall through */ }
        if (memoryStore) return memoryStore;
        const state = freshState();
        save(state);
        return state;
    }
    function save(state) {
        memoryStore = state;
        try { localStorage.setItem(STORE_KEY, JSON.stringify(state)); } catch (e) { /* in-memory only */ }
    }
    let state = load();

    // ---------- flash messages (same markup as layout.html) ----------
    function queueFlash(category, message) {
        let list = [];
        try { list = JSON.parse(sessionStorage.getItem(FLASH_KEY) || '[]'); } catch (e) { list = []; }
        list.push([category, message]);
        try { sessionStorage.setItem(FLASH_KEY, JSON.stringify(list)); } catch (e) { /* ignore */ }
    }
    function showFlash(category, message) {
        const main = document.querySelector('main');
        const div = document.createElement('div');
        div.className = `alert alert-${category === 'error' ? 'danger' : category} alert-dismissible fade show`;
        div.setAttribute('role', 'alert');
        div.textContent = message;
        const close = document.createElement('button');
        close.type = 'button';
        close.className = 'btn-close';
        close.setAttribute('data-bs-dismiss', 'alert');
        close.setAttribute('aria-label', 'Close');
        div.appendChild(close);
        main.insertBefore(div, main.firstChild);
    }
    function drainFlashes() {
        let list = [];
        try {
            list = JSON.parse(sessionStorage.getItem(FLASH_KEY) || '[]');
            sessionStorage.removeItem(FLASH_KEY);
        } catch (e) { list = []; }
        list.reverse().forEach(([c, m]) => showFlash(c, m));
    }
    function redirect(url, category, message) {
        if (message) queueFlash(category, message);
        window.location.href = url;
    }

    // ---------- helpers ----------
    function esc(value) {
        return String(value === null || value === undefined ? '' : value)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }
    function plural(n) { return n === 1 ? '' : 's'; }
    function findItem(id) { return state.items.find(i => i.id === id); }
    function warningDays() { return parseInt(state.settings.warningDays, 10) || 7; }
    function categoryOf(item) { return item.category || 'Other'; }
    function cmp(a, b) { return a < b ? -1 : a > b ? 1 : 0; }

    // Mirrors validate_grocery_item() and the expiry checks in app.py
    function validate(name, quantity, purchaseDate, expiryDate) {
        if (!name || !quantity || !purchaseDate) return 'Name, quantity, and purchase date are required';
        if (!/^-?\d+$/.test(quantity)) return 'Quantity must be a valid number';
        const qty = parseInt(quantity, 10);
        if (qty <= 0) return 'Quantity must be a positive number';
        if (qty > 10000) return 'Quantity seems unreasonably high';
        if (parseIso(purchaseDate) === null) return 'Invalid date format. Use YYYY-MM-DD';
        if (name.length > 100) return 'Item name is too long (max 100 characters)';
        if (name.length < 2) return 'Item name is too short (min 2 characters)';
        if (expiryDate) {
            if (parseIso(expiryDate) === null) return 'Invalid expiry date format';
            if (parseIso(expiryDate) < parseIso(purchaseDate)) return 'Expiry date cannot be before purchase date';
        }
        return null;
    }
    function readItemForm(form) {
        const get = n => (form.elements[n] ? String(form.elements[n].value).trim() : '');
        const category = form.elements.category ? form.elements.category.value : 'Other';
        return {
            name: get('name'),
            quantity: get('quantity'),
            purchase_date: get('purchase_date'),
            expiry_date: get('expiry_date'),
            category: SEED.categories.includes(category) ? category : 'Other',
            notes: get('notes'),
            keep_separate: !!(form.elements.keep_separate && form.elements.keep_separate.checked),
        };
    }
    function showFormError(form, message) {
        let alert = form.parentElement.querySelector('.alert.alert-danger.demo-form-error');
        if (!alert) {
            alert = document.createElement('div');
            alert.className = 'alert alert-danger demo-form-error';
            form.parentElement.insertBefore(alert, form);
        }
        alert.textContent = message;
        alert.scrollIntoView({ block: 'center' });
    }
    // Mirrors inventory.py: an item already in stock (same normalized name and
    // category, expiry dates both missing or within the merge window) is
    // merged into the existing row instead of creating a duplicate.
    function normalizeName(name) {
        const words = String(name || '').toLowerCase().replace(/[^\p{L}\p{N}_\s]/gu, ' ').split(/\s+/).filter(Boolean);
        const last = words.length ? words[words.length - 1] : '';
        if (last.length > 3 && last.endsWith('s') && !last.endsWith('ss')) words[words.length - 1] = last.slice(0, -1);
        return words.join(' ');
    }
    function daysApart(a, b) {
        const ta = parseIso(a), tb = parseIso(b);
        return ta === null || tb === null ? null : Math.abs(Math.round((ta - tb) / 86400000));
    }
    function expiryClose(a, b) {
        if (!a && !b) return true;
        if (!a || !b) return false;
        const gap = daysApart(a, b);
        return gap !== null && gap <= (SEED.mergeWindowDays ?? 3);
    }
    function findMergeCandidate(data) {
        const key = normalizeName(data.name);
        const expiry = data.expiry_date || null;
        let best = null, bestGap = null;
        state.items.forEach(it => {
            if (categoryOf(it) !== data.category || normalizeName(it.name) !== key || !expiryClose(it.expiry_date, expiry)) return;
            const gap = expiry ? daysApart(it.expiry_date, expiry) : 0;
            if (best === null || gap < bestGap) { best = it; bestGap = gap; }
        });
        return best;
    }
    // Returns { item, merged }
    function addOrMerge(data) {
        const existing = data.keep_separate ? null : findMergeCandidate(data);
        if (!existing) return { item: addItem(data), merged: false };
        existing.quantity = Math.min(existing.quantity + parseInt(data.quantity, 10), 10000);
        const expiries = [existing.expiry_date, data.expiry_date].filter(Boolean).sort();
        existing.expiry_date = expiries.length ? expiries[0] : null;
        if (data.purchase_date > existing.purchase_date) existing.purchase_date = data.purchase_date;
        const notes = data.notes || '';
        const old = existing.notes || '';
        if (notes && !old.toLowerCase().includes(notes.toLowerCase())) existing.notes = old ? `${old}; ${notes}` : notes;
        return { item: existing, merged: true };
    }
    function addedMessage(result) {
        return result.merged
            ? `${result.item.name} was already in stock, so the quantities were combined. You now have ${result.item.quantity}.`
            : 'Item added successfully!';
    }
    function addItem(data) {
        const item = {
            id: state.nextId++,
            name: data.name,
            quantity: parseInt(data.quantity, 10),
            category: data.category,
            notes: data.notes || '',
            purchase_date: data.purchase_date,
            expiry_date: data.expiry_date || null,
            created: Date.now(),
        };
        state.items.push(item);
        return item;
    }
    function toast(message) {
        const div = document.createElement('div');
        div.className = 'alert alert-success demo-toast';
        div.textContent = message;
        document.body.appendChild(div);
        setTimeout(() => div.remove(), 2500);
    }
    function shareText(text, title) {
        if (navigator.share) {
            navigator.share({ title, text }).catch(() => {});
        } else if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).then(() => toast('Copied to clipboard'), () => window.prompt('Copy this text:', text));
        } else {
            window.prompt('Copy this text:', text);
        }
    }

    // Mirrors barcode_catalog.py and the /api/barcode route: GS1 check digit,
    // then a lookup in the small offline catalog shipped with the app.
    function gs1CheckDigit(body) {
        let total = 0;
        body.split('').reverse().forEach((d, i) => { total += Number(d) * (i % 2 === 0 ? 3 : 1); });
        return (10 - (total % 10)) % 10;
    }
    function barcodeLookup(code) {
        const valid = /^\d+$/.test(code) && [8, 12, 13, 14].includes(code.length) && gs1CheckDigit(code.slice(0, -1)) === Number(code.slice(-1));
        if (!valid) return [{ barcode: code, found: false, error: 'Enter an 8, 12, 13, or 14 digit barcode with a valid check digit.' }, 400];
        const key = code.replace(/^0+/, '');
        const product = (SEED.barcodes || []).find(p => p.barcode.replace(/^0+/, '') === key);
        if (!product) return [{ barcode: code, found: false, message: 'Not in the local catalog. Enter the product details manually.' }, 404];
        return [{ barcode: code, found: true, name: product.name, category: product.category, source: 'local catalog' }, 200];
    }

    // Answer the app's JSON endpoints locally so page scripts never hit a server.
    const realFetch = window.fetch ? window.fetch.bind(window) : null;
    let scanCount = 0;
    window.fetch = function (input, init) {
        const url = typeof input === 'string' ? input : (input && input.url) || '';
        const json = (body, status = 200) => Promise.resolve(new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } }));
        let m = /\/api\/barcode\/([^/?#]+)/.exec(url);
        if (m) return json(...barcodeLookup(decodeURIComponent(m[1]).trim()));
        m = /\/api\/share\/(\d+)/.exec(url);
        if (m) {
            const it = findItem(+m[1]);
            return json(it ? { id: it.id, name: it.name, quantity: it.quantity, category: it.category, expiry_date: it.expiry_date } : { error: 'Item not found' });
        }
        if (/\/api\/ocr\/scan/.test(url)) {
            // Answer with a precomputed sample receipt: the matching sample by file name, else the next one in turn.
            const file = init && init.body && init.body.get ? init.body.get('receipt') : null;
            const m2 = file && /sample-receipt-(\d+)/.exec(file.name || '');
            let receipt = m2 ? SEED.receipts.find(r => r.id === +m2[1]) : null;
            if (!receipt) receipt = SEED.receipts[(scanCount++) % SEED.receipts.length];
            return new Promise(resolve => setTimeout(resolve, 600 + Math.round(receipt.seconds * 400)))
                .then(() => json({ receipt_id: receipt.id, items: receipt.items, seconds: receipt.seconds }));
        }
        if (/^\/api\//.test(url)) return json({});
        return realFetch(input, init);
    };

    // ---------- banner ----------
    const resetBtn = document.getElementById('demo-reset');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            if (!confirm('Restore the sample inventory? Your changes in this browser will be lost.')) return;
            state = freshState();
            save(state);
            try { localStorage.removeItem('shoppingList'); } catch (e) { /* ignore */ }
            redirect('index.html', 'success', 'Sample data restored.');
        });
    }

    // ---------- inventory dashboard (index.html) ----------
    function withExpiry(item) {
        const out = Object.assign({}, item);
        if (item.expiry_date && parseIso(item.expiry_date) !== null) {
            const days = daysUntil(item.expiry_date);
            out.days_until_expiry = days;
            out.expiry_status = days < 0 ? 'expired' : days <= warningDays() ? 'warning' : 'good';
        } else {
            out.days_until_expiry = null;
            out.expiry_status = 'none';
        }
        return out;
    }

    const SORTS = {
        name: (a, b) => cmp(a.name.toLowerCase(), b.name.toLowerCase()),
        purchase_date: (a, b) => cmp(b.purchase_date, a.purchase_date) || cmp(b.created, a.created),
        expiry_date: (a, b) => cmp(a.expiry_date === null, b.expiry_date === null) || cmp(a.expiry_date || '', b.expiry_date || ''),
        quantity: (a, b) => b.quantity - a.quantity,
        category: (a, b) => cmp(categoryOf(a), categoryOf(b)) || cmp(a.name.toLowerCase(), b.name.toLowerCase()),
    };

    function useSoonWhen(days) {
        if (days < 0) return `Expired ${-days} day${days === -1 ? '' : 's'} ago`;
        if (days === 0) return 'Expires today';
        if (days === 1) return 'Expires tomorrow';
        return `${days} days left`;
    }

    function statusBadge(item) {
        if (item.expiry_status === 'expired') return '<span class="status status-expired">Expired</span>';
        if (item.expiry_status === 'warning') {
            const d = item.days_until_expiry;
            return `<span class="status status-warning">${d === 0 ? 'Expires today' : `${d} day${plural(d)} left`}</span>`;
        }
        if (item.expiry_status === 'good') return '<span class="status status-good">Fresh</span>';
        return '<span class="status status-none">No date</span>';
    }

    function rowHtml(item) {
        const cat = categoryOf(item);
        return `
            <tr class="row-${item.expiry_status}">
                <td>
                    <div class="fw-semibold">${esc(item.name)}</div>
                    ${item.notes ? `<div class="small text-muted">${esc(item.notes)}</div>` : ''}
                </td>
                <td><span class="category-pill cat-${esc(cat.toLowerCase())}">${esc(cat)}</span></td>
                <td class="text-end">${item.quantity}</td>
                <td class="d-none d-md-table-cell text-muted">${esc(item.purchase_date)}</td>
                <td>${esc(item.expiry_date || '-')}</td>
                <td>${statusBadge(item)}</td>
                <td class="text-end text-nowrap">
                    <form method="POST" action="index.html" class="d-inline use-form" data-id="${item.id}">
                        <button type="submit" class="btn btn-sm btn-light" title="Take one off the quantity">Used</button>
                    </form>
                    <a href="edit.html?id=${item.id}" class="btn btn-sm btn-light">Edit</a>
                    <button type="button" class="btn btn-sm btn-light share-btn" data-id="${item.id}">Share</button>
                    <form method="POST" action="index.html" class="d-inline delete-form" data-id="${item.id}" data-name="${esc(item.name)}">
                        <button type="submit" class="btn btn-sm btn-light text-danger">Delete</button>
                    </form>
                </td>
            </tr>`;
    }

    function renderIndex() {
        const params = new URLSearchParams(window.location.search);
        const search = (params.get('search') || '').trim();
        const category = params.get('category') || '';
        const sort = SORTS[params.get('sort')] ? params.get('sort') : 'purchase_date';
        const form = document.querySelector('form.filter-bar');
        form.elements.search.value = search;
        form.elements.category.value = category;
        form.elements.sort.value = sort;

        const wd = warningDays();
        const all = state.items.map(withExpiry);
        let list = all.filter(i => (!search || i.name.toLowerCase().includes(search.toLowerCase())) && (!category || i.category === category));
        list.sort(SORTS[sort]);

        const expiringSoon = all.filter(i => i.days_until_expiry !== null && i.days_until_expiry >= 0 && i.days_until_expiry <= wd).length;
        const expired = all.filter(i => i.days_until_expiry !== null && i.days_until_expiry < 0).length;
        const cats = new Set(all.map(i => i.category)).size;
        const values = document.querySelectorAll('.stat-card .stat-value');
        [all.length, expiringSoon, expired, cats].forEach((v, idx) => { if (values[idx]) values[idx].textContent = v; });
        const hint = document.querySelectorAll('.stat-card .stat-hint')[1];
        if (hint) hint.textContent = `within ${wd} days`;

        // "Use these first" panel
        const useSoon = all.filter(i => i.days_until_expiry !== null && i.days_until_expiry <= wd)
            .sort((a, b) => cmp(a.expiry_date, b.expiry_date) || cmp(a.name, b.name));
        const oldPanel = document.getElementById('use-soon');
        if (oldPanel) oldPanel.remove();
        if (useSoon.length) {
            const section = document.createElement('section');
            section.className = 'panel mb-4';
            section.id = 'use-soon';
            section.innerHTML = `
                <div class="panel-header">
                    <h2 class="h5 mb-0">Use these first</h2>
                    <span class="text-muted small">Expired or expiring within ${wd} days</span>
                </div>
                <div class="use-soon-grid">
                    ${useSoon.slice(0, 10).map(i => `
                    <a href="edit.html?id=${i.id}" class="use-soon-item ${i.days_until_expiry < 0 ? 'is-expired' : i.days_until_expiry <= 2 ? 'is-urgent' : ''}">
                        <div class="fw-semibold">${esc(i.name)}</div>
                        <div class="small text-muted">${esc(categoryOf(i))} &middot; qty ${i.quantity}</div>
                        <div class="use-soon-when">${useSoonWhen(i.days_until_expiry)}</div>
                    </a>`).join('')}
                </div>
                ${useSoon.length > 10 ? `<div class="mt-3 small"><a href="index.html?sort=expiry_date">and ${useSoon.length - 10} more, sorted by expiry date</a></div>` : ''}`;
            form.parentElement.insertBefore(section, form);
        }

        // Table or empty state
        let after = form.nextElementSibling;
        while (after && after.tagName === 'SCRIPT') after = after.nextElementSibling;
        const holder = document.createElement('div');
        if (list.length) {
            holder.className = 'table-responsive panel p-0';
            holder.innerHTML = `
                <table class="table inventory-table align-middle mb-0">
                    <thead>
                        <tr>
                            <th>Item</th>
                            <th>Category</th>
                            <th class="text-end">Qty</th>
                            <th class="d-none d-md-table-cell">Purchased</th>
                            <th>Expires</th>
                            <th>Status</th>
                            <th class="text-end">Actions</th>
                        </tr>
                    </thead>
                    <tbody>${list.map(rowHtml).join('')}</tbody>
                </table>`;
        } else {
            holder.className = 'panel text-center py-5';
            holder.innerHTML = (search || category)
                ? '<p class="mb-2">No items match your filters.</p><a href="index.html">Clear filters</a>'
                : '<p class="mb-2">Your fridge is empty.</p><p class="mb-0"><a href="add.html">Add your first item</a> or <a href="ocr.html">scan a receipt</a>.</p>';
        }
        if (after && (after.classList.contains('panel') || after.classList.contains('table-responsive'))) {
            after.replaceWith(holder);
        } else {
            form.after(holder);
        }
    }

    function initIndex() {
        renderIndex();
        const main = document.querySelector('main');
        main.addEventListener('submit', event => {
            const form = event.target;
            if (!form.matches('.delete-form, .use-form')) return;
            event.preventDefault();
            const item = findItem(+form.dataset.id);
            if (!item) { showFlash('error', 'Item not found'); return; }
            let message;
            if (form.matches('.delete-form')) {
                if (!confirm(`Delete ${item.name}?`)) return;
                state.items = state.items.filter(i => i.id !== item.id);
                message = 'Item deleted successfully!';
            } else if (item.quantity > 1) {
                item.quantity -= 1;
                message = `Marked one ${item.name} as used. ${item.quantity} left.`;
            } else {
                state.items = state.items.filter(i => i.id !== item.id);
                message = `Used the last ${item.name}. Removed it from the inventory.`;
            }
            save(state);
            main.querySelectorAll(':scope > .alert').forEach(a => a.remove());
            renderIndex();
            showFlash('success', message);
        });
        main.addEventListener('click', event => {
            const btn = event.target.closest('.share-btn');
            if (!btn) return;
            const it = findItem(+btn.dataset.id);
            if (!it) return;
            shareText(`${it.name} - Quantity: ${it.quantity}, Category: ${it.category}${it.expiry_date ? ', Expires: ' + it.expiry_date : ''}`, 'Grocery item');
        });
    }

    // ---------- add / edit ----------
    function bindItemForm(form, onValid) {
        form.addEventListener('submit', event => {
            event.preventDefault();
            const data = readItemForm(form);
            const error = validate(data.name, data.quantity, data.purchase_date, data.expiry_date);
            if (error) { showFormError(form, error); return; }
            onValid(data);
        });
    }

    function initAdd() {
        const form = document.querySelector('form.grocery-form');
        bindItemForm(form, data => {
            const result = addOrMerge(data);
            save(state);
            redirect('index.html', 'success', addedMessage(result));
        });
    }

    function initEdit() {
        const id = parseInt(new URLSearchParams(window.location.search).get('id'), 10);
        const item = findItem(id);
        if (!item) { redirect('index.html', 'error', 'Item not found'); return; }
        const form = document.querySelector('form.grocery-form');
        form.setAttribute('action', `edit.html?id=${id}`);
        form.elements.name.value = item.name;
        form.elements.quantity.value = item.quantity;
        form.elements.purchase_date.value = item.purchase_date;
        form.elements.expiry_date.value = item.expiry_date || '';
        form.elements.category.value = categoryOf(item);
        form.elements.notes.value = item.notes || '';
        bindItemForm(form, data => {
            Object.assign(item, {
                name: data.name, quantity: parseInt(data.quantity, 10), purchase_date: data.purchase_date,
                expiry_date: data.expiry_date || null, category: data.category, notes: data.notes,
            });
            save(state);
            redirect('index.html', 'success', 'Item updated successfully!');
        });
    }

    // ---------- receipt upload (ocr.html) ----------
    // The page's own script reads the selected files one at a time through
    // /api/ocr/scan; the fetch() stand-in above answers with the precomputed
    // sample receipts, so single and batch scanning both work offline.
    function loadSample(receipt) {
        return fetch(receipt.image)
            .then(r => r.blob())
            .then(blob => new Promise(resolve => {
                const file = new File([blob], `sample-receipt-${receipt.id}.png`, { type: 'image/png' });
                const reader = new FileReader();
                reader.onload = () => {
                    if (typeof window.handlePhotoResult === 'function') window.handlePhotoResult({ dataUrl: reader.result, file });
                    resolve();
                };
                reader.readAsDataURL(file);
            }))
            .catch(() => {});
    }

    function initOcr() {
        const form = document.getElementById('upload-form');
        const note = document.createElement('div');
        note.className = 'alert alert-info';
        note.innerHTML = '<strong>Demo:</strong> a sample receipt is loaded below. OCR results for the three sample receipts were computed when the demo was built; any photo you add here shows one of those results. '
            + '<button type="button" class="btn btn-sm btn-outline-primary ms-1 mt-1" id="demo-batch">Load all 3 sample receipts</button>';
        form.closest('.card').before(note);
        loadSample(SEED.receipts[0]);
        document.getElementById('demo-batch').addEventListener('click', event => {
            event.target.disabled = true;
            const clear = document.getElementById('clear-btn');
            if (clear) clear.click();
            SEED.receipts.reduce((p, r) => p.then(() => loadSample(r)), Promise.resolve());
        });
    }

    function receiptState(id) {
        state.receipts = state.receipts || {};
        return state.receipts[id] || { status: 'pending', imported: 0 };
    }
    function setReceiptState(id, value) {
        state.receipts = state.receipts || {};
        state.receipts[id] = value;
    }

    // ---------- receipt review (ocr-review.html) ----------
    function initReview() {
        const form = document.getElementById('review-form');
        const wanted = (new URLSearchParams(window.location.search).get('receipts') || '')
            .split(',').map(n => parseInt(n, 10)).filter(n => SEED.receipts.some(r => r.id === n));
        let ids = wanted.length ? wanted : SEED.receipts.map(r => r.id);
        // Like the app, receipts that were already added or discarded drop out of a review
        // (unless nothing is left, so the demo page never comes up empty).
        const pendingIds = ids.filter(id => receiptState(id).status === 'pending');
        if (pendingIds.length) ids = pendingIds;
        // Show only the receipts that were scanned; hidden rows are never added.
        form.querySelectorAll('.receipt-group').forEach(group => {
            if (ids.includes(parseInt(group.dataset.receiptId, 10))) return;
            group.hidden = true;
            group.querySelectorAll('input, select').forEach(el => { el.disabled = true; if (el.type === 'checkbox') el.checked = false; });
        });
        const intro = form.previousElementSibling;
        if (intro) intro.textContent = `Check the items read from ${ids.length > 1 ? `your ${ids.length} receipts` : 'your receipt'}. Fix names, set expiry dates, and untick anything you do not want to save.`;
        const note = document.createElement('div');
        note.className = 'alert alert-info small';
        const engine = SEED.receipts.every(r => r.engine === 'tesseract')
            ? 'the OCR pipeline (OpenCV preprocessing, Tesseract, receipt parser, product catalog)' : 'the receipt parser';
        note.textContent = `Demo: these rows are what ${engine} read from the sample receipt images when the demo was built. Click a receipt image to see it full size.`;
        form.before(note);

        form.addEventListener('submit', event => {
            event.preventDefault();
            if (event.submitter && event.submitter.value === 'discard') {
                ids.forEach(id => setReceiptState(id, { status: 'discarded', imported: 0 }));
                save(state);
                redirect('ocr.html', 'info', 'Scan discarded. Nothing was added.');
                return;
            }
            const selected = Array.from(form.querySelectorAll('input[name="selected"]:checked')).filter(cb => !cb.disabled);
            if (!selected.length) { showFlash('warning', 'No items selected'); return; }
            let added = 0;
            let merged = 0;
            const errors = [];
            const perReceipt = {};
            ids.forEach(id => { perReceipt[id] = 0; });
            selected.forEach(cb => {
                const idx = cb.value;
                const get = n => (form.elements[`${n}_${idx}`] ? String(form.elements[`${n}_${idx}`].value).trim() : '');
                const data = {
                    name: get('name'), quantity: get('quantity'), purchase_date: get('purchase_date'),
                    expiry_date: get('expiry_date'), category: get('category') || 'Other', notes: '',
                };
                if (!SEED.categories.includes(data.category)) data.category = 'Other';
                const error = validate(data.name, data.quantity, data.purchase_date, data.expiry_date);
                if (error) { errors.push(`${data.name}: ${error}`); return; }
                if (addOrMerge(data).merged) merged += 1;
                added += 1;
                const rid = parseInt(cb.closest('.receipt-group').dataset.receiptId, 10);
                perReceipt[rid] = (perReceipt[rid] || 0) + 1;
            });
            ids.forEach(id => setReceiptState(id, { status: 'imported', imported: perReceipt[id] || 0 }));
            save(state);
            const mergedNote = merged ? ` (${merged} combined with items already in stock)` : '';
            if (added) queueFlash('success', `Successfully added ${added} items${mergedNote}!`);
            if (errors.length) queueFlash('warning', `${errors.length} items had errors and were not added`);
            redirect('index.html');
        });
    }

    // ---------- receipt history (receipts.html) ----------
    function initReceipts() {
        const rows = Array.from(document.querySelectorAll('.receipts-table tbody tr'));
        rows.forEach(row => {
            const m = /sample-receipt-(\d+)/.exec(row.innerHTML);
            const receipt = m ? SEED.receipts.find(r => r.id === +m[1]) : null;
            if (!receipt) return;
            const info = receiptState(receipt.id);
            if (info.status === 'deleted') { row.remove(); return; }
            const cells = row.querySelectorAll('td');
            if (info.status === 'imported') {
                cells[3].textContent = `${info.imported} of ${receipt.items} added`;
                cells[4].innerHTML = '<span class="status status-good">Added</span>';
            } else if (info.status === 'discarded') {
                cells[4].innerHTML = '<span class="status status-none">Discarded</span>';
            }
            if (info.status !== 'pending') {
                const review = cells[5].querySelector('a.btn');
                if (review) review.remove();
            }
            const del = row.querySelector('form.delete-receipt-form');
            del.addEventListener('submit', event => {
                if (event.defaultPrevented) return;      // the page's confirm() was cancelled
                event.preventDefault();
                setReceiptState(receipt.id, { status: 'deleted', imported: 0 });
                save(state);
                redirect('receipts.html', 'success', 'Receipt deleted. Items already added to the inventory were kept.');
            });
        });
    }

    // ---------- accounts (login.html, register.html, sign out) ----------
    function initAuth() {
        const form = document.querySelector('form.auth-form');
        const note = document.createElement('div');
        note.className = 'alert alert-info small';
        note.textContent = 'Demo: any username and password sign you in to the sample household. Nothing is sent anywhere. The real app stores salted password hashes and keeps each household’s data separate.';
        form.before(note);
        form.addEventListener('submit', event => {
            event.preventDefault();
            const name = (form.elements.username.value || 'demo').trim();
            if (form.elements.confirm && form.elements.confirm.value !== form.elements.password.value) {
                showFlash('error', 'The two passwords do not match.');
                return;
            }
            redirect('index.html', 'success', page === 'register'
                ? `Welcome, ${name}! Your household inventory is ready.` : `Signed in as ${name} (demo).`);
        });
    }
    document.querySelectorAll('form.logout-form').forEach(form => {
        form.addEventListener('submit', event => {
            event.preventDefault();
            redirect('login.html', 'info', 'You have been signed out.');
        });
    });

    // ---------- shopping list ----------
    function suggestionList(items, badge, label) {
        return `<div class="list-group">${items.map(item => `
            <div class="list-group-item d-flex justify-content-between align-items-center">
                <div>
                    <h5 class="mb-1">${esc(item.name)}</h5>
                    <small>
                        <span class="badge bg-secondary">${esc(item.category)}</span>
                        ${badge(item)}
                    </small>
                </div>
                <div>
                    <button class="btn btn-sm btn-primary" onclick='addToShoppingList(${esc(JSON.stringify(item.name))}, ${esc(JSON.stringify(item.category))})'>
                        ${label}
                    </button>
                </div>
            </div>`).join('')}</div>`;
    }

    function initShopping() {
        const today = todayIso();
        const weekAgo = addDays(-7);
        const lowStock = state.items.filter(i => i.quantity <= 2 && i.quantity > 0).sort((a, b) => a.quantity - b.quantity);
        const expiredRecent = state.items.filter(i => i.expiry_date && i.expiry_date < today && i.expiry_date >= weekAgo)
            .sort((a, b) => cmp(b.expiry_date, a.expiry_date));
        const groups = new Map();
        state.items.forEach(i => {
            const key = i.name.toLowerCase();
            const g = groups.get(key) || { name: i.name, category: i.category, purchase_count: 0, last_purchase: '' };
            g.purchase_count += 1;
            if (i.purchase_date > g.last_purchase) g.last_purchase = i.purchase_date;
            groups.set(key, g);
        });
        const frequent = Array.from(groups.values()).filter(g => g.purchase_count >= 2)
            .sort((a, b) => b.purchase_count - a.purchase_count || cmp(b.last_purchase, a.last_purchase)).slice(0, 10);

        const bodies = document.querySelectorAll('main .card > .card-body');
        bodies[0].innerHTML = lowStock.length
            ? suggestionList(lowStock, i => `<span class="badge bg-warning text-dark ms-1">Only ${i.quantity} left</span>`, 'Add to List')
            : '<div class="alert alert-success">✅ All items are well stocked!</div>';
        bodies[1].innerHTML = expiredRecent.length
            ? suggestionList(expiredRecent, i => `<span class="badge bg-danger ms-1">Expired ${esc(i.expiry_date)}</span>`, 'Re-buy')
            : '<div class="alert alert-info">No recently expired items</div>';
        bodies[2].innerHTML = frequent.length
            ? suggestionList(frequent, i => `<span class="badge bg-info text-dark ms-1">Purchased ${i.purchase_count} times</span>
                        <span class="text-muted ms-1">Last: ${esc(i.last_purchase)}</span>`, 'Add')
            : '<div class="alert alert-info">No frequent purchase patterns detected yet</div>';

        // Share falls back to a prompt when the clipboard is unavailable
        window.shareShoppingList = function () {
            const list = JSON.parse(localStorage.getItem('shoppingList') || '[]');
            if (!list.length) { alert('Your shopping list is empty!'); return; }
            shareText('Shopping List:\n' + list.map((it, i) => `${i + 1}. ${it.name} (${it.category})`).join('\n'), 'My Shopping List');
        };
    }

    // ---------- insights ----------
    function initStatistics() {
        const today = todayIso();
        const items = state.items;
        const expired = items.filter(i => i.expiry_date && i.expiry_date < today);
        const saved = items.length - expired.length;
        const total = saved + expired.length;
        const rate = total ? saved / total * 100 : 0;
        const withDates = items.filter(i => i.expiry_date && i.purchase_date);
        const avg = withDates.length
            ? withDates.reduce((s, i) => s + (parseIso(i.expiry_date) - parseIso(i.purchase_date)) / 86400000, 0) / withDates.length : 0;

        const h2 = document.querySelectorAll('main .stat-card h2');
        [String(saved), String(expired.length), `${rate.toFixed(1)}%`, avg.toFixed(0)].forEach((v, i) => { if (h2[i]) h2[i].textContent = v; });

        const bodies = document.querySelectorAll('main .card > .card-body');
        bodies[0].innerHTML = `
            <div class="progress mb-2" style="height: 28px;">
                <div class="progress-bar" role="progressbar" style="width: ${rate}%">${rate.toFixed(1)}% fresh</div>
            </div>
            <p class="text-muted mb-0">${saved} of ${total} tracked items are still within their expiry date.</p>`;

        const byCat = new Map();
        items.forEach(i => {
            const c = byCat.get(i.category) || { category: i.category, item_count: 0, total_quantity: 0 };
            c.item_count += 1; c.total_quantity += i.quantity; byCat.set(i.category, c);
        });
        const catStats = Array.from(byCat.values()).sort((a, b) => b.item_count - a.item_count);
        const catTotal = catStats.reduce((s, c) => s + c.item_count, 0);
        bodies[1].innerHTML = catStats.length ? `
            <div class="table-responsive"><table class="table table-hover">
                <thead><tr><th>Category</th><th>Items</th><th>Total Quantity</th><th>Distribution</th></tr></thead>
                <tbody>${catStats.map(c => {
                    const pct = catTotal ? c.item_count / catTotal * 100 : 0;
                    return `<tr><td><span class="badge bg-secondary">${esc(c.category)}</span></td><td>${c.item_count}</td><td>${c.total_quantity}</td>
                        <td><div class="progress" style="height: 20px;"><div class="progress-bar" role="progressbar" style="width: ${pct}%">${pct.toFixed(1)}%</div></div></td></tr>`;
                }).join('')}</tbody></table></div>`
            : '<div class="alert alert-info">No data available yet. Start adding items to see statistics!</div>';

        const since = addMonths(-6);
        const byMonth = new Map();
        items.filter(i => i.purchase_date >= since).forEach(i => {
            const key = i.purchase_date.slice(0, 7);
            const m = byMonth.get(key) || { month: key, items_added: 0, total_quantity: 0 };
            m.items_added += 1; m.total_quantity += i.quantity; byMonth.set(key, m);
        });
        const months = Array.from(byMonth.values()).sort((a, b) => cmp(b.month, a.month));
        bodies[2].innerHTML = months.length ? `
            <div class="table-responsive"><table class="table table-striped">
                <thead><tr><th>Month</th><th>Items Added</th><th>Total Quantity</th><th>Trend</th></tr></thead>
                <tbody>${months.map((m, idx) => {
                    let trend = '<span class="badge bg-secondary">-</span>';
                    if (idx < months.length - 1) {
                        const prev = months[idx + 1];
                        trend = m.items_added > prev.items_added ? '<span class="badge bg-success">↗ Growing</span>'
                            : m.items_added < prev.items_added ? '<span class="badge bg-warning">↘ Declining</span>'
                            : '<span class="badge bg-secondary">→ Stable</span>';
                    }
                    return `<tr><td>${m.month}</td><td>${m.items_added}</td><td>${m.total_quantity}</td><td>${trend}</td></tr>`;
                }).join('')}</tbody></table></div>`
            : '<div class="alert alert-info">No trend data available yet</div>';

        const waste = new Map();
        expired.forEach(i => {
            const w = waste.get(i.category) || { category: i.category, expired_count: 0, wasted_quantity: 0 };
            w.expired_count += 1; w.wasted_quantity += i.quantity; waste.set(i.category, w);
        });
        const wasteStats = Array.from(waste.values()).sort((a, b) => b.expired_count - a.expired_count);
        bodies[3].innerHTML = wasteStats.length ? `
            <div class="table-responsive"><table class="table table-hover">
                <thead><tr><th>Category</th><th>Expired Items</th><th>Wasted Quantity</th><th>Action</th></tr></thead>
                <tbody>${wasteStats.map(w => `<tr><td><span class="badge bg-secondary">${esc(w.category)}</span></td><td>${w.expired_count}</td><td>${w.wasted_quantity}</td><td>${
                    w.expired_count > 5 ? '<span class="badge bg-warning text-dark">High waste, check purchase patterns</span>'
                        : w.expired_count > 2 ? '<span class="badge bg-info">Monitor this category</span>'
                        : '<span class="badge bg-success">✓ Good</span>'}</td></tr>`).join('')}</tbody></table></div>`
            : '<div class="alert alert-success">No expired items.</div>';
    }

    // ---------- settings ----------
    function initSettings() {
        const form = document.querySelector('main form');
        const s = state.settings;
        form.elements.notifications_enabled.checked = s.notificationsEnabled !== false;
        form.elements.notification_time.value = s.notificationTime || '09:00';
        form.elements.expiry_warning_days.value = String(warningDays());
        form.addEventListener('submit', event => {
            event.preventDefault();
            const days = parseInt(form.elements.expiry_warning_days.value, 10) || 7;
            state.settings = {
                notificationsEnabled: form.elements.notifications_enabled.checked,
                notificationTime: form.elements.notification_time.value || '09:00',
                warningDays: Math.min(Math.max(days, 1), 30),
            };
            save(state);
            redirect('settings.html', 'success', 'Settings saved successfully!');
        });

        window.exportData = function () {
            const quote = v => {
                const text = String(v === null || v === undefined ? '' : v);
                return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
            };
            const rows = [['ID', 'Name', 'Quantity', 'Category', 'Purchase Date', 'Expiry Date', 'Notes']];
            state.items.slice().sort((a, b) => cmp(b.purchase_date, a.purchase_date)).forEach(i => {
                rows.push([i.id, i.name, i.quantity, i.category, i.purchase_date, i.expiry_date || '', i.notes || '']);
            });
            const blob = new Blob([rows.map(r => r.map(quote).join(',')).join('\r\n') + '\r\n'], { type: 'text/csv' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'grocery_inventory.csv';
            document.body.appendChild(a);
            a.click();
            setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 0);
        };
        window.clearExpiredItems = function () {
            if (!confirm('Remove all expired items from inventory?')) return;
            const today = todayIso();
            const before = state.items.length;
            state.items = state.items.filter(i => !(i.expiry_date && i.expiry_date < today));
            save(state);
            alert(`Removed ${before - state.items.length} expired items`);
            window.location.reload();
        };
        window.confirmReset = function () {
            if (window.prompt('Type "DELETE ALL" to confirm reset:') !== 'DELETE ALL') return;
            state.items = [];
            save(state);
            alert('All data has been reset. Use "Reset demo data" in the banner to bring the sample items back.');
            window.location.href = 'index.html';
        };
    }

    // ---------- barcode ----------
    function initBarcode() {
        // Capture phase on the document runs before the page's own camera handler
        document.addEventListener('click', event => {
            if (!event.target.closest('#start-camera')) return;
            event.stopPropagation();
            const container = document.getElementById('camera-container');
            if (!container.querySelector('.demo-camera-note')) {
                const note = document.createElement('div');
                note.className = 'alert alert-info mt-3 demo-camera-note';
                note.textContent = 'The live camera scanner is turned off in this demo. Enter a barcode number below to try the lookup.';
                container.appendChild(note);
            }
        }, true);
        const form = document.querySelector('#add-form form');
        if (form) {
            bindItemForm(form, data => {
                const result = addOrMerge(data);
                save(state);
                redirect('index.html', 'success', addedMessage(result));
            });
        }
    }

    const inits = {
        index: initIndex,
        add: initAdd,
        edit: initEdit,
        ocr: initOcr,
        'ocr-review': initReview,
        receipts: initReceipts,
        login: initAuth,
        register: initAuth,
        'shopping-list': initShopping,
        statistics: initStatistics,
        settings: initSettings,
        barcode: initBarcode,
    };
    drainFlashes();
    if (inits[page]) inits[page]();
})();
