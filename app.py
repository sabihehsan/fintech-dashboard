import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. Page Configuration
st.set_page_config(page_title="Fintech Analytics Dashboard", layout="wide")
st.title("📈 Stock Analytics Dashboard")
st.markdown("Fetches real-time market data and calculates moving averages.")

# 2. Sidebar Controls
st.sidebar.header("Dashboard Controls")
ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL, MSFT, TSLA)", value="AAPL")

# Date range selection
start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2025-01-01"))
end_date = st.sidebar.date_input("End Date", value=pd.to_datetime("today"))

# Moving Average parameter
ma_window = st.sidebar.slider("Simple Moving Average (SMA) Window", min_value=5, max_value=100, value=20)

# 3. Fetching Data
@st.cache_data # Caches data so it doesn't fetch on every button click
def load_data(stock_ticker, start, end):
    df = yf.download(stock_ticker, start=start, end=end)
    return df

try:
    data = load_data(ticker, start_date, end_date)
    
    if data.empty:
        st.error("No data found. Please enter a valid ticker or adjust dates.")
    else:
        # FIX: Force 'Close' column to be a 1D Series if yfinance returned a multi-index DataFrame
        if isinstance(data['Close'], pd.DataFrame):
            close_series = data['Close'].squeeze()
        else:
            close_series = data['Close']

        # Calculate Moving Average using our clean Series
        data['SMA'] = close_series.rolling(window=ma_window).mean()
        sma_series = data['SMA'].squeeze() if isinstance(data['SMA'], pd.DataFrame) else data['SMA']

        # 4. Metric Highlights
        last_close = float(close_series.iloc[-1])
        prev_close = float(close_series.iloc[-2])
        percent_change = ((last_close - prev_close) / prev_close) * 100

        col1, col2 = st.columns(2)
        with col1:
            st.metric(label=f"Current Price ({ticker})", value=f"${last_close:.2f}", delta=f"{percent_change:.2f}%")
        with col2:
            st.metric(label=f"{ma_window}-Day Simple Moving Average", value=f"${float(sma_series.iloc[-1]):.2f}")

        # 5. Visualizations (Interactive Plotly Chart)
        st.subheader("Stock Price Trend & Moving Average")
        
        fig = go.Figure()
        # Closing price line
        fig.add_trace(go.Scatter(x=data.index, y=close_series, name='Close Price', line=dict(color='royalblue', width=2)))
        # SMA line
        fig.add_trace(go.Scatter(x=data.index, y=sma_series, name=f'{ma_window}-Day SMA', line=dict(color='orange', width=2, dash='dash')))
        
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
