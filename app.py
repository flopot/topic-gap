import streamlit as st
import pandas as pd
import numpy as np

def main():
    st.title("CSV Merger and Analyzer App")

    st.markdown("""
    **Instructions:**
    1. Upload your CSV files.
    2. The app will merge them, remove duplicates, and process the data as specified.
    3. Download the processed results.
    """)

    # Step 1: Upload CSV Files
    st.header("Step 1: Upload CSV Files")
    uploaded_files = st.file_uploader("Choose CSV files", accept_multiple_files=True, type=["csv"])

    if uploaded_files:
        csv_list = []
        for uploaded_file in uploaded_files:
            try:
                df = pd.read_csv(uploaded_file)
                csv_list.append(df)
                st.success(f"Uploaded `{uploaded_file.name}` successfully!")
                st.write(f"Preview of `{uploaded_file.name}`:")
                st.dataframe(df.head())
            except Exception as e:
                st.error(f"Error uploading `{uploaded_file.name}`: {e}")
                return

        # Step 2: Merge CSV Files
        st.header("Step 2: Merged Data")
        try:
            merged_df = pd.concat(csv_list, ignore_index=True)
            st.success("CSV files merged successfully!")
            st.write("Preview of Merged Data:")
            st.dataframe(merged_df.head())
        except Exception as e:
            st.error(f"Error merging CSV files: {e}")
            return

        # Ensure required columns exist
        required_columns = ['Keyword', 'Search Volume', 'Keyword Difficulty', 'Domain', 'Domain Position', 'Competitor URL']
        missing_columns = [col for col in required_columns if col not in merged_df.columns]
        if missing_columns:
            st.error(f"The following required columns are missing in the CSV files: {missing_columns}")
            return
        else:
            st.success("All required columns are present.")

        # Step 3: Remove Duplicates
        st.header("Step 3: Remove Duplicates")
        # Sort by 'Domain' ascending and 'Keyword' ascending
        merged_df.sort_values(by=['Domain', 'Keyword'], ascending=[True, True], inplace=True)
        # Drop duplicates based on 'Keyword', keeping the first occurrence
        dedup_df = merged_df.drop_duplicates(subset=['Keyword'], keep='first').reset_index(drop=True)
        st.success("Duplicates removed based on 'Keyword' and sorted by 'Domain' ascending.")
        st.write("Preview after Removing Duplicates:")
        st.dataframe(dedup_df.head())

        # Step 4: Sort by Descending Search Volume
        st.header("Step 4: Sort by Descending Search Volume")
        dedup_df['Search Volume'] = pd.to_numeric(dedup_df['Search Volume'], errors='coerce')
        dedup_df.sort_values(by='Search Volume', ascending=False, inplace=True)
        st.success("Data sorted by 'Search Volume' in descending order.")
        st.write("Preview after Sorting:")
        st.dataframe(dedup_df.head())

        # Step 5: Remove Specific Rows
        st.header("Step 5: Remove Rows Based on Domain Position")
        # Assuming lower 'Domain Position' means better rank
        # Remove rows where 'Domain Position' > min competitor positions and 'Domain Position' != 0
        # First, ensure 'Competitor Position' exists or compute it
        # Assuming 'Competitor Position' is part of 'Competitor URL' data, which might need clarification
        # For simplicity, let's assume 'Competitor Position' is another column
        if 'Competitor Position' not in dedup_df.columns:
            st.error("The column 'Competitor Position' is missing.")
            return

        dedup_df['Domain Position'] = pd.to_numeric(dedup_df['Domain Position'], errors='coerce')
        dedup_df['Competitor Position'] = pd.to_numeric(dedup_df['Competitor Position'], errors='coerce')

        # Remove rows where Domain Position > Competitor Position and Domain Position != 0
        condition = (dedup_df['Domain Position'] > dedup_df['Competitor Position']) & (dedup_df['Domain Position'] != 0)
        filtered_df = dedup_df[~condition].reset_index(drop=True)
        st.success("Filtered out rows where 'Domain Position' is lower than competitors and not 0.")
        st.write("Preview after Filtering:")
        st.dataframe(filtered_df.head())

        # Step 6: Create the Desired Table
        st.header("Step 6: Create Final Table")

        # Define a helper function to get Domain's Info
        def get_domain_info(row, group_df):
            # Find rows where the domain ranks for the keywords the competitor URL ranks in top 10
            domain_ranked = group_df[
                (group_df['Keyword'] == row['Keyword']) &
                (group_df['Domain'] == row['Domain']) &
                (group_df['Domain Position'] > 0)
            ]
            if not domain_ranked.empty:
                info = domain_ranked.apply(lambda x: f"{x['Keyword']} ({x['Domain']} - {x['Domain Position']})", axis=1)
                return ", ".join(info.tolist())
            else:
                return ""

        # Group by 'Competitor URL'
        competitor_groups = filtered_df.groupby('Competitor URL')

        final_rows = []

        for competitor_url, group in competitor_groups:
            # Topic: keyword with the most search volume
            top_keyword_row = group.loc[group['Search Volume'].idxmax()]
            topic = top_keyword_row['Keyword']

            # Keywords: list of keywords in top 10 sorted by descending search volume
            top_keywords = group.sort_values(by='Search Volume', ascending=False)['Keyword'].tolist()
            keywords = ", ".join(top_keywords)

            # Search Volume: sum of search volumes
            total_search_volume = group['Search Volume'].sum()

            # Keyword Difficulty: average keyword difficulty
            avg_keyword_difficulty = group['Keyword Difficulty'].mean()

            # Domain's Info
            domain_info = get_domain_info(top_keyword_row, filtered_df)

            # Creation or Optimization
            creation_optimization = "Optimization" if domain_info else "Creation"

            final_rows.append({
                "Competitor URL": competitor_url,
                "Topic": topic,
                "Keywords": keywords,
                "Search Volume": total_search_volume,
                "Keyword Difficulty": round(avg_keyword_difficulty, 2),
                "Domain's Info": domain_info,
                "Creation or Optimization": creation_optimization
            })

        final_df = pd.DataFrame(final_rows)

        # Remove duplicate Competitor URLs
        final_df.drop_duplicates(subset=['Competitor URL'], inplace=True)

        st.success("Final table created successfully!")
        st.write("Preview of Final Table:")
        st.dataframe(final_df.head())

        # Step 7: Download Final Table
        st.header("Step 7: Download Results")
        csv = final_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Final Table as CSV",
            data=csv,
            file_name='final_table.csv',
            mime='text/csv',
        )

        # Optionally, display the final table
        st.subheader("Final Table")
        st.dataframe(final_df)

if __name__ == "__main__":
    main()
