import streamlit as st
import pandas as pd
import numpy as np

# ==========================================
# 1. SETUP & DESIGN
# ==========================================
st.set_page_config(page_title="Platinum Pricing Engine", layout="wide")


st.title("🍽️ XYZ Pricing Simulator")

This analysis integrates historical sales, ad performance, pricing, competitor data, returns, and inventory health to:
- Calculate advanced unit economics (CPA, return costs, net profit)
- Optimize pricing suggestions
- Generate actionable strategies
- Visualize top 10 critical charts for business insights
 Platinum Pricing Simulator")
st.markdown("### Operational Offense/Defense Engine")
st.markdown("---")

# ==========================================
# 2. ROBUST DATA LOADER
# ==========================================
@st.cache_data
def load_data():
    try:
        df_pricing = pd.read_csv('Pricing_Data.csv')
        df_competitor = pd.read_csv('Competitor_Data.csv')
        df_returns = pd.read_csv('Returns_Data.csv')
        df_inventory = pd.read_csv('Inventory_Health.csv')
        df_sales = pd.read_csv('Historical_Sales.csv')
        df_ads = pd.read_csv('Ads_Performance.csv')
    except:
        st.error("❌ Files not found. Ensure CSVs are in the root folder.")
        return pd.DataFrame()

    # --- CLEANING FUNCTIONS ---
    def clean_currency(x):
        if isinstance(x, str): return float(x.replace('$', '').replace(',', '').strip())
        return float(x) if isinstance(x, (int, float)) else 0.0

    def clean_percent(x):
        if isinstance(x, str): return float(x.replace('%', '').strip())
        return float(x) if isinstance(x, (int, float)) else 0.0

    def clean_numeric(x):
        if isinstance(x, str): return float(str(x).replace(',', '').strip())
        return float(x) if isinstance(x, (int, float)) else 0.0

    # Apply Cleaning
    df_pricing['True_Unit_Cost'] = df_pricing['True_Unit_Cost'].apply(clean_currency)
    df_pricing['Current_Price'] = df_pricing['Current_Price'].apply(clean_currency)
    df_pricing['Min_Margin'] = df_pricing['Minimum_Acceptable_Margin_%'].apply(clean_percent)
    if df_pricing['Min_Margin'].mean() > 1: df_pricing['Min_Margin'] /= 100
    
    df_competitor['Avg_Competitor_Price'] = df_competitor['Avg_Competitor_Price'].apply(clean_currency)
    
    # Returns
    ret_col = [c for c in df_returns.columns if '90' in c][0]
    df_returns['Returns_Qty'] = df_returns[ret_col].apply(clean_numeric)
    
    # Inventory
    df_inventory['Days_of_Supply'] = df_inventory['days-of-supply'].apply(clean_numeric)
    
    # Sales Aggregation
    df_sales['Units Ordered'] = pd.to_numeric(df_sales['Units Ordered'], errors='coerce').fillna(0)
    sales_agg = df_sales.groupby('SKU')['Units Ordered'].sum().reset_index()

    # Ads Aggregation
    df_ads['spend'] = df_ads['spend'].apply(clean_currency)
    df_ads['sales1d'] = df_ads['sales1d'].apply(clean_currency)
    ads_agg = df_ads.groupby('SKU').agg({'spend': 'sum', 'sales1d': 'sum'}).reset_index().rename(columns={'spend': 'Ad_Spend', 'sales1d': 'Ad_Sales'})

    # Merging
    df = pd.merge(df_pricing, df_competitor[['SKU', 'Avg_Competitor_Price']], on='SKU', how='left')
    df = pd.merge(df, df_inventory[['SKU', 'Days_of_Supply']], on='SKU', how='left')
    df = pd.merge(df, sales_agg, on='SKU', how='left')
    df = pd.merge(df, df_returns[['SKU', 'Returns_Qty']], on='SKU', how='left')
    df = pd.merge(df, ads_agg, on='SKU', how='left')
    
    # Derived Metrics
    df['Return_Rate'] = (df['Returns_Qty'] / df['Units Ordered']) * 100
    df['Return_Rate'] = df['Return_Rate'].fillna(0)
    df.fillna(0, inplace=True)
    
    return df

