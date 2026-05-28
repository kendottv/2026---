"""
Clean rebuild of the interactive housing report.

Goals:
- Main thick solid red line = 蛋黃區總體 (pre-fixed 9 districts aggregate)
- 9 individual egg yolk district lines visible by default as dashed colored lines near the red area
- Distinct high-contrast colors + dashed style + markers for individuals so they are clearly visible
- Pre-checked egg yolk checkboxes
- Reliable hover with rich info (price, count, gaps)
- Simple, stable JS for toggling
"""

import json
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ============== CONFIG ==============
DISTRICT_CSV = "district_yearly_stats.csv"
EGG_PROTEIN_CSV = "egg_protein_yearly.csv"
EGG_DEF_JSON = "egg_yolk_definition.json"
OUTPUT_HTML = "interactive_housing_report.html"

COLOR_EGG_AGG = "#C1121F"   # Main thick red for aggregate
COLOR_PROTEIN_AGG = "#1D3557"

# High contrast palette for the 9 individual egg districts (warm family, distinct)
EGG_INDIV_COLORS = {
    "大安區": "#D62828",
    "中正區": "#E63946",
    "松山區": "#F77F00",
    "中山區": "#FF6B35",
    "信義區": "#E76F51",
    "南港區": "#9D0208",
    "大同區": "#FF85A1",
    "士林區": "#FCA311",
    "內湖區": "#FFB703",
}

# Protein districts available for comparison + their colors
PRIORITY_PROTEIN = ["板橋區", "永和區", "三重區", "中和區", "新店區", "淡水區", "林口區"]

PROTEIN_COLORS = {
    "板橋區": "#264653",
    "永和區": "#2A9D8F",
    "三重區": "#0077B6",
    "中和區": "#1D3557",
    "新店區": "#7B2CBF",
    "淡水區": "#5E60CE",
    "林口區": "#00B4D8",
}
# ====================================


def load_data():
    df_d = pd.read_csv(DISTRICT_CSV, encoding="utf-8-sig")
    df_ep = pd.read_csv(EGG_PROTEIN_CSV, encoding="utf-8-sig")

    with open(EGG_DEF_JSON, encoding="utf-8") as f:
        egg_def = json.load(f)

    egg_districts = egg_def["蛋黃區"]

    # Egg aggregate
    egg_agg = df_ep[df_ep["蛋黃區"] == True].sort_values("年份")
    prot_agg = df_ep[df_ep["蛋黃區"] == False].sort_values("年份")

    # Individual egg yolk districts data
    egg_individuals = {}
    for dist in egg_districts:
        sub = df_d[df_d["行政區"] == dist].sort_values("年份")
        egg_individuals[dist] = {
            "years": sub["年份"].tolist(),
            "price": sub["單價中位數"].tolist(),
            "count": sub["交易筆數"].tolist(),
        }

    # Individual protein districts data (for toggling)
    protein_individuals = {}
    for dist in PRIORITY_PROTEIN:
        sub = df_d[df_d["行政區"] == dist].sort_values("年份")
        if len(sub) > 0:
            protein_individuals[dist] = {
                "years": sub["年份"].tolist(),
                "price": sub["單價中位數"].tolist(),
                "count": sub["交易筆數"].tolist(),
            }

    # Protein lookup for gaps
    prot_price_by_year = dict(zip(prot_agg["年份"], prot_agg["單價中位數"]))
    egg_price_by_year = dict(zip(egg_agg["年份"], egg_agg["單價中位數"]))

    return egg_agg, prot_agg, egg_individuals, protein_individuals, egg_price_by_year, prot_price_by_year, egg_districts, egg_def


