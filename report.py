import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# --- Data Processing Functions ---
def calculate_GMV(df, group_by_columns, sum_column='GMV'):
    """General function to calculate GMV per group."""
    try:
        gmv = df.groupby(group_by_columns)[sum_column].sum().reset_index()
        gmv = gmv.rename(columns={sum_column: 'Total GMV'})
        gmv['Total GMV'] = gmv['Total GMV'].round(0).astype(int)
        gmv = gmv.sort_values(by='Total GMV', ascending=False)
        return gmv
    except KeyError as e:
        print(f"Missing column for GMV calculation: {e}")
        return pd.DataFrame()

# --- Charting Functions ---
def plot_bar_chart(data, x_col, y_col, title, xlabel, ylabel):
    """General bar plot function."""
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=x_col, y=y_col, data=data, ax=ax, palette="viridis")
    plt.xticks(rotation=90)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    st.pyplot(fig)

def plot_pie_chart(data, column, title):
    """Pie chart for categorical breakdown."""
    fig, ax = plt.subplots(figsize=(6, 6))
    data[column].value_counts().plot.pie(autopct='%1.1f%%', startangle=90, ax=ax, colors=sns.color_palette("Set2"))
    ax.set_title(title)
    st.pyplot(fig)

# --- Streamlit Main App ---
st.title("Weekly Dashboard")
st.write("Upload your dataset")

# File uploader
uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Option to calculate and view each metric
    st.sidebar.header("Choose Analysis to Display")

    # Supplier GMV
    if st.sidebar.checkbox("Supplier GMV"):
        st.subheader("Supplier GMV")
        supplier_GMV = calculate_GMV(df, ['Supplier'])
        st.write(supplier_GMV)
        plot_bar_chart(supplier_GMV, 'Supplier', 'Total GMV', 'Supplier GMV', 'Supplier', 'Total GMV')

    # Subcategory GMV
    if st.sidebar.checkbox("Subcategory GMV"):
        st.subheader("Subcategory GMV")
        subcategory_GMV = calculate_GMV(df, ['sub_cat'])
        st.write(subcategory_GMV)
        plot_bar_chart(subcategory_GMV, 'sub_cat', 'Total GMV', 'Subcategory GMV', 'Subcategory', 'Total GMV')

    # Region GMV
    if st.sidebar.checkbox("Region GMV"):
        st.subheader("Region GMV")
        region_GMV = calculate_GMV(df, ['region'])
        st.write(region_GMV)
        plot_bar_chart(region_GMV, 'region', 'Total GMV', 'Region GMV', 'Region', 'Total GMV')

    # Restaurant GMV
    if st.sidebar.checkbox("Restaurant GMV"):
        st.subheader("Restaurant GMV")
        restaurant_GMV = calculate_GMV(df, ['Restaurant_name'])
        st.write(restaurant_GMV)
        plot_bar_chart(restaurant_GMV, 'Restaurant_name', 'Total GMV', 'Restaurant GMV', 'Restaurant', 'Total GMV')

    # Supplier Region Contribution
    if st.sidebar.checkbox("Supplier Region Contribution"):
        st.subheader("Supplier Region Contribution")
        supplier_region_contribution = calculate_GMV(df, ['region', 'Supplier'])
        supplier_region_contribution['Contribution (%)'] = (supplier_region_contribution['Total GMV'] / supplier_region_contribution.groupby('region')['Total GMV'].transform('sum') * 100)
        st.write(supplier_region_contribution)
        plot_bar_chart(supplier_region_contribution, 'Supplier', 'Contribution (%)', 'Supplier Region Contribution', 'Supplier', 'Contribution (%)')

    # Download report button
    if st.sidebar.button("Download Report"):
        output_file = f"summary_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        with pd.ExcelWriter(output_file) as writer:
            supplier_GMV.to_excel(writer, sheet_name='Supplier_GMV', index=False)
            subcategory_GMV.to_excel(writer, sheet_name='Subcategory_GMV', index=False)
            region_GMV.to_excel(writer, sheet_name='Region_GMV', index=False)
            restaurant_GMV.to_excel(writer, sheet_name='Restaurant_GMV', index=False)
            supplier_region_contribution.to_excel(writer, sheet_name='Supplier_Region_Contribution', index=False)

        with open(output_file, "rb") as file:
            st.download_button(
                label="Download Excel Report",
                data=file,
                file_name=output_file,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
