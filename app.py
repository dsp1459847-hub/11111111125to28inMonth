import pandas as pd
import streamlit as st
from collections import Counter, defaultdict

st.set_page_config(layout="wide", page_title="MAYA AI: Super Dashboard")

def get_val_str(val):
    if pd.isna(val): return ""
    v = str(val).replace('.0', '').strip()
    return v.zfill(2)[-2:] if v.isdigit() else ""

# --- Core Engine Logic ---
def get_predictions(df, target_date, shift_name):
    hist_df = df[df['DATE'] < pd.to_datetime(target_date)].copy()
    if hist_df.empty: return []

    scores = defaultdict(float)
    curr_weekday = pd.to_datetime(target_date).weekday()
    curr_day_num = pd.to_datetime(target_date).day

    # 1. Bar-wise (Pichle 15 hafte ka same day)
    bw = hist_df[hist_df['DATE'].dt.weekday == curr_weekday][shift_name].tail(15)
    for v in bw: scores[v] += 2.5
    
    # 2. Date-wise (Pichle 6 mahino ki same date)
    dw = hist_df[hist_df['DATE'].dt.day == curr_day_num][shift_name].tail(6)
    for v in dw: scores[v] += 2.0

    # 3. T1/T2/T3 Triple History Integration
    for i, weight in zip([1, 2, 3], [1.5, 1.2, 1.0]):
        if len(hist_df) >= i:
            val = hist_df.iloc[-i][shift_name]
            if val: scores[val] += weight

    return [n for n, s in sorted(scores.items(), key=lambda x: -x[1])[:30]]

# --- UI Layout ---
st.title("🎯 Maya AI: All-Shift Prediction Dashboard")
uploaded_file = st.file_uploader("Excel File Upload Karein", type=['xlsx'])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df['DATE'] = pd.to_datetime(df['DATE'])
    df = df.sort_values('DATE').reset_index(drop=True)
    
    cols = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
    for c in cols: df[c] = df[c].apply(get_val_str)

    target_date = st.date_input("Tareekh Chunein", df['DATE'].max())
    
    # --- Sabhi Shifton Ka Prediction Ek Saath ---
    st.subheader(f"📅 Predictions for {target_date.strftime('%d-%m-%Y')} ({target_date.strftime('%A')})")
    
    results = {}
    actual_results = df[df['DATE'] == pd.to_datetime(target_date)]
    
    # Display in Columns
    grid = st.columns(6)
    for i, shift in enumerate(cols):
        with grid[i]:
            st.markdown(f"### {shift}")
            preds = get_predictions(df, target_date, shift)
            actual = actual_results[shift].values[0] if not actual_results.empty else None
            
            # Highlight Pass/Fail
            for p in preds:
                if p == actual:
                    st.markdown(f"**<span style='color:green; font-size:18px;'>✅ {p}</span>**", unsafe_allow_html=True)
                else:
                    st.write(p)
            results[shift] = preds

    st.divider()

    # --- Triple History Section (Prediction ke Niche) ---
    st.subheader("📜 Pattern History (T1, T2, T3)")
    hist_data = df[df['DATE'] < pd.to_datetime(target_date)].tail(3)[['DATE'] + cols]
    
    # Ulta karke dikhayenge taaki T1 sabse upar rahe
    hist_data = hist_data.sort_values('DATE', ascending=False)
    
    # Styling for T-labels
    t_labels = ["T1 (Yesterday)", "T2 (Day Before)", "T3 (3 Days Ago)"]
    hist_data.insert(0, "Type", t_labels[:len(hist_data)])
    
    st.table(hist_data)

    # --- Monthly Accuracy Auditor ---
    st.divider()
    if st.button("Run Full Month Backtest Audit"):
        st.write("Checking last 30 days...")
        audit_log = []
        test_range = df[df['DATE'] > (df['DATE'].max() - pd.Timedelta(days=30))]
        
        for idx, row in test_range.iterrows():
            day_hits = 0
            for s in cols:
                p_list = get_predictions(df, row['DATE'], s)
                if row[s] in p_list and row[s] != "":
                    day_hits += 1
            audit_log.append({"Date": row['DATE'].date(), "Pass Shifts": day_hits})
        
        audit_df = pd.DataFrame(audit_log)
        st.line_chart(audit_df.set_index('Date'))
        st.write(f"Average Daily Pass: **{audit_df['Pass Shifts'].mean():.2f} Shifts**")
      
