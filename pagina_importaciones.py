import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Dashboard de Importaciones", layout="wide")

# Cargar datos de importaciones
@st.cache_data
def load_importaciones():
    version = datetime.now().strftime("%Y%m%d%H%M%S")
    url_importaciones = f"https://raw.githubusercontent.com/HUHU0101123/og-app/main/importaciones.csv?v={version}"
    df_importaciones = pd.read_csv(url_importaciones)
    df_importaciones.columns = df_importaciones.columns.str.strip().str.upper().str.replace(' ', '_')
    df_importaciones = df_importaciones.rename(columns={
        'FECHA_IMPORTACION': 'fecha_importacion',
        'CATEGORIA': 'Categoria',
        'STOCK_INICIAL': 'cantidad'
    })
    df_importaciones['fecha_importacion'] = pd.to_datetime(df_importaciones['fecha_importacion']).dt.date
    return df_importaciones

# Cargar los datos de importaciones
df_importaciones = load_importaciones()

# Título de la aplicación
st.title("Dashboard de Importaciones")

# Filtros en la barra lateral
st.sidebar.header("Filtros")
categories_import = st.sidebar.multiselect("Categorías de Importación", options=df_importaciones['Categoria'].unique())

# Aplicar filtros
if categories_import:
    df_importaciones = df_importaciones[df_importaciones['Categoria'].isin(categories_import)]

# Resumen de Importaciones
st.header("Resumen de Importaciones")

df_grouped = df_importaciones.groupby('fecha_importacion').agg(
    cantidad_total=('cantidad', 'sum')
).reset_index()

fig_importaciones = go.Figure(data=[
    go.Bar(name='Cantidad Total', x=df_grouped['fecha_importacion'], y=df_grouped['cantidad_total'])
])
fig_importaciones.update_layout(title_text="Importaciones por Fecha", xaxis_title="Fecha", yaxis_title="Cantidad")
st.plotly_chart(fig_importaciones, use_container_width=True)

# Mostrar tabla detallada
st.header("Detalle de Importaciones")
st.dataframe(df_importaciones)
