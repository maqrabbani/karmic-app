import streamlit as st
import pandas as pd
import numpy as np

# ==========================================
# 1. SETUP & CONFIGURATION
# ==========================================
st.set_page_config(page_title="Karmic Seed Pricing Simulator", layout="wide")

st.title("🌱 Karmic Seed: Pricing Decision Support Tool")
st.markdown("""
This tool translates our **Margin-Aware Pricing Framework** into a live simulator. 
Operations teams can use this to review price recommendations or test "What-If" scenarios for new products.
""")

# ==========================================
# 2. THE PRICING LOGIC (Hidden Backend)
# ==========================================
def calculate_recommendation(cost, current_price, competitor_price, min_margin, target_margin, returns_pct, inventory_days):
    # 1. Calculate True Break Even (simplified for simulator inputs)
    # Assuming ad_spend is roughly covered in the 'cost' input for this simple view, 
    # or we calculate a 'loaded cost'.
    
    # Logic Checks
    margin_current = (current_price - cost) / current_price
    min_price = cost / (1 - (min_margin/100))
    target_price = cost / (1 - (target_margin/100))
    
    # Elasticity Logic
    elasticity = -1.5 if current_price > (competitor_price * 0.9) else -0.8
    
    # Recommendation Engine
    strategy = "MAINTAIN"
    rec_price = current_price
    
    # Hard Block
    if returns_pct > 8.0:
        return current_price, "⛔ BLOCKED (High Returns)", "Fix Quality First", margin_current
        
    # Decision Tree
    if current_price < min_price:
        strategy = "📈 PROFIT RECOVERY"
        rec_price = min_price # Floor
    elif inventory_days > 120:
        strategy = "📉 LIQUIDATE"
        rec_price = max(cost * 1.05, competitor_price * 0.95) # Don't lose money, but move stock
    elif current_price < (competitor_price - 1.0) and margin_current < (target_margin/100):
        strategy = "🚀 MARKET CATCH-UP"
        rec_price = min(target_price, competitor_price - 0.50)
        
    return round(rec_price, 2), strategy, "optimize margin", margin_current

# ==========================================
# 3. SIDEBAR: INPUTS
# ==========================================
st.sidebar.header("📝 SKU Simulator")
st.sidebar.info("Enter product details to generate a real-time pricing strategy.")

sku_name = st.sidebar.text_input("SKU Name (Optional)", "Bio-Plate-Standard")
cost_input = st.sidebar.number_input("True Unit Cost ($)", value=15.00, step=0.50)
curr_price_input = st.sidebar.number_input("Current Selling Price ($)", value=22.00, step=0.50)
comp_price_input = st.sidebar.number_input("Avg Competitor Price ($)", value=25.00, step=0.50)

st.sidebar.markdown("---")
st.sidebar.subheader("Business Constraints")
min_margin_input = st.sidebar.slider("Min Acceptable Margin (%)", 10, 50, 20)
target_margin_input = st.sidebar.slider("Target Gross Margin (%)", 20, 70, 40)

st.sidebar.markdown("---")
st.sidebar.subheader("Health Signals")
inventory_input = st.sidebar.number_input("Days of Supply", value=45)
returns_input = st.sidebar.slider("Return Rate (%)", 0.0, 20.0, 2.5)

# ==========================================
# 4. MAIN DASHBOARD
# ==========================================
if st.button("Run Analysis", type="primary"):
    new_price, strategy, reason, curr_margin = calculate_recommendation(
        cost_input, curr_price_input, comp_price_input, 
        min_margin_input, target_margin_input, 
        returns_input, inventory_input
    )
    
    # METRICS ROW
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Margin", f"{curr_margin:.1%}", delta_color="normal")
    with col2:
        st.metric("Competitor Gap", f"${curr_price_input - comp_price_input:.2f}", 
                  delta="-Undercut" if curr_price_input < comp_price_input else "+Premium")
    with col3:
        # Dynamic color for strategy
        color = "red" if "BLOCKED" in strategy else "green" if "CATCH-UP" in strategy else "orange"
        st.markdown(f"**Strategy:**")
        st.markdown(f":{color}[{strategy}]")
    with col4:
        st.metric("Recommended Price", f"${new_price:.2f}", 
                  delta=f"${new_price - curr_price_input:.2f}")

    st.markdown("---")
    
    # DETAILED ANALYSIS
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("Price Position Analysis")
        # Visualizing the bands
        chart_data = pd.DataFrame({
            'Price Point': ['Unit Cost', 'Min Margin Floor', 'Current Price', 'Target Ideal', 'Competitor Avg'],
            'Value': [cost_input, cost_input/(1-min_margin_input/100), curr_price_input, cost_input/(1-target_margin_input/100), comp_price_input]
        })
        st.bar_chart(chart_data.set_index('Price Point'))
        
    with c2:
        st.subheader("Decision Logic")
        st.write(f"""
        1. **Floor Check:** cost / (1 - {min_margin_input}%) = **${cost_input/(1-min_margin_input/100):.2f}**
        2. **Ceiling Check:** Competitor @ **${comp_price_input:.2f}**
        3. **Health Check:** Returns are {returns_input}% (Limit: 8%)
        
        **Final Verdict:** {strategy}
        """)

else:
    st.info("👈 Edit parameters in the sidebar and click 'Run Analysis'")
