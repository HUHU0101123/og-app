import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Cargar los archivos CSV desde GitHub
url_main = "https://raw.githubusercontent.com/HUHU0101123/og-app/main/datasource.csv"
url_categorias = "https://raw.githubusercontent.com/HUHU0101123/og-app/main/categorias.csv"

df_main = pd.read_csv(url_main)
df_categorias = pd.read_csv(url_categorias)

# Preprocesamiento de datos
def preprocess_data(df_main, df_categorias):
    # Rellenar valores faltantes para detalles de productos y fusionar con categorías
    df_main = df_main.fillna('')
    df_main['Fecha'] = pd.to_datetime(df_main['Fecha']).dt.date
    
    # Fusionar con categorías
    df = df_main.merge(df_categorias, on='SKU del Producto', how='left')
    
    # Calcular la cantidad total por ID y clasificar como Mayorista o Detalle
    total_quantity_per_id = df.groupby('ID')['Cantidad de Productos'].sum()
    df['Tipo de Venta'] = df['ID'].map(lambda x: 'Mayorista' if total_quantity_per_id[x] >= 6 else 'Detalle')
    
    # Convertir 'Precio del Producto' de string a float
    df['Precio del Producto'] = df['Precio del Producto'].str.replace(',', '.').astype(float)
    
    # Calcular ventas totales por ID
    df['Total de Venta'] = df.groupby('ID')['Precio del Producto'].transform('sum')
    
    # Verificar si el método de envío específico está presente
    if 'Despacho Santiago (RM) a domicilio' in df['Nombre del método de envío'].unique():
        # Ajustar ventas totales según el método de envío
        df['Total Ajustado'] = df.apply(
            lambda row: row['Total de Venta'] - 2990 if row['Nombre del método de envío'] == 'Despacho Santiago (RM) a domicilio' else row['Total de Venta'],
            axis=1
        )
    else:
        # Si el método de envío no está presente, no ajustar las ventas
        df['Total Ajustado'] = df['Total de Venta']
    
    return df

df = preprocess_data(df_main, df_categorias)

# Aplicación de Streamlit
st.title("Sales Dashboard")

# Selector de fechas
dates = pd.to_datetime(df['Fecha']).sort_values().unique()
selected_date = st.sidebar.selectbox('Select Date', dates)

# Filtrar datos según la fecha seleccionada
filtered_data = df[df['Fecha'] == selected_date]

# Ventas por región
sales_by_region = filtered_data.groupby('Región de Envío')['Total Ajustado'].sum().reset_index()

# Ventas por categoría de producto
sales_by_category = filtered_data.groupby('Categoria')['Total Ajustado'].sum().reset_index()

# Ventas totales
total_sales = filtered_data['Total Ajustado'].sum()

# Mostrar ventas totales
st.subheader(f"Total Sales for {selected_date}")
st.write(f"${total_sales:,.2f}")

# Gráfico de ventas por región
st.subheader("Sales by Region")
st.bar_chart(sales_by_region.set_index('Región de Envío'))

# Gráfico de ventas por categoría
st.subheader("Sales by Product Category")
st.bar_chart(sales_by_category.set_index('Categoria'))

# Opcional: Mostrar datos en bruto
if st.checkbox('Show Raw Data'):
    st.subheader("Raw Data")
    st.write(filtered_data)
