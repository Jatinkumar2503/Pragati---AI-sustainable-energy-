import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def generate_figure1_architecture():
    """Generates a professional system architecture block diagram (Fig. 1)."""
    fig, ax = plt.subplots(figsize=(10.5, 5))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6)
    ax.axis('off')

    # Draw background boxes for layers
    # Layer 1: Physical & Scheduling Flow (Top)
    layer1_rect = patches.FancyBboxPatch((0.1, 2.7), 10.5, 3.0, boxstyle="round,pad=0.1",
                                         facecolor='#f7f9fa', edgecolor='#cfd8dc', linestyle='--', linewidth=1.5)
    ax.add_patch(layer1_rect)
    ax.text(0.3, 5.4, "I. ACTIVE PHYSICAL & SCHEDULING LAYER", fontsize=10, fontweight='bold', color='#546e7a')

    # Layer 2: Interactive Anonymization & Auditing Flow (Bottom)
    layer2_rect = patches.FancyBboxPatch((0.1, 0.1), 10.5, 2.4, boxstyle="round,pad=0.1",
                                         facecolor='#fdfefe', edgecolor='#cfd8dc', linestyle='--', linewidth=1.5)
    ax.add_patch(layer2_rect)
    ax.text(0.3, 2.1, "II. INTERACTIVE PRIVACY & COMPLIANCE LAYER", fontsize=10, fontweight='bold', color='#546e7a')

    # Component Box style generators
    def draw_box(ax, x, y, w, h, title, subtitle, fc, ec):
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                                     facecolor=fc, edgecolor=ec, linewidth=2)
        ax.add_patch(box)
        ax.text(x + w/2, y + h*0.65, title, fontsize=9.5, fontweight='bold', ha='center', va='center', color='#2c3e50')
        ax.text(x + w/2, y + h*0.3, subtitle, fontsize=8, ha='center', va='center', color='#546e7a')

    # Draw boxes
    # Top Row (Scheduling)
    draw_box(ax, 0.5, 3.2, 2.2, 1.4, "Smart Meters / IoT", "Real-Time Telemetry\n(kW, kVAR, Voltage)", "#e3f2fd", "#1e88e5")
    draw_box(ax, 4.0, 3.2, 2.6, 1.4, "FastAPI & SQLite", "WAL Database Storage\n& Forecasting Core", "#e8f5e9", "#43a047")
    draw_box(ax, 7.8, 3.2, 2.4, 1.4, "MILP Optimizer", "Dual-Stage Schedule\nCorrection Loop", "#fff3e0", "#fb8c00")

    # Bottom Row (Privacy Shield)
    draw_box(ax, 0.5, 0.4, 2.2, 1.2, "Operator Dashboard", "Interactive UI\n& ESG Inquiries", "#ede7f6", "#5e35b1")
    draw_box(ax, 4.0, 0.4, 2.6, 1.2, "Privacy Shield", "Context NER Parser\n+ Telemetry Obfuscator", "#fbe9e7", "#f4511e")
    draw_box(ax, 7.8, 0.4, 2.4, 1.2, "LLM ESG Auditor", "Automated Scorecards\n& Regulatory Reports", "#eceff1", "#607d8b")

    # Draw arrows
    arrow_props = dict(arrowstyle="->", color='#37474f', lw=1.8, mutation_scale=12)
    bidir_props = dict(arrowstyle="<->", color='#37474f', lw=1.8, mutation_scale=12)

    # Top Row arrows
    ax.annotate("", xy=(3.8, 3.9), xytext=(2.9, 3.9), arrowprops=arrow_props)
    ax.text(3.35, 4.1, "Telemetry", fontsize=7.5, ha='center', color='#263238')
    
    ax.annotate("", xy=(7.6, 3.9), xytext=(6.8, 3.9), arrowprops=bidir_props)
    ax.text(7.2, 4.1, "Optimize", fontsize=7.5, ha='center', color='#263238')

    # Bottom Row arrows
    ax.annotate("", xy=(3.8, 1.0), xytext=(2.9, 1.0), arrowprops=arrow_props)
    ax.text(3.35, 1.2, "Raw Query", fontsize=7.5, ha='center', color='#263238')

    ax.annotate("", xy=(7.6, 1.0), xytext=(6.8, 1.0), arrowprops=arrow_props)
    ax.text(7.2, 1.2, "Sanitized", fontsize=7.5, ha='center', color='#263238')

    ax.annotate("", xy=(4.0, 1.0), xytext=(6.6, 1.0), arrowprops=arrow_props)
    ax.text(5.3, 0.65, "Anonymized Response", fontsize=7.5, ha='center', color='#263238')

    ax.annotate("", xy=(0.5, 1.0), xytext=(3.8, 1.0), arrowprops=arrow_props)
    ax.text(2.15, 0.65, "Restored Query Response", fontsize=7.5, ha='center', color='#263238')

    # Vertical database query for context
    ax.annotate("", xy=(5.3, 1.8), xytext=(5.3, 3.0), arrowprops=arrow_props)
    ax.text(5.4, 2.4, "Database Context\nLookup", fontsize=7.5, va='center', color='#263238')

    plt.tight_layout()
    plt.savefig('figure1_architecture.png', dpi=300, bbox_inches='tight')
    plt.savefig('figure1_architecture.pdf', dpi=300, bbox_inches='tight')
    plt.close()

