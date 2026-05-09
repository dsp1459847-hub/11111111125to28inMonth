import pandas as pd
import streamlit as st
from collections import Counter, defaultdict

st.set_page_config(layout="wide", page_title="MAYA AI SUPER VIP")

# --- Custom CSS for Compact View ---
st.markdown("""
    <style>
    .stTable { font-size: 12px !important; }
    .compact-grid {
        display: grid; 
        grid-template-columns: repeat(5, 1fr); 
        gap: 2px; 
    }
    .compact-item {
        font-size: 12px;
        padding: 2px;
        text-align: center;
        border: 1px solid #ccc;
        border-radius: 2px;
    }
    </style>
    """, unsafe_allow_html=True)

def get_val_str(val):
    if pd.isna(val): return ""
    v = str(val).replace('.0', '').strip()
    return v.zfill(2)[-2:] if v.isdigit() else ""

def apply_32_patterns(val_str):
    if not val_str or len(val_str) != 2: return set()
    A, B = int(val_str[0]), int(val_str[1])
    PAT = [(0,1),(0,-1),(1,0),(-1,0),(0,5),(0,-5),(5,0),(-5,0),(1,4),(-1,-4),(4,1),(-4,-1),(1,6),(-1,-6),(6,1),(-6,-1),(1,1),(-1,-1),(1,-1),(-1,1),(5,5),(-5,-5),(5,-5),(-5,5),(1,5),(-1,-5),(1,-5),(-1,5),(5,1),(-5,-1),(5,-1),(-5,1)]
    res = set()
    for da, db in PAT:
        na, nb = A + da, B + db
        if 0 <= na <= 9 and 0 <= nb <= 9: res.add(f"{na}{nb}")
    return res

# --- 7yr Optimized Lookbacks ---
DS_SELF = [6, 5, 8]
GL_CROSS = [3, 1, 4]

def get_combined_logic(df, target_date, shift='DS'):
    hist_df = df[df['DATE'] < pd.to_datetime(target_date)]
    if hist_df.empty: return set(), set()
    
    p_self = set()
    for lb in DS_SELF:
        if len(hist_df) >= lb: p_self.update(apply_32_patterns(hist_df.iloc[-lb]['DS']))
            
    p_cross = set()
    for lb in GL_CROSS:
        if len(hist_df) >= lb: p_cross.update(apply_32_patterns(hist_df.iloc[-lb]['GL']))
            
    common = p_self.intersection(p_cross)
    diff = p_self.symmetric_difference(p_cross) # Dono ka bacha hua data
    return common, diff

# --- Main Dashboard ---
uploaded_file = st.file_uploader("Upload Excel", type=['xlsx'], label_visibility="collapsed")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df['DATE'] = pd.to_datetime(df['DATE'])
    df = df.sort_values('DATE').reset_index(drop=True)
    for c in ['DS','FD','GD','GL','DB','SG']: df[c] = df[c].apply(get_val_str)
    
    t_date = st.date_input("Tareekh Chunein", df['DATE'].max())
    
    st.markdown(f"### 📅 {t_date.strftime('%d-%b-%Y')} | {t_date.strftime('%A')}")

    # --- TOP Prediction Display (Compact) ---
    common, unique = get_combined_logic(df, t_date)
    actual_ds = df[df['DATE'] == pd.to_datetime(t_date)]['DS'].values[0] if not df[df['DATE'] == pd.to_datetime(t_date)].empty else ""

    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("<div style='background:gold; color:black; text-align:center; font-weight:bold;'>⭐ SUPER VIP (Common)</div>", unsafe_allow_html=True)
        html = "<div class='compact-grid'>"
        for n in sorted(list(common)):
            bg = "#28a745" if n == actual_ds else "#f0f2f6"
            html += f"<div class='compact-item' style='background:{bg};'>{n}</div>"
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    with col2:
        st.markdown("<div style='background:#007bff; color:white; text-align:center; font-weight:bold;'>💎 Support (Unique)</div>", unsafe_allow_html=True)
        html = "<div class='compact-grid' style='grid-template-columns: repeat(10, 1fr);'>"
        for n in sorted(list(unique)):
            bg = "#28a745" if n == actual_ds else "#f0f2f6"
            html += f"<div class='compact-item' style='background:{bg};'>{n}</div>"
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    st.markdown("---")

    # --- 11-Day History (Pehle Jaisa Format) ---
    st.subheader("📜 11-Day History (Audit)")
    hist_view = df[df['DATE'] <= pd.to_datetime(t_date)].tail(11).copy().sort_values('DATE', ascending=False)
    
    audit_data = []
    for idx, row in hist_view.iterrows():
        # Aaj ke date ke liye predictions nikalna
        c_ank, u_ank = get_combined_logic(df, row['DATE'])
        val = row['DS']
        
        status = val # Default
        if val in c_ank: status = f"⭐ {val} (Common)"
        elif val in u_ank: status = f"🟢 {val} (Support)"
        
        audit_data.append({
            "Tarikh": row['DATE'].strftime('%d-%m'),
            "Bar (Day)": row['DATE'].strftime('%A'),
            "Disawar Result": status,
            "Faridabad": row['FD'],
            "Gaziabad": row['GD'],
            "Gali": row['GL'],
            "Delhi Bajar": row['DB'],
            "Shri Ganesh": row['SG']
        })
    
    st.table(pd.DataFrame(audit_data))

    # Real Metrics
    if actual_ds != "":
        if actual_ds in common: st.success("SUCCESS: Aaj ka result SUPER VIP se pass hua!")
        elif actual_ds in unique: st.info("PASS: Aaj ka result Support se pass hua!")
        else: st.error("FAIL: Aaj match nahi hua.")
            
