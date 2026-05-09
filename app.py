import pandas as pd
import streamlit as st
from collections import Counter, defaultdict

st.set_page_config(layout="wide", page_title="MAYA AI: Correct Audit")

def get_val_str(val):
    if pd.isna(val): return ""
    v = str(val).replace('.0', '').strip()
    return v.zfill(2)[-2:] if v.isdigit() else ""

# --- Core Prediction Logic (Independent for each day) ---
def get_predictions(df, target_date, shift_name):
    # Sirf us din se pehle ka data lena (No Cheating)
    hist_df = df[df['DATE'] < pd.to_datetime(target_date)].copy()
    if hist_df.empty: return []

    scores = defaultdict(float)
    curr_weekday = pd.to_datetime(target_date).weekday()
    curr_day_num = pd.to_datetime(target_date).day

    # 1. Bar-wise logic
    bw = hist_df[hist_df['DATE'].dt.weekday == curr_weekday][shift_name].tail(15)
    for v in bw: scores[v] += 2.5
    # 2. Date-wise logic
    dw = hist_df[hist_df['DATE'].dt.day == curr_day_num][shift_name].tail(6)
    for v in dw: scores[v] += 2.0
    # 3. T1/T2/T3 logic
    for i, w in zip([1, 2, 3], [1.5, 1.2, 1.0]):
        if len(hist_df) >= i:
            val = hist_df.iloc[-i][shift_name]
            if val: scores[val] += w

    return [n for n, s in sorted(scores.items(), key=lambda x: -x[1])[:30]]

# --- UI Setup ---
st.title("🎯 Maya AI: Real Accuracy Dashboard")
uploaded_file = st.file_uploader("Upload Excel File", type=['xlsx'])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df['DATE'] = pd.to_datetime(df['DATE'])
    df = df.sort_values('DATE').reset_index(drop=True)
    
    cols = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
    for c in cols: df[c] = df[c].apply(get_val_str)

    target_date = st.date_input("Tareekh Chunein", df['DATE'].max())
    
    # --- Prediction Grid Display ---
    st.markdown(f"### 📅 Predictions for {target_date.strftime('%d-%m-%Y')} ({target_date.strftime('%A')})")
    
    actual_row = df[df['DATE'] == pd.to_datetime(target_date)]
    pred_columns = st.columns(6)
    current_day_preds = {}

    for i, shift in enumerate(cols):
        with pred_columns[i]:
            st.markdown(f"<div style='background:#007bff; color:white; padding:5px; text-align:center; font-weight:bold; border-radius:5px;'>{shift}</div>", unsafe_allow_html=True)
            preds = get_predictions(df, target_date, shift)
            current_day_preds[shift] = preds
            actual = actual_row[shift].values[0] if not actual_row.empty else ""
            
            # Compact Grid (5 numbers per row)
            p_html = "<div style='display:grid; grid-template-columns: repeat(5, 1fr); gap:2px; margin-top:5px;'>"
            for p in preds:
                bg = "#28a745" if p == actual and actual != "" else "#f0f2f6"
                color = "white" if p == actual else "black"
                p_html += f"<div style='background:{bg}; color:{color}; font-size:11px; padding:3px; text-align:center; border:1px solid #ddd;'>{p}</div>"
            p_html += "</div>"
            st.markdown(p_html, unsafe_allow_html=True)

    st.divider()

    # --- Real 11-Day History with Accurate Green Highlighting ---
    st.subheader("📜 Last 11 Days History (True Backtest)")
    
    history_view = df[df['DATE'] <= pd.to_datetime(target_date)].tail(11).copy()
    history_view = history_view.sort_values('DATE', ascending=False)
    
    # Is table ko row-by-row analyze karenge taaki highlight sahi ho
    final_table_data = []
    for idx, row in history_view.iterrows():
        row_dict = {"Date": row['DATE'].strftime('%d-%b'), "Day": row['DATE'].strftime('%a')}
        for shift in cols:
            # Har din ke liye uske pichle data se prediction nikalna
            day_preds = get_predictions(df, row['DATE'], shift)
            val = row[shift]
            if val in day_preds and val != "":
                row_dict[shift] = f"🟢 {val}" # Pass mark
            else:
                row_dict[shift] = val
        final_table_data.append(row_dict)

    # Styling and displaying the history
    st.table(pd.DataFrame(final_table_data))

    # Real Metrics
    if not actual_row.empty:
        hits = sum([1 for s in cols if actual_row[s].values[0] in current_day_preds[s]])
        st.info(f"**Final Audit:** Aaj की 6 में से **{hits}** शिफ्ट पास हुई हैं।")
        
