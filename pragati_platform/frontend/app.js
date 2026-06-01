// PRAGATI AI Web Dashboard Controller
const API_BASE = "http://127.0.0.1:8000/api";

// State variables to hold Chart instances
let telemetryChart = null;
let forecastChart = null;
let scheduleChart = null;

// Application Initialization
document.addEventListener("DOMContentLoaded", () => {
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
});

// Sidebar Navigation Control
function initTabNavigation() {
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
        }
    };
    
    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const targetTab = item.getAttribute("data-tab");
            
            // Toggle active classes
            navItems.forEach(n => n.classList.remove("active"));
            tabPanels.forEach(p => p.classList.remove("active"));
            
            item.classList.add("active");
            document.getElementById(targetTab).classList.add("active");
            
            // Set dynamic header titles
            if (tabMetadata[targetTab]) {
                tabTitle.innerText = tabMetadata[targetTab].title;
                tabSubtitle.innerText = tabMetadata[targetTab].sub;
            }
            
            // Specific chart resizing on tab reveal
            if (targetTab === "tab-forecasting" && forecastChart) {
                forecastChart.resize();
            } else if (targetTab === "tab-scheduler" && scheduleChart) {
                scheduleChart.resize();
            }
        });
    });
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
    
    btn.disabled = true;
    btn.innerText = "Training models, compiling curves...";
    
    try {
        const res = await fetch(`${API_BASE}/forecast`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ hours: hours })
        });
        
        if (!res.ok) throw new Error("Forecasting calculations failed");
        
        const data = await res.json();
        
        // Update metrics
        document.getElementById("metric-prophet-rmse").innerText = `${data.metrics.prophet_rmse} kW`;
        document.getElementById("metric-rf-rmse").innerText = `${data.metrics.rf_rmse} kW`;
        
        const bestBadge = document.getElementById("metric-best-model");
        bestBadge.innerText = data.metrics.best_model;
        
        // Render forecast chart
        renderForecastChart(data);
    } catch (e) {
        alert("Failed to compile forecast predictions.");
    } finally {
        btn.disabled = false;
        btn.innerText = "Run Forecasting Models";
    }
}

function renderForecastChart(data) {
    const ctx = document.getElementById("forecastChart").getContext("2d");
    if (forecastChart) {
        forecastChart.destroy();
    }
    
    forecastChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.timestamps.map(t => t.split(" ")[1] ? t.split(" ")[1].substring(0, 5) : t),
            datasets: [
                {
                    label: 'Actual Telemetry (kWh)',
                    data: data.actuals,
                    borderColor: '#94A3B8',
                    borderWidth: 2,
                    borderDash: [3, 3],
                    tension: 0.1,
                    fill: false
                },
                {
                    label: 'Meta Prophet (Forecast)',
                    data: data.prophet_forecast,
                    borderColor: '#10B981', // Emerald
                    borderWidth: 2.5,
                    tension: 0.3,
                    fill: false
                },
                {
                    label: 'Random Forest (Forecast)',
                    data: data.rf_forecast,
                    borderColor: '#8B5CF6', // Violet
                    borderWidth: 2,
                    tension: 0.2,
                    fill: false
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
                    title: { display: true, text: 'Active Power (kWh)', color: '#94A3B8' },
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
    
    try {
        const res = await fetch(`${API_BASE}/schedule`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                task_load_kw: load,
                task_duration_h: duration,
                solar_capacity_kw: solar,
                environmental_weight: weight
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
    
    // Fill baseline task run (starts at 9 AM)
    const baseStart = data.baseline.start_hour;
    for (let k = 0; k < data.baseline.details.length; k++) {
        const h = (baseStart + k) % 24;
        baselineDraw[h] = data.baseline.details[k].grid_draw_kwh;
    }
    
    // Fill optimized task run
    const optStart = data.best_start_hour;
    for (let k = 0; k < data.best_hourly_details.length; k++) {
        const h = (optStart + k) % 24;
        optimizedDraw[h] = data.best_hourly_details[k].grid_draw_kwh;
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
                    borderWidth: 1
                },
                {
                    label: 'Optimized Shift Grid Draw (kW)',
                    data: optimizedDraw,
                    backgroundColor: 'rgba(16, 185, 129, 0.4)', // Muted Emerald
                    borderColor: '#10B981',
                    borderWidth: 1
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
    } catch (e) {
        console.error(e);
    }
}

// Tab 6: AI Copilot Chat Engine
async function sendCopilotMessage() {
    const input = document.getElementById("chat-input");
    const container = document.getElementById("chat-messages-container");
    const msg = input.value.trim();
    
    if (!msg) return;
    
    // Add user message bubble
    const userBubble = document.createElement("div");
    userBubble.className = "message user";
    userBubble.innerHTML = `<div class="message-content">${msg}</div>`;
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