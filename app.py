import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import hashlib
import json
import os
from datetime import datetime, timedelta, time

# --- INITIAL SYSTEM CONFIGURATION ---
st.set_page_config(page_title="Finansal Araç Filo Yönetim Merkezi", page_icon="📊", layout="wide")

# --- DATABASE STORAGE ASSIGNMENTS ---
FLEET_FILE = "fleet_master.csv"
DEALS_FILE = "rental_deals.csv"

# --- CRYPTOGRAPHIC UTILITY ENGINE ---
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# --- SECURITY PROFILE INITIALIZATION ---
if "password_hash" not in st.session_state:
    st.session_state.password_hash = hash_password("deneme")  # Default password: deneme

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- GATEKEEPER TERMINAL INTERFACE ---
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center;'>🔒 Sistem Güvenli Giriş</h2>", unsafe_allow_html=True)
            st.caption("Finansal Araç Filo Yönetim Merkezi Operasyon ve Veri Paneli")
            st.markdown("---")
            with st.form("gatekeeper_login_form", clear_on_submit=True):
                username_input = st.text_input("👤 Kullanıcı Adı (Username):", placeholder="garden")
                password_input = st.text_input("🔑 Şifre (Password):", type="password", placeholder="••••••")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("Sistem Girişi Sağla", use_container_width=True, type="primary"):
                    if username_input == "garden" and hash_password(password_input) == st.session_state.password_hash:
                        st.session_state.logged_in = True
                        st.success("✔️ Kimlik doğrulandı! Oturum başlatılıyor...")
                        st.rerun()
                    else:
                        st.error("❌ Hatalı Kullanıcı Adı veya Şifre!")
    st.stop()

# --- REAL-TIME OFFLINE STORAGE SYNC & SANITATION ENGINE ---
def sync_with_local_database():
    """Reads records from local CSVs and enforces strict text sanitization to block Pandas float64/nan bugs."""
    if not os.path.exists(FLEET_FILE):
        df_fleet = pd.DataFrame(columns=[
            "Car ID", "Make/Model", "Year", "License Plate", "Color", 
            "Current Mileage", "Status", "Base Daily Rate ($)", "Notes", "Client Maintenance Charge"
        ])
        df_fleet.to_csv(FLEET_FILE, index=False)
    else:
        try:
            df_fleet = pd.read_csv(FLEET_FILE).dropna(how="all")
        except Exception:
            df_fleet = pd.DataFrame(columns=[
                "Car ID", "Make/Model", "Year", "License Plate", "Color", 
                "Current Mileage", "Status", "Base Daily Rate ($)", "Notes", "Client Maintenance Charge"
            ])
            
    fleet_text_cols = ["Car ID", "Make/Model", "License Plate", "Color", "Status", "Notes"]
    for col in fleet_text_cols:
        if col in df_fleet.columns:
            df_fleet[col] = df_fleet[col].fillna("").astype(str)
    st.session_state.fleet_db = df_fleet

    if not os.path.exists(DEALS_FILE):
        df_deals = pd.DataFrame(columns=[
            'Deal ID', 'Client Name', 'Phone/WhatsApp', 'ID/Passport',
            'Rental Start Date', 'Rental Start Time', 'Rental End Date', 'Rental End Time', 
            'Rental Days', 'Car ID', 'Daily Rate', 'Total Amount', 'Deposit', 'Payment Status',
            'Overdue Days', 'Overdue Charge ($)', 'Contract Signed', 'Return Condition Notes', 'Car Make/Model'
        ])
        df_deals.to_csv(DEALS_FILE, index=False)
    else:
        try:
            df_deals = pd.read_csv(DEALS_FILE).dropna(how="all")
        except Exception:
            df_deals = pd.DataFrame(columns=[
                'Deal ID', 'Client Name', 'Phone/WhatsApp', 'ID/Passport',
                'Rental Start Date', 'Rental Start Time', 'Rental End Date', 'Rental End Time', 
                'Rental Days', 'Car ID', 'Daily Rate', 'Total Amount', 'Deposit', 'Payment Status',
                'Overdue Days', 'Overdue Charge ($)', 'Contract Signed', 'Return Condition Notes', 'Car Make/Model'
            ])
            
    deals_text_cols = [
        'Deal ID', 'Client Name', 'Phone/WhatsApp', 'ID/Passport',
        'Rental Start Date', 'Rental Start Time', 'Rental End Date', 'Rental End Time', 
        'Car ID', 'Payment Status', 'Contract Signed', 'Return Condition Notes', 'Car Make/Model'
    ]
    for col in deals_text_cols:
        if col in df_deals.columns:
            df_deals[col] = df_deals[col].fillna("").astype(str)
    st.session_state.deals_db = df_deals

