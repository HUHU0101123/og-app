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
date_range = st.sidebar.date_input("Rango de fechas", [df['Fecha'].min(), df['Fecha'].max()])
categories = st.sidebar.multiselect("Categorías", options=df['Categoria'].unique())
sale_type = st.sidebar.multiselect("Tipo de Venta", options=df['Tipo de Venta'].unique())
order_ids = st.sidebar.text_input("IDs de Orden de Compra (separados por coma)", "")
regions = st.sidebar.multiselect("Región de Envío", options=df['Región de Envío'].unique())  # Filtro para Región de Envío

# Aplicar filtros
mask = (df['Fecha'] >= date_range[0]) & (df['Fecha'] <= date_range[1])
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

# Ganancia Neta
col3.markdown(
    f"""
    <div style="background-color: #FFCCCB; padding: 10px; border-radius: 5px; text-align: center;">
        <strong style="color: black;">Ganancia Neta</strong><br>
        <span style="color: black;">{format_chilean_currency(beneficio_bruto_despues_impuestos)}</span>
        <p style="font-size:10px; color: black;">Es el dinero que realmente ganaste. Es tuyo.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Margen
col4.markdown(
    f"""
    <div style="background-color: #FFCCCB; padding: 10px; border-radius: 5px; text-align: center;">
        <strong style="color: black;">Margen</strong><br>
        <span style="color: black;">{format_chilean_currency(margen_bruto, is_percentage=True)}</span>
        <p style="font-size:10px; color: black;">% que te queda de las ventas después de pagar la inversión e impuestos.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Añadir un espacio antes de la nueva fila
st.markdown("<br>", unsafe_allow_html=True)

# Nueva fila para la Cantidad Total de Productos y Descuento Promedio %
col1, col2, col3, col4 = st.columns(4)

# Cantidad Total de Productos
col1.markdown(
    f"""
    <div style="background-color: #D3D3D3; padding: 10px; border-radius: 5px; text-align: center;">
        <strong style="color: black;">Cantidad Total de Productos</strong><br>
        <span style="color: black;">{int(filtered_df['Cantidad de Productos'].sum())}</span>
        <p style='font-size:10px; color: black;'>Total de productos vendidos.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Descuento Promedio %
col2.markdown(
    f"""
    <div style="background-color: #D3D3D3; padding: 10px; border-radius: 5px; text-align: center;">
        <strong style="color: black;">Descuento Promedio %</strong><br>
        <span style="color: black;">{(filtered_df['Descuento del producto'].sum() / ventas_totales * 100):.2f}%</span>
        <p style='font-size:10px; color: black;'>Porcentaje promedio de descuento aplicado.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Dejar las otras columnas vacías
col3.markdown("")
col4.markdown("")

# Gráficos
col1, col2 = st.columns(2)

with col1:
    # Calcular las ventas netas y cantidad de productos por SKU y categoría
    sales_data = filtered_df.groupby(['Categoria', 'SKU del Producto']).agg(
        Ventas_Netas=('Ventas Netas', 'sum'),
        Cantidad_Productos=('Cantidad de Productos', 'sum')
    ).reset_index()
    
    # Crear un gráfico de barras para ventas netas por categoría y SKU
    fig = px.bar(
        sales_data,
        x='Categoria',
        y='Ventas_Netas',
        color='SKU del Producto',
        title="Ventas Netas por Categoría y SKU",
        labels={'Ventas_Netas': 'Ventas Netas'},
        hover_data={'SKU del Producto': True, 'Cantidad_Productos': True}
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Ventas diarias: Ventas Totales, Ventas Netas y Ganancia Neta
    daily_sales = filtered_df.groupby('Fecha').agg(
        Ventas_Totales=('Precio del Producto', lambda x: (x * filtered_df.loc[x.index, 'Cantidad de Productos']).sum()),
        Ventas_Netas=('Ventas Netas', 'sum')
    ).reset_index()

    # Calcular la Ganancia Neta diaria
    daily_sales['Ganancia_Neta'] = daily_sales['Ventas_Netas'] - (daily_sales['Ventas_Netas'] * 0.19)

    if len(daily_sales) > 1:
        # Crear un gráfico de líneas para múltiples días
        fig = px.line(
            daily_sales,
            x='Fecha',
            y=['Ventas_Totales', 'Ventas_Netas', 'Ganancia_Neta'],
            labels={'value': 'Monto', 'variable': 'Métrica'},
            title="Desarrollo Diario de Ventas Totales, Ventas Netas y Ganancia Neta"
        )
    else:
        # Crear un gráfico de dispersión para un solo día
        fig = px.scatter(
            daily_sales,
            x='Fecha',
            y=['Ventas_Totales', 'Ventas_Netas', 'Ganancia_Neta'],
            labels={'value': 'Monto', 'variable': 'Métrica'},
            title="Desarrollo Diario de Ventas Totales, Ventas Netas y Ganancia Neta"
        )

    # Configurar el formato de fecha en el eje X
    fig.update_xaxes(
        tickformat="%d-%m-%Y",  # Formato de fecha: día-mes-año
        title="Fecha"
    )

    st.plotly_chart(fig, use_container_width=True)

# Top productos vendidos
top_products = filtered_df.groupby('SKU del Producto')['Cantidad de Productos'].sum().sort_values(ascending=False).head(10)
fig = px.bar(top_products, x=top_products.index, y=top_products.values, title="Top 10 Productos Más Vendidos")
st.plotly_chart(fig, use_container_width=True)

# Descuentos por categoría
discounts_by_category = filtered_df.groupby('Categoria')['Descuento del producto'].sum().sort_values(ascending=False)
fig = px.bar(discounts_by_category, x=discounts_by_category.index, y=discounts_by_category.values, title="Descuentos por Categoría")
st.plotly_chart(fig, use_container_width=True)

# Tabla de datos
st.subheader("Datos Detallados")
st.dataframe(filtered_df)






@st.cache_data
def load_importaciones():
    version = datetime.now().strftime("%Y%m%d%H%M%S")
    url_importaciones = f"https://raw.githubusercontent.com/HUHU0101123/og-app/main/importaciones.csv?v={version}"
    df_importaciones = pd.read_csv(url_importaciones)
    
    # Limpiar los nombres de las columnas
    df_importaciones.columns = df_importaciones.columns.str.strip().str.upper().str.replace(' ', '_')
    
    # Renombrar las columnas
    df_importaciones = df_importaciones.rename(columns={
        'FECHA_IMPORTACION': 'fecha_importacion',
        'CATEGORIA': 'Categoria',
        'STOCK_INICIAL': 'cantidad'
    })
    
    # Asegurarse de que la fecha_importacion sea de tipo date
    df_importaciones['fecha_importacion'] = pd.to_datetime(df_importaciones['fecha_importacion']).dt.date
    
    return df_importaciones

# Cargar los datos de importaciones
df_importaciones = load_importaciones()

# Verificar si df_importaciones tiene datos
if df_importaciones.empty:
    st.warning("No se pudieron cargar datos de importaciones.")
else:
    # Mostrar la tabla de importaciones
    st.subheader("Resumen de Importaciones")

    # Convertir fecha_importacion a string antes de agrupar
    df_importaciones['fecha_importacion'] = df_importaciones['fecha_importacion'].astype(str)

    # Agrupar por fecha de importación y categoría
    importaciones_agrupadas = df_importaciones.groupby(['fecha_importacion', 'Categoria'])['cantidad'].sum().reset_index()

    # Crear un gráfico de barras apiladas
    fig = px.bar(importaciones_agrupadas, 
                 y='fecha_importacion', 
                 x='cantidad',
                 color='Categoria',
                 title="Importaciones por Fecha y Categoría",
                 labels={'cantidad': 'Cantidad de Prendas', 'fecha_importacion': 'Fecha de Importación', 'Categoria': 'Categoría'},
                 orientation='h')

    # Añadir una línea vertical en x=0 para representar la cantidad vendida
    fig.add_vline(x=0, line_width=2, line_dash="dash", line_color="white")
    
    # Añadir una anotación para el texto "Cantidad vendida 0%"
    fig.add_annotation(
        x=0,
        y=1.02,  # Posición ligeramente por encima del gráfico
        xref="x",
        yref="paper",
        text="Cantidad vendida 0%",
        showarrow=False,
        font=dict(size=12, color="white"),
        align="center",
    )

    fig.update_layout(
        yaxis_title="Fecha de Importación",
        xaxis_title="Cantidad de Prendas",
        barmode='stack',
        yaxis={'type': 'category'},  # Esto fuerza a tratar las fechas como categorías discretas
        xaxis=dict(
            range=[min(importaciones_agrupadas['cantidad'].min() * 1.1, -10), importaciones_agrupadas['cantidad'].max() * 1.1]
        )  # Ajusta el rango del eje x para que la línea sea visible
    )

    st.plotly_chart(fig, use_container_width=True)







#Segundo Grafico

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
            orientation='h'
        ))

        # Add the 'cantidad vendida' line at x=0
        fig.add_trace(go.Scatter(
            x=[0],  # X position of the line
            y=[row['Categoria']],  # Y position of the line
            mode='lines+text',
            line=dict(color='red', dash='dash'),
            name='Cantidad Vendida (0%)',
            text=['0%'],  # Text to display on the line
            textposition='top right',
            showlegend=False
        ))

    # Update layout with annotation
    fig.update_layout(
        title=f"Importaciones por Categoría para la Fecha: {fecha_seleccionada}",
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
                text="La línea roja indica la 'Cantidad Vendida' al 0% para cada categoría.",
                showarrow=False,
                font=dict(size=12, color="black"),
                align="center",
                bgcolor="rgba(255, 255, 255, 0.7)"
            ),
            dict(
                x=1,
                y=-0.5,  # Position annotation below the chart
                xref='x',
                yref='paper',
                text="Nota: La línea roja representa la 'Cantidad Vendida' (0%).",
                showarrow=False,
                font=dict(size=12, color="black"),
                align="center",
                bgcolor="rgba(255, 255, 255, 0.7)"
            )
        ]
    )

    st.plotly_chart(fig, use_container_width=True)



























