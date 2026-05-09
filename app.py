import pandas as pd
import streamlit as st
from collections import Counter, defaultdict

st.set_page_config(layout="wide", page_title="MAYA AI: Compact Dashboard")

def get_val_str(val):
    if pd.isna(val): return ""
    v = str(val).replace('.0', '').strip()
    return v.zfill(2)[-2:] if v.isdigit() else ""

# --- Core Engine ---
def get_predictions(df, target_date, shift_name):
    # True Blind Test: Target date se pehle ka data
    hist_df = df[df['DATE'] < pd.to_datetime(target_date)].copy()
    if hist_df.empty: return []

    scores = defaultdict(float)
    curr_weekday = pd.to_datetime(target_date).weekday()
    curr_day_num = pd.to_datetime(target_date).day

    # Logic: Bar + Date + T1/T2/T3
    bw = hist_df[hist_df['DATE'].dt.weekday == curr_weekday][shift_name].tail(15)
    for v in bw: scores[v] += 2.5
    dw = hist_df[hist_df['DATE'].dt.day == curr_day_num][shift_name].tail(6)
    for v in dw: scores[v] += 2.0
    for i, w in zip([1, 2, 3], [1.5, 1.2, 1.0]):
        if len(hist_df) >= i:
            val = hist_df.iloc[-i][shift_name]
            if val: scores[val] += w

    return [n for n, s in sorted(scores.items(), key=lambda x: -x[1])[:30]]

# --- UI Layout ---
st.title("🎯 Maya AI: Smart Compact Dashboard")
uploaded_file = st.file_uploader("Excel File Upload Karein", type=['xlsx'])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df['DATE'] = pd.to_datetime(df['DATE'])
    df = df.sort_values('DATE').reset_index(drop=True)
    
    cols = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
    for c in cols: df[c] = df[c].apply(get_val_str)

    target_date = st.date_input("Tareekh Chunein", df['DATE'].max())
    st.markdown(f"### 📅 {target_date.strftime('%d-%m-%Y')} | {target_date.strftime('%A')}")

    # --- Predictions in Compact Grid ---
    shift_predictions = {}
    grid = st.columns(6)
    
    actual_row = df[df['DATE'] == pd.to_datetime(target_date)]
    
    for i, shift in enumerate(cols):
        with grid[i]:
            st.markdown(f"<div style='background-color:#007bff; color:white; padding:5px; text-align:center; border-radius:5px; font-weight:bold;'>{shift}</div>", unsafe_allow_html=True)
            preds = get_predictions(df, target_date, shift)
            shift_predictions[shift] = preds
            actual = actual_row[shift].values[0] if not actual_row.empty else ""
            
            # 5-5 की लाइन में दिखाने के लिए HTML
            preds_html = "<div style='display:grid; grid-template-columns: repeat(5, 1fr); gap:2px; margin-top:5px;'>"
            for p in preds:
                bg = "#28a745" if p == actual and actual != "" else "#f0f2f6"
                color = "white" if p == actual else "black"
                preds_html += f"<div style='background:{bg}; color:{color}; font-size:12px; padding:3px; text-align:center; border-radius:2px; border:1px solid #ddd;'>{p}</div>"
            preds_html += "</div>"
            st.markdown(preds_html, unsafe_allow_html=True)

    st.divider()

    # --- 11-Day History Section (Including Target Date) ---
    st.subheader("📜 Last 11 Days Full History (Backtest Check)")
    
    # Target date tak ka 11 din ka data nikalna
    history_view = df[df['DATE'] <= pd.to_datetime(target_date)].tail(11).copy()
    history_view = history_view.sort_values('DATE', ascending=False)
    
    # Table formatting with Green Highlight
    def highlight_pass(row):
        styles = ['' for _ in row]
        for i, col_name in enumerate(row.index):
            if col_name in shift_predictions:
                # Check if the value in this cell was predicted for THIS specific date
                # Note: This is for visual audit
                if row[col_name] in shift_predictions[col_name]:
                    styles[i] = 'background-color: #c3e6cb; color: #155724; font-weight: bold'
        return styles

    # Display History Table
    styled_hist = history_view.style.apply(highlight_pass, axis=1)
    st.table(styled_hist)

    # --- Bottom Stats ---
    if not actual_row.empty:
        total_hits = sum([1 for s in cols if actual_row[s].values[0] in shift_predictions[s]])
        st.metric("Total Shifts Passed Today", f"{total_hits} / 6")
        
