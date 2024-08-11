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
    # Fill missing values for product details and merge with categories
    df_main = df_main.fillna('')
    df_main['Fecha'] = pd.to_datetime(df_main['Fecha']).dt.date
    
    # Merge with categories
    df = df_main.merge(df_categorias, on='SKU del Producto', how='left')
    
    # Calculate total quantity per ID and categorize as Mayorista or Detalle
    total_quantity_per_id = df.groupby('ID')['Cantidad de Productos'].sum()
    df['Tipo de Venta'] = df['ID'].map(lambda x: 'Mayorista' if total_quantity_per_id[x] >= 6 else 'Detalle')
    
    # Calculate total sales
    df['Precio del Producto'] = df['Precio del Producto'].str.replace(',', '.').astype(float)
    df['Total de Venta'] = df.groupby('ID')['Precio del Producto'].transform('sum')
    
    # Adjust total sales based on shipping method
    df['Total Ajustado'] = np.where(df['Nombre del método de envío'] == 'Despacho Santiago (RM) a domicilio', df['Total de Venta'] - 2990, df['Total de Venta'])
    
    return df

df = preprocess_data(df_main, df_categorias)

# Streamlit App
st.title("Sales Dashboard")

# Date Selector
dates = pd.to_datetime(df['Fecha']).sort_values().unique()
selected_date = st.sidebar.selectbox('Select Date', dates)

# Filter data based on selected date
filtered_data = df[df['Fecha'] == selected_date]

# Sales by Region
sales_by_region = filtered_data.groupby('Región de Envío')['Total Ajustado'].sum().reset_index()

# Sales by Product Category
sales_by_category = filtered_data.groupby('Categoria')['Total Ajustado'].sum().reset_index()

# Total Sales
total_sales = filtered_data['Total Ajustado'].sum()

# Display Total Sales
st.subheader(f"Total Sales for {selected_date}")
st.write(f"${total_sales:,.2f}")

# Sales by Region Chart
st.subheader("Sales by Region")
st.bar_chart(sales_by_region.set_index('Región de Envío'))

# Sales by Category Chart
st.subheader("Sales by Product Category")
st.bar_chart(sales_by_category.set_index('Categoria'))

# Optional: Display raw data
if st.checkbox('Show Raw Data'):
    st.subheader("Raw Data")
    st.write(filtered_data)
