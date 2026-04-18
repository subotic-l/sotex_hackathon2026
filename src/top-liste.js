const API_BASE = 'http://localhost:5000';

let allItems = [];
let activeTab = 'svi';
let searchQuery = '';
let sortMode = 'najnoviji';

async function loadAll() {
    renderSkeletons();
    try {
        const [fideri, provodnici, potrosaci] = await Promise.all([
            fetch(`${API_BASE}/api/fideri`).then(r => r.json()),
            fetch(`${API_BASE}/api/provodnici`).then(r => r.json()),
            fetch(`${API_BASE}/api/potrosaci`).then(r => r.json()),
        ]);
        allItems = [
            ...fideri.map(x => ({ ...x, tip: 'fider' })),
            ...provodnici.map(x => ({ ...x, tip: 'provodnik' })),
            ...potrosaci.map(x => ({ ...x, tip: 'potrosac' })),
        ];
        render();
    } catch (e) {
        console.error('Greška pri učitavanju:', e);
        document.getElementById('cardsGrid').innerHTML =
            '<p style="color:#c00;grid-column:1/-1;padding:20px">Greška pri učitavanju podataka</p>';
    }
}

// ── Filtering & sorting ─────────────────────────────────────────
function getFiltered() {
    let items = allItems;

    if (activeTab !== 'svi') {
        const map = { fideri: 'fider', provodnici: 'provodnik', potrosaci: 'potrosac' };
        items = items.filter(i => i.tip === map[activeTab]);
    }

    if (searchQuery) {
        const q = searchQuery.toLowerCase();
        items = items.filter(i =>
            (i.naziv || '').toLowerCase().includes(q) ||
            (i.telefon || '').toLowerCase().includes(q) ||
            (i.id_oznaka || '').toLowerCase().includes(q)
        );
    }

    items = [...items].sort((a, b) => {
        switch (sortMode) {
            case 'najnoviji':     return new Date(b.vreme_dolaska) - new Date(a.vreme_dolaska);
            case 'najstariji':    return new Date(a.vreme_dolaska) - new Date(b.vreme_dolaska);
            case 'naziv_az':     return (a.naziv || '').localeCompare(b.naziv || '', 'sr');
            case 'naziv_za':     return (b.naziv || '').localeCompare(a.naziv || '', 'sr');
            case 'opterecenje_desc': return (b.opterecenje_pct || 0) - (a.opterecenje_pct || 0);
            case 'opterecenje_asc':  return (a.opterecenje_pct || 0) - (b.opterecenje_pct || 0);
            default: return 0;
        }
    });

    return items;
}

// ── Render helpers ──────────────────────────────────────────────
function badgeClass(tip) {
    return { fider: 'badge-fider', provodnik: 'badge-provodnik', potrosac: 'badge-potrosac' }[tip] || '';
}

function badgeLabel(tip) {
    return { fider: 'Fider', provodnik: 'Provodnik', potrosac: 'Potrošač' }[tip] || tip;
}

function loadClass(pct) {
    if (pct >= 80) return 'high';
    if (pct >= 50) return 'medium';
    return 'low';
}

