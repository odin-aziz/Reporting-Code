import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime


def get_supplier_GMV(df):
    try:
        supplier_GMV = df.groupby('Supplier')['GMV'].sum().reset_index()
        supplier_GMV = supplier_GMV.rename(columns={'GMV': 'Total GMV'})

        order_counts = df.groupby('Supplier')['order_id'].nunique().reset_index()
        order_counts = order_counts.rename(columns={'order_id': 'Total Orders'})

        supplier_summary = pd.merge(supplier_GMV, order_counts, on='Supplier')
        supplier_summary['Total GMV'] = supplier_summary['Total GMV'].round(0).astype(int)
        supplier_summary = supplier_summary.sort_values(by='Total GMV', ascending=False)
        
        return supplier_summary
    except KeyError as e:
        print(f"Missing column for supplier GMV calculation: {e}")
        return pd.DataFrame()


def get_subcategory_GMV(df):
    try:
        subcategory_GMV = df.groupby('sub_cat')['GMV'].sum().reset_index()
        subcategory_GMV = subcategory_GMV.rename(columns={'GMV': 'Total GMV'})
        subcategory_GMV['Total GMV'] = subcategory_GMV['Total GMV'].round(0).astype(int)
        subcategory_GMV = subcategory_GMV.sort_values(by='Total GMV', ascending=False)
        
        return subcategory_GMV
    except KeyError as e:
        print(f"Missing column for subcategory GMV calculation: {e}")
        return pd.DataFrame()


def get_region_GMV(df):
    try:
        region_GMV = df.groupby('region')['GMV'].sum().reset_index()
        region_GMV = region_GMV.rename(columns={'GMV': 'Total GMV'})
        region_GMV['Total GMV'] = region_GMV['Total GMV'].round(0).astype(int)
        region_GMV = region_GMV.sort_values(by='Total GMV', ascending=False)
        
        return region_GMV
    except KeyError as e:
        print(f"Missing column for region GMV calculation: {e}")
        return pd.DataFrame()


def get_restaurant_GMV(df):
    try:
        restaurant_GMV = df.groupby('Restaurant_name')['GMV'].sum().reset_index()
        restaurant_GMV = restaurant_GMV.rename(columns={'GMV': 'Total GMV'})
        restaurant_GMV['Total GMV'] = restaurant_GMV['Total GMV'].round(0).astype(int)
        restaurant_GMV = restaurant_GMV.sort_values(by='Total GMV', ascending=False)
        
        return restaurant_GMV
    except KeyError as e:
        print(f"Missing column for restaurant GMV calculation: {e}")
        return pd.DataFrame()


def get_restaurant_region_GMV(df):
    """Calculates GMV per restaurant for each region."""
    try:
        restaurant_region_GMV = df.groupby(['region', 'Restaurant_name'])['GMV'].sum().reset_index()
        restaurant_region_GMV = restaurant_region_GMV.rename(columns={'GMV': 'Total GMV'})
        restaurant_region_GMV['Total GMV'] = restaurant_region_GMV['Total GMV'].round(0).astype(int)
        restaurant_region_GMV = restaurant_region_GMV.sort_values(by=['region', 'Total GMV'], ascending=[True, False])
        
        return restaurant_region_GMV
    except KeyError as e:
        print(f"Missing columns for restaurant-region GMV calculation: {e}")
        return pd.DataFrame()


def get_restaurant_supplier_region_GMV(df):
    """Calculates GMV per restaurant for each supplier in each region."""
    try:
        restaurant_supplier_region_GMV = df.groupby(['region', 'Supplier', 'Restaurant_name'])['GMV'].sum().reset_index()
        restaurant_supplier_region_GMV = restaurant_supplier_region_GMV.rename(columns={'GMV': 'Total GMV'})
        restaurant_supplier_region_GMV['Total GMV'] = restaurant_supplier_region_GMV['Total GMV'].round(0).astype(int)
        restaurant_supplier_region_GMV = restaurant_supplier_region_GMV.sort_values(by=['region', 'Supplier', 'Total GMV'], ascending=[True, True, False])
        
        return restaurant_supplier_region_GMV
    except KeyError as e:
        print(f"Missing columns for restaurant-supplier-region GMV calculation: {e}")
        return pd.DataFrame()


