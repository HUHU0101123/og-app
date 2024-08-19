import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go

def pagina_importaciones():
    st.title("Dashboard de Importaciones")
    #SEGUNDO GRAFICO
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
                hoverinfo='skip',  # Desactiva las tooltips para las barras
                text=[row['cantidad']],  # Muestra la cantidad al final de la barra
                textposition='outside'  # Posiciona el texto al final de la barra
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
                showlegend=False,
                hoverinfo='skip'  # Desactiva las tooltips para la línea
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
                    text="La línea roja representa la 'Cantidad Vendida' al 0% para cada categoría.",
                    showarrow=False,
                    font=dict(size=12, color="black"),
                    align="center",
                    bgcolor="rgba(255, 255, 255, 0.7)"
                )
            ]
        )
    
        st.plotly_chart(fig, use_container_width=True)
    
    
    
    
    
    
    
    
    
    
    
    
    
    #TABLA IMPORTACIONES
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
