import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import datetime

# 1. Page Configuration
st.set_page_config(page_title="Fintech Analytics Dashboard", layout="wide")
st.title("Fintech Stock Analytics Dashboard")
st.markdown("Bridge your CS and Finance skills. This app fetches real-time market data and calculates moving averages.")

# 2. Sidebar Controls
st.sidebar.header("Dashboard Controls")
ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL, MSFT, TSLA)", value="AAPL")

# Date range selection — use datetime.date to avoid type issues
default_start = datetime.date(2025, 1, 1)
default_end = datetime.date.today()
start_date = st.sidebar.date_input("Start Date", value=default_start)
end_date = st.sidebar.date_input("End Date", value=default_end)

# Validate date range
if start_date > end_date:
    st.sidebar.error("Start Date must be before or equal to End Date.")

# Moving Average parameter
ma_window = st.sidebar.slider("Simple Moving Average (SMA) Window", min_value=5, max_value=100, value=20)

# 3. Fetching Data
@st.cache_data
def load_data(stock_ticker, start, end):
    # Convert to ISO-format strings for yfinance
    start_str = start.isoformat() if isinstance(start, (datetime.date, datetime.datetime)) else str(start)
    end_str = end.isoformat() if isinstance(end, (datetime.date, datetime.datetime)) else str(end)
    df = yf.download(stock_ticker, start=start_str, end=end_str)
    return df

try:
    # Only attempt load if dates are valid
    if start_date <= end_date:
        data = load_data(ticker, start_date, end_date)
    else:
        data = pd.DataFrame()

    if data.empty:
        st.error("No data found. Please enter a valid ticker or adjust dates.")
    else:
        # Calculate Moving Average
        data['SMA'] = data['Close'].rolling(window=ma_window).mean()

        # If not enough rows for metrics, show a helpful message
        if len(data) < 2:
            st.warning("Not enough data to calculate metrics (need at least 2 rows). Displaying available raw data.")
            with st.expander("View Raw Financial Data"):
                st.dataframe(data.tail(10))
        else:
            # 4. Metric Highlights
            last_close = float(data['Close'].iloc[-1])
            prev_close = float(data['Close'].iloc[-2])
            # Guard against division by zero just in case
            if prev_close == 0:
                percent_change = float('nan')
            else:
                percent_change = ((last_close - prev_close) / prev_close) * 100

            col1, col2 = st.columns(2)
            with col1:
                st.metric(label=f"Current Price ({ticker})", value=f"${last_close:.2f}", delta=(f"{percent_change:.2f}%" if pd.notna(percent_change) else "N/A"))

            # Handle SMA possibly being NaN (not enough rows for window)
            sma_last = data['SMA'].iloc[-1]
            sma_display = "N/A" if pd.isna(sma_last) else f"${float(sma_last):.2f}"

            with col2:
                st.metric(label=f"{ma_window}-Day Simple Moving Average", value=sma_display)

            # 5. Visualizations (Interactive Plotly Chart)
            st.subheader("Stock Price Trend & Moving Average")

            fig = go.Figure()
            # Closing price line
            fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Close Price', line=dict(color='royalblue', width=2)))
            # SMA line
            fig.add_trace(go.Scatter(x=data.index, y=data['SMA'], name=f'{ma_window}-Day SMA', line=dict(color='orange', width=2, dash='dash')))

            fig.update_layout(
                template="plotly_dark",
                xaxis_title="Date",
                yaxis_title="Price (USD)",
                margin=dict(l=20, r=20, t=20, b=20),
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)

            # 6. Raw Data Table (Financial Analysts love raw numbers)
            with st.expander("View Raw Financial Data"):
                st.dataframe(data.tail(10))

except Exception as e:
    st.error(f"Error loading ticker data: {e}")
