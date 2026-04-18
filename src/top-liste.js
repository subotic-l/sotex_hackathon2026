const API_BASE = 'http://localhost:5000';

let allItems = [];
let activeTab = 'svi';
let searchQuery = '';
let sortMode = 'najnoviji';

function calcPct(item) {
    if (!item.nameplate_rating_kva || !item.ocitavanje_val) return 0;
    return Math.min(100, Math.round((item.ocitavanje_val / item.nameplate_rating_kva) * 100));
}

async function loadAll() {
    renderSkeletons();
    try {
        const [fideri, provodnici, potrosaci] = await Promise.all([
            fetch(`${API_BASE}/api/fideri`).then(r => r.json()),
            fetch(`${API_BASE}/api/provodnici`).then(r => r.json()),
            fetch(`${API_BASE}/api/potrosaci`).then(r => r.json()),
        ]);
        allItems = [
            ...fideri.map(x => ({ ...x, tip: 'fider',     opterecenje_pct: calcPct(x), vreme_dolaska: x.ocitavanje_ts })),
            ...provodnici.map(x => ({ ...x, tip: 'provodnik', opterecenje_pct: calcPct(x), vreme_dolaska: x.ocitavanje_ts })),
            ...potrosaci.map(x => ({ ...x, tip: 'potrosac',  opterecenje_pct: calcPct(x), vreme_dolaska: x.ocitavanje_ts })),
        ];
        render();
    } catch (e) {
        console.error('Greška pri učitavanju:', e);
        document.getElementById('cardsGrid').innerHTML =
            '<p style="color:#c00;grid-column:1/-1;padding:20px">Failed to load data</p>';
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
    return { fider: 'Feeder 33kV', provodnik: 'Feeder 11kV', potrosac: 'Substation' }[tip] || tip;
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
                    <svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="18" rx="2"/><path d="M8 10h8M8 14h5"/></svg>
                    Meter ID: ${item.meter_id ?? '—'}
                </div>
                <div class="meta-row">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15 15"/></svg>
                    ${fmtTime(item.ocitavanje_ts)}
                </div>
            </div>
            <div class="card-footer">
                <div class="load-bar-wrap">
                    <div class="load-label">Load</div>
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
    document.getElementById('modalSubtitle').textContent = `${badgeLabel(item.tip)} · ID: ${item.id}`;

    let html = '';

    html += `
    <div class="modal-section">
        <div class="modal-section-title">General</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Record ID</div>
                <div class="info-value">${item.id}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Meter No. (MeterId)</div>
                <div class="info-value">${item.meter_id ?? '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Nameplate Rating</div>
                <div class="info-value">${item.nameplate_rating_kva != null ? item.nameplate_rating_kva + ' kVA' : '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Type</div>
                <div class="info-value">${badgeLabel(item.tip)}</div>
            </div>
        </div>
    </div>`;

    html += `
    <div class="modal-section">
        <div class="modal-section-title">Meter (Meters)</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Serial No. (MSN)</div>
                <div class="info-value">${item.msn ?? '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Multiplier Factor</div>
                <div class="info-value">${item.multiplier_factor ?? '—'}</div>
            </div>
        </div>
    </div>`;

    html += `
    <div class="modal-section">
        <div class="modal-section-title">Last Reading (MeterReadTfes)</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Value (Val)</div>
                <div class="info-value ${pct >= 80 ? 'red' : pct >= 50 ? 'accent' : 'green'}">${item.ocitavanje_val ?? '—'} ${item.kanal_jedinica ?? ''}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Timestamp (Ts)</div>
                <div class="info-value">${fmtTime(item.ocitavanje_ts)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Channel (Channels.Name)</div>
                <div class="info-value">${item.kanal_naziv ?? '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Unit of Measure</div>
                <div class="info-value">${item.kanal_jedinica ?? '—'}</div>
            </div>
            <div class="info-item full">
                <div class="info-label">Load (Val / NameplateRating)</div>
                <div class="info-value">${pct}%</div>
                <div class="modal-load-bar"><div class="modal-load-fill ${cls}" style="width:${pct}%"></div></div>
            </div>
        </div>
    </div>`;

    if (item.tip === 'fider') {
        html += `
    <div class="modal-section">
        <div class="modal-section-title">Feeders33 – High Voltage Line</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Transmission Station (TsId)</div>
                <div class="info-value">${item.ts_id ?? '—'}</div>
            </div>
        </div>
    </div>`;
    }

    if (item.tip === 'provodnik') {
        html += `
    <div class="modal-section">
        <div class="modal-section-title">Feeders11 – Medium Voltage Line</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Substation (SsId)</div>
                <div class="info-value">${item.ss_id ?? '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">HV Feeder (Feeder33Id)</div>
                <div class="info-value">${item.feeder33_id ?? '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Transmission Station (TsId)</div>
                <div class="info-value">${item.ts_id ?? '—'}</div>
            </div>
        </div>
    </div>`;
    }

    if (item.tip === 'potrosac') {
        html += `
    <div class="modal-section">
        <div class="modal-section-title">Dt – Low Voltage Substation</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">MV Feeder (Feeder11Id)</div>
                <div class="info-value">${item.feeder11_id ?? '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">HV Feeder (Feeder33Id)</div>
                <div class="info-value">${item.feeder33_id ?? '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Latitude</div>
                <div class="info-value">${item.latitude ?? '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Longitude</div>
                <div class="info-value">${item.longitude ?? '—'}</div>
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