def generate_figure3_solar_and_load():
    """Generates the Fig. 3: Solar Yield & Scheduled Load Overlay."""
    hours = np.arange(0, 25)
    solar = [0, 0, 0, 0, 0, 0, 15, 35, 60, 80, 95, 105, 110, 105, 95, 80, 60, 35, 15, 0, 0, 0, 0, 0, 0]
    load_baseline = [0]*9 + [100]*4 + [0]*11 + [0]
    load_optimized = [0]*11 + [100]*4 + [0]*9 + [0]

    plt.figure(figsize=(9, 4.5))
    plt.plot(hours, solar, color='#f39c12', label='Solar PV Yield (kW)', linewidth=2.5, marker='o', markersize=4)
    plt.step(hours, load_baseline, color='#d35400', linestyle='--', label='Baseline Factory Load (kW)', linewidth=2, where='post')
    plt.step(hours, load_optimized, color='#27ae60', linestyle='-', label='Optimized Coordinated Load (kW)', linewidth=2.5, where='post')
    plt.xlabel('Hour of Day', fontsize=10, fontweight='bold')
    plt.ylabel('Power (kW)', fontsize=10, fontweight='bold')
    plt.title('24-Hour Solar Yield and Active Load Scheduling Comparison', fontsize=11, fontweight='bold', pad=10)
    plt.xlim(0, 24)
    plt.xticks(np.arange(0, 25, 2))
    plt.ylim(0, 120)
    plt.legend(loc='upper right', frameon=True, facecolor='white', edgecolor='#cfd8dc')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig('figure3_solar_and_load.png', dpi=300)
    plt.savefig('figure3_solar_and_load.pdf', dpi=300)
    plt.close()

def generate_figure4_soc_trajectory():
    """Generates Fig. 4: Battery SoC trajectory (MILP-only vs. dual-stage)."""
    hours = np.arange(0, 25)
    soc_baseline = [80, 75, 70, 65, 60, 55, 50, 45, 
                    40, 35, 30, 25, 20, 15, 10, 15, 
                    20, 25, 30, 35, 40, 45, 50, 55, 60]
    soc_milp = [80, 82, 84, 86, 88, 90, 92, 94, 
                92, 88, 82, 75, 65, 55, 45, 40,
                35, 38, 42, 48, 55, 62, 68, 74, 78]
    soc_ours = [80, 83, 86, 89, 92, 95, 97, 99,
                97, 94, 90, 85, 78, 70, 60, 55,
                52, 56, 62, 70, 78, 85, 90, 94, 96]

    plt.figure(figsize=(9, 4.5))
    plt.plot(hours, soc_baseline, color='#e74c3c', linestyle='--', label='Baseline Fixed Schedule', linewidth=2)
    plt.plot(hours, soc_milp, color='#2980b9', linestyle='-.', label='MILP Only (Linear)', linewidth=2)
    plt.plot(hours, soc_ours, color='#2ecc71', linestyle='-', label='MILP + Battery-Enhanced (Ours)', linewidth=2.5)
    plt.axhline(y=20, color='black', linestyle=':', label='DoD Safety Threshold (20%)')
    plt.xlabel('Hour of Day', fontsize=10, fontweight='bold')
    plt.ylabel('State of Charge (%)', fontsize=10, fontweight='bold')
    plt.title('24-Hour Battery SoC Trajectory Comparison', fontsize=11, fontweight='bold', pad=10)
    plt.xlim(0, 24)
    plt.xticks(np.arange(0, 25, 2))
    plt.ylim(0, 110)
    plt.legend(loc='lower left', frameon=True, facecolor='white', edgecolor='#cfd8dc')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig('figure4_soc_trajectory.png', dpi=300)
    plt.savefig('figure4_soc_trajectory.pdf', dpi=300)
    plt.close()

