import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date

def pagina_ventas():
    st.title("Dashboard de Ventas")

    # Función para formatear números al estilo chileno
    def format_chilean_currency(value, is_percentage=False):
        if is_percentage:
            return f"{value:.2f}%".replace('.', ',')
        else:
            return f"${value:,.0f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    # Cargar los archivos CSV desde GitHub sin caché
    @st.cache_data(ttl=3600)
    def load_data():
        try:
            version = datetime.now().strftime("%Y%m%d%H%M%S")
            url_main = f"https://raw.githubusercontent.com/HUHU0101123/og-app/main/datasource.csv?v={version}"
            df_main = pd.read_csv(url_main)
            url_categorias = f"https://raw.githubusercontent.com/HUHU0101123/og-app/main/categorias.csv?v={version}"
            df_categorias = pd.read_csv(url_categorias)
            return df_main, df_categorias
        except Exception as e:
            st.error(f"Error al cargar los datos: {str(e)}")
            return None, None

    # Preprocesamiento de datos
    def preprocess_data(df_main, df_categorias):
        try:
            df_main['Fecha'] = pd.to_datetime(df_main['Fecha'], errors='coerce')
            df = pd.merge(df_main, df_categorias, on='SKU del Producto', how='left')

            columns_to_fill = ['Estado del Pago', 'Fecha', 'Moneda', 'Región de Envío', 'Nombre del método de envío', 'Cupones', 'Nombre de Pago']
            df[columns_to_fill] = df.groupby('ID')[columns_to_fill].fillna(method='ffill')

            numeric_columns = ['Cantidad de Productos', 'Precio del Producto', 'Margen del producto (%)', 'Descuento del producto']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')

            df['Total Productos'] = df.groupby('ID')['Cantidad de Productos'].transform('sum')
            df['Tipo de Venta'] = df['Total Productos'].apply(lambda x: 'Mayorista' if x >= 6 else 'Detalle')

            df['Ventas Netas'] = (df['Precio del Producto'] - df['Descuento del producto']) * df['Cantidad de Productos']
            return df
        except Exception as e:
            st.error(f"Error en el preprocesamiento de datos: {str(e)}")
            return None

    # Cargar y preprocesar los datos
    df_main, df_categorias = load_data()
    if df_main is None or df_categorias is None:
        st.error("No se pudieron cargar los datos. Por favor, intente nuevamente más tarde.")
        return

    df = preprocess_data(df_main, df_categorias)
    if df is None:
        st.error("Error en el preprocesamiento de los datos. Por favor, revise el formato de los archivos CSV.")
        return

    # Filtros en la barra lateral
    st.sidebar.header("Filtros")

    # Manejo seguro de las fechas mínima y máxima
    try:
        valid_dates = df['Fecha'].dropna()
        if valid_dates.empty:
            st.error("No hay fechas válidas en los datos. Por favor, revise el formato de las fechas en el archivo CSV.")
            return
        min_date = valid_dates.min().date()
        max_date = valid_dates.max().date()
    except Exception as e:
        st.error(f"Error al procesar las fechas: {str(e)}")
        return

    date_range = st.sidebar.date_input("Rango de fechas", [min_date, max_date])

    # Otros filtros
    categories = st.sidebar.multiselect("Categorías", options=df['Categoria'].unique() if 'Categoria' in df.columns else [])
    sale_type = st.sidebar.multiselect("Tipo de Venta", options=df['Tipo de Venta'].unique() if 'Tipo de Venta' in df.columns else [])
    order_ids = st.sidebar.text_input("IDs de Orden de Compra (separados por coma)", "")
    regions = st.sidebar.multiselect("Región de Envío", options=df['Región de Envío'].unique() if 'Región de Envío' in df.columns else [])
    payment_status = st.sidebar.multiselect("Estado del Pago", options=df['Estado del Pago'].unique() if 'Estado del Pago' in df.columns else [])
    payment_method = st.sidebar.multiselect("Nombre de Pago", options=df['Nombre de Pago'].unique() if 'Nombre de Pago' in df.columns else [])

    # Convertir date_range a datetime para compatibilidad con df['Fecha']
    date_range_dt = [pd.to_datetime(date) for date in date_range]

    # Aplicar filtros
    mask = (df['Fecha'] >= date_range_dt[0]) & (df['Fecha'] <= date_range_dt[1])
    if 'Categoria' in df.columns and categories:
        mask &= df['Categoria'].isin(categories)
    if 'Tipo de Venta' in df.columns and sale_type:
        mask &= df['Tipo de Venta'].isin(sale_type)
    if order_ids:
        order_id_list = [int(id.strip()) for id in order_ids.split(',') if id.strip().isdigit()]
        mask &= df['ID'].isin(order_id_list)
    if 'Región de Envío' in df.columns and regions:
        mask &= df['Región de Envío'].isin(regions)
    if 'Estado del Pago' in df.columns and payment_status:
        mask &= df['Estado del Pago'].isin(payment_status)
    if 'Nombre de Pago' in df.columns and payment_method:
        mask &= df['Nombre de Pago'].isin(payment_method)

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
    margen_bruto = (beneficio_bruto / ventas_netas) * 100 if ventas_netas > 0 else 0

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

    # Beneficio Bruto
    col4.markdown(
        f"""
        <div style="background-color: #D3D3D3; padding: 10px; border-radius: 5px; text-align: center;">
            <strong style="color: black;">Beneficio Bruto</strong><br>
            <span style="color: black;">{format_chilean_currency(beneficio_bruto_despues_impuestos)}</span>
            <p style='font-size:10px; color: black;'>Beneficio bruto después de impuestos (19%).</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Mostrar el DataFrame filtrado
    st.subheader("Datos Filtrados")
    st.dataframe(filtered_df)

# Ejecución principal
if __name__ == "__main__":
    pagina_ventas()

