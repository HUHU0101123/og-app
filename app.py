import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página (debe ser la primera llamada a Streamlit)
st.set_page_config(page_title="Dashboard de Ventas", layout="wide")

# Cargar los archivos CSV desde GitHub
@st.cache_data
def load_data():
    url_main = "https://raw.githubusercontent.com/HUHU0101123/og-app/main/datasource.csv"
    df_main = pd.read_csv(url_main)
    url_categorias = "https://raw.githubusercontent.com/HUHU0101123/og-app/main/categorias.csv"
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
    numeric_columns = ['Cantidad de Productos', 'Precio del Producto', 'Rentabilidad del producto', 'Margen del producto (%)', 'Descuento del producto']
    for col in numeric_columns:
        if df[col].dtype == 'object':
            df[col] = df[col].str.replace(',', '.').astype(float)
        else:
            df[col] = df[col].astype(float)
    
    # Calcular el total de productos por compra
    df['Total Productos'] = df.groupby('ID')['Cantidad de Productos'].transform('sum')
    
    # Clasificar el tipo de venta
    df['Tipo de Venta'] = df['Total Productos'].apply(lambda x: 'Mayorista' if x >= 6 else 'Detalle')
    
    # Ajustar el precio para envíos a domicilio en Santiago
    mask = df['Nombre del método de envío'] == 'Despacho Santiago (RM) a domicilio'
    df.loc[mask, 'Precio del Producto'] -= 2990 / df.loc[mask].groupby('ID')['Cantidad de Productos'].transform('sum')
    
    # Calcular las ventas netas
    df['Ventas Netas'] = df['Precio del Producto'] - df['Descuento del producto']
    
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

# Aplicar filtros
mask = (df['Fecha'] >= date_range[0]) & (df['Fecha'] <= date_range[1])
if categories:
    mask &= df['Categoria'].isin(categories)
if sale_type:
    mask &= df['Tipo de Venta'].isin(sale_type)
filtered_df = df[mask]

# Ajustar el cálculo de ventas totales para envíos a domicilio en Santiago
filtered_df['Ajuste Envío'] = 0
mask_envio = filtered_df['Nombre del método de envío'] == 'Despacho Santiago (RM) a domicilio'
filtered_df.loc[mask_envio, 'Ajuste Envío'] = 2990 / filtered_df.loc[mask_envio].groupby('ID')['Cantidad de Productos'].transform('sum')
ventas_totales = filtered_df['Precio del Producto'].sum() - filtered_df['Ajuste Envío'].sum()

# Calcular ventas netas después de impuestos
ventas_netas = ventas_totales - filtered_df['Descuento del producto'].sum()
ventas_netas_despues_impuestos = ventas_netas * (1 - 0.19)

# Calcular el beneficio bruto
beneficio_bruto = filtered_df['Rentabilidad del producto'].sum()

# Calcular el beneficio bruto después de impuestos
beneficio_bruto_despues_impuestos = beneficio_bruto * (1 - 0.19)

# Métricas principales
st.header("Resumen de Ventas")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Ventas Totales", f"${ventas_totales:,.0f}")
col1.markdown("<p style='font-size:10px;'>Ingresos totales antes de descuentos y ajustes.</p>", unsafe_allow_html=True)

col2.metric("Descuentos Aplicados", f"${filtered_df['Descuento del producto'].sum():,.0f}")
col2.markdown("<p style='font-size:10px;'>Total de descuentos otorgados en ventas.</p>", unsafe_allow_html=True)

col3.metric("Ventas Netas", f"${ventas_netas:,.0f}")
col3.markdown("<p style='font-size:10px;'>Ventas totales menos descuentos.</p>", unsafe_allow_html=True)

col4.metric("Ventas Netas Después de Impuestos", f"${ventas_netas_despues_impuestos:,.0f}")
col4.markdown("<p style='font-size:10px;'>Ventas netas menos impuestos del 19%.</p>", unsafe_allow_html=True)

# Calcular el margen
margen = (beneficio_bruto / ventas_netas) * 100

# Métricas adicionales
st.header("Métricas Adicionales")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Cantidad de Órdenes", filtered_df['ID'].nunique())
col1.markdown("<p style='font-size:10px;'>Total de órdenes procesadas.</p>", unsafe_allow_html=True)

col2.metric("Ganancia Bruta", f"${beneficio_bruto:,.0f}")
col2.markdown("<p style='font-size:10px;'>Ventas netas menos costos de adquisición del producto.</p>", unsafe_allow_html=True)

col3.metric("Ganancia Neta", f"${beneficio_bruto_despues_impuestos:,.0f}")
col3.markdown("<p style='font-size:10px;'>Es el dinero que realmente puedes guardar o reinvertir en tu negocio.</p>", unsafe_allow_html=True)

col4.metric("Margen", f"{margen:.2f}%")
col4.markdown("<p style='font-size:10px;'>Es el porcentaje del dinero que te queda de las ventas netas, después de pagar por los productos y los impuestos.</p>", unsafe_allow_html=True)

# Nueva fila para el Descuento Promedio
col5, = st.columns(1)  # Desempaqueta la lista de columnas

col5.metric("Descuento Promedio %", f"{(filtered_df['Descuento del producto'].sum() / ventas_totales * 100):.2f}%")
col5.markdown("<p style='font-size:10px;'>Porcentaje promedio de descuento aplicado.</p>", unsafe_allow_html=True)


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
    # Ventas diarias
    daily_sales = filtered_df.groupby('Fecha')['Precio del Producto'].sum().reset_index()
    fig = px.line(daily_sales, x='Fecha', y='Precio del Producto', title="Ventas Diarias")
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
