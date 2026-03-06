import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import warnings
from scipy.interpolate import interp1d

warnings.filterwarnings('ignore')

# Configure page
st.set_page_config(
    page_title="Sector Rotation Analysis",
    layout="centered"
)
# Apply fixed screen width for app (1440px)
st.markdown(
    f"""
    <style>
      .stAppViewContainer .stMain .stMainBlockContainer{{ max-width: 1440px; }}
    </style>    
  """,
    unsafe_allow_html=True,
)

def fetch_data(symbols, period_days):
    """Fetch data from Yahoo Finance with error handling"""
    data = {}
    failed_symbols = []

    # Calculate start date
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_days + 10)  # Add buffer for calculations

    for symbol in symbols:
        try:
            # Using Ticker().history() is much safer across different yfinance versions
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)

            if len(hist) < 20:  # Minimum data requirement
                failed_symbols.append(symbol)
                continue

            data[symbol] = hist['Close']
        except Exception as e:
            failed_symbols.append(symbol)
            continue

    return data, failed_symbols


def calculate_relative_strength(price_data, benchmark_data, period):
    """Calculate relative strength vs benchmark"""
    # Ensure we have enough data
    min_length = min(len(price_data), len(benchmark_data))
    if min_length < period:
        return None, None

    # Align data by index
    aligned_data = pd.DataFrame({
        'price': price_data,
        'benchmark': benchmark_data
    }).dropna()

    if len(aligned_data) < period:
        return None, None

    # Calculate relative strength (sector/benchmark)
    relative_strength = aligned_data['price'] / aligned_data['benchmark']

    # Calculate momentum (rate of change)
    rs_momentum = relative_strength.pct_change(period).dropna()

    return relative_strength, rs_momentum


def calculate_jdk_rs_ratio(relative_strength, short_period=10, long_period=40):
    """Calculate JdK RS-Ratio similar to RRG methodology"""
    if len(relative_strength) < long_period:
        return None

    # Normalize relative strength to 100
    rs_normalized = (relative_strength / relative_strength.rolling(long_period).mean()) * 100

    return rs_normalized


def calculate_jdk_rs_momentum(rs_ratio, period=10):
    """Calculate JdK RS-Momentum"""
    if rs_ratio is None or len(rs_ratio) < period:
        return None

    # Calculate momentum as rate of change
    momentum = ((rs_ratio / rs_ratio.shift(period)) - 1) * 100

    return momentum


def get_quadrant_info(rs_ratio, rs_momentum):
    """Determine quadrant and provide info"""
    if rs_ratio > 100 and rs_momentum > 0:
        return "Leading", "green", "🚀"
    elif rs_ratio > 100 and rs_momentum < 0:
        return "Weakening", "orange", "📉"
    elif rs_ratio < 100 and rs_momentum < 0:
        return "Lagging", "red", "📊"
    else:
        return "Improving", "blue", "📈"


def smooth_data(x_vals, y_vals, method="Moving Average", window=3):
    """Smooth the tail data using various methods"""
    if len(x_vals) < 3 or len(y_vals) < 3:
        return x_vals, y_vals

    try:
        if method == "Moving Average":
            # Simple moving average
            x_smooth = pd.Series(x_vals).rolling(window=window, center=True, min_periods=1).mean().values
            y_smooth = pd.Series(y_vals).rolling(window=window, center=True, min_periods=1).mean().values

        elif method == "Exponential":
            # Exponential smoothing
            alpha = 2.0 / (window + 1)
            x_smooth = pd.Series(x_vals).ewm(alpha=alpha, adjust=False).mean().values
            y_smooth = pd.Series(y_vals).ewm(alpha=alpha, adjust=False).mean().values

        elif method == "Spline":
            # Spline interpolation for smoothing
            if len(x_vals) >= 4:  # Need at least 4 points for cubic spline
                indices = np.arange(len(x_vals))

                # Create more points for smoother curve
                new_indices = np.linspace(0, len(x_vals) - 1, len(x_vals) * 2)

                # Interpolate
                f_x = interp1d(indices, x_vals, kind='cubic', bounds_error=False, fill_value='extrapolate')
                f_y = interp1d(indices, y_vals, kind='cubic', bounds_error=False, fill_value='extrapolate')

                x_smooth = f_x(new_indices)
                y_smooth = f_y(new_indices)

                # Sample back to original length but smoothed
                sample_indices = np.linspace(0, len(x_smooth) - 1, len(x_vals)).astype(int)
                x_smooth = x_smooth[sample_indices]
                y_smooth = y_smooth[sample_indices]
            else:
                # Fall back to moving average for short series
                x_smooth = pd.Series(x_vals).rolling(window=2, center=True, min_periods=1).mean().values
                y_smooth = pd.Series(y_vals).rolling(window=2, center=True, min_periods=1).mean().values

        return x_smooth, y_smooth

    except Exception as e:
        # If smoothing fails, return original data
        return x_vals, y_vals


