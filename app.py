import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Rental Fleet Command Center",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "rental business.xlsx - Fleet Master.csv"
DEALS_FILE = "rental business.xlsx - Rental Deals Sheet.csv"

# --- CORE DATABASE AUTO-SAVE ENGINES ---
def load_fleet_database():
    """Loads the live fleet spreadsheet from disk, or initializes state."""
    if 'fleet_data' not in st.session_state:
        if os.path.exists(DB_FILE):
            df = pd.read_csv(DB_FILE)
            df.columns = df.columns.str.strip()
            # Ensure required columns exist
            if 'Status' not in df.columns:
                df['Status'] = 'Available'
            st.session_state.fleet_data = df
        else:
            # Fallback initialization if file gets misplaced
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
            st.session_state.fleet_data.to_csv(DB_FILE, index=False)

def save_fleet_database():
    """Permanently commits browser session changes back to the actual CSV spreadsheet."""
    st.session_state.fleet_data.to_csv(DB_FILE, index=False)

def load_deals_database():
    if 'deals_data' not in st.session_state:
        if os.path.exists(DEALS_FILE):
            df = pd.read_csv(DEALS_FILE)
            df.columns = df.columns.str.strip()
            st.session_state.deals_data = df
        else:
            st.session_state.deals_data = pd.DataFrame(columns=[
                'Deal ID', 'Client Name', 'Phone/WhatsApp', 'ID/Passport', 
                'Rental Start Date', 'Rental End Date', 'Rental Days', 
                'Car ID', 'Daily Rate', 'Total Amount', 'Payment Status'
            ])

def save_deals_database():
    st.session_state.deals_data.to_csv(DEALS_FILE, index=False)

# Trigger initial database connection hooks
load_fleet_database()
load_deals_database()

# --- INTERFACE NAVIGATION ---
view_mode = st.radio(
    "Select Interface View", 
    ["🛎️ Front Desk Dashboard", "🛠️ Fleet Operations & Status Switcher"], 
    horizontal=True
)

# ==============================================================================
# VIEW 1: FRONT DESK DASHBOARD (AVAILABILITY CHECKER & INTAKE FORM)
# ==============================================================================
if view_mode == "🛎️ Front Desk Dashboard":
    st.title("FRONT DESK: VEHICLE AVAILABILITY CHECKER")
    
    col_input, col_grid = st.columns([1, 2.5])
    
    with col_input:
        st.markdown("### 📅 Reservation Range")
        start_date = st.date_input("Start Date:", datetime.today())
        num_days = st.number_input("No. of Days:", min_value=1, max_value=90, value=5, step=1)
        
        expected_return = start_date + timedelta(days=int(num_days))
        st.info(f"🔮 **Expected Return Date:** {expected_return.strftime('%Y-%m-%d')}")
        
        # Read the current up-to-date state from the master session memory
        fleet_df = st.session_state.fleet_data
        
        # Filter for live deployment options
        available_cars = fleet_df[
            (fleet_df['Status'].astype(str).str.strip() == 'Available')
        ]
        
        st.metric(label="AVAILABLE VEHICLES MATCHED", value=len(available_cars))

    with col_grid:
        st.markdown("### 🚘 Dynamic Fleet Inventory Matrix")
        if len(available_cars) == 0:
            st.warning("⚠️ No vehicles are currently marked as 'Available' in the Fleet database.")
        else:
            display_df = available_cars.copy()
            display_df['Price / Day'] = display_df['Base Daily Rate ($)']
            display_df['Total Price'] = display_df['Base Daily Rate ($)'] * num_days
            
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
                        if st.button("Book Car", key=f"book_{row['Car ID']}"):
                            st.session_state.selected_car = row
                            st.session_state.booking_days = num_days
                            st.session_state.booking_start = start_date
                            st.session_state.booking_end = expected_return
                            st.session_state.show_form = True

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
            
            if st.form_submit_button("Generate Active Rental Assignment"):
                if client_name and client_phone:
                    deal_id = f"RENT-{datetime.today().strftime('%Y%m')}-{len(st.session_state.deals_data)+1:03d}"
                    new_deal = {
                        'Deal ID': deal_id, 'Client Name': client_name, 'Phone/WhatsApp': client_phone,
                        'ID/Passport': client_id, 'Rental Start Date': st.session_state.booking_start,
                        'Rental End Date': st.session_state.booking_end, 'Rental Days': st.session_state.booking_days,
                        'Car ID': car['Car ID'], 'Daily Rate': car['Base Daily Rate ($)'], 'Total Amount': total_price, 'Payment Status': 'Pending'
                    }
                    # Save Contract record row
                    st.session_state.deals_data = pd.concat([st.session_state.deals_data, pd.DataFrame([new_deal])], ignore_index=True)
                    save_deals_database()
                    
                    # Flip status and commit change directly to physical file
                    st.session_state.fleet_data.loc[st.session_state.fleet_data['Car ID'] == car['Car ID'], 'Status'] = 'Rented'
                    save_fleet_database()
                    
                    st.success(f"✔️ Contract successfully processed and saved to database! Reference: {deal_id}")
                    st.session_state.show_form = False
                    st.rerun()
                else:
                    st.error("❌ Failed to process. Please complete Name and Contact entries.")

