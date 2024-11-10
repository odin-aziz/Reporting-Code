import streamlit as st
import pandas as pd
from datetime import datetime

# --- Helper Functions ---

def calculate_GMV(df, group_by_columns, sum_column='GMV'):
    """Calculates GMV by grouping specified columns."""
    try:
        if sum_column not in df.columns:
            raise KeyError(f"Missing column for GMV calculation: {sum_column}")
        
        gmv = df.groupby(group_by_columns)[sum_column].sum().reset_index()
        gmv = gmv.rename(columns={sum_column: 'Total GMV (€)'})
        gmv['Total GMV (€)'] = gmv['Total GMV (€)'].round(0).astype(int)
        gmv = gmv.sort_values(by='Total GMV (€)', ascending=False)
        return gmv
    except KeyError as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

def compare_metrics(df_week1, df_week2, group_by_columns, sum_column='GMV'):
    """Compares metrics between two weeks and calculates growth and difference."""
    # Calculate GMV for both weeks
    gmv_week1 = calculate_GMV(df_week1, group_by_columns, sum_column)
    gmv_week2 = calculate_GMV(df_week2, group_by_columns, sum_column)
    
    # Merge the two dataframes on the group_by_columns
    comparison = pd.merge(gmv_week1, gmv_week2, on=group_by_columns, suffixes=('_Week1', '_Week2'))
    
    # Calculate Growth Percentage and Difference
    comparison['Growth (%)'] = ((comparison['Total GMV (€)_Week2'] - comparison['Total GMV (€)_Week1']) / 
                                comparison['Total GMV (€)_Week1']) * 100
    comparison['Difference (€)'] = comparison['Total GMV (€)_Week2'] - comparison['Total GMV (€)_Week1']
    
    # Round and format for display
    comparison['Growth (%)'] = comparison['Growth (%)'].round(1)
    comparison['Difference (€)'] = comparison['Difference (€)'].round(0).astype(int)
    
    return comparison

# --- Main Streamlit App ---

st.title("Weekly Purchasing Dashboard")

# File uploader for two weeks
uploaded_file_week1 = st.file_uploader("Upload Week 1 Data (e.g., W44)", type="xlsx")
uploaded_file_week2 = st.file_uploader("Upload Week 2 Data (e.g., W45)", type="xlsx")

if uploaded_file_week1 and uploaded_file_week2:
    df_week1 = pd.read_excel(uploaded_file_week1)
    df_week2 = pd.read_excel(uploaded_file_week2)

    # --- Sidebar Configuration ---
    st.sidebar.header("Select Week and Metrics")

    # Dropdown for W44 sections
    with st.sidebar.expander("W44 (Week 1) Sections"):
        week1_section = st.selectbox("Select Section for W44", ["High-Level Summary", "Region-Based Analysis", "Supplier GMV", "Subcategory GMV"])
    
    # Dropdown for W45 sections
    with st.sidebar.expander("W45 (Week 2) Sections"):
        week2_section = st.selectbox("Select Section for W45", ["High-Level Summary", "Region-Based Analysis", "Supplier GMV", "Subcategory GMV"])

    # --- Dashboard Overview ---
    if week1_section == "High-Level Summary" or week2_section == "High-Level Summary":
        st.subheader("High-Level Summary")

        # --- Total GMV ---
        gmvs_week1 = df_week1['GMV'].sum() if 'GMV' in df_week1.columns else 0
        gmvs_week2 = df_week2['GMV'].sum() if 'GMV' in df_week2.columns else 0
        growth_total_gmv = (gmvs_week2 - gmvs_week1) / gmvs_week1 * 100 if gmvs_week1 != 0 else 0
        diff_total_gmv = gmvs_week2 - gmvs_week1
        st.metric("Total GMV Week 1 (€)", f"{gmvs_week1:,.0f} €")
        st.metric("Total GMV Week 2 (€)", f"{gmvs_week2:,.0f} €")
        st.write(f"**Growth (%)**: {growth_total_gmv:.1f}% | **Difference (€)**: {diff_total_gmv:,.0f} €")

        # --- GMV by Region ---
        region_gmv_week1 = calculate_GMV(df_week1, ['region'])
        region_gmv_week2 = calculate_GMV(df_week2, ['region'])
        st.write("### GMV by Region")
        comparison_region = compare_metrics(region_gmv_week1, region_gmv_week2, ['region'])
        st.write(comparison_region)

        # --- GMV by Subcategory ---
        subcategory_gmv_week1 = calculate_GMV(df_week1, ['sub_cat'])
        subcategory_gmv_week2 = calculate_GMV(df_week2, ['sub_cat'])
        st.write("### GMV by Subcategory")
        comparison_subcategory = compare_metrics(subcategory_gmv_week1, subcategory_gmv_week2, ['sub_cat'])
        st.write(comparison_subcategory)

        # --- GMV by Supplier ---
        supplier_gmv_week1 = calculate_GMV(df_week1, ['Supplier'])
        supplier_gmv_week2 = calculate_GMV(df_week2, ['Supplier'])
        st.write("### GMV by Supplier")
        comparison_supplier = compare_metrics(supplier_gmv_week1, supplier_gmv_week2, ['Supplier'])
        st.write(comparison_supplier)

        # --- GMV by Product ---
        product_gmv_week1 = calculate_GMV(df_week1, ['Product'])
        product_gmv_week2 = calculate_GMV(df_week2, ['Product'])
        st.write("### GMV by Product")
        comparison_product = compare_metrics(product_gmv_week1, product_gmv_week2, ['Product'])
        st.write(comparison_product)

    # --- GMV Comparison ---
    if week1_section == "Region-Based Analysis" or week2_section == "Region-Based Analysis":
        st.subheader("Region-Based GMV Comparison")
        comparison = compare_metrics(df_week1, df_week2, ['region'])
        st.write(comparison)

    if week1_section == "Supplier GMV" or week2_section == "Supplier GMV":
        st.subheader("Supplier GMV Analysis")
        supplier_gmv_week1 = calculate_GMV(df_week1, ['Supplier'])
        supplier_gmv_week2 = calculate_GMV(df_week2, ['Supplier'])
        comparison_supplier = compare_metrics(supplier_gmv_week1, supplier_gmv_week2, ['Supplier'])
        st.write(comparison_supplier)

    if week1_section == "Subcategory GMV" or week2_section == "Subcategory GMV":
        st.subheader("Subcategory GMV Analysis")
        subcategory_gmv_week1 = calculate_GMV(df_week1, ['sub_cat'])
        subcategory_gmv_week2 = calculate_GMV(df_week2, ['sub_cat'])
        comparison_subcategory = compare_metrics(subcategory_gmv_week1, subcategory_gmv_week2, ['sub_cat'])
        st.write(comparison_subcategory)


else:
    st.warning("Please upload both week files.")
