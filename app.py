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
st.title('Sales Analysis Dashboard')

# Interactive Filters
st.sidebar.subheader('Interactive Filters')
date_range = st.sidebar.date_input('Select Date Range', [df['Fecha'].min().date(), df['Fecha'].max().date()])
date_range = [pd.to_datetime(date) for date in date_range]
filtered_df = df[(df['Fecha'] >= date_range[0]) & (df['Fecha'] <= date_range[1])]

# Summary Metrics
st.subheader('Summary Metrics')

# Calculate metrics
total_revenue = filtered_df['Total'].sum()
total_profit = filtered_df['Ganancia'].sum()
total_orders = filtered_df['ID'].nunique()
average_order_value = total_revenue / total_orders if total_orders > 0 else 0
average_profit_per_order = total_profit / total_orders if total_orders > 0 else 0
overall_profit_margin = (total_profit / total_revenue) * 100 if total_revenue > 0 else 0

# Display metrics using Streamlit's built-in functions
col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    st.metric("Total Revenue", f"{total_revenue:,.0f} CLP")
with col2:
    st.metric("Total Profit", f"{total_profit:,.0f} CLP")
with col3:
    st.metric("Total Orders", f"{total_orders:,}")
with col4:
    st.metric("Average Order Value", f"{average_order_value:,.0f} CLP")
with col5:
    st.metric("Average Profit per Order", f"{average_profit_per_order:,.0f} CLP")
with col6:
    st.metric("Overall Profit Margin", f"{overall_profit_margin:.2f} %")

# Sales Trends
st.subheader('Sales Trends')

# Aggregating data for trends
sales_trends = filtered_df.resample('M', on='Fecha').agg({'Total': 'sum', 'Ganancia': 'sum'}).reset_index()
sales_trends['Month'] = sales_trends['Fecha'].dt.to_period('M').astype(str)

# Line chart for Sales and Profit Trends
fig_sales_trends = px.line(sales_trends, x='Month', y=['Total', 'Ganancia'],
                           labels={'value': 'Amount', 'Month': 'Date'},
                           title='Sales and Profit Trends Over Time',
                           template='plotly_dark')
fig_sales_trends.update_layout(legend_title_text='Metrics')
st.plotly_chart(fig_sales_trends)

# Sales by Year, Month, and Week
st.subheader('Sales Breakdown by Period')

# Aggregating data by year, month, and week
sales_by_year = filtered_df.resample('Y', on='Fecha').agg({'Total': 'sum', 'ID': 'count'}).reset_index()
sales_by_month = filtered_df.resample('M', on='Fecha').agg({'Total': 'sum', 'ID': 'count'}).reset_index()
sales_by_week = filtered_df.resample('W', on='Fecha').agg({'Total': 'sum', 'ID': 'count'}).reset_index()

# Display total sales and orders for the year
yearly_sales = sales_by_year.tail(1).iloc[0]
st.subheader(f'Sales for the Year {yearly_sales["Fecha"].year}')
col1, col2 = st.columns(2)
col1.metric("Total Sales", f"{yearly_sales['Total']:,.0f} CLP")
col2.metric("Total Orders", f"{yearly_sales['ID']:,}")

# Display total sales and orders for the current month
monthly_sales = sales_by_month.tail(1).iloc[0]
st.subheader(f'Sales for the Month {monthly_sales["Fecha"].strftime("%B %Y")}')
col1, col2 = st.columns(2)
col1.metric("Total Sales", f"{monthly_sales['Total']:,.0f} CLP")
col2.metric("Total Orders", f"{monthly_sales['ID']:,}")

# Display total sales and orders for the current week
weekly_sales = sales_by_week.tail(1).iloc[0]
st.subheader(f'Sales for the Week of {weekly_sales["Fecha"].strftime("%d %b %Y")}')
col1, col2 = st.columns(2)
col1.metric("Total Sales", f"{weekly_sales['Total']:,.0f} CLP")
col2.metric("Total Orders", f"{weekly_sales['ID']:,}")

