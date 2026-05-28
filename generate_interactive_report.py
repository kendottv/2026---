"""
Generate a single self-contained interactive HTML dashboard for the
「打炒房與升息下，蛋黃區 vs 蛋白區房價分化」視覺化期末報告

Features (per user request):
- Standalone .html (double-click to open)
- 中度互動：時間範圍滑桿、hover、切換指標
- 可多選個別行政區即時 overlay 比較
- 嚴格使用預先固定的 9 區蛋黃定義
- 清楚標註 2022 升息斷點與資料來源
"""

import json
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

# ============== CONFIG ==============
DISTRICT_CSV = "district_yearly_stats.csv"
EGG_PROTEIN_CSV = "egg_protein_yearly.csv"
EGG_DEF_JSON = "egg_yolk_definition.json"
OUTPUT_HTML = "interactive_housing_report.html"

# Color scheme (professional, colorblind friendly)
COLOR_EGG = "#E63946"       # Strong red for 蛋黃區 (premium)
COLOR_PROTEIN = "#457B9D"   # Calm blue for 蛋白區
COLOR_2022 = "#F4A261"      # Orange for policy line
COLOR_GRID = "#E9ECEF"
# ====================================


def load_data():
    df_district = pd.read_csv(DISTRICT_CSV, encoding="utf-8-sig")
    df_ep = pd.read_csv(EGG_PROTEIN_CSV, encoding="utf-8-sig")

    with open(EGG_DEF_JSON, encoding="utf-8") as f:
        egg_def = json.load(f)

    return df_district, df_ep, egg_def


