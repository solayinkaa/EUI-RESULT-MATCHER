import streamlit as st
import pandas as pd
import io
import numpy as np
from typing import Tuple, List, Dict, Optional

# Page configuration
st.set_page_config(
    page_title="EDSU Result Auto-Matcher", 
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .stats-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.25rem;
        padding: 0.75rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">📊 EDSU Faculty of Science Auto-Matcher</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666;">Automated matching of manual results with portal templates</p>', unsafe_allow_html=True)

def validate_dataframe(df: pd.DataFrame, file_type: str, required_columns: List[str]) -> Tuple[bool, str]:
    """Validate uploaded dataframe structure and content."""
    if df.empty:
        return False, f"The {file_type} file is empty."
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return False, f"Missing required columns in {file_type}: {', '.join(missing_columns)}"
    
    # Check for completely empty required columns
    for col in required_columns:
        if col == 'MatNo' and df[col].isna().all():
            return False, f"MatNo column in {file_type} cannot be completely empty."
    
    return True, "Valid"

def clean_matno(matno_series: pd.Series) -> pd.Series:
    """Clean and standardize MatNo values."""
    return matno_series.astype(str).str.strip().str.upper().replace('NAN', np.nan)

def process_results(manual_df: pd.DataFrame, template_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """Process and merge the manual results with template."""
    
    # Store original template structure
    original_template = template_df[['MatNo', 'Name', 'Department']].copy()
    
    # Clean MatNo columns
    manual_df = manual_df.copy()
    template_df = template_df.copy()
    
    manual_df['MatNo_clean'] = clean_matno(manual_df['MatNo'])
    template_df['MatNo_clean'] = clean_matno(template_df['MatNo'])
    
    # Remove rows with invalid MatNo
    manual_df = manual_df.dropna(subset=['MatNo_clean'])
    template_df = template_df.dropna(subset=['MatNo_clean'])
    
    # Check for duplicates
    manual_duplicates = manual_df['MatNo_clean'].duplicated().sum()
    template_duplicates = template_df['MatNo_clean'].duplicated().sum()
    
    # Merge CA and Exam scores
    merge_columns = ['MatNo_clean']
    score_columns = []
    
    if 'CA' in manual_df.columns:
        merge_columns.append('CA')
        score_columns.append('CA')
    if 'Exam' in manual_df.columns:
        merge_columns.append('Exam')
        score_columns.append('Exam')
    
    merged = pd.merge(
        template_df[['MatNo_clean']], 
        manual_df[merge_columns],
        on='MatNo_clean', 
        how='left'
    )
    
    # Replace NaN with empty strings for score columns
    for col in score_columns:
        merged[col] = merged[col].fillna('')
    
    # Combine with original template
    final_df = original_template.copy()
    for col in score_columns:
        final_df[col] = merged[col]
    
    # Generate statistics
    stats = {
        'total_template_records': len(template_df),
        'total_manual_records': len(manual_df),
        'successful_matches': len(merged[merged[score_columns[0]] != '']) if score_columns else 0,
        'unmatched_records': len(merged[merged[score_columns[0]] == '']) if score_columns else 0,
        'manual_duplicates': manual_duplicates,
        'template_duplicates': template_duplicates,
        'unmatched_matnos': merged[merged[score_columns[0]] == '']['MatNo_clean'].tolist() if score_columns else []
    }
    
    return final_df, stats

def display_statistics(stats: Dict):
    """Display processing statistics."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 Template Records", stats['total_template_records'])
    with col2:
        st.metric("📄 Manual Records", stats['total_manual_records'])
    with col3:
        st.metric("✅ Successful Matches", stats['successful_matches'])
    with col4:
        st.metric("❌ Unmatched Records", stats['unmatched_records'])

# User guide section
with st.expander("📘 How to Use This App (Click to Expand)", expanded=False):
    st.markdown("""
    ### 🎯 Purpose  
    Automatically match and fill student **CA** and **Exam** scores from manual results into the official **portal template**.
    
    ### 📂 Required File Formats
    
    **1. Manual Result File (CSV)**
    - Required columns: `MatNo`, `CA`, `Exam`
    - Optional columns: `Name`, `Department`, `Total`, `Grade`
    - MatNo should be unique per student
    
    **2. Portal Template File (CSV)**
    - Required columns: `MatNo`, `Name`, `Department`
    - May include empty `CA` and `Exam` columns
    
    ### 🚀 Step-by-Step Process
    1. **Upload Files**: Select your manual result and portal template CSV files
    2. **Validation**: App automatically validates file formats and structure
    3. **Processing**: Click "Process Results" to match records
    4. **Review**: Check statistics and any unmatched records
    5. **Download**: Get your completed portal template ready for upload
    
    ### ⚠️ Important Notes
    - Matching uses **MatNo** (automatically cleaned and standardized)
    - Duplicate MatNo entries will be flagged
    - Unmatched records will show empty CA/Exam fields
    - Original template structure is preserved
    - Processing is case-insensitive and handles extra spaces
    
    ### 🔧 Troubleshooting
    - Ensure MatNo format consistency between files
    - Check for typos in student registration numbers
    - Verify all required columns are present
    """)

# File upload section
st.subheader("📁 File Upload")

col1, col2 = st.columns(2)

with col1:
    manual_file = st.file_uploader(
        "📄 Upload Manual Result CSV", 
        type=["csv"],
        help="CSV file containing student scores with MatNo, CA, and Exam columns"
    )

with col2:
    template_file = st.file_uploader(
        "📄 Upload Portal Template CSV", 
        type=["csv"],
        help="Official portal template with MatNo, Name, and Department columns"
    )

# Processing section
if manual_file and template_file:
    try:
        # Load dataframes
        with st.spinner("Loading and validating files..."):
            manual_df = pd.read_csv(manual_file)
            template_df = pd.read_csv(template_file)
        
        # Validate files
        manual_valid, manual_msg = validate_dataframe(
            manual_df, "Manual Result", ["MatNo", "CA", "Exam"]
        )
        template_valid, template_msg = validate_dataframe(
            template_df, "Portal Template", ["MatNo", "Name", "Department"]
        )
        
        if not manual_valid:
            st.error(f"❌ Manual Result Validation Error: {manual_msg}")
        elif not template_valid:
            st.error(f"❌ Portal Template Validation Error: {template_msg}")
        else:
            st.success("✅ Both files validated successfully!")
            
            # Display file previews
            with st.expander("👀 Preview Uploaded Files", expanded=False):
                st.subheader("Manual Result Preview")
                st.dataframe(manual_df.head(), use_container_width=True)
                
                st.subheader("Portal Template Preview")
                st.dataframe(template_df.head(), use_container_width=True)
            
            # Process button
            if st.button("🚀 Process Results", type="primary", use_container_width=True):
                with st.spinner("Processing and matching records..."):
                    final_df, stats = process_results(manual_df, template_df)
                
                st.success("✅ Processing completed successfully!")
                
                # Display statistics
                st.subheader("📊 Processing Statistics")
                display_statistics(stats)
                
                # Show warnings for duplicates
                if stats['manual_duplicates'] > 0:
                    st.warning(f"⚠️ Found {stats['manual_duplicates']} duplicate MatNo(s) in manual results")
                
                if stats['template_duplicates'] > 0:
                    st.warning(f"⚠️ Found {stats['template_duplicates']} duplicate MatNo(s) in template")
                
                # Show unmatched records
                if stats['unmatched_matnos']:
                    st.subheader("❌ Unmatched Records")
                    st.warning(f"The following {len(stats['unmatched_matnos'])} MatNo(s) from the template were not found in manual results:")
                    
                    # Display unmatched in a more readable format
                    unmatched_df = pd.DataFrame(stats['unmatched_matnos'], columns=['Unmatched MatNo'])
                    st.dataframe(unmatched_df, use_container_width=True)
                
                # Preview final results
                with st.expander("👀 Preview Final Results", expanded=False):
                    st.dataframe(final_df.head(10), use_container_width=True)
                    if len(final_df) > 10:
                        st.info(f"Showing first 10 rows of {len(final_df)} total records")
                
                # Download section
                st.subheader("📥 Download Results")
                
                # Generate filename with timestamp
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"EDSU_Completed_Results_{timestamp}.csv"
                
                # Create download data
                csv_buffer = io.StringIO()
                final_df.to_csv(csv_buffer, index=False)
                csv_data = csv_buffer.getvalue()
                
                # Download button
                st.download_button(
                    label="📥 Download Completed Portal Template",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv",
                    type="primary",
                    use_container_width=True
                )
                
                # Summary message
                match_rate = (stats['successful_matches'] / stats['total_template_records'] * 100) if stats['total_template_records'] > 0 else 0
                st.info(f"📈 Match Rate: {match_rate:.1f}% ({stats['successful_matches']}/{stats['total_template_records']} records matched)")

    except pd.errors.EmptyDataError:
        st.error("❌ One or both files are empty or corrupted. Please check your CSV files.")
    except pd.errors.ParserError as e:
        st.error(f"❌ Error parsing CSV files: {str(e)}")
    except Exception as e:
        st.error(f"❌ Unexpected error occurred: {str(e)}")
        st.info("💡 Please check that your files are properly formatted CSV files with the correct columns.")

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #666; font-size: 0.9em;'>"
    "EDSU Faculty of Science Result Processing Tool | "
    "Developed for efficient result management"
    "</p>", 
    unsafe_allow_html=True
)
