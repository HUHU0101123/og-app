import streamlit as st

# Configuración del título de la aplicación principal
st.set_page_config(page_title="Dashboard de Ventas e Importaciones")

# Título de la aplicación principal
st.title("Dashboard de Ventas e Importaciones")

# Selección de página
page = st.sidebar.selectbox("Seleccione la página:", ["Ventas", "Importaciones"])

if page == "Ventas":
    st.write("## Página de Ventas")
    exec(open("pagina_ventas.py").read())
elif page == "Importaciones":
    st.write("## Página de Importaciones")
    exec(open("pagina_importaciones.py").read())
