import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import plotly.express as px  # For advanced plotting options

# --- Data Processing Functions ---

@st.cache_data
def calculate_GMV(df, group_by_columns, sum_column='GMV'):
    """General function to calculate GMV per group."""
    try:
        gmv = df.groupby(group_by_columns)[sum_column].sum().reset_index()
        gmv = gmv.rename(columns={sum_column: 'Total GMV (€)'})
        gmv['Total GMV (€)'] = gmv['Total GMV (€)'].round(0).astype(int)
        gmv = gmv.sort_values(by='Total GMV (€)', ascending=False)
        return gmv
    except KeyError as e:
        print(f"Missing column for GMV calculation: {e}")
        return pd.DataFrame()

# --- Charting Functions ---
def plot_treemap(data, path, values, title):
    """Treemap for representing proportions."""
    fig = px.treemap(data, path=path, values=values, title=title)
    st.plotly_chart(fig)

def plot_stacked_bar(data, x, y, hue, title, xlabel, ylabel):
    """Stacked bar chart for GMV breakdown."""
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=x, y=y, hue=hue, data=data, ax=ax, palette="coolwarm")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    st.pyplot(fig)

def plot_bubble_chart(data, x, y, size, color, title):
    """Bubble chart for representing restaurant GMV by region."""
    fig = px.scatter(data, x=x, y=y, size=size, color=color, hover_name=x, title=title)
    st.plotly_chart(fig)

# --- Streamlit Main App ---

# Section 1: Dashboard Overview
st.title("Weekly Dashboard Overview")
st.subheader("High-Level Summary of Key Metrics")

if 'df' in locals():
    st.metric("Total GMV (€)", f"{df['GMV'].sum():,.0f} €")
    st.metric("Total Orders", df['order_id'].nunique())
    
    top_suppliers = calculate_GMV(df, ['Supplier'])
    st.write("Top 5 Suppliers by GMV")
    st.write(top_suppliers.head(5))

    # Link to details for Supplier GMV
    if st.button("View Supplier GMV Details"):
        st.session_state.view_supplier_gmv = True

# Section 2: Supplier GMV Analysis
if 'view_supplier_gmv' in st.session_state:
    st.subheader("Supplier GMV Analysis")

    supplier_GMV = calculate_GMV(df, ['Supplier'])
    plot_treemap(supplier_GMV, path=['Supplier'], values='Total GMV (€)', title="Supplier GMV Treemap")

    supplier_region_GMV = calculate_GMV(df, ['region', 'Supplier'])
    plot_stacked_bar(supplier_region_GMV, 'region', 'Total GMV (€)', 'Supplier', "Supplier GMV by Region", "Region", "Total GMV (€)")

# Section 3: Subcategory GMV
if st.sidebar.checkbox("Subcategory GMV Analysis"):
    st.subheader("Subcategory GMV Analysis")

    subcategory_GMV = calculate_GMV(df, ['sub_cat'])
    plot_stacked_bar(subcategory_GMV, 'sub_cat', 'Total GMV (€)', 'sub_cat', "Subcategory GMV", "Subcategory", "Total GMV (€)")

# Section 4: Restaurant GMV by Region
if st.sidebar.checkbox("Restaurant GMV by Region"):
    st.subheader("Restaurant GMV by Region")

    restaurant_region_GMV = calculate_GMV(df, ['region', 'Restaurant_name'])
    plot_bubble_chart(restaurant_region_GMV, 'Restaurant_name', 'region', 'Total GMV (€)', 'region', "Restaurant GMV by Region")

# Download Report button
if st.sidebar.button("Download Report"):
    output_file = f"summary_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
    with pd.ExcelWriter(output_file) as writer:
        top_suppliers.to_excel(writer, sheet_name='Top_Suppliers', index=False)
        subcategory_GMV.to_excel(writer, sheet_name='Subcategory_GMV', index=False)
        restaurant_region_GMV.to_excel(writer, sheet_name='Restaurant_GMV_Region', index=False)

    with open(output_file, "rb") as file:
        st.download_button(
            label="Download Excel Report",
            data=file,
            file_name=output_file,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
