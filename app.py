import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Cargar el archivo CSV principal desde GitHub
url_main = "https://raw.githubusercontent.com/HUHU0101123/og-app/main/datasource.csv"
df_main = pd.read_csv(url_main)

# Cargar el archivo CSV de categorías desde GitHub
url_categorias = "https://raw.githubusercontent.com/HUHU0101123/og-app/main/categorias.csv"
df_categorias = pd.read_csv(url_categorias)

# Limpiar nombres de columnas
df_main.columns = df_main.columns.str.strip()
df_categorias.columns = df_categorias.columns.str.strip()

# Convertir la columna 'Fecha' a tipo datetime
df_main['Fecha'] = pd.to_datetime(df_main['Fecha'], errors='coerce')

# Convertir columnas a tipo numérico (si es necesario)
df_main['Precio del Producto'] = df_main['Precio del Producto'].str.replace(',', '.').astype(float)
df_main['Cantidad de Productos'] = pd.to_numeric(df_main['Cantidad de Productos'], errors='coerce')
df_main['Descuento del producto'] = df_main['Descuento del producto'].str.replace(',', '.').astype(float)
df_main['Rentabilidad del producto'] = pd.to_numeric(df_main['Rentabilidad del producto'], errors='coerce')

# Mostrar los datos iniciales para diagnóstico
st.write("Primeras filas del DataFrame Principal:")
st.write(df_main.head())

st.write("Columnas del DataFrame Principal:")
st.write(df_main.columns)

st.write("Tipos de datos del DataFrame Principal:")
st.write(df_main.dtypes)

st.write("Fechas mínimas y máximas en el DataFrame Principal:")
st.write(df_main['Fecha'].min(), df_main['Fecha'].max())

# Mostrar los datos iniciales para diagnóstico de categorias.csv
st.write("Primeras filas del DataFrame de Categorías:")
st.write(df_categorias.head())

st.write("Columnas del DataFrame de Categorías:")
st.write(df_categorias.columns)

st.write("Tipos de datos del DataFrame de Categorías:")
st.write(df_categorias.dtypes)

# Supongamos que la columna de clave para unir es 'SKU del Producto'
df_merged = pd.merge(df_main, df_categorias, how='left', left_on='SKU del Producto', right_on='SKU del Producto')

# Agrupar las filas de cada pedido
df_merged['Precio del Producto'] = df_merged.groupby('ID')['Precio del Producto'].transform(lambda x: x.ffill())
df_merged['Rentabilidad del producto'] = df_merged.groupby('ID')['Rentabilidad del producto'].transform(lambda x: x.ffill())
df_merged['Descuento del producto'] = df_merged.groupby('ID')['Descuento del producto'].transform(lambda x: x.ffill())
df_merged['Nombre del método de envío'] = df_merged.groupby('ID')['Nombre del método de envío'].transform(lambda x: x.ffill())

# Crear una nueva columna 'Total' calculada
df_merged['Total'] = df_merged['Cantidad de Productos'] * df_merged['Precio del Producto']

# Crear una nueva columna 'Total Final' considerando el descuento y el costo de envío
df_merged['Total Final'] = df_merged['Total'] - df_merged['Descuento del producto']

# Restar el costo de envío si el método de entrega es "Despacho Santiago (RM) a domicilio"
df_merged['Total Final'] = df_merged.apply(
    lambda row: row['Total Final'] - 2990 if row['Nombre del método de envío'] == "Despacho Santiago (RM) a domicilio" else row['Total Final'],
    axis=1
)

# Agregar los detalles de las órdenes (sumar los totales por ID)
order_summary = df_merged.groupby('ID').agg({
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
start_date = st.sidebar.date_input('Fecha de Inicio', df_main['Fecha'].min().date())
# Selector de fecha final
end_date = st.sidebar.date_input('Fecha de Fin', df_main['Fecha'].max().date())

# Convertir las fechas seleccionadas a tipo datetime para comparación
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

# Asegúrate de que la fecha de fin sea después de la fecha de inicio
if start_date > end_date:
    st.sidebar.error('La fecha de fin debe ser posterior a la fecha de inicio.')
else:
    # Filtro por tipo de venta
    tipo_venta = st.sidebar.selectbox('Tipo de Venta', ['Todo', 'Venta al Detalle', 'Venta Mayorista'])

    # Mostrar el DataFrame filtrado sin filtros aplicados para diagnóstico
    st.write("Datos sin filtros:")
    st.write(order_summary)

    # Filtrar por fecha y tipo de venta
    filtered_df = order_summary[(order_summary['ID'].isin(df_main[(df_main['Fecha'] >= start_date) & (df_main['Fecha'] <= end_date)]['ID']))]
    if tipo_venta != 'Todo':
        filtered_df = filtered_df[filtered_df['Tipo de Venta'] == tipo_venta]

    # Mostrar datos filtrados para diagnóstico
    st.write("Datos filtrados:")
    st.write(filtered_df)

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
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric(label="Ganancia Después de Impuestos", value=f"{format_chilean_number(total_profit_after_tax, 0)} CLP")
        col2.metric(label="Margen Después de Impuestos", value=format_percentage(overall_margin_after_tax))

        # Visualización de tendencias de ventas
        st.subheader('Tendencias de Ventas y Ganancias')

        # Agrupar datos por mes
        sales_trends = filtered_df.groupby(filtered_df['Fecha'].dt.to_period('M')).agg({
            'Total Final': 'sum',
            'Ganancia': 'sum'
        }).reset_index()

        # Convertir periodos a fechas
        sales_trends['Month'] = sales_trends['Fecha'].dt.to_timestamp()

        # Crear gráficos de tendencias
        fig_sales_trends = px.line(sales_trends, x='Month', y=['Total Final', 'Ganancia'], labels={'Month': 'Fecha'}, title='Ventas y Ganancias Después de Impuestos por Mes')

        if len(sales_trends) > 1:
            mid_index = len(sales_trends) // 2
            mid_x = sales_trends['Month'].iloc[mid_index]

            fig_sales_trends.update_layout(
                xaxis=dict(
                    tickvals=sales_trends['Month'].tolist(),
                    ticktext=sales_trends['Month'].tolist(),
                    title='Fecha',
                    showgrid=True,
                    zeroline=False
                ),
                yaxis=dict(
                    title='Monto',
                    showgrid=True,
                    zeroline=False
                ),
                title={
                    'text': 'Ventas y Ganancias Después de Impuestos por Mes',
                    'x': 0.5
                },
                shapes=[
                    dict(
                        type='line',
                        x0=mid_x,
                        x1=mid_x,
                        y0=0,
                        y1=1,
                        yref='paper',
                        line=dict(color='red', width=2, dash='dash')
                    )
                ]
            )

            st.plotly_chart(fig_sales_trends)
        else:
            st.write("No hay datos suficientes para mostrar tendencias de ventas.")
