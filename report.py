import streamlit as st
import pandas as pd
from datetime import datetime

# --- Helper Functions ---

def calculate_GMV(df, group_by_columns, sum_column='GMV'):
    """General function to calculate GMV per group with euro formatting, without IDs."""
    try:
        gmv = df.groupby(group_by_columns)[sum_column].sum().reset_index()
        gmv = gmv.rename(columns={sum_column: 'Total GMV (€)'})
        gmv['Total GMV (€)'] = gmv['Total GMV (€)'].round(0).astype(int)
        gmv = gmv.sort_values(by='Total GMV (€)', ascending=False)
        return gmv
    except KeyError as e:
        print(f"Missing column for GMV calculation: {e}")
        return pd.DataFrame()

# Extract all metrics functions
def extract_unique_values(df, column_name):
    """Helper function to extract unique values for metrics."""
    return pd.DataFrame(df[column_name].unique(), columns=[column_name])

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
    
    top_suppliers = calculate_GMV(df, ['Supplier'])
    st.write("Top 5 Suppliers by GMV")
    st.write(top_suppliers.head(5))

    # Section 2: Supplier GMV Tables
    st.subheader("Supplier GMV Analysis")
    supplier_GMV = calculate_GMV(df, ['Supplier'])
    st.write("Supplier GMV")
    st.write(supplier_GMV)
    
    # Supplier GMV per Region
    supplier_region_GMV = calculate_GMV(df, ['region', 'Supplier'])
    st.write("Supplier GMV per Region")
    st.write(supplier_region_GMV)

    # Section 3: Subcategory GMV Tables
    st.subheader("Subcategory GMV Analysis")
    subcategory_GMV = calculate_GMV(df, ['sub_cat'])
    st.write("Subcategory GMV")
    st.write(subcategory_GMV)

    # Subcategory GMV per Supplier
    subcategory_supplier_GMV = calculate_GMV(df, ['Supplier', 'sub_cat'])
    st.write("Subcategory GMV per Supplier")
    st.write(subcategory_supplier_GMV)

    # Subcategory GMV per Region
    subcategory_region_GMV = calculate_GMV(df, ['region', 'sub_cat'])
    st.write("Subcategory GMV per Region")
    st.write(subcategory_region_GMV)

    # Section 4: Restaurant GMV by Region Tables
    st.subheader("Restaurant GMV by Region")
    restaurant_region_GMV = calculate_GMV(df, ['region', 'Restaurant_name'])
    st.write("Restaurant GMV by Region")
    st.write(restaurant_region_GMV)

    # Section 5: Comprehensive Data Extraction Tables
    st.subheader("Comprehensive Data by Key Metrics")

    # Extract and Display Metrics for Suppliers, Regions, Subcategories, Products, and Restaurants
    st.write("Unique Suppliers")
    st.write(extract_unique_values(df, 'Supplier'))

    st.write("Unique Regions")
    st.write(extract_unique_values(df, 'region'))

    st.write("Unique Subcategories")
    st.write(extract_unique_values(df, 'sub_cat'))

    st.write("Unique Products")
    st.write(extract_unique_values(df, 'product_name'))

    st.write("Unique Restaurants per Region")
    restaurants_per_region = df.groupby('region')['Restaurant_name'].unique().reset_index()
    restaurants_per_region = restaurants_per_region.rename(columns={'Restaurant_name': 'Restaurants'})
    st.write(restaurants_per_region)

    # Download Report Button
    if st.sidebar.button("Download Report"):
        output_file = f"summary_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        with pd.ExcelWriter(output_file) as writer:
            supplier_GMV.to_excel(writer, sheet_name='Supplier_GMV', index=False)
            supplier_region_GMV.to_excel(writer, sheet_name='Supplier_Region_GMV', index=False)
            subcategory_GMV.to_excel(writer, sheet_name='Subcategory_GMV', index=False)
            subcategory_supplier_GMV.to_excel(writer, sheet_name='Subcategory_Supplier_GMV', index=False)
            subcategory_region_GMV.to_excel(writer, sheet_name='Subcategory_Region_GMV', index=False)
            restaurant_region_GMV.to_excel(writer, sheet_name='Restaurant_Region_GMV', index=False)
            extract_unique_values(df, 'Supplier').to_excel(writer, sheet_name='Unique_Suppliers', index=False)
            extract_unique_values(df, 'region').to_excel(writer, sheet_name='Unique_Regions', index=False)
            extract_unique_values(df, 'sub_cat').to_excel(writer, sheet_name='Unique_Subcategories', index=False)
            extract_unique_values(df, 'product_name').to_excel(writer, sheet_name='Unique_Products', index=False)
            restaurants_per_region.to_excel(writer, sheet_name='Restaurants_Per_Region', index=False)

        with open(output_file, "rb") as file:
            st.download_button(
                label="Download Excel Report",
                data=file,
                file_name=output_file,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