def save_state_to_local():
    """Safely writes back state mutations instantly into physical local tracking ledgers."""
    st.session_state.fleet_db.to_csv(FLEET_FILE, index=False)
    st.session_state.deals_db.to_csv(DEALS_FILE, index=False)
    st.toast("💾 Yerel Veri Tabanı Güncellendi (CSV)!")

if "fleet_db" not in st.session_state or "deals_db" not in st.session_state:
    sync_with_local_database()

fleet_df = st.session_state.fleet_db
deals_df = st.session_state.deals_db

# --- SAFE CASTING AND DATA READING CONTROLS ---
def get_safe_str(val):
    if pd.isna(val) or str(val).strip().lower() == "nan":
        return ""
    return str(val).strip()

def safe_int(value, default=100):
    try:
        if pd.isna(value): return default
        return int(float(str(value).replace('$', '').replace(',', '').strip()))
    except Exception: return default

def safe_float(value, default=0.0):
    try:
        if pd.isna(value): return default
        return float(str(value).replace('$', '').replace(',', '').strip())
    except Exception: return default

def generate_next_car_id(df):
    if df.empty or 'Car ID' not in df.columns:
        return "C001"
    try:
        valid_ids = df['Car ID'].dropna().astype(str)
        numeric_extracts = valid_ids.str.extract(r'(\d+)')[0].dropna().astype(int)
        if numeric_extracts.empty:
            return "C001"
        return f"C{numeric_extracts.max() + 1:03d}"
    except Exception:
        return f"C{len(df) + 1:03d}"

# --- PAGE ROUTING CONTROLS ---
if "current_page" not in st.session_state:
    st.session_state.current_page = "🛎️ Resepsiyon Paneli"

st.markdown("### 🗺️ Kontrol Merkezi Navigasyon Paneli")
nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)

with nav_col1:
    if st.button("🛎️ ÖN OFİS RESEPSİYON", use_container_width=True, type="primary" if st.session_state.current_page == "🛎️ Resepsiyon Paneli" else "secondary"):
        st.session_state.current_page = "🛎️ Resepsiyon Paneli"
        sync_with_local_database()
        st.rerun()
with nav_col2:
    if st.button("🛠️ CANLI FİLO & SÜRE/HASAR KONTROLLERİ", use_container_width=True, type="primary" if st.session_state.current_page == "🛠️ Canlı Filo Yöneticisi" else "secondary"):
        st.session_state.current_page = "🛠️ Canlı Filo Yöneticisi"
        sync_with_local_database()
        st.rerun()
with nav_col3:
    if st.button("📊 AYLIK FİNANSAL PERFORMANS ÖZETİ & CRUD", use_container_width=True, type="primary" if st.session_state.current_page == "📊 Finansal Analiz Raporları" else "secondary"):
        st.session_state.current_page = "📊 Finansal Analiz Raporları"
        sync_with_local_database()
        st.rerun()
with nav_col4:
    if st.button("🔒 GÜVENLİ ÇIKIŞ (LOGOUT)", use_container_width=True, type="secondary"):
        st.session_state.logged_in = False
        st.rerun()

st.markdown("---")

