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

# Dashboard Title
st.title('Dashboard de Análisis de Ventas')

# Interactive Filters
st.sidebar.subheader('Filtros Interactivos')
date_range = st.sidebar.date_input('Selecciona el Rango de Fechas', [df['Fecha'].min().date(), df['Fecha'].max().date()])
date_range = [pd.to_datetime(date) for date in date_range]
filtered_df = df[(df['Fecha'] >= date_range[0]) & (df['Fecha'] <= date_range[1])]

# Summary Metrics
st.subheader('Métricas de Resumen Antes de Impuestos')

# Calculate metrics
total_revenue = filtered_df['Total'].sum()
total_profit = filtered_df['Ganancia'].sum()
total_orders = filtered_df['ID'].nunique()
average_order_value = total_revenue / total_orders if total_orders > 0 else 0
average_profit_per_order = total_profit / total_orders if total_orders > 0 else 0
overall_profit_margin = (total_profit / total_revenue) * 100 if total_revenue > 0 else 0

# Display metrics using Streamlit's built-in functions
col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric(label="Ingresos Totales", value=f"{total_revenue:,.0f} CLP", delta=None)
col2.metric(label="Beneficio Total", value=f"{total_profit:,.0f} CLP", delta=None)
col3.metric(label="Total de Pedidos", value=f"{total_orders:,}", delta=None)
col4.metric(label="Valor Promedio por Pedido", value=f"{average_order_value:,.0f} CLP", delta=None)
col5.metric(label="Beneficio Promedio por Pedido", value=f"{average_profit_per_order:,.0f} CLP", delta=None)
col6.metric(label="Margen de Beneficio Total antes de impuestos", value=f"{overall_profit_margin:.2f} %", delta=None)

# Calculate profit after tax
tax_rate = 0.19
total_profit_after_tax = total_profit * (1 - tax_rate)

# Additional metric for profit after tax
st.subheader('Métricas de Resumen Después de Impuestos y Descuentos')
st.metric("Beneficio Después de Impuestos (19%)", f"{total_profit_after_tax:,.0f} CLP")

# Sales Trends
st.subheader('Tendencias de Ventas')

# Aggregating data for trends
sales_trends = filtered_df.resample('M', on='Fecha').agg({'Total': 'sum', 'Ganancia': 'sum'}).reset_index()
sales_trends['Month'] = sales_trends['Fecha'].dt.to_period('M').astype(str)

# Line chart for Sales and Profit Trends
fig_sales_trends = px.line(sales_trends, x='Month', y=['Total', 'Ganancia'],
                           labels={'value': 'Monto', 'Month': 'Fecha'},
                           title='Tendencias de Ventas y Beneficio a lo Largo del Tiempo',
                           template='plotly_dark')
fig_sales_trends.update_layout(legend_title_text='Métricas')
st.plotly_chart(fig_sales_trends)

# Sales by Year, Month, and Week
st.subheader('Desglose de Ventas por Período')

# Aggregating data by year, month, and week
sales_by_year = filtered_df.resample('Y', on='Fecha').agg({'Total': 'sum', 'ID': 'count'}).reset_index()
sales_by_month = filtered_df.resample('M', on='Fecha').agg({'Total': 'sum', 'ID': 'count'}).reset_index()
sales_by_week = filtered_df.resample('W', on='Fecha').agg({'Total': 'sum', 'ID': 'count'}).reset_index()

# Display total sales and orders for the year
yearly_sales = sales_by_year.tail(1).iloc[0]
st.subheader(f'Ventas del Año {yearly_sales["Fecha"].year}')
col1, col2 = st.columns(2)
col1.metric("Ventas Totales", f"{yearly_sales['Total']:,.0f} CLP")
col2.metric("Total de Pedidos", f"{yearly_sales['ID']:,}")

# Display total sales and orders for the current month
monthly_sales = sales_by_month.tail(1).iloc[0]
st.subheader(f'Ventas del Mes {monthly_sales["Fecha"].strftime("%B %Y")}')
col1, col2 = st.columns(2)
col1.metric("Ventas Totales", f"{monthly_sales['Total']:,.0f} CLP")
col2.metric("Total de Pedidos", f"{monthly_sales['ID']:,}")

# Display total sales and orders for the current week
weekly_sales = sales_by_week.tail(1).iloc[0]
st.subheader(f'Ventas de la Semana del {weekly_sales["Fecha"].strftime("%d %b %Y")}')
col1, col2 = st.columns(2)
col1.metric("Ventas Totales", f"{weekly_sales['Total']:,.0f} CLP")
col2.metric("Total de Pedidos", f"{weekly_sales['ID']:,}")

