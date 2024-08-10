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

# Create a new column to differentiate between 'Venta al Detalle' and 'Venta Mayorista'
df['Tipo de Venta'] = df['Cantidad de Productos'].apply(lambda x: 'Venta al Detalle' if x < 6 else 'Venta Mayorista')

# Dashboard Title
st.title('Dashboard de Análisis de Ventas')

# Add space between title and the next part
st.write("")
st.write("")

# Interactive Filters
st.sidebar.subheader('Filtros Interactivos')

# Date Range Filter
date_range = st.sidebar.date_input('Selecciona el Rango de Fechas', [df['Fecha'].min().date(), df['Fecha'].max().date()])
date_range = [pd.to_datetime(date) for date in date_range]

# Tipo de Venta Filter
tipo_venta = st.sidebar.selectbox('Selecciona el Tipo de Venta', ['Todo', 'Venta al Detalle', 'Venta Mayorista'])

# Filter DataFrame based on selections
filtered_df = df[(df['Fecha'] >= date_range[0]) & (df['Fecha'] <= date_range[1])]
if tipo_venta != 'Todo':
    filtered_df = filtered_df[filtered_df['Tipo de Venta'] == tipo_venta]

# Check if filtered DataFrame is empty
if filtered_df.empty:
    st.error('No hay datos disponibles para los filtros seleccionados.')
