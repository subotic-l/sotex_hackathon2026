const API_BASE = '';

const ENDPOINT_BY_TAB = {
    fideri: '/api/fideri',
    provodnici: '/api/provodnici',
};

const DETAIL_ENDPOINT_BY_TIP = {
    fider: (id) => `/api/fideri/${id}/details`,
    provodnik: (id) => `/api/provodnici/${id}/details`,
};

let allItems = [];
let activeTab = 'fideri';
let searchQuery = '';
let sortMode = 'naziv_az';
let currentPage = 1;
let totalPages = 1;
let totalItems = 0;
const PAGE_SIZE = 24;

async function fetchCategoryPage() {
    const endpoint = ENDPOINT_BY_TAB[activeTab];
    if (!endpoint) {
        return { items: [], totalPages: 1, totalItems: 0, page: 1 };
    }

    const params = new URLSearchParams({
        page: String(currentPage),
        pageSize: String(PAGE_SIZE),
        q: searchQuery,
        sort: sortMode,
    });

    const response = await fetch(`${API_BASE}${endpoint}?${params.toString()}`);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
}

async function loadCurrentPage() {
    renderSkeletons();
    try {
        const payload = await fetchCategoryPage();
        totalPages = Math.max(Number(payload.totalPages || 1), 1);
        totalItems = Number(payload.totalItems || 0);
        currentPage = Math.min(Math.max(Number(payload.page || currentPage), 1), totalPages);

        allItems = (payload.items || []).map((x) => ({
            ...x,
            opterecenje_pct: x.opterecenje_pct ?? 0,
            vreme_dolaska: x.ocitavanje_ts,
        }));

        render();
    } catch (e) {
        console.error('Greška pri učitavanju:', e);
        document.getElementById('cardsGrid').innerHTML =
            '<p style="color:#c00;grid-column:1/-1;padding:20px">Failed to load data</p>';
    }
}

function badgeClass(tip) {
    return { fider: 'badge-fider', provodnik: 'badge-provodnik', potrosac: 'badge-potrosac' }[tip] || '';
}

function badgeLabel(tip) {
    return { fider: 'Feeder 33kV', provodnik: 'Feeder 11kV' }[tip] || tip;
}

function loadClass(pct) {
    if (pct >= 20) return 'high';
    if (pct >= 10) return 'medium';
    return 'low';
}

