import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

# Configure page
st.set_page_config(page_title="Nifty 50 RRG Analysis", layout="centered")

# App Width Styling
st.markdown("""
    <style>
      .stAppViewContainer .stMain .stMainBlockContainer{ max-width: 1440px; }
    </style>    
    """, unsafe_allow_html=True)

def fetch_data(symbols, period_days):
    data = {}
    failed_symbols = []
    end_date = datetime.now()
    # Buffer for rolling calculations (40-day MA + 10-day Mom)
    start_date = end_date - timedelta(days=period_days + 80)

    for symbol in symbols:
        try:
            hist = yf.download(symbol, start=start_date, end=end_date, multi_level_index=False, progress=False)
            if not hist.empty and len(hist) > 50:
                data[symbol] = hist['Close']
            else:
                failed_symbols.append(symbol)
        except:
            failed_symbols.append(symbol)
    return data, failed_symbols

def calculate_rrg_metrics(price_series, benchmark_series):
    df = pd.DataFrame({'price': price_series, 'bench': benchmark_series}).dropna()
    if len(df) < 50: return None, None
    
    # 1. Relative Strength
    rs = (df['price'] / df['bench'])
    # 2. JdK RS-Ratio
    rs_ratio = (rs / rs.rolling(window=40).mean()) * 100
    # 3. JdK RS-Momentum (Centered at 100)
    rs_momentum = (rs_ratio / rs_ratio.shift(10)) * 100
    
    return rs_ratio.dropna(), rs_momentum.dropna()

def get_quadrant_info(rs_ratio, rs_momentum):
    if rs_ratio >= 100 and rs_momentum >= 100:
        return "Leading", "green"
    elif rs_ratio >= 100 and rs_momentum < 100:
        return "Weakening", "orange"
    elif rs_ratio < 100 and rs_momentum < 100:
        return "Lagging", "red"
    else:
        return "Improving", "blue"

def create_rrg_plot(results, tail_length, show_tail=False):
    fig = go.Figure()
    all_x, all_y = [], []
    for s in results:
        all_x.extend(results[s]['ratio'].tail(tail_length))
        all_y.extend(results[s]['momentum'].tail(tail_length))
    
    if not all_x: return None

    x_range = [min(all_x + [98]) - 1, max(all_x + [102]) + 1]
    y_range = [min(all_y + [98]) - 1, max(all_y + [102]) + 1]

    # Background Quadrants
    quads = [
        dict(x0=100, y0=100, x1=x_range[1], y1=y_range[1], color="rgba(0,255,0,0.08)"), # Leading
        dict(x0=100, y0=y_range[0], x1=x_range[1], y1=100, color="rgba(255,165,0,0.08)"), # Weakening
        dict(x0=x_range[0], y0=y_range[0], x1=100, y1=100, color="rgba(255,0,0,0.08)"), # Lagging
        dict(x0=x_range[0], y0=100, x1=100, y1=y_range[1], color="rgba(0,0,255,0.08)") # Improving
    ]
    for q in quads:
        fig.add_shape(type="rect", x0=q['x0'], y0=q['y0'], x1=q['x1'], y1=q['y1'], fillcolor=q['color'], line_width=0, layer="below")

    fig.add_hline(y=100, line_dash="dot", line_color="black", opacity=0.3)
    fig.add_vline(x=100, line_dash="dot", line_color="black", opacity=0.3)

    colors = px.colors.qualitative.Alphabet
    for i, symbol in enumerate(results):
        ratio_tail = results[symbol]['ratio'].tail(tail_length)
        mom_tail = results[symbol]['momentum'].tail(tail_length)
        color = colors[i % len(colors)]

        if show_tail:
            fig.add_trace(go.Scatter(x=ratio_tail, y=mom_tail, mode='lines', line=dict(color=color, width=1.5), hoverinfo='skip', showlegend=False))

        fig.add_trace(go.Scatter(
            x=[ratio_tail.iloc[-1]], y=[mom_tail.iloc[-1]],
            mode='markers+text', marker=dict(size=12, color=color, line=dict(width=1, color='white')),
            text=[symbol], textposition="top center", name=symbol,
            hovertemplate=f"<b>{symbol}</b><br>RS-Ratio: %{{x:.2f}}<br>RS-Mom: %{{y:.2f}}<extra></extra>"
        ))

    fig.update_layout(xaxis=dict(title="RS-Ratio", range=x_range), yaxis=dict(title="RS-Momentum", range=y_range), height=800, plot_bgcolor='white')
    return fig

