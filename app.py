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

# Summary Metrics
st.subheader('Summary Metrics')
total_revenue = df['Total'].sum()
total_profit = df['Ganancia'].sum()
total_orders = df['ID'].nunique()
average_order_value = total_revenue / total_orders
average_profit_per_order = total_profit / total_orders
overall_profit_margin = (total_profit / total_revenue) * 100

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Revenue", f"{total_revenue:,.0f} CLP")
col2.metric("Total Profit", f"{total_profit:,.0f} CLP")
col3.metric("Total Orders", f"{total_orders:,}")
col4.metric("Average Order Value", f"{average_order_value:,.0f} CLP")
col5.metric("Average Profit per Order", f"{average_profit_per_order:,.0f} CLP")
st.metric("Overall Profit Margin", f"{overall_profit_margin:.2f} %")

# Sales Trends
st.subheader('Sales Trends')
# Aggregating data for trends
sales_trends = df.resample('M', on='Fecha').agg({'Total': 'sum', 'Ganancia': 'sum'}).reset_index()
sales_trends['Month'] = sales_trends['Fecha'].dt.to_period('M').astype(str)

# Line chart for Sales and Profit Trends
fig_sales_trends = px.line(sales_trends, x='Month', y=['Total', 'Ganancia'],
                           labels={'value': 'Amount', 'Month': 'Date'},
                           title='Sales and Profit Trends Over Time')
fig_sales_trends.update_layout(legend_title_text='Metrics')
st.plotly_chart(fig_sales_trends)

# Product Performance
st.subheader('Product Performance Overview')
product_performance = df.groupby(['Nombre del Producto', 'SKU del Producto']).agg({
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
                                  labels={'Cantidad de Productos': 'Quantity Sold'})
st.plotly_chart(fig_top_selling_products)

# Product Profitability
fig_product_profitability = px.scatter(product_performance, x='Precio Promedio', y='Rentabilidad (%)',
                                       size='Total', color='Nombre del Producto',
                                       hover_name='Nombre del Producto',
                                       title='Product Profitability')
st.plotly_chart(fig_product_profitability)

# Payment and Discount Analysis
st.subheader('Payment and Discount Analysis')
# Payment Methods Breakdown
payment_methods = df['Nombre de Pago'].value_counts().reset_index()
payment_methods.columns = ['Payment Method', 'Count']
fig_payment_methods = px.pie(payment_methods, names='Payment Method', values='Count',
                            title='Sales Breakdown by Payment Method')
st.plotly_chart(fig_payment_methods)

# Discounts Applied
discounts = df.groupby('Cupones').agg({'Subtotal': 'sum', 'Total': 'sum'}).reset_index()
discounts.columns = ['Coupon', 'Subtotal', 'Total']
fig_discounts = px.bar(discounts, x='Coupon', y=['Subtotal', 'Total'],
                      title='Impact of Discounts on Sales',
                      labels={'value': 'Amount', 'Coupon': 'Coupon'})
fig_discounts.update_layout(barmode='group')
st.plotly_chart(fig_discounts)

# Shipping Insights
st.subheader('Shipping Insights')
# Shipping Methods Distribution
shipping_methods = df['Nombre del metodo de envio'].value_counts().reset_index()
shipping_methods.columns = ['Shipping Method', 'Count']
fig_shipping_methods = px.pie(shipping_methods, names='Shipping Method', values='Count',
                              title='Distribution of Shipping Methods')
st.plotly_chart(fig_shipping_methods)

# Shipping Status
shipping_status = df['Estado del Envio'].value_counts().reset_index()
shipping_status.columns = ['Shipping Status', 'Count']
fig_shipping_status = px.pie(shipping_status, names='Shipping Status', values='Count',
                             title='Shipping Status Distribution')
st.plotly_chart(fig_shipping_status)

# Average Shipping Cost
average_shipping_cost = df['Envio'].mean()
st.metric("Average Shipping Cost", f"{average_shipping_cost:,.0f} CLP")

# Geographic Analysis
st.subheader('Geographic Analysis')
# Sales by Country
sales_by_country = df.groupby('Pais de Envio').agg({'Total': 'sum'}).reset_index()
fig_sales_by_country = px.bar(sales_by_country, x='Pais de Envio', y='Total',
                              title='Sales by Country',
                              labels={'Total': 'Sales Amount'})
st.plotly_chart(fig_sales_by_country)

# Sales by City
sales_by_city = df.groupby('Ciudad de Envio').agg({'Total': 'sum'}).reset_index()
fig_sales_by_city = px.bar(sales_by_city, x='Ciudad de Envio', y='Total',
                          title='Sales by City',
                          labels={'Total': 'Sales Amount'})
st.plotly_chart(fig_sales_by_city)

# Customer Insights
# Placeholder if customer data is available
# st.subheader('Customer Insights')
# st.write("Customer segmentation data not available")

# Margin Analysis
st.subheader('Margin Analysis')
# Overall Margin Analysis
overall_margin = (df['Ganancia'].sum() / df['Total'].sum()) * 100
st.metric("Overall Margin", f"{overall_margin:.2f} %")

# Product Margin Analysis
product_margin_analysis = df.groupby('Nombre del Producto').agg({
    'Total': 'sum',
    'Ganancia': 'sum'
}).reset_index()
product_margin_analysis['Margen (%)'] = (product_margin_analysis['Ganancia'] / product_margin_analysis['Total']) * 100
fig_product_margin = px.bar(product_margin_analysis, x='Nombre del Producto', y='Margen (%)',
                            title='Margin Analysis by Product',
                            labels={'Margen (%)': 'Margin (%)'})
st.plotly_chart(fig_product_margin)

# Interactive Filters
st.sidebar.subheader('Interactive Filters')
date_range = st.sidebar.date_input('Select Date Range', [df['Fecha'].min().date(), df['Fecha'].max().date()])
# Convert date_range to datetime
date_range = [pd.to_datetime(date) for date in date_range]
filtered_df = df[(df['Fecha'] >= date_range[0]) & (df['Fecha'] <= date_range[1])]

selected_country = st.sidebar.selectbox('Select Country:', df['Pais de Envio'].unique())
filtered_df = filtered_df[filtered_df['Pais de Envio'] == selected_country]

# Update KPIs with filters
total_revenue_filtered = filtered_df['Total'].sum()
total_profit_filtered = filtered_df['Ganancia'].sum()
total_orders_filtered = filtered_df['ID'].nunique()
average_order_value_filtered = total_revenue_filtered / total_orders_filtered if total_orders_filtered > 0 else 0
average_profit_per_order_filtered = total_profit_filtered / total_orders_filtered if total_orders_filtered > 0 else 0
overall_profit_margin_filtered = (total_profit_filtered / total_revenue_filtered) * 100 if total_revenue_filtered > 0 else 0

col1, col2, col3, col4, col5 = st.sidebar.columns(5)
col1.metric("Total Revenue", f"{total_revenue_filtered:,.0f} CLP")
col2.metric("Total Profit", f"{total_profit_filtered:,.0f} CLP")
col3.metric("Total Orders", f"{total_orders_filtered:,}")
col4.metric("Average Order Value", f"{average_order_value_filtered:,.0f} CLP")
col5.metric("Average Profit per Order", f"{average_profit_per_order_filtered:,.0f} CLP")
st.sidebar.metric("Overall Profit Margin", f"{overall_profit_margin_filtered:.2f} %")

# Display filtered data preview
st.sidebar.subheader('Filtered Data Preview')
st.sidebar.dataframe(filtered_df.head())
