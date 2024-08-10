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

# Calculate additional KPIs
ventas_por_producto['Precio Promedio'] = ventas_por_producto['Total'] / ventas_por_producto['Cantidad de Productos']
ventas_por_producto['Rentabilidad (%)'] = (ventas_por_producto['Ganancia'] / ventas_por_producto['Total']) * 100

# Sort by Total Sales in descending order
ventas_por_producto = ventas_por_producto.sort_values('Total', ascending=False)

# Display the sales table
st.subheader('Sales Overview by Product')
st.dataframe(ventas_por_producto)

# 1. KPI Cards
st.subheader('Key Performance Indicators (KPIs)')
col1, col2, col3 = st.columns(3)
col1.metric("Total Revenue", f"{df['Total'].sum():,.0f} CLP")
col2.metric("Total Quantity Sold", f"{df['Cantidad de Productos'].sum():,.0f}")
col3.metric("Total Profit", f"{df['Ganancia'].sum():,.0f} CLP")

# 2. Pie Chart: Sales Distribution by Product
st.subheader('Sales Distribution by Product')
fig_pie = px.pie(ventas_por_producto, names='Nombre del Producto', values='Total', 
                 title='Sales Distribution by Product')
st.plotly_chart(fig_pie)

# 3. Heatmap: Sales and Profit by Month
st.subheader('Monthly Sales and Profit Heatmap')
# Aggregating data by month
ventas_mensuales = df.resample('M', on='Fecha').agg({'Total': 'sum', 'Ganancia': 'sum'}).reset_index()
ventas_mensuales['Month'] = ventas_mensuales['Fecha'].dt.to_period('M').astype(str)

# Creating the heatmap using a matrix of months vs. sales/profit
fig_heatmap = go.Figure()

fig_heatmap.add_trace(go.Heatmap(
    z=ventas_mensuales[['Total', 'Ganancia']].values.T,
    x=ventas_mensuales['Month'],
    y=['Total', 'Ganancia'],
    colorscale='Viridis',
    colorbar=dict(title='Value')
))

fig_heatmap.update_layout(title='Monthly Sales and Profit Heatmap', xaxis_title='Month', yaxis_title='Metric')
st.plotly_chart(fig_heatmap)

# 4. Line Chart: Profit Margin Over Time
st.subheader('Profit Margin Over Time')
ventas_diarias = df.groupby('Fecha').agg({'Total': 'sum', 'Ganancia': 'sum'}).reset_index()
ventas_diarias['Margen (%)'] = (ventas_diarias['Ganancia'] / ventas_diarias['Total']) * 100
fig_margin = px.line(ventas_diarias, x='Fecha', y='Margen (%)', 
                     title='Profit Margin Over Time')
st.plotly_chart(fig_margin)

# 5. Scatter Plot: Average Price vs Profit Margin by Product
st.subheader('Average Price vs Profit Margin by Product')
fig_scatter_avg_price = px.scatter(ventas_por_producto, x='Precio Promedio', y='Rentabilidad (%)',
                                   size='Total', color='Nombre del Producto',
                                   hover_name='Nombre del Producto',
                                   title='Average Price vs Profit Margin by Product')
st.plotly_chart(fig_scatter_avg_price)

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
# Plot: Sales of Selected Product Over Time
fig_producto = px.line(producto_df, x='Fecha', y='Total', 
                      title=f'Sales of {producto_seleccionado} Over Time')
st.plotly_chart(fig_producto)
