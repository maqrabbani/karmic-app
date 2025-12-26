import streamlit as st
import pandas as pd
import numpy as np

# ==========================================
# 1. SETUP & CONFIGURATION
# ==========================================
st.set_page_config(page_title="Karmic Seed Pricing Simulator", layout="wide")
st.title("🌱 Karmic Seed: Pricing Decision Support Tool")

# ==========================================
# 2. DATA LOADER (The "Brain")
# ==========================================
@st.cache_data
def load_and_prep_data():
    # Load Files
    try:
        df_pricing = pd.read_csv('Pricing_Data.csv')
        df_competitor = pd.read_csv('Competitor_Data.csv')
        df_returns = pd.read_csv('Returns_Data.csv')
        df_inventory = pd.read_csv('Inventory_Health.csv')
        df_sales = pd.read_csv('Historical_Sales.csv')
    except FileNotFoundError:
        st.error("❌ CSV files not found. Please place Pricing_Data.csv, Competitor_Data.csv, etc. in the same folder.")
        return pd.DataFrame()

    # Helpers
    def clean_currency(x):
        if isinstance(x, str): return float(x.replace('$', '').replace(',', '').strip())
        return x
    def clean_percent(x):
        if isinstance(x, str): return float(x.replace('%', '').strip())
        return 0.0
    def clean_numeric(x):
        if isinstance(x, str): return float(x.replace(',', '').strip())
        return 0.0

    # Cleaning
    df_pricing['True_Unit_Cost'] = df_pricing['True_Unit_Cost'].apply(clean_currency)
    df_pricing['Current_Price'] = df_pricing['Current_Price'].apply(clean_currency)
    df_pricing['Min_Margin'] = df_pricing['Minimum_Acceptable_Margin_%'].apply(clean_percent)
    df_pricing['Target_Margin'] = df_pricing['Target_Gross_Margin_%'].apply(clean_percent)
    
    df_competitor['Avg_Competitor_Price'] = df_competitor['Avg_Competitor_Price'].apply(clean_currency)
    
    df_returns['Returns_Qty'] = df_returns['Return Quantity \n(Last 90 days)'].apply(clean_numeric)
    
    df_inventory['Days_of_Supply'] = df_inventory['days-of-supply'].apply(clean_numeric)

    # Sales Aggregation for Return Rate Calc
    df_sales['Units Ordered'] = df_sales['Units Ordered'].astype(float)
    sales_agg = df_sales.groupby('SKU')['Units Ordered'].sum().reset_index()

    # Merging
    df = pd.merge(df_pricing, df_competitor[['SKU', 'Avg_Competitor_Price']], on='SKU', how='left')
    df = pd.merge(df, df_inventory[['SKU', 'Days_of_Supply']], on='SKU', how='left')
    df = pd.merge(df, sales_agg, on='SKU', how='left')
    df = pd.merge(df, df_returns[['SKU', 'Returns_Qty']], on='SKU', how='left')
    
    # Calculate Return Rate
    df['Return_Rate'] = (df['Returns_Qty'] / df['Units Ordered']) * 100
    df['Return_Rate'] = df['Return_Rate'].fillna(0)
    
    return df

df_master = load_and_prep_data()

# ==========================================
# 3. SIDEBAR: SELECT YOUR REAL SKU
# ==========================================
st.sidebar.header("📝 SKU Selector")

if not df_master.empty:
    # Dropdown to select a real SKU
    sku_list = df_master['SKU'].unique().tolist()
    selected_sku = st.sidebar.selectbox("Select a Product:", sku_list)
    
    # Get data for that SKU
    sku_data = df_master[df_master['SKU'] == selected_sku].iloc[0]
    
    # Pre-fill variables
    default_cost = float(sku_data['True_Unit_Cost'])
    default_price = float(sku_data['Current_Price'])
    default_comp = float(sku_data['Avg_Competitor_Price'])
    default_min_margin = float(sku_data['Min_Margin'])
    default_target_margin = float(sku_data['Target_Margin'])
    default_inventory = float(sku_data['Days_of_Supply'])
    default_returns = float(sku_data['Return_Rate'])
else:
    st.sidebar.warning("Using dummy data (CSVs failed load)")
    default_cost = 15.0
    default_price = 22.0
    default_comp = 25.0
    default_min_margin = 20.0
    default_target_margin = 40.0
    default_inventory = 45.0
    default_returns = 2.5

