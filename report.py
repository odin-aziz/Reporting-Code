import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO
import numpy as np
from datetime import datetime, timedelta
import altair as alt
from sklearn.ensemble import RandomForestClassifier

def create_weekly_order_tracking(data, agg_func='sum', show_plots=True, week_start='Monday'):
    """
    Tracks weekly orders for customers and extracts purchasing patterns.
    """
    # Convert dates to datetime format and check validity
    data['Date de commande'] = pd.to_datetime(data['Date de commande'], dayfirst=True, errors='coerce')
    
    if data['Date de commande'].isnull().any():
        print("Warning: Some rows have invalid date values. These will be excluded.")
        data = data.dropna(subset=['Date de commande'])
    
    # Debugging the date range
    min_date = data['Date de commande'].min()
    max_date = data['Date de commande'].max()
    print(f"Date range in dataset: {min_date} to {max_date}")
    
    # Add Year-Week column based on order date
    data['Year_Week'] = data['Date de commande'].apply(lambda x: f"{x.isocalendar()[0]}-W{x.isocalendar()[1]:02d}")
    
    # Create pivot table for weekly tracking using Year_Week
    weekly_tracking = data.pivot_table(
        index='Restaurant', 
        columns='Year_Week',
        values='GMV_Euro', 
        aggfunc=agg_func
    ).fillna(0)
    
    # Add total GMV for each restaurant
    weekly_tracking['Total_GMV'] = weekly_tracking.sum(axis=1)
    
    # Optimize supplier and region mappings
    supplier_map = data.groupby('Restaurant')['Canal'].apply(lambda x: ', '.join(map(str, x.unique()))).to_dict()
    region_map = data.groupby('Restaurant')['Region'].first().to_dict()
    
    weekly_tracking['Suppliers'] = weekly_tracking.index.map(supplier_map)
    weekly_tracking['Region'] = weekly_tracking.index.map(region_map)
    
    # Round GMV values
    weekly_tracking = weekly_tracking.round()
    
    # Reset index for final output
    weekly_tracking.reset_index(inplace=True)
       
    return weekly_tracking

   
def extract_customer_segments_with_gmv(weekly_tracking, churn_threshold=4, winback_threshold=4):
    churned = []
    reactivated = []
    winback = []
    
    # Loop through each restaurant (customer)
    for idx, row in weekly_tracking.iterrows():
        gmv_values = row[1:-2].values  # Extract the GMV data (excluding the restaurant name, Region, and Suppliers columns)
        restaurant_name = row['Restaurant']
        region = row['Region']  # Now region is available
        supplier = row['Canal']  # Now supplier info is available
        total_gmv = gmv_values.sum()  # Total GMV for the restaurant
        
        # Find the week of first and last order
        first_order_week = next((week for i, week in enumerate(gmv_values) if week > 0), None)
        last_order_week = next((week for i, week in reversed(list(enumerate(gmv_values))) if week > 0), None)
        
        # If no orders were placed (both first_order_week and last_order_week will be None), skip this customer
        if first_order_week is None or last_order_week is None:
            continue
        
        # Format the weeks (in Year-Week format)
        first_order_week = row.index[1 + list(gmv_values).index(first_order_week)]  # Index of the first order week
        last_order_week = row.index[1 + list(gmv_values).index(last_order_week)]  # Index of the last order week
        
        # Check for churn: no GMV > 0 for 'churn_threshold' consecutive weeks
        if len([week for week in gmv_values[-churn_threshold:] if week > 0]) == 0:
            churned.append([restaurant_name, total_gmv, first_order_week, last_order_week, region, supplier])
        
        # Check for reactivation: GMV > 0 after a period of GMV == 0
        if any(gmv_values[-(churn_threshold + 1):]) and any(week == 0 for week in gmv_values[-(churn_threshold + 1):-1]):
            reactivated.append([restaurant_name, total_gmv, first_order_week, last_order_week, region, supplier])
        
        # Check for winback: GMV == 0 for 'winback_threshold' weeks, then GMV > 0
        if len([week for week in gmv_values[-(winback_threshold + 1):-1] if week == 0]) == winback_threshold and gmv_values[-1] > 0:
            winback.append([restaurant_name, total_gmv, first_order_week, last_order_week, region, supplier])
    
    # Convert lists to DataFrames and add Region and Supplier columns
    churned_df = pd.DataFrame(churned, columns=['Restaurant_name', 'Total_GMV', 'First_Order_Week', 'Last_Order_Week', 'Region', 'Supplier'])
    reactivated_df = pd.DataFrame(reactivated, columns=['Restaurant_name', 'Total_GMV', 'First_Order_Week', 'Last_Order_Week', 'Region', 'Supplier'])
    winback_df = pd.DataFrame(winback, columns=['Restaurant_name', 'Total_GMV', 'First_Order_Week', 'Last_Order_Week', 'Region', 'Supplier'])
    
    return churned_df, reactivated_df, winback_df




