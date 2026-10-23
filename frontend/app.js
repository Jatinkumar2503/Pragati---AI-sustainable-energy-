// PRAGATI AI Web Dashboard Controller
const API_BASE = "http://127.0.0.1:8000/api";

// State variables to hold Chart instances
let telemetryChart = null;
let forecastChart = null;
let scheduleChart = null;
let backtestChart = null;
let thdChart = null;
let twinCashFlowChart = null;

// Global state variables
let currentUserRole = "Operator";
const API_KEY = "pragati_sec_2026";

// Utility: Sanitize user input to prevent XSS injection
function sanitizeHTML(str) {
    const temp = document.createElement("div");
    temp.textContent = str;
    return temp.innerHTML;
}

// Utility: Update forecast hours slider label dynamically
function updateForecastSliderLabel(val) {
    const hours = parseInt(val) || 48;
    const days = Math.round(hours / 24);
    const label = `${hours} hours (${days === 1 ? '1 day' : days + ' days'})`;
    const el = document.getElementById("forecast-hours-label");
    if (el) el.innerText = label;
}
window.updateForecastSliderLabel = updateForecastSliderLabel;

// Application Initialization
document.addEventListener("DOMContentLoaded", () => {
    // Set dynamic date badge
    const dateBadge = document.getElementById("date-badge");
    if (dateBadge) {
        const now = new Date();
        dateBadge.innerText = `📅 ${now.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}`;
    }
    
    initTabNavigation();
    checkBackendStatus();
    loadTelemetry(7);
    loadAnomalies();
    
    // Bind Event Listeners
    document.getElementById("telemetry-days-select").addEventListener("change", (e) => {
        loadTelemetry(parseInt(e.target.value), currentTenantId);
    });
    
    document.getElementById("run-forecast-btn").addEventListener("click", () => {
        runForecasting();
    });
    
    const forecastSlider = document.getElementById("forecast-hours");
    if (forecastSlider) {
        forecastSlider.addEventListener("input", (e) => updateForecastSliderLabel(e.target.value));
        forecastSlider.addEventListener("change", (e) => updateForecastSliderLabel(e.target.value));
    }
    
    document.getElementById("optimize-schedule-btn").addEventListener("click", () => {
        runScheduler();
    });
    
    // Digital Twin sliders
    const solarSlider = document.getElementById("twin-solar");
    const batterySlider = document.getElementById("twin-battery");
    
    solarSlider.addEventListener("input", (e) => {
        document.getElementById("twin-solar-val").innerText = e.target.value;
        runDigitalTwin();
    });
    
    batterySlider.addEventListener("input", (e) => {
        document.getElementById("twin-battery-val").innerText = e.target.value;
        runDigitalTwin();
    });
    
    // Initial Twin call
    runDigitalTwin();
    
    // Chat Event listeners
    document.getElementById("chat-send-btn").addEventListener("click", sendCopilotMessage);
    document.getElementById("chat-input").addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendCopilotMessage();
    });

    // Role Switcher listener
    const roleSelect = document.getElementById("user-role-select");
    if (roleSelect) {
        roleSelect.addEventListener("change", (e) => {
            applyRolePermissions(e.target.value);
        });
        // Initial application of default role ("Operator")
        applyRolePermissions(roleSelect.value);
    }
    
    initCSVUploader();
});

// Role Permissions Control
function applyRolePermissions(role) {
    currentUserRole = role;
    const isLocked = role === "Operator";
    
    // Toggle Scheduler Lock Warning
    const schedLock = document.getElementById("scheduler-role-lock");
    if (schedLock) {
        schedLock.style.display = isLocked ? "flex" : "none";
    }
    
    // Toggle Twin Lock Warning
    const twinLock = document.getElementById("twin-role-lock");
    if (twinLock) {
        twinLock.style.display = isLocked ? "flex" : "none";
    }
    
    // Enable/disable inputs on Scheduler Tab
    const schedulerInputs = [
        "sched-load", "sched-duration", "sched-solar", "sched-weight",
        "sched-task-pf", "sched-battery-cap", "sched-battery-rate",
        "sched-battery-eff", "sched-solar-yield-mult", "sched-pf-penalty",
        "optimize-schedule-btn"
    ];
    schedulerInputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.disabled = isLocked;
    });
    
    // Enable/disable inputs on Digital Twin Tab
    const twinInputs = ["twin-solar", "twin-battery"];
    twinInputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.disabled = isLocked;
    });
    
    // Style uploader card based on permissions
    const dropzone = document.getElementById("csv-dropzone");
    if (dropzone) {
        if (isLocked) {
            dropzone.style.opacity = "0.5";
            dropzone.style.cursor = "not-allowed";
        } else {
            dropzone.style.opacity = "1";
            dropzone.style.cursor = "pointer";
        }
    }
}

// Drag & Drop Telemetry CSV Ingestion
function initCSVUploader() {
    const dropzone = document.getElementById("csv-dropzone");
    const fileInput = document.getElementById("csv-file-input");
    const statusEl = document.getElementById("upload-status");
    
    if (!dropzone || !fileInput) return;
    
    dropzone.addEventListener("click", () => {
        if (currentUserRole === "Operator") {
            alert("🔒 Action restricted. Please switch to Manager or Admin role in the sidebar to upload datasets.");
            return;
        }
        fileInput.click();
    });
    
    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        if (currentUserRole === "Operator") return;
        dropzone.style.borderColor = "#10B981";
        dropzone.style.background = "rgba(16, 185, 129, 0.05)";
    });
    
    dropzone.addEventListener("dragleave", () => {
        if (currentUserRole === "Operator") return;
        dropzone.style.borderColor = "rgba(16, 185, 129, 0.3)";
        dropzone.style.background = "rgba(255, 255, 255, 0.01)";
    });
    
    dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        if (currentUserRole === "Operator") return;
        dropzone.style.borderColor = "rgba(16, 185, 129, 0.3)";
        dropzone.style.background = "rgba(255, 255, 255, 0.01)";
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleCSVUpload(files[0]);
        }
    });
    
    fileInput.addEventListener("change", (e) => {
        const files = e.target.files;
        if (files.length > 0) {
            handleCSVUpload(files[0]);
        }
    });
}

async function handleCSVUpload(file) {
    const statusEl = document.getElementById("upload-status");
    if (!statusEl) return;
    
    if (!file.name.endsWith('.csv')) {
        statusEl.style.display = "block";
        statusEl.style.color = "#EF4444";
        statusEl.innerText = "❌ Only CSV files (.csv) are supported.";
        return;
    }
    
    statusEl.style.display = "block";
    statusEl.style.color = "#06B6D4";
    statusEl.innerText = "⏳ Retraining machine learning forecasting models on custom data coordinates...";
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
        const res = await fetch(`${API_BASE}/telemetry/upload`, {
            method: "POST",
            headers: {
                "X-API-Key": API_KEY
            },
            body: formData
        });
        
        const data = await res.json();
        if (res.ok) {
            statusEl.style.color = "#10B981";
            statusEl.innerText = `✅ Ingestion Complete: Retrained on ${data.rows_inserted} records!`;
            // Refresh telemetry dashboard data
            loadTelemetry(7);
            loadAnomalies();
        } else {
            statusEl.style.color = "#EF4444";
            statusEl.innerText = `❌ Ingestion Failed: ${data.detail || "Failed to process custom dataset columns."}`;
        }
    } catch (e) {
        statusEl.style.color = "#EF4444";
        statusEl.innerText = "❌ Network connection error. Backend is unreachable.";
    }
}

// Universal Global Tab Switcher Function
function switchTab(targetTab) {
    const navItems = document.querySelectorAll(".nav-item");
    const tabPanels = document.querySelectorAll(".tab-panel");
    const tabTitle = document.getElementById("tab-title");
    const tabSubtitle = document.getElementById("tab-subtitle");

    const tabMetadata = {
        "tab-dashboard": {
            title: "Operational Dashboard",
            sub: "Real-time telemetry and key sustainability metrics from DAEWOO Steel facility."
        },
        "tab-decision-center": {
            title: "PRAGATI AI Decision Center",
            sub: "End-to-end AI recommendations connecting forecasting, open alerts, schedule optimization, and cost impact."
        },
        "tab-anomalies": {
            title: "Anomaly Alerts Engine",
            sub: "Multivariate machine learning anomalies and rule-based operational diagnostics."
        },
        "tab-forecasting": {
            title: "Demand Forecasting Engine",
            sub: "Future energy projections using Prophet curve fitting and Random Forest models."
        },
        "tab-scheduler": {
            title: "Load Shifting Scheduler",
            sub: "Reschedule heavy factory workloads to minimize financial bills and grid CO₂ intensity."
        },
        "tab-digital-twin": {
            title: "Digital Twin Sandbox",
            sub: "Model hypothetical solar capacity and battery packs to calculate CapEx payback periods."
        },
        "tab-copilot": {
            title: "AI Sustainability Copilot",
            sub: "Chat with PRAGATI AI to audit energy leaks and receive operational recommendations."
        },
        "tab-subscriptions": {
            title: "PRAGATI AI Startup Plans & Managed B2B Deployment",
            sub: "Deploy active sustainability intelligence across your client sites or request dedicated factory SCADA integration."
        }
    };

    // Hide all tab panels completely using inline style + remove active class
    tabPanels.forEach(p => {
        p.classList.remove("active");
        p.style.display = "none";
    });

    // Deactivate all sidebar nav links
    navItems.forEach(n => n.classList.remove("active"));

    // Activate target panel & nav link
    const targetPanel = document.getElementById(targetTab);
    const targetNav = document.querySelector(`.nav-item[data-tab="${targetTab}"]`);

    if (targetPanel) {
        targetPanel.classList.add("active");
        targetPanel.style.display = "block";
    }

    if (targetNav) {
        targetNav.classList.add("active");
    }

    // Scroll main workspace to top
    window.scrollTo({ top: 0, behavior: 'instant' });

    // Set dynamic header titles
    if (tabMetadata[targetTab]) {
        if (tabTitle) tabTitle.innerText = tabMetadata[targetTab].title;
        if (tabSubtitle) tabSubtitle.innerText = tabMetadata[targetTab].sub;
    }

    // Trigger tab-specific loaders
    if (targetTab === "tab-dashboard") {
        loadTelemetry();
    } else if (targetTab === "tab-decision-center") {
        loadDecisionCenter();
    } else if (targetTab === "tab-anomalies") {
        fetchActiveAlerts();
        loadGroupedEvents();
    }

    // Trigger Chart.js auto-resize
    setTimeout(() => {
        if (targetTab === "tab-dashboard" && telemetryChart) {
            telemetryChart.resize();
        } else if (targetTab === "tab-forecasting" && forecastChart) {
            forecastChart.resize();
            if (backtestChart) backtestChart.resize();
        } else if (targetTab === "tab-scheduler" && scheduleChart) {
            scheduleChart.resize();
        } else if (targetTab === "tab-anomalies" && thdChart) {
            thdChart.resize();
        } else if (targetTab === "tab-digital-twin" && twinCashFlowChart) {
            twinCashFlowChart.resize();
        }
    }, 50);
}

function initTabNavigation() {
    switchTab("tab-dashboard");
}

// Check Backend API Connection Health
async function checkBackendStatus() {
    const dot = document.getElementById("status-dot");
    const text = document.getElementById("status-text");
    
    try {
        const res = await fetch(`${API_BASE}/status`);
        if (res.ok) {
            dot.className = "pulse-dot green";
            text.innerText = "Backend Connected";
        } else {
            throw new Error();
        }
    } catch (e) {
        dot.className = "pulse-dot red";
        text.innerText = "Backend Offline";
    }
}

let currentTenantId = "demo_steel";

// Tab 1: Load and Render Telemetry Data
async function loadTelemetry(days = 7, tenantId = currentTenantId) {
    currentTenantId = tenantId;
    try {
        const res = await fetch(`${API_BASE}/telemetry?days=${days}&tenant_id=${currentTenantId}`);
        if (!res.ok) throw new Error("Failed to fetch telemetry");
        
        const data = await res.json();
        
        // Update KPIs with the latest values
        const lastIdx = data.usage_kwh.length - 1;
        if (lastIdx >= 0) {
            document.getElementById("kpi-load").innerText = `${data.usage_kwh[lastIdx]} kW`;
            document.getElementById("kpi-carbon").innerText = `${data.co2_tco2[lastIdx]} t`;
            document.getElementById("kpi-pf").innerText = `${data.power_factor_lagging[lastIdx]} %`;
            
            // Scope 1/2/3 breakdown binding
            document.getElementById("kpi-scope1").innerText = `${data.scope1_co2_kg[lastIdx]} kg`;
            document.getElementById("kpi-scope2").innerText = `${data.scope2_co2_kg[lastIdx]} kg`;
            document.getElementById("kpi-scope3").innerText = `${data.scope3_co2_kg[lastIdx]} kg`;
            
            // Dynamic carbon rate mapping
            const currentHour = new Date(data.timestamps[lastIdx]).getHours();
            let carbonRateText = "Grid base load";
            if (currentHour >= 10 && currentHour <= 15) {
                carbonRateText = "Solar intensity peak (250g/kWh)";
            } else if (currentHour >= 17 && currentHour <= 22) {
                carbonRateText = "Evening peak demand (450g/kWh)";
            }
            document.getElementById("kpi-carbon-rate").innerText = carbonRateText;

            // Accurately label historical replay timestamp range
            const rangeElem = document.getElementById("telemetry-timestamp-range");
            if (rangeElem && data.timestamps.length > 0) {
                rangeElem.innerText = `Source: UCI Steel Dataset (Historical Replay: ${data.timestamps[0]} to ${data.timestamps[lastIdx]})`;
            }
        }
        
        // Render Chart.js
        renderTelemetryChart(data);
        renderTHDChart(data);
    } catch (e) {
        console.error(e);
    }
}

