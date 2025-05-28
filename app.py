import streamlit as st
import pandas as pd
import io

# Page config
st.set_page_config(page_title="EDSU Result Auto-Matcher", layout="centered")

st.title("📊 EDSU Faculty of Science Auto-Matcher for Manual / Portal Template Results")

# User guide
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
- CA/Exam will be left **empty** (not `NaN`) if unmatched
""")

# Upload
manual_file = st.file_uploader("📄 Upload Manual Result CSV", type=["csv"])
template_file = st.file_uploader("📄 Upload Portal Template CSV", type=["csv"])

if manual_file and template_file:
    try:
        # Load data
        manual_df = pd.read_csv(manual_file)
        template_df = pd.read_csv(template_file)

        # Preserve original first 3 columns
        original_template = template_df[['MatNo', 'Name', 'Department']].copy()

        # Normalize MatNo
        manual_df['MatNo'] = manual_df['MatNo'].astype(str).str.strip().str.upper()
        template_df['MatNo'] = template_df['MatNo'].astype(str).str.strip().str.upper()

        # Merge only CA and Exam columns
        merged = pd.merge(template_df[['MatNo']], manual_df[['MatNo', 'CA', 'Exam']],
                          on='MatNo', how='left')

        # Replace NaN with empty strings
        merged['CA'] = merged['CA'].fillna('')
        merged['Exam'] = merged['Exam'].fillna('')

        # Combine back with original template columns
        final_df = original_template.copy()
        final_df['CA'] = merged['CA']
        final_df['Exam'] = merged['Exam']

        # Filter unmatched valid MatNo only (non-empty and not NaN)
        unmatched = [matno for matno in unmatched if pd.notna(matno) and str(matno).strip() != ""]

        # Show only valid unmatched entries
        if unmatched:
            st.warning("⚠️ The following MatNo(s) were not found in the manual result:")
            st.code('\n'.join(unmatched))
            
        # Create CSV for download
        csv_buffer = io.StringIO()
        final_df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()

        st.success("✅ Processing complete. Download the result below:")
        st.download_button(
            label="📥 Download Completed Results",
            data=csv_data,
            file_name="Completed_Results.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")
