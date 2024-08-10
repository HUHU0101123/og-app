import streamlit as st
import pandas as pd
import plotly.express as px

# Load the CSV file from GitHub
url = "https://raw.githubusercontent.com/HUHU0101123/og-app/main/datasource.csv"  # Change this to your actual file URL
df = pd.read_csv(url)

# Strip any extra whitespace from column names
df.columns = df.columns.str.strip()

# Display the raw data with an expander
with st.expander('Data'):
    st.write('**Raw data**')
    st.dataframe(df)

# Título del dashboard
st.title('Análisis de Ventas por Producto')

# Convertir la columna 'Fecha' a datetime si no lo está ya
df['Fecha'] = pd.to_datetime(df['Fecha'])

# Agrupar por SKU y Nombre del Producto
ventas_por_producto = df.groupby(['SKU del Producto', 'Nombre del Producto']).agg({
    'Cantidad de Productos': 'sum',
    'Total': 'sum',
    'Ganancia': 'sum'
}).reset_index()

# Calcular el precio promedio por producto
ventas_por_producto['Precio Promedio'] = ventas_por_producto['Total'] / ventas_por_producto['Cantidad de Productos']

# Ordenar por Total de ventas descendente
ventas_por_producto = ventas_por_producto.sort_values('Total', ascending=False)

# Mostrar tabla de ventas por producto
st.subheader('Tabla de Ventas por Producto')
st.dataframe(ventas_por_producto)

# Gráfico de barras de ventas totales por producto
st.subheader('Ventas Totales por Producto')
fig_ventas = px.bar(ventas_por_producto, x='Nombre del Producto', y='Total', 
                    text='Total', color='SKU del Producto')
fig_ventas.update_traces(texttemplate='%{text:.2s}', textposition='outside')
fig_ventas.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
st.plotly_chart(fig_ventas)

# Gráfico de dispersión de Cantidad vs Ganancia
st.subheader('Cantidad vs Ganancia por Producto')
fig_scatter = px.scatter(ventas_por_producto, x='Cantidad de Productos', y='Ganancia', 
                         size='Total', color='SKU del Producto', hover_name='Nombre del Producto', 
                         log_x=True, size_max=60)
st.plotly_chart(fig_scatter)

# Análisis de tendencias de ventas en el tiempo
ventas_diarias = df.groupby('Fecha').agg({
    'Total': 'sum',
    'Cantidad de Productos': 'sum'
}).reset_index()

st.subheader('Tendencia de Ventas en el Tiempo')
fig_trend = px.line(ventas_diarias, x='Fecha', y='Total', title='Ventas Diarias')
st.plotly_chart(fig_trend)

# Filtro para análisis detallado por producto
st.subheader('Análisis Detallado por Producto')
producto_seleccionado = st.selectbox('Selecciona un producto:', df['Nombre del Producto'].unique())

producto_df = df[df['Nombre del Producto'] == producto_seleccionado]

col1, col2, col3 = st.columns(3)
col1.metric("Total Vendido", f"{producto_df['Total'].sum():,.0f}")
col2.metric("Cantidad Vendida", f"{producto_df['Cantidad de Productos'].sum():,.0f}")
col3.metric("Ganancia Total", f"{producto_df['Ganancia'].sum():,.0f}")

# Gráfico de ventas del producto seleccionado en el tiempo
fig_producto = px.line(producto_df, x='Fecha', y='Total', title=f'Ventas de {producto_seleccionado} en el Tiempo')
st.plotly_chart(fig_producto)
