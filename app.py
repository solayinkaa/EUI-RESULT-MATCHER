import streamlit as st
import pandas as pd
import io
import datetime

# Set page configuration
st.set_page_config(
    page_title="ESUI Result Auto-Matcher",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("📊 ESUI Faculty of Science Auto-Matcher")
st.markdown("Automated matching of manual results with portal templates.")

# Function to normalize text fields
def normalize(val):
    return str(val).strip().lower() if pd.notna(val) else ''

# Function to validate uploaded dataframes
def validate_dataframe(df, required_columns):
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        return False, f"Missing columns: {', '.join(missing_cols)}"
    return True, ""

# File upload section
st.header("📁 Upload Files")
manual_file = st.file_uploader("Upload Manual Result CSV", type=["csv"])
template_file = st.file_uploader("Upload Portal Template CSV", type=["csv"])

if manual_file and template_file:
    try:
        # Read uploaded files
        manual_df = pd.read_csv(manual_file, dtype=str)
        template_df = pd.read_csv(template_file, dtype=str)

        # Strip whitespace from headers
        manual_df.columns = manual_df.columns.str.strip()
        template_df.columns = template_df.columns.str.strip()

        # Validate required columns
        manual_valid, manual_msg = validate_dataframe(manual_df, ["MatNo", "CA", "Exam"])
        template_valid, template_msg = validate_dataframe(template_df, ["MatNo", "Name", "Department"])

        if not manual_valid:
            st.error(f"Manual Result File Error: {manual_msg}")
        elif not template_valid:
            st.error(f"Portal Template File Error: {template_msg}")
        else:
            st.success("Files uploaded and validated successfully.")

            # Backup original Name and Department
            template_df['Name_Original'] = template_df['Name']
            template_df['Department_Original'] = template_df['Department']

            # Normalize fields for matching
            manual_df['MatNo_clean'] = manual_df['MatNo'].str.strip().str.upper()
            manual_df['Name_clean'] = manual_df['Name'].apply(normalize)
            manual_df['Department_clean'] = manual_df['Department'].apply(normalize)

            template_df['MatNo_clean'] = template_df['MatNo'].str.strip().str.upper()
            template_df['Name_clean'] = template_df['Name'].apply(normalize)
            template_df['Department_clean'] = template_df['Department'].apply(normalize)

            # Initialize CA and Exam columns
            template_df['CA'] = ''
            template_df['Exam'] = ''

            # Lists to store matched and unmatched records
            matched = []
            unmatched = []

            # Matching function
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

            # Apply matching
            template_df[['CA', 'Exam']] = template_df.apply(match_scores, axis=1)

            # Restore original Name and Department
            template_df['Name'] = template_df['Name_Original']
            template_df['Department'] = template_df['Department_Original']
            template_df.drop(columns=[
                'Name_Original', 'Department_Original',
                'MatNo_clean', 'Name_clean', 'Department_clean'
            ], inplace=True)

            # Display matched and unmatched counts
            st.subheader("🔍 Matching Summary")
            st.write(f"Total Records in Template: {len(template_df)}")
            st.write(f"Matched Records: {len(matched)}")
            st.write(f"Unmatched Records: {len(unmatched)}")

            # Display unmatched records if any
            if unmatched:
                st.subheader("❌ Unmatched Records")
                unmatched_df = pd.DataFrame(unmatched)
                st.dataframe(unmatched_df)

            # Display matched records
            st.subheader("✅ Matched Records")
            matched_df = pd.DataFrame(matched)
            st.dataframe(matched_df)

            # Provide download options
            st.subheader("📥 Download Results")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

            # Completed results
            completed_csv = template_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Completed Results CSV",
                data=completed_csv,
                file_name=f"BIO_111_Results_Template_Completed_{timestamp}.csv",
                mime='text/csv'
            )

            # Matched log
            if matched:
                matched_csv = pd.DataFrame(matched).to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Matched Students Log CSV",
                    data=matched_csv,
                    file_name=f"BIO_111_Matched_Students_Log_{timestamp}.csv",
                    mime='text/csv'
                )

            # Unmatched log
            if unmatched:
                unmatched_csv = pd.DataFrame(unmatched).to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Unmatched Students Log CSV",
                    data=unmatched_csv,
                    file_name=f"BIO_111_Unmatched_Students_Log_{timestamp}.csv",
                    mime='text/csv'
                )

    except Exception as e:
        st.error(f"An error occurred: {e}")