# ==============================================================================
# VIEW 2: FLEET OPERATIONS (DYNAMIC FLEET STATUS MANAGEMENT COMMANDS)
# ==============================================================================
else:
    st.title("🛠️ FLEET MASTER DATABASE MANAGER")
    st.markdown("Use this panel to clear returned rental cars or toggle vehicles into maintenance lines permanently.")
    
    # Render interactive row control panel for EVERY car in the database file
    for index, row in st.session_state.fleet_data.iterrows():
        current_status = str(row['Status']).strip()
        
        # Pick dynamic visual accents based on real data
        if current_status == 'Available':
            status_badge = "🟢 Available"
        elif current_status == 'Rented':
            status_badge = "🔴 Out on Rent"
        else:
            status_badge = "🛠️ Maintenance / Workshop"
        
        with st.container(border=True):
            o_c1, o_c2, o_c3, o_c4 = st.columns([1, 2, 2, 3])
            
            with o_c1:
                st.markdown(f"### `{row['Car ID']}`")
            with o_c2:
                st.markdown(f"**{row['Make/Model']}** ({row['Color']})")
                st.caption(f"License Plate: {row['License Plate']}")
            with o_c3:
                st.markdown(f"Current Row State:\n### {status_badge}")
            with o_c4:
                action_col1, action_col2 = st.columns(2)
                
                with action_col1:
                    # Render button to clear a vehicle if it is Rented or in Maintenance
                    if current_status != 'Available':
                        if st.button("✅ Make Available (Return)", key=f"avail_{row['Car ID']}", use_container_width=True):
                            st.session_state.fleet_data.at[index, 'Status'] = 'Available'
                            if 'Override Status' in st.session_state.fleet_data.columns:
                                st.session_state.fleet_data.at[index, 'Override Status'] = 'Normal'
                            
                            # CRITICAL STEP: Write back to spreadsheet on disk
                            save_fleet_database()
                            st.toast(f"Success: Database updated! {row['Car ID']} is back on the lot.", icon="✅")
                            st.rerun()
                    else:
                        st.button("✔️ Active on Lot", key=f"disabled_avail_{row['Car ID']}", disabled=True, use_container_width=True)
                        
                with action_col2:
                    # Render button to send an active/rented car to maintenance
                    if current_status != 'Maintenance':
                        if st.button("🛠️ Send to Maintenance", key=f"maint_{row['Car ID']}", use_container_width=True):
                            st.session_state.fleet_data.at[index, 'Status'] = 'Maintenance'
                            if 'Override Status' in st.session_state.fleet_data.columns:
                                st.session_state.fleet_data.at[index, 'Override Status'] = 'Maintenance'
                            
                            # CRITICAL STEP: Write back to spreadsheet on disk
                            save_fleet_database()
                            st.toast(f"Success: Database updated! {row['Car ID']} flagged for service.", icon="🛠️")
                            st.rerun()
                    else:
                        st.button("🔧 Currently in Workshop", key=f"disabled_maint_{row['Car ID']}", disabled=True, use_container_width=True)