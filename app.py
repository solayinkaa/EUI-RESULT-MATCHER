import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(page_title="Result Matcher", layout="centered")
st.title("📘 EDSU Faculty of Science Auto-Matcher for Manual / Portal Template Results")
st.markdown("Upload the **Result prepared manually in CSV** and the **CSV Template downloaded from the Result Portal** to generate the upload-ready file.")

# Upload Section
manual_file = st.file_uploader("📄 Upload XYZ 111 Manual Result in CSV", type="csv")
template_file = st.file_uploader("📄 Upload XZY 111 Result Template from Portal in CSV", type="csv")

if manual_file and template_file:
    # Load CSVs
    manual_df = pd.read_csv(manual_file, dtype=str)
    template_df = pd.read_csv(template_file, dtype=str)

    # Clean headers
    manual_df.columns = manual_df.columns.str.strip()
    template_df.columns = template_df.columns.str.strip()

    # Backup originals
    template_df['Name_Original'] = template_df['Name']
    template_df['Department_Original'] = template_df['Department']

    # Normalize for matching
    def normalize(val):
        return str(val).strip().lower() if pd.notna(val) else ''

    manual_df['MatNo_clean'] = manual_df['MatNo'].str.strip().str.upper()
    manual_df['Name_clean'] = manual_df['Name'].apply(normalize)
    manual_df['Department_clean'] = manual_df['Department'].apply(normalize)

    template_df['MatNo_clean'] = template_df['MatNo'].str.strip().str.upper()
    template_df['Name_clean'] = template_df['Name'].apply(normalize)
    template_df['Department_clean'] = template_df['Department'].apply(normalize)

    # Initialize score columns
    template_df['CA'] = ''
    template_df['Exam'] = ''

    # Matching logs
    matched, unmatched = [], []

    # Match Function
    def match_scores(row):
        matno = row['MatNo_clean']
        match = manual_df[manual_df['MatNo_clean'] == matno] if matno else pd.DataFrame()

        if match.empty:
            match = manual_df[
                (manual_df['Name_clean'] == row['Name_clean']) &
                (manual_df['Department_clean'] == row['Department_clean'])
            ]

        if not match.empty:
            ca = str(match.iloc[0]['CA']).strip()
            exam = str(match.iloc[0]['Exam']).strip()
            matched.append({
                'MatNo': row['MatNo'],
                'Name': row['Name_Original'],
                'Department': row['Department_Original'],
                'CA': ca,
                'Exam': exam
            })
            return pd.Series([ca, exam])
        else:
            unmatched.append({
                'MatNo': row['MatNo'],
                'Name': row['Name_Original'],
                'Department': row['Department_Original']
            })
            return pd.Series(['', ''])

    # Apply Matching
    template_df[['CA', 'Exam']] = template_df.apply(match_scores, axis=1)

    # Restore original formatting
    template_df['Name'] = template_df['Name_Original']
    template_df['Department'] = template_df['Department_Original']
    template_df.drop(columns=[
        'Name_Original', 'Department_Original',
        'MatNo_clean', 'Name_clean', 'Department_clean'
    ], inplace=True)

    # Show status
    st.success(f"✅ Matched {len(matched)} students")
    if unmatched:
        st.warning(f"⚠️ {len(unmatched)} students unmatched — please review manually")

    # Convert to downloadable CSVs
    def df_to_csv_download(df):
        return StringIO(df.to_csv(index=False)).getvalue()

    # Downloads
    st.download_button("⬇️ Download Completed Template",
        data=df_to_csv_download(template_df),
        file_name="XYZ_111_Results_Template.csv",
        mime="text/csv"
    )

    if matched:
        st.download_button("📄 Download Matched Students Log",
            data=df_to_csv_download(pd.DataFrame(matched)),
            file_name="XYZ_111_Matched_Students_Log.csv",
            mime="text/csv"
        )

    if unmatched:
        st.download_button("⚠️ Download Unmatched Students Log",
            data=df_to_csv_download(pd.DataFrame(unmatched)),
            file_name="XYZ_111_Unmatched_Students_Log.csv",
            mime="text/csv"
        )
