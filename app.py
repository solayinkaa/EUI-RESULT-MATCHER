import streamlit as st
import pandas as pd
from io import BytesIO
from rapidfuzz import fuzz

st.set_page_config(page_title="ESUI Result Matcher by A.S. Olayinka", layout="wide")

st.title("🧬 ESUI Result Matcher by A.S. Olayinka")

# File upload section
manual_file = st.file_uploader("Upload CA & Exam Scores Manually computed (containing columns name: MatNo	Name	Department	CA	Exam in .csv)", type="csv")
template_file = st.file_uploader("Upload Result Template File as downloaded from the portal (e.g. PHY 111_Results_Template.csv)", type="csv")

if manual_file and template_file:
    manual_df = pd.read_csv(manual_file, dtype=str)
    template_df = pd.read_csv(template_file, dtype=str)

    # Clean headers
    manual_df.columns = manual_df.columns.str.strip()
    template_df.columns = template_df.columns.str.strip()

    # Preserve original
    template_df['Name_Original'] = template_df['Name']
    template_df['Department_Original'] = template_df['Department']

    # Normalize
    def normalize(val):
        return str(val).strip().lower() if pd.notna(val) else ''

    manual_df['MatNo_clean'] = manual_df['MatNo'].str.strip().str.upper()
    manual_df['Name_clean'] = manual_df['Name'].apply(normalize)
    manual_df['Department_clean'] = manual_df['Department'].apply(normalize)

    template_df['MatNo_clean'] = template_df['MatNo'].str.strip().str.upper()
    template_df['Name_clean'] = template_df['Name'].apply(normalize)
    template_df['Department_clean'] = template_df['Department'].apply(normalize)

    # Ensure columns exist
    template_df['CA'] = ''
    template_df['Exam'] = ''

    matched = []
    unmatched = []

    def match_scores(row):
        matno = row['MatNo_clean']
        name = row['Name_clean']
        dept = row['Department_clean']

        # First try exact MatNo match
        match = manual_df[manual_df['MatNo_clean'] == matno] if matno else pd.DataFrame()

        # Next try exact Name and Department
        if match.empty:
            match = manual_df[
                (manual_df['Name_clean'] == name) &
                (manual_df['Department_clean'] == dept)
            ]

        # Then try fuzzy name match within same department
        if match.empty:
            possible_matches = manual_df[manual_df['Department_clean'] == dept]
            best_score = 0
            best_row = None

            for _, manual_row in possible_matches.iterrows():
                score = fuzz.ratio(name, manual_row['Name_clean'])
                if score > 85 and score > best_score:  # adjust threshold as needed
                    best_score = score
                    best_row = manual_row

            if best_row is not None:
                ca = str(best_row['CA']).strip()
                exam = str(best_row['Exam']).strip()
                matched.append({
                    'MatNo': row['MatNo'],
                    'Name': row['Name_Original'],
                    'Department': row['Department_Original'],
                    'CA': ca,
                    'Exam': exam,
                    'Matched_By': 'Fuzzy Name'
                })
                return pd.Series([ca, exam])

        # If matched by previous methods
        if not match.empty:
            ca = str(match.iloc[0]['CA']).strip()
            exam = str(match.iloc[0]['Exam']).strip()
            matched.append({
                'MatNo': row['MatNo'],
                'Name': row['Name_Original'],
                'Department': row['Department_Original'],
                'CA': ca,
                'Exam': exam,
                'Matched_By': 'Exact'
            })
            return pd.Series([ca, exam])
        else:
            unmatched.append({
                'MatNo': row['MatNo'],
                'Name': row['Name_Original'],
                'Department': row['Department_Original']
            })
            return pd.Series(['', ''])

    template_df[['CA', 'Exam']] = template_df.apply(match_scores, axis=1)

    # Restore original columns
    template_df['Name'] = template_df['Name_Original']
    template_df['Department'] = template_df['Department_Original']
    template_df.drop(columns=[
        'Name_Original', 'Department_Original',
        'MatNo_clean', 'Name_clean', 'Department_clean'
    ], inplace=True)

    # Output
    st.success("✅ Matching complete!")
    st.write(f"🎯 **Matched students:** {len(matched)}")
    st.write(f"⚠️ **Unmatched students:** {len(unmatched)}")

    # Download helpers
    def to_csv_download(df):
        output = BytesIO()
        df.to_csv(output, index=False)
        return output.getvalue()

    st.download_button(
        label="⬇️ Download Completed Result Template",
        data=to_csv_download(template_df),
        file_name="BIO_111_Results_Template_Completed.csv",
        mime="text/csv"
    )

    if matched:
        matched_df = pd.DataFrame(matched)
        st.download_button(
            label="📄 Download Matched Students Log",
            data=to_csv_download(matched_df),
            file_name="PHY_111_Matched_Students_Log.csv",
            mime="text/csv"
        )

    if unmatched:
        unmatched_df = pd.DataFrame(unmatched)
        st.download_button(
            label="⚠️ Download Unmatched Students Log",
            data=to_csv_download(unmatched_df),
            file_name="PHY_111_Unmatched_Students_Log.csv",
            mime="text/csv"
        )
        st.warning("⚠️ Some students could not be matched. Please review the unmatched log.")
    else:
        st.success("🎉 All students matched successfully!")

else:
    st.info("Please upload both the CA/Exam data and the template file to proceed.")
