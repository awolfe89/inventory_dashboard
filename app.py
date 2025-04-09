import streamlit as st
import pandas as pd
import datetime
import altair as alt


st.set_page_config(page_title="Days of Inventory Dashboard", layout="wide")
st.markdown("<h1 style='text-align: center;'>📦 Days of Inventory Dashboard</h1>", unsafe_allow_html=True)

st.markdown("""
            ---
### 🧠 Inventory Intelligence Dashboard
Welcome to the Days of Inventory performance dashboard — designed to help ecommerce teams track stock health, surface overstock and risk, and drive action with data.

This demo uses **sample data (200 products)** and includes:
- 📊 Visual insights by Buyer, Category, and Product
- 🤖 AI-style summaries using rule-based logic
- 🛠️ Interactive filters, sortable tables, and smart highlights

---
""")

# --- Sidebar ---
st.sidebar.header("Upload Your Data Source")
st.sidebar.markdown("🔒 Upload disabled for demo.")
st.sidebar.markdown("_Using sample inventory data with 200 products for demo purposes._")
view_mode = st.sidebar.radio("Select View Mode", ["📊 Overview", "📈 Visual Explorer"])

# --- Load Sample Data ---
@st.cache_data
def load_data(file):
    return pd.read_csv(file, parse_dates=['ExpiryDate'])

df = load_data("days_of_inventory_200_products.csv")

# Helper function to categorize DOI
def get_doi_status(dois):
    status = []
    for doi in dois:
        if doi < 10:
            status.append("🔴 Low")
        elif doi > 180:
            status.append("🟢 Overstock")
        else:
            status.append("🟡 Normal")
    return status

df['DOI_Status'] = get_doi_status(df['DOI'])

if view_mode == "📊 Overview":
    # --- Rule-Based Filters for Insights ---
    low_doi_df = df[df['DOI'] < 10]
    overstock_df = df[df['OverstockInventoryValue'] > 0]
    expiring_df = df[df['ExpiryDate'] < pd.Timestamp.today() + pd.Timedelta(days=30)]
    high_cost_low_sales_df = df[(df['TotalInventoryCost'] > 5000) & (df['Last12MoQtySold'] < 50)]

    # --- AI Insights Block ---
    st.subheader("🤖 A.I. Insights")
    st.markdown(
        "_These insights are automatically generated using rule-based logic that mimics GPT-style summaries. "
        "In a production version, this is powered by OpenAI (or local LLM)._"
    )

    buyers = df['Buyer'].unique()
    low_doi_count = low_doi_df.shape[0]
    top_buyer = overstock_df.groupby('Buyer')['OverstockInventoryValue'].sum().idxmax() if not overstock_df.empty else None
    top_buyer_val = overstock_df.groupby('Buyer')['OverstockInventoryValue'].sum().max() if not overstock_df.empty else 0
    risky_sample = high_cost_low_sales_df.sample(min(2, len(high_cost_low_sales_df)))['Product'].tolist()
    expiring_sample = expiring_df.sample(min(2, len(expiring_df)))['Product'].tolist()

    insight_lines = []
    insight_lines.append(f"<li><b>🔻 {low_doi_count} products</b> are critically low on inventory (DOI < 10).</li>")
    if top_buyer:
        insight_lines.append(f"<li><b>📦 Buyer {top_buyer}</b> is carrying <b>${top_buyer_val:,.0f}</b> in overstocked items.</li>")
    if risky_sample:
        insight_lines.append(f"<li><b>⚠️ High holding cost</b> with low movement detected in SKUs: {', '.join(risky_sample)}.</li>")
    if expiring_sample:
        insight_lines.append(f"<li><b>⏳ Expiring soon</b>: {', '.join(expiring_sample)} within 30 days.</li>")

    insights_html = f"""
    <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 6px; border-left: 4px solid #999;">
        <ul style="margin-bottom: 0;">
            {''.join(insight_lines)}
        </ul>
    </div>
    """
    st.markdown(insights_html, unsafe_allow_html=True)
 

    # Add a little space before the charts
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # --- KPI Metrics ---
    total_products = df.shape[0]
    low_stock = low_doi_df.shape[0]
    total_overstock_value = df['OverstockInventoryValue'].sum()
    total_inventory_value = df['TotalInventoryCost'].sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Products", total_products)
    col2.metric("Products w/ DOI < 10", low_stock)
    col3.metric("Overstock Inventory $", f"${total_overstock_value:,.0f}")
    col4.metric("Total Inventory Value", f"${total_inventory_value:,.0f}")

    # --- Charts ---
    st.subheader("📊 Inventory Insights")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        doi_chart = alt.Chart(df).mark_bar().encode(
            x=alt.X('DOI:Q', bin=alt.Bin(maxbins=30), title='Days of Inventory'),
            y='count()',
            tooltip=['DOI']
        ).properties(height=300, title='DOI Distribution')
        st.altair_chart(doi_chart, use_container_width=True)

    with chart_col2:
        top_overstock = df.sort_values(by='OverstockInventoryValue', ascending=False).head(10)
        overstock_chart = alt.Chart(top_overstock).mark_bar().encode(
            x=alt.X('OverstockInventoryValue:Q', title='Overstock $'),
            y=alt.Y('Product:N', sort='-x'),
            tooltip=['OverstockInventoryValue']
        ).properties(height=300, title='Top Overstocked Products')
        st.altair_chart(overstock_chart, use_container_width=True)

    # --- Data Table ---
    st.subheader("📋 Detailed Inventory Table")
    st.dataframe(df[['Product', 'Warehouse', 'Buyer', 'Category', 'StockQty', 'AvgLandedCost',
                     'TotalInventoryCost', 'Last12MoQtySold', 'DOI', 'DOI_Status',
                     'OverstockInventoryValue', 'ExpiryDate', '12MoDollarsSold']])

