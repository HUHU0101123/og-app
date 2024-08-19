import streamlit as st
from pagina_importaciones import pagina_importaciones
from pagina_ventas import pagina_ventas

# Configuración de la página (debe estar al inicio del archivo)
st.set_page_config(page_title="Dashboard de Ventas", layout="wide")

# Título de la aplicación
st.title("Mi Dashboard")

# Menú de navegación lateral
page = st.sidebar.selectbox("Selecciona una página", ["Importaciones", "Ventas"])

# Mostrar la página seleccionada
if page == "Importaciones":
    pagina_importaciones()
elif page == "Ventas":
    pagina_ventas()