df_master = load_data()

# ==========================================
# 3. CONTROL PANEL (MOVED TO MAIN PAGE)
# ==========================================

# --- SKU SELECTION ---
if not df_master.empty:
    sku_list = df_master['SKU'].unique().tolist()
    # Create a small column for SKU selection so it doesn't take full width
    col_sel, _ = st.columns([1, 3])
    with col_sel:
        selected_sku = st.selectbox("👉 Select SKU to Analyze:", sku_list)
    
    row = df_master[df_master['SKU'] == selected_sku].iloc[0]
    
    # Pre-fill Defaults
    def_cost = float(row['True_Unit_Cost'])
    def_price = float(row['Current_Price'])
    def_comp = float(row['Avg_Competitor_Price'])
    def_inv = float(row['Days_of_Supply'])
    def_ret = float(row['Return_Rate'])
    def_spend = float(row['Ad_Spend'])
    def_adsales = float(row['Ad_Sales'])
    def_units = float(row['Units Ordered'])
    def_min_marg = float(row['Min_Margin']) * 100

else:
    def_cost = 10.0; def_price=20.0; def_comp=22.0; def_inv=45.0; def_ret=2.0
    def_spend = 500.0; def_adsales=2000.0; def_units=100.0; def_min_marg=20.0

# --- INPUT COLUMNS (3-Column Layout) ---
input_c1, input_c2, input_c3 = st.columns(3)

with input_c1:
    st.markdown("#### 1. Core Economics")
    cost = st.number_input("Unit Cost ($)", value=def_cost)
    curr_price = st.number_input("Current Price ($)", value=def_price)
    comp_price = st.number_input("Competitor Price ($)", value=def_comp)

with input_c2:
    st.markdown("#### 2. Health Signals")
    inv_days = st.number_input("Days of Supply", value=def_inv)
    ret_rate = st.slider("Return Rate (%)", 0.0, 20.0, def_ret)
    min_margin = st.slider("Min Margin (%)", 0.0, 50.0, def_min_marg)

with input_c3:
    st.markdown("#### 3. Ad Performance")
    ad_spend = st.number_input("Total Ad Spend ($)", value=def_spend)
    ad_sales = st.number_input("Total Ad Sales ($)", value=def_adsales)
    total_units = st.number_input("Total Units Sold", value=def_units)

st.markdown("") # Spacing