# ==================== 1. ÖN OFİS RESEPSİYON PANELİ ====================
if st.session_state.current_page == "🛎️ Resepsiyon Paneli":
    st.title("🛎️ ÖN OFİS RESEPSİYON VE CANLI REZERVASYON TAKVİMİ")
    st.markdown("### 📅 Canlı Kiralama Zaman Çizelgesi (Filo Yoğunluk Haritası)")
    
    calendar_events = []
    color_palette = ['#2563EB', '#DC2626', '#16A34A', '#D97706', '#7C3AED', '#0891B2', '#EA580C', '#DB2777', '#4B5563', '#059669']
    car_colors = {}
    
    if not deals_df.empty:
        active_calendar_deals = deals_df[deals_df['Payment Status'] == 'Active']
        for _, deal in active_calendar_deals.iterrows():
            car_id = get_safe_str(deal.get('Car ID', ''))
            
            if car_id not in car_colors:
                car_colors[car_id] = color_palette[len(car_colors) % len(color_palette)]
                
            s_date = get_safe_str(deal.get('Rental Start Date', ''))
            s_time = get_safe_str(deal.get('Rental Start Time', '10:00:00'))
            e_date = get_safe_str(deal.get('Rental End Date', ''))
            e_time = get_safe_str(deal.get('Rental End Time', '10:00:00'))
            
            if s_date and e_date:
                start_iso = f"{s_date}T{s_time}"
                end_iso = f"{e_date}T{e_time}"
                
                popup_html = f"""
                <strong>🚗 {car_id} - {deal.get('Car Make/Model')}</strong><br>
                👤 <b>Müşteri:</b> {deal.get('Client Name')}<br>
                📞 <b>İletişim:</b> {deal.get('Phone/WhatsApp')}<br>
                ⏱️ <b>Teslim Saati:</b> {e_time}<br>
                🆔 <b>Sözleşme No:</b> {deal.get('Deal ID')}
                """
                
                calendar_events.append({
                    "title": f"🚘 {car_id} ({deal.get('Car Make/Model')})",
                    "start": start_iso,
                    "end": end_iso,
                    "color": car_colors[car_id],
                    "description": popup_html
                })

    events_json_payload = json.dumps(calendar_events)
    
    fullcalendar_html_component = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset='utf-8' />
      <script src='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.js'></script>
      <script src="https://unpkg.com/@popperjs/core@2"></script>
      <script src="https://unpkg.com/tippy.js@6"></script>
      <link rel="stylesheet" href="https://unpkg.com/tippy.js@6/dist/tippy.css" />
      <style>
        body {{ font-family: system-ui, -apple-system, sans-serif; margin: 0; padding: 2px; background-color: transparent; }}
        #calendar-canvas {{ max-width: 100%; background: #ffffff; padding: 12px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
        .fc-event {{ cursor: pointer; font-size: 11px !important; font-weight: 500; border: none !important; padding: 2px 4px; border-radius: 4px; }}
        .fc-toolbar-title {{ font-size: 16px !important; font-weight: 600; color: #1e293b; }}
        .fc-button-primary {{ background-color: #3b82f6 !important; border-color: #3b82f6 !important; }}
        .fc-button-primary:hover {{ background-color: #2563eb !important; border-color: #2563eb !important; }}
        .tippy-box[data-theme~='rental-popup'] {{
          background-color: #0f172a;
          color: #f8fafc;
          padding: 8px 12px;
          border-radius: 8px;
          font-size: 12px;
          box-shadow: 0 10px 25px -5px rgba(0,0,0,0.4);
          border: 1px solid #334155;
        }}
      </style>
    </head>
    <body>
      <div id='calendar-canvas'></div>
      <script>
        document.addEventListener('DOMContentLoaded', function() {{
          var calendarEl = document.getElementById('calendar-canvas');
          var calendar = new FullCalendar.Calendar(calendarEl, {{
            initialView: 'dayGridMonth',
            locale: 'tr',
            firstDay: 1,
            height: 480,
            headerToolbar: {{
              left: 'prev,next today',
              center: 'title',
              right: 'dayGridMonth,timeGridWeek'
            }},
            events: {events_json_payload},
            eventDidMount: function(info) {{
              tippy(info.el, {{
                content: info.event.extendedProps.description,
                allowHTML: true,
                theme: 'rental-popup',
                placement: 'top',
                animation: 'shift-away',
                interactive: true
              }});
            }}
          }});
          calendar.render();
        }});
      </script>
    </body>
    </html>
    """
    components.html(fullcalendar_html_component, height=520, scrolling=False)
    st.markdown("---")

    active_fleet_view = fleet_df[fleet_df['Status'] != 'DELETED'] if not fleet_df.empty else pd.DataFrame()
    
    if active_fleet_view.empty:
        st.info("ℹ️ Filoda henüz aktif araç bulunmuyor. Lütfen Finansal Analiz panelinden araç tanımlayın.")
    else:
        col_input, col_grid = st.columns([1.2, 2.6])
        
        with col_input:
            st.markdown("### 📅 Tarih ve Kesin Saat Ayarı")
            start_date = st.date_input("Kiralama Başlangıç Tarihi:", datetime.today().date())
            start_time = st.time_input("Alış Saati:", time(10, 0))
            num_days = st.number_input("Gün Sayısı:", min_value=1, max_value=90, value=3, step=1)
            expected_return_date = start_date + timedelta(days=int(num_days))
            return_time = st.time_input("İade/Teslim Saati:", start_time)
            st.markdown("---")
            st.caption("🔮 HESAPLANAN DÖNÜŞ ZAMANI")
            st.subheader(f"📅 {expected_return_date.strftime('%d.%m.%Y')}")
            st.subheader(f"⏰ Saat: {return_time.strftime('%H:%M')}")

        with col_grid:
            st.markdown("### 🚘 Belirtilen Saatlerde Müsait Olan Araçlar")
            filtered_available_cars = []
            req_start_dt = datetime.combine(start_date, start_time)
            req_end_dt = datetime.combine(expected_return_date, return_time)
            
            for index, car_row in active_fleet_view.iterrows():
                car_id = car_row.get('Car ID', 'N/A')
                car_status = str(car_row.get('Status', 'Available')).strip()
                if car_status in ['Maintenance', 'In Garage']:
                    continue
                has_date_conflict = False
                if not deals_df.empty:
                    car_specific_deals = deals_df[(deals_df['Car ID'] == car_id) & (deals_df['Payment Status'] != 'Closed')]
                    for _, deal_row in car_specific_deals.iterrows():
                        try:
                            d_start_date = pd.to_datetime(deal_row['Rental Start Date']).date()
                            d_start_time = datetime.strptime(str(deal_row['Rental Start Time']), '%H:%M:%S').time() if 'Rental Start Time' in deal_row else time(10,0)
                            d_end_date = pd.to_datetime(deal_row['Rental End Date']).date()
                            d_end_time = datetime.strptime(str(deal_row['Rental End Time']), '%H:%M:%S').time() if 'Rental End Time' in deal_row else time(10,0)
                            existing_start_dt = datetime.combine(d_start_date, d_start_time)
                            existing_end_dt = datetime.combine(d_end_date, d_end_time)
                            if max(req_start_dt, existing_start_dt) <= min(req_end_dt, existing_end_dt):
                                has_date_conflict = True
                                break
                        except Exception: continue
                if not has_date_conflict:
                    filtered_available_cars.append(car_row)
            
            available_cars_df = pd.DataFrame(filtered_available_cars) if filtered_available_cars else pd.DataFrame()

            if available_cars_df.empty:
                st.warning("⚠️ Seçilen zaman aralığında müsait araç kalmamıştır.")
            else:
                for index, row in available_cars_df.iterrows():
                    car_id = row.get('Car ID', 'N/A')
                    rate = safe_int(row.get('Base Daily Rate ($)', 100))
                    total_price = rate * num_days
                    with st.container(border=True):
                        c1, c2, c3, c4 = st.columns([1.1, 1.8, 1.5, 1.0])
                        with c1:
                            st.caption(f"Araç Kodu: {car_id}")
                            st.subheader(row.get('Make/Model', 'N/A'))
                        with c2:
                            st.write(f"🏷️ **Plaka:** {row.get('License Plate','-')}")
                            st.write(f"🎨 **Renk:** {row.get('Color','-')}")
                        with c3:
                            st.metric(label="Günlük Ücret", value=f"${rate}")
                            st.caption(f"Toplam ({num_days} Gün): ${total_price}")
                        with c4:
                            st.write("") 
                            if st.button("Aracı Seç", key=f"bk_{car_id}", use_container_width=True, type="primary"):
                                st.session_state.selected_car = row
                                st.session_state.booking_days = num_days
                                st.session_state.req_start_dt = req_start_dt
                                st.session_state.req_end_dt = req_end_dt
                                st.session_state.show_form = True
                                st.rerun()

        if st.session_state.get('show_form', False):
            st.markdown('<div id="reservation_form_anchor"></div>', unsafe_allow_html=True)
            components.html(
                """
                <script>
                    window.parent.document.getElementById('reservation_form_anchor').scrollIntoView({
                        behavior: 'smooth', block: 'center'
                    });
                </script>
                """, height=0
            )
            car = st.session_state.selected_car
            rate = safe_int(car.get('Base Daily Rate ($)', 100))
            with st.form("contract_form"):
                st.subheader(f"📑 Hızlı Sözleşme — {car.get('Make/Model')} ({car.get('Car ID')})")
                st.write(f"📅 **Kiralama Aralığı:** {st.session_state.req_start_dt.strftime('%d.%m.%Y %H:%M')} ➡️ {st.session_state.req_end_dt.strftime('%d.%m.%Y %H:%M')}")
                client_name = st.text_input("Müşteri Adı Soyadı:")
                client_phone = st.text_input("Telefon / WhatsApp:")
                client_id = st.text_input("Kimlik / Pasaport No:")
                negotiated_rate = st.number_input("Anlaşılan Günlük Ücret ($):", min_value=0, value=int(rate), step=5)
                calculated_total = negotiated_rate * int(st.session_state.booking_days)
                st.metric(label="Hesaplanan Sözleşme Toplam Kira Tutarı", value=f"${calculated_total}")
                
                if st.form_submit_button("Kiralamayı Onayla ve Kaydet"):
                    if client_name and client_phone:
                        sync_with_local_database()
                        deal_id = f"RENT-{datetime.today().strftime('%Y%m')}-{len(st.session_state.deals_db)+1:03d}"
                        new_deal = {
                            'Deal ID': deal_id, 'Client Name': client_name, 'Phone/WhatsApp': client_phone, 'ID/Passport': client_id,
                            'Rental Start Date': st.session_state.req_start_dt.strftime('%Y-%m-%d'),
                            'Rental Start Time': st.session_state.req_start_dt.strftime('%H:%M:%S'),
                            'Rental End Date': st.session_state.req_end_dt.strftime('%Y-%m-%d'),
                            'Rental End Time': st.session_state.req_end_dt.strftime('%H:%M:%S'),
                            'Rental Days': int(st.session_state.booking_days), 'Car ID': car.get('Car ID'), 
                            'Daily Rate': negotiated_rate, 'Total Amount': calculated_total, 'Deposit': 0, 
                            'Payment Status': 'Active', 'Overdue Days': 0, 'Overdue Charge ($)': 0.0, 
                            'Contract Signed': 'Yes', 'Return Condition Notes': '', 'Car Make/Model': car.get('Make/Model')
                        }
                        st.session_state.deals_db = pd.concat([st.session_state.deals_db, pd.DataFrame([new_deal])], ignore_index=True)
                        st.session_state.fleet_db.loc[st.session_state.fleet_db['Car ID'] == car.get('Car ID'), 'Status'] = 'Rented'
                        save_state_to_local()
                        st.success("✔️ Sözleşme başarıyla yerel veri tabanına işlendi!")
                        st.session_state.show_form = False
                        st.rerun()

# ==================== 2. CANLI FİLO DURUM YÖNETİCİSİ ====================
elif st.session_state.current_page == "🛠️ Canlı Filo Yöneticisi":
    st.title("🛠️ CANLI FİLO TAKİBİ, SAAT KONTROLLERİ VE GECİKME DEĞERLENDİRME")
    
    # --- VERIFICATION OPERATOR POP-UP FOR RENTAL CANCELLATION ---
    if "pending_cancel" in st.session_state:
        pc = st.session_state.pending_cancel
        with st.container(border=True):
            st.markdown(f"### 🚨 Kiralama İptal Doğrulama ve Finansal Hesaplama Paneli")
            st.warning(f"**Sözleşme ID:** {pc['deal_id']} | **Araç:** {pc['car_id']} ({pc['model']}) | **Müşteri:** {pc['client']}")
            st.write(f"📅 **Kiralama Başlangıç Tarihi:** {pc['start_date']}")
            st.write(f"⏱️ **Geçen Süre (Gün Bazlı):** {pc['passed_days']} gün")
            
            adjusted_days = pc['passed_days']
            charge_same_day = "Hayır"
            
            # Sub-logic configuration for identical calendar date drops
            if pc['passed_days'] == 0:
                st.info("💡 Bu rezervasyon bugün başlatılmıştır (Aynı Gün İptali).")
                charge_same_day = st.radio("Müşteriye 1 günlük kiralama bedeli yansıtılsın mı?", ["Hayır (Ücretsiz İptal - $0)", "Evet (1 Günlük Ücret Tahsil Et)"])
                adjusted_days = 1 if charge_same_day == "Evet (1 Günlük Ücret Tahsil Et)" else 0
                
            calculated_charge = (adjusted_days * pc['daily_rate']) + pc['overdue_charge']
            st.metric(label="Güncellenen Yeni Finansal Tutar", value=f"${calculated_charge} (Gün Sayısı: {adjusted_days})")
            
            c_col1, c_col2 = st.columns(2)
            if c_col1.button("🔥 İptali Onayla ve Kaydet", type="primary", use_container_width=True):
                # Update specific contract transaction values
                st.session_state.deals_db.at[pc['deal_idx'], 'Rental Days'] = adjusted_days
                st.session_state.deals_db.at[pc['deal_idx'], 'Total Amount'] = calculated_charge
                st.session_state.deals_db.at[pc['deal_idx'], 'Payment Status'] = 'Closed'
                
                # Free the physical car allocation track
                st.session_state.fleet_db.loc[st.session_state.fleet_db['Car ID'] == pc['car_id'], 'Status'] = 'Available'
                
                save_state_to_local()
                del st.session_state.pending_cancel
                st.success("✔️ Rezervasyon başarıyla iptal edildi ve finans kayıtları güncellendi!")
                st.rerun()
                
            if c_col2.button("❌ İşlemi Geri Al", type="secondary", use_container_width=True):
                del st.session_state.pending_cancel
                st.rerun()
        st.markdown("---")

    active_fleet_manager = fleet_df[fleet_df['Status'] != 'DELETED'] if not fleet_df.empty else pd.DataFrame()
    
    if active_fleet_manager.empty:
        st.info("Aktif operasyonel araç bulunmuyor.")
    else:
        for index, row in active_fleet_manager.iterrows():
            car_id = row.get('Car ID', 'N/A')
            current_status = str(row.get('Status', 'Available')).strip()
            current_car_damage_charge = safe_float(row.get('Client Maintenance Charge', 0.0))
            is_overdue = False
            overdue_msg = ""
            active_deal_idx = None
            current_deal_charge = 0.0
            active_deal_row = None
            
            # Scan ledger to resolve references if the vehicle is currently dispatched
            if not deals_df.empty:
                matching_deals = deals_df[(deals_df['Car ID'] == car_id) & (deals_df['Payment Status'] == 'Active')]
                if not matching_deals.empty:
                    active_deal_row = matching_deals.iloc[0]
                    active_deal_idx = matching_deals.index[0]
                    current_deal_charge = safe_float(active_deal_row.get('Overdue Charge ($)', 0.0))
                    try:
                        end_d = pd.to_datetime(active_deal_row['Rental End Date']).date()
                        end_t = datetime.strptime(str(active_deal_row['Rental End Time']), '%H:%M:%S').time()
                        full_expected_return_dt = datetime.combine(end_d, end_t)
                        if datetime.now() > full_expected_return_dt:
                            is_overdue = True
                            time_diff = datetime.now() - full_expected_return_dt
                            overdue_msg = f"⚠️ [SÜRESİ GEÇMİŞ / OVERDUE] - Toplam {time_diff.total_seconds() / 3600:.1f} saattir gecikmede!"
                    except Exception: pass

            with st.container(border=True):
                o_c1, o_c2, o_c3 = st.columns([1.2, 1.8, 2])
                with o_c1:
                    st.subheader(f"`{car_id}` {row.get('Make/Model')}")
                    if is_overdue: st.error(overdue_msg)
                    else: st.caption(f"Durum: {current_status}")
                with o_c2:
                    st.markdown("**Finansal Ek Girdiler:**")
                    new_damage = st.number_input("Araç Fiziksel Hasar Maliyeti ($):", min_value=0.0, value=current_car_damage_charge, key=f"dmg_{car_id}")
                    new_overdue_fee = st.number_input("Zaman Aşımı / Gecikme Cezası Tutar ($):", min_value=0.0, value=current_deal_charge, key=f"ovd_{car_id}", disabled=(current_status != 'Rented'))
                    if st.button("Maliyetleri Kaydet/Güncelle", key=f"btn_maliyet_{car_id}"):
                        st.session_state.fleet_db.loc[st.session_state.fleet_db['Car ID'] == car_id, 'Client Maintenance Charge'] = new_damage
                        if active_deal_idx is not None:
                            st.session_state.deals_db.at[active_deal_idx, 'Overdue Charge ($)'] = new_overdue_fee
                            base_amt = safe_float(st.session_state.deals_db.at[active_deal_idx, 'Total Amount'])
                            st.session_state.deals_db.at[active_deal_idx, 'Total Amount'] = base_amt + new_overdue_fee
                        save_state_to_local()
                        st.success("Finansal kayıtlar güncellendi!")
                        st.rerun()
                with o_c3:
                    st.write(""); st.write("")
                    a1, a2, a3 = st.columns(3)
                    
                    # 1. MAKE AVAILABLE BUTTON
                    if a1.button("🟢 Müsait Yap", key=f"av_{car_id}", use_container_width=True, disabled=(current_status == 'Available')):
                        st.session_state.fleet_db.loc[st.session_state.fleet_db['Car ID'] == car_id, 'Status'] = 'Available'
                        if active_deal_idx is not None:
                            st.session_state.deals_db.at[active_deal_idx, 'Payment Status'] = 'Closed'
                        save_state_to_local()
                        st.rerun()
                        
                    # 2. SEND TO GARAGE/MAINTENANCE BUTTON
                    if a2.button("🛠️ Garaja Çek", key=f"ig_{car_id}", use_container_width=True, disabled=(current_status == 'In Garage')):
                        st.session_state.fleet_db.loc[st.session_state.fleet_db['Car ID'] == car_id, 'Status'] = 'In Garage'
                        if active_deal_idx is not None:
                            st.session_state.deals_db.at[active_deal_idx, 'Payment Status'] = 'Closed'
                        save_state_to_local()
                        st.rerun()
                        
                    # 3. INTERACTIVE CONDITIONAL CANCELLATION TRIGGER
                    if current_status == 'Rented' and active_deal_row is not None:
                        if a3.button("🚨 İptal Et (Cancel)", key=f"cnc_{car_id}", use_container_width=True, type="primary"):
                            try:
                                s_date = pd.to_datetime(active_deal_row['Rental Start Date']).date()
                            except Exception:
                                s_date = datetime.today().date()
                                
                            days_passed = max(0, (datetime.today().date() - s_date).days)
                            
                            st.session_state.pending_cancel = {
                                "deal_idx": active_deal_idx,
                                "deal_id": active_deal_row['Deal ID'],
                                "car_id": car_id,
                                "model": row.get('Make/Model', 'N/A'),
                                "client": active_deal_row['Client Name'],
                                "start_date": s_date.strftime('%Y-%m-%d'),
                                "passed_days": days_passed,
                                "daily_rate": safe_float(active_deal_row.get('Daily Rate', 0.0)),
                                "overdue_charge": safe_float(active_deal_row.get('Overdue Charge ($)', 0.0))
                            }
                            st.rerun()
                    else:
                        a3.button("🔴 Kiraya Ver", key=f"rt_{car_id}", use_container_width=True, disabled=True)

# ==================== 3. FİNANSAL YÖNETİM PANELİ & CRUD DURUMU ====================
else:
    st.title("📊 AYLIK FİNANSAL PERFORMANS & FİLO CRUD YÖNETİMİ")
    computed_next_id = generate_next_car_id(st.session_state.fleet_db)
    
    crud_tabs = st.tabs([
        "📋 Aktif Finansal Ledger", "➕ Yeni Araç Ekle (AUTO-ID)", 
        "✏️ Araç Güncelle (UPDATE)", "❌ Araç Sil (SOFT-DELETE)", "🔒 Şifre Değiştir (SECURITY)"
    ])
    
    with crud_tabs[0]:
        st.subheader("Aktif Filo Finansal Dağılım Tablosu")
        fin_data = []
        for index, row in fleet_df.iterrows():
            car_id = row.get('Car ID', 'N/A')
            status = row.get('Status','Available')
            if status == 'DELETED': continue
            car_deals = deals_df[deals_df['Car ID'] == car_id] if not deals_df.empty else pd.DataFrame()
            total_days = int(car_deals['Rental Days'].apply(safe_int, default=0).sum()) if not car_deals.empty else 0
            total_rental_income = car_deals['Total Amount'].apply(safe_float).sum() if not car_deals.empty else 0.0
            client_maintenance_rev = safe_float(row.get('Client Maintenance Charge', 0.0))
            fin_data.append({
                "Araç ID": car_id, "Model": row.get('Make/Model','-'), "Plaka": row.get('License Plate','-'),
                "Durum": status, "Toplam Kiralama Gün": total_days, 
                "Kiralama ve Gecikme Geliri ($)": total_rental_income, "Hasar Tahsilatı ($)": client_maintenance_rev
            })
        if fin_data: st.dataframe(pd.DataFrame(fin_data), use_container_width=True, hide_index=True)
        else: st.info("Görüntülenecek aktif operasyonel veri yok.")
        
        deleted_cars = fleet_df[fleet_df['Status'] == 'DELETED']
        if not deleted_cars.empty:
            with st.expander("📁 Arşiv: Sistemden Silinmiş Araç Geçmişi Kayıtları"):
                st.dataframe(deleted_cars[["Car ID", "Make/Model", "License Plate", "Status", "Notes"]], use_container_width=True, hide_index=True)

    with crud_tabs[1]:
        st.subheader("➕ Yeni Araç Giriş Modülü")
        st.success(f"🤖 **Benzersiz Akıllı Kod Ataması:** Sıradaki Araç ID'si otomatik olarak **{computed_next_id}** olarak kilitlendi.")
        with st.form("add_car_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            c_model = col1.text_input("Make/Model * (Örn: Volkswagen Touran)")
            c_year = col2.number_input("Year", min_value=1990, max_value=2030, value=2024)
            col3, col4, col5 = st.columns(3)
            c_plate = col3.text_input("License Plate")
            c_color = col4.text_input("Color")
            c_mileage = col5.number_input("Current Mileage", min_value=0, value=0)
            col6, col7 = st.columns(2)
            c_rate = col6.number_input("Base Daily Rate ($) *", min_value=0, value=30)
            c_status = col7.selectbox("Status *", ["Available", "In Garage", "Rented"])
            c_notes = st.text_area("Notes")
            if st.form_submit_button("Yeni Aracı Veri Tabanına Ekle"):
                if not c_model: st.error("❌ Hata: Model bilgisi zorunludur!")
                else:
                    new_car_row = {
                        "Car ID": computed_next_id, "Make/Model": c_model, "Year": int(c_year), "License Plate": c_plate,
                        "Color": c_color, "Current Mileage": int(c_mileage), "Status": c_status,
                        "Base Daily Rate ($)": int(c_rate), "Notes": c_notes, "Client Maintenance Charge": 0.0
                    }
                    st.session_state.fleet_db = pd.concat([st.session_state.fleet_db, pd.DataFrame([new_car_row])], ignore_index=True)
                    save_state_to_local()
                    st.success(f"✔️ Araç `{computed_next_id}` koduyla sisteme işlendi!")
                    st.rerun()

    with crud_tabs[2]:
        st.subheader("✏️ Araç Kayıt Bilgilerini Düzenleme")
        active_for_update = fleet_df[fleet_df['Status'] != 'DELETED'] if not fleet_df.empty else pd.DataFrame()
        if active_for_update.empty: st.caption("Düzenlenecek aktif araç yok.")
        else:
            select_update_id = st.selectbox("Düzenlemek İstediğiniz Aracı Seçin:", active_for_update['Car ID'].unique(), key="up_select")
            car_to_edit = fleet_df[fleet_df['Car ID'] == select_update_id].iloc[0]
            with st.form("update_car_form"):
                u_col1, u_col2 = st.columns(2)
                u_model = u_col1.text_input("Make/Model", value=get_safe_str(car_to_edit.get('Make/Model','')))
                u_year = u_col2.number_input("Year", min_value=1990, max_value=2030, value=safe_int(car_to_edit.get('Year', 2024)))
                u_col3, u_col4, u_col5 = st.columns(3)
                u_plate = u_col3.text_input("License Plate", value=get_safe_str(car_to_edit.get('License Plate','')))
                u_color = u_col4.text_input("Color", value=get_safe_str(car_to_edit.get('Color','')))
                u_mileage = u_col5.number_input("Current Mileage", min_value=0, value=safe_int(car_to_edit.get('Current Mileage', 0)))
                u_col6, u_col7 = st.columns(2)
                u_rate = u_col6.number_input("Base Daily Rate ($)", min_value=0, value=safe_int(car_to_edit.get('Base Daily Rate ($)', 30)))
                status_options = ["Available", "In Garage", "Rented"]
                current_st_idx = status_options.index(car_to_edit['Status']) if car_to_edit['Status'] in status_options else 0
                u_status = u_col7.selectbox("Status", status_options, index=current_st_idx)
                u_notes = st.text_area("Notes", value=get_safe_str(car_to_edit.get('Notes','')))
                if st.form_submit_button("Değişiklikleri Güncelle"):
                    idx = st.session_state.fleet_db[st.session_state.fleet_db['Car ID'] == select_update_id].index[0]
                    st.session_state.fleet_db.at[idx, 'Make/Model'] = u_model
                    st.session_state.fleet_db.at[idx, 'Year'] = int(u_year)
                    st.session_state.fleet_db.at[idx, 'License Plate'] = u_plate
                    st.session_state.fleet_db.at[idx, 'Color'] = u_color
                    st.session_state.fleet_db.at[idx, 'Current Mileage'] = int(u_mileage)
                    st.session_state.fleet_db.at[idx, 'Base Daily Rate ($)'] = int(u_rate)
                    st.session_state.fleet_db.at[idx, 'Status'] = u_status
                    st.session_state.fleet_db.at[idx, 'Notes'] = u_notes
                    save_state_to_local()
                    st.success(f"✔️ `{u_model}` ({select_update_id}) başarıyla güncellendi!")
                    st.rerun()

    with crud_tabs[3]:
        st.subheader("❌ Filodan Güvenli Araç Kaldırma (Soft-Delete)")
        active_for_delete = fleet_df[fleet_df['Status'] != 'DELETED'] if not fleet_df.empty else pd.DataFrame()
        if active_for_delete.empty: st.caption("Silinecek aktif araç yok.")
        else:
            select_delete_id = st.selectbox("Kaldırılacak Aracı Seçin:", active_for_delete['Car ID'].unique(), key="del_select")
            st.warning(f"⚠️ **GÜVENLİK SİSTEMİ MESAJI:** `{select_delete_id}` kodlu aracı sildiğinizde, araç rezervasyon ekranlarından kaldırılır.")
            confirm_check = st.checkbox("Bu aracı silmek ve finans panellerinde arşivlemek istediğimi onaylıyorum.")
            if st.button("🚨 ARACI GÜVENLİ ŞEKİLDE SİL", type="primary", disabled=not confirm_check):
                idx = st.session_state.fleet_db[st.session_state.fleet_db['Car ID'] == select_delete_id].index[0]
                st.session_state.fleet_db.at[idx, 'Status'] = 'DELETED'
                save_state_to_local()
                st.success(f"💥 `{select_delete_id}` kodlu araç başarıyla soft-delete edildi ve arşivlendi!")
                st.rerun()

    with crud_tabs[4]:
        st.subheader("🔒 Sistem Giriş Şifresini Güncelle")
        with st.form("security_password_rotation_form", clear_on_submit=True):
            current_pass_field = st.text_input("Mevcut Şifre (Current Password):", type="password")
            new_pass_field = st.text_input("Yeni Şifre (New Password):", type="password")
            confirm_pass_field = st.text_input("Yeni Şifre Tekrarı (Confirm Password):", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("Güvenlik Şifresini Değiştir", type="primary"):
                if not current_pass_field or not new_pass_field or not confirm_pass_field: st.error("⚠️ Alanların tamamı doldurulmalıdır!")
                elif hash_password(current_pass_field) != st.session_state.password_hash: st.error("❌ Mevcut sistem şifresi hatalı!")
                elif new_pass_field != confirm_pass_field: st.error("❌ Girdiğiniz yeni şifreler birbiriyle eşleşmiyor!")
                elif len(new_pass_field) < 4: st.error("⚠️ Yeni şifreniz en az 4 karakter uzunluğunda olmalıdır!")
                else:
                    st.session_state.password_hash = hash_password(new_pass_field)
                    st.success("✔️ Şifreniz başarıyla güncellenmiştir!")