import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Rental Fleet Command Center",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SYSTEM STATE & INITIALIZATION (Simulating Live Cloud Database) ---
if 'fleet_data' not in st.session_state:
    try:
        # Load your actual Fleet Master data sheet
        df = pd.read_csv("rental business.xlsx - Fleet Master.csv")
        # Clean any trailing spaces or hidden column anomalies
        df.columns = df.columns.str.strip()
        st.session_state.fleet_data = df
    except FileNotFoundError:
        # Emergency backup fallback data structure matching your exact data scheme
        fallback_data = {
            'Car ID': ['C001', 'C002', 'C003', 'C004', 'C005'],
            'Make/Model': ['Toyota Camry', 'Honda Civic', 'Kia Sportage', 'Hyundai Elantra', 'Toyota Prius'],
            'License Plate': ['01KG123ABC', '01KG567XYZ', '01KG999DEF', '01KG111GHI', '01KG444AAA'],
            'Color': ['Silver', 'Blue', 'Black', 'White', 'White'],
            'Status': ['Maintenance', 'Available', 'Available', 'Rented', 'Available'],
            'Base Daily Rate ($)': [150, 120, 180, 140, 100],
            'Override Status': ['Normal', 'Normal', 'Normal', 'Normal', 'Normal']
        }
        st.session_state.fleet_data = pd.DataFrame(fallback_data)

if 'deals_data' not in st.session_state:
    st.session_state.deals_data = pd.DataFrame(columns=[
        'Deal ID', 'Client Name', 'Phone/WhatsApp', 'ID/Passport', 
        'Rental Start Date', 'Rental End Date', 'Rental Days', 
        'Car ID', 'Daily Rate', 'Total Amount', 'Payment Status'
    ])

# --- TOP UTILITIES (NAVIGATION AND VIEW SWITCHING) ---
view_mode = st.radio(
    "Select Interface View", 
    ["🛎️ Front Desk Dashboard", "🛠️ Fleet Operations & Status Switcher"], 
    horizontal=True
)

# ==============================================================================
# VIEW 1: FRONT DESK DASHBOARD (IMITATES LANDING PAGE SHEET)
# ==============================================================================
if view_mode == "🛎️ Front Desk Dashboard":
    st.title("FRONT DESK: VEHICLE AVAILABILITY CHECKER")
    
    # Split Layout for Input Controls vs Database Results Display Grid
    col_input, col_grid = st.columns([1, 2.5])
    
    with col_input:
        st.markdown("### 📅 Reservation Range")
        start_date = st.date_input("Start Date:", datetime.today())
        num_days = st.number_input("No. of Days:", min_value=1, max_value=90, value=5, step=1)
        
        # Automatic continuous calculation of the end vector
        expected_return = start_date + timedelta(days=int(num_days))
        st.info(f"🔮 **Expected Return Date:** {expected_return.strftime('%Y-%m-%d')}")
        
        # Pull live snapshot data to evaluate system states
        fleet_df = st.session_state.fleet_data
        
        # Simple rule filtering: Cars must be explicitly marked 'Available'
        available_cars = fleet_df[
            (fleet_df['Status'].str.strip() == 'Available') & 
            (~fleet_df['Override Status'].isin(['Maintenance', 'Out of Service']))
        ]
        
        # Display the real-time calculated metrics badge
        st.metric(label="AVAILABLE VEHICLES MATCHED", value=len(available_cars))

    with col_grid:
        st.markdown("### 🚘 Dynamic Fleet Inventory Matrix")
        if len(available_cars) == 0:
            st.warning("⚠️ No vehicles match the current query dates. Check adjustments or maintenance queues.")
        else:
            # Reformat columns to show pricing options perfectly
            display_df = available_cars.copy()
            display_df['Price / Day'] = display_df['Base Daily Rate ($)']
            display_df['Total Price'] = display_df['Base Daily Rate ($)'] * num_days
            
            # Print interactive workspace grid containing data subsets
            for index, row in display_df.iterrows():
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([1, 2, 1.5, 1])
                    with c1:
                        st.markdown(f"**`{row['Car ID']}`**")
                    with c2:
                        st.markdown(f"**{row['Make/Model']}** ({row['Color']})")
                        st.caption(f"Plate: {row['License Plate']}")
                    with c3:
                        st.markdown(f"Rate: **${row['Price / Day']}**/day")
                        st.markdown(f"Est. Total: **${row['Total Price']}**")
                    with c4:
                        # Direct dynamic form popup generation trigger
                        if st.button("Book Car", key=f"book_{row['Car ID']}"):
                            st.session_state.selected_car = row
                            st.session_state.booking_days = num_days
                            st.session_state.booking_start = start_date
                            st.session_state.booking_end = expected_return
                            st.session_state.show_form = True

    # --- SIMPLIFIED DYNAMIC CLIENT QUESTIONNAIRE ---
    if st.session_state.get('show_form', False):
        car = st.session_state.selected_car
        total_price = car['Base Daily Rate ($)'] * st.session_state.booking_days
        
        st.markdown("---")
        st.subheader("📑 Fast Contract Generator")
        
        with st.form("contract_form"):
            f_c1, f_c2 = st.columns(2)
            with f_c1:
                st.text_input("Car ID (Locked Field)", value=car['Car ID'], disabled=True)
                st.text_input("Vehicle Allocation (Locked Field)", value=f"{car['Make/Model']} - {car['Color']}", disabled=True)
                st.text_input("Rental Span", value=f"{st.session_state.booking_start} to {st.session_state.booking_end} ({st.session_state.booking_days} Days)", disabled=True)
            with f_c2:
                client_name = st.text_input("Client Full Name:")
                client_phone = st.text_input("Phone / WhatsApp:")
                client_id = st.text_input("ID or Passport Number:")
                
            st.markdown(f"💰 **Financial Verification Check:** Base Rate: ${car['Base Daily Rate ($)']} | **Grand Total Due: ${total_price}**")
            
            # Submission logic mapping
            if st.form_submit_button("Generate Active Rental Assignment"):
                if client_name and client_phone:
                    # 1. Update transactions database record log
                    deal_id = f"RENT-{datetime.today().strftime('%Y%m')}-{len(st.session_state.deals_data)+1:03d}"
                    new_deal = {
                        'Deal ID': deal_id, 'Client Name': client_name, 'Phone/WhatsApp': client_phone,
                        'ID/Passport': client_id, 'Rental Start Date': st.session_state.booking_start,
                        'Rental End Date': st.session_state.booking_end, 'Rental Days': st.session_state.booking_days,
                        'Car ID': car['Car ID'], 'Daily Rate': car['Base Daily Rate ($)'], 'Total Amount': total_price, 'Payment Status': 'Pending'
                    }
                    st.session_state.deals_data = pd.concat([st.session_state.deals_data, pd.DataFrame([new_deal])], ignore_index=True)
                    
                    # 2. Modify Fleet database entity status on the fly
                    st.session_state.fleet_data.loc[st.session_state.fleet_data['Car ID'] == car['Car ID'], 'Status'] = 'Rented'
                    
                    st.success(f"✔️ Contract successfully processed! Reference Generated: {deal_id}")
                    st.session_state.show_form = False
                    st.rerun()
                else:
                    st.error("❌ Failed to process. Please complete Name and Contact phone entries before validation.")