# --- BIG ACTION BUTTON ---
if st.button("🚀 ANALYZE & RECOMMEND", type="primary", use_container_width=True):
    
    # ==========================================
    # 4. PLATINUM LOGIC ENGINE
    # ==========================================
    
    # 1. Advanced Unit Economics
    cpa = ad_spend / total_units if total_units > 0 else 0
    actual_acos = (ad_spend / ad_sales * 100) if ad_sales > 0 else 0
    
    # Refund Tax Calculation
    refund_tax = 0
    if ret_rate > 8.1:
        refund_tax = (ret_rate / 100) * curr_price
        
    total_cost = cost + cpa + refund_tax
    net_profit = curr_price - total_cost
    
    # Break-Even ACOS
    margin_dollar = curr_price - (cost + refund_tax)
    be_acos = (margin_dollar / curr_price) * 100 if curr_price > 0 else 0
    
    # 2. Logic Gates
    rec_price = curr_price
    strategy = "MAINTAIN"
    reason = "Metrics stable."
    bg_color = "gray"

    # A. HARD BLOCK (Quality)
    if ret_rate > 8.1:
        strat_res = "⛔ BLOCK HIKE"
        reason = f"Refund Tax Applied (${refund_tax:.2f}). Quality Issue."
        bg_color = "#d63031" # Red
        rec_price = curr_price # No change

    # B. LIQUIDATION (Zombie Stock)
    elif inv_days > 180:
        rec_price = max(cost * 1.05, comp_price * 0.95)
        strategy = "📉 LIQUIDATE"
        reason = "Zombie Stock (>180 days). Flush cash."
        bg_color = "#d63031" # Red

    # C. DEFENSE (Ad Bleed)
    elif actual_acos > be_acos:
        rec_price = curr_price # Don't move price yet
        strategy = "🛡️ DEFENSE (CUT ADS)"
        reason = f"Actual ACOS ({actual_acos:.1f}%) > Break-Even ({be_acos:.1f}%). Cut spend."
        bg_color = "#e17055" # Orange

    # D. PROFIT RECOVERY
    elif net_profit < 0:
        rec_price = total_cost / (1 - (min_margin/100))
        strategy = "📈 PROFIT RECOVERY"
        reason = "Unit Economics negative. Must raise price."
        bg_color = "#fdcb6e" # Yellow

    # E. OFFENSE (Growth)
    elif (actual_acos < be_acos * 0.8) and (inv_days < 90) and (curr_price < comp_price):
        rec_price = min(comp_price, curr_price * 1.05)
        strategy = "⚔️ OFFENSE (SCALE)"
        reason = "High Efficiency & Low Price. Boost Ads + Hike Price."
        bg_color = "#00b894" # Green

    # F. CATCH UP
    elif curr_price < comp_price * 0.9:
        rec_price = comp_price * 0.95
        strategy = "🚀 CATCH UP"
        reason = "Significant gap to competitor."
        bg_color = "#0984e3" # Blue
    
    else:
        # Default fallback if no conditions met
        strategy = "MAINTAIN"
        bg_color = "#636e72"

    st.markdown("---")
    
    # --- HEADER METRICS ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Recommended Price", f"${rec_price:.2f}", delta=f"{rec_price - curr_price:.2f}")
    c2.metric("Projected Unit Profit", f"${net_profit:.2f}", delta_color="normal")
    c3.metric("Inventory Age", f"{int(inv_days)} Days", delta="CRITICAL" if inv_days > 180 else "OK", delta_color="inverse")

    # --- STRATEGY BANNER ---
    st.markdown(f"""
    <div style="background-color: {bg_color}; padding: 15px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px;">
        <h2 style="margin:0;">{strategy}</h2>
        <p style="margin:0; font-size: 18px;">{reason}</p>
    </div>
    """, unsafe_allow_html=True)

    # --- DEEP DIVE COLUMNS ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("💰 Unit Economics Stack")
        # Visualizing the stack
        chart_data = pd.DataFrame({
            "Component": ["1. COGS", "2. Refund Tax", "3. Ad CPA", "4. Net Profit"],
            "Value": [cost, refund_tax, (ad_spend/total_units if total_units else 0), net_profit]
        })
        st.bar_chart(chart_data.set_index("Component"))
        if refund_tax > 0:
            st.error(f"⚠️ Refund Tax of ${refund_tax:.2f} applied due to high return rate (>8.1%)")

    with col_right:
        st.subheader("🎯 ACOS Gap Analysis")
        
        # Simple progress bar visualization for ACOS
        st.write(f"**Actual ACOS: {actual_acos:.1f}%**")
        st.progress(min(actual_acos/100, 1.0))
        
        st.write(f"**Break-Even ACOS: {be_acos:.1f}%**")
        st.progress(min(be_acos/100, 1.0))
        
        if actual_acos > be_acos:
            st.warning("📉 You are spending more on ads than your margin allows (Parasite Loss).")
        else:
            st.success("✅ Ad spend is profitable. Room to scale.")
else:
    st.info("👆 Adjust the parameters above and click 'ANALYZE & RECOMMEND' to see the strategy.")

# Footer
st.markdown("---")
st.markdown("*Platinum Pricing Engine v2.0 | Karmic Seed Operations*")
