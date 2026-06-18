import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- INITIAL COMPONENT CONFIGURATION ---
st.set_page_config(page_title="Rental Fleet Center", page_icon="🚗", layout="wide")

# File targets for local offline operations
LOCAL_FLEET = "rental business.xlsx - Fleet Master.csv"
LOCAL_DEALS = "rental business.xlsx - Rental Deals Sheet.csv"

# Dedicated Offline Enforcement
USING_GOOGLE_SHEETS = False
st.sidebar.info("💾 Mode: Local Offline Mode (CSV File)")

# --- ROBUST TYPE-CASTING UTILITY ---
def safe_int(value, default=100):
    """Safely extracts clean integer rates from strings, floats, or currency formats."""
    try:
        if pd.isna(value):
            return default
        cleaned = str(value).replace('$', '').replace(',', '').strip()
        return int(float(cleaned))
    except (ValueError, TypeError):
        return default

# --- INTEGRATED READ/WRITE CONTROLLERS ---
def fetch_fleet_data():
    if os.path.exists(LOCAL_FLEET):
        df = pd.read_csv(LOCAL_FLEET)
        df.columns = df.columns.str.strip()
        return df
    else:
        return pd.DataFrame({
            'Car ID': ['C001', 'C002', 'C003', 'C004', 'C005', 'C006', 'C007', 'C008'],
            'Make/Model': ['Toyota Camry', 'Honda Civic', 'Kia Sportage', 'Hyundai Elantra', 'Toyota Prius', 'Lexus RX350', 'Chevrolet Cobalt', 'Volkswagen Polo'],
            'License Plate': ['01KG123ABC', '01KG567XYZ', '01KG999DEF', '01KG111GHI', '01KG444AAA', '01KG777BBB', '01KG888CCC', '01KG222DDD'],
            'Color': ['Silver', 'Blue', 'Black', 'White', 'White', 'Charcoal', 'Grey', 'Red'],
            'Status': ['Maintenance', 'Maintenance', 'Available', 'Rented', 'Available', 'Available', 'Available', 'Available'],
            'Base Daily Rate ($)': [150, 120, 180, 140, 100, 200, 100, 110]
        })

def fetch_deals_data():
    if os.path.exists(LOCAL_DEALS):
        df = pd.read_csv(LOCAL_DEALS)
        df.columns = df.columns.str.strip()
        return df
    else:
        return pd.DataFrame(columns=[
            'Deal ID', 'Client Name', 'Phone/WhatsApp', 'ID/Passport', 'Rental Start Date', 
            'Rental End Date', 'Rental Days', 'Time of Rental', 'Car ID', 'Daily Rate', 
            'Total Amount', 'Deposit', 'Payment Status', 'Overdue Days', 'Contract Signed', 
            'Return Condition Notes', 'Car Make/Model', 'Car Status Link'
        ])

def commit_data(target_mode, dataframe):
    dataframe_filled = dataframe.fillna("")
    file_path = LOCAL_FLEET if target_mode == "fleet" else LOCAL_DEALS
    dataframe_filled.to_csv(file_path, index=False)

# Sync live file states
fleet_df = fetch_fleet_data()
deals_df = fetch_deals_data()

# --- INTERFACE DISPLAY ROUTINES ---
view_mode = st.radio("Select Interface View", ["🛎️ Front Desk Dashboard", "🛠️ Live Fleet Status Manager"], horizontal=True)