else:
    # Summary Metrics
    st.subheader('Antes de Impuestos')

    # Calculate metrics
    total_revenue = filtered_df['Total'].sum()
    total_profit = filtered_df['Ganancia'].sum()
    total_orders = filtered_df['ID'].nunique()
    average_order_value = total_revenue / total_orders if total_orders > 0 else 0
    average_profit_per_order = total_profit / total_orders if total_orders > 0 else 0
    overall_profit_margin = (total_profit / total_revenue) * 100 if total_revenue > 0 else 0

    # Calculate Total Discounts
    total_descuentos = filtered_df['Descuento'].sum()  # Ensure 'Descuento' column exists in your DataFrame

    # Display metrics using Streamlit's built-in functions
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    col1.metric(label="Ventas", value=f"{total_revenue:,.0f} CLP", delta=None)
    col2.metric(label="Ganancias", value=f"{total_profit:,.0f} CLP", delta=None)
    col3.metric(label="Total de Pedidos", value=f"{total_orders:,}", delta=None)
    col4.metric(label="Valor Promedio por Pedido", value=f"{average_order_value:,.0f} CLP", delta=None)
    col5.metric(label="Ganancia Promedio por Pedido", value=f"{average_profit_per_order:,.0f} CLP", delta=None)
    col6.metric(label="Margen", value=f"{overall_profit_margin:.2f} %", delta=None)

    # Display Total Discounts
    st.metric("Descuentos Aplicados", f"{total_descuentos:,.0f} CLP")

    # Calculate profit after tax
    tax_rate = 0.19
    filtered_df['Ganancia Después de Impuestos'] = filtered_df['Ganancia'] * (1 - tax_rate)

    # Calculate margin after tax
    total_profit_after_tax = filtered_df['Ganancia Después de Impuestos'].sum()
    overall_margin_after_tax = (total_profit_after_tax / total_revenue) * 100 if total_revenue > 0 else 0

    # Additional metric for profit after tax
    st.subheader('Después de Impuestos')
    st.metric("Ganancias Después de Impuestos (19%)", f"{total_profit_after_tax:,.0f} CLP")
    st.metric("Margen Después de Impuestos", f"{overall_margin_after_tax:.2f} %")

    # Add space before Sales Trends section
    st.write("")
    st.write("")

    # Sales Trends
    st.subheader('Ventas')

    # Aggregating data for trends
    sales_trends = filtered_df.resample('M', on='Fecha').agg({'Total': 'sum', 'Ganancia': 'sum', 'Ganancia Después de Impuestos': 'sum'}).reset_index()
    sales_trends['Month'] = sales_trends['Fecha'].dt.to_period('M').astype(str)

    if not sales_trends.empty:
        # Line chart for Sales and Profit After Tax Trends
        fig_sales_trends = px.line(sales_trends, x='Month', y=['Total', 'Ganancia Después de Impuestos'],
                                   labels={'value': 'Monto', 'Month': 'Fecha'},
                                   title='Ventas vs Ganancias Después de Impuestos',
                                   template='plotly_dark')
        # Update the legend to rename the lines
        fig_sales_trends.for_each_trace(lambda t: t.update(name='Ventas' if t.name == 'Total' else 'Ganancias Después de Impuestos'))
        fig_sales_trends.update_layout(legend_title_text='Métricas')
        st.plotly_chart(fig_sales_trends)
    else:
        st.write("No hay datos suficientes para mostrar tendencias de ventas.")

    # Product Performance
    st.subheader('Desempeño de Productos')
    product_performance = filtered_df.groupby(['Nombre del Producto', 'SKU del Producto', 'Tipo de Venta']).agg({
        'Cantidad de Productos': 'sum',
        'Total': 'sum',
        'Ganancia': 'sum'
    }).reset_index()
    product_performance['Precio Promedio'] = product_performance['Total'] / product_performance['Cantidad de Productos']
    product_performance['Rentabilidad (%)'] = (product_performance['Ganancia'] / product_performance['Total']) * 100

    if not product_performance.empty:
        # Top-Selling Products Bar Chart with SKU
        fig_top_selling_products = px.bar(product_performance.sort_values('Cantidad de Productos', ascending=False),
                                          x='Nombre del Producto', y='Cantidad de Productos',
                                          color='Tipo de Venta',
                                          title='Productos Más Vendidos',
                                          labels={'Cantidad de Productos': 'Cantidad Vendida'},
                                          template='plotly_dark',
                                          text='SKU del Producto')  # Add SKU to bars
        fig_top_selling_products.update_layout(xaxis_title='Nombre del Producto', yaxis_title='Cantidad Vendida')
        fig_top_selling_products.update_traces(texttemplate='%{text}', textposition='outside')
        st.plotly_chart(fig_top_selling_products)

        # Product Profitability
        fig_product_profitability = px.scatter(product_performance, x='Precio Promedio', y='Rentabilidad (%)',
                                               size='Total', color='Nombre del Producto',
                                               hover_name='Nombre del Producto',
                                               title='Rentabilidad de Productos',
                                               template='plotly_dark')
        fig_product_profitability.update_layout(xaxis_title='Precio Promedio', yaxis_title='Rentabilidad (%)')
        st.plotly_chart(fig_product_profitability)
    else:
        st.write("No hay datos suficientes para mostrar el desempeño de productos.")

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
    st.metric("Costo Promedio de Envío", f"{average_shipping_cost:,.0f} CLP")

    # Detailed Analysis by Product
    st.subheader('Análisis Detallado por Producto')
    producto_seleccionado = st.selectbox('Selecciona un Producto:', filtered_df['Nombre del Producto'].unique())
    producto_df = filtered_df[filtered_df['Nombre del Producto'] == producto_seleccionado]

    if not producto_df.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Vendido", f"{producto_df['Total'].sum():,.0f} CLP")
        col2.metric("Cantidad Vendida", f"{producto_df['Cantidad de Productos'].sum():,.0f}")
        col3.metric("Beneficio Total", f"{producto_df['Ganancia'].sum():,.0f} CLP")

        # Plot: Sales of Selected Product Over Time
        fig_producto = px.line(producto_df, x='Fecha', y='Total', 
                              title=f'Ventas de {producto_seleccionado} a lo Largo del Tiempo',
                              template='plotly_dark')
        st.plotly_chart(fig_producto)
    else:
        st.write("No hay datos disponibles para el producto seleccionado.")
