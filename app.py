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
    url_categorias = f"https://raw.githubusercontent.com/HUHU0101123/og-app/main/importaciones.csv?v={version}"
    df_categorias = pd.read_csv(url_categorias)
    return df_main, df_categorias

# Preprocesamiento de datos
def preprocess_data(df_main, df_categorias):
    df_main['Fecha'] = pd.to_datetime(df_main['Fecha']).dt.date
    df_categorias['Fecha_Importacion'] = pd.to_datetime(df_categorias['Fecha_Importacion']).dt.date

    df = pd.merge(df_main, df_categorias[['SKU del Producto', 'PRODUCTO']], on='SKU del Producto', how='left')

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

# Verificar columnas disponibles
st.write("Columnas disponibles en el DataFrame filtrado:", filtered_df.columns)

# Gráfico de Top Productos Más Vendidos
st.header("Top 10 Productos Más Vendidos")

# Verificar si la columna 'PRODUCTO' existe
if 'PRODUCTO' in filtered_df.columns:
    top_products = filtered_df.groupby('PRODUCTO')['Cantidad de Productos'].sum().sort_values(ascending=False).head(10)
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
else:
    st.error("No se pudo generar el gráfico de Top 10 Productos Más Vendidos debido a la falta de la columna 'PRODUCTO'.")


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