def classify_order_frequency_table(df, date_column='Date de commande', restaurant_column='Restaurant', order_id_column='numero de commande (valide)'):
    # Ensure the date column is in datetime format
    df[date_column] = pd.to_datetime(df[date_column], dayfirst=True, errors='coerce')

    # Drop rows with invalid dates
    if df[date_column].isnull().any():
        print("Warning: Some rows have invalid date values. These will be excluded.")
        df = df.dropna(subset=[date_column])

    # Sort data by Restaurant and Date
    df = df.sort_values(by=[restaurant_column, date_column])

    # Initialize an empty list to store results
    results = []

    # Group by Restaurant
    for restaurant, group in df.groupby(restaurant_column):
        # Track each month’s classification separately
        group['Month'] = group[date_column].dt.to_period('M')
        monthly_classification = {}

        # Loop through each month and classify ordering frequency
        for month, month_data in group.groupby('Month'):
            # Calculate days between orders
            month_data = month_data.sort_values(date_column)
            month_data['Days_Between'] = month_data[date_column].diff().dt.days

            # Drop first NaN (as it has no previous order to compare)
            month_data = month_data.dropna(subset=['Days_Between'])

            # Calculate average days between orders for the month
            avg_days = month_data['Days_Between'].mean()

            # Classify based on average days between orders
            if avg_days <= 7:
                classification = "Weekly"
            elif avg_days <= 14:
                classification = "Biweekly"
            elif avg_days <= 30:
                classification = "Monthly"
            else:
                classification = "Infrequent"

            # Save the classification for the month
            monthly_classification[str(month)] = classification

        # Determine the most common pattern over months or note mixed behavior
        if monthly_classification:
            main_pattern = pd.Series(list(monthly_classification.values())).mode()[0]
            if len(set(monthly_classification.values())) > 1:
                main_pattern = f"Mixed ({main_pattern})"
        else:
            main_pattern = "No Orders"

        # Prepare row for this restaurant
        row = {
            "Restaurant Name": restaurant,
            "Overall Classification": main_pattern,
        }

        # Add monthly classifications to the row
        row.update(monthly_classification)
        results.append(row)

    # Convert results into a DataFrame for table format
    result_df = pd.DataFrame(results)

    # Fill NaN values with "-" for any missing months
    result_df = result_df.fillna("-")

    return result_df


def create_weekly_supplier_gmv(data, agg_func='sum', week_start='Monday'):
    """
    Creates a table showing GMV per supplier on a weekly basis across all available years.

    Args:
    - data (pd.DataFrame): The dataset containing supplier GMV information.
    - agg_func (str or function): Aggregation function for GMV. Defaults to 'sum'.
    - week_start (str): Determines the start of the week. Defaults to 'Monday'.

    Returns:
    - pd.DataFrame: Weekly GMV table with suppliers across all years.
    """
    # Convert 'Date de commande' to datetime
    data['Date de commande'] = pd.to_datetime(data['Date de commande'], dayfirst=True, errors='coerce')

    # Ensure all GMV values are numeric, and replace NaN or invalid values with 0
    data['GMV_Euro'] = pd.to_numeric(data['GMV_Euro'], errors='coerce').fillna(0)

    # Drop rows with missing or invalid dates
    data = data.dropna(subset=['Date de commande'])

    # Extract Year-Week based on the specified week start
    if week_start == 'Monday':
        data['Year_Week'] = data['Date de commande'].dt.strftime('%Y-W%U')  # Week starting Monday
    else:
        data['Year_Week'] = data['Date de commande'].dt.strftime('%Y-W%U')  # Week starting Sunday

    # Determine the full range of Year-Weeks present in the data
    full_year_weeks = (
        pd.date_range(
            start=data['Date de commande'].min(),
            end=data['Date de commande'].max(),
            freq='W-MON' if week_start == 'Monday' else 'W-SUN'
        )
        .strftime('%Y-W%U')
    )

    # Create pivot table with weekly GMV per supplier
    weekly_gmv = data.pivot_table(
        index='Canal',  # Using 'Canal' for Supplier representation
        columns='Year_Week',
        values='GMV_Euro',
        aggfunc=agg_func
    ).fillna(0)

    # Reindex columns to include all Year-Weeks
    weekly_gmv = weekly_gmv.reindex(columns=full_year_weeks, fill_value=0)

    # Validate GMV calculations (ensures summing is correct)
    weekly_gmv['Total_GMV'] = weekly_gmv.sum(axis=1)

    # Round GMV values to 2 decimal places
    weekly_gmv = weekly_gmv.round(2)

    # Reset index for a cleaner display
    weekly_gmv.reset_index(inplace=True)

    return weekly_gmv


