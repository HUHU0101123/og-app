import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go

# Configuración de la página
st.set_page_config(page_title="Dashboard de Ventas", layout="wide")

# Función para formatear números al estilo chileno
def format_chilean_currency(value, is_percentage=False):
    if is_percentage:
        return f"{value:.2f}%".replace('.', ',')
    else:
        return f"${value:,.0f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# Cargar los archivos CSV desde GitHub sin caché
def load_data():
    version = datetime.now().strftime("%Y%m%d%H%M%S")
    url_main = f"https://raw.githubusercontent.com/HUHU0101123/og-app/main/datasource.csv?v={version}"
    df_main = pd.read_csv(url_main)
    url_categorias = f"https://raw.githubusercontent.com/HUHU0101123/og-app/main/categorias.csv?v={version}"
    df_categorias = pd.read_csv(url_categorias)
    return df_main, df_categorias

# Preprocesamiento de datos
def preprocess_data(df_main, df_categorias):
    df_main['Fecha'] = pd.to_datetime(df_main['Fecha']).dt.date
    df = pd.merge(df_main, df_categorias, on='SKU del Producto', how='left')
    columns_to_fill = ['Estado del Pago', 'Fecha', 'Moneda', 'Región de Envío', 'Nombre del método de envío', 'Cupones']
    df[columns_to_fill] = df.groupby('ID')[columns_to_fill].fillna(method='ffill')
    numeric_columns = ['Cantidad de Productos', 'Precio del Producto', 'Margen del producto (%)', 'Descuento del producto']
    for col in numeric_columns:
        if df[col].dtype == 'object':
            df[col] = df[col].str.replace(',', '.').astype(float)
        else:
            df[col] = df[col].astype(float)
    df['Total Productos'] = df.groupby('ID')['Cantidad de Productos'].transform('sum')
    df['Tipo de Venta'] = df['Total Productos'].apply(lambda x: 'Mayorista' if x >= 6 else 'Detalle')
    df['Ventas Netas'] = (df['Precio del Producto'] - df['Descuento del producto']) * df['Cantidad de Productos']
    return df

# Cargar y preprocesar los datos
df_main, df_categorias = load_data()
df = preprocess_data(df_main, df_categorias)

# Título de la aplicación
st.title("Dashboard de Ventas")

# Filtros en la barra lateral
st.sidebar.header("Filtros")

# Agregar el filtro de Estado del Pago en la parte superior
payment_status = st.sidebar.multiselect("Estado del Pago", options=df['Estado del Pago'].unique())
date_range = st.sidebar.date_input("Rango de fechas", [df['Fecha'].min(), df['Fecha'].max()])
categories = st.sidebar.multiselect("Categorías", options=df['Categoria'].unique())
sale_type = st.sidebar.multiselect("Tipo de Venta", options=df['Tipo de Venta'].unique())
order_ids = st.sidebar.text_input("IDs de Orden de Compra (separados por coma)", "")
regions = st.sidebar.multiselect("Región de Envío", options=df['Región de Envío'].unique())  # Filtro para Región de Envío

# Aplicar filtros
mask = (df['Fecha'] >= date_range[0]) & (df['Fecha'] <= date_range[1])
if payment_status:
    mask &= df['Estado del Pago'].isin(payment_status)
if categories:
    mask &= df['Categoria'].isin(categories)
if sale_type:
    mask &= df['Tipo de Venta'].isin(sale_type)
if order_ids:
    order_id_list = [int(id.strip()) for id in order_ids.split(',')]
    mask &= df['ID'].isin(order_id_list)
if regions:  # Filtrar por Región de Envío
    mask &= df['Región de Envío'].isin(regions)

filtered_df = df[mask]

# Calcular las ventas totales
ventas_totales = (filtered_df['Precio del Producto'] * filtered_df['Cantidad de Productos']).sum()

# Calcular ventas netas después de impuestos
ventas_netas = filtered_df['Ventas Netas'].sum()
ventas_netas_despues_impuestos = ventas_netas * (1 - 0.19)

