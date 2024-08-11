import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Cargar los archivos CSV desde GitHub
@st.cache_data
def load_data():
    url_main = "https://raw.githubusercontent.com/HUHU0101123/og-app/main/datasource.csv"
    df_main = pd.read_csv(url_main)
    url_categorias = "https://raw.githubusercontent.com/HUHU0101123/og-app/main/categorias.csv"
    df_categorias = pd.read_csv(url_categorias)
    return df_main, df_categorias

df_main, df_categorias = load_data()

def preprocess_data(df_main, df_categorias):
    # Convertir la columna 'Fecha' a datetime
    df_main['Fecha'] = pd.to_datetime(df_main['Fecha']).dt.date
    
    # Unir los dataframes para agregar las categorías
    df = pd.merge(df_main, df_categorias, on='SKU del Producto', how='left')
    
    # Llenar los valores NaN en las columnas relevantes
    columns_to_fill = ['Estado del Pago', 'Fecha', 'Moneda', 'Región de Envío', 'Nombre del método de envío', 'Cupones']
    df[columns_to_fill] = df.groupby('ID')[columns_to_fill].fillna(method='ffill')
    
    # Convertir columnas numéricas
    numeric_columns = ['Cantidad de Productos', 'Precio del Producto', 'Rentabilidad del producto', 'Margen del producto (%)', 'Descuento del producto']
    for col in numeric_columns:
        if df[col].dtype == 'object':
            df[col] = df[col].str.replace(',', '.').astype(float)
        else:
            df[col] = df[col].astype(float)
    
    # Calcular el total de productos por compra
    df['Total Productos'] = df.groupby('ID')['Cantidad de Productos'].transform('sum')
    
    # Clasificar el tipo de venta
    df['Tipo de Venta'] = df['Total Productos'].apply(lambda x: 'Mayorista' if x >= 6 else 'Detalle')
    
    # Ajustar el precio para envíos a domicilio en Santiago
    mask = df['Nombre del método de envío'] == 'Despacho Santiago (RM) a domicilio'
    df.loc[mask, 'Precio del Producto'] -= 2990 / df.loc[mask].groupby('ID')['Cantidad de Productos'].transform('sum')
    
    return df

df = preprocess_data(df_main, df_categorias)

# Configuración de la página
st.set_page_config(page_title="Dashboard de Ventas", layout="wide")
st.title("Dashboard de Ventas")

# Filtros en la barra lateral
st.sidebar.header("Filtros")
date_range = st.sidebar.date_input("Rango de fechas", [df['Fecha'].min(), df['Fecha'].max()])
categories = st.sidebar.multiselect("Categorías", options=df['Categoria'].unique())
sale_type = st.sidebar.multiselect("Tipo de Venta", options=df['Tipo de Venta'].unique())

# Aplicar filtros
mask = (df['Fecha'] >= date_range[0]) & (df['Fecha'] <= date_range[1])
if categories:
    mask &= df['Categoria'].isin(categories)
if sale_type:
    mask &= df['Tipo de Venta'].isin(sale_type)
filtered_df = df[mask]

# Métricas principales
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Ventas", f"${filtered_df['Precio del Producto'].sum():,.0f}")
col2.metric("Número de Órdenes", filtered_df['ID'].nunique())
col3.metric("Rentabilidad Total", f"${filtered_df['Rentabilidad del producto'].sum():,.0f}")
col4.metric("Margen Promedio", f"{filtered_df['Margen del producto (%)'].mean():.2f}%")

# Gráficos
col1, col2 = st.columns(2)

with col1:
    # Ventas por categoría
    sales_by_category = filtered_df.groupby('Categoria')['Precio del Producto'].sum().sort_values(ascending=False)
    fig = px.bar(sales_by_category, x=sales_by_category.index, y=sales_by_category.values, title="Ventas por Categoría")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Ventas diarias
    daily_sales = filtered_df.groupby('Fecha')['Precio del Producto'].sum().reset_index()
    fig = px.line(daily_sales, x='Fecha', y='Precio del Producto', title="Ventas Diarias")
    st.plotly_chart(fig, use_container_width=True)

# Top productos vendidos
top_products = filtered_df.groupby('SKU del Producto')['Cantidad de Productos'].sum().sort_values(ascending=False).head(10)
fig = px.bar(top_products, x=top_products.index, y=top_products.values, title="Top 10 Productos Más Vendidos")
st.plotly_chart(fig, use_container_width=True)

# Tabla de datos
st.subheader("Datos Detallados")
st.dataframe(filtered_df)
