import streamlit as st
import pagina_ventas
import pagina_importaciones

st.set_page_config(page_title="Dashboard", layout="wide")

st.sidebar.title("Navegación")
page = st.sidebar.radio("Ir a", ["Ventas", "Importaciones"])

if page == "Ventas":
    pagina_ventas.show()
elif page == "Importaciones":
    pagina_importaciones.show()



