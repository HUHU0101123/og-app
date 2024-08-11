import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuración de la página (debe ser la primera llamada a Streamlit)
st.set_page_config(page_title="Dashboard de Ventas", layout="wide")

# Función para formatear números al estilo chileno
def format_chilean_currency(value, is_percentage=False):
    """Formatea un número al estilo chileno con punto para miles y coma para decimales.
    Si is_percentage es True, se formatea como porcentaje."""
    if is_percentage:
        return f"{value:.2f}%".replace('.', ',')
    else:
        return f"${value:,.0f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# Cargar los archivos CSV desde GitHub sin caché
def load_data():
    # Añadir un parámetro de versión basado en la fecha actual para evitar caché
    version = datetime.now().strftime("%Y%m%d%H%M%S")
    url_main = f"https://raw.githubusercontent.com/HUHU0101123/og-app/main/datasource.csv?v={version}"
    df_main = pd.read_csv(url_main)
    url_categorias = f"https://raw.githubusercontent.com/HUHU0101123/og-app/main/categorias.csv?v={version}"
    df_categorias = pd.read_csv(url_categorias)
    return df_main, df_categorias

# Preprocesamiento de datos
def preprocess_data(df_main, df_categorias):
    # Convertir la columna 'Fecha' a datetime
    df_main['Fecha'] = pd.to_datetime(df_main['Fecha']).dt.date
    
    # Unir los dataframes para agregar las categorías
    df = pd.merge(df_main, df_categorias, on='SKU del Producto', how='left')
    
    # Llenar los valores NaN en las columnas relevantes
    columns_to_fill = ['Estado del Pago', 'Fecha', 'Moneda', 'Región de Envío', 'Nombre del método de envío', 'Cupones']
    df[columns_to_fill] = df.groupby('ID')[columns_to_fill].fillna(method='ffill')
    
    # Convertir columnas numéricas
    numeric_columns = ['Cantidad de Productos', 'Precio del Producto', 'Margen del producto (%)', 'Descuento del producto']
    for col in numeric_columns:
        if df[col].dtype == 'object':
            df[col] = df[col].str.replace(',', '.').astype(float)
        else:
            df[col] = df[col].astype(float)
    
    # Calcular el total de productos por compra
    df['Total Productos'] = df.groupby('ID')['Cantidad de Productos'].transform('sum')
    
    # Clasificar el tipo de venta
    df['Tipo de Venta'] = df['Total Productos'].apply(lambda x: 'Mayorista' if x >= 6 else 'Detalle')
    
    # Calcular las ventas netas
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

# Aplicar filtros
mask = (df['Fecha'] >= date_range[0]) & (df['Fecha'] <= date_range[1])
if categories:
    mask &= df['Categoria'].isin(categories)
if sale_type:
    mask &= df['Tipo de Venta'].isin(sale_type)
if order_ids:
    order_id_list = [int(id.strip()) for id in order_ids.split(',')]
    mask &= df['ID'].isin(order_id_list)
filtered_df = df[mask]

# Ventas Totales
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
        <p style='font-size:10px; color: black;'>Ingresos totales antes de descuentos.</p>
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
        <p style='font-size:10px; color: black;'>Ganancia antes de impuestos.</p>
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
        <p style='font-size:10px; color: black;'>Ganancia bruta menos impuestos del 19%.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Margen Bruto
col4.markdown(
    f"""
    <div style="background-color: #D3D3D3; padding: 10px; border-radius: 5px; text-align: center;">
        <strong style="color: black;">Margen Bruto</strong><br>
        <span style="color: black;">{format_chilean_currency(margen_bruto, is_percentage=True)}</span>
        <p style='font-size:10px; color: black;'>Porcentaje de ganancia bruta respecto a ventas netas.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Gráfico de líneas para Ventas Totales, Ventas Netas y Ganancia Neta
daily_sales = filtered_df.groupby('Fecha').agg(
    Ventas_Totales=('Precio del Producto', 'sum'),
    Ventas_Netas=('Ventas Netas', 'sum')
).reset_index()

# Calcular la Ganancia Neta diaria
daily_sales['Ganancia_Neta'] = daily_sales['Ventas_Netas'] - (daily_sales['Ventas_Netas'] * 0.19)  # Aplicar impuestos del 19%

# Crear un gráfico de líneas para Ventas Totales, Ventas Netas y Ganancia Neta
fig = px.line(
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

# Tabla de datos
st.subheader("Datos Detallados")
st.dataframe(filtered_df)