def create_rrg_plot(results, tail_length, enable_smoothing=True, smoothing_method="Moving Average",
                    smoothing_window=3, show_tail=False):
    """Create the Relative Rotation Graph"""
    fig = go.Figure()

    # First, determine the actual data ranges
    all_rs_ratios = []
    all_rs_momentum = []

    for symbol, data in results.items():
        if data['rs_ratio'] is not None and data['rs_momentum'] is not None:
            # FIX: Ensure rs_ratio and rs_momentum are aligned by date before dropping NaNs
            df_aligned = pd.DataFrame({
                'rs_ratio': data['rs_ratio'],
                'rs_momentum': data['rs_momentum']
            }).dropna()
            
            if not df_aligned.empty:
                all_rs_ratios.extend(df_aligned['rs_ratio'].values)
                all_rs_momentum.extend(df_aligned['rs_momentum'].values)

    if not all_rs_ratios or not all_rs_momentum:
        st.error("No valid data to plot")
        return None

    # Calculate dynamic ranges with some padding
    x_min, x_max = min(all_rs_ratios), max(all_rs_ratios)
    y_min, y_max = min(all_rs_momentum), max(all_rs_momentum)

    # Add padding (10% on each side)
    x_padding = (x_max - x_min) * 0.1
    y_padding = (y_max - y_min) * 0.1

    x_range = [x_min - x_padding, x_max + x_padding]
    y_range = [y_min - y_padding, y_max + y_padding]

    # Ensure 100 is visible on x-axis and 0 is visible on y-axis
    x_center = 100
    x_data_range = max(x_max - 100, 100 - x_min)  # Get the larger distance from 100
    x_range = [x_center - x_data_range - x_padding, x_center + x_data_range + x_padding]
    if y_range[0] > 0:
        y_range[0] = min(y_range[0], -0.5)
    if y_range[1] < 0:
        y_range[1] = max(y_range[1], 0.5)

    # Add quadrant backgrounds based on actual ranges
    fig.add_shape(type="rect", x0=100, y0=0, x1=x_range[1], y1=y_range[1], fillcolor="rgba(0,255,0,0.1)", line=dict(color="rgba(0,0,0,0)"), name="Leading")
    fig.add_shape(type="rect", x0=100, y0=y_range[0], x1=x_range[1], y1=0, fillcolor="rgba(255,165,0,0.1)", line=dict(color="rgba(0,0,0,0)"), name="Weakening")
    fig.add_shape(type="rect", x0=x_range[0], y0=y_range[0], x1=100, y1=0, fillcolor="rgba(255,0,0,0.1)", line=dict(color="rgba(0,0,0,0)"), name="Lagging")
    fig.add_shape(type="rect", x0=x_range[0], y0=0, x1=100, y1=y_range[1], fillcolor="rgba(0,0,255,0.1)", line=dict(color="rgba(0,0,0,0)"), name="Improving")

    # Add center lines
    fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
    fig.add_vline(x=100, line_dash="dash", line_color="black", opacity=0.5)

    colors = px.colors.qualitative.Set2

    for i, (symbol, data) in enumerate(results.items()):
        if data['rs_ratio'] is None or data['rs_momentum'] is None:
            continue

        # FIX: Align data before grabbing the tail to ensure coordinates match the exact same dates
        df_aligned = pd.DataFrame({
            'rs_ratio': data['rs_ratio'],
            'rs_momentum': data['rs_momentum']
        }).dropna()

        tail_points = min(tail_length, len(df_aligned))

        if tail_points < 2:
            continue

        x_vals = df_aligned['rs_ratio'].tail(tail_points).values
        y_vals = df_aligned['rs_momentum'].tail(tail_points).values

        # Apply smoothing if enabled
        if enable_smoothing and tail_points > 2:
            x_vals_smooth, y_vals_smooth = smooth_data(x_vals, y_vals, smoothing_method, smoothing_window)
            x_vals_smooth[-1] = x_vals[-1]
            y_vals_smooth[-1] = y_vals[-1]
        else:
            x_vals_smooth, y_vals_smooth = x_vals, y_vals

        color = colors[i % len(colors)]

        # Add tail (trajectory) - use smoothed data for the line, original for markers
        if show_tail:
            fig.add_trace(go.Scatter(
                x=x_vals_smooth,
                y=y_vals_smooth,
                mode='lines',
                name=f'{symbol} Trail',
                line=dict(color=color, width=3, shape='spline' if smoothing_method == "Spline" else 'linear'),
                opacity=0.7,
                showlegend=False
            ))

        # Add current position (larger marker) - always use original data
        current_quad, quad_color, quad_icon = get_quadrant_info(x_vals[-1], y_vals[-1])

        fig.add_trace(go.Scatter(
            x=[x_vals[-1]],
            y=[y_vals[-1]],
            mode='markers+text',
            name=f'{symbol} ({current_quad})',
            marker=dict(
                size=20,
                color=color,
                line=dict(width=2, color='white')
            ),
            text=[f'{symbol}'],
            textposition="middle right",
            textfont=dict(size=15, color='black'),
            hovertemplate=f'<b>{symbol}</b><br>' +
                          f'RS-Ratio: {x_vals[-1]:.2f}<br>' +
                          f'RS-Momentum: {y_vals[-1]:.2f}<br>' +
                          f'Quadrant: {current_quad}<extra></extra>'
        ))

    # Update layout
    fig.update_layout(
        xaxis_title="RS-Ratio",
        yaxis_title="RS-Momentum",
        width=800,
        height=1000,
        showlegend=False,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.01
        )
    )

    # Set dynamic axis ranges
    fig.update_xaxes(range=x_range)
    fig.update_yaxes(range=y_range)

    # Add annotations for quadrants
    leading_x = (100 + x_range[1]) / 2
    leading_y = y_range[1] * 0.8
    fig.add_annotation(x=leading_x, y=leading_y, text="Leading<br>(Hold Position)", showarrow=False, font=dict(size=14))

    weakening_x = (100 + x_range[1]) / 2
    weakening_y = y_range[0] * 0.8
    fig.add_annotation(x=weakening_x, y=weakening_y, text="Weakening<br>(Look to Sell)", showarrow=False, font=dict(size=14))

    lagging_x = (x_range[0] + 100) / 2
    lagging_y = y_range[0] * 0.8
    fig.add_annotation(x=lagging_x, y=lagging_y, text="Lagging<br>(Avoid)", showarrow=False, font=dict(size=14))

    improving_x = (x_range[0] + 100) / 2
    improving_y = y_range[1] * 0.8
    fig.add_annotation(x=improving_x, y=improving_y, text="Improving<br>(Look to Buy)", showarrow=False, font=dict(size=14))

    return fig


