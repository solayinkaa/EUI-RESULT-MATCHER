# ESUI Streamlit App with Improved Matching Logic
import streamlit as st
import pandas as pd
import io
import numpy as np
from typing import Tuple, List, Dict

# Streamlit page setup
st.set_page_config(page_title="ESUI Result Auto-Matcher", page_icon="📊")

st.markdown("""
    <style>
        .main-header { text-align: center; color: #1f77b4; margin-bottom: 2rem; }
        .stats-container { background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0; }
        .warning-box { background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 0.25rem; padding: 0.75rem; margin: 0.5rem 0; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">📊 ESUI Faculty of Science Auto-Matcher</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666;">Automated matching of manual results with portal templates</p>', unsafe_allow_html=True)

def normalize(val):
    return str(val).strip().lower() if pd.notna(val) else ''

def clean_and_match(manual_df: pd.DataFrame, template_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    # Clean column names
    manual_df.columns = manual_df.columns.str.strip()
    template_df.columns = template_df.columns.str.strip()

    # Preserve original names
    template_df['Name_Original'] = template_df['Name']
    template_df['Department_Original'] = template_df['Department']

    # Normalize fields
    manual_df['MatNo_clean'] = manual_df['MatNo'].str.strip().str.upper()
    manual_df['Name_clean'] = manual_df['Name'].apply(normalize)
    manual_df['Department_clean'] = manual_df['Department'].apply(normalize)

    template_df['MatNo_clean'] = template_df['MatNo'].str.strip().str.upper()
    template_df['Name_clean'] = template_df['Name'].apply(normalize)
    template_df['Department_clean'] = template_df['Department'].apply(normalize)

    # Prepare output and logs
    template_df['CA'] = ''
    template_df['Exam'] = ''
    matched, unmatched = [], []

    # Matching logic
    def match_scores(row):
        matno = row['MatNo_clean']
        match = manual_df[manual_df['MatNo_clean'] == matno] if matno else pd.DataFrame()

        if match.empty:
            match = manual_df[(manual_df['Name_clean'] == row['Name_clean']) &
                              (manual_df['Department_clean'] == row['Department_clean'])]

        if not match.empty:
            ca = str(match.iloc[0]['CA']).strip()
            exam = str(match.iloc[0]['Exam']).strip()
            matched.append({
                'MatNo': row['MatNo'], 'Name': row['Name_Original'],
                'Department': row['Department_Original'], 'CA': ca, 'Exam': exam
            })
            return pd.Series([ca, exam])
        else:
            unmatched.append({
                'MatNo': row['MatNo'], 'Name': row['Name_Original'],
                'Department': row['Department_Original']
            })
            return pd.Series(['', ''])

    template_df[['CA', 'Exam']] = template_df.apply(match_scores, axis=1)
    template_df['Name'] = template_df['Name_Original']
    template_df['Department'] = template_df['Department_Original']
    template_df.drop(columns=['Name_Original', 'Department_Original', 'MatNo_clean', 'Name_clean', 'Department_clean'], inplace=True)

    return template_df, {
        'matched': matched,
        'unmatched': unmatched,
        'match_count': len(matched),
        'unmatched_count': len(unmatched),
        'total': len(template_df)
    }

# File upload UI
st.subheader("📁 Upload Files")
col1, col2 = st.columns(2)
with col1:
    manual_file = st.file_uploader("📄 Manual Result CSV", type=["csv"])
with col2:
    template_file = st.file_uploader("📄 Portal Template CSV", type=["csv"])

if manual_file and template_file:
    try:
        manual_df = pd.read_csv(manual_file, dtype=str)
        template_df = pd.read_csv(template_file, dtype=str)

        st.success("✅ Files loaded successfully.")

        if st.button("🚀 Process and Match Results", type="primary"):
            with st.spinner("Matching records..."):
                final_df, stats = clean_and_match(manual_df, template_df)

            st.success("✅ Matching complete.")
            st.metric("🎯 Total Records", stats['total'])
            st.metric("✅ Matched Records", stats['match_count'])
            st.metric("❌ Unmatched Records", stats['unmatched_count'])

            with st.expander("👁 Preview Final Results"):
                st.dataframe(final_df.head(10))

            timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
            output_csv = final_df.to_csv(index=False).encode('utf-8')

            st.download_button(
                label="📥 Download Completed Template",
                data=output_csv,
                file_name=f"BIO111_Results_Completed_{timestamp}.csv",
                mime="text/csv"
            )

            if stats['unmatched']:
                unmatched_df = pd.DataFrame(stats['unmatched'])
                with st.expander("❌ View Unmatched Records"):
                    st.dataframe(unmatched_df)

                unmatched_csv = unmatched_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⚠️ Download Unmatched Log",
                    data=unmatched_csv,
                    file_name=f"BIO111_Unmatched_Log_{timestamp}.csv",
                    mime="text/csv"
                )

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