def main():
    st.subheader("Sector Rotation - Relative Rotation Graph")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        benchmark = st.text_input("Benchmark Symbol", value="^NSEI")
        period = st.slider("Analysis Period (days)", 65, 400, 150)
        tail_len = st.slider("Tail Length (days)", 2, 50, 10)
        show_tail = st.checkbox("Show Tail", value=True)

    with col2:
        default_list = "ADANIENT.NS\nADANIPORTS.NS\nAPOLLOHOSP.NS\nASIANPAINT.NS\nAXISBANK.NS\nBAJAJ-AUTO.NS\nBAJFINANCE.NS\nBAJAJFINSV.NS\nBEL.NS\nBPCL.NS\nBHARTIARTL.NS\nBRITANNIA.NS\nCIPLA.NS\nCOALINDIA.NS\nDIVISLAB.NS\nDRREDDY.NS\nEICHERMOT.NS\nGRASIM.NS\nHCLTECH.NS\nHDFCBANK.NS\nHDFCLIFE.NS\nHEROMOTOCO.NS\nHINDALCO.NS\nHINDUNILVR.NS\nICICIBANK.NS\nITC.NS\nINDUSINDBK.NS\nINFY.NS\nJSWSTEEL.NS\nKOTAKBANK.NS\nLT.NS\nLTIM.NS\nM&M.NS\nMARUTI.NS\nNESTLEIND.NS\nNTPC.NS\nONGC.NS\nPOWERGRID.NS\nRELIANCE.NS\nSBILIFE.NS\nSBIN.NS\nSUNPHARMA.NS\nTATACONSUM.NS\nTATASTEEL.NS\nTCS.NS\nTECHM.NS\nTITAN.NS\nULTRACEMCO.NS\nWIPRO.NS"
        stocks_input = st.text_area("Symbols", value=default_list, height=200)
        stock_list = [s.strip() for s in stocks_input.split('\n') if s.strip()]

    if st.button("Run Analysis", type="primary"):
        with st.spinner("Processing..."):
            b_data, _ = fetch_data([benchmark], period)
            s_data, _ = fetch_data(stock_list, period)

            results = {}
            for s in s_data:
                r, m = calculate_rrg_metrics(s_data[s], b_data[benchmark])
                if r is not None: results[s] = {'ratio': r, 'momentum': m}

            if results:
                fig = create_rrg_plot(results, tail_len, show_tail=show_tail)
                st.plotly_chart(fig, width="stretch")
                
                # Summary Table
                summary = []
                for s in results:
                    r_val, m_val = results[s]['ratio'].iloc[-1], results[s]['momentum'].iloc[-1]
                    quad, _ = get_quadrant_info(r_val, m_val)
                    summary.append({"Ticker": s, "RS-Ratio": round(r_val, 2), "RS-Momentum": round(m_val, 2), "Quadrant": quad})
                
                st.subheader("Relative Positions Summary")
                st.dataframe(pd.DataFrame(summary).sort_values("RS-Ratio", ascending=False), width="stretch", hide_index=True)

                # Restored Explanation Block
                with st.expander("Understanding the Relative Rotation Graph"):
                    st.markdown("""
                        **Quadrants Explanation:**
                        * **Leading (Top-Right)**: High relative strength, positive momentum. Stocks outperforming benchmark with increasing strength.
                        * **Weakening (Bottom-Right)**: High relative strength, negative momentum. Stocks still outperforming but losing relative power.
                        * **Lagging (Bottom-Left)**: Low relative strength, negative momentum. Stocks underperforming the benchmark.
                        * **Improving (Top-Left)**: Low relative strength, positive momentum. Stocks underperforming but gaining strength/momentum.

                        **How to Read:**
                        - **RS-Ratio > 100**: Stock is outperforming the benchmark.
                        - **RS-Ratio < 100**: Stock is underperforming the benchmark.
                        - **RS-Momentum > 100**: Relative performance is accelerating.
                        - **RS-Momentum < 100**: Relative performance is decelerating.
                        - **Tail**: Shows the path the stock has taken over the selected Tail Length period.
                        """)

if __name__ == "__main__":
    main()