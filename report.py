import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO
import numpy as np
from datetime import datetime, timedelta
import altair as alt
import plotly.express as px

def analysis(df_last_week, df_this_week):
    st.title("Analysis")
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
    restaurant_gmv_comparison.fillna(0, inplace=True)

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
    suppliers_gmv_comparison.fillna(0, inplace=True)

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
    products_gmv_comparison.fillna(0, inplace=True)

    st.write(products_gmv_comparison)



    st.title("By Region")
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
    st.subheader(f"Key Metrics for {selected_region}")
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
    restaurant_customer_comparison.fillna(0, inplace=True)

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
    suppliers_gmv_comparison.fillna(0, inplace=True)
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
    supplier_product_comparison.fillna(0, inplace=True)

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

    # **New: Number of Restaurants per Catégorie de Cuisine**
    st.header("Restaurants per Catégorie de Cuisine")

    # Count unique restaurants per cuisine category for last week and this week
    cuisine_restaurant_last = df_last_week.groupby("Catégorie de cuisine ( NEW )")["Restaurant_id"].nunique()
    cuisine_restaurant_this = df_this_week.groupby("Catégorie de cuisine ( NEW )")["Restaurant_id"].nunique()

    # Combine both weeks into a comparison dataframe
    cuisine_restaurant_comparison = pd.concat(
        [cuisine_restaurant_last, cuisine_restaurant_this],
        axis=1,
        keys=["Last Week Restaurants", "This Week Restaurants"]
    )

    # Calculate the growth rate in restaurant count
    cuisine_restaurant_comparison["Growth (%)"] = (
        (cuisine_restaurant_comparison["This Week Restaurants"] - cuisine_restaurant_comparison["Last Week Restaurants"]) /
        cuisine_restaurant_comparison["Last Week Restaurants"] * 100
    ).round(2)

    # Replace NaN values with 0
    cuisine_restaurant_comparison.fillna(0, inplace=True)

    # Display the results
    st.write(cuisine_restaurant_comparison)
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



# ------------------------------------------------------------------------------------------