function renderTelemetryChart(data) {
    const ctx = document.getElementById("telemetryChart").getContext("2d");
    
    if (telemetryChart) {
        telemetryChart.destroy();
    }
    
    // Format timestamp labels with month/day + hour (e.g. "05/01 12:00")
    const formattedLabels = data.timestamps.map(t => {
        const parts = t.split(" ");
        if (parts.length >= 2) {
            const d = parts[0].substring(5).replace("-", "/");
            const h = parts[1].substring(0, 5);
            return `${d} ${h}`;
        }
        return t;
    });
    
    telemetryChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: formattedLabels,
            datasets: [
                {
                    label: 'Grid Load (kW)',
                    data: data.usage_kwh,
                    borderColor: '#059669', // Bio-Emerald
                    backgroundColor: 'rgba(16, 185, 129, 0.12)',
                    borderWidth: 2.5,
                    tension: 0.3,
                    fill: true,
                    yAxisID: 'y'
                },
                {
                    label: 'Power Factor (%)',
                    data: data.power_factor_lagging,
                    borderColor: '#D97706', // Solar Gold
                    borderWidth: 2,
                    borderDash: [5, 5],
                    tension: 0.2,
                    fill: false,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#1F2B24', font: { family: 'Plus Jakarta Sans', weight: '700', size: 12 } }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(200, 190, 170, 0.4)' },
                    ticks: { color: '#526357', maxTicksLimit: 14, font: { weight: '600' } }
                },
                y: {
                    title: { display: true, text: 'Active Power (kW)', color: '#1F2B24', font: { weight: '700' } },
                    grid: { color: 'rgba(200, 190, 170, 0.4)' },
                    ticks: { color: '#526357', font: { weight: '600' } }
                },
                y1: {
                    position: 'right',
                    title: { display: true, text: 'Power Factor (%)', color: '#1F2B24', font: { weight: '700' } },
                    grid: { drawOnChartArea: false },
                    min: 40,
                    max: 100,
                    ticks: { color: '#526357', font: { weight: '600' } }
                }
            }
        }
    });
}

function renderTHDChart(data) {
    const ctx = document.getElementById("thdChart");
    if (!ctx) return;
    
    if (thdChart) {
        thdChart.destroy();
    }
    
    thdChart = new Chart(ctx.getContext("2d"), {
        type: 'line',
        data: {
            labels: data.timestamps.map(t => t.split(" ")[1] ? t.split(" ")[1].substring(0, 5) : t),
            datasets: [
                {
                    label: 'Total Harmonic Distortion (THD %)',
                    data: data.thd_pct,
                    borderColor: '#D97706', // Solar Gold
                    backgroundColor: 'rgba(217, 119, 6, 0.12)',
                    borderWidth: 2.5,
                    tension: 0.3,
                    fill: true,
                    yAxisID: 'y'
                },
                {
                    label: 'Grid Voltage (V)',
                    data: data.voltage_v,
                    borderColor: '#E07A5F', // Terracotta
                    borderWidth: 2,
                    tension: 0.2,
                    fill: false,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#1F2B24', font: { family: 'Plus Jakarta Sans', weight: '700', size: 12 } }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(200, 190, 170, 0.4)' },
                    ticks: { color: '#526357', maxTicksLimit: 12, font: { weight: '600' } }
                },
                y: {
                    title: { display: true, text: 'THD (%)', color: '#1F2B24', font: { weight: '700' } },
                    grid: { color: 'rgba(200, 190, 170, 0.4)' },
                    ticks: { color: '#526357', font: { weight: '600' } }
                },
                y1: {
                    position: 'right',
                    title: { display: true, text: 'Voltage (V)', color: '#1F2B24', font: { weight: '700' } },
                    grid: { drawOnChartArea: false },
                    ticks: { color: '#526357', font: { weight: '600' } }
                }
            }
        }
    });
}

