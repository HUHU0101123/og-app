!pip install openpyxl
import streamlit as st
import pandas as pd

# Load the Excel file
file_name = "https://raw.githubusercontent.com/HUHU0101123/og-app/main/DATOSDEPRUEBA.xlsx"  # Replace with your actual file name
data = pd.read_excel(file_name)

# Strip any extra whitespace from column names
data.columns = data.columns.str.strip()

# Convert 'Date' column to datetime
data['Date'] = pd.to_datetime(data['Date'])

# Streamlit app title
st.title("Sales Dashboard")

# Display the DataFrame
st.header("Sales Data")
st.write(data)

# Line chart of total sales over time
st.subheader("Total Sales Over Time")
# Assuming 'Sales' is the total sales column
st.line_chart(data.set_index('Date')['Sales'])

# Bar chart of units sold by product
st.subheader("Units Sold by Product")
# Assuming 'Quantity' is the units sold column
st.bar_chart(data.groupby('Product')['Quantity'].sum())

# Sidebar for product selection
product = st.sidebar.selectbox("Select a Product", data['Product'].unique())
filtered_data = data[data['Product'] == product]

# Display filtered data
st.subheader(f"Data for {product}")
st.write(filtered_data)

# Bar chart of total sales by selected product
st.subheader(f"Total Sales for {product}")
st.bar_chart(filtered_data.groupby('Date')['Sales'].sum())
