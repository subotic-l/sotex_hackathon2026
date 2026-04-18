const API_BASE = 'http://localhost:5000';

let allItems = [];
let activeTab = 'sve';
let searchQuery = '';
let sortMode = 'najnoviji';

async function loadAll() {
    renderSkeletons();
    try {
        const data = await fetch(`${API_BASE}/api/notifikacije`).then(r => r.json());
        allItems = data;
        updateStats();
        render();
    } catch (e) {
        console.error('Greška:', e);
        document.getElementById('cardsGrid').innerHTML =
            '<p style="color:#c00;grid-column:1/-1;padding:20px">Greška pri učitavanju podataka</p>';
    }
}

function updateStats() {
    document.getElementById('cntAlarm').textContent   = allItems.filter(x => x.tip === 'alarm').length;
    document.getElementById('cntPromena').textContent = allItems.filter(x => x.tip === 'upozorenje').length;
    document.getElementById('cntGubitak').textContent = allItems.filter(x => x.tip === 'gubitak').length;
    document.getElementById('cntInfo').textContent    = allItems.filter(x => x.tip === 'info').length;
}

function getFiltered() {
    let items = allItems;
    if (activeTab !== 'sve') items = items.filter(i => i.tip === activeTab);
    if (searchQuery) {
        const q = searchQuery.toLowerCase();
        items = items.filter(i =>
            (i.naziv || '').toLowerCase().includes(q) ||
            (i.poruka || '').toLowerCase().includes(q) ||
            (i.feeder_naziv || '').toLowerCase().includes(q)
        );
    }
    return [...items].sort((a, b) => {
        switch (sortMode) {
            case 'najnoviji':     return new Date(b.vreme) - new Date(a.vreme);
            case 'najstariji':    return new Date(a.vreme) - new Date(b.vreme);
            case 'promena_desc':  return Math.abs(b.promena_pct || 0) - Math.abs(a.promena_pct || 0);
            case 'promena_asc':   return Math.abs(a.promena_pct || 0) - Math.abs(b.promena_pct || 0);
            default: return 0;
        }
    });
}

function badgeClass(tip) {
    return { alarm: 'badge-alarm', upozorenje: 'badge-upozorenje', gubitak: 'badge-gubitak', info: 'badge-info' }[tip] || '';
}
function badgeLabel(tip) {
    return { alarm: 'Alarm', upozorenje: 'Nagla promena', gubitak: 'Gubitak', info: 'Info' }[tip] || tip;
}

