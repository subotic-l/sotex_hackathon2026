/**
 * Dashboard API endpoints and data loading logic
 * Connects to server.py endpoints
 */

const API_BASE_URL = '';

/**
 * Endpoint: /api/dashboard-data
 * Fetches dashboard metrics: active meters, down meters, network effectiveness
 */
async function getDashboardData() {
    try {
        const d = new Date();
        d.setDate(d.getDate() - 5);
        const dateStr = d.toISOString().slice(0, 10);
        const response = await fetch(`${API_BASE_URL}/api/dashboard-data?date=${dateStr}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
        throw error;
    }
}

/**
 * Endpoint: /map
 * Fetches the map visualization (HTML)
 */
async function getMapVisualization() {
    try {
        const response = await fetch(`${API_BASE_URL}/map`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return await response.text();
    } catch (error) {
        console.error('Error fetching map:', error);
        throw error;
    }
}

/**
 * Updates the dashboard with fetched data
 * @param {Object} data - Dashboard data object
 */
function updateDashboardMetrics(data) {
    const activeEl = document.getElementById('numActiveMeters');
    const downEl = document.getElementById('numDownMeters');
    const genderPieEl = document.getElementById('genderPie');
    const genderPercentageEl = document.getElementById('genderPercentage');

    // Update active meters
    if (activeEl) {
        activeEl.textContent = Number(data.NumActiveMeters ?? 0).toLocaleString();
        activeEl.classList.remove('error');
    }

    // Update down meters
    if (downEl) {
        downEl.textContent = Number(data.NumDownMeters ?? 0).toLocaleString();
        downEl.classList.remove('error');
    }

    // Update gender pie chart with effectiveness percentage
    const effectiveness = Number(data.NetworkEffectivnessPercentage ?? 0) * 100;
    if (genderPercentageEl) {
        genderPercentageEl.textContent = effectiveness.toFixed(1) + '%';
    }

    if (genderPieEl) {
        const clamped = Math.max(0, Math.min(100, effectiveness));
        const degrees = (clamped / 100) * 360;
        const gap = 3;
        const g1 = Math.max(gap, degrees - gap);
        const g2 = Math.min(360 - gap, degrees + gap);
        genderPieEl.style.background =
            `conic-gradient(transparent 0deg, transparent ${gap}deg, #f2c94c ${gap}deg, #f2c94c ${g1}deg, transparent ${g1}deg, transparent ${g2}deg, #555 ${g2}deg, #555 ${360 - gap}deg, transparent ${360 - gap}deg)`;
    }
}

/**
 * Handles error state in dashboard
 * @param {string} message - Error message to display
 */
function setDashboardError(message = 'Nije uspelo ucitavanje podataka') {
    const activeEl = document.getElementById('numActiveMeters');
    const downEl = document.getElementById('numDownMeters');
    const genderPieEl = document.getElementById('genderPie');
    const genderPercentageEl = document.getElementById('genderPercentage');

    if (activeEl) {
        activeEl.textContent = message;
        activeEl.classList.add('error');
    }

    if (downEl) {
        downEl.textContent = message;
        downEl.classList.add('error');
    }

    if (genderPercentageEl) {
        genderPercentageEl.textContent = '-';
    }

    if (genderPieEl) {
        genderPieEl.style.background = 'conic-gradient(#555 0deg, #555 360deg)';
    }
}

/**
 * Loads dashboard data and updates the UI
 */
async function loadDashboardData() {
    try {
        const data = await getDashboardData();
        updateDashboardMetrics(data);
    } catch (error) {
        console.error('Failed to load dashboard data:', error);
        setDashboardError();
    }
}

/**
 * Loads map visualization and inserts into the page
 * @param {string} targetSelector - CSS selector for container
 */
async function loadMapVisualization(targetSelector = '.card-map .placeholder') {
    try {
        const mapHTML = await getMapVisualization();
        const container = document.querySelector(targetSelector);
        if (container) {
            container.innerHTML = mapHTML;
        }
    } catch (error) {
        console.error('Failed to load map visualization:', error);
        const container = document.querySelector(targetSelector);
        if (container) {
            container.innerHTML = '<p style="color: #999;">Map not available</p>';
        }
    }
}

let lossChartInstance = null;

async function getLossGraphData() {
    const response = await fetch(`${API_BASE_URL}/api/loss_graph`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
}

function makeStripePattern(color) {
    const size = 10;
    const patCanvas = document.createElement('canvas');
    patCanvas.width = size;
    patCanvas.height = size;
    const ctx = patCanvas.getContext('2d');
    ctx.fillStyle = color;
    ctx.fillRect(0, 0, size, size);
    ctx.strokeStyle = 'rgba(255,255,255,0.35)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(0, size);
    ctx.lineTo(size, 0);
    ctx.stroke();
    return patCanvas;
}

function renderLossChart(loss11, loss33) {
    const canvas = document.getElementById('lossChart');
    if (!canvas) return;

    const container = canvas.parentElement;
    container.style.position = 'relative';
    let legend = container.querySelector('.loss-legend-overlay');
    if (!legend) {
        legend = document.createElement('div');
        legend.className = 'loss-legend-overlay';
        legend.style.cssText = [
            'position:absolute',
            'top:10px',
            'right:12px',
            'display:flex',
            'flex-direction:column',
            'gap:5px',
            'pointer-events:none',
            'z-index:10',
            'background:rgba(40,40,40,0.75)',
            'border-radius:6px',
            'padding:6px 10px',
        ].join(';');
        container.appendChild(legend);
    }
    legend.innerHTML = `
        <div style="display:flex;align-items:center;gap:6px;">
            <div style="width:10px;height:10px;background:#f2c94c;border-radius:2px;flex-shrink:0;"></div>
            <span style="color:#ccc;font-size:10px;font-family:Montserrat,sans-serif;">Loss Feeders33</span>
        </div>
        <div style="display:flex;align-items:center;gap:6px;">
            <div style="width:10px;height:10px;background:rgba(180,180,180,0.5);border-radius:2px;flex-shrink:0;"></div>
            <span style="color:#ccc;font-size:10px;font-family:Montserrat,sans-serif;">Loss Feeders11</span>
        </div>
        <div style="display:flex;align-items:center;gap:6px;">
            <div style="width:10px;height:3px;background:rgba(139,28,28,0.6);flex-shrink:0;"></div>
            <span style="color:#ccc;font-size:10px;font-family:Montserrat,sans-serif;">Acceptable loss</span>
        </div>
    `;

    const ctx = canvas.getContext('2d');
    const stripePattern = ctx.createPattern(makeStripePattern('#f2c94c'), 'repeat');

    if (lossChartInstance) lossChartInstance.destroy();

    const refLinePlugin = {
        id: 'refLine',
        afterDraw(chart) {
            const { ctx, chartArea: { left, right }, scales: { y } } = chart;
            const yPos = y.getPixelForValue(10);
            ctx.save();
            ctx.beginPath();
            ctx.moveTo(left, yPos);
            ctx.lineTo(right, yPos);
            ctx.strokeStyle = 'rgba(139, 28, 28, 0.6)';
            ctx.lineWidth = 3;
            ctx.setLineDash([]);
            ctx.stroke();
            ctx.restore();
        }
    };

    lossChartInstance = new Chart(ctx, {
        type: 'bar',
        plugins: [refLinePlugin],
        data: {
            labels: [''],
            datasets: [
                {
                    data: [loss33],
                    backgroundColor: stripePattern,
                    borderColor: '#f2c94c',
                    borderWidth: 1,
                    borderRadius: 3,
                    barPercentage: 0.35,
                    categoryPercentage: 0.5,
                },
                {
                    data: [loss11],
                    backgroundColor: 'rgba(180,180,180,0.35)',
                    borderColor: 'rgba(180,180,180,0.5)',
                    borderWidth: 1,
                    borderRadius: 3,
                    barPercentage: 0.35,
                    categoryPercentage: 0.5,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => ` ${ctx.parsed.y.toFixed(2)}%`
                    },
                    backgroundColor: '#c8b8f0',
                    titleColor: '#1a1a1a',
                    bodyColor: '#1a1a1a',
                    displayColors: false,
                    padding: 8,
                    cornerRadius: 6,
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { display: false },
                    border: { display: false },
                },
                y: {
                    min: 0,
                    max: 100,
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#aaa', font: { size: 11 }, stepSize: 20 },
                    border: { display: false },
                }
            }
        }
    });
}

async function loadLossGraph() {
    try {
        const data = await getLossGraphData();
        renderLossChart(data.feeder11_avg_loss_pct, data.feeder33_avg_loss_pct);
    } catch (error) {
        console.error('Failed to load loss graph:', error);
    }
}

async function loadLossTotal() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/loss_total`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        const el = document.getElementById('lossTotalValue');
        if (el) el.textContent = Number(data.total_avg_loss_pct ?? 0).toFixed(2);
    } catch (error) {
        console.error('Failed to load loss total:', error);
    }
}

/**
 * Initialize dashboard - load all data on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    loadLossGraph();
    loadLossTotal();

    setInterval(loadDashboardData, 30000);
    setInterval(loadLossGraph, 30000);
    setInterval(loadLossTotal, 30000);
});
