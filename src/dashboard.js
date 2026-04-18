/**
 * Dashboard API endpoints and data loading logic
 * Connects to server.py endpoints
 */

const API_BASE_URL = 'http://localhost:5000';

/**
 * Endpoint: /api/dashboard-data
 * Fetches dashboard metrics: active meters, down meters, network effectiveness
 */
async function getDashboardData() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard-data`);
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
    const effectivenessEl = document.getElementById('networkEffectivnessPercentage');
    const pieEl = document.getElementById('networkEffectivenessPie');

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

    // Update network effectiveness percentage and pie chart
    const effectiveness = Number(data.NetworkEffectivnessPercentage ?? 0) * 100;
    if (effectivenessEl) {
        effectivenessEl.textContent = effectiveness.toFixed(1) + '%';
        effectivenessEl.classList.remove('error');
    }

    if (pieEl) {
        const clamped = Math.max(0, Math.min(100, effectiveness));
        const degrees = (clamped / 100) * 360;
        pieEl.style.background =
            `conic-gradient(#2f7d32 0deg, #2f7d32 ${degrees}deg, #e8e8e8 ${degrees}deg, #e8e8e8 360deg)`;
    }
}

/**
 * Handles error state in dashboard
 * @param {string} message - Error message to display
 */
function setDashboardError(message = 'Nije uspelo ucitavanje podataka') {
    const activeEl = document.getElementById('numActiveMeters');
    const downEl = document.getElementById('numDownMeters');
    const effectivenessEl = document.getElementById('networkEffectivnessPercentage');
    const pieEl = document.getElementById('networkEffectivenessPie');

    if (activeEl) {
        activeEl.textContent = message;
        activeEl.classList.add('error');
    }

    if (downEl) {
        downEl.textContent = message;
        downEl.classList.add('error');
    }

    if (effectivenessEl) {
        effectivenessEl.textContent = message;
        effectivenessEl.classList.add('error');
    }

    if (pieEl) {
        pieEl.style.background = 'conic-gradient(#e8e8e8 0deg, #e8e8e8 360deg)';
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