def get_product_supplier_region_GMV(df):
    """Calculates GMV per product for each supplier in each region."""
    try:
        product_supplier_region_GMV = df.groupby(['region', 'Supplier', 'product_name'])['GMV'].sum().reset_index()
        product_supplier_region_GMV = product_supplier_region_GMV.rename(columns={'GMV': 'Total GMV'})
        product_supplier_region_GMV['Total GMV'] = product_supplier_region_GMV['Total GMV'].round(0).astype(int)
        product_supplier_region_GMV = product_supplier_region_GMV.sort_values(by=['region', 'Supplier', 'Total GMV'], ascending=[True, True, False])
        
        return product_supplier_region_GMV
    except KeyError as e:
        print(f"Missing columns for product-supplier-region GMV calculation: {e}")
        return pd.DataFrame()


def get_top_restaurants_per_supplier_region(df, top_n=5):
    """Extracts the top N restaurants by GMV for each supplier in each region."""
    restaurant_supplier_region_GMV = get_restaurant_supplier_region_GMV(df)
    top_restaurants = restaurant_supplier_region_GMV.groupby(['region', 'Supplier']).head(top_n).reset_index(drop=True)
    return top_restaurants


def get_top_products_per_supplier_region(df, top_n=5):
    """Extracts the top N products by GMV for each supplier in each region."""
    product_supplier_region_GMV = get_product_supplier_region_GMV(df)
    top_products = product_supplier_region_GMV.groupby(['region', 'Supplier']).head(top_n).reset_index(drop=True)
    return top_products


def get_supplier_region_contribution(df):
    """Calculates the GMV contribution percentage of each supplier to the total GMV in each region."""
    region_total_GMV = df.groupby('region')['GMV'].sum().reset_index().rename(columns={'GMV': 'Region Total GMV'})
    supplier_region_GMV = df.groupby(['region', 'Supplier'])['GMV'].sum().reset_index()
    supplier_region_contribution = pd.merge(supplier_region_GMV, region_total_GMV, on='region')
    supplier_region_contribution['Contribution (%)'] = (supplier_region_contribution['GMV'] / supplier_region_contribution['Region Total GMV'] * 100).round(2)
    supplier_region_contribution = supplier_region_contribution.sort_values(by=['region', 'Contribution (%)'], ascending=[True, False])
    return supplier_region_contribution

# Main Streamlit app
st.title("GMV Analysis Dashboard")
st.write("Upload your dataset and view analysis results.")