# ==============================================================================
# VIEW 2: FLEET OPERATIONS (IMITATES FLEET MASTER QUICK SWITCHER ACTIONS)
# ==============================================================================
else:
    st.title("🛠️ FLEET OPERATIONS & QUICK STATUS SWITCHER")
    st.markdown("Instantly switch vehicles between active deployment, maintenance, or storage lines below.")
    
    # Render interactive controls block per grid asset
    for index, row in st.session_state.fleet_data.iterrows():
        status_color = "🟢" if row['Status'] == 'Available' else "🔴" if row['Status'] == 'Rented' else "🟡"
        
        with st.container(border=True):
            o_c1, o_c2, o_c3, o_c4 = st.columns([1, 2, 1.5, 3])
            
            with o_c1:
                st.markdown(f"### `{row['Car ID']}`")
            with o_c2:
                st.markdown(f"**{row['Make/Model']}** ({row['Color']})")
                st.caption(f"License Identification: {row['License Plate']}")
            with o_c3:
                st.markdown(f"Current Status: {status_color} **{row['Status']}**")
            with o_c4:
                # Layout action panel elements
                action_col1, action_col2 = st.columns(2)
                
                with action_col1:
                    # Condition validation logic step
                    if row['Status'] != 'Available':
                        if st.button("✅ Reset to Available", key=f"avail_{row['Car ID']}", use_container_width=True):
                            st.session_state.fleet_data.at[index, 'Status'] = 'Available'
                            st.session_state.fleet_data.at[index, 'Override Status'] = 'Normal'
                            st.toast(f"{row['Car ID']} returned to active lineup!", icon="✅")
                            st.rerun()
                with action_col2:
                    if row['Status'] != 'Maintenance':
                        if st.button("🛠️ Send to Maintenance", key=f"maint_{row['Car ID']}", use_container_width=True):
                            st.session_state.fleet_data.at[index, 'Status'] = 'Maintenance'
                            st.session_state.fleet_data.at[index, 'Override Status'] = 'Maintenance'
                            st.toast(f"{row['Car ID']} sent to repair queue.", icon="🛠️")
                            st.rerun()