function fmtTime(iso) {
    if (!iso) return '—';
    const d = new Date(iso);
    const pad = n => String(n).padStart(2, '0');
    return `${pad(d.getDate())}.${pad(d.getMonth()+1)}.${d.getFullYear()}  ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function tipIcon(tip) {
    if (tip === 'fider')    return '<svg viewBox="0 0 24 24"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>';
    if (tip === 'provodnik') return '<svg viewBox="0 0 24 24"><path d="M2 12h20M12 2v20" stroke-width="2" stroke="currentColor" fill="none"/></svg>';
    return '<svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>';
}


function render() {
    const items = getFiltered();
    const grid = document.getElementById('cardsGrid');
    const empty = document.getElementById('emptyState');

    document.getElementById('cardCount').textContent = items.length;

    if (items.length === 0) {
        grid.innerHTML = '';
        empty.style.display = 'flex';
        return;
    }
    empty.style.display = 'none';

    grid.innerHTML = items.map(item => {
        const pct = item.opterecenje_pct ?? 0;
        const cls = loadClass(pct);
        return `
        <div class="card" data-id="${item.id}" data-tip="${item.tip}">
            <span class="card-badge ${badgeClass(item.tip)}">${badgeLabel(item.tip)}</span>
            <div class="card-naziv">${item.naziv || '—'}</div>
            <div class="card-meta">
                <div class="meta-row">
                    <svg viewBox="0 0 24 24"><path d="M22 16.92v3a2 2 0 0 1-2.18 2A19.79 19.79 0 0 1 11.62 19a19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.9-8.2A2 2 0 0 1 3.68 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L7.91 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
                    ${item.telefon || '—'}
                </div>
                <div class="meta-row">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15 15"/></svg>
                    ${fmtTime(item.vreme_dolaska)}
                </div>
            </div>
            <div class="card-footer">
                <div class="load-bar-wrap">
                    <div class="load-label">Opterećenje</div>
                    <div class="load-bar-bg"><div class="load-bar-fill ${cls}" style="width:${pct}%"></div></div>
                </div>
                <div class="load-value">${pct}%</div>
            </div>
        </div>`;
    }).join('');

    grid.querySelectorAll('.card').forEach(card => {
        card.addEventListener('click', () => {
            const id = card.dataset.id;
            const tip = card.dataset.tip;
            const item = allItems.find(x => String(x.id) === id && x.tip === tip);
            if (item) openModal(item);
        });
    });
}

function renderSkeletons() {
    const grid = document.getElementById('cardsGrid');
    grid.innerHTML = Array.from({ length: 8 }, () => `
        <div class="skeleton-card">
            <div class="skeleton-line" style="width:35%;height:18px"></div>
            <div class="skeleton-line" style="width:75%"></div>
            <div class="skeleton-line" style="width:55%"></div>
            <div class="skeleton-line" style="width:60%"></div>
        </div>`).join('');
}


function statusDot(status) {
    const s = (status || '').toLowerCase();
    if (s.includes('alarm')) return '<span class="status-dot alarm"></span>';
    if (s.includes('upozorenje')) return '<span class="status-dot upozorenje"></span>';
    return '<span class="status-dot aktivan"></span>';
}

function openModal(item) {
    const pct = item.opterecenje_pct ?? 0;
    const cls = loadClass(pct);

    document.getElementById('modalTitle').textContent = item.naziv || '—';
    document.getElementById('modalSubtitle').textContent = `${badgeLabel(item.tip)} · ID: ${item.id_oznaka || item.id}`;

    let html = '';

    html += `
    <div class="modal-section">
        <div class="modal-section-title">Opšte informacije</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Status</div>
                <div class="info-value">${statusDot(item.status)}${item.status || 'Aktivan'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Vreme dolaska</div>
                <div class="info-value">${fmtTime(item.vreme_dolaska)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Telefon</div>
                <div class="info-value">${item.telefon || '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Tip</div>
                <div class="info-value">${badgeLabel(item.tip)}</div>
            </div>
        </div>
    </div>`;

    // Load section
    html += `
    <div class="modal-section">
        <div class="modal-section-title">Opterećenje</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Opterećenje (%)</div>
                <div class="info-value ${pct >= 80 ? 'red' : pct >= 50 ? 'accent' : 'green'}">${pct}%</div>
                <div class="modal-load-bar"><div class="modal-load-fill ${cls}" style="width:${pct}%"></div></div>
            </div>
            <div class="info-item">
                <div class="info-label">Snaga (kW)</div>
                <div class="info-value">${item.snaga_kw != null ? item.snaga_kw + ' kW' : '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Struja (A)</div>
                <div class="info-value">${item.struja_a != null ? item.struja_a + ' A' : '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Napon (V)</div>
                <div class="info-value">${item.napon_v != null ? item.napon_v : '—'}</div>
            </div>
        </div>
    </div>`;

    // Extra fields depending on type
    if (item.tip === 'fider' || item.tip === 'provodnik') {
        html += `
    <div class="modal-section">
        <div class="modal-section-title">Tehničke karakteristike</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Dužina (km)</div>
                <div class="info-value">${item.duzina_km != null ? item.duzina_km + ' km' : '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Tip provodnika</div>
                <div class="info-value">${item.tip_provodnika || '—'}</div>
            </div>
            <div class="info-item full">
                <div class="info-label">Zona / Lokacija</div>
                <div class="info-value">${item.zona || item.lokacija || '—'}</div>
            </div>
        </div>
    </div>`;
    }

    if (item.tip === 'potrosac') {
        html += `
    <div class="modal-section">
        <div class="modal-section-title">Podaci o potrošaču</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Broj brojila</div>
                <div class="info-value">${item.br_brojila || '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Fider</div>
                <div class="info-value">${item.fider || '—'}</div>
            </div>
            <div class="info-item full">
                <div class="info-label">Adresa</div>
                <div class="info-value">${item.adresa || '—'}</div>
            </div>
        </div>
    </div>`;
    }

    document.getElementById('modalBody').innerHTML = html;
    document.getElementById('modalOverlay').classList.add('open');
}

function closeModal() {
    document.getElementById('modalOverlay').classList.remove('open');
}

// ── Events ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    loadAll();

    document.getElementById('globalSearch').addEventListener('input', e => {
        searchQuery = e.target.value.trim();
        render();
    });

    document.getElementById('sortSelect').addEventListener('change', e => {
        sortMode = e.target.value;
        render();
    });

    document.querySelectorAll('.filter-tab').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-tab').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            activeTab = btn.dataset.tab;
            render();
        });
    });

    document.getElementById('modalClose').addEventListener('click', closeModal);
    document.getElementById('modalOverlay').addEventListener('click', e => {
        if (e.target === e.currentTarget) closeModal();
    });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
});
