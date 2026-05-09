import pandas as pd
import streamlit as st
from collections import Counter, defaultdict

st.set_page_config(layout="wide", page_title="MAYA AI: 3-Shift Success Engine")

# --- Cleaning Function ---
def get_val_str(val):
    if pd.isna(val): return ""
    v = str(val).replace('.0', '').strip()
    return v.zfill(2)[-2:] if v.isdigit() else ""

# --- 32 Patterns Logic (Strict Boundary 0-9) ---
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
        if 0 <= na <= 9 and 0 <= nb <= 9: # Boundary check
            res.append(f"{na}{nb}")
    return res

# --- Data Audit Filters (Jo humne analysis se nikale) ---
BEST_LOOKBACKS = {
    'DS': [6, 5, 10, 8, 9],
    'FD': [2, 5, 9, 7, 3],
    'GD': [3, 7, 5, 2, 6],
    'GL': [2, 4, 6, 5, 3],
    'DB': [2, 6, 5, 4, 9],
    'SG': [3, 6, 8, 5, 2]
}

def get_filtered_predictions(df, target_date, shift):
    hist_df = df[df['DATE'] < pd.to_datetime(target_date)].copy()
    if hist_df.empty: return []

    scores = defaultdict(float)
    active_days = BEST_LOOKBACKS.get(shift, [2, 3, 5, 6])

    for lb in active_days:
        if len(hist_df) >= lb:
            prev_val = hist_df.iloc[-lb][shift]
            if prev_val and prev_val != "XX":
                # Apply 32 patterns to the most successful days
                candidates = apply_32_patterns(prev_val)
                for c in candidates:
                    scores[c] += 2.0 # In dino ko zyada weightage

    # Final top 30 based on scores
    return [n for n, s in sorted(scores.items(), key=lambda x: -x[1])[:30]]

# --- UI Setup ---
st.title("🎯 Maya AI: Triple-Shift Accuracy Dashboard")
uploaded_file = st.file_uploader("Upload 0DSP0 Excel", type=['xlsx', 'csv'])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    df['DATE'] = pd.to_datetime(df['DATE'])
    df = df.sort_values('DATE').reset_index(drop=True)
    cols = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
    for c in cols: df[c] = df[c].apply(get_val_str)

    target_date = st.date_input("Tareekh Chunein", df['DATE'].max())
    
    # Dashboard Grid
    st.markdown(f"### 📊 Prediction Grid: {target_date.strftime('%d-%m-%Y')} ({target_date.strftime('%A')})")
    actual_row = df[df['DATE'] == pd.to_datetime(target_date)]
    pred_cols = st.columns(6)
    day_predictions = {}

    for i, shift in enumerate(cols):
        with pred_cols[i]:
            st.markdown(f"<div style='background:#1E1E1E; color:gold; padding:5px; text-align:center; font-weight:bold; border-radius:5px;'>{shift}</div>", unsafe_allow_html=True)
            preds = get_filtered_predictions(df, target_date, shift)
            day_predictions[shift] = preds
            actual = actual_row[shift].values[0] if not actual_row.empty else ""
            
            p_html = "<div style='display:grid; grid-template-columns: repeat(5, 1fr); gap:2px; margin-top:5px;'>"
            for p in preds:
                bg = "#28a745" if p == actual and actual != "" else "#f0f2f6"
                color = "white" if p == actual else "black"
                p_html += f"<div style='background:{bg}; color:{color}; font-size:11px; padding:3px; text-align:center; border:1px solid #ddd;'>{p}</div>"
            p_html += "</div>"
            st.markdown(p_html, unsafe_allow_html=True)

    st.divider()
    
    # --- Real 11-Day Live History ---
    st.subheader("📜 Last 11 Days Performance Audit")
    hist_view = df[df['DATE'] <= pd.to_datetime(target_date)].tail(11).copy().sort_values('DATE', ascending=False)
    
    audit_data = []
    for idx, row in hist_view.iterrows():
        row_dict = {"Date": row['DATE'].strftime('%d-%b'), "Day": row['DATE'].strftime('%a')}
        for s in cols:
            d_preds = get_filtered_predictions(df, row['DATE'], s)
            val = row[s]
            row_dict[s] = f"🟢 {val}" if val in d_preds and val != "" else val
        audit_data.append(row_dict)
    
    st.table(pd.DataFrame(audit_data))
    
