import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Cargar el archivo CSV principal desde GitHub
url = "https://raw.githubusercontent.com/HUHU0101123/og-app/main/datasource.csv"
df = pd.read_csv(url)

# Cargar el archivo de categorías desde GitHub
categorias_url = "https://raw.githubusercontent.com/HUHU0101123/og-app/main/categorias.csv"
categorias_df = pd.read_csv(categorias_url)

# Limpiar nombres de columnas
df.columns = df.columns.str.strip()
categorias_df.columns = categorias_df.columns.str.strip()

# Convertir la columna 'Fecha' a tipo datetime
df['Fecha'] = pd.to_datetime(df['Fecha'])

# Imprimir las primeras filas del DataFrame y los nombres de columnas para verificar
st.write("Primeras filas del DataFrame:")
st.write(df.head())
st.write("Columnas del DataFrame:")
st.write(df.columns)

# Unir los DataFrames usando 'SKU del Producto'
merged_df = pd.merge(df, categorias_df, on='SKU del Producto', how='left')

# Crear una nueva columna 'Total' calculada
merged_df['Total'] = merged_df['Cantidad de Productos'] * merged_df['Precio del Producto'].str.replace(',', '.').astype(float)

# Crear una nueva columna 'Total Final' considerando el descuento y el costo de envío
merged_df['Total Final'] = merged_df['Total'] - merged_df['Descuento del producto'].str.replace(',', '.').astype(float)

# Restar el costo de envío si el método de entrega es "Despacho Santiago (RM) a domicilio"
merged_df['Total Final'] = merged_df.apply(
    lambda row: row['Total Final'] - 2990 if row['Nombre del método de envío'] == "Despacho Santiago (RM) a domicilio" else row['Total Final'],
    axis=1
)

# Crear una nueva columna 'Ganancia' calculada
merged_df['Ganancia'] = (merged_df['Rentabilidad del producto'] / 100) * merged_df['Total Final']

# Crear una nueva columna para diferenciar entre 'Venta al Detalle' y 'Venta Mayorista'
merged_df['Tipo de Venta'] = merged_df['Cantidad de Productos'].apply(lambda x: 'Venta al Detalle' if x < 6 else 'Venta Mayorista')

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
start_date = st.sidebar.date_input('Fecha de Inicio', merged_df['Fecha'].min().date())
# Selector de fecha final
end_date = st.sidebar.date_input('Fecha de Fin', merged_df['Fecha'].max().date())

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
    filtered_df = merged_df[(merged_df['Fecha'] >= start_date) & (merged_df['Fecha'] <= end_date)]
    if tipo_venta != 'Todo':
        filtered_df = filtered_df[filtered_df['Tipo de Venta'] == tipo_venta]

    # Agrupar por ID de la orden para evitar duplicados en las métricas
    order_summary = filtered_df.groupby('ID').agg({
        'Total Final': 'sum',
        'Ganancia': 'sum',
        'Cantidad de Productos': 'sum',
        'Descuento del producto': 'sum'
    }).reset_index()

    # Verificar si el DataFrame filtrado está vacío
    if order_summary.empty:
        st.error('No hay datos disponibles para los filtros seleccionados.')
    else:
        # Métricas de resumen
        st.subheader('Antes de Impuestos')

        # Calcular métricas
        total_revenue = order_summary['Total Final'].sum()
        total_profit = order_summary['Ganancia'].sum()
        total_orders = order_summary['ID'].nunique()
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0
        average_profit_per_order = total_profit / total_orders if total_orders > 0 else 0
        overall_profit_margin = (total_profit / total_revenue) * 100 if total_revenue > 0 else 0

        # Calcular descuentos totales
        total_descuentos = order_summary['Descuento del producto'].sum()

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
        order_summary['Ganancia Después de Impuestos'] = order_summary['Ganancia'] * (1 - tax_rate)

        # Calcular margen después de impuestos
        total_profit_after_tax = order_summary['Ganancia Después de Impuestos'].sum()
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
            # Gráfico de líneas para Ventas y Ganancia Después de Impuestos
            fig_sales_trends = px.line(sales_trends, x='Month', y=['Total Final', 'Ganancia Después de Impuestos'],
                                       labels={'value': 'Monto', 'Month': 'Fecha'},
                                       title='Ventas vs Ganancias Después de Impuestos',
                                       template='plotly_dark')
            fig_sales_trends.for_each_trace(lambda t: t.update(name='Ventas' if t.name == 'Total Final' else 'Ganancias Después de Impuestos'))

            # Calcular el punto medio en el eje x
            num_points = len(sales_trends['Month'])
            mid_index = num_points // 2
            mid_month = sales_trends['Month'].iloc[mid_index]
            
            # Añadir anotaciones en el medio de las curvas
            fig_sales_trends.update_layout(showlegend=False)
            fig_sales_trends.update_layout(
                annotations=[
                    dict(
                        x=mid_month,  # Posición X para la anotación
                        y=sales_trends[sales_trends['Month'] == mid_month]['Total Final'].mean(),  # Posición Y para la anotación
                        text='Ventas',
                        showarrow=True,
                        arrowhead=2,
                        ax=0,
                        ay=-40
                    ),
                    dict(
                        x=mid_month,  # Posición X para la anotación
                        y=sales_trends[sales_trends['Month'] == mid_month]['Ganancia Después de Impuestos'].mean(),  # Posición Y para la anotación
                        text='Ganancias Después de Impuestos',
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
        producto_seleccionado = st.selectbox('Selecciona un Producto:', filtered_df['Nombre del Producto'].unique())
        producto_df = filtered_df[filtered_df['Nombre del Producto'] == producto_seleccionado]

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