# Product Performance
st.subheader('Product Performance Overview')
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
                                  title='Top-Selling Products',
                                  labels={'Cantidad de Productos': 'Quantity Sold'},
                                  template='plotly_dark')
fig_top_selling_products.update_layout(xaxis_title='Product Name', yaxis_title='Quantity Sold')
st.plotly_chart(fig_top_selling_products)

# Product Profitability
fig_product_profitability = px.scatter(product_performance, x='Precio Promedio', y='Rentabilidad (%)',
                                       size='Total', color='Nombre del Producto',
                                       hover_name='Nombre del Producto',
                                       title='Product Profitability',
                                       template='plotly_dark')
fig_product_profitability.update_layout(xaxis_title='Average Price', yaxis_title='Profitability (%)')
st.plotly_chart(fig_product_profitability)

# Payment and Discount Analysis
st.subheader('Payment and Discount Analysis')
# Payment Methods Breakdown
payment_methods = filtered_df['Nombre de Pago'].value_counts().reset_index()
payment_methods.columns = ['Payment Method', 'Count']
fig_payment_methods = px.pie(payment_methods, names='Payment Method', values='Count',
                            title='Sales Breakdown by Payment Method',
                            template='plotly_dark')
st.plotly_chart(fig_payment_methods)

# Discounts Applied
discounts = filtered_df.groupby('Cupones').agg({'Subtotal': 'sum', 'Total': 'sum'}).reset_index()
discounts.columns = ['Coupon', 'Subtotal', 'Total']
fig_discounts = px.bar(discounts, x='Coupon', y=['Subtotal', 'Total'],
                      title='Impact of Discounts on Sales',
                      labels={'value': 'Amount', 'Coupon': 'Coupon'},
                      template='plotly_dark')
fig_discounts.update_layout(barmode='group', xaxis_title='Coupon', yaxis_title='Amount')
st.plotly_chart(fig_discounts)

# Shipping Insights
st.subheader('Shipping Insights')
# Shipping Methods Distribution
shipping_methods = filtered_df['Nombre del metodo de envio'].value_counts().reset_index()
shipping_methods.columns = ['Shipping Method', 'Count']
fig_shipping_methods = px.pie(shipping_methods, names='Shipping Method', values='Count',
                              title='Distribution of Shipping Methods',
                              template='plotly_dark')
st.plotly_chart(fig_shipping_methods)

# Shipping Status
shipping_status = filtered_df['Estado del Envio'].value_counts().reset_index()
shipping_status.columns = ['Shipping Status', 'Count']
fig_shipping_status = px.bar(shipping_status, x='Shipping Status', y='Count',
                             title='Shipping Status Breakdown',
                             template='plotly_dark')
st.plotly_chart(fig_shipping_status)

# Average Shipping Cost
average_shipping_cost = filtered_df['Envio'].mean()
st.metric("Average Shipping Cost", f"{average_shipping_cost:,.0f} CLP")

# Detailed Analysis by Product
st.subheader('Detailed Analysis by Product')
producto_seleccionado = st.selectbox('Select a Product:', df['Nombre del Producto'].unique())
producto_df = df[df['Nombre del Producto'] == producto_seleccionado]

# Detailed Metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Sold", f"{producto_df['Total'].sum():,.0f} CLP")
with col2:
    st.metric("Quantity Sold", f"{producto_df['Cantidad de Productos'].sum():,.0f}")
with col3:
    st.metric("Total Profit", f"{producto_df['Ganancia'].sum():,.0f} CLP")

# Sales of Selected Product Over Time
fig_producto = px.line(producto_df, x='Fecha', y='Total',
                      title=f'Sales of {producto_seleccionado} Over Time',
                      template='plotly_dark')
st.plotly_chart(fig_producto)