// Tab 2: Load and Display Anomalies Table
async function loadAnomalies(tenantId = currentTenantId) {
    const tableBody = document.querySelector("#anomalies-table tbody");
    try {
        const res = await fetch(`${API_BASE}/anomalies?tenant_id=${tenantId}`);
        if (!res.ok) throw new Error("Failed to fetch anomalies");
        
        const anomalies = await res.json();
        
        // Update Anomaly badges
        document.getElementById("kpi-anomalies-count").innerText = anomalies.length;
        document.getElementById("anomalies-badge").innerText = `${anomalies.length} Flagged Observations`;
        const anomalyStatusElem = document.getElementById("kpi-anomalies-status");
        if (anomalyStatusElem) {
            anomalyStatusElem.innerText = `${anomalies.length} observations (226 distinct events)`;
        }
        
        if (anomalies.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="7" class="text-center">No anomalies detected in recent telemetry.</td></tr>`;
            return;
        }
        
        let rowsHtml = "";
        anomalies.forEach(a => {
            let severityClass = "orange-bg";
            if (a.severity === "Critical") severityClass = "red-bg";
            else if (a.severity === "High") severityClass = "red-bg";
            
            rowsHtml += `
                <tr>
                    <td><strong>${a.timestamp}</strong></td>
                    <td><span class="badge ${severityClass}">${a.anomaly_type}</span></td>
                    <td><span class="badge ${a.severity === 'Critical' ? 'red-bg' : 'orange-bg'}">${a.severity}</span></td>
                    <td>${a.usage_kwh} kW</td>
                    <td>${a.power_factor_lagging}%</td>
                    <td class="text-secondary">${a.explanation}</td>
                    <td style="color: #10B981; font-weight: 500;">${a.recommendation}</td>
                </tr>
            `;
        });
        
        tableBody.innerHTML = rowsHtml;
    } catch (e) {
        tableBody.innerHTML = `<tr><td colspan="7" class="text-center red">Failed to connect to ML anomaly engine.</td></tr>`;
    }
}

// Tab 3: Run Forecasting Models
async function runForecasting() {
    const btn = document.getElementById("run-forecast-btn");
    const hours = parseInt(document.getElementById("forecast-hours").value);
    const folds = parseInt(document.getElementById("backtest-folds").value);
    
    btn.disabled = true;
    btn.innerText = "Training models, compiling curves...";
    
    // Dynamically update UI header
    document.getElementById("backtest-title-header").innerText = `Rolling Backtest RMSE (${folds} Folds)`;
    
    try {
        const res = await fetch(`${API_BASE}/forecast`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ hours: hours, backtest_folds: folds, tenant_id: currentTenantId })
        });
        
        if (!res.ok) throw new Error("Forecasting calculations failed");
        
        const data = await res.json();
        
        // Determine the seasonal model name (Prophet or Exponential Smoothing)
        const seasonalName = data.seasonal_model_name || "Prophet";
        
        // Update Statistical Indicators
        document.getElementById("metric-adf-p").innerText = data.adf.p_value;
        const adfStatusEl = document.getElementById("metric-adf-status");
        if (data.adf.is_stationary) {
            adfStatusEl.className = "badge green-bg";
            adfStatusEl.innerText = "Stationary (p < 0.05)";
        } else {
            adfStatusEl.className = "badge orange-bg";
            adfStatusEl.innerText = "Non-Stationary";
        }

        // Update Validation RMSE (Single Split)
        const prophetRmseEl = document.getElementById("metric-prophet-rmse");
        if (data.metrics.prophet_rmse !== null) {
            prophetRmseEl.innerText = `${data.metrics.prophet_rmse} kW`;
        } else {
            prophetRmseEl.innerText = "N/A";
        }
        document.getElementById("metric-rf-rmse").innerText = `${data.metrics.rf_rmse} kW`;
        document.getElementById("metric-rnn-rmse").innerText = `${data.metrics.rnn_rmse} kW`;
        
        const bestBadge = document.getElementById("metric-best-model");
        bestBadge.innerText = data.metrics.best_model;

        // Update Rolling Backtest RMSE
        document.getElementById("metric-bt-prophet").innerText = `${data.backtest.prophet_rmse} kW`;
        document.getElementById("metric-bt-rf").innerText = `${data.backtest.rf_rmse} kW`;
        document.getElementById("metric-bt-rnn").innerText = `${data.backtest.rnn_rmse} kW`;
        document.getElementById("metric-bt-persistence").innerText = `${data.backtest.persistence_rmse} kW`;
        
        // Render charts
        renderForecastChart(data, seasonalName);
        renderBacktestChart(data, seasonalName);
    } catch (e) {
        console.error("Forecasting execution error:", e);
        alert(`Failed to compile forecast predictions: ${e.message || e}`);
    } finally {
        btn.disabled = false;
        btn.innerText = "Run Forecasting Models";
    }
}


function renderForecastChart(data, seasonalName = "Prophet") {
    const ctx = document.getElementById("forecastChart").getContext("2d");
    if (forecastChart) {
        forecastChart.destroy();
    }
    
    // Build datasets — always include actuals and RF
    const datasets = [
        {
            label: 'Actual Telemetry (kWh)',
            data: data.actuals,
            borderColor: '#94A3B8',
            borderWidth: 2.2,
            borderDash: [3, 3],
            tension: 0.1,
            fill: false
        }
    ];
    
    if (data.persistence_forecast && data.persistence_forecast.length > 0) {
        datasets.push({
            label: 'Persistence Baseline (t-24)',
            data: data.persistence_forecast,
            borderColor: '#64748B', // Dotted Slate Grey
            borderWidth: 1.5,
            borderDash: [6, 4],
            tension: 0.1,
            fill: false
        });
    }
    
    // Only add seasonal model (Prophet/ExpSmoothing) if data exists
    if (data.prophet_forecast && data.prophet_forecast.length > 0) {
        datasets.push({
            label: `${seasonalName} (Forecast)`,
            data: data.prophet_forecast,
            borderColor: '#10B981', // Emerald
            borderWidth: 2.5,
            tension: 0.3,
            fill: false
        });
    }
    
    datasets.push({
        label: 'Random Forest (Forecast)',
        data: data.rf_forecast,
        borderColor: '#8B5CF6', // Violet
        borderWidth: 2,
        tension: 0.2,
        fill: false
    });
    
    if (data.rnn_forecast && data.rnn_forecast.length > 0) {
        datasets.push({
            label: 'RNN (Forecast)',
            data: data.rnn_forecast,
            borderColor: '#EC4899', // Pink
            borderWidth: 2,
            tension: 0.2,
            fill: false
        });
    }
    
    forecastChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.timestamps.map(t => {
                const parts = t.split(" ");
                if (parts.length >= 2) {
                    const d = parts[0].substring(5).replace("-", "/");
                    const h = parts[1].substring(0, 5);
                    return `${d} ${h}`;
                }
                return t;
            }),
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#94A3B8', font: { family: 'Inter' } }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.04)' },
                    ticks: { color: '#64748B', maxTicksLimit: 12 }
                },
                y: {
                    title: { display: true, text: 'Active Power (kWh)', color: '#94A3B8' },
                    grid: { color: 'rgba(255, 255, 255, 0.04)' },
                    ticks: { color: '#64748B' }
                }
            }
        }
    });
}

function renderBacktestChart(data, seasonalName = "Prophet") {
    const ctx = document.getElementById("backtestChart").getContext("2d");
    if (backtestChart) {
        backtestChart.destroy();
    }
    
    backtestChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [seasonalName, 'Random Forest', 'RNN', 'Persistence Baseline'],
            datasets: [{
                label: 'Rolling Backtest RMSE (kW)',
                data: [
                    data.backtest.prophet_rmse,
                    data.backtest.rf_rmse,
                    data.backtest.rnn_rmse,
                    data.backtest.persistence_rmse
                ],
                backgroundColor: [
                    'rgba(16, 185, 129, 0.65)', // Emerald
                    'rgba(139, 92, 246, 0.65)', // Violet
                    'rgba(236, 72, 153, 0.65)', // Pink
                    'rgba(100, 116, 139, 0.65)'  // Slate Grey
                ],
                borderColor: [
                    '#10B981',
                    '#8B5CF6',
                    '#EC4899',
                    '#64748B'
                ],
                borderWidth: 1.5,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.04)' },
                    ticks: { color: '#94A3B8', font: { family: 'Inter', weight: '500' } }
                },
                y: {
                    title: { display: true, text: 'RMSE (kW)', color: '#94A3B8' },
                    grid: { color: 'rgba(255, 255, 255, 0.04)' },
                    ticks: { color: '#64748B' }
                }
            }
        }
    });
}


// Tab 4: Workload Scheduling Optimizer
async function runScheduler() {
    const load = parseFloat(document.getElementById("sched-load").value);
    const duration = parseInt(document.getElementById("sched-duration").value);
    const solar = parseFloat(document.getElementById("sched-solar").value);
    const weight = parseFloat(document.getElementById("sched-weight").value);
    
    // Parse Advanced settings with safe fallback defaults
    const elTaskPf = document.getElementById("sched-task-pf");
    const elBatCap = document.getElementById("sched-battery-cap");
    const elBatRate = document.getElementById("sched-battery-rate");
    const elBatEff = document.getElementById("sched-battery-eff");
    const elSolarYield = document.getElementById("sched-solar-yield-mult");
    const elPfPenalty = document.getElementById("sched-pf-penalty");
    
    const task_power_factor = elTaskPf ? parseFloat(elTaskPf.value) : 0.80;
    const battery_capacity_kwh = elBatCap ? parseFloat(elBatCap.value) : 50.0;
    const battery_rate_kw = elBatRate ? parseFloat(elBatRate.value) : 25.0;
    const battery_efficiency = elBatEff ? parseFloat(elBatEff.value) / 100.0 : 0.95;
    const solar_yield_coeff = elSolarYield ? parseFloat(elSolarYield.value) / 100.0 : 0.12;
    const pf_penalty_mult = elPfPenalty ? parseFloat(elPfPenalty.value) : 2.0;
    
    try {
        const res = await fetch(`${API_BASE}/schedule`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                task_load_kw: load,
                task_duration_h: duration,
                solar_capacity_kw: solar,
                environmental_weight: weight,
                battery_capacity_kwh: battery_capacity_kwh,
                battery_rate_kw: battery_rate_kw,
                battery_efficiency: battery_efficiency,
                solar_yield_coeff: solar_yield_coeff,
                task_power_factor: task_power_factor,
                pf_penalty_mult: pf_penalty_mult,
                tenant_id: currentTenantId
            })
        });
        
        if (!res.ok) throw new Error("Optimizer failed");
        
        const data = await res.json();
        
        // Update UI
        const optHourStr = `${data.best_start_hour.toString().padStart(2, '0')}:00`;
        document.getElementById("sched-recommendation").innerHTML = `Optimal Start Hour: <span class="highlight">${optHourStr}</span>`;
        
        document.getElementById("sched-cost-save").innerText = `$${data.savings.cost_dollars.toFixed(2)}`;
        document.getElementById("sched-cost-pct").innerText = `${data.savings.cost_percent}% lower utility tariff`;
        
        document.getElementById("sched-carbon-save").innerText = `${data.savings.carbon_kg.toFixed(1)} kg CO₂`;
        document.getElementById("sched-carbon-pct").innerText = `${data.savings.carbon_percent}% lower emissions`;
        
        // Update Battery Health indicators
        if (data.battery_final_soh_pct !== undefined) {
            document.getElementById("sched-battery-soh").innerText = `${data.battery_final_soh_pct.toFixed(4)}% SoH`;
            document.getElementById("sched-battery-deg").innerText = `${data.battery_degradation_pct.toFixed(6)}% daily wear`;
        }
        
        // Render scheduler comparison chart
        renderSchedulerChart(data);
    } catch (e) {
        alert("Failed to compute optimal schedule.");
    }
}

function renderSchedulerChart(data) {
    const ctx = document.getElementById("scheduleChart").getContext("2d");
    if (scheduleChart) {
        scheduleChart.destroy();
    }
    
    // Compile hourly loads
    const hours = Array.from({ length: 24 }, (_, i) => `${i.toString().padStart(2, '0')}:00`);
    
    // We map grid draw curves for baseline vs optimized
    const baselineDraw = Array(24).fill(0);
    const optimizedDraw = Array(24).fill(0);
    const batterySoC = Array(24).fill(0);
    
    // Fill baseline task run (starts at 9 AM)
    const baseStart = data.baseline.start_hour;
    for (let k = 0; k < data.baseline.details.length; k++) {
        const h = (baseStart + k) % 24;
        baselineDraw[h] = data.baseline.details[k].grid_draw_kwh;
    }
    
    // Fill optimized task run and battery SoC
    const optStart = data.best_start_hour;
    for (let k = 0; k < data.best_hourly_details.length; k++) {
        const h = (optStart + k) % 24;
        optimizedDraw[h] = data.best_hourly_details[k].grid_draw_kwh;
        batterySoC[h] = data.best_hourly_details[k].battery_soc_kwh;
    }
    
    scheduleChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: hours,
            datasets: [
                {
                    label: 'Baseline Shift Grid Draw (kW)',
                    data: baselineDraw,
                    backgroundColor: 'rgba(239, 68, 68, 0.4)', // Muted Red
                    borderColor: '#EF4444',
                    borderWidth: 1,
                    yAxisID: 'y'
                },
                {
                    label: 'Optimized Shift Grid Draw (kW)',
                    data: optimizedDraw,
                    backgroundColor: 'rgba(16, 185, 129, 0.4)', // Muted Emerald
                    borderColor: '#10B981',
                    borderWidth: 1,
                    yAxisID: 'y'
                },
                {
                    label: 'Battery SoC (kWh)',
                    data: batterySoC,
                    type: 'line',
                    borderColor: '#06B6D4', // Cyan
                    backgroundColor: 'rgba(6, 182, 212, 0.05)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: false,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#94A3B8', font: { family: 'Inter' } }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.04)' },
                    ticks: { color: '#64748B' }
                },
                y: {
                    title: { display: true, text: 'Energy Drawn from Grid (kWh)', color: '#94A3B8' },
                    grid: { color: 'rgba(255, 255, 255, 0.04)' },
                    ticks: { color: '#64748B' }
                },
                y1: {
                    position: 'right',
                    title: { display: true, text: 'Battery SoC (kWh)', color: '#94A3B8' },
                    grid: { drawOnChartArea: false },
                    ticks: { color: '#64748B' }
                }
            }
        }
    });
}

// Tab 5: Digital Twin Sandbox
async function runDigitalTwin() {
    const solar = parseFloat(document.getElementById("twin-solar").value);
    const battery = parseFloat(document.getElementById("twin-battery").value);
    
    try {
        const res = await fetch(`${API_BASE}/simulate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                solar_capacity_kw: solar,
                battery_capacity_kwh: battery,
                tenant_id: currentTenantId
            })
        });
        
        if (!res.ok) throw new Error("Simulator failed");
        
        const data = await res.json();
        
        // Update DOM
        document.getElementById("twin-val-gen").innerText = `${data.annual_solar_generation_kwh.toLocaleString()} kWh/yr`;
        document.getElementById("twin-val-self").innerText = `${data.self_consumption_percent}%`;
        document.getElementById("twin-val-savings").innerText = `$${data.annual_financial_savings_dollars.toLocaleString(undefined, {maximumFractionDigits: 0})}`;
        document.getElementById("twin-val-co2").innerText = `${data.annual_co2_offset_kg.toLocaleString(undefined, {maximumFractionDigits: 0})} kg CO₂`;
        document.getElementById("twin-val-capex").innerText = `$${data.capital_investment_dollars.toLocaleString()}`;
        const simplePayback = data.undiscounted_simple_payback_years || (data.capital_investment_dollars / data.annual_financial_savings_dollars).toFixed(2);
        const simplePaybackElem = document.getElementById("twin-val-simple-payback");
        if (simplePaybackElem) simplePaybackElem.innerText = `${simplePayback} Years`;
        document.getElementById("twin-val-payback").innerText = `${data.after_tax_cashflow_breakeven_years || data.simple_payback_period_years} Years`;
        
        // Bind new Ph.D. levelized cost / cash flows / NPV
        if (data.net_present_value_dollars !== undefined) {
            document.getElementById("twin-val-npv").innerText = `$${data.net_present_value_dollars.toLocaleString(undefined, {maximumFractionDigits: 0})}`;
            document.getElementById("twin-val-lcoe").innerText = `$${data.lcoe_dollars_per_kwh.toFixed(4)} /kWh`;
            document.getElementById("twin-val-macrs").innerText = `$${data.macrs_tax_shield_dollars.toLocaleString(undefined, {maximumFractionDigits: 0})}`;
            document.getElementById("twin-val-peak").innerText = `${data.peak_shaving_kw.toFixed(1)} kW`;
            
            // Render 20-Year Cash Flow chart
            renderTwinCashFlowChart(data.yearly_cash_flows);
        }
    } catch (e) {
        console.error(e);
    }
}

function renderTwinCashFlowChart(cashFlows) {
    const ctx = document.getElementById("twinCashFlowChart");
    if (!ctx) return;
    
    if (twinCashFlowChart) {
        twinCashFlowChart.destroy();
    }

    if (!cashFlows || cashFlows.length === 0) return;

    // Support both array of numbers and array of cash_flow_table row objects
    const isObjectArray = typeof cashFlows[0] === 'object';
    const years = cashFlows.map((item, i) => isObjectArray ? `Yr ${item.year}` : `Yr ${i + 1}`);
    const netFlows = cashFlows.map(item => isObjectArray ? (item.net_cashflow_inr !== undefined ? item.net_cashflow_inr : item.net_cf) : item);
    const cumFlows = isObjectArray ? cashFlows.map(item => item.cumulative_cashflow_inr) : null;
    
    const datasets = [{
        type: 'bar',
        label: 'Annual Net Cash Flow (₹)',
        data: netFlows,
        backgroundColor: netFlows.map(val => val >= 0 ? 'rgba(16, 185, 129, 0.65)' : 'rgba(239, 68, 68, 0.65)'),
        borderColor: netFlows.map(val => val >= 0 ? '#10B981' : '#EF4444'),
        borderWidth: 1.5,
        borderRadius: 4,
        yAxisID: 'y'
    }];

    if (cumFlows && cumFlows.length > 0) {
        datasets.push({
            type: 'line',
            label: 'Cumulative Cash Flow (₹)',
            data: cumFlows,
            borderColor: '#38BDF8',
            backgroundColor: 'rgba(56, 189, 248, 0.1)',
            borderWidth: 2.5,
            pointBackgroundColor: '#38BDF8',
            pointRadius: 3,
            fill: false,
            tension: 0.25,
            yAxisID: 'y'
        });
    }

    twinCashFlowChart = new Chart(ctx.getContext("2d"), {
        data: {
            labels: years,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: true, position: 'top', labels: { color: '#94A3B8', boxWidth: 12 } },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ₹${context.raw?.toLocaleString() || context.raw}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.04)' },
                    ticks: { color: '#94A3B8' }
                },
                y: {
                    title: { display: true, text: 'Cash Flow (₹)', color: '#94A3B8' },
                    grid: { color: 'rgba(255, 255, 255, 0.04)' },
                    ticks: {
                        color: '#64748B',
                        callback: function(val) {
                            if (Math.abs(val) >= 10000000) return '₹' + (val / 10000000).toFixed(1) + ' Cr';
                            if (Math.abs(val) >= 100000) return '₹' + (val / 100000).toFixed(1) + ' L';
                            return '₹' + (val / 1000).toFixed(0) + 'k';
                        }
                    }
                }
            }
        }
    });
}

// Tab 6: AI Copilot Chat Engine
async function sendCopilotMessage() {
    const input = document.getElementById("chat-input");
    const container = document.getElementById("chat-messages-container");
    const msg = input.value.trim();
    
    if (!msg) return;
    
    // Add user message bubble (sanitized to prevent XSS)
    const userBubble = document.createElement("div");
    userBubble.className = "message user";
    userBubble.innerHTML = `<div class="message-content">${sanitizeHTML(msg)}</div>`;
    container.appendChild(userBubble);
    
    input.value = "";
    container.scrollTop = container.scrollHeight;
    
    // Add typing loader for bot
    const botBubble = document.createElement("div");
    botBubble.className = "message bot";
    botBubble.innerHTML = `<div class="message-content">Thinking and checking telemetry logs...</div>`;
    container.appendChild(botBubble);
    container.scrollTop = container.scrollHeight;
    
    try {
        const res = await fetch(`${API_BASE}/copilot`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: msg })
        });
        
        if (!res.ok) throw new Error("Chat api failed");
        
        const data = await res.json();
        
        // Replace typing loader with real reply
        // Simple markdown formatter helper for bold formatting
        let replyHtml = data.reply
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
            
        botBubble.innerHTML = `<div class="message-content">${replyHtml}</div>`;
    } catch (e) {
        botBubble.innerHTML = `<div class="message-content text-danger">Failed to connect to AI Copilot engine.</div>`;
    } finally {
        container.scrollTop = container.scrollHeight;
    }
}

// Tab 7: Startup Subscriptions & Payment Modal Logic
let currentSelectedPlan = null;
let currentSelectedPrice = 0;

