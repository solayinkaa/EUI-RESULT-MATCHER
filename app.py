import streamlit as st
import pandas as pd
import io  # Needed for in-memory CSV download

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
   - 📄 *Upload XYZ 111 Manual Result in CSV*  
   - 📄 *Upload XYZ 111 Result Template from Portal in CSV*

2. **Click 'Process Results'**  
   - CA and Exam scores will be auto-filled based on **MatNo** match.

3. **Download the Completed File**  
   - Use **"Download Completed Results"** button.

---

### ⚠️ Notes
- Matching is done using **MatNo** (trimmed and case-insensitive).
- Unmatched students remain in the file with CA/Exam fields left blank.
- Files **must be in CSV format**.
""")

# File Upload Section
manual_file = st.file_uploader("📄 Upload XYZ 111 Manual Result in CSV", type=["csv"])
template_file = st.file_uploader("📄 Upload XYZ 111 Result Template from Portal in CSV", type=["csv"])

# Main Logic
if manual_file is not None and template_file is not None:
    try:
        manual_df = pd.read_csv(manual_file)
        template_df = pd.read_csv(template_file)

        # Normalize MatNo for matching (trim and uppercase)
        manual_df['MatNo'] = manual_df['MatNo'].astype(str).str.strip().str.upper()
        template_df['MatNo'] = template_df['MatNo'].astype(str).str.strip().str.upper()

        # Create lookup from manual result
        manual_lookup = manual_df.set_index('MatNo')

        # Track unmatched students
        unmatched = []

        # Fill CA and Exam where matches exist
        for i, row in template_df.iterrows():
            matno = row['MatNo']
            if matno in manual_lookup.index:
                match_row = manual_lookup.loc[matno]
                if isinstance(match_row, pd.Series):
                template_df.at[i, 'CA'] = match_row['CA']
                template_df.at[i, 'Exam'] = match_row['Exam']
                else:
            template_df.at[i, 'CA'] = match_row.iloc[0]['CA']
            template_df.at[i, 'Exam'] = match_row.iloc[0]['Exam']
            else:
                unmatched.append(matno)

        # Show unmatched entries
        if unmatched:
            st.warning("⚠️ The following MatNo(s) were not found in the manual result:")
            st.code('\n'.join(unmatched))

        # Generate CSV for download
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