# Calcular el costo del producto
filtered_df['Precio Neto del Producto'] = filtered_df['Precio del Producto'] - filtered_df['Descuento del producto']
filtered_df['Costo del Producto'] = filtered_df['Precio Neto del Producto'] * (1 - filtered_df['Margen del producto (%)'] / 100)
costo_total = (filtered_df['Costo del Producto'] * filtered_df['Cantidad de Productos']).sum()

# Calcular el beneficio bruto
beneficio_bruto = ventas_netas - costo_total

# Calcular el beneficio bruto después de impuestos
beneficio_bruto_despues_impuestos = beneficio_bruto * (1 - 0.19)

# Calcular el margen
margen_bruto = (beneficio_bruto / ventas_netas) * 100

# Resumen de Ventas
st.header("Resumen de Ventas")
col1, col2, col3, col4 = st.columns(4)

# Ventas Totales
col1.markdown(
    f"""
    <div style="background-color: #D3D3D3; padding: 10px; border-radius: 5px; text-align: center;">
        <strong style="color: black;">Ventas Totales</strong><br>
        <span style="color: black;">{format_chilean_currency(ventas_totales)}</span>
        <p style='font-size:10px; color: black;'>Ingresos totales antes de descuentos y ajustes.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Descuentos Aplicados
col2.markdown(
    f"""
    <div style="background-color: #D3D3D3; padding: 10px; border-radius: 5px; text-align: center;">
        <strong style="color: black;">Descuentos Aplicados</strong><br>
        <span style="color: black;">{format_chilean_currency(filtered_df['Descuento del producto'].sum())}</span>
        <p style='font-size:10px; color: black;'>Total de descuentos otorgados en ventas.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Ventas Netas
col3.markdown(
    f"""
    <div style="background-color: #D3D3D3; padding: 10px; border-radius: 5px; text-align: center;">
        <strong style="color: black;">Ventas Netas</strong><br>
        <span style="color: black;">{format_chilean_currency(ventas_netas)}</span>
        <p style='font-size:10px; color: black;'>Ventas totales menos descuentos.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Ventas Netas Después de Impuestos
col4.markdown(
    f"""
    <div style="background-color: #D3D3D3; padding: 10px; border-radius: 5px; text-align: center;">
        <strong style="color: black;">Ventas Netas Después de Impuestos</strong><br>
        <span style="color: black;">{format_chilean_currency(ventas_netas_despues_impuestos)}</span>
        <p style='font-size:10px; color: black;'>Ventas netas menos impuestos del 19%.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Métricas Adicionales
st.header("Métricas Adicionales")
col1, col2, col3, col4 = st.columns(4)

# Cantidad de Órdenes
col1.markdown(
    f"""
    <div style="background-color: #D3D3D3; padding: 10px; border-radius: 5px; text-align: center;">
        <strong style="color: black;">Cantidad de Órdenes</strong><br>
        <span style="color: black;">{filtered_df['ID'].nunique()}</span>
        <p style='font-size:10px; color: black;'>Total de órdenes procesadas.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Ganancia Bruta
col2.markdown(
    f"""
    <div style="background-color: #D3D3D3; padding: 10px; border-radius: 5px; text-align: center;">
        <strong style="color: black;">Ganancia Bruta</strong><br>
        <span style="color: black;">{format_chilean_currency(beneficio_bruto)}</span>
        <p style='font-size:10px; color: black;'>Ventas netas menos costos de adquisición del producto.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Ganancia Bruta Después de Impuestos
col3.markdown(
    f"""
    <div style="background-color: #D3D3D3; padding: 10px; border-radius: 5px; text-align: center;">
        <strong style="color: black;">Ganancia Bruta Después de Impuestos</strong><br>
        <span style="color: black;">{format_chilean_currency(beneficio_bruto_despues_impuestos)}</span>
        <p style='font-size:10px; color: black;'>Ganancia bruta después de impuestos del 19%.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Margen Bruto
col4.markdown(
    f"""
    <div style="background-color: #D3D3D3; padding: 10px; border-radius: 5px; text-align: center;">
        <strong style="color: black;">Margen Bruto</strong><br>
        <span style="color: black;">{margen_bruto:.2f}%</span>
        <p style='font-size:10px; color: black;'>Porcentaje de ganancia sobre las ventas netas.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Gráfico de Ventas por Categoría
st.header("Ventas por Categoría")
ventas_por_categoria = filtered_df.groupby('Categoria')['Ventas Netas'].sum().sort_values(ascending=False)
ventas_por_categoria_df = ventas_por_categoria.reset_index()
ventas_por_categoria_df.columns = ['Categoría', 'Ventas Netas']

fig_ventas_categoria = px.bar(
    ventas_por_categoria_df,
    x='Categoría',
    y='Ventas Netas',
    title="Ventas por Categoría",
    labels={'Ventas Netas': 'Ventas Netas'}
)

st.plotly_chart(fig_ventas_categoria, use_container_width=True)

# Gráfico de Top Productos Más Vendidos
st.header("Top 10 Productos Más Vendidos")
top_products = filtered_df.groupby('Producto')['Cantidad de Productos'].sum().sort_values(ascending=False).head(10)
top_products_df = top_products.reset_index()
top_products_df.columns = ['Producto', 'Cantidad Vendida']

fig_top_products = px.bar(
    top_products_df,
    x='Producto',
    y='Cantidad Vendida',
    title="Top 10 Productos Más Vendidos",
    labels={'Cantidad Vendida': 'Cantidad Vendida'}
)

st.plotly_chart(fig_top_products, use_container_width=True)

# Gráfico de Descuentos por Categoría
st.header("Descuentos por Categoría")
discounts_by_category = filtered_df.groupby('Categoria')['Descuento del producto'].sum().sort_values(ascending=False)
discounts_by_category_df = discounts_by_category.reset_index()
discounts_by_category_df.columns = ['Categoría', 'Descuento del Producto']

fig_discounts_category = px.bar(
    discounts_by_category_df,
    x='Categoría',
    y='Descuento del Producto',
    title="Descuentos por Categoría",
    labels={'Descuento del Producto': 'Descuento del Producto'}
)

st.plotly_chart(fig_discounts_category, use_container_width=True)


#Primer Grafico Importaciones

@st.cache_data
def load_importaciones():
    version = datetime.now().strftime("%Y%m%d%H%M%S")
    url_importaciones = f"https://raw.githubusercontent.com/HUHU0101123/og-app/main/importaciones.csv?v={version}"
    df_importaciones = pd.read_csv(url_importaciones)
    
    # Clean and rename columns
    df_importaciones.columns = df_importaciones.columns.str.strip().str.upper().str.replace(' ', '_')
    df_importaciones = df_importaciones.rename(columns={
        'FECHA_IMPORTACION': 'fecha_importacion',
        'CATEGORIA': 'Categoria',
        'STOCK_INICIAL': 'cantidad'
    })
    
    # Ensure fecha_importacion is of type date
    df_importaciones['fecha_importacion'] = pd.to_datetime(df_importaciones['fecha_importacion']).dt.date
    
    return df_importaciones

# Load importaciones data
df_importaciones = load_importaciones()

if df_importaciones.empty:
    st.warning("No se pudieron cargar datos de importaciones.")
else:
    st.subheader("Resumen de Importaciones")

    # Convert fecha_importacion to string before grouping
    df_importaciones['fecha_importacion'] = df_importaciones['fecha_importacion'].astype(str)

    # Add a filter for fecha_importacion
    fechas = df_importaciones['fecha_importacion'].unique()
    fecha_seleccionada = st.selectbox("Seleccionar Fecha de Importación", fechas)

    # Filter the data based on selected fecha_importacion
    df_filtrado = df_importaciones[df_importaciones['fecha_importacion'] == fecha_seleccionada]

    # Group by categoria
    importaciones_agrupadas = df_filtrado.groupby(['Categoria'])['cantidad'].sum().reset_index()

    # Create the bar chart
    fig = go.Figure()

    # Add bars for each category
    for _, row in importaciones_agrupadas.iterrows():
        fig.add_trace(go.Bar(
            x=[row['cantidad']],
            y=[row['Categoria']],
            name=row['Categoria'],
            orientation='h',
            hovertemplate=f'Total Importado: {row["cantidad"]}<br>Total Vendido %: 0%<extra></extra>'
        ))

        # Add the 'cantidad vendida' line at x=0
        fig.add_trace(go.Scatter(
            x=[0],  # X position of the line
            y=[row['Categoria']],  # Y position of the line
            mode='lines+text',
            line=dict(color='white', dash='dash'),
            name='Cantidad Vendida (0%)',
            text=['0%'],  # Text to display on the line
            textposition='top right',
            showlegend=False
        ))

    # Update layout with annotation
    fig.update_layout(
        title=f"Importaciones por Categoría y % Vendido",
        xaxis_title="Cantidad de Prendas",
        yaxis_title="Categoría",
        yaxis=dict(type='category'),
        xaxis=dict(
            range=[-10, importaciones_agrupadas['cantidad'].max() * 1.1]
        ),
        barmode='group',
        annotations=[
            dict(
                x=0,
                y=-0.5,  # Position annotation below the chart
                xref='x',
                yref='paper',
                text="La línea blanca indica la 'Cantidad Vendida' al 0% para cada categoría.",
                showarrow=False,
                font=dict(size=12, color="white"),
                align="center",
                bgcolor="rgba(0, 0, 0, 0.7)"
            ),
            dict(
                x=1,
                y=-0.5,  # Position annotation below the chart
                xref='x',
                yref='paper',
                text="Nota: La línea blanca representa la 'Cantidad Vendida' (0%).",
                showarrow=False,
                font=dict(size=12, color="white"),
                align="center",
                bgcolor="rgba(0, 0, 0, 0.7)"
            )
        ]
    )

    st.plotly_chart(fig, use_container_width=True)


#SEGUNDO GRAFICO
# Cargar los datos
try:
    df_importaciones = pd.read_csv('importaciones.csv')
except FileNotFoundError:
    st.error("No se pudo encontrar el archivo 'importaciones.csv'. Por favor, asegúrese de que el archivo existe en el directorio correcto.")
    st.stop()

# Reemplazar valores vacíos en la columna PRODUCTO con "Sin especificar"
df_importaciones['PRODUCTO'] = df_importaciones['PRODUCTO'].fillna('Sin especificar')

# Crear un filtro para SKU del Producto
skus = ['Todos'] + list(df_importaciones['SKU del Producto'].unique())
selected_sku = st.selectbox("Seleccione SKU del Producto", skus)

# Filtrar el dataframe basado en el SKU seleccionado
if selected_sku == 'Todos':
    df_filtered = df_importaciones
else:
    df_filtered = df_importaciones[df_importaciones['SKU del Producto'] == selected_sku]

# Agrupar los datos por CATEGORIA, PRODUCTO y calcular el STOCK INICIAL total
grouped_data = df_filtered.groupby(['CATEGORIA', 'PRODUCTO'])['STOCK INICIAL'].sum().reset_index()

# Calcular el total de STOCK INICIAL
total_stock = grouped_data['STOCK INICIAL'].sum()
st.markdown(f"**Total de Stock Inicial:** {total_stock}")

def create_nested_data(df):
    nested_data = []
    for fecha in df['Fecha_Importacion'].unique():
        fecha_data = df[df['Fecha_Importacion'] == fecha]
        total_fecha = fecha_data['STOCK INICIAL'].sum()
        
        # Agrupar por categoría, producto y sumar el STOCK INICIAL
        grouped_data = fecha_data.groupby(['CATEGORIA', 'PRODUCTO'])['STOCK INICIAL'].sum().reset_index()
        nested_data.append({
            "Fecha": fecha,
            "Total": total_fecha,
            "Detalles": grouped_data
        })
    
    return nested_data

nested_data = create_nested_data(df_filtered)

st.markdown("**Detalle de Importaciones por Fecha**")
# Mostrar los datos de manera expandible y ordenada
for item in nested_data:
    with st.expander(f"Fecha: {item['Fecha']}  |  **Total: {item['Total']}** unidades"):
        st.markdown(f"**Fecha de Importación:** `{item['Fecha']}`")
        st.markdown(f"**Total de Stock Inicial:** `{item['Total']}`")
        # Mostrar detalles en una tabla
        st.markdown("**Desglose por Categoría y Producto:**")
        detalles_df = item["Detalles"]
        st.dataframe(detalles_df, use_container_width=True)

st.markdown("___")