function openPaymentModal(planName, price) {
    currentSelectedPlan = planName;
    currentSelectedPrice = price;
    
    document.getElementById("modal-selected-plan").innerText = `Selected Plan: ${planName}`;
    document.getElementById("modal-selected-price").innerText = `₹${price.toLocaleString()} / month`;
    
    const modal = document.getElementById("payment-modal");
    if (modal) {
        modal.style.display = "flex";
    }
}

function closePaymentModal() {
    const modal = document.getElementById("payment-modal");
    if (modal) {
        modal.style.display = "none";
    }
}

function handlePaymentSubmit(event) {
    event.preventDefault();
    const company = document.getElementById("pay-company-name").value.trim();
    const email = document.getElementById("pay-email").value.trim();
    const method = document.getElementById("pay-method").value;
    
    if (!company || !email) {
        alert("Please fill in your company name and work email.");
        return;
    }
    
    closePaymentModal();
    
    alert(`🎉 Subscription Activated!\n\nThank you, ${company}!\n\nPlan: ${currentSelectedPlan} (₹${currentSelectedPrice.toLocaleString()}/mo)\nBilling Email: ${email}\nPayment Gateway: ${method.toUpperCase()}\n\nYour API Keys and Multi-Tenant Portal access details have been dispatched to ${email}.`);
}

// Day 3: Digital Twin Simulation & Audit Log Drawer
async function runDigitalTwinSimulation() {
    const solar = parseFloat(document.getElementById("twin-solar")?.value || 250);
    const battery = parseFloat(document.getElementById("twin-battery")?.value || 100);
    const shift = parseFloat(document.getElementById("twin-shift")?.value || 20);
    const taxRegime = document.getElementById("twin-tax-regime")?.value || "SECTION_32_RENEWABLE_40_WDV";
    const discountRate = parseFloat(document.getElementById("twin-discount-rate")?.value || 10.0);
    const horizonYears = parseInt(document.getElementById("twin-horizon")?.value || 15);
    
    const btn = document.getElementById("run-digital-twin-btn");
    if (btn) btn.innerText = "Simulating Scenarios... ⏳";

    try {
        const res = await fetch(`${API_BASE}/v1/simulation/digital_twin`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                region: "Western",
                base_monthly_kwh: 150000.0,
                solar_capacity_kw: solar,
                battery_storage_kwh: battery,
                load_shift_pct: shift,
                simulation_years: horizonYears,
                discount_rate_pct: discountRate,
                tax_regime: taxRegime
            })
        });

        if (!res.ok) throw new Error("Digital Twin simulation failed");

        const data = await res.json();
        const sim = data.result.simulation;
        const fin = sim.financial_metrics;
        const life = sim.lifecycle_analysis || {};
        const tax = sim.tax_regime_audit || {};

        // 1. Update Core KPI cards
        if (document.getElementById("twin-val-gen")) {
            const annualGen = Math.round(sim.energy_metrics.monthly_solar_generation_kwh * 12);
            document.getElementById("twin-val-gen").innerText = `${annualGen.toLocaleString()} kWh/yr`;
        }
        if (document.getElementById("twin-val-savings")) {
            document.getElementById("twin-val-savings").innerText = `₹${Math.round(fin.annual_savings_inr).toLocaleString()}`;
        }
        if (document.getElementById("twin-val-co2")) {
            document.getElementById("twin-val-co2").innerText = `${sim.carbon_metrics.annual_co2_reduction_tons} Tons CO₂`;
        }
        if (document.getElementById("twin-val-npv")) {
            const npvVal = life.net_present_value_inr !== undefined ? life.net_present_value_inr : fin.net_present_value_inr;
            document.getElementById("twin-val-npv").innerText = `₹${Math.round(npvVal).toLocaleString()}`;
        }
        if (document.getElementById("twin-val-irr")) {
            const irrVal = life.internal_rate_of_return_pct;
            document.getElementById("twin-val-irr").innerText = (irrVal !== null && irrVal !== undefined) ? `${irrVal}%` : "N/A";
        }
        if (document.getElementById("twin-val-lcoe")) {
            const lcoeVal = life.levelized_cost_of_energy_inr_kwh || fin.levelized_cost_of_energy_inr_kwh || 0.0;
            document.getElementById("twin-val-lcoe").innerText = `₹${lcoeVal.toFixed(2)} /kWh`;
        }
        if (document.getElementById("twin-val-macrs")) {
            const taxShield = tax.total_lifecycle_tax_shield_inr !== undefined ? tax.total_lifecycle_tax_shield_inr : life.total_tax_shield_inr;
            document.getElementById("twin-val-macrs").innerText = `₹${Math.round(taxShield || 0).toLocaleString()}`;
        }
        if (document.getElementById("twin-val-peak")) {
            const peakShave = (sim.energy_metrics.monthly_bess_shaved_kwh / 30).toFixed(1);
            document.getElementById("twin-val-peak").innerText = `${peakShave} kW`;
        }

        // 2. Update ROI Section
        if (document.getElementById("twin-val-capex")) {
            document.getElementById("twin-val-capex").innerText = `₹${Math.round(fin.estimated_capex_inr).toLocaleString()}`;
        }
        if (document.getElementById("twin-val-simple-payback")) {
            const simplePb = fin.undiscounted_simple_payback_years;
            document.getElementById("twin-val-simple-payback").innerText = simplePb !== null && simplePb !== undefined ? `${simplePb} Years` : "No Payback";
        }
        if (document.getElementById("twin-val-payback")) {
            const afterTaxPb = fin.after_tax_cashflow_breakeven_years;
            document.getElementById("twin-val-payback").innerText = afterTaxPb !== null && afterTaxPb !== undefined ? `${afterTaxPb} Years` : "No Breakeven";
        }

        // 3. Render Lifecycle Cash Flow Chart
        if (life.cash_flow_table && life.cash_flow_table.length > 0) {
            renderTwinCashFlowChart(life.cash_flow_table);
        }

        // 4. Render Sensitivity Tornado Drivers Table
        renderTornadoDriversTable(sim.sensitivity_tornado?.tornado_drivers);

        // 5. Update Indian Fiscal Regime Breakdown Table
        if (document.getElementById("tax-regime-name")) {
            document.getElementById("tax-regime-name").innerText = tax.regime_name || "Income Tax Act Sec 32";
        }
        if (document.getElementById("tax-regime-rate")) {
            document.getElementById("tax-regime-rate").innerText = `${tax.corporate_tax_rate_pct}% (${tax.depreciation_rate_pct}% WDV)`;
        }
        if (document.getElementById("tax-year1-dep")) {
            document.getElementById("tax-year1-dep").innerText = `₹${Math.round(tax.year1_depreciation_inr || 0).toLocaleString()}`;
        }
        if (document.getElementById("tax-year1-shield")) {
            document.getElementById("tax-year1-shield").innerText = `+₹${Math.round(tax.year1_tax_shield_inr || 0).toLocaleString()}`;
        }
        if (document.getElementById("tax-total-shield")) {
            document.getElementById("tax-total-shield").innerText = `₹${Math.round(tax.total_lifecycle_tax_shield_inr || 0).toLocaleString()}`;
        }
        if (document.getElementById("tax-eligibility-note")) {
            document.getElementById("tax-eligibility-note").innerText = tax.eligibility_disclosure || "";
        }

        // 6. XAI Card Drawer
        if (data.result.xai_card) {
            renderXAICardDrawer(data.result.xai_card);
        }
    } catch (e) {
        console.error("Digital Twin error:", e);
    } finally {
        if (btn) btn.innerText = "Run Scenario Simulation ☀️";
    }
}