# -----------------





def analysis(df_last_week, df_this_week):
    st.title("Business Analysis")
    st.markdown("---")

    # **Summary Section**
    st.header("Summary of Key Metrics")
    overall_gmv_last = df_last_week["GMV"].sum()
    overall_gmv_this = df_this_week["GMV"].sum()
    overall_customer_count_last = df_last_week["Restaurant_id"].nunique()
    overall_customer_count_this = df_this_week["Restaurant_id"].nunique()

    gmv_growth = ((overall_gmv_this - overall_gmv_last) / overall_gmv_last * 100).round(2)
    customer_growth = round(((overall_customer_count_this - overall_customer_count_last) / overall_customer_count_last * 100), 2)

    summary_data = pd.DataFrame({
        "Metric": ["GMV", "Number of Customers"],
        "Last Week": [overall_gmv_last, overall_customer_count_last],
        "This Week": [overall_gmv_this, overall_customer_count_this],
        "Growth Rate (%)": [gmv_growth, customer_growth]
    })

    st.table(summary_data)
    st.markdown("---")

    # **1 & 2. GMV and Customers per Region**
    st.header("Customers per Region")
    region_gmv_last = df_last_week.groupby("region")["GMV"].sum()
    region_gmv_this = df_this_week.groupby("region")["GMV"].sum()

    region_customer_count_last = df_last_week.groupby("region")["Restaurant_id"].nunique()
    region_customer_count_this = df_this_week.groupby("region")["Restaurant_id"].nunique()

    region_comparison = pd.concat(
        [region_gmv_last, region_gmv_this, region_customer_count_last, region_customer_count_this],
        axis=1,
        keys=["GMV Last Week", "GMV This Week", "Customers Last Week", "Customers This Week"]
    )

    region_comparison["GMV Growth (%)"] = (
        (region_comparison["GMV This Week"] - region_comparison["GMV Last Week"]) / 
        region_comparison["GMV Last Week"] * 100
    ).round(2)
    region_comparison["Customer Growth (%)"] = (
        (region_comparison["Customers This Week"] - region_comparison["Customers Last Week"]) / 
        region_comparison["Customers Last Week"] * 100
    ).round(2)

    st.write(region_comparison)
    st.markdown("---")

    # **3. Restaurants GMV Comparison**
    st.header("Restaurants")
    restaurant_gmv_last = df_last_week.groupby("Restaurant_name")["GMV"].sum()
    restaurant_gmv_this = df_this_week.groupby("Restaurant_name")["GMV"].sum()
    region_map_last_week = df_last_week.groupby("Restaurant_name")["region"].first()
    region_map_this_week = df_this_week.groupby("Restaurant_name")["region"].first()

    restaurant_gmv_comparison = pd.concat(
        [restaurant_gmv_last, restaurant_gmv_this],
        axis=1,
        keys=["Last Week GMV", "This Week GMV"]
    )
    email_map_last_week = df_last_week.groupby("Restaurant_name")["Account_email"].first()
    email_map_this_week = df_this_week.groupby("Restaurant_name")["Account_email"].first()
    restaurant_gmv_comparison["Account_email"] = restaurant_gmv_comparison.index.map(
    lambda x: email_map_last_week.get(x) or email_map_this_week.get(x)
    )
    restaurant_gmv_comparison["region"] = restaurant_gmv_comparison.index.map(
    lambda x: region_map_last_week.get(x) or region_map_this_week.get(x)
    )
    restaurant_gmv_comparison["Growth (%)"] = (
        (restaurant_gmv_comparison["This Week GMV"] - restaurant_gmv_comparison["Last Week GMV"]) / 
        restaurant_gmv_comparison["Last Week GMV"] * 100
    ).round(2)

    st.write(restaurant_gmv_comparison)


    st.markdown("---")

    # **4. Suppliers GMV Comparison**
    st.header("Suppliers GMV")
    suppliers_gmv_last = df_last_week.groupby("Supplier")["GMV"].sum()
    suppliers_gmv_this = df_this_week.groupby("Supplier")["GMV"].sum()

    suppliers_gmv_comparison = pd.concat(
        [suppliers_gmv_last, suppliers_gmv_this],
        axis=1,
        keys=["Last Week GMV", "This Week GMV"]
    )
    suppliers_gmv_comparison["Growth (%)"] = (
        (suppliers_gmv_comparison["This Week GMV"] - suppliers_gmv_comparison["Last Week GMV"]) / 
        suppliers_gmv_comparison["Last Week GMV"] * 100
    ).round(2)

    st.write(suppliers_gmv_comparison)
    st.markdown("---")


    st.header("Suppliers GMV by Product")
    
    # Ensure GMV is numeric in both datasets
    df_last_week["GMV"] = pd.to_numeric(df_last_week["GMV"], errors="coerce")
    df_this_week["GMV"] = pd.to_numeric(df_this_week["GMV"], errors="coerce")
    
    # **Last Week GMV**
    products_gmv_last = (
        df_last_week.groupby(["Supplier", "product_name"], as_index=False)["GMV"].sum()
    )
    
    # **This Week GMV**
    products_gmv_this = (
        df_this_week.groupby(["Supplier", "product_name"], as_index=False)["GMV"].sum()
    )
    
    # Merge the two weeks' data on Supplier and Product Name
    products_gmv_comparison = pd.merge(
        products_gmv_last,
        products_gmv_this,
        on=["Supplier", "product_name"],
        how="outer",
        suffixes=("_Last_Week", "_This_Week"),
    )
    
    # Replace NaN with 0 for missing GMV values
    products_gmv_comparison.fillna(0, inplace=True)
    
    # Add Difference and Growth Percentage columns
    products_gmv_comparison["Difference"] = (
        products_gmv_comparison["GMV_This_Week"] - products_gmv_comparison["GMV_Last_Week"]
    ).round(2)
    
    # Calculate Growth Rate for the GMV, taking care of division by zero (when last week's GMV is 0)
    products_gmv_comparison["Growth (%)"] = (
        (products_gmv_comparison["Difference"] /
         products_gmv_comparison["GMV_Last_Week"].replace(0, float("nan"))) * 100
    ).fillna(0).round(2)
    
    # Rename columns for clarity
    products_gmv_comparison.columns = [
        "Supplier", "Product Name", "Last Week GMV", "This Week GMV", "Difference", "Growth (%)"
    ]
    
    # Display the table
    st.write(products_gmv_comparison)



    st.title("Business Analysis (By Region)")
    st.markdown("---")

    # Create a dropdown menu to select a region
    regions = df_last_week["region"].unique()  # Get all unique regions
    selected_region = st.selectbox("Select a Region to Analyze", options=regions)

    # Filter data for the selected region
    df_last_week_region = df_last_week[df_last_week["region"] == selected_region]
    df_this_week_region = df_this_week[df_this_week["region"] == selected_region]

    st.header(f"Region: {selected_region}")
    st.markdown("---")

    # **Summary Section for the Selected Region**
    st.subheader(f"Summary of Key Metrics for {selected_region}")
    regional_gmv_last = df_last_week_region["GMV"].sum()
    regional_gmv_this = df_this_week_region["GMV"].sum()
    regional_customer_count_last = df_last_week_region["Restaurant_id"].nunique()
    regional_customer_count_this = df_this_week_region["Restaurant_id"].nunique()

    gmv_growth = ((regional_gmv_this - regional_gmv_last) / regional_gmv_last * 100).round(2)
    customer_growth = round(((regional_customer_count_this - regional_customer_count_last) / regional_customer_count_last * 100), 2)

    summary_data = pd.DataFrame({
        "Metric": ["GMV", "Number of Customers"],
        "Last Week": [regional_gmv_last, regional_customer_count_last],
        "This Week": [regional_gmv_this, regional_customer_count_this],
        "Growth Rate (%)": [gmv_growth, customer_growth]
    })

    st.table(summary_data)
    st.markdown("---")

    # **Customers in the Region**
    st.subheader(f"Customers per Region: {selected_region}")
    st.write("Customer breakdown by restaurant.")
    restaurant_gmv_last = df_last_week_region.groupby("Restaurant_name")["GMV"].sum()
    restaurant_gmv_this = df_this_week_region.groupby("Restaurant_name")["GMV"].sum()

    restaurant_customer_comparison = pd.concat(
        [restaurant_gmv_last, restaurant_gmv_this],
        axis=1,
        keys=["Last Week GMV", "This Week GMV"]
    )

    restaurant_customer_comparison["Growth (%)"] = (
        (restaurant_customer_comparison["This Week GMV"] - restaurant_customer_comparison["Last Week GMV"]) /
        restaurant_customer_comparison["Last Week GMV"] * 100
    ).round(2)

    st.write(restaurant_customer_comparison)
    st.markdown("---")

    # **Suppliers GMV in the Selected Region**
    st.subheader(f"Suppliers GMV in {selected_region}")
    suppliers_gmv_last = df_last_week_region.groupby("Supplier")["GMV"].sum()
    suppliers_gmv_this = df_this_week_region.groupby("Supplier")["GMV"].sum()

    suppliers_gmv_comparison = pd.concat(
        [suppliers_gmv_last, suppliers_gmv_this],
        axis=1,
        keys=["Last Week GMV", "This Week GMV"]
    )

    suppliers_gmv_comparison["Growth (%)"] = (
        (suppliers_gmv_comparison["This Week GMV"] - suppliers_gmv_comparison["Last Week GMV"]) /
        suppliers_gmv_comparison["Last Week GMV"] * 100
    ).round(2)

    st.write(suppliers_gmv_comparison)
    st.markdown("---")

    # **Suppliers GMV by Product in the Selected Region**
    st.subheader(f"Suppliers GMV by Product in {selected_region}")
    supplier_product_gmv_last = df_last_week_region.groupby(["Supplier", "product_name"])["GMV"].sum()
    supplier_product_gmv_this = df_this_week_region.groupby(["Supplier", "product_name"])["GMV"].sum()

    supplier_product_comparison = pd.concat(
        [supplier_product_gmv_last, supplier_product_gmv_this],
        axis=1,
        keys=["Last Week GMV", "This Week GMV"]
    )

    supplier_product_comparison["Growth (%)"] = (
        (supplier_product_comparison["This Week GMV"] - supplier_product_comparison["Last Week GMV"]) /
        supplier_product_comparison["Last Week GMV"] * 100
    ).round(2)

    st.write(supplier_product_comparison)
    st.markdown("---")

    # **Subcategories in the Selected Region**
    st.subheader(f"Subcategories in {selected_region}")
    subcategory_gmv_last = df_last_week_region.groupby("sub_cat")["GMV"].sum()
    subcategory_gmv_this = df_this_week_region.groupby("sub_cat")["GMV"].sum()

    subcategory_comparison = pd.concat(
        [subcategory_gmv_last, subcategory_gmv_this],
        axis=1,
        keys=["Last Week GMV", "This Week GMV"]
    )

    subcategory_comparison["Growth (%)"] = (
        (subcategory_comparison["This Week GMV"] - subcategory_comparison["Last Week GMV"]) /
        subcategory_comparison["Last Week GMV"] * 100
    ).round(2)

    st.write(subcategory_comparison)
    st.markdown("---")

    # **Accounts in the Selected Region**
    st.subheader(f"Accounts in {selected_region}")
    account_gmv_last = df_last_week_region.groupby("Account_email")["GMV"].sum()
    account_gmv_this = df_this_week_region.groupby("Account_email")["GMV"].sum()

    account_comparison = pd.concat(
        [account_gmv_last, account_gmv_this],
        axis=1,
        keys=["Last Week GMV", "This Week GMV"]
    )

    account_comparison["Growth (%)"] = (
        (account_comparison["This Week GMV"] - account_comparison["Last Week GMV"]) /
        account_comparison["Last Week GMV"] * 100
    ).round(2)

    st.write(account_comparison)
    st.markdown("---")

    # **Restaurants Who Did Not Reorder This Week**
    last_week_restaurants = set(df_last_week_region["Restaurant_name"].unique())
    this_week_restaurants = set(df_this_week_region["Restaurant_name"].unique())

    restaurants_not_reordered = last_week_restaurants - this_week_restaurants


    # **Restaurants Who Did Not Reorder by Account**
    st.subheader(f"Restaurants Who Did Not Reorder by Account in {selected_region}")
    restaurants_not_reordered_by_account = df_last_week_region[
        df_last_week_region["Restaurant_name"].isin(restaurants_not_reordered)
    ].groupby("Account_email")["Restaurant_name"].apply(list)

    st.write(restaurants_not_reordered_by_account)
    st.markdown("---")


























    # **5. Subcategory GMV Comparison**
    st.header("Subcategories")
    subcat_gmv_last = df_last_week.groupby("sub_cat")["GMV"].sum()
    subcat_gmv_this = df_this_week.groupby("sub_cat")["GMV"].sum()

    subcat_gmv_comparison = pd.concat(
        [subcat_gmv_last, subcat_gmv_this],
        axis=1,
        keys=["Last Week GMV", "This Week GMV"]
    )
    subcat_gmv_comparison["Growth (%)"] = (
        (subcat_gmv_comparison["This Week GMV"] - subcat_gmv_comparison["Last Week GMV"]) / 
        subcat_gmv_comparison["Last Week GMV"] * 100
    ).round(2)

    st.write(subcat_gmv_comparison)
    st.markdown("---")

    # **6. Account Email GMV Comparison**
    st.header("Accounts")
    account_gmv_last = df_last_week.groupby("Account_email")["GMV"].sum()
    account_gmv_this = df_this_week.groupby("Account_email")["GMV"].sum()

    account_gmv_comparison = pd.concat(
        [account_gmv_last, account_gmv_this],
        axis=1,
        keys=["Last Week GMV", "This Week GMV"]
    )
    account_gmv_comparison["Growth (%)"] = (
        (account_gmv_comparison["This Week GMV"] - account_gmv_comparison["Last Week GMV"]) / 
        account_gmv_comparison["Last Week GMV"] * 100
    ).round(2)

    st.write(account_gmv_comparison)
    st.markdown("---")

    # **7. Restaurants Who Did Not Reorder**
    st.header("Restaurants Who Did Not Reorder This Week")
    restaurants_last_week = set(df_last_week["Restaurant_id"].unique())
    restaurants_this_week = set(df_this_week["Restaurant_id"].unique())

    not_reordered_restaurants = restaurants_last_week - restaurants_this_week
    not_reordered_df = df_last_week[df_last_week["Restaurant_id"].isin(not_reordered_restaurants)]

    not_reordered_summary = not_reordered_df.groupby("Account_email").agg(
        GMV_Last_Week=("GMV", "sum"),
        Restaurants=("Restaurant_name", lambda x: ", ".join(x.unique()))
    ).reset_index()

    st.write("Restaurants Who Did Not Reorder by Account")
    st.write(not_reordered_summary)
    st.markdown("---")