def main():
    st.subheader("Sector Rotation - Relative Rotation Graph")
    st.markdown("Analyze sector/stock performance relative to benchmark using RRG methodology. Input Symbols as seen in Yahoo Finance")

    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        benchmark = st.text_input("Benchmark Symbol", value="^NSEI", help="Enter benchmark symbol (e.g., ^NSEI for Nifty 50)")
        st.markdown("<style> .st-bu { background-color: rgba(0, 0, 0, 0); } </style>", unsafe_allow_html=True)
        period = st.slider("Analysis Period (days)", min_value=65, max_value=365, value=90, step=5)
        tail_length = st.slider("Tail Length (days)", min_value=2, max_value=25, value=4, step=1)

    with col2:
        # 1. Define our cheat-sheet of stock/sector baskets
        baskets = {

    # ── Sector Indices ────────────────────────────────────────────────
    "Nifty Sectors": (
        "^CNXAUTO\n"       # Auto
        "^CNXPHARMA\n"     # Pharma
        "^CNXMETAL\n"      # Metal
        "^CNXIT\n"         # IT
        "^CNXENERGY\n"     # Energy
        "^CNXREALTY\n"     # Realty
        "^CNXPSUBANK\n"    # PSU Bank
        "^CNXMEDIA\n"      # Media
        "^CNXINFRA\n"      # Infrastructure
        "^CNXFMCG\n"       # FMCG
        "^CNXSERVICE\n"    # Services
        "^CNXFIN\n"          # Financial Services
        "NIFTY_FIN_SERVICE.NS" # Financial Services if CNXFIN doesn't work (yfinance can be inconsistent with index symbols)
    ),

    # ── Nifty 50 ──────────────────────────────────────
    "Nifty 50": (
        "ADANIENT.NS\n"
        "ADANIPORTS.NS\n"
        "APOLLOHOSP.NS\n"
        "ASIANPAINT.NS\n"
        "AXISBANK.NS\n"
        "BAJAJ-AUTO.NS\n"
        "BAJFINANCE.NS\n"
        "BAJAJFINSV.NS\n"
        "BEL.NS\n"
        "BHARTIARTL.NS\n"
        "CIPLA.NS\n"
        "COALINDIA.NS\n"
        "DRREDDY.NS\n"
        "EICHERMOT.NS\n"
        "ETERNAL.NS\n"
        "GRASIM.NS\n"
        "HCLTECH.NS\n"
        "HDFCBANK.NS\n"
        "HDFCLIFE.NS\n"
        "HINDALCO.NS\n"
        "HINDUNILVR.NS\n"
        "ICICIBANK.NS\n"
        "ITC.NS\n"
        "INFY.NS\n"
        "INDIGO.NS\n"
        "JSWSTEEL.NS\n"
        "JIOFIN.NS\n"
        "KOTAKBANK.NS\n"
        "LT.NS\n"
        "M&M.NS\n"
        "MARUTI.NS\n"
        "MAXHEALTH.NS\n"
        "NTPC.NS\n"
        "NESTLEIND.NS\n"
        "ONGC.NS\n"
        "POWERGRID.NS\n"
        "RELIANCE.NS\n"
        "SBILIFE.NS\n"
        "SHRIRAMFIN.NS\n"
        "SBIN.NS\n"
        "SUNPHARMA.NS\n"
        "TCS.NS\n"
        "TATACONSUM.NS\n"
        "TMPV.NS\n"
        "TATASTEEL.NS\n"
        "TECHM.NS\n"
        "TITAN.NS\n"
        "TRENT.NS\n"
        "ULTRACEMCO.NS\n"
        "WIPRO.NS"
    ),

    # ── Nifty 100 ──────────────────────────────────────
    "Nifty 100": (
        "ABB.NS\n"
        "ADANIENSOL.NS\n"
        "ADANIENT.NS\n"
        "ADANIGREEN.NS\n"
        "ADANIPORTS.NS\n"
        "ADANIPOWER.NS\n"
        "AMBUJACEM.NS\n"
        "APOLLOHOSP.NS\n"
        "ASIANPAINT.NS\n"
        "DMART.NS\n"
        "AXISBANK.NS\n"
        "BAJAJ-AUTO.NS\n"
        "BAJFINANCE.NS\n"
        "BAJAJFINSV.NS\n"
        "BAJAJHLDING.NS\n"
        "BAJAJHFL.NS\n"
        "BANKBARODA.NS\n"
        "BEL.NS\n"
        "BPCL.NS\n"
        "BHARTIARTL.NS\n"
        "BOSCHLTD.NS\n"
        "BRITANNIA.NS\n"
        "CGPOWER.NS\n"
        "CANBK.NS\n"
        "CHOLAFIN.NS\n"
        "CIPLA.NS\n"
        "COALINDIA.NS\n"
        "DLF.NS\n"
        "DIVISLAB.NS\n"
        "DRREDDY.NS\n"
        "EICHERMOT.NS\n"
        "ETERNAL.NS\n"
        "GAIL.NS\n"
        "GODREJCP.NS\n"
        "GRASIM.NS\n"
        "HCLTECH.NS\n"
        "HDFCBANK.NS\n"
        "HDFCLIFE.NS\n"
        "HAVELLS.NS\n"
        "HINDALCO.NS\n"
        "HAL.NS\n"
        "HINDUNILVR.NS\n"
        "HINDZINC.NS\n"
        "HYUNDAI.NS\n"
        "ICICIBANK.NS\n"
        "ICICIGILTS.NS\n"
        "ITC.NS\n"
        "INDHOTEL.NS\n"
        "IOC.NS\n"
        "IRFC.NS\n"
        "NAUKRI.NS\n"
        "INFY.NS\n"
        "INDIGO.NS\n"
        "JSWENERGY.NS\n"
        "JSWSTEEL.NS\n"
        "JINDALSTEL.NS\n"
        "JIOFIN.NS\n"
        "KOTAKBANK.NS\n"
        "LTM.NS\n"
        "LT.NS\n"
        "LICI.NS\n"
        "LODHA.NS\n"
        "M&M.NS\n"
        "MARUTI.NS\n"
        "MAXHEALTH.NS\n"
        "MAZDOCK.NS\n"
        "NTPC.NS\n"
        "NESTLEIND.NS\n"
        "ONGC.NS\n"
        "PIDILITIND.NS\n"
        "PFC.NS\n"
        "POWERGRID.NS\n"
        "PNB.NS\n"
        "RECLLTD.NS\n"
        "RELIANCE.NS\n"
        "SBILIFE.NS\n"
        "MOTHERSON.NS\n"
        "SHREECEM.NS\n"
        "SHRIRAMFIN.NS\n"
        "ENRINOV.NS\n"
        "SIEMENS.NS\n"
        "SOLARINDS.NS\n"
        "SBIN.NS\n"
        "SUNPHARMA.NS\n"
        "TVSMOTOR.NS\n"
        "TCS.NS\n"
        "TATACONSUM.NS\n"
        "TMPV.NS\n"
        "TATAPOWER.NS\n"
        "TATASTEEL.NS\n"
        "TECHM.NS\n"
        "TITAN.NS\n"
        "TORNTPHARM.NS\n"
        "TRENT.NS\n"
        "ULTRACEMCO.NS\n"
        "UNITDSPR.NS\n"
        "VBL.NS\n"
        "VEDL.NS\n"
        "WIPRO.NS\n"
        "ZYDUSLIFE.NS"
    ),

# ── Nifty Midcap 50 ──────────────────────────────────────
    "Nifty Midcap 50": (
        "APLAPOLLO.NS\n"
        "AUBANK.NS\n"
        "ASHOKLEY.NS\n"
        "AUROPHARMA.NS\n"
        "BSE.NS\n"
        "BHARATFORG.NS\n"
        "BHEL.NS\n"
        "COFORGE.NS\n"
        "COLPAL.NS\n"
        "CUMMINSIND.NS\n"
        "DABUR.NS\n"
        "DIXON.NS\n"
        "FEDERALBNK.NS\n"
        "FORTIS.NS\n"
        "GMRAIRPORT.NS\n"
        "GODREJPROP.NS\n"
        "HDFCAMC.NS\n"
        "HEROMOTOCO.NS\n"
        "HINDPETRO.NS\n"
        "IDFCFIRSTB.NS\n"
        "IRCTC.NS\n"
        "INDUSTOWER.NS\n"
        "INDUSINDBK.NS\n"
        "JUBLFOOD.NS\n"
        "LUPIN.NS\n"
        "MANKIND.NS\n"
        "MARICO.NS\n"
        "MFSL.NS\n"
        "MPHASIS.NS\n"
        "MUTHOOTFIN.NS\n"
        "NHPC.NS\n"
        "NMDC.NS\n"
        "OBEROIRLTY.NS\n"
        "OIL.NS\n"
        "PAYTM.NS\n"
        "OFSS.NS\n"
        "POLICYBZR.NS\n"
        "PIIND.NS\n"
        "PAGEIND.NS\n"
        "PERSISTENT.NS\n"
        "PHOENIXLTD.NS\n"
        "POLYCAB.NS\n"
        "PRESTIGE.NS\n"
        "SBICARD.NS\n"
        "SRF.NS\n"
        "SUPREMEIND.NS\n"
        "SUZLON.NS\n"
        "TIINDIA.NS\n"
        "UPL.NS\n"
        "YESBANK.NS"
    ),

# ── Nifty Smallcap 50 ──────────────────────────────────────
    "Nifty Smallcap 50": (
        "AARTIIND.NS\n"
        "ABREL.NS\n"
        "AEGISLOG.NS\n"
        "AFFLE.NS\n"
        "ARE&M.NS\n"
        "AMBER.NS\n"
        "ANGELONE.NS\n"
        "ASTERDM.NS\n"
        "BANDHANBNK.NS\n"
        "CESC.NS\n"
        "CASTROLIND.NS\n"
        "CDSL.NS\n"
        "CHOLAHLDNG.NS\n"
        "CAMS.NS\n"
        "CROMPTON.NS\n"
        "CYIENT.NS\n"
        "DELHIVERY.NS\n"
        "LALPATHLAB.NS\n"
        "FSL.NS\n"
        "FIVESTAR.NS\n"
        "GLAND.NS\n"
        "HSCL.NS\n"
        "IIFL.NS\n"
        "IEX.NS\n"
        "INOXWIND.NS\n"
        "JBCHEPHARM.NS\n"
        "KARURVYSYA.NS\n"
        "KAYNES.NS\n"
        "KEC.NS\n"
        "KFINTECH.NS\n"
        "LAURUSLABS.NS\n"
        "MANAPPURAM.NS\n"
        "MCX.NS\n"
        "NATCOPHARM.NS\n"
        "NBCC.NS\n"
        "NH.NS\n"
        "NAVINFLUOR.NS\n"
        "NEULANDLAB.NS\n"
        "PGEL.NS\n"
        "PNBHOUSING.NS\n"
        "PPLPHARMA.NS\n"
        "POONAWALLA.NS\n"
        "RADICO.NS\n"
        "REDINGTON.NS\n"
        "RPOWER.NS\n"
        "TATACHEM.NS\n"
        "RAMCOCEM.NS\n"
        "WELCORP.NS\n"
        "WOCKPHARMA.NS\n"
        "ZENSARTECH.NS"
    ),

# ── Nifty Auto ─────────────────────────────────────────────
    "Nifty Auto": (
        "ASHOKLEY.NS\n"
        "BAJAJ-AUTO.NS\n"
        "BHARATFORG.NS\n"
        "BOSCHLTD.NS\n"
        "EICHERMOT.NS\n"
        "EXIDEIND.NS\n"
        "HEROMOTOCO.NS\n"
        "M&M.NS\n"
        "MARUTI.NS\n"
        "MOTHERSON.NS\n"
        "SONACOMS.NS\n"
        "TVSMOTOR.NS\n"
        "TMPV.NS\n"
        "TIINDIA.NS\n"
        "UNOMINDA.NS"
    ),

# ── Nifty Bank ─────────────────────────────────────────────
    "Nifty Bank": (
        "AUBANK.NS\n"
        "AXISBANK.NS\n"
        "BANKBARODA.NS\n"
        "CANBK.NS\n"
        "FEDERALBNK.NS\n"
        "HDFCBANK.NS\n"
        "ICICIBANK.NS\n"
        "IDFCFIRSTB.NS\n"
        "INDUSINDBK.NS\n"
        "KOTAKBANK.NS\n"
        "PNB.NS\n"
        "SBIN.NS\n"
        "UNIONBANK.NS\n"
        "YESBANK.NS"
    ),

# ── Nifty Chemicals ────────────────────────────────────────
    "Nifty Chemicals": (
        "AARTIIND.NS\n"
        "ATUL.NS\n"
        "BAYERCROP.NS\n"
        "CHAMBLFERT.NS\n"
        "COROMANDEL.NS\n"
        "DEEPAKNTR.NS\n"
        "EIDPARRY.NS\n"
        "FLUOROCHEM.NS\n"
        "GNFC.NS\n"
        "HSCL.NS\n"
        "LINDEINDIA.NS\n"
        "NAVINFLUOR.NS\n"
        "PCBL.NS\n"
        "PIIND.NS\n"
        "PIDILITIND.NS\n"
        "SRF.NS\n"
        "SOLARINDS.NS\n"
        "SUMICHEM.NS\n"
        "TATACHEM.NS\n"
        "UPL.NS"
    ),

# ── Nifty FMCG ─────────────────────────────────────────────
    "Nifty FMCG": (
        "BRITANNIA.NS\n"
        "COLPAL.NS\n"
        "DABUR.NS\n"
        "EMAMILTD.NS\n"
        "GODREJCP.NS\n"
        "HINDUNILVR.NS\n"
        "ITC.NS\n"
        "MARICO.NS\n"
        "NESTLEIND.NS\n"
        "PATANJALI.NS\n"
        "RADICO.NS\n"
        "TATACONSUM.NS\n"
        "UBL.NS\n"
        "UNITDSPR.NS\n"
        "VBL.NS"
    ),
    # ── Nifty IT ───────────────────────────────────────────────
    "Nifty IT": (
        "COFORGE.NS\n"
        "HCLTECH.NS\n"
        "INFY.NS\n"
        "LTM.NS\n"
        "MPHASIS.NS\n"
        "OFSS.NS\n"
        "PERSISTENT.NS\n"
        "TCS.NS\n"
        "TECHM.NS\n"
        "WIPRO.NS"
    ),

# ── Nifty Oil & Gas ────────────────────────────────────────
    "Nifty Oil & Gas": (
        "ATGL.NS\n"
        "AEGISLOG.NS\n"
        "BPCL.NS\n"
        "CASTROLIND.NS\n"
        "GAIL.NS\n"
        "GUJGASLTD.NS\n"
        "GSPL.NS\n"
        "HINDPETRO.NS\n"
        "IOC.NS\n"
        "IGL.NS\n"
        "MGL.NS\n"
        "ONGC.NS\n"
        "OIL.NS\n"
        "PETRONET.NS\n"
        "RELIANCE.NS"
    ),

    # ── Custom ────────────────────────────────────────────────────────
    "Custom (Type your own)": "RELIANCE.NS\nINFY.NS",
}
        
        # 2. Add a dropdown for the user to select a basket
        selected_basket = st.selectbox(
            "Quick-Load Baskets ⚡", 
            options=list(baskets.keys()),
            help="Select a pre-made list of symbols, or choose 'Custom' to type your own."
        )
        
        # 3. Set the text box content based on their choice
        default_val = baskets[selected_basket]
        if selected_basket == "Custom (Type your own)":
            default_val = "RELIANCE.NS\nINFY.NS" # Just a placeholder so it isn't totally blank

        # 4. The actual text area
        sectors_text = st.text_area(
            "Enter Sector/Stock symbols (one per line)",
            value=default_val,
            height=220,
            help="Enter each sector/stock symbol on a new line. You can edit the quick-loaded lists here."
        )

        sectors = [s.strip() for s in sectors_text.split('\n') if s.strip()]
        show_tail = st.checkbox(label="Show Tail", value=False)

    if st.button("Run Analysis", type="primary"):
        if not sectors:
            st.error("Please enter at least one sector symbol")
            return

        with st.spinner("Fetching data and calculating metrics..."):
            benchmark_data, benchmark_failed = fetch_data([benchmark], period)

            if benchmark not in benchmark_data:
                st.error(f"Could not fetch data for benchmark: {benchmark}")
                return

            sector_data, failed_sectors = fetch_data(sectors, period)

            if not sector_data:
                st.error("Could not fetch data for any sectors")
                return

            if failed_sectors:
                st.warning(f"Could not fetch data for: {', '.join(failed_sectors)}")

            results = {}
            benchmark_prices = benchmark_data[benchmark]

            for symbol, prices in sector_data.items():
                try:
                    rel_strength, rel_momentum = calculate_relative_strength(prices, benchmark_prices, 10)

                    if rel_strength is not None:
                        rs_ratio = calculate_jdk_rs_ratio(rel_strength)
                        rs_momentum = calculate_jdk_rs_momentum(rs_ratio)

                        results[symbol] = {
                            'rs_ratio': rs_ratio,
                            'rs_momentum': rs_momentum,
                            'relative_strength': rel_strength
                        }
                except Exception as e:
                    st.warning(f"Error calculating metrics for {symbol}: {str(e)}")
                    continue

            if not results:
                st.error("Could not calculate metrics for any sectors")
                return

            # FIX: Explicitly pass show_tail as a keyword argument
            fig = create_rrg_plot(results, tail_length, show_tail=show_tail)
            if fig is not None:
                st.plotly_chart(fig, width='stretch')

            st.subheader("Relative Positions of Sector/Stock")
            summary_data = []

            for symbol, data in results.items():
                if data['rs_ratio'] is not None and data['rs_momentum'] is not None:
                    # FIX: Align data for summary table to match the plot's final data point
                    df_aligned = pd.DataFrame({
                        'rs_ratio': data['rs_ratio'],
                        'rs_momentum': data['rs_momentum']
                    }).dropna()
                    
                    if not df_aligned.empty:
                        current_ratio = df_aligned['rs_ratio'].iloc[-1]
                        current_momentum = df_aligned['rs_momentum'].iloc[-1]
                        quadrant, color, icon = get_quadrant_info(current_ratio, current_momentum)

                        summary_data.append({
                            'Sector': symbol,
                            'RS-Ratio': f"{current_ratio:.2f}",
                            'RS-Momentum': f"{current_momentum:.2f}",
                            'Quadrant': f"{quadrant}"
                        })

            if summary_data:
                df_summary = pd.DataFrame(summary_data)
                st.dataframe(df_summary, width='stretch', hide_index=True)

            with st.expander("Understanding the Relative Rotation Graph"):
                st.markdown("""
                    **Quadrants Explanation:**

                    **Leading (Top-Right)**: High relative strength, positive momentum
                    - Sectors outperforming benchmark with increasing momentum

                    **Weakening (Bottom-Right)**: High relative strength, negative momentum  
                    - Sectors still outperforming but losing momentum

                    **Lagging (Bottom-Left)**: Low relative strength, negative momentum
                    - Sectors underperforming benchmark with decreasing momentum

                    **Improving (Top-Left)**: Low relative strength, positive momentum
                    - Sectors underperforming but gaining momentum

                    **How to Read:**
                    - **RS-Ratio > 100**: Sector outperforming benchmark
                    - **RS-Ratio < 100**: Sector underperforming benchmark  
                    - **RS-Momentum > 0**: Relative strength is improving
                    - **RS-Momentum < 0**: Relative strength is declining
                    - **Tail**: Shows the trajectory of sector movement over time
                    """)
                
    st.markdown("""
        <hr style="margin-top: 3rem; border-color: #e0e0e0;">
        <div style="text-align: center; padding: 1rem 0; color: #888; font-size: 0.85rem;">
            <a href="https://github.com/VaibhavDaveDev/Relative-Rotation-Graphs" target="_blank"
               style="display: inline-flex; align-items: center; gap: 8px; text-decoration: none; color: #444; font-weight: 500;">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="#333">
                    <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/>
                </svg>
                VaibhavDaveDev / Relative-Rotation-Graphs
            </a>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()