def create_nested_data(df):
    nested_data = []
    for fecha in df['fecha_importacion'].unique():
        fecha_data = df[df['fecha_importacion'] == fecha]
        total_fecha = fecha_data['cantidad'].sum()
        
        # Agrupar por categoría y sumar las cantidades
        grouped_data = fecha_data.groupby('Categoria').agg({'cantidad': 'sum'}).reset_index()

        nested_data.append({
            "Fecha": fecha,
            "Total": total_fecha,
            "Detalles": grouped_data
        })
    
    return nested_data

nested_data = create_nested_data(df_importaciones)

st.markdown("**Detalle de Importaciones por Fecha**")

# Mostrar los datos de manera expandible y ordenada
for item in nested_data:
    with st.expander(f"Fecha: {item['Fecha']}  |  **Total: {item['Total']}** unidades"):
        st.markdown(f"**Fecha de Importación:** `{item['Fecha']}`")
        st.markdown(f"**Total de Unidades Importadas:** `{item['Total']}`")

        # Mostrar detalles en una tabla
        st.markdown("**Desglose por Categoría:**")
        detalles_df = item["Detalles"].reset_index(drop=True)
        detalles_df.columns = ["Categoría", "Cantidad"]

        # Aplicar estilo al dataframe de detalles
        styled_table = detalles_df.style.set_properties(**{
            'background-color': '#f5f5f5',
            'color': '#333',
            'border-color': '#ffffff',
            'border-width': '1px',
            'border-style': 'solid',
            'font-size': '14px',
            'text-align': 'left'
        })
        st.dataframe(styled_table, use_container_width=True)

st.markdown("___")