# Product Performance
st.subheader('Desempeño de Productos')
product_performance = filtered_df.groupby(['Nombre del Producto', 'SKU del Producto']).agg({
    'Cantidad de Productos': 'sum',
    'Total': 'sum',
    'Ganancia': 'sum'
}).reset_index()
product_performance['Precio Promedio'] = product_performance['Total'] / product_performance['Cantidad de Productos']
product_performance['Rentabilidad (%)'] = (product_performance['Ganancia'] / product_performance['Total']) * 100

# Top-Selling Products Bar Chart
fig_top_selling_products = px.bar(product_performance.sort_values('Cantidad de Productos', ascending=False),
                                  x='Nombre del Producto', y='Cantidad de Productos',
                                  title='Productos Más Vendidos',
                                  labels={'Cantidad de Productos': 'Cantidad Vendida'},
                                  template='plotly_dark')
fig_top_selling_products.update_layout(xaxis_title='Nombre del Producto', yaxis_title='Cantidad Vendida')
st.plotly_chart(fig_top_selling_products)

# Product Profitability
fig_product_profitability = px.scatter(product_performance, x='Precio Promedio', y='Rentabilidad (%)',
                                       size='Total', color='Nombre del Producto',
                                       hover_name='Nombre del Producto',
                                       title='Rentabilidad de Productos',
                                       template='plotly_dark')
fig_product_profitability.update_layout(xaxis_title='Precio Promedio', yaxis_title='Rentabilidad (%)')
st.plotly_chart(fig_product_profitability)

# Payment and Discount Analysis
st.subheader('Análisis de Métodos de Pago y Descuentos')
# Payment Methods Breakdown
payment_methods = filtered_df['Nombre de Pago'].value_counts().reset_index()
payment_methods.columns = ['Método de Pago', 'Cantidad']
fig_payment_methods = px.pie(payment_methods, names='Método de Pago', values='Cantidad',
                            title='Desglose de Ventas por Método de Pago',
                            template='plotly_dark')
st.plotly_chart(fig_payment_methods)

# Discounts Applied
discounts = filtered_df.groupby('Cupones').agg({'Subtotal': 'sum', 'Total': 'sum'}).reset_index()
discounts.columns = ['Cupón', 'Subtotal', 'Total']
fig_discounts = px.bar(discounts, x='Cupón', y=['Subtotal', 'Total'],
                      title='Impacto de Descuentos en Ventas',
                      labels={'value': 'Monto', 'Cupón': 'Cupón'},
                      template='plotly_dark')
fig_discounts.update_layout(barmode='group', xaxis_title='Cupón', yaxis_title='Monto')
st.plotly_chart(fig_discounts)

# Shipping Insights
st.subheader('Información sobre Envíos')
# Shipping Methods Distribution
shipping_methods = filtered_df['Nombre del metodo de envio'].value_counts().reset_index()
shipping_methods.columns = ['Método de Envío', 'Cantidad']
fig_shipping_methods = px.pie(shipping_methods, names='Método de Envío', values='Cantidad',
                              title='Distribución de Pedidos por Método de Envío',
                              template='plotly_dark')
st.plotly_chart(fig_shipping_methods)

# Shipping Status
shipping_status = filtered_df['Estado del Envio'].value_counts().reset_index()
shipping_status.columns = ['Estado del Envío', 'Cantidad']
fig_shipping_status = px.pie(shipping_status, names='Estado del Envío', values='Cantidad',
                             title='Estado de los Envíos',
                             template='plotly_dark')
st.plotly_chart(fig_shipping_status)

# Average Shipping Cost
average_shipping_cost = filtered_df['Envio'].mean()
st.subheader('Costo Promedio de Envío')
st.metric("Costo Promedio de Envío", f"{average_shipping_cost:,.0f} CLP")

# Detailed Analysis by Product
st.subheader('Análisis Detallado por Producto')
producto_seleccionado = st.selectbox('Selecciona un Producto:', df['Nombre del Producto'].unique())
producto_df = filtered_df[filtered_df['Nombre del Producto'] == producto_seleccionado]

col1, col2, col3 = st.columns(3)
col1.metric("Total Vendido", f"{producto_df['Total'].sum():,.0f} CLP")
col2.metric("Cantidad Vendida", f"{producto_df['Cantidad de Productos'].sum():,.0f}")
col3.metric("Beneficio Total", f"{producto_df['Ganancia'].sum():,.0f} CLP")

# Plot: Sales of Selected Product Over Time
fig_producto = px.line(producto_df, x='Fecha', y='Total', 
                      title=f'Ventas de {producto_seleccionado} a lo Largo del Tiempo',
                      template='plotly_dark')
st.plotly_chart(fig_producto)
