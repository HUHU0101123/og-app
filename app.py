import streamlit as st
from pagina_importaciones import pagina_importaciones
from pagina_ventas import pagina_ventas

# Título de la aplicación
st.set_page_config(page_title="Mi Dashboard")

# Función para mostrar la página de importaciones
def show_importaciones():
    pagina_importaciones()

# Función para mostrar la página de ventas
def show_ventas():
    pagina_ventas()

# Menú de navegación lateral
page = st.sidebar.selectbox("Selecciona una página", ["Importaciones", "Ventas"])

# Mostrar la página seleccionada
if page == "Importaciones":
    show_importaciones()
elif page == "Ventas":
    show_ventas()