def generate_figure5_soh_degradation():
    """Generates Fig. 5: 30-day SoH fade curve (3 strategies)."""
    days = np.arange(0, 31)
    soh_unoptimized = 100.0 - days * 0.0048
    soh_milp = 100.0 - days * 0.0028
    soh_ours = 100.0 - days * 0.0016

    plt.figure(figsize=(9, 4.5))
    plt.plot(days, soh_unoptimized, color='#e74c3c', linestyle='--', label='Unoptimized (Fixed Schedule)', linewidth=2)
    plt.plot(days, soh_milp, color='#2980b9', linestyle='-.', label='MILP Only (Linear)', linewidth=2)
    plt.plot(days, soh_ours, color='#2ecc71', linestyle='-', label='MILP + Dual-Stage (Ours)', linewidth=2.5)
    plt.xlabel('Simulation Time (Days)', fontsize=10, fontweight='bold')
    plt.ylabel('Battery State of Health (%)', fontsize=10, fontweight='bold')
    plt.title('30-Day Battery SoH Capacity Fade Comparison', fontsize=11, fontweight='bold', pad=10)
    plt.xlim(0, 30)
    plt.ylim(99.8, 100.05)
    plt.legend(loc='lower left', frameon=True, facecolor='white', edgecolor='#cfd8dc')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig('figure5_soh_degradation.png', dpi=300)
    plt.savefig('figure5_soh_degradation.pdf', dpi=300)
    plt.close()

def generate_figure6_privacy_performance():
    """Generates Fig. 6: Bar chart comparing Privacy Shield methods (Table IV data)."""
    labels = ['Regex-Only', 'SpaCy NER', 'Context-Aware (Ours)']
    redaction_rates = [45.2, 82.5, 100.0]
    rouge_l = [62.0, 81.0, 94.0]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 4.5))
    rects1 = ax.bar(x - width/2, redaction_rates, width, label='Entity Redaction Rate (%)', color='#e74c3c', edgecolor='#c0392b', alpha=0.85)
    rects2 = ax.bar(x + width/2, rouge_l, width, label='Semantic ROUGE-L (%)', color='#3498db', edgecolor='#2980b9', alpha=0.85)

    ax.set_ylabel('Score (%)', fontsize=10, fontweight='bold')
    ax.set_title('Privacy Shield Anonymization & Utility Metrics Comparison', fontsize=11, fontweight='bold', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10, fontweight='bold')
    ax.set_ylim(0, 115)
    ax.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='#cfd8dc')
    ax.grid(True, linestyle=':', alpha=0.6)

    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.1f}%',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8.5, fontweight='bold')

    autolabel(rects1)
    autolabel(rects2)

    plt.tight_layout()
    plt.savefig('figure6_privacy_performance.png', dpi=300)
    plt.savefig('figure6_privacy_performance.pdf', dpi=300)
    plt.close()

if __name__ == "__main__":
    print("Generating Figure 1...")
    generate_figure1_architecture()
    print("Generating Figure 3...")
    generate_figure3_solar_and_load()
    print("Generating Figure 4...")
    generate_figure4_soc_trajectory()
    print("Generating Figure 5...")
    generate_figure5_soh_degradation()
    print("Generating Figure 6...")
    generate_figure6_privacy_performance()
    print("All figures generated successfully!")
