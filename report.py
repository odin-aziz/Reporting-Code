import streamlit as st
import pandas as pd
from datetime import datetime

# --- Helper Functions ---

def calculate_GMV(df, group_by_columns, sum_column='GMV'):
    """Calculates GMV by grouping specified columns."""
    try:
        if sum_column not in df.columns:
            raise KeyError(f"Missing column for GMV calculation: {sum_column}")
        
        gmv = df.groupby(group_by_columns)[sum_column].sum().reset_index()
        gmv = gmv.rename(columns={sum_column: 'Total GMV (€)'})
        gmv['Total GMV (€)'] = gmv['Total GMV (€)'].round(0).astype(int)
        gmv = gmv.sort_values(by='Total GMV (€)', ascending=False)
        return gmv
    except KeyError as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

def compare_metrics(df_week1, df_week2, group_by_columns, sum_column='GMV'):
    """Compares metrics between two weeks and calculates growth and difference."""
    # Calculate GMV for both weeks
    gmv_week1 = calculate_GMV(df_week1, group_by_columns, sum_column)
    gmv_week2 = calculate_GMV(df_week2, group_by_columns, sum_column)
    
    # Merge the two dataframes on the group_by_columns
    comparison = pd.merge(gmv_week1, gmv_week2, on=group_by_columns, suffixes=('_Week1', '_Week2'))
    
    # Calculate Growth Percentage and Difference
    comparison['Growth (%)'] = ((comparison['Total GMV (€)_Week2'] - comparison['Total GMV (€)_Week1']) /
                                comparison['Total GMV (€)_Week1']) * 100
    comparison['Difference (€)'] = comparison['Total GMV (€)_Week2'] - comparison['Total GMV (€)_Week1']
    
    # Round and format for display
    comparison['Growth (%)'] = comparison['Growth (%)'].round(1)
    comparison['Difference (€)'] = comparison['Difference (€)'].round(0).astype(int)
    
    return comparison

def get_region_hierarchy(df):
    """Organizes the data into hierarchical GMV tables by region, subcategory, supplier, and restaurant."""
    regions = df['region'].unique()
    region_data = {}
    
    for region in regions:
        region_df = df[df['region'] == region]
        
        # Overall GMV for the region
        total_gmv = region_df['GMV'].sum() if 'GMV' in region_df.columns else 0
        
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

st.title("Weekly Purchasing Dashboard")

# File uploader for two weeks
uploaded_file_week1 = st.file_uploader("Upload Week 1 Data (e.g., W44)", type="xlsx")
uploaded_file_week2 = st.file_uploader("Upload Week 2 Data (e.g., W45)", type="xlsx")

