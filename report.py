import streamlit as st
import pandas as pd
from datetime import datetime

# --- Helper Functions ---

def calculate_GMV(df, group_by_columns, sum_column='GMV'):
    """Calculates GMV by grouping specified columns, handling NaNs and ensuring numeric data type."""
    try:
        gmv = df.groupby(group_by_columns)[sum_column].sum().reset_index()
        gmv = gmv.rename(columns={sum_column: 'Total GMV (€)'})
        
        # Ensure 'Total GMV (€)' is numeric and fill NaN values
        gmv['Total GMV (€)'] = pd.to_numeric(gmv['Total GMV (€)'], errors='coerce').fillna(0)
        
        # Round to integers after filling NaNs
        gmv['Total GMV (€)'] = gmv['Total GMV (€)'].round(0).astype(int)
        
        return gmv.sort_values(by='Total GMV (€)', ascending=False)
    except KeyError as e:
        st.warning(f"Missing column for GMV calculation: {e}")
        return pd.DataFrame()

def get_region_hierarchy(df):
    """Organizes GMV data hierarchically by region, subcategory, supplier, and restaurant."""
    regions = df['region'].unique()
    region_data = {}
    
    for region in regions:
        region_df = df[df['region'] == region]
        total_gmv = region_df['GMV'].sum()
        region_data[region] = {
            "Total GMV": f"{total_gmv:,.0f} €",
            "Subcategory GMV": calculate_GMV(region_df, ['sub_cat']),
            "Supplier GMV": calculate_GMV(region_df, ['Supplier']),
            "Restaurant GMV": calculate_GMV(region_df, ['Restaurant_name'])
        }
    return region_data

def get_comprehensive_GMV(df):
    """Extracts GMV for each supplier, region, subcategory, and product."""
    return {
        "Supplier GMV": calculate_GMV(df, ['Supplier']),
        "Region GMV": calculate_GMV(df, ['region']),
        "Subcategory GMV": calculate_GMV(df, ['sub_cat']),
        "Product GMV": calculate_GMV(df, ['product_name'])
    }

# --- Main Streamlit App ---

st.title("Weekly Purchasing Dashboard")

# File Upload
uploaded_file = st.file_uploader("Upload weekly data file", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Section 1: Summary Tab
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Summary", "Region Analysis", "Supplier Analysis", "Subcategory Analysis", "Detailed GMV Analysis"
    ])

    # Tab 1: Summary
    with tab1:
        st.subheader("📊 Summary of Key Metrics")
        # Organize metrics into columns
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total GMV (€)", f"{df['GMV'].sum():,.0f} €")
        with col2:
            st.metric("Total Weight", f"{df['Weight'].sum():,.2f}")
        with col3:
            st.metric("Total Purchase Price", f"{df['purchase price'].sum():,.2f}")
        
        col4, col5 = st.columns(2)
        with col4:
            st.metric("Total Tax Amount", f"{df['tax_amount'].sum():,.2f}")

    # Tab 2: Region Analysis
    with tab2:
        st.subheader("📍 Region-Based GMV Analysis")
        region_hierarchy_data = get_region_hierarchy(df)
        
        for region, data in region_hierarchy_data.items():
            st.write(f"### {region} - Total GMV: {data['Total GMV']}")
            st.write("#### GMV by Subcategory")
            st.dataframe(data['Subcategory GMV'], use_container_width=True)
            st.write("#### GMV by Supplier")
            st.dataframe(data['Supplier GMV'], use_container_width=True)
            st.write("#### GMV by Restaurant")
            st.dataframe(data['Restaurant GMV'], use_container_width=True)

    # Tab 3: Supplier Analysis
    with tab3:
        st.subheader("🏢 Supplier GMV Analysis")
        supplier_gmv = calculate_GMV(df, ['Supplier'])
        st.dataframe(supplier_gmv, use_container_width=True)

    # Tab 4: Subcategory Analysis
    with tab4:
        st.subheader("📦 Subcategory GMV Analysis")
        subcategory_gmv = calculate_GMV(df, ['sub_cat'])
        st.dataframe(subcategory_gmv, use_container_width=True)

    # Tab 5: Detailed GMV Analysis
    with tab5:
        st.subheader("🔍 Comprehensive GMV Analysis by Supplier, Region, Subcategory, and Product")
        comprehensive_data = get_comprehensive_GMV(df)

        st.write("#### Supplier GMV")
        st.dataframe(comprehensive_data['Supplier GMV'], use_container_width=True)
        
        st.write("#### Region GMV")
        st.dataframe(comprehensive_data['Region GMV'], use_container_width=True)
        
        st.write("#### Subcategory GMV")
        st.dataframe(comprehensive_data['Subcategory GMV'], use_container_width=True)
        
        st.write("#### Product GMV")
        st.dataframe(comprehensive_data['Product GMV'], use_container_width=True)

    # Download Report Button
    if st.sidebar.button("Download Report"):
        output_file = f"summary_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        with pd.ExcelWriter(output_file) as writer:
            for region, data in region_hierarchy_data.items():
                data['Subcategory GMV'].to_excel(writer, sheet_name=f'{region}_Subcategory_GMV', index=False)
                data['Supplier GMV'].to_excel(writer, sheet_name=f'{region}_Supplier_GMV', index=False)
                data['Restaurant GMV'].to_excel(writer, sheet_name=f'{region}_Restaurant_GMV', index=False)

            comprehensive_data['Supplier GMV'].to_excel(writer, sheet_name='Supplier_GMV', index=False)
            comprehensive_data['Region GMV'].to_excel(writer, sheet_name='Region_GMV', index=False)
            comprehensive_data['Subcategory GMV'].to_excel(writer, sheet_name='Subcategory_GMV', index=False)
            comprehensive_data['Product GMV'].to_excel(writer, sheet_name='Product_GMV', index=False)

        with open(output_file, "rb") as file:
            st.download_button(
                label="Download Excel Report",
                data=file,
                file_name=output_file,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
