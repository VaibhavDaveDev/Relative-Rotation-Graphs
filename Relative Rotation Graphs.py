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
    # Add extra buffer for rolling calculations (40-day MA + 10-day Mom)
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
    # Align dates
    df = pd.DataFrame({'price': price_series, 'bench': benchmark_series}).dropna()
    if len(df) < 50: return None, None
    
    # 1. Relative Strength
    rs = (df['price'] / df['bench'])
    
    # 2. JdK RS-Ratio (Normalized RS over 40 periods)
    rs_ratio = (rs / rs.rolling(window=40).mean()) * 100
    
    # 3. JdK RS-Momentum (Rate of change of RS-Ratio over 10 periods)
    # Using 100 as center to match standard RRG charts
    rs_momentum = (rs_ratio / rs_ratio.shift(10)) * 100
    
    return rs_ratio.dropna(), rs_momentum.dropna()

def create_rrg_plot(results, tail_length, show_tail=False):
    fig = go.Figure()
    
    all_x, all_y = [], []
    for s in results:
        all_x.extend(results[s]['ratio'].tail(tail_length))
        all_y.extend(results[s]['momentum'].tail(tail_length))
    
    if not all_x: return None

    # Set Chart Bounds
    x_min, x_max = min(all_x), max(all_x)
    y_min, y_max = min(all_y), max(all_y)
    
    # Add padding and ensure center (100,100) is visible
    x_range = [min(x_min, 98) - 1, max(x_max, 102) + 1]
    y_range = [min(y_min, 98) - 1, max(y_max, 102) + 1]

    # Draw Quadrant Colors using add_shape
    quadrants = [
        dict(x0=100, y0=100, x1=x_range[1], y1=y_range[1], color="rgba(0,255,0,0.1)"),   # Leading
        dict(x0=100, y0=y_range[0], x1=x_range[1], y1=100, color="rgba(255,165,0,0.1)"), # Weakening
        dict(x0=x_range[0], y0=y_range[0], x1=100, y1=100, color="rgba(255,0,0,0.1)"),   # Lagging
        dict(x0=x_range[0], y0=100, x1=100, y1=y_range[1], color="rgba(0,0,255,0.1)")    # Improving
    ]

    for q in quadrants:
        fig.add_shape(type="rect", x0=q['x0'], y0=q['y0'], x1=q['x1'], y1=q['y1'],
                      fillcolor=q['color'], line_width=0, layer="below")

    # Crosshair lines
    fig.add_hline(y=100, line_dash="dot", line_color="black", opacity=0.5)
    fig.add_vline(x=100, line_dash="dot", line_color="black", opacity=0.5)

    colors = px.colors.qualitative.Alphabet
    
    for i, symbol in enumerate(results):
        ratio_tail = results[symbol]['ratio'].tail(tail_length)
        mom_tail = results[symbol]['momentum'].tail(tail_length)
        color = colors[i % len(colors)]

        # Plot Tail Line
        if show_tail:
            fig.add_trace(go.Scatter(
                x=ratio_tail, y=mom_tail,
                mode='lines',
                line=dict(color=color, width=2),
                hoverinfo='skip',
                showlegend=False
            ))

        # Plot Current Point (last value of the tail)
        fig.add_trace(go.Scatter(
            x=[ratio_tail.iloc[-1]], 
            y=[mom_tail.iloc[-1]],
            mode='markers+text',
            marker=dict(size=12, color=color, line=dict(width=1, color='white')),
            text=[symbol],
            textposition="top center",
            name=symbol,
            hovertemplate=f"<b>{symbol}</b><br>RS-Ratio: %{{x:.2f}}<br>RS-Mom: %{{y:.2f}}<extra></extra>"
        ))

    fig.update_layout(
        xaxis=dict(title="RS-Ratio", range=x_range, gridcolor='white'),
        yaxis=dict(title="RS-Momentum", range=y_range, gridcolor='white'),
        height=800,
        margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor='white'
    )
    return fig

def main():
    st.title("Relative Rotation Graph (RRG)")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        benchmark = st.text_input("Benchmark", value="^NSEI")
        period = st.slider("Lookback Period", 60, 500, 150)
        tail_len = st.slider("Tail Length", 2, 50, 15)
        show_tail = st.checkbox("Show Trail/Tail", value=True)

    with col2:
        default_list = "ADANIENT.NS\nADANIPORTS.NS\nAPOLLOHOSP.NS\nASIANPAINT.NS\nAXISBANK.NS\nBAJAJ-AUTO.NS\nBAJFINANCE.NS\nBAJAJFINSV.NS\nBEL.NS\nBPCL.NS\nBHARTIARTL.NS\nBRITANNIA.NS\nCIPLA.NS\nCOALINDIA.NS\nDIVISLAB.NS\nDRREDDY.NS\nEICHERMOT.NS\nGRASIM.NS\nHCLTECH.NS\nHDFCBANK.NS\nHDFCLIFE.NS\nHEROMOTOCO.NS\nHINDALCO.NS\nHINDUNILVR.NS\nICICIBANK.NS\nITC.NS\nINDUSINDBK.NS\nINFY.NS\nJSWSTEEL.NS\nKOTAKBANK.NS\nLT.NS\nLTIM.NS\nM&M.NS\nMARUTI.NS\nNESTLEIND.NS\nNTPC.NS\nONGC.NS\nPOWERGRID.NS\nRELIANCE.NS\nSBILIFE.NS\nSBIN.NS\nSUNPHARMA.NS\nTATACONSUM.NS\nTATAMOTORS.NS\nTATASTEEL.NS\nTCS.NS\nTECHM.NS\nTITAN.NS\nULTRACEMCO.NS\nWIPRO.NS"
        stocks_input = st.text_area("Stocks (one per line)", value=default_list, height=200)
        stock_list = [s.strip() for s in stocks_input.split('\n') if s.strip()]

    if st.button("Generate RRG", type="primary"):
        with st.spinner("Downloading data..."):
            bench_data, _ = fetch_data([benchmark], period)
            stock_data, _ = fetch_data(stock_list, period)

            if benchmark not in bench_data:
                st.error("Could not load benchmark data.")
                return

            results = {}
            for s in stock_data:
                ratio, mom = calculate_rrg_metrics(stock_data[s], bench_data[benchmark])
                if ratio is not None:
                    results[s] = {'ratio': ratio, 'momentum': mom}

            if results:
                fig = create_rrg_plot(results, tail_len, show_tail=show_tail)
                st.plotly_chart(fig, width="stretch")
                
                # Summary Table
                summary = []
                for s in results:
                    summary.append({
                        "Ticker": s,
                        "RS-Ratio": round(results[s]['ratio'].iloc[-1], 2),
                        "RS-Momentum": round(results[s]['momentum'].iloc[-1], 2)
                    })
                st.dataframe(pd.DataFrame(summary).sort_values("RS-Ratio", ascending=False), width="stretch", hide_index=True)

if __name__ == "__main__":
    main()