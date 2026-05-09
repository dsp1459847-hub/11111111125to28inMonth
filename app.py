import pandas as pd
import streamlit as st
from collections import Counter, defaultdict

st.set_page_config(layout="wide")

def get_val_str(val):
    if pd.isna(val): return ""
    v = str(val).replace('.0', '').strip()
    return v.zfill(2)[-2:] if v.isdigit() else ""

def apply_32_patterns(val_str):
    if not val_str or len(val_str) != 2: return set()
    A, B = int(val_str[0]), int(val_str[1])
    # 32 Patterns Logic
    PAT = [(0,1),(0,-1),(1,0),(-1,0),(0,5),(0,-5),(5,0),(-5,0),(1,4),(-1,-4),(4,1),(-4,-1),(1,6),(-1,-6),(6,1),(-6,-1),(1,1),(-1,-1),(1,-1),(-1,1),(5,5),(-5,-5),(5,-5),(-5,5),(1,5),(-1,-5),(1,-5),(-1,5),(5,1),(-5,-1),(5,-1),(-5,1)]
    res = set()
    for da, db in PAT:
        na, nb = A + da, B + db
        if 0 <= na <= 9 and 0 <= nb <= 9: res.add(f"{na}{nb}")
    return res

# --- Optimized Lookbacks from 7yr Audit ---
DS_SELF_DAYS = [6, 5, 8]
GL_CROSS_DAYS = [3, 1, 4]

def get_super_vip_logic(df, target_date):
    hist_df = df[df['DATE'] < pd.to_datetime(target_date)]
    if hist_df.empty: return set(), set(), set()
    
    # 1. DS Self Pool
    p_ds = set()
    for lb in DS_SELF_DAYS:
        if len(hist_df) >= lb: p_ds.update(apply_32_patterns(hist_df.iloc[-lb]['DS']))
            
    # 2. GL Cross Pool
    p_gl = set()
    for lb in GL_CROSS_DAYS:
        if len(hist_df) >= lb: p_gl.update(apply_32_patterns(hist_df.iloc[-lb]['GL']))
            
    common = p_ds.intersection(p_gl)
    diff_ds = p_ds.difference(p_gl)
    diff_gl = p_gl.difference(p_ds)
    
    return common, diff_ds, diff_gl

# --- Main Dashboard ---
uploaded_file = st.file_uploader("Upload 0DSP0 File")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df['DATE'] = pd.to_datetime(df['DATE'])
    for c in ['DS','FD','GD','GL','DB','SG']: df[c] = df[c].apply(get_val_str)
    
    t_date = st.date_input("Select Date", df['DATE'].max())
    
    common, d_ds, d_gl = get_super_vip_logic(df, t_date)
    actual_ds = df[df['DATE'] == pd.to_datetime(t_date)]['DS'].values[0] if not df[df['DATE'] == pd.to_datetime(t_date)].empty else ""

    # Visual Display
    st.write(f"### 🛡️ Multi-Logic VIP Audit: {t_date.strftime('%d-%b')}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.success(f"⭐ COMMON (SUPER VIP): {len(common)} Ank")
        st.write(sorted(list(common)))
        if actual_ds in common: st.markdown("🎯 **HIT IN COMMON!**")
        
    with col2:
        st.info(f"💎 DS-ONLY: {len(d_ds)} Ank")
        st.write(sorted(list(d_ds)))
        if actual_ds in d_ds: st.markdown("🎯 **HIT IN DS-ONLY!**")
        
    with col3:
        st.warning(f"🎯 GL-CROSS: {len(d_gl)} Ank")
        st.write(sorted(list(d_gl)))
        if actual_ds in d_gl: st.markdown("🎯 **HIT IN GL-CROSS!**")

    # --- THE KILLER BACKTEST ENGINE ---
    st.divider()
    st.subheader("📊 15-Day Winning Logic Tracker")
    st.write("Ye table bataegi ki pichle 15 dino mein kaun sa logic sabse zyada pass hua hai.")
    
    audit_results = []
    test_range = df[df['DATE'] <= pd.to_datetime(t_date)].tail(15)
    
    for idx, row in test_range.iterrows():
        c, ds, gl = get_super_vip_logic(df, row['DATE'])
        res = row['DS']
        winner = "❌ FAIL"
        if res in c: winner = "⭐ COMMON (SUPER VIP)"
        elif res in ds: winner = "💎 DS-ONLY"
        elif res in gl: winner = "🎯 GL-CROSS"
        
        audit_results.append({"Date": row['DATE'].date(), "Day": row['DATE'].strftime('%A'), "Result": res, "Winner": winner})
    
    st.table(pd.DataFrame(audit_results))
            
