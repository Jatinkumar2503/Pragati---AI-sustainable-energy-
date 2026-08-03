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
        loadTelemetry(parseInt(e.target.value));
    });
    
    document.getElementById("run-forecast-btn").addEventListener("click", () => {
        runForecasting();
    });
    
    document.getElementById("forecast-hours").addEventListener("input", (e) => {
        document.getElementById("forecast-hours-val").innerText = e.target.value;
    });
    
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

// Tab 1: Load and Render Telemetry Data
async function loadTelemetry(days = 7) {
    try {
        const res = await fetch(`${API_BASE}/telemetry?days=${days}`);
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
    
    telemetryChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.timestamps.map(t => t.split(" ")[1] ? t.split(" ")[1].substring(0, 5) : t),
            datasets: [
                {
                    label: 'Grid Load (kW)',
                    data: data.usage_kwh,
                    borderColor: '#10B981', // Emerald
                    backgroundColor: 'rgba(16, 185, 129, 0.05)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true,
                    yAxisID: 'y'
                },
                {
                    label: 'Power Factor (%)',
                    data: data.power_factor_lagging,
                    borderColor: '#06B6D4', // Cyan
                    borderWidth: 1.5,
                    borderDash: [5, 5],
                    tension: 0.1,
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
                    ticks: { color: '#64748B', maxTicksLimit: 12 }
                },
                y: {
                    title: { display: true, text: 'Active Power (kW)', color: '#94A3B8' },
                    grid: { color: 'rgba(255, 255, 255, 0.04)' },
                    ticks: { color: '#64748B' }
                },
                y1: {
                    position: 'right',
                    title: { display: true, text: 'Power Factor (%)', color: '#94A3B8' },
                    grid: { drawOnChartArea: false },
                    ticks: { color: '#64748B', min: 40, max: 100 }
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
                    borderColor: '#F59E0B', // Amber
                    backgroundColor: 'rgba(245, 158, 11, 0.05)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true,
                    yAxisID: 'y'
                },
                {
                    label: 'Grid Voltage (V)',
                    data: data.voltage_v,
                    borderColor: '#EF4444', // Red
                    borderWidth: 1.5,
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
                    labels: { color: '#94A3B8', font: { family: 'Inter' } }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.04)' },
                    ticks: { color: '#64748B', maxTicksLimit: 12 }
                },
                y: {
                    title: { display: true, text: 'THD (%)', color: '#94A3B8' },
                    grid: { color: 'rgba(255, 255, 255, 0.04)' },
                    ticks: { color: '#64748B' }
                },
                y1: {
                    position: 'right',
                    title: { display: true, text: 'Voltage (V)', color: '#94A3B8' },
                    grid: { drawOnChartArea: false },
                    ticks: { color: '#64748B', min: 380, max: 440 }
                }
            }
        }
    });
}

// Tab 2: Load and Display Anomalies Table
async function loadAnomalies() {
    const tableBody = document.querySelector("#anomalies-table tbody");
    try {
        const res = await fetch(`${API_BASE}/anomalies`);
        if (!res.ok) throw new Error("Failed to fetch anomalies");
        
        const anomalies = await res.json();
        
        // Update Anomaly badges
        document.getElementById("kpi-anomalies-count").innerText = anomalies.length;
        document.getElementById("anomalies-badge").innerText = `${anomalies.length} Flagged`;
        
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
            body: JSON.stringify({ hours: hours, backtest_folds: folds })
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
            labels: data.timestamps.map(t => t.split(" ")[1] ? t.split(" ")[1].substring(0, 5) : t),
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
                pf_penalty_mult: pf_penalty_mult
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
                battery_capacity_kwh: battery
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
        document.getElementById("twin-val-payback").innerText = `${data.simple_payback_period_years} Years`;
        
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
    
    const years = Array.from({ length: 20 }, (_, i) => `Yr ${i + 1}`);
    
    twinCashFlowChart = new Chart(ctx.getContext("2d"), {
        type: 'bar',
        data: {
            labels: years,
            datasets: [{
                label: 'Annual Net Cash Flow ($)',
                data: cashFlows,
                backgroundColor: cashFlows.map(val => val >= 0 ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)'),
                borderColor: cashFlows.map(val => val >= 0 ? '#10B981' : '#EF4444'),
                borderWidth: 1.5,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.04)' },
                    ticks: { color: '#94A3B8' }
                },
                y: {
                    title: { display: true, text: 'Net Cash Flow ($)', color: '#94A3B8' },
                    grid: { color: 'rgba(255, 255, 255, 0.04)' },
                    ticks: { color: '#64748B' }
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
                load_shift_pct: shift
            })
        });

        if (!res.ok) throw new Error("Digital Twin simulation failed");

        const data = await res.json();
        const sim = data.result.simulation;

        // Update DOM metrics
        if (document.getElementById("twin-val-gen")) {
            document.getElementById("twin-val-gen").innerText = `${sim.energy_metrics.monthly_solar_generation_kwh.toLocaleString()} kWh/mo`;
        }
        if (document.getElementById("twin-val-savings")) {
            document.getElementById("twin-val-savings").innerText = `₹${sim.financial_metrics.annual_savings_inr.toLocaleString()}`;
        }
        if (document.getElementById("twin-val-co2")) {
            document.getElementById("twin-val-co2").innerText = `${sim.carbon_metrics.annual_co2_reduction_tons} Tons CO₂`;
        }

        if (data.result.xai_card) {
            renderXAICardDrawer(data.result.xai_card);
        }
    } catch (e) {
        console.error("Digital Twin error:", e);
    } finally {
        if (btn) btn.innerText = "Run Scenario Simulation ☀️";
    }
}