def build_dashboard(df_district, df_ep, egg_def):
    years = [int(y) for y in sorted(df_ep["年份"].unique())]
    min_year, max_year = min(years), max(years)

    # Prepare egg vs protein series (for main lines)
    egg = df_ep[df_ep["蛋黃區"] == True].sort_values("年份")
    protein = df_ep[df_ep["蛋黃區"] == False].sort_values("年份")

    # All districts for the multi-select
    all_districts = sorted(df_district["行政區"].unique())
    egg_districts = egg_def["蛋黃區"]

    # Pre-compute per-district traces data (will be controlled by JS checkboxes)
    district_data = {}
    for dist in all_districts:
        d = df_district[df_district["行政區"] == dist].sort_values("年份")
        district_data[dist] = {
            "years": d["年份"].tolist(),
            "price": d["單價中位數"].tolist(),
            "count": d["交易筆數"].tolist(),
            "is_egg": bool(d["蛋黃區"].iloc[0]),
        }

    # ========== BUILD FIGURE ==========
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.50, 0.25, 0.25],
        subplot_titles=(
            "單價中位數時間序列（蛋黃區 vs 蛋白區）",
            "蛋黃區相對蛋白區的單價差距（元/坪）",
            "每年交易筆數對比"
        )
    )

    # Row 1: Main price lines
    # Egg yolk aggregate (thick)
    fig.add_trace(go.Scatter(
        x=egg["年份"], y=egg["單價中位數"],
        mode="lines+markers",
        name="蛋黃區總體（預先固定9區）",
        line=dict(color=COLOR_EGG, width=4),
        marker=dict(size=8),
        hovertemplate="%{x}年<br>蛋黃區中位數: %{y:,.0f} 元/坪<extra></extra>"
    ), row=1, col=1)

    # Protein aggregate (thick)
    fig.add_trace(go.Scatter(
        x=protein["年份"], y=protein["單價中位數"],
        mode="lines+markers",
        name="蛋白區總體",
        line=dict(color=COLOR_PROTEIN, width=4),
        marker=dict(size=8),
        hovertemplate="%{x}年<br>蛋白區中位數: %{y:,.0f} 元/坪<extra></extra>"
    ), row=1, col=1)

    # 2022 vertical line (policy breakpoint)
    fig.add_vline(
        x=2022, line_width=2.5, line_dash="dash", line_color=COLOR_2022,
        annotation_text="2022 升息開始",
        annotation_position="top right",
        annotation_font=dict(size=10, color="#E76F51"),
        row=1, col=1
    )

    # Row 2: Gap (Egg - Protein)
    gap = egg["單價中位數"].values - protein["單價中位數"].values
    fig.add_trace(go.Scatter(
        x=egg["年份"], y=gap,
        mode="lines+markers",
        name="單價差距",
        line=dict(color="#2A9D8F", width=3),
        marker=dict(size=7),
        fill="tozeroy",
        fillcolor="rgba(42,157,143,0.15)",
        hovertemplate="%{x}年<br>差距: %{y:,.0f} 元/坪<extra></extra>"
    ), row=2, col=1)

    fig.add_hline(y=0, line_width=1, line_color="gray", row=2, col=1)

    # Row 3: Transaction volume
    fig.add_trace(go.Bar(
        x=egg["年份"], y=egg["交易筆數"],
        name="蛋黃區成交量",
        marker_color=COLOR_EGG,
        opacity=0.85,
        hovertemplate="%{x}年<br>蛋黃區: %{y:,} 筆<extra></extra>"
    ), row=3, col=1)

    fig.add_trace(go.Bar(
        x=protein["年份"], y=protein["交易筆數"],
        name="蛋白區成交量",
        marker_color=COLOR_PROTEIN,
        opacity=0.85,
        hovertemplate="%{x}年<br>蛋白區: %{y:,} 筆<extra></extra>"
    ), row=3, col=1)

    # Layout polish
    fig.update_layout(
        height=920,
        template="plotly_white",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(size=11)
        ),
        margin=dict(l=55, r=35, t=30, b=50),
        title=dict(
            text="<b>2015–2025 蛋黃區 vs 蛋白區 單價中位數變化</b><br>"
                 "<span style='font-size:12.5px; color:#444'>打炒房 + 升息後，市中心精華區跟外圍區的房價差距，是縮小了還是拉大了？</span>",
            x=0.5, xanchor="center",
            font=dict(size=17, color="#1D3557")
        ),
        hovermode="x unified"
    )

    # X-axis formatting
    fig.update_xaxes(
        range=[min_year - 0.3, max_year + 0.3],
        tickmode="linear",
        dtick=1,
        title_text="年份",
        row=3, col=1
    )

    # Y-axes labels
    fig.update_yaxes(title_text="單價中位數（元/坪）", row=1, col=1)
    fig.update_yaxes(title_text="差距（元/坪）", row=2, col=1)
    fig.update_yaxes(title_text="交易筆數", row=3, col=1)

    # Cleaner, less crowded annotation for egg yolk definition
    fig.add_annotation(
        text="<b>紅線 = 蛋黃區（9區，預先固定）</b><br>大安、中正、松山、中山、信義、<br>南港、大同、士林、內湖<br>（2015-2017 基期就決定好了）",
        xref="paper", yref="paper",
        x=0.015, y=0.965,
        showarrow=False,
        font=dict(size=9.5, color="#222"),
        align="left",
        bordercolor="#E63946",
        borderwidth=1.5,
        borderpad=5,
        bgcolor="rgba(255,250,250,0.95)"
    )

    # ========== CONVERT TO HTML + ADD CUSTOM INTERACTIVITY ==========
    # We will embed the full district data as JSON and add simple JS checkboxes
    # for live district overlay. This keeps everything in one file.

    html_str = fig.to_html(
        full_html=True,
        include_plotlyjs=True,
        config={"displayModeBar": True, "displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 2}}
    )

    # Inject custom data + JS controls right before </body>
    extra_html = build_custom_controls_and_js(district_data, egg_districts, years, egg_def)

    final_html = html_str.replace("</body>", extra_html + "\n</body>")

    return final_html


def build_custom_controls_and_js(district_data, egg_districts, years, egg_def):
    """Build the HTML controls + JavaScript that enables live multi-district selection."""

    # Serialize data for JS
    data_json = json.dumps(district_data, ensure_ascii=False)

    # Nice list of districts to show as checkboxes (prioritize egg + a few interesting protein)
    priority_protein = ["板橋區", "永和區", "三重區", "中和區", "新店區", "淡水區", "林口區"]
    checkbox_districts = egg_districts + [d for d in priority_protein if d not in egg_districts]

    checkbox_html = ""
    for d in checkbox_districts:
        is_egg = d in egg_districts
        color = "#E63946" if is_egg else "#457B9D"
        checked = "checked" if is_egg else ""
        label_style = f"color:{color}; font-weight:600;" if is_egg else ""
        checkbox_html += f"""
        <label style="display:inline-block; margin: 4px 12px 4px 0; font-size:13px;">
            <input type="checkbox" class="district-cb" value="{d}" {checked}>
            <span style="{label_style}">{d}</span>
        </label>
        """

    js_code = f"""
<script>
// ============== INTERACTIVE DISTRICT OVERLAY ==============
const DISTRICT_DATA = {data_json};
const BASE_YEARS = {json.dumps(years)};

let currentExtraTraces = [];   // keep track of added traces so we can remove them

function updateDistrictOverlays() {{
    const checkboxes = document.querySelectorAll('.district-cb');
    const selected = Array.from(checkboxes).filter(cb => cb.checked).map(cb => cb.value);

    // Remove previously added district traces
    if (window.myPlot) {{
        const tracesToDelete = [];
        window.myPlot.data.forEach((trace, i) => {{
            if (trace._isDistrictOverlay) tracesToDelete.push(i);
        }});
        if (tracesToDelete.length) {{
            Plotly.deleteTraces(window.myPlot, tracesToDelete);
        }}
    }}
    currentExtraTraces = [];

    if (selected.length === 0) return;

    const addTraces = [];
    selected.forEach(dist => {{
        const d = DISTRICT_DATA[dist];
        if (!d) return;
        const color = d.is_egg ? '#E63946' : '#457B9D';
        const dash = d.is_egg ? 'solid' : 'dot';

        addTraces.push({{
            x: d.years,
            y: d.price,
            type: 'scatter',
            mode: 'lines+markers',
            name: dist + (d.is_egg ? ' (蛋黃)' : ' (蛋白)'),
            line: {{ color: color, width: 2, dash: dash }},
            marker: {{ size: 5 }},
            hovertemplate: dist + ' %{{x}}年<br>中位數: %{{y:,.0f}} 元/坪<extra></extra>',
            _isDistrictOverlay: true,
            visible: true
        }});
    }});

    if (addTraces.length && window.myPlot) {{
        Plotly.addTraces(window.myPlot, addTraces);
    }}
}}

// Attach listeners after Plotly is ready
function initInteractiveControls() {{
    // Store reference to the main plot
    const gd = document.querySelector('.plotly-graph-div');
    if (gd) {{
        window.myPlot = gd;
    }}

    // Checkbox listeners
    document.querySelectorAll('.district-cb').forEach(cb => {{
        cb.addEventListener('change', updateDistrictOverlays);
    }});

    // Initial render of pre-checked egg yolk districts
    setTimeout(() => {{
        updateDistrictOverlays();
    }}, 800);

    // Keyboard hint
    console.log('%c[互動式報表] 勾選行政區即可即時疊加比較線', 'color:#888');
}}

// Bootstrap
window.addEventListener('load', () => {{
    // Wait for Plotly to finish drawing the main figure
    setTimeout(initInteractiveControls, 1200);
}});
</script>
"""

    controls_html = f"""
<div style="max-width: 1100px; margin: 12px auto 8px; padding: 12px 16px; background:#F8F9FA; border:1px solid #DEE2E6; border-radius:6px; font-family: system-ui, -apple-system, sans-serif;">
    <div style="margin-bottom:6px; font-weight:600; color:#1D3557; font-size:13px;">
        想看單一行政區？直接勾選（可多選）
    </div>
    <div style="line-height:1.55; font-size:12.5px;">
        {checkbox_html}
    </div>
    <div style="margin-top:6px; font-size:11.5px; color:#555;">
        紅色字 = 蛋黃區（9區已預先固定） ｜ 藍色字 = 蛋白區 ｜ 勾選後會即時在上面的大圖疊加走勢線
    </div>
</div>
"""

    source_html = f"""
<div style="max-width:1100px; margin: 18px auto 35px; padding:13px 18px; background:#fff; border-left:5px solid #E63946; font-size:13px; color:#333; line-height:1.6; font-family: system-ui, -apple-system, sans-serif;">
    <b>這張圖到底在說什麼？</b><br>
    看 2015～2025 年，<b>蛋黃區（市中心 9 個精華區）</b>跟<b>蛋白區（其他外圍區）</b>的房價中位數走勢。<br>
    <span style="color:#E63946"><b>紅線</b></span> 是 9 個「蛋黃區」，在 2015-2017 年就先決定好，之後完全不改（避免事後挑選）。<br>
    <b>怎麼看故事？</b> 2022 年升息之後，如果紅線繼續明顯往上、藍線比較平 → 代表打炒房 + 升息下，區域差距不減反增。
</div>
"""

    # Add a very clear one-sentence takeaway banner
    takeaway_html = """
<div style="max-width:1100px; margin: 10px auto 4px; padding:8px 14px; background:#FFF4E6; border:1px solid #FFB347; border-radius:5px; font-size:13px; color:#5C3D00; font-family: system-ui, -apple-system, sans-serif;">
    <b>最簡單的看圖重點：</b> 2022 年以後，如果你發現紅色的蛋黃區線繼續明顯上升、藍色的蛋白區線比較平 → 這就是「區域落差不減反增」的證據。
</div>
"""

    return takeaway_html + controls_html + js_code + source_html


def main():
    print("Loading data...")
    df_district, df_ep, egg_def = load_data()

    print("Building interactive dashboard...")
    html = build_dashboard(df_district, df_ep, egg_def)

    out_path = Path(OUTPUT_HTML)
    out_path.write_text(html, encoding="utf-8")
    print("\nInteractive report generated successfully!")
    print(f"File: {out_path.resolve()}")
    print("Open the HTML file directly in any browser (fully offline).")


if __name__ == "__main__":
    main()
