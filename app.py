import streamlit as st

# Import the pages
import pagina_ventas
import pagina_importaciones

# Set up page configuration
st.set_page_config(page_title="Dashboard", layout="wide")

# Sidebar for navigation
st.sidebar.title("Navegación")
page = st.sidebar.radio("Ir a", ["Ventas", "Importaciones"])

# Display the selected page
if page == "Ventas":
    pagina_ventas.show()  # Call the function that runs the sales dashboard
elif page == "Importaciones":
    pagina_importaciones.show()  # Call the function that runs the importations summary