def build_dashboard(egg_agg, prot_agg, egg_individuals, protein_individuals, egg_price_by_year, prot_price_by_year, egg_districts, egg_def):
    years = egg_agg["年份"].tolist()

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.07,
        row_heights=[0.52, 0.24, 0.24],
        subplot_titles=(
            "單價中位數時間序列（蛋黃區 vs 蛋白區）",
            "蛋黃區相對蛋白區的單價差距（元/坪）",
            "每年交易筆數對比"
        )
    )

    # === Main aggregate lines (thick solid) ===
    fig.add_trace(go.Scatter(
        x=egg_agg["年份"], y=egg_agg["單價中位數"],
        mode="lines+markers",
        name="蛋黃區總體（預先固定9區）",
        line=dict(color=COLOR_EGG_AGG, width=4.5),
        marker=dict(size=8),
        hovertemplate="<b>【蛋黃區總體】</b>（9區預先固定）<br>%{x}年<br>單價中位數: <b>%{y:,.0f}</b> 元/坪<extra></extra>",
        hoverlabel=dict(bgcolor=COLOR_EGG_AGG, font=dict(color="white", size=12))
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=prot_agg["年份"], y=prot_agg["單價中位數"],
        mode="lines+markers",
        name="蛋白區總體",
        line=dict(color=COLOR_PROTEIN_AGG, width=4.5),
        marker=dict(size=8),
        hovertemplate="<b>【蛋白區總體】</b><br>%{x}年<br>單價中位數: <b>%{y:,.0f}</b> 元/坪<extra></extra>",
        hoverlabel=dict(bgcolor=COLOR_PROTEIN_AGG, font=dict(color="white", size=12))
    ), row=1, col=1)

    # 2022 line
    fig.add_vline(x=2022, line_width=2.5, line_dash="dash", line_color="#E76F51",
                  annotation_text="2022 升息開始", annotation_position="top right",
                  annotation_font=dict(size=10, color="#E76F51"), row=1, col=1)

    # === Pre-add the 9 individual egg yolk district lines (dashed + markers) ===
    # These will be visible by default
    individual_trace_indices = {}  # name -> trace index in fig.data

    for dist in egg_districts:
        data = egg_individuals[dist]
        color = EGG_INDIV_COLORS.get(dist, "#E63946")

        # Build rich hover text
        hover_texts = []
        for i, y in enumerate(data["years"]):
            p = data["price"][i]
            c = data["count"][i]
            egg_p = egg_price_by_year.get(y, p)
            gap = round(p - egg_p)
            hover_texts.append(
                f"<b>{dist}</b><br>{int(y)}年<br>"
                f"單價中位數: <b>{p:,.0f}</b> 元/坪<br>"
                f"交易筆數: {c:,} 筆<br>"
                f"與蛋黃總體差距: {gap:+,} 元"
            )

        trace = go.Scatter(
            x=data["years"],
            y=data["price"],
            mode="lines+markers",
            name=dist,
            line=dict(color=color, width=2.2, dash="dash"),
            marker=dict(size=5.5),
            hovertext=hover_texts,
            hoverinfo="text",
            visible=True   # Show by default
        )
        fig.add_trace(trace, row=1, col=1)
        individual_trace_indices[dist] = len(fig.data) - 1

    # === Pre-add priority protein district lines (hidden by default) ===
    for dist in PRIORITY_PROTEIN:
        if dist not in protein_individuals:
            continue
        data = protein_individuals[dist]
        color = PROTEIN_COLORS.get(dist, "#457B9D")

        hover_texts = []
        for i, y in enumerate(data["years"]):
            p = data["price"][i]
            c = data["count"][i]
            hover_texts.append(
                f"<b>{dist}</b><br>{int(y)}年<br>"
                f"單價中位數: <b>{p:,.0f}</b> 元/坪<br>"
                f"交易筆數: {c:,} 筆"
            )

        trace = go.Scatter(
            x=data["years"],
            y=data["price"],
            mode="lines+markers",
            name=dist,
            line=dict(color=color, width=2, dash="dot"),
            marker=dict(size=5),
            hovertext=hover_texts,
            hoverinfo="text",
            visible=False  # Hidden by default
        )
        fig.add_trace(trace, row=1, col=1)
        individual_trace_indices[dist] = len(fig.data) - 1

    # Gap subplot (main only for simplicity)
    gap = egg_agg["單價中位數"].values - prot_agg["單價中位數"].values
    fig.add_trace(go.Scatter(
        x=egg_agg["年份"], y=gap,
        mode="lines+markers",
        name="單價差距",
        line=dict(color="#2A9D8F", width=3),
        marker=dict(size=6),
        fill="tozeroy",
        fillcolor="rgba(42,157,143,0.12)",
        hovertemplate="%{x}年<br>差距: %{y:,.0f} 元/坪<extra></extra>"
    ), row=2, col=1)

    # Volume
    fig.add_trace(go.Bar(
        x=egg_agg["年份"], y=egg_agg["交易筆數"],
        name="蛋黃區成交量",
        marker_color=COLOR_EGG_AGG,
        opacity=0.8,
        hovertemplate="%{x}年<br>蛋黃區: %{y:,} 筆<extra></extra>"
    ), row=3, col=1)

    fig.add_trace(go.Bar(
        x=prot_agg["年份"], y=prot_agg["交易筆數"],
        name="蛋白區成交量",
        marker_color=COLOR_PROTEIN_AGG,
        opacity=0.8,
        hovertemplate="%{x}年<br>蛋白區: %{y:,} 筆<extra></extra>"
    ), row=3, col=1)

    # Layout
    fig.update_layout(
        height=900,
        template="plotly_white",
        showlegend=True,
        legend=dict(
            orientation="v",           # vertical legend on the right to avoid title overlap
            yanchor="top", y=0.98,
            xanchor="left", x=1.02,
            font=dict(size=9.5),
            bgcolor="rgba(255,255,255,0.9)"
        ),
        margin=dict(l=50, r=140, t=50, b=45),   # increased top margin to prevent title overlap
        title=dict(
            text="<b>2015–2025 蛋黃區 vs 蛋白區 單價中位數變化</b>",
            x=0.5, xanchor="center",
            font=dict(size=15, color="#1D3557")
        ),
        hovermode="closest"
    )

    fig.update_xaxes(tickmode="linear", dtick=1, title_text="年份", row=3, col=1)
    fig.update_yaxes(title_text="單價中位數（元/坪）", row=1, col=1)
    fig.update_yaxes(title_text="差距（元/坪）", row=2, col=1)
    fig.update_yaxes(title_text="交易筆數", row=3, col=1)

    # Reduce subplot title size to reduce top crowding
    fig.update_annotations(selector={"text": "單價中位數時間序列（蛋黃區 vs 蛋白區）"}, font=dict(size=11))
    fig.update_annotations(selector={"text": "蛋黃區相對蛋白區的單價差距（元/坪）"}, font=dict(size=11))
    fig.update_annotations(selector={"text": "每年交易筆數對比"}, font=dict(size=11))

    # Annotation for definition (moved lower and smaller to avoid title overlap)
    fig.add_annotation(
        text="<b>紅線</b>=蛋黃總體　虛線=個別行政區",
        xref="paper", yref="paper",
        x=0.015, y=0.88,
        showarrow=False,
        font=dict(size=8, color="#444"),
        align="left",
        bordercolor=COLOR_EGG_AGG,
        borderwidth=0.5,
        borderpad=2,
        bgcolor="rgba(255,250,250,0.85)"
    )

    # Convert to HTML
    html = fig.to_html(
        full_html=True,
        include_plotlyjs=True,
        config={"displayModeBar": True, "displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 2}}
    )

    # Districts for checkboxes
    priority_protein = PRIORITY_PROTEIN  # use the constant defined at top

    # Build nicer grouped checkboxes
    checkbox_html = ""

    # Egg yolk section (pre-checked)
    checkbox_html += "<div style='margin-bottom:4px; font-weight:600; color:#C1121F; font-size:12px;'>蛋黃區（預設顯示）</div>"
    for dist in egg_districts:
        color = EGG_INDIV_COLORS.get(dist, "#E63946")
        checkbox_html += f"""
        <label style="display:inline-block; margin:2px 6px 2px 0; font-size:12px;">
            <input type="checkbox" class="dist-toggle" data-name="{dist}" data-type="egg" checked>
            <span style="color:{color}; font-weight:600;">{dist}</span>
        </label>
        """

    # Protein section
    checkbox_html += "<div style='margin:6px 0 4px 0; font-weight:600; color:#1D3557; font-size:12px;'>其他行政區（可新增比較）</div>"
    for dist in priority_protein:
        color = PROTEIN_COLORS.get(dist, "#457B9D")
        checkbox_html += f"""
        <label style="display:inline-block; margin:2px 6px 2px 0; font-size:12px;">
            <input type="checkbox" class="dist-toggle" data-name="{dist}" data-type="protein">
            <span style="color:{color};">{dist}</span>
        </label>
        """

    # Pass the correct trace indices to JS for reliable toggling
    trace_index_json = json.dumps(individual_trace_indices)

    extra_js = f"""
<script>
(function() {{
    const traceIndexMap = {trace_index_json};

    function updateVisibility() {{
        const checkboxes = document.querySelectorAll('.dist-toggle');
        checkboxes.forEach(cb => {{
            const name = cb.getAttribute('data-name');
            const visible = cb.checked;
            const idx = traceIndexMap[name];

            if (typeof idx === 'number') {{
                // Use the exact index recorded when the trace was added
                Plotly.restyle(document.querySelector('.plotly-graph-div'), {{visible: visible ? true : 'legendonly'}}, idx);
            }}
        }});
    }}

    window.addEventListener('load', function() {{
        setTimeout(function() {{
            const checkboxes = document.querySelectorAll('.dist-toggle');
            checkboxes.forEach(cb => cb.addEventListener('change', updateVisibility));
        }}, 1200);
    }});
}})();
</script>
"""

    controls = f"""
<div style="max-width:1100px; margin:20px auto 10px; padding:14px 18px; background:#fafafa; border:1px solid #e0e0e0; border-radius:8px; font-size:12.5px;">
    <div style="font-weight:600; margin-bottom:8px; color:#222; font-size:13px;">
        控制顯示（點擊下方核取方塊即可切換）
    </div>
    {checkbox_html}
    <div style="margin-top:10px; font-size:11px; color:#666; border-top:1px dashed #ddd; padding-top:8px;">
        提示：蛋黃區預設顯示（虛線），可取消勾選隱藏。其他行政區勾選後會新增比較線。
    </div>
</div>
"""

    source = """
<div style="max-width:1100px; margin:10px auto 30px; padding:12px 16px; background:#fff; border-left:5px solid #E63946; font-size:12.5px; color:#333;">
    <b>資料來源與方法</b><br>
    內政部實價登錄（台北市＋新北市，2015–2025）。蛋黃區定義：2015-2017基期單價中位數前25%（9區），預先固定，永不事後調整。
</div>
"""

    # Insert controls BELOW the chart (after the Plotly div) for better usability
    # We insert it right before the closing </body>, but after the chart
    final_html = html.replace("</body>", extra_js + controls + source + "\n</body>")

    return final_html


def main():
    print("Loading data...")
    egg_agg, prot_agg, egg_individuals, protein_individuals, egg_price_by_year, prot_price_by_year, egg_districts, egg_def = load_data()

    print("Building clean interactive dashboard...")
    html = build_dashboard(egg_agg, prot_agg, egg_individuals, protein_individuals, egg_price_by_year, prot_price_by_year, egg_districts, egg_def)

    out_path = Path(OUTPUT_HTML)
    out_path.write_text(html, encoding="utf-8")
    print(f"Generated: {out_path.resolve()}")
    print("Done. Open the HTML file in a browser.")


if __name__ == "__main__":
    main()
