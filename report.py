import pandas as pd
import streamlit as st

# Load data for both weeks
def load_data(file):
    df = pd.read_excel(file)
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')
    return df

# Function to calculate GMV
def calculate_GMV(df, group_by_columns):
    if 'GMV' not in df.columns:
        st.error("GMV column is missing from the data!")
        return None
    gmv = df.groupby(group_by_columns)['GMV'].sum().reset_index()
    return gmv

# Function to compare two dataframes (for two weeks)
def compare_data(df_week_1, df_week_2, group_by_columns):
    gmv_week_1 = calculate_GMV(df_week_1, group_by_columns)
    gmv_week_2 = calculate_GMV(df_week_2, group_by_columns)
    
    if gmv_week_1 is None or gmv_week_2 is None:
        return None
    
    comparison_df = pd.merge(gmv_week_1, gmv_week_2, on=group_by_columns, suffixes=('_W44', '_W45'))
    comparison_df['% Growth'] = ((comparison_df['GMV_W45'] - comparison_df['GMV_W44']) / comparison_df['GMV_W44']) * 100
    comparison_df['Ecart'] = comparison_df['GMV_W45'] - comparison_df['GMV_W44']
    
    return comparison_df

# Streamlit UI components
st.title('Weekly Purchasing Data Comparison')

# File Upload
st.sidebar.subheader("Upload Weekly Data Files")
week_1_file = st.sidebar.file_uploader("Upload W44 File", type=["xlsx"])
week_2_file = st.sidebar.file_uploader("Upload W45 File", type=["xlsx"])

if week_1_file and week_2_file:
    # Load the data for both weeks
    df_week_1 = load_data(week_1_file)
    df_week_2 = load_data(week_2_file)

    # Summary of Key Metrics
    st.subheader("Summary of Key Metrics")
    
    # GMV by Region Comparison
    st.subheader("GMV Comparison by Region")
    region_comparison = compare_data(df_week_1, df_week_2, group_by_columns=['region'])
    
    if region_comparison is not None:
        st.write(region_comparison[['region', 'GMV_W44', 'GMV_W45', '% Growth', 'Ecart']])

    # GMV by Supplier Comparison
    st.subheader("GMV Comparison by Supplier")
    supplier_comparison = compare_data(df_week_1, df_week_2, group_by_columns=['Supplier'])
    
    if supplier_comparison is not None:
        st.write(supplier_comparison[['Supplier', 'GMV_W44', 'GMV_W45', '% Growth', 'Ecart']])

    # GMV by Subcategory Comparison
    st.subheader("GMV Comparison by Subcategory")
    subcategory_comparison = compare_data(df_week_1, df_week_2, group_by_columns=['sub_cat'])
    
    if subcategory_comparison is not None:
        st.write(subcategory_comparison[['sub_cat', 'GMV_W44', 'GMV_W45', '% Growth', 'Ecart']])

    # Detailed GMV Analysis (moved to dashboard)
    st.subheader("Comprehensive GMV Analysis")

    # GMV by Region for W44
    st.subheader("W44 GMV by Region")
    region_gmv_w44 = calculate_GMV(df_week_1, group_by_columns=['region'])
    if region_gmv_w44 is not None:
        st.write(region_gmv_w44)

    # GMV by Region for W45
    st.subheader("W45 GMV by Region")
    region_gmv_w45 = calculate_GMV(df_week_2, group_by_columns=['region'])
    if region_gmv_w45 is not None:
        st.write(region_gmv_w45)

    # GMV by Supplier for W44
    st.subheader("W44 GMV by Supplier")
    supplier_gmv_w44 = calculate_GMV(df_week_1, group_by_columns=['Supplier'])
    if supplier_gmv_w44 is not None:
        st.write(supplier_gmv_w44)

    # GMV by Supplier for W45
    st.subheader("W45 GMV by Supplier")
    supplier_gmv_w45 = calculate_GMV(df_week_2, group_by_columns=['Supplier'])
    if supplier_gmv_w45 is not None:
        st.write(supplier_gmv_w45)

    # GMV by Subcategory for W44
    st.subheader("W44 GMV by Subcategory")
    subcategory_gmv_w44 = calculate_GMV(df_week_1, group_by_columns=['sub_cat'])
    if subcategory_gmv_w44 is not None:
        st.write(subcategory_gmv_w44)

    # GMV by Subcategory for W45
    st.subheader("W45 GMV by Subcategory")
    subcategory_gmv_w45 = calculate_GMV(df_week_2, group_by_columns=['sub_cat'])
    if subcategory_gmv_w45 is not None:
        st.write(subcategory_gmv_w45)
    
else:
    st.warning("Please upload both W44 and W45 data files to compare.")