function fmtTime(iso) {
    if (!iso) return '—';
    const d = new Date(iso);
    const pad = n => String(n).padStart(2, '0');
    return `${pad(d.getDate())}.${pad(d.getMonth()+1)}.${d.getFullYear()}  ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function arrowDir(pct) {
    return pct >= 0 ? 'up' : 'down';
}

function render() {
    const items = getFiltered();
    const grid  = document.getElementById('cardsGrid');
    const empty = document.getElementById('emptyState');

    document.getElementById('cardCount').textContent = items.length;

    if (items.length === 0) {
        grid.innerHTML = '';
        empty.style.display = 'flex';
        return;
    }
    empty.style.display = 'none';

    grid.innerHTML = items.map(item => {
        const pct = item.promena_pct ?? 0;
        const dir = arrowDir(pct);
        const sign = pct >= 0 ? '+' : '';
        return `
        <div class="card ${item.tip}" data-id="${item.id}">
            <div class="card-top">
                <span class="card-badge ${badgeClass(item.tip)}">${badgeLabel(item.tip)}</span>
                <span class="card-time">${fmtTime(item.vreme)}</span>
            </div>
            <div class="card-naziv">${item.naziv}</div>
            <div class="card-poruka">${item.poruka}</div>
            <div class="card-change">
                <span class="change-arrow ${dir}">${dir === 'up' ? '↑' : '↓'}</span>
                <span class="change-vals">${item.vrednost_pre} → ${item.vrednost_posle} ${item.jedinica ?? ''}</span>
                <span class="change-pct ${item.tip === 'gubitak' ? 'loss' : dir}">${sign}${pct}%</span>
            </div>
        </div>`;
    }).join('');

    grid.querySelectorAll('.card').forEach(card => {
        card.addEventListener('click', () => {
            const item = allItems.find(x => String(x.id) === card.dataset.id);
            if (item) openModal(item);
        });
    });
}

function renderSkeletons() {
    document.getElementById('cardsGrid').innerHTML = Array.from({ length: 8 }, () => `
        <div class="skeleton-card">
            <div class="skeleton-line" style="width:30%;height:16px"></div>
            <div class="skeleton-line" style="width:70%"></div>
            <div class="skeleton-line" style="width:90%"></div>
            <div class="skeleton-line" style="width:50%"></div>
        </div>`).join('');
}

function openModal(item) {
    const pct = item.promena_pct ?? 0;
    const dir = arrowDir(pct);
    const sign = pct >= 0 ? '+' : '';

    // Header icon
    const iconEl = document.getElementById('modalIcon');
    iconEl.className = `modal-icon ${item.tip}`;

    document.getElementById('modalTitle').textContent = item.naziv;
    document.getElementById('modalSubtitle').textContent =
        `${badgeLabel(item.tip)} · ${fmtTime(item.vreme)}`;

    let html = '';

    // Promena blok
    html += `
    <div class="modal-section">
        <div class="modal-section-title">Promena vrednosti</div>
        <div class="change-block">
            <div>
                <div class="cb-label">Pre</div>
                <div class="cb-val">${item.vrednost_pre} ${item.jedinica ?? ''}</div>
            </div>
            <div class="cb-arrow">→</div>
            <div>
                <div class="cb-label">Posle</div>
                <div class="cb-val ${dir}">${item.vrednost_posle} ${item.jedinica ?? ''}</div>
            </div>
            <div style="margin-left:auto;text-align:right">
                <div class="cb-label">Promena</div>
                <div class="cb-val ${dir}">${sign}${pct}%</div>
            </div>
        </div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Vreme detekcije (Ts)</div>
                <div class="info-value">${fmtTime(item.vreme)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Tip notifikacije</div>
                <div class="info-value">${badgeLabel(item.tip)}</div>
            </div>
        </div>
    </div>`;

    // Izvor – MeterReadTfes / Meters
    html += `
    <div class="modal-section">
        <div class="modal-section-title">Izvor (MeterReadTfes · Meters)</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Br. brojila (MeterId / Mid)</div>
                <div class="info-value">${item.meter_id ?? '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Serijski broj (MSN)</div>
                <div class="info-value">${item.msn ?? '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Kanal (Channels.Name)</div>
                <div class="info-value">${item.kanal_naziv ?? '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Jedinica mere</div>
                <div class="info-value">${item.jedinica ?? '—'}</div>
            </div>
        </div>
    </div>`;

    // Mrežna lokacija – Feeder
    html += `
    <div class="modal-section">
        <div class="modal-section-title">Mrežna lokacija</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Naziv voda / podstanice</div>
                <div class="info-value">${item.feeder_naziv ?? '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Feeder33 ID</div>
                <div class="info-value">${item.feeder33_id ?? '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Feeder11 ID</div>
                <div class="info-value">${item.feeder11_id ?? '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Nominalna snaga</div>
                <div class="info-value">${item.nameplate_rating_kva != null ? item.nameplate_rating_kva + ' kVA' : '—'}</div>
            </div>
        </div>
    </div>`;

    // Poruka / opis
    html += `
    <div class="modal-section">
        <div class="modal-section-title">Opis</div>
        <div class="info-item full" style="background:#f8f8f8;border-radius:10px;padding:14px">
            <div class="info-label">Poruka</div>
            <div class="info-value" style="font-size:14px;font-weight:400;line-height:1.5;color:#333">${item.poruka}</div>
        </div>
    </div>`;

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
