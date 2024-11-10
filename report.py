import streamlit as st
import pandas as pd
from datetime import datetime

# --- Helper Functions ---

def clean_and_convert_gmv(df, sum_column='GMV'):
    """Cleans the GMV column by removing commas and converting it to a float."""
    if sum_column in df.columns:
        # Replace commas with periods and convert to float
        df[sum_column] = df[sum_column].str.replace(',', '.').astype(float)
    return df

def calculate_GMV(df, group_by_columns, sum_column='GMV'):
    """Calculates GMV by grouping specified columns."""
    try:
        # Clean GMV column
        df = clean_and_convert_gmv(df, sum_column)
        
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
    # Read the Excel files
    df_week1 = pd.read_excel(uploaded_file_week1)
    df_week2 = pd.read_excel(uploaded_file_week2)

    # Clean up GMV columns in both files
    df_week1 = clean_and_convert_gmv(df_week1)
    df_week2 = clean_and_convert_gmv(df_week2)

    # --- Check Column Names ---
    if 'GMV' not in df_week1.columns or 'GMV' not in df_week2.columns:
        st.error("GMV column is missing from one of the uploaded files.")
    else:
        # --- Dashboard Overview ---
        st.subheader("Dashboard Summary")

        # Total GMV for both weeks
        gmvs_week1 = df_week1['GMV'].sum() if 'GMV' in df_week1.columns else 0
        gmvs_week2 = df_week2['GMV'].sum() if 'GMV' in df_week2.columns else 0
        st.metric("Total GMV Week 1 (€)", f"{gmvs_week1:,.0f} €")
        st.metric("Total GMV Week 2 (€)", f"{gmvs_week2:,.0f} €")
        
        # GMV comparison for the dashboard
        comparison_total = compare_metrics(df_week1, df_week2, ['region'])
        st.write("### GMV Comparison by Region")
        st.write(comparison_total)

        # GMV by Subcategory Comparison
        subcategory_gmv_week1 = calculate_GMV(df_week1, ['sub_cat'])
        subcategory_gmv_week2 = calculate_GMV(df_week2, ['sub_cat'])
        comparison_subcategory = compare_metrics(subcategory_gmv_week1, subcategory_gmv_week2, ['sub_cat'])
        st.write("### GMV Comparison by Subcategory")
        st.write(comparison_subcategory)

        # GMV by Supplier Comparison
        supplier_gmv_week1 = calculate_GMV(df_week1, ['Supplier'])
        supplier_gmv_week2 = calculate_GMV(df_week2, ['Supplier'])
        comparison_supplier = compare_metrics(supplier_gmv_week1, supplier_gmv_week2, ['Supplier'])
        st.write("### GMV Comparison by Supplier")
        st.write(comparison_supplier)

        # GMV by Product Comparison
        product_gmv_week1 = calculate_GMV(df_week1, ['product_name'])
        product_gmv_week2 = calculate_GMV(df_week2, ['product_name'])
        comparison_product = compare_metrics(product_gmv_week1, product_gmv_week2, ['product_name'])
        st.write("### GMV Comparison by Product")
        st.write(comparison_product)

else:
    st.warning("Please upload both week files.")
