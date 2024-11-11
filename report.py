import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# --- Helper Functions ---
def calculate_GMV(df, group_by_columns, sum_column='GMV'):
    """Calculates GMV by grouping specified columns."""
    try:
        if sum_column not in df.columns:
            raise KeyError(f"Missing column for GMV calculation: {sum_column}")
        
        gmv = df.groupby(group_by_columns)[sum_column].sum().reset_index()
        gmv = gmv.rename(columns={sum_column: 'GMV'}).sort_values(by='GMV', ascending=False)
        return gmv.round(0).astype({'GMV': int})
    except KeyError as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

def calculate_difference_and_growth(df_Last_Week, df_This_Week, group_by_columns):
    """Calculates Growth percentage between two weeks."""
    comparison = pd.merge(df_Last_Week, df_This_Week, on=group_by_columns, suffixes=('_Last_Week', '_This_Week'), how='outer').fillna(0)
    comparison['Difference (€)'] = comparison['GMV_This_Week'] - comparison['GMV_Last_Week']
    comparison['Growth (%)'] = comparison.apply(
        lambda row: (row['Difference (€)'] / row['GMV_Last_Week'] * 100) if row['GMV_Last_Week'] != 0 else 0, axis=1
    )
    
    # Sort the comparison table by Total GMV Week 2 in descending order
    comparison = comparison.sort_values(by='GMV_This_Week', ascending=False)
    
    # Remove index after sorting
    comparison = comparison.reset_index(drop=True)
    
    return comparison.round({'Growth (%)': 1, 'Difference (€)': 0}).astype({'Difference (€)': int})

# --- Main Streamlit App ---
st.title("Weekly Analysis")

# File uploader for two weeks
uploaded_file_Last_Week = st.file_uploader("Last Week", type="xlsx")
uploaded_file_This_Week = st.file_uploader("This Week", type="xlsx")