if view_mode == "🛎️ Front Desk Dashboard":
    st.title("FRONT DESK: VEHICLE AVAILABILITY CHECKER")
    col_input, col_grid = st.columns([1, 2.5])
    
    with col_input:
        st.markdown("### 📅 Reservation Range")
        start_date = st.date_input("Start Date:", datetime.today())
        num_days = st.number_input("No. of Days:", min_value=1, max_value=90, value=5, step=1)
        expected_return = start_date + timedelta(days=int(num_days))
        st.info(f"🔮 **Expected Return Date:** {expected_return.strftime('%Y-%m-%d')}")
        
        available_cars = fleet_df[fleet_df['Status'].astype(str).str.strip() == 'Available']
        st.metric(label="AVAILABLE VEHICLES MATCHED", value=len(available_cars))

    with col_grid:
        st.markdown("### 🚘 Dynamic Fleet Inventory Matrix")
        if len(available_cars) == 0:
            st.warning("⚠️ No vehicles are currently marked as 'Available'.")
        else:
            for index, row in available_cars.iterrows():
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([1, 2, 1.5, 1])
                    with c1: st.markdown(f"**`{row['Car ID']}`**")
                    with c2: st.markdown(f"**{row['Make/Model']}** ({row['Color']})")
                    with c3:
                        rate = safe_int(row['Base Daily Rate ($)'])
                        # Removed the asterisks around the price metrics below
                        st.markdown(f"Rate: ${rate}/day | Total: ${rate * num_days}")
                    with c4:
                        if st.button("Book Car", key=f"bk_{row['Car ID']}"):
                            st.session_state.selected_car = row
                            st.session_state.booking_days = num_days
                            st.session_state.show_form = True

    if st.session_state.get('show_form', False):
        car = st.session_state.selected_car
        rate = safe_int(car['Base Daily Rate ($)'])
        with st.form("contract_form"):
            st.subheader("📑 Fast Contract Generator")
            client_name = st.text_input("Client Full Name:")
            client_phone = st.text_input("Phone / WhatsApp:")
            client_id = st.text_input("ID / Passport / Document No:")
            
            if st.form_submit_button("Confirm Deployment"):
                if client_name and client_phone:
                    deal_id = f"RENT-{datetime.today().strftime('%Y%m')}-{len(deals_df)+1:03d}"
                    
                    new_deal = {
                        'Deal ID': deal_id, 
                        'Client Name': client_name, 
                        'Phone/WhatsApp': client_phone, 
                        'ID/Passport': client_id,
                        'Rental Start Date': start_date.strftime('%Y-%m-%d'),
                        'Rental End Date': expected_return.strftime('%Y-%m-%d'),
                        'Rental Days': int(st.session_state.booking_days),
                        'Time of Rental': datetime.now().strftime('%I:%M %p'),
                        'Car ID': car['Car ID'], 
                        'Daily Rate': rate,
                        'Total Amount': rate * int(st.session_state.booking_days),
                        'Deposit': 0,
                        'Payment Status': 'Pending',
                        'Overdue Days': 0,
                        'Contract Signed': 'No',
                        'Return Condition Notes': '',
                        'Car Make/Model': car['Make/Model'],
                        'Car Status Link': ''
                    }
                    
                    deals_df = pd.concat([deals_df, pd.DataFrame([new_deal])], ignore_index=True)
                    commit_data("deals", deals_df)
                    
                    fleet_df.loc[fleet_df['Car ID'] == car['Car ID'], 'Status'] = 'Rented'
                    commit_data("fleet", fleet_df)
                    st.success("✔️ Contract recorded and status changed successfully!")
                    st.session_state.show_form = False
                    st.rerun()

else:
    st.title("🛠️ LIVE FLEET MASTER STATUS MANAGER")
    for index, row in fleet_df.iterrows():
        current_status = str(row['Status']).strip()
        status_badge = "🟢 Available" if current_status == 'Available' else "🔴 Rented" if current_status == 'Rented' else "🛠️ Maintenance"
        
        with st.container(border=True):
            o_c1, o_c2, o_c3, o_c4 = st.columns([1, 2, 2, 3])
            with o_c1: st.markdown(f"### `{row['Car ID']}`")
            with o_c2: st.markdown(f"**{row['Make/Model']}** ({row['Color']})")
            with o_c3: st.markdown(f"State: **{status_badge}**")
            with o_c4:
                a1, a2 = st.columns(2)
                with a1:
                    if current_status != 'Available' and st.button("✅ Make Available", key=f"av_{row['Car ID']}", use_container_width=True):
                        fleet_df.at[index, 'Status'] = 'Available'
                        commit_data("fleet", fleet_df)
                        st.rerun()
                with a2:
                    if current_status != 'Maintenance' and st.button("🛠️ Maintenance", key=f"mn_{row['Car ID']}", use_container_width=True):
                        fleet_df.at[index, 'Status'] = 'Maintenance'
                        commit_data("fleet", fleet_df)
                        st.rerun()