# File uploader
uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Display data preview
    st.subheader("Data Preview")
    st.write(df.head())

    # Option to calculate and view each metric
    st.sidebar.header("Choose Analysis to Display")

    if st.sidebar.checkbox("Supplier GMV"):
        st.subheader("Supplier GMV")
        supplier_GMV = get_supplier_GMV(df)
        st.write(supplier_GMV)
        
        # Plot supplier GMV
        fig, ax = plt.subplots()
        sns.barplot(x='Supplier', y='Total GMV', data=supplier_GMV, ax=ax)
        plt.xticks(rotation=90)
        st.pyplot(fig)

    if st.sidebar.checkbox("Subcategory GMV"):
        st.subheader("Subcategory GMV")
        subcategory_GMV = get_subcategory_GMV(df)
        st.write(subcategory_GMV)
        
        # Plot subcategory GMV
        fig, ax = plt.subplots()
        sns.barplot(x='sub_cat', y='Total GMV', data=subcategory_GMV, ax=ax)
        plt.xticks(rotation=90)
        st.pyplot(fig)

    if st.sidebar.checkbox("Region GMV"):
        st.subheader("Region GMV")
        region_GMV = get_region_GMV(df)
        st.write(region_GMV)
        
        # Plot region GMV
        fig, ax = plt.subplots()
        sns.barplot(x='region', y='Total GMV', data=region_GMV, ax=ax)
        plt.xticks(rotation=90)
        st.pyplot(fig)

    if st.sidebar.checkbox("Restaurant GMV"):
        st.subheader("Restaurant GMV")
        restaurant_GMV = get_restaurant_GMV(df)
        st.write(restaurant_GMV)
        
        # Plot restaurant GMV
        fig, ax = plt.subplots()
        sns.barplot(x='Restaurant_name', y='Total GMV', data=restaurant_GMV, ax=ax)
        plt.xticks(rotation=90)
        st.pyplot(fig)

    if st.sidebar.checkbox("Restaurant Region GMV"):
        st.subheader("Restaurant Region GMV")
        restaurant_region_GMV = get_restaurant_region_GMV(df)
        st.write(restaurant_region_GMV)

    if st.sidebar.checkbox("Restaurant Supplier Region GMV"):
        st.subheader("Restaurant Supplier Region GMV")
        restaurant_supplier_region_GMV = get_restaurant_supplier_region_GMV(df)
        st.write(restaurant_supplier_region_GMV)

    if st.sidebar.checkbox("Product Supplier Region GMV"):
        st.subheader("Product Supplier Region GMV")
        product_supplier_region_GMV = get_product_supplier_region_GMV(df)
        st.write(product_supplier_region_GMV)

    if st.sidebar.checkbox("Top Restaurants per Supplier and Region"):
        st.subheader("Top Restaurants per Supplier and Region")
        top_restaurants = get_top_restaurants_per_supplier_region(df)
        st.write(top_restaurants)

    if st.sidebar.checkbox("Top Products per Supplier and Region"):
        st.subheader("Top Products per Supplier and Region")
        top_products = get_top_products_per_supplier_region(df)
        st.write(top_products)

    if st.sidebar.checkbox("Supplier Region Contribution"):
        st.subheader("Supplier Region Contribution")
        supplier_region_contribution = get_supplier_region_contribution(df)
        st.write(supplier_region_contribution)
        
        # Plot supplier region contribution
        fig, ax = plt.subplots()
        sns.barplot(x='Supplier', y='Contribution (%)', hue='region', data=supplier_region_contribution, ax=ax)
        plt.xticks(rotation=90)
        st.pyplot(fig)

    # Download report button
    if st.sidebar.button("Download Report"):
        output_file = f"summary_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        with pd.ExcelWriter(output_file) as writer:
            get_supplier_GMV(df).to_excel(writer, sheet_name='Supplier_GMV', index=False)
            get_subcategory_GMV(df).to_excel(writer, sheet_name='Subcategory_GMV', index=False)
            get_region_GMV(df).to_excel(writer, sheet_name='Region_GMV', index=False)
            get_restaurant_GMV(df).to_excel(writer, sheet_name='Restaurant_GMV', index=False)
            get_restaurant_region_GMV(df).to_excel(writer, sheet_name='Restaurant_Region_GMV', index=False)
            get_restaurant_supplier_region_GMV(df).to_excel(writer, sheet_name='Restaurant_Supplier_Region_GMV', index=False)
            get_product_supplier_region_GMV(df).to_excel(writer, sheet_name='Product_Supplier_Region_GMV', index=False)
            get_top_restaurants_per_supplier_region(df).to_excel(writer, sheet_name='Top_Restaurants_Per_Supplier', index=False)
            get_top_products_per_supplier_region(df).to_excel(writer, sheet_name='Top_Products_Per_Supplier', index=False)
            get_supplier_region_contribution(df).to_excel(writer, sheet_name='Supplier_Region_Contribution', index=False)

        with open(output_file, "rb") as file:
            btn = st.download_button(
                label="Download Excel Report",
                data=file,
                file_name=output_file,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )