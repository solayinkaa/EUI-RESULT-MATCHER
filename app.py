import streamlit as st
import pandas as pd
import io  # For in-memory CSV

# Page config
st.set_page_config(page_title="EDSU Result Auto-Matcher", layout="centered")

st.title("📊 EDSU Faculty of Science Auto-Matcher for Manual / Portal Template Results")

# 📘 User Guide
with st.expander("📘 How to Use This App (Click to Expand)"):
    st.markdown("""
### 🎯 Purpose  
Auto-fill student **CA** and **Exam** scores into the official **portal template**, ready for upload.

### 📂 Required Files
1. **Manual Result (CSV)**  
   - Columns: `MatNo, Name, Department, CA, Exam, Total, Grade`

2. **Portal Template (CSV)**  
   - Columns: `MatNo, Name, Department, CA, Exam`

### 🚀 Steps
1. Upload both files  
2. Click "Process Results"  
3. Download the updated portal file

### ⚠️ Notes
- Matching is done using **MatNo** (trimmed and uppercase)
- Only `CA` and `Exam` columns are updated
- Blank CA/Exam cells will remain **empty**, not `NaN`
""")

# Uploads
manual_file = st.file_uploader("📄 Upload Manual Result CSV", type=["csv"])
template_file = st.file_uploader("📄 Upload Portal Template CSV", type=["csv"])

# Processing logic
if manual_file and template_file:
    try:
        manual_df = pd.read_csv(manual_file)
        template_df = pd.read_csv(template_file)

        # Backup original data
        original_template = template_df.copy()

        # Normalize MatNo for matching
        manual_df['MatNo'] = manual_df['MatNo'].astype(str).str.strip().str.upper()
        template_df['MatNo'] = template_df['MatNo'].astype(str).str.strip().str.upper()

        # Build lookup dictionary for CA and Exam
        manual_lookup = manual_df.set_index('MatNo')[['CA', 'Exam']].to_dict(orient='index')

        unmatched = []

        # Update only CA and Exam in original template
        updated_template = original_template.copy()
        for i, row in template_df.iterrows():
            matno = row['MatNo']
            if matno in manual_lookup:
                ca = manual_lookup[matno].get('CA', '')
                exam = manual_lookup[matno].get('Exam', '')
                updated_template.at[i, 'CA'] = '' if pd.isna(ca) else ca
                updated_template.at[i, 'Exam'] = '' if pd.isna(exam) else exam
            else:
                updated_template.at[i, 'CA'] = ''
                updated_template.at[i, 'Exam'] = ''
                unmatched.append(original_template.at[i, 'MatNo'])  # use original format

        if unmatched:
            st.warning("⚠️ The following MatNo(s) were not found in the manual result:")
            st.code('\n'.join(unmatched))

        # Convert to CSV without NaNs
        csv_buffer = io.StringIO()
        updated_template.to_csv(csv_buffer, index=False, na_rep='')  # <-- This avoids NaN
        csv_data = csv_buffer.getvalue()

        # Download button
        st.success("✅ Processing complete. Download the result below:")
        st.download_button(
            label="📥 Download Completed Results",
            data=csv_data,
            file_name="Completed_Results.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")