# -----------------










st.title("Weekly Analysis")

# File uploader for two weeks
uploaded_file_Last_Week = st.file_uploader("Last Week", type="xlsx")
uploaded_file_This_Week = st.file_uploader("This Week", type="xlsx")
uploaded_file_data = st.file_uploader("Data", type="csv")


if uploaded_file_Last_Week and uploaded_file_This_Week and uploaded_file_data:
    df_Last_Week = pd.read_excel(uploaded_file_Last_Week)
    df_This_Week = pd.read_excel(uploaded_file_This_Week)
    df_data = pd.read_csv(uploaded_file_data)


    # Sidebar Section Selection
    st.sidebar.header("Select Analysis Sections")
    sections = st.sidebar.multiselect(
        "Choose Analysis Sections", 
        ["Pattern","Analysis"]
    )

    if "Pattern" in sections:

        st.subheader("Weekly Order Tracking and Pattern Analysis")
        
        # Calculate weekly order tracking
        weekly_tracking = create_weekly_order_tracking(df_data)
        
        # Display the tracking table
        st.write("### Weekly Order Tracking Table")
        st.dataframe(weekly_tracking)
        st.write(churned_customers)
        classified_data_table = classify_order_frequency_table(df_data)
        st.subheader('Classification')
        st.write(classified_data_table)
    
        
    if "Analysis" in sections:
        analysis(df_Last_Week, df_This_Week)
        









else:
    st.warning("Please upload data files for both weeks.")