if uploaded_file_Last_Week and uploaded_file_This_Week:
    df_Last_Week = pd.read_excel(uploaded_file_Last_Week)
    df_This_Week = pd.read_excel(uploaded_file_This_Week)



    # Sidebar Section Selection
    st.sidebar.header("Select Analysis Sections")
    sections = st.sidebar.multiselect(
        "Choose Analysis Sections", 
        ["Summary", "Region", "Supplier", "Subcategory","Restaurants","GMV by Region and Subcategory", "Orders Frequency", "Daily Analysis"]
    )

    # High-Level Summary for GMV Growth
    if "Summary" in sections:
        st.subheader("Summary")
        
        # Total GMV for each week
        gmv_Last_Week = df_Last_Week['GMV'].sum() if 'GMV' in df_Last_Week.columns else 0
        gmv_This_Week = df_This_Week['GMV'].sum() if 'GMV' in df_This_Week.columns else 0
        growth_total_gmv = (gmv_This_Week - gmv_Last_Week) / gmv_Last_Week * 100 if gmv_Last_Week != 0 else 0
        st.metric("Last Week", f"{gmv_Last_Week:,.0f} €")
        st.metric("This Week", f"{gmv_This_Week:,.0f} €")
        diff_total_gmv = gmv_This_Week - gmv_Last_Week
        
        st.metric("Difference", f"{diff_total_gmv:,.0f} €")
        st.metric("Growth Rate", f"{growth_total_gmv:.1f}%")

    # Regional GMV Comparison
    
    if "Region" in sections:
    # Sidebar Region Selection
        st.sidebar.header("Select Region")
        regions = df_Last_Week['region'].unique()  # Assuming 'region' is the column name
        region_choice = st.sidebar.selectbox("Choose Region", regions)

        st.subheader(f"Regional Growth for {region_choice}")

        st.write("**Subcategories**")
        region_subcategory_Last_Week = calculate_GMV(df_Last_Week[df_Last_Week['region'] == region_choice], ['sub_cat'])
        region_subcategory_This_Week = calculate_GMV(df_This_Week[df_This_Week['region'] == region_choice], ['sub_cat'])
        comparison_subcategory = calculate_difference_and_growth(region_subcategory_Last_Week, region_subcategory_This_Week, ['sub_cat'])
        st.write(comparison_subcategory)

        st.write("**Suppliers**")
        region_supplier_Last_Week = calculate_GMV(df_Last_Week[df_Last_Week['region'] == region_choice], ['Supplier'])
        region_supplier_This_Week = calculate_GMV(df_This_Week[df_This_Week['region'] == region_choice], ['Supplier'])
        comparison_supplier = calculate_difference_and_growth(region_supplier_Last_Week, region_supplier_This_Week, ['Supplier'])
        st.write(comparison_supplier)

        st.write("**Restaurant Names**")
        region_restaurant_Last_Week = calculate_GMV(df_Last_Week[df_Last_Week['region'] == region_choice], ['Restaurant_name'])
        region_restaurant_This_Week = calculate_GMV(df_This_Week[df_This_Week['region'] == region_choice], ['Restaurant_name'])
        comparison_restaurant = calculate_difference_and_growth(region_restaurant_Last_Week, region_restaurant_This_Week, ['Restaurant_name'])
        st.write(comparison_restaurant)

        st.write("**Products**")
        region_product_Last_Week = calculate_GMV(df_Last_Week[df_Last_Week['region'] == region_choice], ['product_name'])
        region_product_This_Week = calculate_GMV(df_This_Week[df_This_Week['region'] == region_choice], ['product_name'])
        comparison_product = calculate_difference_and_growth(region_product_Last_Week, region_product_This_Week, ['product_name'])
        st.write(comparison_product)

    # Supplier GMV Comparison
    if "Supplier" in sections:
        st.subheader("Supplier Growth")
        supplier_gmv_Last_Week = calculate_GMV(df_Last_Week, ['Supplier'])
        supplier_gmv_This_Week = calculate_GMV(df_This_Week, ['Supplier'])
        comparison_supplier = calculate_difference_and_growth(supplier_gmv_Last_Week, supplier_gmv_This_Week, ['Supplier'])
        st.write(comparison_supplier)

    # Subcategory GMV Comparison
    if "Subcategory" in sections:
        st.subheader("Subcategory Growth")
        subcategory_gmv_Last_Week = calculate_GMV(df_Last_Week, ['sub_cat'])
        subcategory_gmv_This_Week = calculate_GMV(df_This_Week, ['sub_cat'])
        comparison_subcategory = calculate_difference_and_growth(subcategory_gmv_Last_Week, subcategory_gmv_This_Week, ['sub_cat'])
        st.write(comparison_subcategory)

    if "Restaurants" in sections:
        st.subheader("Restaurant Ordering Frequency")

        # Get the restaurants that ordered last week and this week
        restaurants_last_week = df_Last_Week[df_Last_Week['GMV'] > 0].drop_duplicates(subset=['Restaurant_name', 'region'])
        restaurants_this_week = df_This_Week[df_This_Week['GMV'] > 0].drop_duplicates(subset=['Restaurant_name', 'region'])

        # 1. Restaurants that ordered last week but did not order this week
        restaurants_last_week_not_this_week = restaurants_last_week[~restaurants_last_week['Restaurant_name'].isin(restaurants_this_week['Restaurant_name'])]
        restaurants_last_week_not_this_week = restaurants_last_week_not_this_week[['Restaurant_name', 'region', 'GMV']]
        restaurants_last_week_not_this_week = restaurants_last_week_not_this_week.groupby(['Restaurant_name', 'region']).sum().reset_index()

        # 2. Restaurants that ordered this week but did not order last week
        restaurants_this_week_not_last_week = restaurants_this_week[~restaurants_this_week['Restaurant_name'].isin(restaurants_last_week['Restaurant_name'])]
        restaurants_this_week_not_last_week = restaurants_this_week_not_last_week[['Restaurant_name', 'region', 'GMV']]
        restaurants_this_week_not_last_week = restaurants_this_week_not_last_week.groupby(['Restaurant_name', 'region']).sum().reset_index()

        count_not_reordered = restaurants_last_week_not_this_week['Restaurant_name'].nunique()
        total_gmv_not_reordered = restaurants_last_week_not_this_week['GMV'].sum()
        count_new_winback = restaurants_this_week_not_last_week['Restaurant_name'].nunique()
        total_gmv_new_winback = restaurants_this_week_not_last_week['GMV'].sum()


        st.subheader(f"Did NOT Reorder (Count: {count_not_reordered}, Total GMV: {total_gmv_not_reordered})")
        st.write(restaurants_last_week_not_this_week)

        st.subheader(f"New/Winback/Biweekly (Count: {count_new_winback}, Total GMV: {total_gmv_new_winback})")
        st.write(restaurants_this_week_not_last_week)

  # Revenue by Region and Subcategory (Heatmap)
    if "GMV by Region and Subcategory" in sections:
        st.subheader("GMV by Region and Subcategory")
        
        region_subcategory_gmv_Last_Week = df_Last_Week.groupby(['region', 'sub_cat'])['GMV'].sum().reset_index()
        region_subcategory_gmv_This_Week = df_This_Week.groupby(['region', 'sub_cat'])['GMV'].sum().reset_index()

        # Combine both weeks into a single DataFrame for comparison
        combined_gmv = pd.merge(region_subcategory_gmv_Last_Week, region_subcategory_gmv_This_Week, on=['region', 'sub_cat'], suffixes=('_Last_Week', '_This_Week'))

        # Create a heatmap
        pivot_table = combined_gmv.pivot_table(index='region', columns='sub_cat', values='GMV_This_Week', aggfunc='sum')
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(pivot_table, annot=True, cmap='Blues', fmt='.0f', ax=ax)
        st.pyplot(fig)

    # Order Frequency and Size Comparison
    if "Orders Frequency" in sections:
        st.subheader("Orders Frequency")
        
        df_Last_Week['order_value'] = df_Last_Week['GMV']
        df_This_Week['order_value'] = df_This_Week['GMV']
        
        # Calculate Average Order Value (AOV)
        aov_last_week = df_Last_Week['order_value'].mean()
        aov_this_week = df_This_Week['order_value'].mean()
        
        # Calculate number of orders per customer (assuming 'Customer_id' exists)
        orders_last_week = df_Last_Week.groupby('Restaurant_id').size().mean()
        orders_this_week = df_This_Week.groupby('Restaurant_id').size().mean()
        
        st.metric("Average Order Value (Last Week)", f"{aov_last_week:,.0f} €")
        st.metric("Average Order Value (This Week)", f"{aov_this_week:,.0f} €")
        st.metric("Orders per Customer (Last Week)", f"{orders_last_week:.0f}")
        st.metric("Orders per Customer (This Week)", f"{orders_this_week:.0f}")

    # Time of Day/Week Analysis (by Day)
    if "Daily Analysis" in sections:
        st.subheader("Daily Analysis")
        
        # Convert 'Date' column to datetime format (assuming 'Date' exists in the dataset)
        df_Last_Week['order_datetime'] = pd.to_datetime(df_Last_Week['Date'], format="%d/%m/%Y %H:%M:%S")
        df_This_Week['order_datetime'] = pd.to_datetime(df_This_Week['Date'], format="%d/%m/%Y %H:%M:%S")
        
        # Extract day of the week (0=Monday, 1=Tuesday, ..., 6=Sunday)
        df_Last_Week['day_of_week'] = df_Last_Week['order_datetime'].dt.day_name()
        df_This_Week['day_of_week'] = df_This_Week['order_datetime'].dt.day_name()
        
        # Calculate GMV by day of the week
        gmv_by_day_last_week = df_Last_Week.groupby('day_of_week')['GMV'].sum().reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
        gmv_by_day_this_week = df_This_Week.groupby('day_of_week')['GMV'].sum().reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])

        # Plot GMV by day of the week for both weeks
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(gmv_by_day_last_week.index, gmv_by_day_last_week, label='Last Week', marker='o')
        ax.plot(gmv_by_day_this_week.index, gmv_by_day_this_week, label='This Week', marker='o')
        ax.set_xlabel('Day of the Week')
        ax.set_ylabel('GMV (€)')
        ax.legend()
        st.pyplot(fig)
else:
    st.warning("Please upload data files for both weeks.")
