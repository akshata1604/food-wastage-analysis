#!/usr/bin/env python
# coding: utf-8

# In[1]:


import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime

st.set_page_config(page_title="Local Food Wastage Management", page_icon="🍽️", layout="wide")
st.title("🍽️ Local Food Wastage Management System")

@st.cache_resource
def get_conn():
    return sqlite3.connect("food_waste.db", check_same_thread=False)

def run_sql(q, params=None):
    conn = get_conn()
    return pd.read_sql_query(q, conn, params=params)

def exec_sql(q, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(q, params or [])
    conn.commit()
    return cur.lastrowid

tab = st.sidebar.radio("Go to", ["Listings", "Providers", "Receivers", "Claims", "SQL Insights"])

if tab == "Listings":
    st.subheader("Available Food Listings")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        city = st.text_input("Filter by City (Location contains)")
    with col2:
        provider_name = st.text_input("Filter Provider Name (contains)")
    with col3:
        food_type = st.text_input("Filter Food Type (e.g., Vegetarian)")
    with col4:
        meal_type = st.text_input("Filter Meal Type (Breakfast/Lunch/Dinner/Snacks)")

    base = """
      SELECT f.Food_ID, f.Food_Name, f.Quantity, f.Expiry_Date,
             f.Provider_ID, f.Provider_Type, f.Location, f.Food_Type, f.Meal_Type,
             p.Name AS Provider_Name, p.Contact AS Provider_Contact
      FROM food_listings f
      LEFT JOIN providers p ON p.Provider_ID = f.Provider_ID
      WHERE 1=1
    """
    params = []
    if city:
        base += " AND f.Location LIKE ?"
        params.append(f"%{city}%")
    if provider_name:
        base += " AND p.Name LIKE ?"
        params.append(f"%{provider_name}%")
    if food_type:
        base += " AND f.Food_Type LIKE ?"
        params.append(f"%{food_type}%")
    if meal_type:
        base += " AND f.Meal_Type LIKE ?"
        params.append(f"%{meal_type}%")
    base += " ORDER BY f.Expiry_Date ASC, f.Food_Name"

    st.dataframe(run_sql(base, params), use_container_width=True)

    with st.expander("➕ Add New Listing"):
        p_id = st.number_input("Provider_ID", min_value=1, step=1)
        food_name = st.text_input("Food_Name")
        qty = st.number_input("Quantity", min_value=1, step=1)
        exp = st.date_input("Expiry_Date", value=date.today())
        ptype = st.text_input("Provider_Type")
        loc = st.text_input("Location")
        ftype = st.text_input("Food_Type")
        mtype = st.text_input("Meal_Type")
        if st.button("Create Listing"):
            exec_sql(
                "INSERT INTO food_listings (Food_Name, Quantity, Expiry_Date, Provider_ID, Provider_Type, Location, Food_Type, Meal_Type) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [food_name, int(qty), str(exp), int(p_id), ptype, loc, ftype, mtype]
            )
            st.success("Listing added. Refresh the page to see it.")

    with st.expander("✏️ Update or 🗑️ Delete Listing"):
        lid = st.number_input("Food_ID", min_value=1, step=1)
        new_qty = st.number_input("New Quantity", min_value=0, step=1)
        if st.button("Update Quantity"):
            exec_sql("UPDATE food_listings SET Quantity=? WHERE Food_ID=?", [int(new_qty), int(lid)])
            st.success("Updated quantity.")
        if st.button("Delete Listing"):
            exec_sql("DELETE FROM food_listings WHERE Food_ID=?", [int(lid)])
            st.warning("Listing deleted.")

elif tab == "Providers":
    st.subheader("Providers")
    st.dataframe(run_sql("SELECT * FROM providers ORDER BY City, Name"), use_container_width=True)
    with st.expander("➕ Add Provider"):
        name = st.text_input("Name")
        ptype = st.text_input("Type")
        addr = st.text_input("Address")
        city = st.text_input("City")
        contact = st.text_input("Contact")
        if st.button("Create Provider"):
            exec_sql("INSERT INTO providers (Name, Type, Address, City, Contact) VALUES (?, ?, ?, ?, ?)", [name, ptype, addr, city, contact])
            st.success("Provider created.")

elif tab == "Receivers":
    st.subheader("Receivers")
    st.dataframe(run_sql("SELECT * FROM receivers ORDER BY City, Name"), use_container_width=True)
    with st.expander("➕ Add Receiver"):
        name = st.text_input("Name")
        rtype = st.text_input("Type")
        city = st.text_input("City")
        contact = st.text_input("Contact")
        if st.button("Create Receiver"):
            exec_sql("INSERT INTO receivers (Name, Type, City, Contact) VALUES (?, ?, ?, ?)", [name, rtype, city, contact])
            st.success("Receiver created.")

elif tab == "Claims":
    st.subheader("Claims")
    st.dataframe(run_sql("""
        SELECT c.Claim_ID, c.Food_ID, c.Receiver_ID, c.Status, c.Timestamp,
               r.Name AS Receiver_Name, f.Food_Name
        FROM claims c
        LEFT JOIN receivers r ON r.Receiver_ID = c.Receiver_ID
        LEFT JOIN food_listings f ON f.Food_ID = c.Food_ID
        ORDER BY c.Timestamp DESC
    """), use_container_width=True)
    with st.expander("➕ Create Claim"):
        food_id = st.number_input("Food_ID", min_value=1, step=1)
        recv_id = st.number_input("Receiver_ID", min_value=1, step=1)
        status = st.selectbox("Status", ["Pending", "Completed", "Cancelled"])
        ts = st.text_input("Timestamp (YYYY-MM-DD HH:MM:SS) - leave empty for now")
        if st.button("Create Claim"):
            if not ts:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            exec_sql("INSERT INTO claims (Food_ID, Receiver_ID, Status, Timestamp) VALUES (?, ?, ?, ?)", [int(food_id), int(recv_id), status, ts])
            st.success("Claim created.")

elif tab == "SQL Insights":
    st.subheader("Key SQL Insights (15 queries)")
    queries = {
        "Providers & Receivers per City": "SELECT p.City, COUNT(DISTINCT p.Provider_ID) AS Providers, COUNT(DISTINCT r.Receiver_ID) AS Receivers FROM providers p LEFT JOIN receivers r ON r.City=p.City GROUP BY p.City ORDER BY p.City",
        "Provider Type → Listings & Quantity": "SELECT Provider_Type, COUNT(*) AS Total_Listings, SUM(Quantity) AS Total_Quantity FROM food_listings GROUP BY Provider_Type ORDER BY Total_Quantity DESC",
        "Receivers with Most Claims": "SELECT r.Name, COUNT(c.Claim_ID) AS Total_Claims FROM receivers r LEFT JOIN claims c ON c.Receiver_ID=r.Receiver_ID GROUP BY r.Name ORDER BY Total_Claims DESC",
        "Total Quantity Available": "SELECT SUM(Quantity) AS Total_Quantity FROM food_listings",
        "Listings by City": "SELECT Location AS City, COUNT(Food_ID) AS Listings FROM food_listings GROUP BY Location ORDER BY Listings DESC",
        "Common Food Types": "SELECT Food_Type, COUNT(*) AS Items, SUM(Quantity) AS Total_Quantity FROM food_listings GROUP BY Food_Type ORDER BY Items DESC",
        "Claims per Food Item": "SELECT f.Food_Name, COUNT(c.Claim_ID) AS Claims FROM food_listings f LEFT JOIN claims c ON c.Food_ID=f.Food_ID GROUP BY f.Food_Name ORDER BY Claims DESC",
        "Top Providers by Completed Claims": "SELECT p.Name, COUNT(c.Claim_ID) AS Completed_Claims FROM providers p JOIN food_listings f ON f.Provider_ID=p.Provider_ID JOIN claims c ON c.Food_ID=f.Food_ID WHERE c.Status='Completed' GROUP BY p.Name ORDER BY Completed_Claims DESC",
        "Claim Status %": "SELECT Status, COUNT(*) AS Count, ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM claims),2) AS Percentage FROM claims GROUP BY Status ORDER BY Count DESC",
        "Avg Quantity per Receiver": "SELECT r.Name, ROUND(AVG(f.Quantity),2) AS Avg_Quantity_Claimed FROM receivers r JOIN claims c ON c.Receiver_ID=r.Receiver_ID JOIN food_listings f ON f.Food_ID=c.Food_ID GROUP BY r.Name ORDER BY Avg_Quantity_Claimed DESC",
        "Most Claimed Meal Type": "SELECT f.Meal_Type, COUNT(c.Claim_ID) AS Total_Claims FROM food_listings f JOIN claims c ON c.Food_ID=f.Food_ID GROUP BY f.Meal_Type ORDER BY Total_Claims DESC",
        "Total Donated by Provider": "SELECT p.Name, SUM(f.Quantity) AS Total_Quantity_Donated FROM providers p JOIN food_listings f ON f.Provider_ID=p.Provider_ID GROUP BY p.Name ORDER BY Total_Quantity_Donated DESC",
        "Availability by City": "SELECT Location AS City, SUM(Quantity) AS Total_Available FROM food_listings GROUP BY Location ORDER BY Total_Available DESC",
        "Top 5 Receivers (Completed)": "SELECT r.Name, COUNT(c.Claim_ID) AS Completed_Claims FROM receivers r JOIN claims c ON c.Receiver_ID=r.Receiver_ID WHERE c.Status='Completed' GROUP BY r.Name ORDER BY Completed_Claims DESC LIMIT 5"
    }
    for title, q in queries.items():
        st.markdown(f"### {title}")
        st.dataframe(run_sql(q), use_container_width=True)


# In[ ]:




