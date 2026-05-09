import pandas as pd
import streamlit as st
from collections import Counter, defaultdict

# Page setup for wide view
st.set_page_config(layout="wide", page_title="MAYA AI COMPACT")

# Custom CSS for ultra-small boxes and tight layout
st.markdown("""
    <style>
    .reportview-container .main .block-container{ padding-top: 1rem; }
    .stTable { font-size: 12px !important; }
    .jodi-box {
        display: grid; 
        grid-template-columns: repeat(5, 1fr); 
        gap: 2px; 
        margin-top: 5px;
    }
    .jodi-item {
        font-size: 13px !important;
        padding: 2px !important;
        text-align: center;
        border: 1px solid #ddd;
        border-radius: 2px;
    }
    </style>
    """, unsafe_allow_html=True)

def get_val_str(val):
    if pd.isna(val): return ""
    v = str(val).replace('.0', '').strip()
    return v.zfill(2)[-2:] if v.isdigit() else ""

# Analysis se nikale gaye Best Lookback Days
BEST_LOOKBACKS = {
    'DS': [6, 5, 10, 8, 9], 'FD': [2, 5, 9, 7, 3], 'GD': [3, 7, 5, 2, 6],
    'GL': [2, 4, 6, 5, 3], 'DB': [2, 6, 5, 4, 9], 'SG': [3, 6, 8, 5, 2]
}

def apply_32_patterns(val_str):
    if not val_str or len(val_str) != 2: return []
    A, B = int(val_str[0]), int(val_str[1])
    PATTERNS = [
        (0,1), (0,-1), (1,0), (-1,0), (0,5), (0,-5), (5,0), (-5,0),
        (1,4), (-1,-4), (4,1), (-4,-1), (1,6), (-1,-6), (6,1), (-6,-1),
        (1,1), (-1,-1), (1,-1), (-1,1), (5,5), (-5,-5), (5,-5), (-5,5),
        (1,5), (-1,-5), (1,-5), (-1,5), (5,1), (-5,-1), (5,-1), (-5,1)
    ]
    res = []
    for da, db in PATTERNS:
        na, nb = A + da, B + db
        if 0 <= na <= 9 and 0 <= nb <= 9: res.append(f"{na}{nb}")
    return res

def get_filtered_preds(df, target_date, shift):
    hist_df = df[df['DATE'] < pd.to_datetime(target_date)]
    if hist_df.empty: return []
    scores = defaultdict(float)
    active_days = BEST_LOOKBACKS.get(shift, [2, 3, 5, 6])
    for lb in active_days:
        if len(hist_df) >= lb:
            prev_val = hist_df.iloc[-lb][shift]
            if prev_val and prev_val != "XX":
                for c in apply_32_patterns(prev_val): scores[c] += 2.0
    return [n for n, s in sorted(scores.items(), key=lambda x: -x[1])[:30]]

# --- UI Layout ---
uploaded_file = st.file_uploader("Upload Excel", type=['xlsx', 'csv'], label_visibility="collapsed")

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    df['DATE'] = pd.to_datetime(df['DATE'])
    df = df.sort_values('DATE').reset_index(drop=True)
    cols = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
    for c in cols: df[c] = df[c].apply(get_val_str)

    t_date = st.date_input("Select Date", df['DATE'].max())
    
    # Prediction Section
    st.write(f"### 🎯 Prediction: {t_date.strftime('%d-%b')} ({t_date.strftime('%A')})")
    actual_row = df[df['DATE'] == pd.to_datetime(t_date)]
    p_cols = st.columns(6)
    all_current_preds = {}

    for i, shift in enumerate(cols):
        with p_cols[i]:
            st.markdown(f"<div style='background:#1E1E1E; color:gold; text-align:center; font-weight:bold; font-size:14px;'>{shift}</div>", unsafe_allow_html=True)
            preds = get_filtered_preds(df, t_date, shift)
            all_current_preds[shift] = preds
            actual = actual_row[shift].values[0] if not actual_row.empty else ""
            
            p_html = "<div class='jodi-box'>"
            for p in preds:
                bg = "#28a745" if p == actual and actual != "" else "#f0f2f6"
                color = "white" if p == actual else "black"
                p_html += f"<div class='jodi-item' style='background:{bg}; color:{color};'>{p}</div>"
            p_html += "</div>"
            st.markdown(p_html, unsafe_allow_html=True)

    # --- History Section (Bar-wise & Date-wise) ---
    st.markdown("---")
    st.write("### 📜 11-Day History (Bar + Date)")
    hist_view = df[df['DATE'] <= pd.to_datetime(t_date)].tail(11).copy().sort_values('DATE', ascending=False)
    
    audit_data = []
    for idx, row in hist_view.iterrows():
        # 'Bar' aur 'Date' ko alag columns mein dikhana
        row_dict = {
            "Tarikh": row['DATE'].strftime('%d-%m'),
            "Bar (Day)": row['DATE'].strftime('%A')
        }
        for s in cols:
            d_preds = get_filtered_preds(df, row['DATE'], s)
            val = row[s]
            # Agar us din prediction pass thi to Green Emoji
            row_dict[s] = f"🟢 {val}" if val in d_preds and val != "" else val
        audit_data.append(row_dict)
    
    st.table(pd.DataFrame(audit_data))
    