elif view_mode == "📈 Visual Explorer":
    st.subheader("Visual Explorer")

    # --- Filters ---
    with st.expander("🔎 Filter Options", expanded=True):
        selected_warehouse = st.selectbox("Warehouse", options=["All"] + list(df['Warehouse'].unique()))
        selected_buyer = st.selectbox("Buyer", options=["All"] + list(df['Buyer'].unique()))
        selected_category = st.selectbox("Category", options=["All"] + list(df['Category'].unique()))

    filtered_df = df.copy()
    if selected_warehouse != "All":
        filtered_df = filtered_df[filtered_df['Warehouse'] == selected_warehouse]
    if selected_buyer != "All":
        filtered_df = filtered_df[filtered_df['Buyer'] == selected_buyer]
    if selected_category != "All":
        filtered_df = filtered_df[filtered_df['Category'] == selected_category]

    # --- Scatter Plot: DOI vs Revenue ---
    st.markdown("### 📈 DOI vs Revenue (Bubble = Stock Qty)")
    scatter_chart = alt.Chart(filtered_df).mark_circle(size=60).encode(
        x='DOI',
        y='12MoDollarsSold',
        size='StockQty',
        color='Category',
        tooltip=['Product', 'DOI', '12MoDollarsSold', 'StockQty']
    ).properties(height=400)
    st.altair_chart(scatter_chart, use_container_width=True)

    # --- Bar: Avg DOI per Buyer ---
    st.markdown("### 📊 Average DOI by Buyer")
    avg_doi_chart = alt.Chart(filtered_df).mark_bar().encode(
        x=alt.X('mean(DOI):Q', title='Average DOI'),
        y=alt.Y('Buyer:N', sort='-x'),
        color='Buyer:N',
        tooltip=['mean(DOI)']
    ).properties(height=300)
    st.altair_chart(avg_doi_chart, use_container_width=True)

    # --- Bar: Inventory Value by Category ---
    st.markdown("### 📦 Inventory Value by Category")
    cat_chart = alt.Chart(filtered_df).mark_bar().encode(
        x=alt.X('Category:N', sort='-y'),
        y=alt.Y('sum(TotalInventoryCost):Q', title='Total Inventory $'),
        color='Category:N',
        tooltip=['Category', 'sum(TotalInventoryCost)']
    ).properties(height=300)
    st.altair_chart(cat_chart, use_container_width=True)

    # --- Bar: Top 10 Products by Revenue ---
    st.markdown("### 💸 Top 10 Products by Revenue")
    top_revenue = filtered_df.sort_values(by='12MoDollarsSold', ascending=False).head(10)
    revenue_chart = alt.Chart(top_revenue).mark_bar().encode(
        x=alt.X('12MoDollarsSold:Q', title='12Mo Revenue'),
        y=alt.Y('Product:N', sort='-x'),
        tooltip=['12MoDollarsSold']
    ).properties(height=300)
    st.altair_chart(revenue_chart, use_container_width=True)

    # --- Scatter: DOI vs Total Inventory Cost ---
    st.markdown("### 🟠 DOI vs Inventory Cost")
    doi_cost_chart = alt.Chart(filtered_df).mark_circle(size=60).encode(
        x='DOI',
        y='TotalInventoryCost',
        size='StockQty',
        color='Buyer',
        tooltip=['Product', 'DOI', 'TotalInventoryCost', 'StockQty']
    ).properties(height=400)
    st.altair_chart(doi_cost_chart, use_container_width=True)

    # --- Expiry Risk Timeline ---
    st.markdown("### ⏳ Products Expiring Soon")
    expiring_soon = filtered_df[filtered_df['ExpiryDate'] < pd.Timestamp.today() + pd.Timedelta(days=90)]
    if not expiring_soon.empty:
        expiry_chart = alt.Chart(expiring_soon).mark_bar().encode(
            x=alt.X('ExpiryDate:T', title='Expiry Date'),
            y='count()',
            tooltip=['count()']
        ).properties(height=300)
        st.altair_chart(expiry_chart, use_container_width=True)
    else:
        st.info("🎉 No products expiring in the next 90 days.")
