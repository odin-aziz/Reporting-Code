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

def get_comprehensive_GMV(df):
    """Extracts GMV for each supplier, region, subcategory, and product."""
    supplier_gmv = calculate_GMV(df, ['Supplier'])
    region_gmv = calculate_GMV(df, ['region'])
    subcategory_gmv = calculate_GMV(df, ['sub_cat'])
    product_gmv = calculate_GMV(df, ['product_name'])
    return {
        "Supplier GMV": supplier_gmv,
        "Region GMV": region_gmv,
        "Subcategory GMV": subcategory_gmv,
        "Product GMV": product_gmv
    }

# --- Main Streamlit App ---

st.title("Weekly Dashboard")

# File uploader
uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Section 1: Dashboard Overview in First Tab
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Dashboard", "Region-Based Analysis", "Supplier GMV", "Subcategory GMV", "Comprehensive GMV"])

    # Tab 1: High-Level Summary Dashboard
    with tab1:
        st.subheader("High-Level Summary")
        st.metric("Total GMV (€)", f"{df['GMV'].sum():,.0f} €")
        st.metric("Total Orders", df['order_id'].nunique())

    # Tab 2: Region-Based Analysis with Hierarchical GMV Tables
    with tab2:
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

    # Tab 3: Supplier GMV Analysis
    with tab3:
        st.subheader("Supplier GMV Analysis")
        supplier_gmv = calculate_GMV(df, ['Supplier'])
        st.write(supplier_gmv)

    # Tab 4: Subcategory GMV Analysis
    with tab4:
        st.subheader("Subcategory GMV Analysis")
        subcategory_gmv = calculate_GMV(df, ['sub_cat'])
        st.write(subcategory_gmv)

    # Tab 5: Comprehensive GMV Analysis (Suppliers, Regions, Subcategories, Products)
    with tab5:
        st.subheader("Comprehensive GMV Analysis by Supplier, Region, Subcategory, and Product")
        comprehensive_data = get_comprehensive_GMV(df)

        st.write("#### Supplier GMV")
        st.write(comprehensive_data['Supplier GMV'])
        
        st.write("#### Region GMV")
        st.write(comprehensive_data['Region GMV'])
        
        st.write("#### Subcategory GMV")
        st.write(comprehensive_data['Subcategory GMV'])
        
        st.write("#### Product GMV")
        st.write(comprehensive_data['Product GMV'])

    # Download Report Button in Sidebar
    if st.sidebar.button("Download Report"):
        output_file = f"summary_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        with pd.ExcelWriter(output_file) as writer:
            # Write hierarchical GMV data by region to Excel sheets
            for region, data in region_hierarchy_data.items():
                data['Subcategory GMV'].to_excel(writer, sheet_name=f'{region}_Subcategory_GMV', index=False)
                data['Supplier GMV'].to_excel(writer, sheet_name=f'{region}_Supplier_GMV', index=False)
                data['Restaurant GMV'].to_excel(writer, sheet_name=f'{region}_Restaurant_GMV', index=False)

            # Write comprehensive GMV data for Suppliers, Regions, Subcategories, Products
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
