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

    # Cargar los datos
    df_main, df_categorias = load_data()

    # Aquí continúa el resto de tu código para la página de ventas
    # Por ejemplo:
    st.write("Datos cargados correctamente.")
    st.write(f"Número de registros en df_main: {len(df_main)}")
    st.write(f"Número de registros en df_categorias: {len(df_categorias)}")

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

# Cargar y preprocesar los datos
df_main, df_categorias = load_data()
df = preprocess_data(df_main, df_categorias)

# Página de selección
page = st.sidebar.selectbox("Selecciona una página", ["Resumen de Ventas", "Gráficos"])

if page == "Resumen de Ventas":
    st.title("Resumen de Ventas")

    # Filtros en la barra lateral
    st.sidebar.header("Filtros")
    date_range = st.sidebar.date_input("Rango de fechas", [df['Fecha'].min(), df['Fecha'].max()])
    categories = st.sidebar.multiselect("Categorías", options=df['Categoria'].unique())
    sale_type = st.sidebar.multiselect("Tipo de Venta", options=df['Tipo de Venta'].unique())
    order_ids = st.sidebar.text_input("IDs de Orden de Compra (separados por coma)", "")
    regions = st.sidebar.multiselect("Región de Envío", options=df['Región de Envío'].unique())
    payment_status = st.sidebar.multiselect("Estado del Pago", options=df['Estado del Pago'].unique())

    # Aplicar filtros
    mask = (df['Fecha'] >= date_range[0]) & (df['Fecha'] <= date_range[1])
    if categories:
        mask &= df['Categoria'].isin(categories)
    if sale_type:
        mask &= df['Tipo de Venta'].isin(sale_type)
    if order_ids:
        order_id_list = [int(id.strip()) for id in order_ids.split(',')]
        mask &= df['ID'].isin(order_id_list)
    if regions:
        mask &= df['Región de Envío'].isin(regions)
    if payment_status:
        mask &= df['Estado del Pago'].isin(payment_status)

    filtered_df = df[mask]

    # Calcular las ventas totales
    ventas_totales = (filtered_df['Precio del Producto'] * filtered_df['Cantidad de Productos']).sum()
    ventas_netas = filtered_df['Ventas Netas'].sum()
    ventas_netas_despues_impuestos = ventas_netas * (1 - 0.19)

    # Calcular el costo del producto
    filtered_df['Precio Neto del Producto'] = filtered_df['Precio del Producto'] - filtered_df['Descuento del producto']
    filtered_df['Costo del Producto'] = filtered_df['Precio Neto del Producto'] * (1 - filtered_df['Margen del producto (%)'] / 100)
    costo_total = (filtered_df['Costo del Producto'] * filtered_df['Cantidad de Productos']).sum()

    # Calcular el beneficio bruto
    beneficio_bruto = ventas_netas - costo_total
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
            <p style='font-size:10px; color: black;'>Ganancia bruta antes de impuestos.</p>
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
            <p style='font-size:10px; color: black;'>Margen sobre ventas netas.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

elif page == "Gráficos":
    st.title("Gráficos")

    # Gráfico de Ventas Netas por Categoría
    fig_categorias = px.bar(filtered_df, x='Categoria', y='Ventas Netas', color='Categoria', title='Ventas Netas por Categoría')
    st.plotly_chart(fig_categorias, use_container_width=True)

    # Gráfico de Ventas por Región
    fig_regiones = px.bar(filtered_df, x='Región de Envío', y='Ventas Netas', color='Región de Envío', title='Ventas por Región')
    st.plotly_chart(fig_regiones, use_container_width=True)
