import streamlit as st
import pandas as pd
import io  # For in-memory CSV download

# Page configuration
st.set_page_config(page_title="EDSU Result Auto-Matcher", layout="centered")

st.title("📊 EDSU Faculty of Science Auto-Matcher for Manual / Portal Template Results")

# 📘 User Guide Section
with st.expander("📘 How to Use This App (Click to Expand)"):
    st.markdown("""
### 🎯 Purpose  
Automatically match and fill student **CA** and **Exam** scores from a manually prepared result into the official **portal template**, ready for upload.

---

### 📂 Required Files
1. **Manual Result (CSV)**  
   - Columns: `MatNo, Name, Department, CA, Exam, Total, Grade`

2. **Portal Template (CSV)**  
   - Columns: `MatNo, Name, Department, CA, Exam`

---

### 🚀 Steps to Use
1. **Upload Files**  
   - 📄 *Upload Manual Result (CSV)*  
   - 📄 *Upload Portal Template (CSV)*

2. **Click 'Process Results'**  
   - CA and Exam scores will be auto-filled based on **MatNo** match.

3. **Download the Completed File**  
   - Use **"Download Completed Results"** button.

---

### ⚠️ Notes
- Matching is done using **MatNo** (trimmed and case-insensitive).
- Unmatched students remain with CA/Exam blank.
- Files **must be in CSV format**.
""")

# File Upload Section
manual_file = st.file_uploader("📄 Upload Manual Result CSV", type=["csv"])
template_file = st.file_uploader("📄 Upload Portal Template CSV", type=["csv"])

# Main Logic
if manual_file and template_file:
    try:
        manual_df = pd.read_csv(manual_file)
        template_df = pd.read_csv(template_file)

        # Normalize MatNo for matching
        manual_df['MatNo'] = manual_df['MatNo'].astype(str).str.strip().str.upper()
        template_df['MatNo'] = template_df['MatNo'].astype(str).str.strip().str.upper()

        # Ensure CA and Exam columns exist and are string type
        for col in ['CA', 'Exam']:
            if col not in template_df.columns:
                template_df[col] = ''
            else:
                template_df[col] = template_df[col].astype(str).fillna('').replace('nan', '')

        # Manual result as lookup
        manual_lookup = manual_df.set_index('MatNo')

        unmatched = []

        # Match and fill
        for i, row in template_df.iterrows():
            matno = row['MatNo']
            if matno in manual_lookup.index:
                match = manual_lookup.loc[matno]
                if isinstance(match, pd.DataFrame):  # multiple entries
                    match = match.iloc[0]

                template_df.at[i, 'CA'] = str(match.get('CA', '')).strip() if pd.notna(match.get('CA', '')) else ''
                template_df.at[i, 'Exam'] = str(match.get('Exam', '')).strip() if pd.notna(match.get('Exam', '')) else ''
            else:
                unmatched.append(matno)

        # Show unmatched
        if unmatched:
            st.warning("⚠️ The following MatNo(s) were not found in the manual result:")
            st.code('\n'.join(unmatched))

        # Clean the entire DataFrame to prevent NaN in any column
        template_df = template_df.astype(str).replace('nan', '').fillna('')

        # Prepare CSV download
        csv_output = io.StringIO()
        template_df.to_csv(csv_output, index=False)
        csv_data = csv_output.getvalue()

        # Download button
        st.success("✅ Result processing complete. Download the completed file below:")
        st.download_button(
            label="📥 Download Completed Results",
            data=csv_data,
            file_name="PHY_111_Results_Completed.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")