function fmtTime(iso) {
    if (!iso) return '—';
    const d = new Date(iso);
    const pad = (n) => String(n).padStart(2, '0');
    return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.${d.getFullYear()}  ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function updatePaginationUi() {
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    const pageInfo = document.getElementById('pageInfo');

    if (prevBtn) prevBtn.disabled = currentPage <= 1;
    if (nextBtn) nextBtn.disabled = currentPage >= totalPages;
    if (pageInfo) pageInfo.textContent = `Page ${currentPage} / ${totalPages}`;
}

function render() {
    const items = allItems;
    const grid = document.getElementById('cardsGrid');
    const empty = document.getElementById('emptyState');

    document.getElementById('cardCount').textContent = totalItems;
    updatePaginationUi();

    if (items.length === 0) {
        grid.innerHTML = '';
        empty.style.display = 'flex';
        return;
    }
    empty.style.display = 'none';

    grid.innerHTML = items.map((item) => {
        const pct = item.opterecenje_pct ?? 0;
        const cls = loadClass(pct);
        const readingValue = item.ocitavanje_val != null ? `${item.ocitavanje_val}` : '—';
        const tsLabel = item.ts_id != null
            ? `Ts: ${item.ts_id}${item.ts_name ? ` · ${item.ts_name}` : ''}`
            : '';
        const meterLine = item.meter_id != null
            ? `<div class="meta-row"><svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="18" rx="2"/><path d="M8 10h8M8 14h5"/></svg>Meter ID: ${item.meter_id}</div>`
            : '';
        const tsLine = tsLabel
            ? `<div class="meta-row"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg>${tsLabel}</div>`
            : '';
        return `
        <div class="card" data-id="${item.id}" data-tip="${item.tip}">
            <span class="card-badge ${badgeClass(item.tip)}">${badgeLabel(item.tip)}</span>
            <div class="card-naziv">${item.naziv || '—'}</div>
            <div class="card-id">ID: ${item.id}</div>
            <div class="card-meta">
                ${meterLine}
                <div class="meta-row">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15 15"/></svg>
                    Last reading: ${fmtTime(item.ocitavanje_ts)}
                </div>
                ${tsLine}
            </div>
            <div class="card-footer">
                <div class="load-bar-wrap">
                    <div class="load-label">Loss</div>
                    <div class="load-bar-bg"><div class="load-bar-fill ${cls}" style="width:${pct}%"></div></div>
                </div>
                <div class="load-value">${pct != null ? pct.toFixed(2) : '—'}%</div>
            </div>
        </div>`;
    }).join('');

    grid.querySelectorAll('.card').forEach((card) => {
        card.addEventListener('click', async () => {
            const id = card.dataset.id;
            const tip = card.dataset.tip;
            const summaryItem = allItems.find((x) => String(x.id) === id && x.tip === tip);
            const detailUrlFactory = DETAIL_ENDPOINT_BY_TIP[tip];

            if (!detailUrlFactory) {
                if (summaryItem) openModal(summaryItem);
                return;
            }

            try {
                const response = await fetch(`${API_BASE}${detailUrlFactory(id)}`);
                if (!response.ok) {
                    if (summaryItem) openModal(summaryItem);
                    return;
                }

                const details = await response.json();
                const item = {
                    ...(summaryItem || {}),
                    id: details.Id,
                    naziv: details.Name,
                    meter_id: details.MeterId,
                    nameplate_rating_kva: details.NameplateRating,
                    msn: details.MSN,
                    multiplier_factor: details.MultiplierFactor,
                    ocitavanje_val: details.LastVal,
                    ocitavanje_ts: details.LastTs,
                    opterecenje_pct: details.LossPercentage != null ? Math.round(details.LossPercentage) : (summaryItem?.opterecenje_pct ?? 0),
                    tip,
                    kanal_naziv: details.ChannelName,
                    kanal_jedinica: details.Unit,
                    feeder11_id: details.Feeder11Id,
                    feeder33_id: details.Feeder33Id,
                    ss_id: details.SsId,
                    ts_id: details.TsId,
                    ts_name: details.TsName,
                    latitude: details.Latitude,
                    longitude: details.Longitude,
                };

                openModal(item);
            } catch (error) {
                console.error('Failed to load details:', error);
                if (summaryItem) openModal(summaryItem);
            }
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
                <div class="info-value">${item.nameplate_rating_kva != null ? `${item.nameplate_rating_kva} kVA` : '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Type</div>
                <div class="info-value">${badgeLabel(item.tip)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Loss</div>
                <div class="info-value">${pct != null ? pct.toFixed(2) : '—'}%</div>
            </div>
        </div>
    </div>`;

    html += `
    <div class="modal-section">
        <div class="modal-section-title">Operational Summary</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Last reading</div>
                <div class="info-value">${fmtTime(item.ocitavanje_ts)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Reading value</div>
                <div class="info-value">${item.ocitavanje_val ?? '—'}</div>
            </div>
            <div class="info-item full">
                <div class="info-label">Loss</div>
                <div class="info-value ${pct >= 20 ? 'red' : pct >= 10 ? 'accent' : 'green'}">${pct != null ? pct.toFixed(2) : '—'}%</div>
                <div class="modal-load-bar"><div class="modal-load-fill ${cls}" style="width:${pct}%"></div></div>
            </div>
        </div>
    </div>`;

    if (item.tip === 'fider') {
        html += `
    <div class="modal-section">
        <div class="modal-section-title">Feeders33 Details</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">MSN</div>
                <div class="info-value">${item.msn ?? '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Multiplier Factor</div>
                <div class="info-value">${item.multiplier_factor ?? '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Transmission Station Id</div>
                <div class="info-value">${item.ts_id ?? '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Transmission Station Name</div>
                <div class="info-value">${item.ts_name ?? '—'}</div>
            </div>
        </div>
    </div>`;
    }

    if (item.tip === 'provodnik') {
        html += `
    <div class="modal-section">
        <div class="modal-section-title">Feeders11 Details</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">MSN</div>
                <div class="info-value">${item.msn ?? '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Multiplier Factor</div>
                <div class="info-value">${item.multiplier_factor ?? '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Substation Id</div>
                <div class="info-value">${item.ss_id ?? '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">HV Feeder (Feeder33Id)</div>
                <div class="info-value">${item.feeder33_id ?? '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Transmission Station Id</div>
                <div class="info-value">${item.ts_id ?? '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Transmission Station Name</div>
                <div class="info-value">${item.ts_name ?? '—'}</div>
            </div>
        </div>
    </div>`;
    }

    if (item.tip === 'potrosac') {
        html += `
    <div class="modal-section">
        <div class="modal-section-title">Substation Details</div>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">MSN</div>
                <div class="info-value">${item.msn ?? '—'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Multiplier Factor</div>
                <div class="info-value">${item.multiplier_factor ?? '—'}</div>
            </div>
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
    loadCurrentPage();

    document.getElementById('globalSearch').addEventListener('input', (e) => {
        searchQuery = e.target.value.trim();
        currentPage = 1;
        loadCurrentPage();
    });

    document.getElementById('sortSelect').addEventListener('change', (e) => {
        sortMode = e.target.value;
        currentPage = 1;
        loadCurrentPage();
    });

    document.querySelectorAll('.filter-tab').forEach((btn) => {
        btn.addEventListener('click', async () => {
            document.querySelectorAll('.filter-tab').forEach((b) => b.classList.remove('active'));
            btn.classList.add('active');
            activeTab = btn.dataset.tab;
            currentPage = 1;
            await loadCurrentPage();
        });
    });

    document.getElementById('prevPageBtn').addEventListener('click', async () => {
        if (currentPage > 1) {
            currentPage -= 1;
            await loadCurrentPage();
        }
    });

    document.getElementById('nextPageBtn').addEventListener('click', async () => {
        if (currentPage < totalPages) {
            currentPage += 1;
            await loadCurrentPage();
        }
    });

    document.getElementById('modalClose').addEventListener('click', closeModal);
    document.getElementById('modalOverlay').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) closeModal();
    });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });
});
