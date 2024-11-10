import streamlit as st
import pandas as pd
from datetime import datetime

# --- Helper Functions ---

def calculate_GMV(df, group_by_columns, sum_column='GMV'):
    """Calculates GMV by grouping specified columns."""
    try:
        gmv = df.groupby(group_by_columns)[sum_column].sum().reset_index()
        gmv = gmv.rename(columns={sum_column: 'Total GMV (€)'})
        gmv['Total GMV (€)'] = gmv['Total GMV (€)'].round(0).astype(int)
        gmv = gmv.sort_values(by='Total GMV (€)', ascending=False)
        return gmv
    except KeyError as e:
        print(f"Missing column for GMV calculation: {e}")
        return pd.DataFrame()

def get_region_hierarchy(df):
    """Organizes the data into hierarchical GMV tables by region, subcategory, supplier, and restaurant."""
    regions = df['region'].unique()
    region_data = {}
    
    for region in regions:
        region_df = df[df['region'] == region]
        
        # Overall GMV for the region
        total_gmv = region_df['GMV'].sum()
        
        # GMV by Subcategory within Region
        subcategory_gmv = calculate_GMV(region_df, ['sub_cat'])
        
        # GMV by Supplier within Region
        supplier_gmv = calculate_GMV(region_df, ['Supplier'])
        
        # GMV by Restaurant within Region
        restaurant_gmv = calculate_GMV(region_df, ['Restaurant_name'])
        
        # Store the data
        region_data[region] = {
            "Total GMV": f"{total_gmv:,.0f} €",
            "Subcategory GMV": subcategory_gmv,
            "Supplier GMV": supplier_gmv,
            "Restaurant GMV": restaurant_gmv
        }
    return region_data

# --- Main Streamlit App ---

# Section 1: Dashboard Overview
st.title("Weekly Dashboard Overview")
st.write("Upload your dataset for analysis.")

# File uploader
uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Section 1: High-Level Summary
    st.subheader("High-Level Summary of Key Metrics")
    st.metric("Total GMV (€)", f"{df['GMV'].sum():,.0f} €")
    st.metric("Total Orders", df['order_id'].nunique())
    
    # Section 2: Region-based Analysis with Hierarchical GMV Tables
    st.subheader("Detailed GMV Analysis by Region")

    region_hierarchy_data = get_region_hierarchy(df)

    # Display hierarchical tables for each region
    for region, data in region_hierarchy_data.items():
        st.write(f"### {region} - Total GMV: {data['Total GMV']}")

        st.write("#### Subcategory GMV")
        st.write(data['Subcategory GMV'])

        st.write("#### Supplier GMV")
        st.write(data['Supplier GMV'])

        st.write("#### Restaurant GMV")
        st.write(data['Restaurant GMV'])

    # Section 3: Comprehensive Data Extraction
    st.subheader("Comprehensive Data Extraction")

    def extract_unique_values(df, column_name):
        """Extracts unique values for given column in DataFrame."""
        return pd.DataFrame(df[column_name].unique(), columns=[column_name])

    st.write("Unique Suppliers")
    st.write(extract_unique_values(df, 'Supplier'))

    st.write("Unique Regions")
    st.write(extract_unique_values(df, 'region'))

    st.write("Unique Subcategories")
    st.write(extract_unique_values(df, 'sub_cat'))

    st.write("Unique Products")
    st.write(extract_unique_values(df, 'product_name'))

    # Download Report Button
    if st.sidebar.button("Download Report"):
        output_file = f"summary_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        with pd.ExcelWriter(output_file) as writer:
            # Write hierarchical GMV data by region to Excel sheets
            for region, data in region_hierarchy_data.items():
                data['Subcategory GMV'].to_excel(writer, sheet_name=f'{region}_Subcategory_GMV', index=False)
                data['Supplier GMV'].to_excel(writer, sheet_name=f'{region}_Supplier_GMV', index=False)
                data['Restaurant GMV'].to_excel(writer, sheet_name=f'{region}_Restaurant_GMV', index=False)
        
            # Write unique value extracts
            extract_unique_values(df, 'Supplier').to_excel(writer, sheet_name='Unique_Suppliers', index=False)
            extract_unique_values(df, 'region').to_excel(writer, sheet_name='Unique_Regions', index=False)
            extract_unique_values(df, 'sub_cat').to_excel(writer, sheet_name='Unique_Subcategories', index=False)
            extract_unique_values(df, 'product_name').to_excel(writer, sheet_name='Unique_Products', index=False)

        with open(output_file, "rb") as file:
            st.download_button(
                label="Download Excel Report",
                data=file,
                file_name=output_file,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
