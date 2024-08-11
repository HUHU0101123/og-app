import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Load the CSV files
url_main = "https://raw.githubusercontent.com/HUHU0101123/og-app/main/datasource.csv"
url_categorias = "https://raw.githubusercontent.com/HUHU0101123/og-app/main/categorias.csv"

df_main = pd.read_csv(url_main)
df_categorias = pd.read_csv(url_categorias)

# Data Preprocessing
def preprocess_data(df_main, df_categorias):
    # Fill missing values and handle date conversion
    df_main = df_main.fillna('')
    df_main['Fecha'] = pd.to_datetime(df_main['Fecha'], errors='coerce').dt.date

    # Merge with categories
    df = df_main.merge(df_categorias, on='SKU del Producto', how='left')
    
    # Convert 'Precio del Producto' from string to float
    df['Precio del Producto'] = df['Precio del Producto'].str.replace(',', '.').astype(float)
    
    # Calculate total sales for each row
    df['Total de Venta'] = df['Cantidad de Productos'].astype(float) * df['Precio del Producto']
    
    # Aggregate data by order ID
    aggregated = df.groupby('ID').agg(
        Fecha=('Fecha', 'first'),
        Total_Venta=('Total de Venta', 'sum'),
        Tipo_de_Venta=('Cantidad de Productos', lambda x: 'Mayorista' if x.sum() >= 6 else 'Detalle'),
        Region=('Región de Envío', 'first'),
        Categoria=('Categoria', 'first'),
        Metodo_de_Envio=('Nombre del método de envío', 'first'),
        Cupones=('Cupones', 'first')
    ).reset_index()
    
    # Adjust total sales based on shipping method
    aggregated['Total_Ajustado'] = aggregated.apply(
        lambda row: row['Total_Venta'] - 2990 if row['Metodo_de_Envio'] == 'Despacho Santiago (RM) a domicilio' else row['Total_Venta'],
        axis=1
    )
    
    return aggregated

df = preprocess_data(df_main, df_categorias)

# Streamlit App
st.title("Sales Dashboard")

# Date Selector
dates = df['Fecha'].dropna().unique()
dates.sort()
selected_date = st.sidebar.selectbox('Select Date', dates)

# Filter data based on selected date
filtered_data = df[df['Fecha'] == selected_date]

# Check if there's any data for the selected date
if not filtered_data.empty:
    st.write("Filtered Data Columns:", filtered_data.columns.tolist())
    st.write("Filtered Data Preview:", filtered_data.head())

    # Sales by Region
    if 'Region' in filtered_data.columns and 'Total_Ajustado' in filtered_data.columns:
        sales_by_region = filtered_data.groupby('Region')['Total_Ajustado'].sum().reset_index()
        st.subheader("Sales by Region")
        st.bar_chart(sales_by_region.set_index('Region'))
    else:
        st.write("Columns for 'Region' or 'Total_Ajustado' are missing in the filtered data.")

    # Sales by Product Category
    if 'Categoria' in filtered_data.columns and 'Total_Ajustado' in filtered_data.columns:
        sales_by_category = filtered_data.groupby('Categoria')['Total_Ajustado'].sum().reset_index()
        st.subheader("Sales by Product Category")
        st.bar_chart(sales_by_category.set_index('Categoria'))
    else:
        st.write("Columns for 'Categoria' or 'Total_Ajustado' are missing in the filtered data.")

    # Total Sales
    total_sales = filtered_data['Total_Ajustado'].sum()
    st.subheader(f"Total Sales for {selected_date}")
    st.write(f"${total_sales:,.2f}")

    # Optional: Display raw data
    if st.checkbox('Show Raw Data'):
        st.subheader("Raw Data")
        st.write(filtered_data)
else:
    st.write("No data available for the selected date.")