def pricing(df_last_week, df_this_week):

    st.header("Prices")

    # Ensure GMV, Weight, and unit_price are numeric
    for df in [df_last_week, df_this_week]:
        df["GMV"] = pd.to_numeric(df["GMV"], errors="coerce")
        df["Weight"] = pd.to_numeric(df["Weight"], errors="coerce")  # Changed to 'Weight'
        df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")

    # Take any row per supplier, product, and variant_id (using .first())
    products_last_week = df_last_week.groupby(["Supplier", "product_name", "variant_id"], as_index=False).first()
    products_this_week = df_this_week.groupby(["Supplier", "product_name", "variant_id"], as_index=False).first()

    # Merge the two weeks' data
    products_comparison = pd.merge(
        products_last_week[["Supplier", "product_name", "variant_id", "GMV", "Weight", "unit_price"]],  # Keep 'Weight'
        products_this_week[["Supplier", "product_name", "variant_id", "GMV", "Weight", "unit_price"]],
        on=["Supplier", "product_name", "variant_id"],
        how="outer",
        suffixes=("_Last_Week", "_This_Week")
    )

    # Rename columns for clarity
    products_comparison.rename(columns={
        "GMV_Last_Week": "Last Week GMV",
        "GMV_This_Week": "This Week GMV",
        "Weight_Last_Week": "Last Week Weight",  # Changed to 'Weight'
        "Weight_This_Week": "This Week Weight",
        "unit_price_Last_Week": "Last Week unit_price",  # Changed to 'unit_price'
        "unit_price_This_Week": "This Week unit_price"   # Changed to 'unit_price'
    }, inplace=True)

    products_comparison["This Week Price HT"] = (
        (products_comparison["This Week unit_price"] / 100) / products_comparison["This Week Weight"]
    ).replace([float('inf'), -float('inf')], 0).fillna(0).round(2)

    # Calculate Last Week Price TTC (modified)
    products_comparison["Last Week Price HT"] = (
        (products_comparison["Last Week unit_price"] / 100) / products_comparison["Last Week Weight"]
    ).replace([float('inf'), -float('inf')], 0).fillna(0).round(2)

    # Calculate the Difference and Growth between this week and last week
    products_comparison["Difference"] = (
        products_comparison["This Week Price HT"] - products_comparison["Last Week Price HT"]
    ).round(2)

    products_comparison["Growth"] = (
        (products_comparison["Difference"] / products_comparison["Last Week Price HT"]) * 100
    ).replace([float('inf'), -float('inf')], 0).fillna(0).round(2)

    # Create the final table with the required columns
    final_table = products_comparison[[
        "product_name", "variant_id", "Supplier","Last Week Weight","This Week Weight","This Week unit_price","Last Week unit_price","Last Week Price HT", "This Week Price HT", "Difference", "Growth"
    ]]

    # Create the final table with the required columns
    final_table2 = products_comparison[[
        "product_name", "variant_id", "Supplier","Last Week Price HT", "This Week Price HT", "Difference", "Growth"
    ]]

    # Display the final table
    st.write(final_table2)





    df_combined = pd.concat([df_last_week, df_this_week])

    supplier_list = df_combined["Supplier"].unique()
    supplier_filter = st.sidebar.selectbox("Select Supplier", supplier_list)

    # **Step 2: Filtered Products Based on Supplier**
    filtered_products = df_combined[df_combined["Supplier"] == supplier_filter]["product_name"].unique()
    product_filter = st.sidebar.selectbox("Select Product", filtered_products)

    # **Step 3: Filtered Variants Based on Product and Supplier**
    filtered_variants = df_combined[
        (df_combined["Supplier"] == supplier_filter) & 
        (df_combined["product_name"] == product_filter)
    ]["variant_id"].unique()
    variant_filter = st.sidebar.selectbox("Select Variant ID", filtered_variants)

    # **Apply Filters to Data**
    filtered_data = df_combined[
        (df_combined["Supplier"] == supplier_filter) & 
        (df_combined["product_name"] == product_filter) & 
        (df_combined["variant_id"] == variant_filter)
    ]
    


    # Apply filters
    filtered_data = products_comparison[
        (products_comparison['Supplier'] == supplier_filter) & 
        (products_comparison['product_name'] == product_filter) &
        (products_comparison['variant_id'] == variant_filter)
    ]

    # Display filtered data
    filtered_table = filtered_data[["product_name", "variant_id", "Last Week Price HT", "This Week Price HT"]]
    st.header(f"Price For {product_filter} - {variant_filter}")
    st.write(filtered_table)

        # Create and display the new table with prices by date
    st.header("By Date")

    # Combine last week and this week data
    df_combined = pd.concat([df_last_week, df_this_week])

    # Filter data based on user selection
    filtered_df = df_combined[
        (df_combined['Supplier'] == supplier_filter) &
        (df_combined['product_name'] == product_filter) &
        (df_combined['variant_id'] == variant_filter)
    ]

    # Convert Date column to datetime format
    filtered_df["Date"] = pd.to_datetime(filtered_df["Date"])

    # Sort by Date (ensures last occurrence per day is taken)
    filtered_df = filtered_df.sort_values(by="Date", ascending=True)
    # Keep only the last occurrence per day
    last_transaction_per_day = filtered_df.groupby(filtered_df["Date"].dt.date).tail(1).reset_index()

    last_transaction_per_day["Price HT"] = (
        (last_transaction_per_day["unit_price"] / 100) / last_transaction_per_day["Weight"]
    ).replace([float('inf'), -float('inf')], 0).fillna(0).round(2)

    # Calculate price change and trend indicators
    last_transaction_per_day["Price HT Change"] = last_transaction_per_day["Price HT"].diff().round(2)

    last_transaction_per_day["Trend"] = last_transaction_per_day["Price HT Change"].apply(
        lambda x: "📈" if x > 0 else ("📉" if x < 0 else "➖")
    )

    # Display the final table
    st.write(last_transaction_per_day[["Date", "Price HT", "Price HT Change", "Trend"]])    

    # Filter products_comparison by the selected variant_id
    filtered_variant_data = products_comparison[products_comparison['variant_id'] == variant_filter]


    st.header("Daily GMV and Total Weight for Selected Variant")

    # Combine last week and this week data
    df_combined = pd.concat([df_last_week, df_this_week])

    # Ensure Date column exists
    if "Date" not in df_combined.columns:
        st.error("The Date column is missing from the dataset!")
    else:
        # Convert Date column to datetime format
        df_combined["Date"] = pd.to_datetime(df_combined["Date"])

        # Filter data for the selected variant_id
        filtered_variant_data = df_combined[df_combined["variant_id"] == variant_filter]

        # Group by Date and sum GMV and total_weight
        daily_summary = (
            filtered_variant_data.groupby(filtered_variant_data["Date"].dt.date)
            .agg({"GMV": "sum", "total_weight": "sum"}).reset_index()
        )

        # Rename columns for clarity
        daily_summary.rename(columns={"total_weight": "Total Weight", "Date": "Date"}, inplace=True)

        # Display the table
        st.write(daily_summary)


    # Create and display the GMV summary by Price HT and Date
    st.header("By Price Point")

    # Ensure Date column exists
    if "Date" not in df_combined.columns:
        st.error("The Date column is missing from the dataset!")
    else:
        # Convert Date column to datetime format
        df_combined["Date"] = pd.to_datetime(df_combined["Date"])

        # Filter data for the selected variant_id
        filtered_variant_data = df_combined[df_combined["variant_id"] == variant_filter]

        # Ensure Price HT is calculated correctly
        filtered_variant_data["Price HT"] = (
            (filtered_variant_data["unit_price"] / 100) / filtered_variant_data["Weight"]
        ).replace([float('inf'), -float('inf')], 0).fillna(0).round(2)

        # Group by Date and Price HT, summing GMV
        gmv_by_price = (
            filtered_variant_data.groupby(["Price HT"], as_index=False)
            .agg({"GMV": "sum","Weight":"sum"})
        )
        
        st.write(filtered_variant_data)

        # Display the table
        st.write(gmv_by_price)



    st.header("Price Evolution Chart")

    # **Create a Line Chart with Plotly**
    fig = px.line(
        last_transaction_per_day, 
        x="Date", 
        y="Price HT", 
        markers=True, 
        title=f"{product_filter} - {variant_filter}",
        labels={"Date": "Days", "Price HT": "Price (€)"},
        line_shape="linear"
    )

    # **Customize Appearance**
    fig.update_traces(line=dict(color="green", width=2))
    fig.update_layout(
        xaxis_title="Days",
        yaxis_title="Price (€)",
        template="plotly_white",
        hovermode="x",
    )

    # **Display the Chart in Streamlit**
    st.plotly_chart(fig)

  
    # Sample data
    competitive_table = final_table2[final_table2["product_name"] == product_filter][["variant_id", "Supplier", "This Week Price HT"]]
    competitive_table = competitive_table[competitive_table["This Week Price HT"] != 0]
    
    st.dataframe(competitive_table)

    competitor_supplier = st.sidebar.selectbox("Compare with Supplier", [s for s in supplier_list if s != supplier_filter])

    competitor_df = df_combined[
        (df_combined['Supplier'] == competitor_supplier) &
        (df_combined['product_name'] == product_filter) &
        (df_combined['variant_id'] == variant_filter)
    ]

    if not competitor_df.empty:
        competitor_df["Date"] = pd.to_datetime(competitor_df["Date"])
        competitor_df = competitor_df.sort_values(by="Date", ascending=True)
        competitor_df["Price HT"] = (
            (competitor_df["unit_price"] / 100) / competitor_df["Weight"]
        ).replace([float('inf'), -float('inf')], 0).fillna(0).round(2)

        fig.add_trace(px.line(competitor_df, x="Date", y="Price HT").data[0])

    st.plotly_chart(fig)

 

