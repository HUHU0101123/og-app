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

# Unir los DataFrames usando 'Nombre del Producto'
merged_df = pd.merge(df, categorias_df, on='Nombre del Producto', how='left')

# Crear una nueva columna para diferenciar entre 'Venta al Detalle' y 'Venta Mayorista'
merged_df['Tipo de Venta'] = merged_df['Cantidad de Productos'].apply(lambda x: 'Venta al Detalle' if x < 6 else 'Venta Mayorista')

# Función para formatear números con el formato chileno
def format_chilean_number(number):
    return "{:,.0f}".format(number).replace(',', '.').replace('.', ',', 1)

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

    # Verificar si el DataFrame filtrado está vacío
    if filtered_df.empty:
        st.error('No hay datos disponibles para los filtros seleccionados.')
    else:
        # Métricas de resumen
        st.subheader('Antes de Impuestos')

        # Calcular métricas
        total_revenue = filtered_df['Total'].sum()
        total_profit = filtered_df['Ganancia'].sum()
        total_orders = filtered_df['ID'].nunique()
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0
        average_profit_per_order = total_profit / total_orders if total_orders > 0 else 0
        overall_profit_margin = (total_profit / total_revenue) * 100 if total_revenue > 0 else 0

        # Calcular descuentos totales
        total_descuentos = filtered_df['Descuento'].sum()

        # Mostrar métricas en columnas
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric(label="Ventas", value=f"{format_chilean_number(total_revenue)} CLP")
        col2.metric(label="Ganancias", value=f"{format_chilean_number(total_profit)} CLP")
        col3.metric(label="Total de Pedidos", value=f"{format_chilean_number(total_orders)}")
        col4.metric(label="Valor Promedio por Pedido", value=f"{format_chilean_number(average_order_value)} CLP")
        col5.metric(label="Ganancia Promedio por Pedido", value=f"{format_chilean_number(average_profit_per_order)} CLP")
        col6.metric(label="Margen", value=f"{overall_profit_margin:.2f} %")

        # Mostrar total de descuentos
        st.metric("Descuentos Aplicados", f"{format_chilean_number(total_descuentos)} CLP")

        # Calcular ganancia después de impuestos
        tax_rate = 0.19
        filtered_df['Ganancia Después de Impuestos'] = filtered_df['Ganancia'] * (1 - tax_rate)

        # Calcular margen después de impuestos
        total_profit_after_tax = filtered_df['Ganancia Después de Impuestos'].sum()
        overall_margin_after_tax = (total_profit_after_tax / total_revenue) * 100 if total_revenue > 0 else 0

        # Métrica adicional para ganancia después de impuestos
        st.subheader('Después de Impuestos')
        st.metric("Ganancias Después de Impuestos (19%)", f"{format_chilean_number(total_profit_after_tax)} CLP")
        st.metric("Margen Después de Impuestos", f"{overall_margin_after_tax:.2f} %")

        # Espacio antes de la sección de Ventas
        st.write("")
        st.write("")
        st.write("")
        st.write("")  # Añadido para más espacio

        # Tendencias de Ventas
        st.subheader('Ventas')

        # Agregación de datos para tendencias
        sales_trends = filtered_df.resample('M', on='Fecha').agg({'Total': 'sum', 'Ganancia': 'sum', 'Ganancia Después de Impuestos': 'sum'}).reset_index()
        sales_trends['Month'] = sales_trends['Fecha'].dt.to_period('M').astype(str)

        if not sales_trends.empty:
            # Gráfico de líneas para Ventas y Ganancia Después de Impuestos
            fig_sales_trends = px.line(sales_trends, x='Month', y=['Total', 'Ganancia Después de Impuestos'],
                                       labels={'value': 'Monto', 'Month': 'Fecha'},
                                       title='Ventas vs Ganancias Después de Impuestos',
                                       template='plotly_dark')
            fig_sales_trends.for_each_trace(lambda t: t.update(name='Ventas' if t.name == 'Total' else 'Ganancias Después de Impuestos'))

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
                        y=sales_trends[sales_trends['Month'] == mid_month]['Total'].mean(),  # Posición Y para la anotación
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
            product_performance = filtered_df.groupby(['Nombre del Producto', 'SKU del Producto', 'Categoria']).agg({
                'Cantidad de Productos': 'sum',
                'Total': 'sum',
                'Ganancia': 'sum'
            }).reset_index()
            product_performance['Precio Promedio'] = product_performance['Total'] / product_performance['Cantidad de Productos']
            product_performance['Rentabilidad (%)'] = (product_performance['Ganancia'] / product_performance['Total']) * 100

            if not product_performance.empty:
                # Agregación de datos para productos más vendidos por categoría
                category_sales = product_performance.groupby(['Categoria', 'SKU del Producto']).agg({
                    'Cantidad de Productos': 'sum'
                }).reset_index()
                
                category_totals = category_sales.groupby('Categoria').agg({
                    'Cantidad de Productos': 'sum'
                }).reset_index()
                category_totals = category_totals.rename(columns={'Cantidad de Productos': 'Total Vendido'})
                
                # Crear gráfico de barras apiladas para mostrar productos más vendidos dentro de cada categoría
                fig_top_selling_products = px.bar(category_sales,
                                                 x='Categoria',
                                                 y='Cantidad de Productos',
                                                 color='SKU del Producto',
                                                 title='Productos Más Vendidos por Categoría',
                                                 labels={'Cantidad de Productos': 'Cantidad Vendida'},
                                                 template='plotly_dark',
                                                 color_discrete_sequence=px.colors.qualitative.Plotly)
                
                fig_top_selling_products.update_layout(barmode='stack', xaxis_title='Categoría', yaxis_title='Cantidad Vendida')
                st.plotly_chart(fig_top_selling_products)

                # Gráfico de dispersión para Rentabilidad de Productos
                fig_product_profitability = px.scatter(product_performance, x='Precio Promedio', y='Rentabilidad (%)',
                                                       size='Total', color='Nombre del Producto',
                                                       hover_name='Nombre del Producto',
                                                       title='Rentabilidad de Productos',
                                                       template='plotly_dark')
                fig_product_profitability.update_layout(xaxis_title='Precio Promedio', yaxis_title='Rentabilidad (%)')
                st.plotly_chart(fig_product_profitability)
            else:
                st.write("No hay datos suficientes para mostrar el desempeño de productos.")
        except KeyError as e:
            st.error(f"Error al agrupar los datos: {e}")

        # Análisis Detallado por Producto
        st.subheader('Análisis Detallado por Producto')
        producto_seleccionado = st.selectbox('Selecciona un Producto:', filtered_df['Nombre del Producto'].unique())
        producto_df = filtered_df[filtered_df['Nombre del Producto'] == producto_seleccionado]

        if not producto_df.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Vendido", f"{format_chilean_number(producto_df['Total'].sum())} CLP")
            col2.metric("Cantidad Vendida", f"{format_chilean_number(producto_df['Cantidad de Productos'].sum())}")
            col3.metric("Beneficio Total", f"{format_chilean_number(producto_df['Ganancia'].sum())} CLP")

            # Gráfico: Ventas del Producto Seleccionado a lo Largo del Tiempo
            fig_producto = px.line(producto_df, x='Fecha', y='Total', 
                                  title=f'Ventas de {producto_seleccionado} a lo Largo del Tiempo',
                                  template='plotly_dark')
            st.plotly_chart(fig_producto)
        else:
            st.write("No hay datos disponibles para el producto seleccionado.")
