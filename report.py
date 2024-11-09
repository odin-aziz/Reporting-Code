import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from prophet import Prophet
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import LabelEncoder

# Load the dataset
df = pd.read_excel('PD W44.xlsx')


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


def save_metrics_to_excel(df, output_file=None):
    if not output_file:
        output_file = f"summary_{datetime.now().strftime('%Y-%m-%d')}.xlsx"

    supplier_GMV = get_supplier_GMV(df)
    subcategory_GMV = get_subcategory_GMV(df)
    region_GMV = get_region_GMV(df)
    restaurant_GMV = get_restaurant_GMV(df)
    restaurant_region_GMV = get_restaurant_region_GMV(df)
    restaurant_supplier_region_GMV = get_restaurant_supplier_region_GMV(df)
    product_supplier_region_GMV = get_product_supplier_region_GMV(df)
    top_restaurants = get_top_restaurants_per_supplier_region(df)
    top_products = get_top_products_per_supplier_region(df)
    supplier_region_contribution = get_supplier_region_contribution(df)

    with pd.ExcelWriter(output_file) as writer:
        if not supplier_GMV.empty:
            supplier_GMV.to_excel(writer, sheet_name='Supplier_GMV', index=False)
        if not subcategory_GMV.empty:
            subcategory_GMV.to_excel(writer, sheet_name='Subcategory_GMV', index=False)
        if not region_GMV.empty:
            region_GMV.to_excel(writer, sheet_name='Region_GMV', index=False)
        if not restaurant_GMV.empty:
            restaurant_GMV.to_excel(writer, sheet_name='Restaurant_GMV', index=False)
        if not restaurant_region_GMV.empty:
            restaurant_region_GMV.to_excel(writer, sheet_name='Restaurant_Region_GMV', index=False)
        if not restaurant_supplier_region_GMV.empty:
            restaurant_supplier_region_GMV.to_excel(writer, sheet_name='Restaurant_Supplier_Region_GMV', index=False)
        if not product_supplier_region_GMV.empty:
            product_supplier_region_GMV.to_excel(writer, sheet_name='Product_Supplier_Region_GMV', index=False)
        if not top_restaurants.empty:
            top_restaurants.to_excel(writer, sheet_name='Top_Restaurants_Per_Supplier', index=False)
        if not top_products.empty:
            top_products.to_excel(writer, sheet_name='Top_Products_Per_Supplier', index=False)
        if not supplier_region_contribution.empty:
            supplier_region_contribution.to_excel(writer, sheet_name='Supplier_Region_Contribution', index=False)
    
    print(f"All metrics saved to {output_file}")


# Run calculations and save metrics
supplier_GMV = get_supplier_GMV(df)
subcategory_GMV = get_subcategory_GMV(df)
region_GMV = get_region_GMV(df)
restaurant_GMV = get_restaurant_GMV(df)
restaurant_region_GMV = get_restaurant_region_GMV(df)
restaurant_supplier_region_GMV = get_restaurant_supplier_region_GMV(df)
product_supplier_region_GMV = get_product_supplier_region_GMV(df)

# Save to Excel with a dynamic filename
save_metrics_to_excel(df)
