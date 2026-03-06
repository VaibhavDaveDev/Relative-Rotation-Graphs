# [Relative Rotation Graphs (RRG) - Interactive Analysis Tool](https://relative-rotation-graphs.streamlit.app/)

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://relative-rotation-graphs.streamlit.app/)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.0+-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

<div align="center">
  <p><strong>Interactive web application for visualizing stock and sector rotation patterns using Relative Rotation Graphs</strong></p>
  <p>
    <a href="#-what-is-a-relative-rotation-graph-rrg">What is RRG</a> •
    <a href="#-prerequisites">Prerequisites</a> •
    <a href="#installation">Installation</a> •
    <a href="#-usage">Usage</a> •
    <a href="#-features">Features</a> •
    <a href="#-practical-applications">Applications</a> •
    <a href="#-technical-details">Technical Details</a>
  </p>
</div>
---

An interactive web application built with Streamlit that generates Relative Rotation Graphs (RRG) for smarter investing and trading decisions. Visualize sector or stock rotation patterns and identify market leaders and laggards at a glance.

## 🎯 What is a Relative Rotation Graph (RRG)?

In the world of investing and trading, identifying market leaders and laggards is crucial. Traditional price charts and indicators provide valuable insights, but they often fail to visualize sector or stock rotation in a clear and intuitive manner. This is where Relative Rotation Graphs (RRG) come into play.

RRG charts allow traders and investors to compare the relative strength and momentum of multiple securities against a benchmark, revealing how different stocks, sectors, or asset classes are rotating through various performance phases.
<img width="1024" height="629" alt="image" src="https://github.com/user-attachments/assets/97de85f1-3934-4f6d-b65b-1c61197d3eba" />

### Key Metrics

RRG is a visualization tool that plots securities based on two key indicators:

- **JdK RS-Ratio (Relative Strength Ratio)** – Measures a security's relative strength against a benchmark. Higher values indicate outperformance, while lower values suggest underperformance.
- **JdK RS-Momentum (Relative Strength Momentum)** – Measures the rate of change of the relative strength. Increasing momentum suggests improving strength, while decreasing momentum signals weakening performance.

### The Four Quadrants

By plotting these values on a two-dimensional plane, RRG divides the chart into four quadrants:

#### 🔵 Improving (Look for Buys) – Top-left quadrant
- Securities in this quadrant have weak relative strength but are gaining momentum
- These are potential turnaround candidates that may soon transition into the leading quadrant
- Ideal for investors looking for early entry points into emerging leaders

#### 🟢 Leading (Hold) – Top-right quadrant
- Securities in this quadrant have both high relative strength and strong momentum
- These are the outperformers of the market
- Typically, stocks or sectors here continue to perform well, making them attractive for holding or further accumulation

#### 🟠 Weakening (Look for Sells) – Bottom-right quadrant
- Securities in this quadrant still have high relative strength but are losing momentum
- This often indicates a mature uptrend that may be slowing down
- If a security remains in this quadrant for an extended period, it may transition into the lagging quadrant, signaling a potential exit point

#### 🔴 Lagging (Avoid) – Bottom-left quadrant
- Securities in this quadrant exhibit both weak relative strength and weak momentum
- These are underperformers that should be avoided or shorted
- Investors should be cautious about bottom fishing unless there is a clear sign of reversal

## 📊 Understanding Rotation Patterns

RRG charts provide more than just a snapshot; they also illustrate how securities rotate through different phases over time. By analyzing the tail movement, investors can gain deeper insights into market dynamics.

### Clockwise Rotation – The most common pattern
- Securities tend to move from improving → leading → weakening → lagging in a clockwise fashion
- This rotation aligns with market cycles and sector rotation

### Sharp Turns in Momentum
- A sudden move from lagging to improving suggests a strong reversal
- Conversely, a sharp drop from leading to weakening may indicate an overbought condition

### Length of the Tail
- A long tail signifies high volatility and strong trends
- A short tail suggests stability but slower movement

### Securities Crossing Quadrants
- Stocks moving from improving to leading are prime buy candidates
- Stocks moving from weakening to lagging should be avoided

## 🌐 Live Demo

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://relative-rotation-graphs.streamlit.app/)

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. **Clone the repository**
```bash
git clone https://github.com/VaibhavDaveDev/Relative-Rotation-Graphs
cd relative-rotation-graphs
```

2. **Create a virtual environment (recommended)**
```bash
python -m venv .venv
```

3. **Activate the virtual environment**
   - Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```

4. **Install required packages**
```bash
pip install -r requirements.txt
```

## 🎮 Usage

1. **Run the Streamlit app**
```bash
streamlit run "Relative Rotation Graphs.py"
```

2. **Configure your analysis**
   - Set your benchmark (e.g., ^NSEI for NIFTY 50, ^GSPC for S&P 500)
   - Adjust the lookback period slider
   - Modify the tail length for trend visualization
   - Toggle the "Show Trail/Tail" checkbox to see historical movement

3. **Add your stocks**
   - Use the text area to add stock symbols (one per line)
   - For Indian stocks, use the .NS suffix (e.g., RELIANCE.NS)
   - For US stocks, use regular ticker symbols (e.g., AAPL, MSFT)

4. **Generate the RRG**
   - Click the "Generate RRG" button
   - Wait for data to download (typically 5-15 seconds)
   - Analyze the chart and summary table

## 🚀 Features

- **Interactive Web Interface**: Built with Streamlit for easy use
- **Customizable Analysis**: 
  - Choose any benchmark (default: NIFTY 50)
  - Adjust lookback period (60-500 days)
  - Control tail length for trend visualization
  - Toggle trail visibility
- **Real-time Data**: Fetches live market data using Yahoo Finance
- **Visual Insights**: Interactive Plotly charts with hover details
- **Summary Table**: Quick view of RS-Ratio and RS-Momentum values
- **Pre-configured**: Comes with all NIFTY 50 stocks pre-loaded

## 💡 Practical Applications

### Sector Rotation Strategy
Investors can use RRG to identify which sectors are gaining strength and allocate capital accordingly. For example, if technology is moving from improving to leading, it may be a good time to increase exposure to tech stocks.

### Stock Selection
RRG helps traders focus on stocks with strong relative performance rather than just absolute price movements.

### Portfolio Diversification
By identifying sector rotations, investors can balance their portfolios across leading and improving sectors.

### Market Timing
Watching how securities rotate through quadrants helps investors time their entries and exits more effectively.

## ⚠️ Limitations

While RRG is a powerful tool, it should not be used in isolation. Here are a few things to keep in mind:

- **Lagging Indicator** – Since it relies on historical data, RRG may not always predict sudden market reversals
- **Works Best for Groups** – It is most effective when comparing multiple securities rather than analyzing a single stock
- **Needs Confirmation** – Combining RRG with other technical indicators like moving averages, RSI, or MACD can improve accuracy

## 📁 Project Structure

```
relative-rotation-graphs/
│
├── Relative Rotation Graphs.py    # Main Streamlit application
├── requirements.txt                # Python dependencies
├── README.md                       # This file
└── .venv/                         # Virtual environment (not tracked)
```
## Screenshots
<img width="2185" height="857" alt="image" src="https://github.com/user-attachments/assets/46edb49e-8ba7-4e0a-847f-c1c6f25ee6a8" />
<img width="737" height="458" alt="image" src="https://github.com/user-attachments/assets/2327c03d-a9c9-43b1-9f07-abbbb83ccd5a" />
<img width="1448" height="673" alt="image" src="https://github.com/user-attachments/assets/fd0804bb-c639-4732-a2a6-47b48a4e8e05" />

## 🔧 Technical Details

### Calculation Methodology

1. **Relative Strength (RS)**: Price of security / Price of benchmark
2. **JdK RS-Ratio**: (RS / 40-period Moving Average of RS) × 100
3. **JdK RS-Momentum**: (Current RS-Ratio / RS-Ratio 10 periods ago) × 100

### Data Requirements
- Minimum 50 data points required for calculation
- Additional 80-day buffer added for rolling calculations
- Automatic alignment of dates between securities and benchmark

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- RRG methodology developed by Julius de Kempenaer
- Market data provided by Yahoo Finance via yfinance library
- Built with Streamlit, Plotly, and Pandas
- Inspired by the article: [Build and Use Relative Rotation Graphs (RRG) for Smarter Investing](https://fabtrader.in/build-and-use-relative-rotation-graphs-rrg-for-smarter-investing-using-python/) by FabTrader

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

## 🎓 Disclaimer

This tool is for educational and informational purposes only. It should not be considered as financial advice. Always do your own research and consult with a qualified financial advisor before making investment decisions.

---

**Happy Investing! 📈**
