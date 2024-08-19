import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

def pagina_ventas():
    st.title("Dashboard de Ventas")

    # Función para formatear números al estilo chileno
    def format_chilean_currency(value, is_percentage=False):
        if is_percentage:
            return f"{value:.2f}%".replace('.', ',')
        else:
            return f"${value:,.0f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    # Función para cargar los datos
    @st.cache_data
    def load_data():
        version = datetime.now().strftime("%Y%m%d%H%M%S")
        url_main = f"https://raw.githubusercontent.com/HUHU0101123/og-app/main/datasource.csv?v={version}"
        df_main = pd.read_csv(url_main)
        url_categorias = f"https://raw.githubusercontent.com/HUHU0101123/og-app/main/categorias.csv?v={version}"
        df_categorias = pd.read_csv(url_categorias)
        return df_main, df_categorias

    # Función para preprocesar los datos
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

    # Cargar los datos
    df_main, df_categorias = load_data()

    # Preprocesar los datos
    df = preprocess_data(df_main, df_categorias)

    # Aquí continúa el resto de tu código para la página de ventas
    st.write("Datos cargados y procesados correctamente.")
    st.write(f"Número de registros en df: {len(df)}")

    # Aquí puedes agregar más visualizaciones y análisis usando el DataFrame 'df'
