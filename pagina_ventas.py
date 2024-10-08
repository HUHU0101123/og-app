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
    
    # Sidebar date input
    date_range = st.sidebar.date_input("Rango de fechas", [min_date, max_date])

    # Otros filtros
    categories = st.sidebar.multiselect("Categorías", options=df['Categoria'].unique() if 'Categoria' in df.columns else [])
    sale_type = st.sidebar.multiselect("Tipo de Venta", options=df['Tipo de Venta'].unique() if 'Tipo de Venta' in df.columns else [])
    order_ids = st.sidebar.text_input("IDs de Orden de Compra (separados por coma)", "")
    regions = st.sidebar.multiselect("Región de Envío", options=df['Región de Envío'].unique() if 'Región de Envío' in df.columns else [])
    payment_status = st.sidebar.multiselect("Estado del Pago", options=df['Estado del Pago'].unique() if 'Estado del Pago' in df.columns else [])
    payment_names = st.sidebar.multiselect("Nombre de Pago", options=df['Nombre de Pago'].unique() if 'Nombre de Pago' in df.columns else [])

    # Convert date_range to datetime for compatibility with df['Fecha']
    date_range_dt = [pd.to_datetime(date) for date in date_range]

    # Adjust the end date to include the entire last day
    date_range_dt[1] = date_range_dt[1] + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)  # End of the day

    # Apply filters
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
    if 'Nombre de Pago' in df.columns and payment_names:
        mask &= df['Nombre de Pago'].isin(payment_names)
    
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
            <p style='font-size:10px; color: black;'>Ventas totales menos descuentos (Jumpseller).</p>
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
    descuento_promedio = (filtered_df['Descuento del producto'].sum() / ventas_totales * 100) if ventas_totales > 0 else 0
    col2.markdown(
        f"""
        <div style="background-color: #D3D3D3; padding: 10px; border-radius: 5px; text-align: center;">
            <strong style="color: black;">Descuento Promedio %</strong><br>
            <span style="color: black;">{descuento_promedio:.2f}%</span>
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

if __name__ == "__main__":
    pagina_ventas()