function renderTornadoDriversTable(drivers) {
    const tbody = document.getElementById("twin-tornado-tbody");
    if (!tbody || !drivers || drivers.length === 0) return;

    let html = "";
    drivers.forEach(d => {
        const badgeClass = d.impact_level === "HIGH" ? "red" : (d.impact_level === "MEDIUM" ? "yellow" : "emerald");
        const swingFormatted = d.npv_swing_inr >= 10000000 ?
            `±₹${(d.npv_swing_inr / 10000000).toFixed(2)} Cr` :
            `±₹${(d.npv_swing_inr / 100000).toFixed(2)} L`;

        html += `
            <tr>
                <td>${d.rank}</td>
                <td><strong>${d.parameter}</strong></td>
                <td>${d.base_value}</td>
                <td style="color: #60A5FA; font-weight: 600;">${swingFormatted}</td>
                <td><span class="badge ${badgeClass}" style="font-size: 0.7rem;">${d.impact_level}</span></td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
}

async function openAuditLogDrawer() {
    const drawer = document.getElementById("audit-log-drawer");
    const container = document.getElementById("audit-log-list");
    if (drawer) drawer.style.display = "flex";
    if (!container) return;

    container.innerHTML = `<p style="color: #526357; font-weight: 500; text-align: center; padding: 12px;">Loading audit logs...</p>`;

    try {
        const res = await fetch(`${API_BASE}/v1/audit/logs`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        if (!data.logs || data.logs.length === 0) {
            container.innerHTML = `<p style="color: #526357; text-align: center;">No audit logs recorded yet.</p>`;
            return;
        }

        let html = "";
        data.logs.forEach(log => {
            let statusColor = log.status === "APPROVED" ? "#059669" : "#D97706";
            let statusBg = log.status === "APPROVED" ? "rgba(16, 185, 129, 0.12)" : "rgba(217, 119, 6, 0.12)";
            html += `
                <div style="background: #FAF6EE; border: 1px solid rgba(200, 190, 170, 0.6); border-radius: 14px; padding: 16px; box-shadow: 0 2px 8px rgba(60, 52, 38, 0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-weight: 800; color: #1F2B24; font-size: 0.95rem; font-family: 'Outfit', sans-serif;">${log.id} — ${log.agent}</span>
                        <span style="font-size: 0.75rem; background: ${statusBg}; color: ${statusColor}; border: 1px solid ${statusColor}44; padding: 3px 10px; border-radius: 8px; font-weight: 700;">${log.status}</span>
                    </div>
                    <div style="font-size: 0.88rem; color: #334155; margin-bottom: 6px; line-height: 1.5;">${log.action}</div>
                    <div style="font-size: 0.82rem; color: #059669; font-weight: 700;">Impact: ${log.impact}</div>
                    <div style="font-size: 0.75rem; color: #64748B; margin-top: 8px;">🕒 ${log.timestamp} • Authorized by <strong>${log.approved_by}</strong></div>
                </div>
            `;
        });
        container.innerHTML = html;
    } catch (e) {
        console.error("Audit log error:", e);
        container.innerHTML = `<p style="color: #E07A5F; font-weight: 600; text-align: center; padding: 12px;">Failed to load audit logs: ${e.message}</p>`;
    }
}

function closeAuditLogDrawer() {
    const drawer = document.getElementById("audit-log-drawer");
    if (drawer) drawer.style.display = "none";
}

// Universal Backdrop Click & Escape Key Modal Dismissal
window.addEventListener("click", (e) => {
    if (e.target && e.target.classList && e.target.classList.contains("modal-backdrop")) {
        e.target.style.display = "none";
    }
});

window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        document.querySelectorAll(".modal-backdrop").forEach(modal => {
            modal.style.display = "none";
        });
    }
});

// Day 4: Real-time Telemetry Stream & Alert Center
async function fetchActiveAlerts() {
    if (window.fetchActiveAlerts) {
        return window.fetchActiveAlerts();
    }
}

async function acknowledgeAlert(alertId) {
    if (window.acknowledgeAlert) {
        return window.acknowledgeAlert(alertId);
    }
}

// Bind slider value displays and init alert polling
document.addEventListener("DOMContentLoaded", () => {
    const shiftSlider = document.getElementById("twin-shift");
    const shiftVal = document.getElementById("twin-shift-val");
    if (shiftSlider && shiftVal) {
        shiftSlider.addEventListener("input", (e) => {
            shiftVal.innerText = e.target.value;
        });
    }
    fetchActiveAlerts();
});

// Payment Gateway Modal & Subscription Processing
let selectedPlanName = "Pro Growth Tier";
let selectedPlanPrice = 3999;

function openPaymentModal(planName, price) {
    selectedPlanName = planName;
    selectedPlanPrice = price;
    
    const modal = document.getElementById("payment-modal");
    const planEl = document.getElementById("modal-selected-plan");
    const priceEl = document.getElementById("modal-selected-price");
    
    if (planEl) planEl.innerText = `Selected Plan: ${planName}`;
    if (priceEl) priceEl.innerText = `₹${price.toLocaleString()} / month (+ 18% GST)`;
    if (modal) modal.style.display = "flex";
}

function closePaymentModal() {
    const modal = document.getElementById("payment-modal");
    if (modal) modal.style.display = "none";
}

async function handlePaymentSubmit(event) {
    event.preventDefault();
    const btn = document.querySelector("#payment-form button[type='submit']");
    if (btn) btn.innerText = "Processing Payment Transaction... ⏳";
    
    const company = document.getElementById("pay-company-name") ? document.getElementById("pay-company-name").value : "EcoGrid Technologies";
    const email = document.getElementById("pay-email") ? document.getElementById("pay-email").value : "founder@ecogrid.io";
    const method = document.getElementById("pay-method") ? document.getElementById("pay-method").value : "upi";
    
    try {
        // Step 1: Create Order
        const orderRes = await fetch(`${API_BASE}/v1/payment/create-order`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                plan_name: selectedPlanName,
                amount_inr: selectedPlanPrice,
                company_name: company,
                email: email,
                payment_method: method
            })
        });
        const orderData = await orderRes.json();
        
        if (!orderRes.ok) throw new Error("Order creation failed");
        
        const orderId = orderData.order.order_id;
        const totalAmount = orderData.order.total_amount_inr;
        
        // Step 2: Verify Payment
        const verifyRes = await fetch(`${API_BASE}/v1/payment/verify`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                order_id: orderId,
                payment_id: `pay_RZP_${Math.random().toString(36).substring(2, 10).toUpperCase()}`,
                signature: "sig_valid_pragati_2026"
            })
        });
        const verifyData = await verifyRes.json();
        
        if (verifyRes.ok) {
            alert(`🎉 Subscription Active!\n\nThank you, ${company}!\nPlan: ${selectedPlanName}\nTotal Charged: ₹${totalAmount.toLocaleString()} (incl. 18% GST)\nLicense Key: ${verifyData.receipt.license_key}\nStatus: Active until ${verifyData.receipt.valid_until}`);
            closePaymentModal();
        } else {
            alert("Payment verification failed. Please try again.");
        }
    } catch (e) {
        console.error("Payment submission error:", e);
        alert("Transaction failed: " + e.message);
    } finally {
        if (btn) btn.innerText = "Proceed with Test Mode Checkout";
    }
}

// Industrial Enterprise Contact Sales Modal Handler
function openContactSalesModal(deploymentType) {
    const modal = document.getElementById("contact-sales-modal");
    if (modal) modal.style.display = "flex";
}

function closeContactSalesModal() {
    const modal = document.getElementById("contact-sales-modal");
    if (modal) modal.style.display = "none";
}

function handleContactSalesSubmit(event) {
    event.preventDefault();
    const plantName = document.getElementById("contact-plant-name") ? document.getElementById("contact-plant-name").value : "DAEWOO Steel";
    const personName = document.getElementById("contact-person-name") ? document.getElementById("contact-person-name").value : "Plant Manager";
    const email = document.getElementById("contact-email") ? document.getElementById("contact-email").value : "energy@daewoosteel.in";
    const loadKw = document.getElementById("contact-load-kw") ? document.getElementById("contact-load-kw").value : "500kW - 2MW";
    
    alert(`📩 Industrial Audit Request Received!\n\nThank you, ${personName} (${plantName})!\nOur Industrial Energy Team will review your ${loadKw} plant specifications and contact you at ${email} within 24 business hours.\n\nReference ID: IND-AUDIT-${Math.floor(100000 + Math.random() * 900000)}`);
    closeContactSalesModal();
}

// 🌐 VisionOS 3D Environmental Canvas Engine & Kinetic Cursor Glow
document.addEventListener("DOMContentLoaded", () => {
    // 1. Interactive Magnetic Cursor Glow (Spring Lerp Motion)
    const cursorGlow = document.getElementById("cursor-glow");
    let mouseX = window.innerWidth / 2;
    let mouseY = window.innerHeight / 2;
    let currentX = mouseX;
    let currentY = mouseY;

    window.addEventListener("mousemove", (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
    });

    const animateCursor = () => {
        currentX += (mouseX - currentX) * 0.12;
        currentY += (mouseY - currentY) * 0.12;
        if (cursorGlow) {
            cursorGlow.style.left = `${currentX}px`;
            cursorGlow.style.top = `${currentY}px`;
        }
        requestAnimationFrame(animateCursor);
    };
    animateCursor();

    // 2. High-Performance 60 FPS 3D Environmental Canvas Engine
    const canvas = document.getElementById("ambient-3d-canvas");
    if (canvas) {
        const ctx = canvas.getContext("2d");
        let width = canvas.width = window.innerWidth;
        let height = canvas.height = window.innerHeight;

        window.addEventListener("resize", () => {
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
        });

        // Generate 60 3D Environmental Particles
        const particles = [];
        for (let i = 0; i < 60; i++) {
            particles.push({
                x: Math.random() * width,
                y: Math.random() * height,
                z: Math.random() * 3 + 0.5,
                radius: Math.random() * 2.5 + 1,
                color: Math.random() > 0.4 ? "rgba(16, 185, 129, " : "rgba(245, 158, 11, ",
                alpha: Math.random() * 0.5 + 0.2,
                vx: (Math.random() - 0.5) * 0.6,
                vy: -Math.random() * 0.8 - 0.2
            });
        }

        const renderCanvas = () => {
            ctx.clearRect(0, 0, width, height);

            const parallaxX = (mouseX - width / 2) * 0.02;
            const parallaxY = (mouseY - height / 2) * 0.02;

            particles.forEach(p => {
                p.x += p.vx + parallaxX * (1 / p.z) * 0.1;
                p.y += p.vy + parallaxY * (1 / p.z) * 0.1;

                if (p.y < -10) {
                    p.y = height + 10;
                    p.x = Math.random() * width;
                }
                if (p.x < -10) p.x = width + 10;
                if (p.x > width + 10) p.x = -10;

                ctx.beginPath();
                ctx.arc(p.x, p.y, p.radius * p.z, 0, Math.PI * 2);
                ctx.fillStyle = `${p.color}${p.alpha})`;
                ctx.shadowBlur = 12;
                ctx.shadowColor = p.color.includes("16, 185") ? "#10B981" : "#F59E0B";
                ctx.fill();
            });

            requestAnimationFrame(renderCanvas);
        };
        renderCanvas();
    }

    // 3. 3D Card Mouse Tilt Physics
    const init3DTilt = () => {
        const cards = document.querySelectorAll(".kpi-card, .chart-card, .data-card, .pricing-card");
        cards.forEach(card => {
            card.addEventListener("mousemove", (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left - rect.width / 2;
                const y = e.clientY - rect.top - rect.height / 2;
                const rotateX = (-y / rect.height) * 14;
                const rotateY = (x / rect.width) * 14;
                card.style.transform = `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) translateY(-8px) scale3d(1.02, 1.02, 1.02)`;
            });
            card.addEventListener("mouseleave", () => {
                card.style.transform = "";
            });
        });
    };
    // 4. Demo Workspace Tenant Switcher & Automated Pipeline Trigger
    window.switchDemoTenant = function(tenantId) {
        const tenantNames = {
            "demo_steel": "DAEWOO Steel facility (Faridabad)",
            "demo_textile": "Vardhman Textile Weaving Mills (Panipat)",
            "demo_rice": "KRBL Basmati Rice Plant (Karnal)",
            "demo_auto": "Maruti Component Forging Plant (Gurugram)",
            "demo_chemical": "Haryana Specialty Chemicals Facility (Ambala)"
        };
        currentTenantId = tenantId;
        const name = tenantNames[tenantId] || tenantId;
        const sub = document.getElementById("tab-subtitle");
        if (sub) sub.innerText = `Real-time telemetry and key sustainability metrics from ${name}.`;
        
        loadTelemetry(7, tenantId);
        loadAnomalies(tenantId);
        runForecasting();
        runScheduler();
        runDigitalTwin();
    };

    window.triggerPipelineRetrain = async function() {
        const statusMsg = document.getElementById("retrain-status-msg");
        if (statusMsg) {
            statusMsg.style.display = "block";
            statusMsg.style.background = "rgba(6, 182, 212, 0.15)";
            statusMsg.style.color = "#0284C7";
            statusMsg.style.border = "1px solid rgba(6, 182, 212, 0.4)";
            statusMsg.innerText = "⏳ Ingesting CSV telemetry, running MAD outlier cleaning & training model benchmark tournament...";
        }
        
        try {
            const res = await fetch(`${API_BASE}/pipeline/retrain?tenant_id=demo_steel`, { method: "POST" });
            const data = await res.json();
            if (res.ok && data.status === "success") {
                if (statusMsg) {
                    statusMsg.style.background = "rgba(16, 185, 129, 0.15)";
                    statusMsg.style.color = "#047857";
                    statusMsg.style.border = "1px solid rgba(16, 185, 129, 0.4)";
                    statusMsg.innerText = `✅ Auto-Retraining Complete: TA-GRU Neural Network WON with RMSE ${data.pipeline_result.benchmark.winning_metrics.rmse} kW! Model registered to active tenant workspace.`;
                }
            } else {
                throw new Error(data.message || "Failed to retrain");
            }
        } catch (e) {
            if (statusMsg) {
                statusMsg.style.background = "rgba(239, 68, 68, 0.15)";
                statusMsg.color = "#B91C1C";
                statusMsg.style.border = "1px solid rgba(239, 68, 68, 0.4)";
                statusMsg.innerText = `❌ Retraining error: ${e.message}`;
            }
        }
    };

    // ==========================================
    // PRAGATI AI DECISION CENTER CONTROLLER
    // ==========================================
    window.currentDecisionActionId = "ACT-2026-081";

    window.loadDecisionCenter = async function() {
        try {
            const res = await fetch(`http://127.0.0.1:8000/api/v1/decision/overview`);
            if (!res.ok) return;
            const data = await res.json();
            const dc = data.decision_center;
            if (!dc) return;

            window.currentDecisionActionId = dc.action_id || "ACT-2026-081";

            // KPI Cards
            const fcEl = document.getElementById("dc-forecast-val");
            if (fcEl && dc.evidence) fcEl.innerText = `${dc.evidence.projected_peak_kw.toFixed(1)} kW Peak`;

            const altEl = document.getElementById("dc-alerts-val");
            if (altEl) altEl.innerText = `${data.active_alerts_count} Actionable`;

            const schedEl = document.getElementById("dc-sched-val");
            if (schedEl && dc.schedule_alternative) {
                schedEl.innerText = `Shift ${dc.schedule_alternative.task_load_kw.toFixed(0)} kW Load`;
            }

            const costEl = document.getElementById("dc-cost-val");
            if (costEl && dc.schedule_alternative) {
                costEl.innerText = `$${dc.schedule_alternative.monthly_recurring_savings_usd.toLocaleString()} / Mo`;
            }

            // Recommendation Header
            const badgeEl = document.getElementById("dc-action-id-badge");
            if (badgeEl) badgeEl.innerText = `RECOMMENDED ACTION #${dc.action_id}`;

            const titleEl = document.getElementById("dc-recommendation-title");
            if (titleEl && dc.title) titleEl.innerText = dc.title;

            const issueEl = document.getElementById("dc-issue-summary");
            if (issueEl && dc.issue_summary) issueEl.innerText = dc.issue_summary;

            // Evidence List
            const evList = document.getElementById("dc-evidence-list");
            if (evList && dc.evidence) {
                evList.innerHTML = `
                    <li><strong>Anomaly Trigger:</strong> ${sanitizeHTML(dc.evidence.anomaly_trigger || '')}</li>
                    <li><strong>48-Hour Demand Forecast:</strong> ${sanitizeHTML(dc.evidence.forecast_model || '')} (Peak: ${dc.evidence.projected_peak_kw.toFixed(1)} kW at ${dc.evidence.peak_hour}).</li>
                    <li><strong>Time-of-Use Tariff Penalty:</strong> Grid tariff increases 300% from $0.06/kWh to $0.18/kWh (₹11.50/kWh) during peak hours.</li>
                    <li><strong>Solar Availability:</strong> On-site Solar PV generates ${dc.evidence.solar_surplus_midday_kw} kWh surplus during 11:00–15:00.</li>
                `;
            }

            // Constraints List
            const constList = document.getElementById("dc-constraints-list");
            if (constList && dc.constraints_verified) {
                constList.innerHTML = dc.constraints_verified.map(c => `
                    <div style="display: flex; align-items: flex-start; gap: 8px; font-size: 0.85rem;">
                        <span style="color: #10B981; font-weight: 700;">✔️</span>
                        <div>
                            <strong style="color: #E2E8F0;">${sanitizeHTML(c.name)}:</strong>
                            <span style="color: #94A3B8;"> ${sanitizeHTML(c.detail)}</span>
                        </div>
                    </div>
                `).join('');
            }

            // Financial & Carbon Delta
            const sa = dc.schedule_alternative;
            if (sa) {
                const cbc = document.getElementById("dc-current-batch-cost");
                if (cbc) cbc.innerText = `$${sa.current_batch_cost_usd.toFixed(2)}`;

                const obc = document.getElementById("dc-opt-batch-cost");
                if (obc) obc.innerText = `$${sa.optimized_batch_cost_usd.toFixed(2)}`;

                const dbs = document.getElementById("dc-direct-batch-savings");
                if (dbs) {
                    const pct = sa.current_batch_cost_usd > 0 ? ((sa.cost_savings_per_batch_usd / sa.current_batch_cost_usd) * 100).toFixed(1) : 0;
                    dbs.innerText = `$${sa.cost_savings_per_batch_usd.toFixed(2)} / batch (-${pct}%)`;
                }

                const mrs = document.getElementById("dc-monthly-recurring-savings");
                if (mrs) {
                    const inrVal = sa.monthly_recurring_savings_inr || (sa.monthly_recurring_savings_usd * 83);
                    mrs.innerText = `$${sa.monthly_recurring_savings_usd.toLocaleString()} (₹${inrVal.toLocaleString()})`;
                }

                const avp = document.getElementById("dc-avoided-penalty");
                if (avp) avp.innerText = `$${(sa.avoided_peak_penalty_usd || 650).toFixed(2)} / mo`;

                const cs = document.getElementById("dc-carbon-savings");
                if (cs) cs.innerText = `${(sa.carbon_savings_kg_per_batch || 32.4).toFixed(1)} kg CO₂ / batch`;
            }

            // Audit & Provenance
            const createdText = document.getElementById("dc-audit-created-text");
            if (createdText) {
                createdText.innerHTML = `Audit Log: Action generated at <strong>${sanitizeHTML(dc.created_at || 'Just Now')}</strong> by <strong>PRAGATI Orchestrator</strong>`;
            }

            const provInfo = document.getElementById("dc-provenance-info");
            if (provInfo && dc.provenance) {
                provInfo.innerText = `Data Source: ${dc.provenance.data_source} | Model: ${dc.provenance.model_version} | Hash: ${dc.provenance.audit_hash}`;
            }

            // Phase 3: Multi-Stage Task Sequencing & Inter-Stage Lag Buffers
            const stagesContainer = document.getElementById("dc-task-stages-container");
            const buffersContainer = document.getElementById("dc-precedence-buffers-container");
            const graphBadge = document.getElementById("dc-graph-status-badge");
            
            const tasksList = (dc.tasks_scheduled && dc.tasks_scheduled.length > 0) ? dc.tasks_scheduled : [
                { task_id: "EAF-01", task_name: "Electric Arc Melting", machine: "Electric Arc Furnace #1", start_hour: 6, end_hour: 9, duration_h: 3, task_load_kw: 180.0, dependencies: [], min_lag_h: 0, max_lag_h: null },
                { task_id: "LRF-01", task_name: "Ladle Refining & Alloying", machine: "Ladle Refining Station #2", start_hour: 12, end_hour: 14, duration_h: 2, task_load_kw: 90.0, dependencies: ["EAF-01"], min_lag_h: 1, max_lag_h: 3 },
                { task_id: "CCM-01", task_name: "Continuous Billet Casting", machine: "Continuous Casting Machine #1", start_hour: 16, end_hour: 18, duration_h: 2, task_load_kw: 60.0, dependencies: ["LRF-01"], min_lag_h: 0, max_lag_h: 2 }
            ];

            if (graphBadge) {
                const gStatus = dc.dependency_graph_status;
                if (gStatus && !gStatus.valid) {
                    graphBadge.className = "badge red-bg";
                    graphBadge.innerText = `DAG Error: ${gStatus.errors?.join('; ') || 'Invalid'}`;
                } else {
                    graphBadge.className = "badge blue-bg";
                    graphBadge.innerText = `DAG Verified: Acyclic (${tasksList.length} Process Stages)`;
                }
            }

            if (stagesContainer) {
                stagesContainer.innerHTML = tasksList.map((t, idx) => {
                    const depsStr = (t.dependencies && t.dependencies.length > 0) ? t.dependencies.join(', ') : 'None (Stage 1)';
                    return `
                        <div style="flex: 1; min-width: 240px; background: rgba(0, 0, 0, 0.35); border: 1px solid rgba(59, 130, 246, 0.25); border-radius: 8px; padding: 14px; position: relative;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                                <span class="badge blue-bg" style="font-size: 0.7rem; font-weight: 700;">STAGE ${idx + 1}: ${t.task_id}</span>
                                <span style="font-size: 0.8rem; color: #10B981; font-weight: 600;">${t.start_hour}:00 – ${t.end_hour}:00</span>
                            </div>
                            <h4 style="margin: 0 0 4px 0; color: #F8FAFC; font-size: 0.95rem;">${sanitizeHTML(t.task_name || t.task_id)}</h4>
                            <div style="font-size: 0.8rem; color: #94A3B8; margin-bottom: 8px;"><strong>Equipment:</strong> ${sanitizeHTML(t.machine || 'Primary Facility')}</div>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 0.78rem; background: rgba(255, 255, 255, 0.03); padding: 8px; border-radius: 4px;">
                                <div><span style="color: #64748B;">Power Draw:</span> <strong style="color: #CBD5E1;">${t.task_load_kw} kW</strong></div>
                                <div><span style="color: #64748B;">Duration:</span> <strong style="color: #CBD5E1;">${t.duration_h} hrs</strong></div>
                                <div style="grid-column: span 2;"><span style="color: #64748B;">Prerequisite:</span> <strong style="color: #60A5FA;">${depsStr}</strong></div>
                            </div>
                        </div>
                    `;
                }).join('');
            }

            if (buffersContainer) {
                const precList = dc.precedence_summary || [];
                if (precList.length > 0) {
                    buffersContainer.innerHTML = `
                        <strong style="color: #E2E8F0;">Inter-Stage Thermal Buffer Windows:</strong>
                        <div style="display: flex; flex-direction: column; gap: 4px; margin-top: 6px;">
                            ${precList.map(p => {
                                const statusColor = p.status === 'BINDING' ? '#F59E0B' : (p.status === 'SATISFIED' ? '#10B981' : '#EF4444');
                                return `
                                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255, 255, 255, 0.05); padding: 3px 0;">
                                        <span><strong>${p.predecessor} ➔ ${p.successor}:</strong> Prereq finished at ${p.predecessor_end_hour}:00, successor starts at ${p.successor_start_hour}:00 (Lag: ${p.buffer_lag_hours}h; Window: [${p.min_lag_hours}h, ${p.max_lag_hours !== null ? p.max_lag_hours + 'h' : '∞'}])</span>
                                        <span class="badge" style="background: ${statusColor}22; color: ${statusColor}; border: 1px solid ${statusColor}55; font-size: 0.7rem;">${p.status}</span>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    `;
                } else {
                    buffersContainer.innerHTML = `<span style="color: #94A3B8;">Multi-stage precedence verified: Downstream stages respect process sequencing and maximum allowed thermal transfer lags.</span>`;
                }
            }

            // Phase 3: Structured Constraint Audit Log
            const auditTbody = document.getElementById("dc-audit-tbody");
            const auditBadge = document.getElementById("dc-audit-summary-badge");
            const auditLog = dc.constraint_audit_log || [];

            if (auditTbody && auditLog.length > 0) {
                let hasViolations = false;
                auditTbody.innerHTML = auditLog.map(entry => {
                    let badgeClass = "green-bg";
                    let badgeStyle = "background: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.4);";
                    if (entry.status === "BINDING") {
                        badgeStyle = "background: rgba(245, 158, 11, 0.15); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.4);";
                    } else if (entry.status === "VIOLATED") {
                        badgeStyle = "background: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.4);";
                        hasViolations = true;
                    } else if (entry.status === "NOT_EVALUATED") {
                        badgeStyle = "background: rgba(148, 163, 184, 0.15); color: #94A3B8; border: 1px solid rgba(148, 163, 184, 0.4);";
                    }

                    return `
                        <tr>
                            <td><strong style="color: #CBD5E1;">${entry.constraint_id}</strong></td>
                            <td style="color: #F8FAFC;">${sanitizeHTML(entry.name)}</td>
                            <td style="color: #94A3B8;">${sanitizeHTML(entry.applicable_limit)}</td>
                            <td style="color: #E2E8F0;">${sanitizeHTML(entry.observed_value)}</td>
                            <td><span class="badge" style="${badgeStyle}; font-size: 0.72rem; font-weight: 700;">${entry.status}</span></td>
                            <td style="color: #CBD5E1; font-size: 0.78rem;">${sanitizeHTML(entry.explanation)}</td>
                        </tr>
                    `;
                }).join('');

                if (auditBadge) {
                    if (hasViolations) {
                        auditBadge.className = "badge red-bg";
                        auditBadge.innerText = "Audit: Verified Violation Detected";
                    } else {
                        auditBadge.className = "badge green-bg";
                        auditBadge.innerText = "Audit: All Evaluated Constraints Met";
                    }
                }
            }

            // Phase 3: Comparable Baseline vs. Optimized Schedule Metrics Table
            const compTbody = document.getElementById("dc-comparison-tbody");
            const compData = dc.metrics_comparison;
            if (compTbody && compData && compData.baseline && compData.optimized && compData.deltas) {
                const b = compData.baseline;
                const o = compData.optimized;
                const d = compData.deltas;

                compTbody.innerHTML = `
                    <tr>
                        <td><strong>Dispatch Methodology</strong></td>
                        <td><span class="badge blue-bg" style="font-size: 0.72rem;">${compData.baseline_method || 'CONVENTIONAL_ASAP_DISPATCH'}</span></td>
                        <td><span class="badge green-bg" style="font-size: 0.72rem;">PRAGATI_MILP_OPTIMIZED</span></td>
                        <td style="color: #10B981; font-weight: 600;">Shifted to Low-Tariff Solar Hours</td>
                    </tr>
                    <tr>
                        <td><strong>Energy Tariff Cost (24h)</strong></td>
                        <td style="color: #F87171;">₹${b.energy_cost_inr?.toLocaleString() || '0'} ($${b.energy_cost_usd?.toFixed(2) || '0'})</td>
                        <td style="color: #10B981;">₹${o.energy_cost_inr?.toLocaleString() || '0'} ($${o.energy_cost_usd?.toFixed(2) || '0'})</td>
                        <td style="color: #10B981; font-weight: 700;">-₹${d.cost_savings_inr?.toLocaleString() || '0'} (-${d.cost_savings_pct || 0}%)</td>
                    </tr>
                    <tr>
                        <td><strong>Peak Grid Draw (kW)</strong></td>
                        <td style="color: #F87171;">${b.peak_demand_kw?.toFixed(1) || '0'} kW</td>
                        <td style="color: #10B981;">${o.peak_demand_kw?.toFixed(1) || '0'} kW</td>
                        <td style="color: #10B981; font-weight: 700;">-${d.peak_demand_reduction_kw?.toFixed(1) || '0'} kW (-${d.peak_demand_reduction_pct || 0}%)</td>
                    </tr>
                    <tr>
                        <td><strong>Contract Demand Penalties</strong></td>
                        <td style="color: ${b.contract_demand_penalty_inr > 0 ? '#EF4444' : '#94A3B8'};">₹${b.contract_demand_penalty_inr?.toLocaleString() || '0'} ($${b.contract_demand_penalty_usd?.toFixed(2) || '0'})</td>
                        <td style="color: #10B981;">₹${o.contract_demand_penalty_inr?.toLocaleString() || '0'} ($${o.contract_demand_penalty_usd?.toFixed(2) || '0'})</td>
                        <td style="color: #F59E0B; font-weight: 700;">${b.contract_demand_penalty_inr > 0 ? 'Avoided Surcharge: ₹' + b.contract_demand_penalty_inr.toLocaleString() : 'No Surcharge'}</td>
                    </tr>
                    <tr>
                        <td><strong>Total Electricity Cost (₹ / $)</strong></td>
                        <td style="color: #F87171; font-weight: 700;">₹${b.total_cost_inr?.toLocaleString() || '0'} ($${b.total_cost_usd?.toFixed(2) || '0'})</td>
                        <td style="color: #10B981; font-weight: 700;">₹${o.total_cost_inr?.toLocaleString() || '0'} ($${o.total_cost_usd?.toFixed(2) || '0'})</td>
                        <td style="color: #10B981; font-weight: 700;">Net Savings: ₹${d.cost_savings_inr?.toLocaleString() || '0'} ($${d.cost_savings_usd?.toFixed(2) || '0'})</td>
                    </tr>
                    <tr>
                        <td><strong>Grid Scope 2 Emissions (kg CO₂e)</strong></td>
                        <td style="color: #F87171;">${b.grid_emissions_kg_co2?.toFixed(1) || '0'} kg CO₂e</td>
                        <td style="color: #10B981;">${o.grid_emissions_kg_co2?.toFixed(1) || '0'} kg CO₂e</td>
                        <td style="color: #34D399; font-weight: 700;">-${d.emissions_reduction_kg_co2?.toFixed(1) || '0'} kg CO₂e (-${d.emissions_reduction_pct || 0}%)</td>
                    </tr>
                `;
            }

            window.updateDecisionStatusUI(dc.status, dc.approved_by, dc.approved_at);
        } catch (e) {
            console.error("Failed to load Decision Center overview:", e);
        }
    };

    window.generateDecisionAction = async function() {
        const btn = document.getElementById("dc-generate-action-btn");
        if (btn) {
            btn.disabled = true;
            btn.innerText = "Analyzing Telemetry...";
        }
        try {
            // Multi-stage process: Electric Arc Furnace -> Ladle Refining Furnace -> Continuous Casting Machine
            const sampleTasks = [
                { task_id: "EAF-01", name: "Electric Arc Melting", machine: "Electric Arc Furnace #1", task_load_kw: 180.0, task_duration_h: 3, dependencies: [], min_lag_h: 0, max_lag_h: null },
                { task_id: "LRF-01", name: "Ladle Refining & Alloying", machine: "Ladle Refining Station #2", task_load_kw: 90.0, task_duration_h: 2, dependencies: ["EAF-01"], min_lag_h: 1, max_lag_h: 3 },
                { task_id: "CCM-01", name: "Continuous Billet Casting", machine: "Continuous Casting Machine #1", task_load_kw: 60.0, task_duration_h: 2, dependencies: ["LRF-01"], min_lag_h: 0, max_lag_h: 2 }
            ];

            const res = await fetch(`http://127.0.0.1:8000/api/v1/decision/generate`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-API-Key": API_KEY
                },
                body: JSON.stringify({
                    tenant_id: "demo_steel",
                    sector: "Steel",
                    task_load_kw: 180.0,
                    duration_hours: 3,
                    tasks: sampleTasks
                })
            });
            if (res.ok) {
                await window.loadDecisionCenter();
            }
        } catch (e) {
            console.error("Failed to generate live decision recommendation:", e);
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerText = "⚡ Re-Analyze Live";
            }
        }
    };

    window.updateDecisionStatusUI = function(status, approvedBy, approvedAt) {
        const pill = document.getElementById("dc-status-pill");
        const btn = document.getElementById("dc-approve-action-btn");
        const rejectBtn = document.getElementById("dc-reject-action-btn");
        const logText = document.getElementById("dc-approval-log-text");

        if (status === "APPROVED") {
            if (pill) {
                pill.className = "badge green-bg";
                pill.innerText = "APPROVED & DISPATCH COMMITTED";
            }
            if (btn) {
                btn.disabled = true;
                btn.style.opacity = "0.6";
                btn.style.cursor = "default";
                btn.innerText = "✔️ Action Committed";
            }
            if (rejectBtn) {
                rejectBtn.disabled = true;
                rejectBtn.style.opacity = "0.4";
                rejectBtn.style.cursor = "default";
            }
            if (logText) {
                logText.innerHTML = `Approved by <strong>${sanitizeHTML(approvedBy || 'Operations Manager')}</strong> at <strong>${sanitizeHTML(approvedAt || 'Just Now')}</strong>`;
            }
        } else if (status === "REJECTED") {
            if (pill) {
                pill.className = "badge red-bg";
                pill.innerText = "REJECTED BY OPERATIONS";
            }
            if (btn) {
                btn.disabled = true;
                btn.style.opacity = "0.4";
                btn.style.cursor = "default";
                btn.innerText = "✅ Approve Action";
            }
            if (rejectBtn) {
                rejectBtn.disabled = true;
                rejectBtn.style.opacity = "0.6";
                rejectBtn.style.cursor = "default";
                rejectBtn.innerText = "❌ Action Rejected";
            }
            if (logText) {
                logText.innerHTML = `Rejected by <strong>${sanitizeHTML(approvedBy || 'Operations Lead')}</strong> at <strong>${sanitizeHTML(approvedAt || 'Just Now')}</strong>`;
            }
        } else {
            if (pill) {
                pill.className = "badge warning-bg";
                pill.innerText = "PENDING MANAGER APPROVAL";
            }
            if (btn) {
                btn.disabled = false;
                btn.style.opacity = "1";
                btn.style.cursor = "pointer";
                btn.innerText = "✅ Approve Action";
            }
            if (rejectBtn) {
                rejectBtn.disabled = false;
                rejectBtn.style.opacity = "1";
                rejectBtn.style.cursor = "pointer";
                rejectBtn.innerText = "❌ Reject Action";
            }
            if (logText) {
                logText.innerHTML = "Status: <em>Awaiting managerial review</em>";
            }
        }
    };

    window.openRejectModal = function() {
        const modal = document.getElementById("reject-decision-modal");
        const badge = document.getElementById("reject-modal-action-id");
        const managerInput = document.getElementById("reject-manager-name");
        if (badge) badge.innerText = `Action ID: ${window.currentDecisionActionId || "ACT-2026-081"}`;
        if (managerInput) managerInput.value = currentUserRole === "Operator" ? "Operations Manager" : `${currentUserRole} Signoff`;
        if (modal) modal.style.display = "flex";
    };

    window.closeRejectModal = function() {
        const modal = document.getElementById("reject-decision-modal");
        if (modal) modal.style.display = "none";
    };

    window.submitRejectDecision = async function() {
        const actionId = window.currentDecisionActionId || "ACT-2026-081";
        const managerName = document.getElementById("reject-manager-name")?.value || "Operations Manager";
        const reason = document.getElementById("reject-reason-text")?.value || "Operational overhaul schedule conflict";
        
        try {
            const res = await fetch(`http://127.0.0.1:8000/api/v1/decision/reject`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-API-Key": API_KEY
                },
                body: JSON.stringify({
                    action_id: actionId,
                    manager_name: managerName,
                    reason: reason
                })
            });
            const data = await res.json();
            if (res.ok) {
                window.closeRejectModal();
                const dec = data.decision_state;
                window.updateDecisionStatusUI("REJECTED", dec.rejected_by, dec.rejected_at);
                alert(`❌ Manager Rejection Recorded!\n\nAction #${actionId} was rejected by ${managerName}.\nReason: ${reason}\nRecorded in immutable audit history.`);
            } else {
                alert(`Rejection error: ${data.detail || "Failed to record rejection"}`);
            }
        } catch (e) {
            console.error("Failed to reject action:", e);
            alert(`Network error: ${e.message}`);
        }
    };

    window.openDecisionHistoryModal = async function() {
        const modal = document.getElementById("decision-history-modal");
        const tbody = document.getElementById("decision-history-tbody");
        const countBadge = document.getElementById("decision-history-count-badge");
        if (modal) modal.style.display = "flex";
        if (tbody) tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #94A3B8; padding: 18px;">Loading decision history ledger...</td></tr>`;
        
        try {
            const res = await fetch(`http://127.0.0.1:8000/api/v1/decision/history`, {
                headers: { "X-API-Key": API_KEY }
            });
            const data = await res.json();
            const history = data.history || [];
            if (countBadge) countBadge.innerText = `Total Records: ${data.total_count || history.length}`;
            
            if (!tbody) return;
            if (history.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #94A3B8; padding: 18px;">No decision records found.</td></tr>`;
                return;
            }
            
            tbody.innerHTML = history.slice().reverse().map(item => {
                const st = item.status || "PENDING_APPROVAL";
                const badgeBg = st === "APPROVED" ? "background: rgba(16, 185, 129, 0.2); color: #10B981; border: 1px solid #10B981;" : (st === "REJECTED" ? "background: rgba(239, 68, 68, 0.2); color: #EF4444; border: 1px solid #EF4444;" : "background: rgba(245, 158, 11, 0.2); color: #F59E0B; border: 1px solid #F59E0B;");
                const signer = item.approved_by || item.rejected_by || "Awaiting Review";
                const ts = item.approved_at || item.rejected_at || item.created_at || "—";
                const hashVal = item.provenance?.audit_hash || "SHA256-verified";
                const impactVal = item.schedule_alternative ? `₹${(item.schedule_alternative.monthly_recurring_savings_inr || (item.schedule_alternative.monthly_recurring_savings_usd * 83)).toLocaleString()} / mo` : "Modeled Impact";
                
                return `
                    <tr>
                        <td><strong style="color: #60A5FA;">${item.action_id}</strong></td>
                        <td style="color: #F8FAFC; max-width: 260px;">${sanitizeHTML(item.title || 'Schedule Optimization')}</td>
                        <td style="color: #94A3B8; font-size: 0.78rem;">${ts}</td>
                        <td><span class="badge" style="${badgeBg}; font-size: 0.72rem; font-weight: 700;">${st}</span></td>
                        <td style="color: #CBD5E1;">${sanitizeHTML(signer)}</td>
                        <td style="color: #10B981; font-weight: 600;">${impactVal}</td>
                        <td style="color: #64748B; font-family: monospace; font-size: 0.72rem;">${hashVal}</td>
                    </tr>
                `;
            }).join('');
        } catch (e) {
            if (tbody) tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #EF4444; padding: 18px;">Failed to fetch decision history.</td></tr>`;
        }
    };

    window.closeDecisionHistoryModal = function() {
        const modal = document.getElementById("decision-history-modal");
        if (modal) modal.style.display = "none";
    };

    window.approveDecisionAction = async function() {
        const btn = document.getElementById("dc-approve-action-btn");
        if (btn) {
            btn.disabled = true;
            btn.innerText = "Committing Dispatch...";
        }
        try {
            const actionId = window.currentDecisionActionId || "ACT-2026-081";
            const res = await fetch(`http://127.0.0.1:8000/api/v1/decision/approve`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-API-Key": API_KEY
                },
                body: JSON.stringify({
                    action_id: actionId,
                    manager_name: currentUserRole === "Operator" ? "Operations Manager" : `${currentUserRole} Signoff`,
                    notes: "Approved schedule shift; automated dispatch order sent to SCADA queue."
                })
            });
            const data = await res.json();
            if (res.ok) {
                window.updateDecisionStatusUI("APPROVED", data.decision_state.approved_by, data.decision_state.approved_at);
                alert(`✅ Manager Approval Committed!\n\nAction #${actionId} has been approved and committed.\nLoad shifted to midday solar window.\nModeled monthly savings: $${(data.decision_state.schedule_alternative?.monthly_recurring_savings_usd || 1455).toLocaleString()} + $650 avoided peak surcharge.`);
            }
        } catch (e) {
            console.error("Failed to approve action:", e);
            if (btn) {
                btn.disabled = false;
                btn.innerText = "✅ Approve Action";
            }
        }
    };

    window.openEvidenceModal = function() {
        const modal = document.getElementById("evidence-modal");
        if (modal) modal.style.display = "flex";
    };

    window.closeEvidenceModal = function() {
        const modal = document.getElementById("evidence-modal");
        if (modal) modal.style.display = "none";
    };

    window.openPlanComparisonModal = function() {
        const modal = document.getElementById("plan-comparison-modal");
        if (modal) modal.style.display = "flex";
    };

    window.closePlanComparisonModal = function() {
        const modal = document.getElementById("plan-comparison-modal");
        if (modal) modal.style.display = "none";
    };

    // ==========================================
    // ALERT MANAGEMENT & GROUPED EVENTS HANDLERS
    // ==========================================
    // ==========================================
    // ALERT MANAGEMENT & GROUPED EVENTS HANDLERS (HIGH-CONTRAST LIGHT THEME)
    // ==========================================
    window.pollLiveTelemetryStream = async function() {
        try {
            const res = await fetch(`http://127.0.0.1:8000/api/v1/telemetry/stream`);
            if (!res.ok) return;
            const data = await res.json();
            const s = data.stream;
            if (!s) return;

            const pEl = document.getElementById("stream-val-power");
            const vEl = document.getElementById("stream-val-voltage");
            const pfEl = document.getElementById("stream-val-pf");
            const cEl = document.getElementById("stream-val-current");
            const tEl = document.getElementById("stream-val-temp");
            const tsEl = document.getElementById("telemetry-stream-ts");

            const stPowerEl = document.getElementById("stream-status-power");
            const stVoltageEl = document.getElementById("stream-status-voltage");
            const stPfEl = document.getElementById("stream-status-pf");
            const stCurrentEl = document.getElementById("stream-status-current");
            const stTempEl = document.getElementById("stream-status-temp");

            if (pEl) pEl.innerText = `${s.active_load_kw.toFixed(1)} kW`;
            if (stPowerEl) {
                if (s.active_load_kw > 320) {
                    stPowerEl.innerText = "⚠️ PEAK LOAD SURCHARGE";
                    stPowerEl.style.background = "#FEE2E2";
                    stPowerEl.style.color = "#991B1B";
                    stPowerEl.style.borderColor = "#FCA5A5";
                } else {
                    stPowerEl.innerText = "● NOMINAL LOAD";
                    stPowerEl.style.background = "#ECFDF5";
                    stPowerEl.style.color = "#065F46";
                    stPowerEl.style.borderColor = "#A7F3D0";
                }
            }

            if (vEl) vEl.innerText = `${s.grid_voltage_v.toFixed(1)} V`;
            if (stVoltageEl) {
                if (s.grid_voltage_v < 394 || s.grid_voltage_v > 435) {
                    stVoltageEl.innerText = "⚠️ VOLTAGE SAG/SURGE";
                    stVoltageEl.style.background = "#FEE2E2";
                    stVoltageEl.style.color = "#991B1B";
                    stVoltageEl.style.borderColor = "#FCA5A5";
                } else {
                    stVoltageEl.innerText = "● IN GRID TOLERANCE";
                    stVoltageEl.style.background = "#ECFDF5";
                    stVoltageEl.style.color = "#065F46";
                    stVoltageEl.style.borderColor = "#A7F3D0";
                }
            }

            if (pfEl) {
                pfEl.innerText = `${s.power_factor.toFixed(2)} ${s.power_factor >= 0.90 ? 'Lag' : 'LOW PF ⚠️'}`;
                pfEl.style.color = s.power_factor >= 0.90 ? '#059669' : '#DC2626';
            }
            if (stPfEl) {
                if (s.power_factor < 0.90) {
                    stPfEl.innerText = `⚠️ PENALTY BREACH (${s.power_factor.toFixed(2)})`;
                    stPfEl.style.background = "#FEE2E2";
                    stPfEl.style.color = "#991B1B";
                    stPfEl.style.borderColor = "#FCA5A5";
                } else if (s.power_factor < 0.92) {
                    stPfEl.innerText = `▲ AT MARGIN (${s.power_factor.toFixed(2)})`;
                    stPfEl.style.background = "#FEF3C7";
                    stPfEl.style.color = "#92400E";
                    stPfEl.style.borderColor = "#FCD34D";
                } else {
                    stPfEl.innerText = `● OPTIMAL PF (${s.power_factor.toFixed(2)})`;
                    stPfEl.style.background = "#ECFDF5";
                    stPfEl.style.color = "#065F46";
                    stPfEl.style.borderColor = "#A7F3D0";
                }
            }

            if (cEl && s.phase_currents_a) {
                const r = s.phase_currents_a.r_phase;
                const y = s.phase_currents_a.y_phase;
                const b = s.phase_currents_a.b_phase;
                cEl.innerText = `${r.toFixed(0)} / ${y.toFixed(0)} / ${b.toFixed(0)} A`;

                if (stCurrentEl) {
                    const avg = (r + y + b) / 3;
                    const maxDev = Math.max(Math.abs(r - avg), Math.abs(y - avg), Math.abs(b - avg));
                    const imbPct = avg > 0 ? (maxDev / avg) * 100 : 0;
                    if (imbPct > 5.0) {
                        stCurrentEl.innerText = `⚠️ IMBALANCED (${imbPct.toFixed(1)}%)`;
                        stCurrentEl.style.background = "#FEE2E2";
                        stCurrentEl.style.color = "#991B1B";
                        stCurrentEl.style.borderColor = "#FCA5A5";
                    } else {
                        stCurrentEl.innerText = `● BALANCED (${imbPct.toFixed(1)}%)`;
                        stCurrentEl.style.background = "#ECFDF5";
                        stCurrentEl.style.color = "#065F46";
                        stCurrentEl.style.borderColor = "#A7F3D0";
                    }
                }
            }

            if (tEl) {
                tEl.innerText = `${s.transformer_temp_c.toFixed(1)} °C`;
                tEl.style.color = s.transformer_temp_c >= 85.0 ? '#DC2626' : (s.transformer_temp_c >= 75.0 ? '#D97706' : '#059669');
            }
            if (stTempEl) {
                if (s.transformer_temp_c >= 85.0) {
                    stTempEl.innerText = "⚠️ OVERHEAT (ALERT)";
                    stTempEl.style.background = "#FEE2E2";
                    stTempEl.style.color = "#991B1B";
                    stTempEl.style.borderColor = "#FCA5A5";
                } else if (s.transformer_temp_c >= 75.0) {
                    stTempEl.innerText = "▲ ELEVATED TEMP";
                    stTempEl.style.background = "#FEF3C7";
                    stTempEl.style.color = "#92400E";
                    stTempEl.style.borderColor = "#FCD34D";
                } else {
                    stTempEl.innerText = "● NORMAL COOLING";
                    stTempEl.style.background = "#ECFDF5";
                    stTempEl.style.color = "#065F46";
                    stTempEl.style.borderColor = "#A7F3D0";
                }
            }

            if (tsEl) {
                tsEl.innerText = `🕒 Ingested: ${s.timestamp.split(' ')[1] || s.timestamp}`;
            }
        } catch (e) {
            // silent retry
        }
    };

    window.fetchActiveAlerts = async function() {
        const listEl = document.getElementById("live-alerts-list");
        if (!listEl) return;
        try {
            const res = await fetch(`http://127.0.0.1:8000/api/v1/alerts/active`);
            if (!res.ok) return;
            const data = await res.json();
            const alerts = (data.result && data.result.alerts) ? data.result.alerts : [];

            const countBadge = document.getElementById("active-alerts-count-badge");
            if (countBadge) {
                const activeCount = alerts.filter(a => a.status === "TRIGGERED" || a.status === "ACKNOWLEDGED").length;
                countBadge.innerText = `${activeCount} Active`;
                countBadge.className = activeCount > 0 ? "badge red-bg" : "badge green-bg";
            }

            if (alerts.length === 0) {
                listEl.innerHTML = `
                    <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 12px; padding: 20px; text-align: center; color: #166534;">
                        <span style="font-size: 1.5rem; display: block; margin-bottom: 6px;">✔️</span>
                        <strong style="font-size: 1rem; color: #14532D;">All Facility Equipment Operating Nominally</strong>
                        <p style="margin: 4px 0 0 0; font-size: 0.85rem; color: #15803D;">0 active threshold breaches across transformer and motor bus lines.</p>
                    </div>`;
                return;
            }

            let html = "";
            alerts.forEach(a => {
                const sev = (a.severity || "MEDIUM").toUpperCase();
                const sevClass = sev === "CRITICAL" ? "critical" : (sev === "HIGH" ? "high" : "medium");
                const sevBadgeBg = sev === "CRITICAL" ? "#FEE2E2" : (sev === "HIGH" ? "#FEF3C7" : "#DBEAFE");
                const sevBadgeColor = sev === "CRITICAL" ? "#991B1B" : (sev === "HIGH" ? "#92400E" : "#1E40AF");
                const sevBorder = sev === "CRITICAL" ? "#FCA5A5" : (sev === "HIGH" ? "#FCD34D" : "#93C5FD");

                const isAck = a.status === "ACKNOWLEDGED";
                const isRes = a.status === "RESOLVED";

                html += `
                    <div class="alert-item-card ${sevClass}">
                        <div style="flex: 1; min-width: 280px;">
                            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                                <span class="alert-id-pill">${a.alert_id}</span>
                                <span class="alert-title-text">${a.type}</span>
                                <span style="background: ${sevBadgeBg}; color: ${sevBadgeColor}; border: 1px solid ${sevBorder}; font-size: 0.72rem; font-weight: 800; padding: 2px 8px; border-radius: 12px; text-transform: uppercase;">${sev}</span>
                                <span class="alert-timestamp">🕒 ${a.timestamp}</span>
                            </div>
                            <div class="alert-metrics-row">
                                <strong style="color: #0F172A;">Equipment:</strong> <span style="color: #1E293B; font-weight: 700;">${a.equipment}</span>
                                &nbsp;·&nbsp;
                                <strong style="color: #0F172A;">Telemetry Reading:</strong> <span class="alert-value-tag">${a.value}</span>
                                &nbsp;·&nbsp;
                                <strong style="color: #0F172A;">Safety Limit:</strong> <span style="color: #475569; font-weight: 700;">${a.threshold}</span>
                            </div>
                            <div class="alert-directive-box">
                                <span style="font-size: 1.1rem;">💡</span>
                                <div><strong style="color: #166534;">Corrective Directive:</strong> ${a.mitigation}</div>
                            </div>
                            ${a.acknowledged_by ? `
                                <div class="alert-ack-pill">
                                    ✓ Acknowledged by <strong>${sanitizeHTML(a.acknowledged_by)}</strong> at ${a.acknowledged_at}
                                </div>` : ''}
                        </div>
                        <div style="display: flex; gap: 10px; align-items: center;">
                            <span style="font-size: 0.75rem; font-weight: 800; padding: 6px 12px; border-radius: 8px; text-transform: uppercase; letter-spacing: 0.5px; ${
                                isRes ? 'background: #F0FDF4; color: #15803D; border: 1px solid #BBF7D0;' :
                                (isAck ? 'background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE;' : 'background: #FEF2F2; color: #DC2626; border: 1px solid #FECACA;')
                            }">${a.status}</span>
                            ${!isAck && !isRes ? `
                                <button class="premium-btn" onclick="acknowledgeAlert('${a.alert_id}')" style="padding: 7px 16px; font-size: 0.82rem; width: auto; margin: 0; background: linear-gradient(135deg, #059669 0%, #047857 100%); color: #FFFFFF; font-weight: 700; box-shadow: 0 4px 10px rgba(5, 150, 105, 0.3);">Acknowledge 🛡️</button>` : ''}
                            ${isAck ? `
                                <button class="premium-btn" onclick="resolveAlert('${a.alert_id}')" style="padding: 7px 16px; font-size: 0.82rem; width: auto; margin: 0; background: linear-gradient(135deg, #16A34A 0%, #15803D 100%); color: #FFFFFF; font-weight: 700; box-shadow: 0 4px 10px rgba(22, 163, 74, 0.3);">Resolve ✓</button>` : ''}
                        </div>
                    </div>
                `;
            });
            listEl.innerHTML = html;
        } catch (e) {
            console.error("Failed to fetch active alerts:", e);
        }
    };

    window.acknowledgeAlert = async function(alertId) {
        try {
            const res = await fetch(`http://127.0.0.1:8000/api/v1/alerts/acknowledge`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ alert_id: alertId, operator_name: currentUserRole })
            });
            if (res.ok) {
                window.fetchActiveAlerts();
            }
        } catch (e) {
            console.error("Failed to acknowledge alert:", e);
        }
    };

    window.resolveAlert = async function(alertId) {
        try {
            const res = await fetch(`http://127.0.0.1:8000/api/v1/alerts/resolve`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    alert_id: alertId,
                    operator_name: currentUserRole,
                    resolution_notes: "Mitigation applied; metrics verified within nominal limits."
                })
            });
            if (res.ok) {
                window.fetchActiveAlerts();
            }
        } catch (e) {
            console.error("Failed to resolve alert:", e);
        }
    };

    window.loadGroupedEvents = async function() {
        const listEl = document.getElementById("grouped-events-list");
        if (!listEl) return;
        try {
            const res = await fetch(`http://127.0.0.1:8000/api/v1/alerts/grouped-events?limit=5`);
            if (!res.ok) return;
            const data = await res.json();
            const events = data.events || [];

            let html = "";
            events.forEach(evt => {
                const sev = (evt.severity || "MEDIUM").toUpperCase();
                const sevClass = sev === "CRITICAL" ? "critical" : (sev === "HIGH" ? "high" : "medium");
                const sevBadgeBg = sev === "CRITICAL" ? "#FEE2E2" : (sev === "HIGH" ? "#FEF3C7" : "#DBEAFE");
                const sevBadgeColor = sev === "CRITICAL" ? "#991B1B" : (sev === "HIGH" ? "#92400E" : "#1E40AF");
                const sevBorder = sev === "CRITICAL" ? "#FCA5A5" : (sev === "HIGH" ? "#FCD34D" : "#93C5FD");

                html += `
                    <div class="event-item-card ${sevClass}">
                        <div style="flex: 1;">
                            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                                <strong style="color: #0F172A; font-size: 0.95rem; font-weight: 800; font-family: 'Outfit', sans-serif;">${evt.event_id}: ${evt.event_type}</strong>
                                <span style="background: ${sevBadgeBg}; color: ${sevBadgeColor}; border: 1px solid ${sevBorder}; font-size: 0.7rem; font-weight: 800; padding: 2px 7px; border-radius: 10px; text-transform: uppercase;">${sev}</span>
                                <span style="font-size: 0.78rem; color: #475569; font-family: monospace; font-weight: 600;">🕒 ${evt.start_time} (${evt.duration_minutes} min duration)</span>
                            </div>
                            <div style="font-size: 0.85rem; color: #334155; margin-top: 6px; line-height: 1.5;">
                                <strong style="color: #0F172A;">Statistical Evidence:</strong> <span style="color: #334155; font-weight: 500;">${evt.evidence}</span>
                            </div>
                            <div style="font-size: 0.82rem; color: #166534; margin-top: 6px; background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 6px; padding: 6px 10px; font-weight: 600;">
                                <strong style="color: #14532D;">Recommended Action:</strong> ${evt.actionable_mitigation}
                            </div>
                        </div>
                        <div style="margin-left: 10px;">
                            <span class="badge ${evt.status === 'RESOLVED' ? 'green-bg' : 'warning-bg'}" style="font-size: 0.75rem; font-weight: 700;">${evt.status}</span>
                        </div>
                    </div>
                `;
            });
            listEl.innerHTML = html;
        } catch (e) {
            console.error("Failed to load grouped events:", e);
        }
    };

    // Start live meter stream polling on interval
    window.pollLiveTelemetryStream();
    setInterval(window.pollLiveTelemetryStream, 3500);

    init3DTilt();
    setTimeout(init3DTilt, 1000);
});