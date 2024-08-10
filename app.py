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

# Summary metrics
total_revenue = filtered_df['Total'].sum()
total_profit = filtered_df['Ganancia'].sum()
total_orders = filtered_df['ID'].nunique()
average_order_value = total_revenue / total_orders if total_orders > 0 else 0
average_profit_per_order = total_profit / total_orders if total_orders > 0 else 0
overall_profit_margin = (total_profit / total_revenue) * 100 if total_revenue > 0 else 0

# Using markdown for better text styling
st.markdown(f"""
<div style="display: flex; justify-content: space-between;">
    <div style="flex: 1; margin-right: 10px;">
        <h3 style="font-size: 14px;">Total Revenue</h3>
        <p style="font-size: 18px; font-weight: bold;">{total_revenue:,.0f} CLP</p>
    </div>
    <div style="flex: 1; margin-right: 10px;">
        <h3 style="font-size: 14px;">Total Profit</h3>
        <p style="font-size: 18px; font-weight: bold;">{total_profit:,.0f} CLP</p>
    </div>
    <div style="flex: 1; margin-right: 10px;">
        <h3 style="font-size: 14px;">Total Orders</h3>
        <p style="font-size: 18px; font-weight: bold;">{total_orders:,}</p>
    </div>
    <div style="flex: 1; margin-right: 10px;">
        <h3 style="font-size: 14px;">Average Order Value</h3>
        <p style="font-size: 18px; font-weight: bold;">{average_order_value:,.0f} CLP</p>
    </div>
    <div style="flex: 1;">
        <h3 style="font-size: 14px;">Average Profit per Order</h3>
        <p style="font-size: 18px; font-weight: bold;">{average_profit_per_order:,.0f} CLP</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style="display: flex; justify-content: center; margin-top: 20px;">
    <div style="flex: 1; text-align: center;">
        <h3 style="font-size: 14px;">Overall Profit Margin</h3>
        <p style="font-size: 18px; font-weight: bold;">{overall_profit_margin:.2f} %</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Sales Trends
st.subheader('Sales Trends')

# Aggregating data for trends
sales_trends = filtered_df.resample('M', on='Fecha').agg({'Total': 'sum', 'Ganancia': 'sum'}).reset_index()
sales_trends['Month'] = sales_trends['Fecha'].dt.to_period('M').astype(str)

# Line chart for Sales and Profit Trends
fig_sales_trends = px.line(sales_trends, x='Month', y=['Total', 'Ganancia'],
                           labels={'value': 'Amount', 'Month': 'Date'},
                           title='Sales and Profit Trends Over Time')
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
                                  labels={'Cantidad de Productos': 'Quantity Sold'})
fig_top_selling_products.update_layout(xaxis_title='Product Name', yaxis_title='Quantity Sold')
st.plotly_chart(fig_top_selling_products)

# Product Profitability
fig_product_profitability = px.scatter(product_performance, x='Precio Promedio', y='Rentabilidad (%)',
                                       size='Total', color='Nombre del Producto',
                                       hover_name='Nombre del Producto',
                                       title='Product Profitability')
fig_product_profitability.update_layout(xaxis_title='Average Price', yaxis_title='Profitability (%)')
st.plotly_chart(fig_product_profitability)

# Payment and Discount Analysis
st.subheader('Payment and Discount Analysis')
# Payment Methods Breakdown
payment_methods = filtered_df['Nombre de Pago'].value_counts().reset_index()
payment_methods.columns = ['Payment Method', 'Count']
fig_payment_methods = px.pie(payment_methods, names='Payment Method', values='Count',
                            title='Sales Breakdown by Payment Method')
st.plotly_chart(fig_payment_methods)

# Discounts Applied
discounts = filtered_df.groupby('Cupones').agg({'Subtotal': 'sum', 'Total': 'sum'}).reset_index()
discounts.columns = ['Coupon', 'Subtotal', 'Total']
fig_discounts = px.bar(discounts, x='Coupon', y=['Subtotal', 'Total'],
                      title='Impact of Discounts on Sales',
                      labels={'value': 'Amount', 'Coupon': 'Coupon'})
fig_discounts.update_layout(barmode='group', xaxis_title='Coupon', yaxis_title='Amount')
st.plotly_chart(fig_discounts)

# Shipping Insights
st.subheader('Shipping Insights')
# Shipping Methods Distribution
shipping_methods = filtered_df['Nombre del metodo de envio'].value_counts().reset_index()
shipping_methods.columns = ['Shipping Method', 'Count']
fig_shipping_methods = px.pie(shipping_methods, names='Shipping Method', values='Count',
                              title='Distribution of Shipping Methods')
st.plotly_chart(fig_shipping_methods)

# Shipping Status
shipping_status = filtered_df['Estado del Envio'].value_counts().reset_index()
shipping_status.columns = ['Shipping Status', 'Count']
fig_shipping_status = px.pie(shipping_status, names='Shipping Status', values='Count',
                             title='Shipping Status Distribution')
st.plotly_chart(fig_shipping_status)

# Average Shipping Cost
average_shipping_cost = filtered_df['Envio'].mean()
st.metric("Average Shipping Cost", f"{average_shipping_cost:,.0f} CLP")

# Geographic Analysis
st.subheader('Geographic Analysis')
# Sales by City
sales_by_city = filtered_df.groupby('Ciudad de Envio').agg({'Total': 'sum'}).reset_index()
fig_sales_by_city = px.bar(sales_by_city, x='Ciudad de Envio', y='Total',
                          title='Sales by City',
                          labels={'Total': 'Sales Amount'})
fig_sales_by_city.update_layout(xaxis_title='City', yaxis_title='Sales Amount')
st.plotly_chart(fig_sales_by_city)

# Margin Analysis
st.subheader('Margin Analysis')
# Overall Margin Analysis
overall_margin = (filtered_df['Ganancia'].sum() / filtered_df['Total'].sum()) * 100
st.metric("Overall Margin", f"{overall_margin:.2f} %")

# Product Margin Analysis
product_margin_analysis = filtered_df.groupby('Nombre del Producto').agg({
    'Total': 'sum',
    'Ganancia': 'sum'
}).reset_index()
product_margin_analysis['Margen (%)'] = (product_margin_analysis['Ganancia'] / product_margin_analysis['Total']) * 100
fig_product_margin = px.bar(product_margin_analysis, x='Nombre del Producto', y='Margen (%)',
                            title='Margin Analysis by Product',
                            labels={'Margen (%)': 'Margin (%)'})
fig_product_margin.update_layout(xaxis_title='Product Name', yaxis_title='Margin (%)')
st.plotly_chart(fig_product_margin)