async function openAuditLogDrawer() {
    const drawer = document.getElementById("audit-log-drawer");
    const container = document.getElementById("audit-log-list");
    if (drawer) drawer.style.display = "flex";
    if (!container) return;

    try {
        const res = await fetch(`${API_BASE}/v1/audit/logs`);
        const data = await res.json();

        let html = "";
        data.logs.forEach(log => {
            let statusColor = log.status === "APPROVED" ? "#10B981" : "#F59E0B";
            html += `
                <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 14px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-weight: 700; color: #E2E8F0; font-size: 0.9rem;">${log.id} — ${log.agent}</span>
                        <span style="font-size: 0.75rem; background: ${statusColor}22; color: ${statusColor}; border: 1px solid ${statusColor}55; padding: 2px 8px; border-radius: 4px; font-weight: 600;">${log.status}</span>
                    </div>
                    <div style="font-size: 0.85rem; color: #CBD5E1; margin-bottom: 4px;">${log.action}</div>
                    <div style="font-size: 0.8rem; color: #10B981; font-weight: 600;">Impact: ${log.impact}</div>
                    <div style="font-size: 0.75rem; color: #64748B; margin-top: 6px;">🕒 ${log.timestamp} • Authorized by ${log.approved_by}</div>
                </div>
            `;
        });
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = `<p style="color: #EF4444;">Failed to load audit logs.</p>`;
    }
}

function closeAuditLogDrawer() {
    const drawer = document.getElementById("audit-log-drawer");
    if (drawer) drawer.style.display = "none";
}

// Day 4: Real-time Telemetry Stream & Alert Center
async function fetchActiveAlerts() {
    const container = document.getElementById("live-alerts-list");
    if (!container) return;

    try {
        const res = await fetch(`${API_BASE}/v1/alerts/active`);
        const data = await res.json();
        const alerts = data.result.alerts || [];

        if (alerts.length === 0) {
            container.innerHTML = `<p style="color: #10B981; font-weight: 500;">✓ All facility meters nominal. 0 active operational alerts.</p>`;
            return;
        }

        let html = "";
        alerts.forEach(a => {
            let badgeBg = a.severity === "CRITICAL" ? "#EF4444" : (a.severity === "HIGH" ? "#F97316" : "#F59E0B");
            let isAck = a.status === "ACKNOWLEDGED";
            html += `
                <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 14px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                            <span style="background: ${badgeBg}; color: #FFF; font-size: 0.7rem; font-weight: 800; padding: 2px 6px; border-radius: 4px;">${a.severity}</span>
                            <strong style="color: #F8FAFC; font-size: 0.95rem;">${a.type} — ${a.equipment}</strong>
                        </div>
                        <div style="font-size: 0.85rem; color: #CBD5E1;">Value: <span style="color: #EF4444; font-weight: 700;">${a.value}</span> (Safety Limit: ${a.threshold})</div>
                        <div style="font-size: 0.8rem; color: #10B981; margin-top: 4px;">Mitigation: ${a.mitigation}</div>
                    </div>
                    <div>
                        ${isAck 
                            ? `<span style="color: #10B981; font-size: 0.8rem; font-weight: 600;">✓ Acknowledged by ${a.acknowledged_by}</span>`
                            : `<button class="premium-btn" style="padding: 6px 12px; font-size: 0.8rem; background: #EF4444;" onclick="acknowledgeAlert('${a.alert_id}')">Acknowledge Alert 🚨</button>`
                        }
                    </div>
                </div>
            `;
        });
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = `<p style="color: #EF4444;">Failed to fetch live alerts.</p>`;
    }
}

async function acknowledgeAlert(alertId) {
    try {
        const res = await fetch(`${API_BASE}/v1/alerts/acknowledge`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ alert_id: alertId, operator_name: "Shift Operator" })
        });
        if (res.ok) {
            fetchActiveAlerts();
        }
    } catch (e) {
        console.error("Alert acknowledgment failed:", e);
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
    init3DTilt();
    setTimeout(init3DTilt, 1000);
});