def Customers(df_last_week, df_this_week):
    
    st.title("Customers")

    # Combine datasets and add week identifier
    df_last_week["Week"] = "Last Week"
    df_this_week["Week"] = "This Week"
    df = pd.concat([df_last_week, df_this_week])
    # Convert the Date column to datetime if not already
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Get unique regions and add an 'All' option
    regions = df["region"].unique().tolist()
    regions.insert(0, "All Regions")

    # Region selection dropdown
    selected_region = st.selectbox("Select a Region", regions, key="region_select")

    # Filter customers based on region if one is selected
    if selected_region == "All Regions":
        filtered_df = df
    else:
        filtered_df = df[df["region"] == selected_region]

   # -------------------- WEEKLY ORDERS FOR ALL CUSTOMERS IN THE SELECTED REGION --------------------
    st.subheader(f"Weekly Orders for Customers in {selected_region}")

    # Extract week number from the Date column
    filtered_df["Week_Number"] = filtered_df["Date"].dt.isocalendar().week

    # Group by week, customer (Restaurant Name) and sum GMV
    weekly_orders = filtered_df.groupby(["Week_Number", "Restaurant_name"])["GMV"].sum().reset_index()
    weekly_orders_pivot = weekly_orders.pivot_table(index="Restaurant_name", columns="Week_Number", values="GMV", aggfunc="sum", fill_value=0)

    # Display weekly orders table for all customers in the selected region
    st.dataframe(weekly_orders_pivot.sort_index(axis=1))  # Sort by week number columns
    



    # Get unique restaurant names
    customers = filtered_df["Restaurant_name"].unique()
    selected_customer = st.selectbox("Select a Customer", customers, key="customer_select")

    if selected_customer:
        # Filter data for the selected customer
        customer_data = filtered_df[filtered_df["Restaurant_name"] == selected_customer]

        # Extract customer info
        customer_region = customer_data["region"].iloc[0]  # Assuming region is consistent
        total_gmv = customer_data["GMV"].sum()

        # GMV per supplier
        suppliers_gmv = customer_data.groupby("Supplier")["GMV"].sum().reset_index()

        # GMV per supplier and product
        suppliers_products_gmv = customer_data.groupby(["Supplier", "product_name"])["GMV"].sum().reset_index()

        # Display customer details
        st.subheader(f"Customer: {selected_customer}")
        st.write(f"**Region:** {customer_region}")
        st.write(f"**Total GMV:** €{total_gmv:,.2f}")

        # Display supplier GMV table
        st.subheader("Suppliers & GMV")
        st.dataframe(suppliers_gmv.sort_values(by="GMV", ascending=False))

        # Display suppliers & products GMV table
        st.subheader("Suppliers, Products & GMV")
        st.dataframe(suppliers_products_gmv.sort_values(by="GMV", ascending=False))

        st.subheader(f"Orders per Week for {selected_customer}")

            # Extract week number from the Date column
        customer_data["Week_Number"] = customer_data["Date"].dt.isocalendar().week

            # Group by week, supplier and sum GMV
        weekly_data = customer_data.groupby(["Week_Number", "Supplier"])["GMV"].sum().reset_index()

            # Display weekly data table
        st.dataframe(weekly_data.sort_values(by=["Week_Number", "GMV"], ascending=[True, False]))

    else:
            st.warning(f"No data found for customer: {selected_customer}")





    suppliers = df["Supplier"].unique()
    selected_supplier = st.selectbox("Select a Supplier", suppliers, key="supplier_select")

    if selected_supplier:
        # Filter data for the selected supplier
        supplier_data = df[df["Supplier"] == selected_supplier]

        # GMV per customer
        customers_gmv = supplier_data.groupby("Restaurant_name")["GMV"].sum().reset_index()

        # GMV per customer and product
        customers_products_gmv = supplier_data.groupby(["Restaurant_name", "product_name"])["GMV"].sum().reset_index()

        # Display customer GMV table
        st.subheader(f"Customers of {selected_supplier} & GMV")
        st.dataframe(customers_gmv.sort_values(by="GMV", ascending=False))

        # Display customers & products GMV table
        st.subheader(f"Customers, Products & GMV for {selected_supplier}")
        st.dataframe(customers_products_gmv.sort_values(by="GMV", ascending=False))


    st.subheader("View by Account Manager")
        # -------------------- REGION FILTER --------------------    
    # Get unique regions and add an 'All' option
    regions = df["region"].unique().tolist()
    regions.insert(0, "All Regions")

    # Region selection dropdown
    selected_region = st.selectbox("Select a Region", regions, key="account_manager_region_select")

    # Filter data by region if one is selected
    if selected_region == "All Regions":
        filtered_df = df
    else:
        filtered_df = df[df["region"] == selected_region]

    # Get unique account managers based on region filter
    account_managers = filtered_df["Account_email"].unique()
    selected_account_manager = st.selectbox("Select an Account Manager", account_managers, key="account_manager_select")

    if selected_account_manager:
        # Filter data for the selected account manager
        account_manager_data = filtered_df[filtered_df["Account_email"] == selected_account_manager]

        if not account_manager_data.empty:
            # Total GMV
            total_gmv = account_manager_data["GMV"].sum()

            # Total number of unique customers
            unique_customers_count = account_manager_data["Restaurant_name"].nunique()

            # Regions covered by the account manager
            regions_covered = account_manager_data["region"].unique().tolist()

            # GMV per customer
            customer_gmv = account_manager_data.groupby("Restaurant_name")["GMV"].sum().reset_index().sort_values(by="GMV", ascending=False)

            # GMV per product
            product_gmv = account_manager_data.groupby("product_name")["GMV"].sum().reset_index().sort_values(by="GMV", ascending=False)

            # Display stats
            st.write(f"**Total GMV:** €{total_gmv:,.2f}")
            st.write(f"**Total Unique Customers:** {unique_customers_count}")
            st.write(f"**Regions Covered:** {', '.join(regions_covered)}")

            # Display customer GMV table
            st.subheader("Customers & GMV")
            st.dataframe(customer_gmv)

            # Display product GMV table
            st.subheader("Products Sold & GMV")
            st.dataframe(product_gmv)
        else:
            st.warning(f"No data found for account manager: {selected_account_manager}")

    # Extract week number for grouping
    df['Week Number'] = df['Date'].dt.isocalendar().week

    # -------------------- WEEKLY GMV BY ACCOUNT MANAGER --------------------
    st.subheader("Weekly GMV by Account Manager")

    # Group data by week and account manager
    weekly_gmv = (
        df.groupby(["Week Number", "Account_email"])["GMV"]
        .sum()
        .reset_index()
        .rename(columns={"Account_email": "Account Manager"})
    )

    # Pivot table for account manager GMV
    weekly_gmv_pivot = weekly_gmv.pivot_table(
        index="Account Manager",
        columns="Week Number",
        values="GMV",
        fill_value=0
    )

    # Display the weekly GMV for all account managers
    st.dataframe(weekly_gmv_pivot)

    # -------------------- ACCOUNT MANAGER FILTER --------------------
    st.subheader("Choose an Account Manager")

    # Get unique account managers
    account_managers = df["Account_email"].unique().tolist()
    selected_manager = st.selectbox("Select an Account Manager", ["All Managers"] + account_managers)

    # -------------------- WEEKLY ORDERS BY CUSTOMERS FOR SELECTED MANAGER --------------------
    if selected_manager != "All Managers":
        st.subheader(f"Weekly Orders for {selected_manager}")

        # Filter data for the selected account manager
        manager_data = df[df["Account_email"] == selected_manager]

        # Group data by week and customer
        weekly_orders = (
            manager_data.groupby(["Week Number", "Restaurant_name"])["GMV"]
            .sum()
            .reset_index()
        )

        # Pivot table for weekly customer orders
        weekly_orders_pivot = weekly_orders.pivot_table(
            index="Restaurant_name",
            columns="Week Number",
            values="GMV",
            fill_value=0
        )

        # Display the weekly orders for the customers of the selected manager
        st.dataframe(weekly_orders_pivot)





































st.title("Weekly Analysis")

# File uploader for two weeks
uploaded_file_Last_Week = st.file_uploader("Last Week", type="xlsx")
uploaded_file_This_Week = st.file_uploader("This Week", type="xlsx")


if uploaded_file_Last_Week and uploaded_file_This_Week:
    df_Last_Week = pd.read_excel(uploaded_file_Last_Week)
    df_This_Week = pd.read_excel(uploaded_file_This_Week)
    
    # Round GMV column in both datasets to whole numbers (euros)
    df_Last_Week["GMV"] = df_Last_Week["GMV"].round(0).astype(int)
    df_This_Week["GMV"] = df_This_Week["GMV"].round(0).astype(int)

    # Sidebar Section Selection
    st.sidebar.header("Select Analysis Sections")
    sections = st.sidebar.multiselect(
        "Choose Analysis Sections", 
        ["Analysis","Pricing","Customers"]
    )


    if "Analysis" in sections:
        analysis(df_Last_Week, df_This_Week)
        

    if "Pricing" in sections:
        pricing(df_Last_Week, df_This_Week)
    
    
    if "Customers" in sections:
        Customers(df_Last_Week, df_This_Week)

else:
    st.warning("Please upload data files for both weeks.")
