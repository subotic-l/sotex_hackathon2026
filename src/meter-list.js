const API_BASE = '';

let allItems = [];
let searchQuery = '';
let sortMode = 'naziv_az';
let statusFilter = '';
let currentPage = 1;
let totalPages = 1;
let totalItems = 0;
const PAGE_SIZE = 24;

function getStatusMeta(status) {
    if (status === 'Up') {
        return { label: 'Up', className: 'badge-status-up' };
    }
    if (status === 'Recently Down' || status === 'Down recently') {
        return { label: 'Recently Down', className: 'badge-status-recent' };
    }
    if (status === 'Down') {
        return { label: 'Down', className: 'badge-status-down' };
    }
    return { label: 'Unknown', className: 'badge-status-unknown' };
}

async function fetchMeterPage() {
    const params = new URLSearchParams({
        page: String(currentPage),
        pageSize: String(PAGE_SIZE),
        q: searchQuery,
        sort: sortMode,
        status: statusFilter,
    });

    const response = await fetch(`${API_BASE}/api/meter-list?${params.toString()}`);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
}

function fmtTime(iso) {
    if (!iso) return '-';
    const d = new Date(iso);
    const pad = (n) => String(n).padStart(2, '0');
    return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.${d.getFullYear()}  ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function fmtDate(iso) {
    if (!iso) return '-';
    const d = new Date(iso);
    const pad = (n) => String(n).padStart(2, '0');
    return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.${d.getFullYear()}`;
}

function updatePaginationUi() {
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    const pageInfo = document.getElementById('pageInfo');

    if (prevBtn) prevBtn.disabled = currentPage <= 1;
    if (nextBtn) nextBtn.disabled = currentPage >= totalPages;
    if (pageInfo) pageInfo.textContent = `Page ${currentPage} / ${totalPages}`;
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

function render() {
    const grid = document.getElementById('cardsGrid');
    const empty = document.getElementById('emptyState');
    document.getElementById('cardCount').textContent = totalItems;
    updatePaginationUi();

    if (allItems.length === 0) {
        grid.innerHTML = '';
        empty.style.display = 'flex';
        return;
    }
    empty.style.display = 'none';

    grid.innerHTML = allItems.map((item) => {
        const readingValue = item.ocitavanje_val != null ? `${item.ocitavanje_val}` : '-';
        const status = getStatusMeta(item.status);
        return `
        <div class="card" data-id="${item.id}">
            <div class="card-badges">
                <span class="card-badge ${status.className}">${status.label}</span>
            </div>
            <div class="card-naziv">${item.naziv || '-'} </div>
            <div class="card-id">ID: ${item.id}</div>
            <div class="card-meta">
                <div class="meta-row">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15 15"/></svg>
                    Last reading: ${fmtTime(item.ocitavanje_ts)}
                </div>
            </div>
        </div>`;
    }).join('');

    grid.querySelectorAll('.card').forEach((card) => {
        card.addEventListener('click', () => {
            const id = card.dataset.id;
            const item = allItems.find((x) => String(x.id) === id);
            if (!item) return;

            document.getElementById('modalTitle').textContent = item.naziv || '-';
            document.getElementById('modalSubtitle').textContent = `Meter · ID: ${item.id}`;
            document.getElementById('modalBody').innerHTML = `
                <div class="info-item">
                    <div class="info-label">Details endpoint</div>
                    <div class="info-value">Pending implementation for individual meter details.</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Status</div>
                    <div class="info-value">${item.status || 'Unknown'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Status reason</div>
                    <div class="info-value">${item.status_reason || '-'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Meter ID</div>
                    <div class="info-value">${item.meter_id ?? '-'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">MSN</div>
                    <div class="info-value">${item.msn ?? '-'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Multiplier Factor</div>
                    <div class="info-value">${item.multiplier_factor ?? '-'}</div>
                </div>
            `;
            document.getElementById('modalOverlay').classList.add('open');
        });
    });
}

async function loadCurrentPage() {
    renderSkeletons();
    try {
        const payload = await fetchMeterPage();
        totalPages = Math.max(Number(payload.totalPages || 1), 1);
        totalItems = Number(payload.totalItems || 0);
        currentPage = Math.min(Math.max(Number(payload.page || currentPage), 1), totalPages);

        const subtitle = document.querySelector('.page-subtitle');
        if (subtitle) {
            subtitle.textContent = payload.snapshotDate ? `Snapshot: ${fmtDate(payload.snapshotDate)}` : 'All Meters';
        }

        allItems = payload.items || [];
        render();
    } catch (error) {
        console.error('Load meter-list failed:', error);
        document.getElementById('cardsGrid').innerHTML =
            '<p style="color:#c00;grid-column:1/-1;padding:20px">Failed to load meter list</p>';
    }
}

function closeModal() {
    document.getElementById('modalOverlay').classList.remove('open');
}

document.addEventListener('DOMContentLoaded', () => {
    loadCurrentPage();

    document.querySelectorAll('.filter-tab').forEach((tab) => {
        tab.addEventListener('click', () => {
            const nextFilter = tab.dataset.status || '';
            if (nextFilter === statusFilter) return;

            statusFilter = nextFilter;
            currentPage = 1;

            document.querySelectorAll('.filter-tab').forEach((btn) => btn.classList.remove('active'));
            tab.classList.add('active');

            loadCurrentPage();
        });
    });

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
