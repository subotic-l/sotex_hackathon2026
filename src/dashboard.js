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

/**
 * Initialize dashboard - load all data on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    // Optional: Load map if needed
    // loadMapVisualization();

    // Optional: Set up auto-refresh (every 30 seconds)
    setInterval(loadDashboardData, 30000);
});