if uploaded_file_week1 and uploaded_file_week2:
    df_week1 = pd.read_excel(uploaded_file_week1)
    df_week2 = pd.read_excel(uploaded_file_week2)

    # --- Section 1: Dashboard Overview in Sidebar ---
    tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Region-Based Analysis", "Supplier GMV", "Subcategory GMV"])

    # --- Tab 1: High-Level Summary Dashboard ---
    with tab1:
        st.subheader("High-Level Summary")
        
        # Total GMV for both weeks
        gmvs_week1 = df_week1['GMV'].sum() if 'GMV' in df_week1.columns else 0
        gmvs_week2 = df_week2['GMV'].sum() if 'GMV' in df_week2.columns else 0
        st.metric("Total GMV Week 1 (€)", f"{gmvs_week1:,.0f} €")
        st.metric("Total GMV Week 2 (€)", f"{gmvs_week2:,.0f} €")
        
        # GMV comparison for the dashboard
        comparison = compare_metrics(df_week1, df_week2, ['region'])
        st.write("### GMV Comparison by Region")
        st.write(comparison)

        # Region-based GMV comparison directly in the dashboard
        st.write("### GMV Comparison by Region")
        region_hierarchy_data_week1 = get_region_hierarchy(df_week1)
        region_hierarchy_data_week2 = get_region_hierarchy(df_week2)
        
        for region in region_hierarchy_data_week1:
            st.write(f"#### {region}")
            st.write(f"**Week 1 GMV:** {region_hierarchy_data_week1[region]['Total GMV']} | **Week 2 GMV:** {region_hierarchy_data_week2[region]['Total GMV']}")
            
            # Compare Subcategory GMVs
            st.write("#### Subcategory GMV Comparison")
            st.write(compare_metrics(region_hierarchy_data_week1[region]['Subcategory GMV'], 
                                     region_hierarchy_data_week2[region]['Subcategory GMV'], ['sub_cat']))

            # Compare Supplier GMVs
            st.write("#### Supplier GMV Comparison")
            st.write(compare_metrics(region_hierarchy_data_week1[region]['Supplier GMV'], 
                                     region_hierarchy_data_week2[region]['Supplier GMV'], ['Supplier']))

            # Compare Restaurant GMVs
            st.write("#### Restaurant GMV Comparison")
            st.write(compare_metrics(region_hierarchy_data_week1[region]['Restaurant GMV'], 
                                     region_hierarchy_data_week2[region]['Restaurant GMV'], ['Restaurant_name']))

    # --- Tab 2: Region-Based Analysis ---
    with tab2:
        st.subheader("Detailed GMV Analysis by Region")
        region_hierarchy_data_week1 = get_region_hierarchy(df_week1)
        region_hierarchy_data_week2 = get_region_hierarchy(df_week2)
        
        # Display GMV data comparison for each region
        for region in region_hierarchy_data_week1:
            st.write(f"### {region} - GMV Week 1: {region_hierarchy_data_week1[region]['Total GMV']} | GMV Week 2: {region_hierarchy_data_week2[region]['Total GMV']}")
            st.write("#### Subcategory GMV Comparison")
            st.write(compare_metrics(region_hierarchy_data_week1[region]['Subcategory GMV'], 
                                     region_hierarchy_data_week2[region]['Subcategory GMV'], ['sub_cat']))
            st.write("#### Supplier GMV Comparison")
            st.write(compare_metrics(region_hierarchy_data_week1[region]['Supplier GMV'], 
                                     region_hierarchy_data_week2[region]['Supplier GMV'], ['Supplier']))
            st.write("#### Restaurant GMV Comparison")
            st.write(compare_metrics(region_hierarchy_data_week1[region]['Restaurant GMV'], 
                                     region_hierarchy_data_week2[region]['Restaurant GMV'], ['Restaurant_name']))

    # --- Tab 3: Supplier GMV Analysis ---
    with tab3:
        st.subheader("Supplier GMV Analysis")
        supplier_gmv_week1 = calculate_GMV(df_week1, ['Supplier'])
        supplier_gmv_week2 = calculate_GMV(df_week2, ['Supplier'])
        comparison_supplier = compare_metrics(supplier_gmv_week1, supplier_gmv_week2, ['Supplier'])
        st.write(comparison_supplier)

    # --- Tab 4: Subcategory GMV Analysis ---
    with tab4:
        st.subheader("Subcategory GMV Analysis")
        subcategory_gmv_week1 = calculate_GMV(df_week1, ['sub_cat'])
        subcategory_gmv_week2 = calculate_GMV(df_week2, ['sub_cat'])
        comparison_subcategory = compare_metrics(subcategory_gmv_week1, subcategory_gmv_week2, ['sub_cat'])
        st.write(comparison_subcategory)

    # Download Report Button in Sidebar
    if st.sidebar.button("Download Report"):
        output_file = f"summary_comparison_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        with pd.ExcelWriter(output_file) as writer:
            comparison.to_excel(writer, sheet_name="GMV Comparison by Region")
            region_hierarchy_data_week1.to_excel(writer, sheet_name="Region Data Week 1")
            region_hierarchy_data_week2.to_excel(writer, sheet_name="Region Data Week 2")
        st.download_button("Download Report", output_file, file_name=output_file, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

else:
    st.warning("Please upload both week files.")