st.sidebar.markdown("---")
st.sidebar.info("👇 Adjust these to test 'What-If' scenarios")

# Input widgets (Pre-filled with Real Data)
cost_input = st.sidebar.number_input("True Unit Cost ($)", value=default_cost, step=0.50)
curr_price_input = st.sidebar.number_input("Current Selling Price ($)", value=default_price, step=0.50)
comp_price_input = st.sidebar.number_input("Avg Competitor Price ($)", value=default_comp, step=0.50)

st.sidebar.subheader("Business Constraints")
min_margin_input = st.sidebar.slider("Min Acceptable Margin (%)", 0.0, 60.0, default_min_margin)
target_margin_input = st.sidebar.slider("Target Gross Margin (%)", 10.0, 80.0, default_target_margin)

st.sidebar.subheader("Health Signals")
inventory_input = st.sidebar.number_input("Days of Supply", value=default_inventory)
returns_input = st.sidebar.slider("Return Rate (%)", 0.0, 20.0, default_returns)

# ==========================================
# 4. CALCULATION ENGINE
# ==========================================
def calculate_recommendation(cost, current_price, competitor_price, min_margin, target_margin, returns_pct, inventory_days):
    if current_price == 0: return 0, "ERROR", "Price is 0", 0
    
    margin_current = (current_price - cost) / current_price
    min_price = cost / (1 - (min_margin/100))
    target_price = cost / (1 - (target_margin/100))
    
    strategy = "MAINTAIN"
    rec_price = current_price
    
    # Logic Tree
    if returns_pct > 8.0:
        return current_price, "⛔ BLOCKED (High Returns)", "Fix Quality First", margin_current
        
    if current_price < min_price:
        strategy = "📈 PROFIT RECOVERY"
        rec_price = min_price 
    elif inventory_days > 120:
        strategy = "📉 LIQUIDATE"
        rec_price = max(cost * 1.05, competitor_price * 0.95)
    elif current_price < (competitor_price - 1.0) and margin_current < (target_margin/100):
        strategy = "🚀 MARKET CATCH-UP"
        rec_price = min(target_price, competitor_price - 0.50)
        
    return round(rec_price, 2), strategy, "optimize margin", margin_current

# ==========================================
# 5. MAIN DASHBOARD RENDER
# ==========================================
if st.button("Run Analysis", type="primary"):
    new_price, strategy, reason, curr_margin = calculate_recommendation(
        cost_input, curr_price_input, comp_price_input, 
        min_margin_input, target_margin_input, 
        returns_input, inventory_input
    )
    
    # Top Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current Margin", f"{curr_margin:.1%}", delta_color="normal")
    c2.metric("Competitor Gap", f"${curr_price_input - comp_price_input:.2f}", 
              delta="-Undercut" if curr_price_input < comp_price_input else "+Premium")
    
    color = "red" if "BLOCKED" in strategy else "green" if "CATCH-UP" in strategy or "RECOVERY" in strategy else "orange"
    c3.markdown(f"**Strategy:** :{color}[{strategy}]")
    c4.metric("Recommended Price", f"${new_price:.2f}", delta=f"${new_price - curr_price_input:.2f}")

    st.markdown("---")
    
    # Charts & Logic
    col_chart, col_text = st.columns([2, 1])
    
    with col_chart:
        st.subheader("Price Position")
        chart_df = pd.DataFrame({
            'Metric': ['Unit Cost', 'Min Margin Floor', 'Current Price', 'Target Ideal', 'Competitor Avg'],
            'Price ($)': [cost_input, cost_input/(1-min_margin_input/100), curr_price_input, cost_input/(1-target_margin_input/100), comp_price_input]
        })
        st.bar_chart(chart_df.set_index('Metric'))

    with col_text:
        st.subheader("Why this price?")
        st.write(f"""
        - **Cost Basis:** ${cost_input:.2f}
        - **Floor Price (Min Margin):** ${cost_input/(1-min_margin_input/100):.2f}
        - **Competitor Anchor:** ${comp_price_input:.2f}
        - **Inventory Health:** {inventory_input} days
        """)
        if "RECOVERY" in strategy:
            st.warning(f"⚠️ Your current price is below the {min_margin_input}% margin floor. We must raise it.")
        elif "BLOCKED" in strategy:
            st.error(f"🛑 Returns are {returns_input}% (Critical > 8%). Do not raise price.")

else:
    st.info("👈 Select a SKU from the sidebar to load its real data.")
