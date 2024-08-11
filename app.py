import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Cargar el archivo CSV principal desde GitHub
url = "https://raw.githubusercontent.com/HUHU0101123/og-app/main/datasource.csv"
df = pd.read_csv(url)

# Limpiar nombres de columnas
df.columns = df.columns.str.strip()

# Convertir la columna 'Fecha' a tipo datetime
df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')

# Convertir columnas a tipo numérico (si es necesario)
df['Precio del Producto'] = df['Precio del Producto'].str.replace(',', '.').astype(float)
df['Cantidad de Productos'] = pd.to_numeric(df['Cantidad de Productos'], errors='coerce')
df['Descuento del producto'] = df['Descuento del producto'].str.replace(',', '.').astype(float)
df['Rentabilidad del producto'] = pd.to_numeric(df['Rentabilidad del producto'], errors='coerce')

# Agrupar las filas de cada pedido
# Para ello, primero necesitamos llenar los datos generales en las filas que contienen productos
df['Precio del Producto'] = df.groupby('ID')['Precio del Producto'].transform(lambda x: x.ffill())
df['Rentabilidad del producto'] = df.groupby('ID')['Rentabilidad del producto'].transform(lambda x: x.ffill())
df['Descuento del producto'] = df.groupby('ID')['Descuento del producto'].transform(lambda x: x.ffill())
df['Nombre del método de envío'] = df.groupby('ID')['Nombre del método de envío'].transform(lambda x: x.ffill())

# Crear una nueva columna 'Total' calculada
df['Total'] = df['Cantidad de Productos'] * df['Precio del Producto']

# Crear una nueva columna 'Total Final' considerando el descuento y el costo de envío
df['Total Final'] = df['Total'] - df['Descuento del producto']

# Restar el costo de envío si el método de entrega es "Despacho Santiago (RM) a domicilio"
df['Total Final'] = df.apply(
    lambda row: row['Total Final'] - 2990 if row['Nombre del método de envío'] == "Despacho Santiago (RM) a domicilio" else row['Total Final'],
    axis=1
)

# Agregar los detalles de las órdenes (sumar los totales por ID)
order_summary = df.groupby('ID').agg({
    'Total Final': 'sum',
    'Rentabilidad del producto': 'mean',
    'Cantidad de Productos': 'sum',
    'Descuento del producto': 'sum'
}).reset_index()

# Crear una nueva columna 'Ganancia' calculada
order_summary['Ganancia'] = (order_summary['Rentabilidad del producto'] / 100) * order_summary['Total Final']

# Crear una nueva columna para diferenciar entre 'Venta al Detalle' y 'Venta Mayorista'
order_summary['Tipo de Venta'] = order_summary['Cantidad de Productos'].apply(lambda x: 'Venta al Detalle' if x < 6 else 'Venta Mayorista')

# Función para formatear números con el formato chileno
def format_chilean_number(number, decimal_places=0):
    formatted = "{:,.{prec}f}".format(number, prec=decimal_places).replace(',', 'X').replace('.', ',').replace('X', '.')
    return formatted

# Función para formatear porcentajes
def format_percentage(percentage):
    return "{:.2f} %".format(percentage).replace('.', ',')

# Configuración del diseño del panel lateral
st.sidebar.subheader('Filtros Interactivos')

# Selector de fecha de inicio
start_date = st.sidebar.date_input('Fecha de Inicio', df['Fecha'].min().date())
# Selector de fecha final
end_date = st.sidebar.date_input('Fecha de Fin', df['Fecha'].max().date())

# Convertir las fechas seleccionadas a tipo datetime para comparación
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

# Asegúrate de que la fecha de fin sea después de la fecha de inicio
if start_date > end_date:
    st.sidebar.error('La fecha de fin debe ser posterior a la fecha de inicio.')
