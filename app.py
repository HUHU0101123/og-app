import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Load the CSV file from GitHub
url = "https://raw.githubusercontent.com/HUHU0101123/og-app/main/datasource.csv"  # Change this to your actual file URL
df = pd.read_csv(url)

# Strip any extra whitespace from column names
df.columns = df.columns.str.strip()

# Convert the 'Fecha' column to datetime
df['Fecha'] = pd.to_datetime(df['Fecha'])

# Display the raw data with an expander
with st.expander('Raw Data'):
    st.write(df)

# Dashboard Title
st.title('Sales Analysis Dashboard')

# Group by SKU and Product Name
ventas_por_producto = df.groupby(['SKU del Producto', 'Nombre del Producto']).agg({
    'Cantidad de Productos': 'sum',
    'Total': 'sum',
    'Ganancia': 'sum'
}).reset_index()

# Calculate the average price per product
ventas_por_producto['Precio Promedio'] = ventas_por_producto['Total'] / ventas_por_producto['Cantidad de Productos']

# Sort by Total Sales in descending order
ventas_por_producto = ventas_por_producto.sort_values('Total', ascending=False)

# Display the sales table
st.subheader('Sales Overview by Product')
st.dataframe(ventas_por_producto)

# Plot: Total Sales by Product
st.subheader('Total Sales by Product')
fig_ventas = px.bar(ventas_por_producto, x='Nombre del Producto', y='Total',
                    text='Total', color='SKU del Producto',
                    title='Total Sales by Product')
fig_ventas.update_traces(texttemplate='%{text:.2s}', textposition='outside')
fig_ventas.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
st.plotly_chart(fig_ventas)

# Plot: Quantity vs Profit by Product
st.subheader('Quantity vs Profit by Product')
fig_scatter = px.scatter(ventas_por_producto, x='Cantidad de Productos', y='Ganancia',
                         size='Total', color='SKU del Producto',
                         hover_name='Nombre del Producto', log_x=True, size_max=60,
                         title='Quantity vs Profit by Product')
st.plotly_chart(fig_scatter)

# Trend Analysis: Daily Sales
ventas_diarias = df.groupby('Fecha').agg({
    'Total': 'sum',
    'Cantidad de Productos': 'sum'
}).reset_index()

st.subheader('Sales Trend Over Time')
fig_trend = px.line(ventas_diarias, x='Fecha', y='Total', 
                    title='Daily Sales Trend')
st.plotly_chart(fig_trend)

# Detailed Analysis by Product
st.subheader('Detailed Analysis by Product')
producto_seleccionado = st.selectbox('Select a Product:', df['Nombre del Producto'].unique())

producto_df = df[df['Nombre del Producto'] == producto_seleccionado]

col1, col2, col3 = st.columns(3)
col1.metric("Total Sold", f"{producto_df['Total'].sum():,.0f} CLP")
col2.metric("Quantity Sold", f"{producto_df['Cantidad de Productos'].sum():,.0f}")
col3.metric("Total Profit", f"{producto_df['Ganancia'].sum():,.0f} CLP")

# Plot: Sales of Selected Product Over Time
fig_producto = px.line(producto_df, x='Fecha', y='Total', 
                      title=f'Sales of {producto_seleccionado} Over Time')
st.plotly_chart(fig_producto)

# Gráfico de ventas del producto seleccionado en el tiempo
fig_producto = px.line(producto_df, x='Fecha', y='Total', title=f'Ventas de {producto_seleccionado} en el Tiempo')
st.plotly_chart(fig_producto)