else:
    # Filtro por tipo de venta
    tipo_venta = st.sidebar.selectbox('Tipo de Venta', ['Todo', 'Venta al Detalle', 'Venta Mayorista'])

    # Filtrar el DataFrame según las selecciones
    filtered_df = order_summary[(df['Fecha'] >= start_date) & (df['Fecha'] <= end_date)]
    if tipo_venta != 'Todo':
        filtered_df = filtered_df[filtered_df['Tipo de Venta'] == tipo_venta]

    # Verificar si el DataFrame filtrado está vacío
    if filtered_df.empty:
        st.error('No hay datos disponibles para los filtros seleccionados.')
    else:
        # Métricas de resumen
        st.subheader('Antes de Impuestos')

        # Calcular métricas
        total_revenue = filtered_df['Total Final'].sum()
        total_profit = filtered_df['Ganancia'].sum()
        total_orders = filtered_df['ID'].nunique()
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0
        average_profit_per_order = total_profit / total_orders if total_orders > 0 else 0
        overall_profit_margin = (total_profit / total_revenue) * 100 if total_revenue > 0 else 0

        # Calcular descuentos totales
        total_descuentos = filtered_df['Descuento del producto'].sum()

        # Mostrar métricas en columnas
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric(label="Ventas", value=f"{format_chilean_number(total_revenue, 0)} CLP")
        col2.metric(label="Ganancias", value=f"{format_chilean_number(total_profit, 0)} CLP")
        col3.metric(label="Total de Pedidos", value=f"{format_chilean_number(total_orders, 0)}")
        col4.metric(label="Valor Promedio por Pedido", value=f"{format_chilean_number(average_order_value, 0)} CLP")
        col5.metric(label="Ganancia Promedio por Pedido", value=f"{format_chilean_number(average_profit_per_order, 0)} CLP")
        col6.metric(label="Margen", value=format_percentage(overall_profit_margin))

        # Mostrar total de descuentos
        st.metric("Descuentos Aplicados", f"{format_chilean_number(total_descuentos, 0)} CLP")

        # Calcular ganancia después de impuestos
        tax_rate = 0.19
        filtered_df['Ganancia Después de Impuestos'] = filtered_df['Ganancia'] * (1 - tax_rate)

        # Calcular margen después de impuestos
        total_profit_after_tax = filtered_df['Ganancia Después de Impuestos'].sum()
        overall_margin_after_tax = (total_profit_after_tax / total_revenue) * 100 if total_revenue > 0 else 0

        # Métrica adicional para ganancia después de impuestos
        st.subheader('Después de Impuestos')
        st.metric("Ganancias Después de Impuestos (19%)", f"{format_chilean_number(total_profit_after_tax, 0)} CLP")
        st.metric("Margen Después de Impuestos", format_percentage(overall_margin_after_tax))

        # Espacio antes de la sección de Ventas
        st.write("")
        st.write("")
        st.write("")
        st.write("")  # Añadido para más espacio

        # Tendencias de Ventas
        st.subheader('Ventas')

        # Agregación de datos para tendencias
        sales_trends = filtered_df.resample('M', on='Fecha').agg({'Total Final': 'sum', 'Ganancia': 'sum', 'Ganancia Después de Impuestos': 'sum'}).reset_index()
        sales_trends['Month'] = sales_trends['Fecha'].dt.to_period('M').astype(str)

        if not sales_trends.empty:
            # Gráfico de líneas para tendencias de ventas
            fig_sales_trends = px.line(sales_trends, x='Month', y='Total Final', title='Tendencias de Ventas',
                                      labels={'Month': 'Mes', 'Total Final': 'Ventas Totales'},
                                      template='plotly_dark')
            fig_sales_trends.update_layout(xaxis_title='Mes', yaxis_title='Ventas Totales')
            fig_sales_trends.add_trace(
                go.Scatter(
                    x=sales_trends['Month'],
                    y=sales_trends['Ganancia'],
                    mode='lines+markers',
                    name='Ganancia',
                    marker=dict(color='rgb(255, 0, 0)')
                )
            )
            fig_sales_trends.add_trace(
                go.Scatter(
                    x=sales_trends['Month'],
                    y=sales_trends['Ganancia Después de Impuestos'],
                    mode='lines+markers',
                    name='Ganancia Después de Impuestos',
                    marker=dict(color='rgb(0, 255, 0)')
                )
            )
            fig_sales_trends.update_layout(
                annotations=[
                    dict(
                        x=sales_trends['Month'].iloc[-1],
                        y=sales_trends['Total Final'].iloc[-1],
                        text=f"Ventas Totales: {format_chilean_number(sales_trends['Total Final'].iloc[-1], 0)} CLP",
                        showarrow=True,
                        arrowhead=2,
                        ax=0,
                        ay=-40
                    ),
                    dict(
                        x=sales_trends['Month'].iloc[-1],
                        y=sales_trends['Ganancia'].iloc[-1],
                        text=f"Ganancia: {format_chilean_number(sales_trends['Ganancia'].iloc[-1], 0)} CLP",
                        showarrow=True,
                        arrowhead=2,
                        ax=0,
                        ay=-40
                    ),
                    dict(
                        x=sales_trends['Month'].iloc[-1],
                        y=sales_trends['Ganancia Después de Impuestos'].iloc[-1],
                        text=f"Ganancia Después de Impuestos: {format_chilean_number(sales_trends['Ganancia Después de Impuestos'].iloc[-1], 0)} CLP",
                        showarrow=True,
                        arrowhead=2,
                        ax=0,
                        ay=-40
                    )
                ]
            )
            st.plotly_chart(fig_sales_trends)
        else:
            st.write("No hay datos suficientes para mostrar tendencias de ventas.")

        # Desempeño de Productos
        st.subheader('Desempeño de Productos')

        try:
            product_performance = filtered_df.groupby('SKU del Producto').agg({
                'Total Final': 'sum',
                'Ganancia': 'sum',
                'Cantidad de Productos': 'sum'
            }).reset_index()

            product_performance = product_performance.sort_values(by='Ganancia', ascending=False)

            # Tabla de desempeño de productos
            st.dataframe(product_performance)

            # Gráfico de barras para desempeño de productos
            fig_product_performance = px.bar(product_performance, x='SKU del Producto', y='Ganancia',
                                             labels={'SKU del Producto': 'SKU', 'Ganancia': 'Ganancia'},
                                             title='Desempeño de Productos',
                                             template='plotly_dark')
            fig_product_performance.update_layout(xaxis_title='SKU del Producto', yaxis_title='Ganancia')
            st.plotly_chart(fig_product_performance)
        except Exception as e:
            st.error(f"Error al calcular el desempeño de productos: {e}")

        # Desempeño por Región
        st.subheader('Desempeño por Región')

        try:
            region_performance = filtered_df.groupby('Región de Envío').agg({
                'Total Final': 'sum',
                'Ganancia': 'sum',
                'Cantidad de Productos': 'sum'
            }).reset_index()

            region_performance = region_performance.sort_values(by='Ganancia', ascending=False)

            # Tabla de desempeño por región
            st.dataframe(region_performance)

            # Gráfico de barras para desempeño por región
            fig_region_performance = px.bar(region_performance, x='Región de Envío', y='Ganancia',
                                            labels={'Región de Envío': 'Región', 'Ganancia': 'Ganancia'},
                                            title='Desempeño por Región',
                                            template='plotly_dark')
            fig_region_performance.update_layout(xaxis_title='Región de Envío', yaxis_title='Ganancia')
            st.plotly_chart(fig_region_performance)
        except Exception as e:
            st.error(f"Error al calcular el desempeño por región: {e}")

        # Análisis Detallado por Producto
        st.subheader('Análisis Detallado por Producto')
        producto_seleccionado = st.selectbox('Selecciona un Producto:', filtered_df['SKU del Producto'].unique())
        producto_df = filtered_df[filtered_df['SKU del Producto'] == producto_seleccionado]

        if not producto_df.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Vendido", f"{format_chilean_number(producto_df['Total Final'].sum(), 0)} CLP")
            col2.metric("Cantidad Vendida", f"{format_chilean_number(producto_df['Cantidad de Productos'].sum(), 0)}")
            col3.metric("Beneficio Total", f"{format_chilean_number(producto_df['Ganancia'].sum(), 0)} CLP")

            # Gráfico: Ventas del Producto Seleccionado a lo Largo del Tiempo
            fig_producto = px.line(producto_df, x='Fecha', y='Total Final',
                                  title=f'Ventas de {producto_seleccionado} a lo Largo del Tiempo',
                                  template='plotly_dark')
            st.plotly_chart(fig_producto)
        else:
            st.write("No hay datos disponibles para el producto seleccionado.")
