import requests
import pdfplumber
import pandas as pd

# Function 1: Download the PDF
def download_pdf(url, output_file):
    response = requests.get(url)
    if response.status_code == 200:
        with open(output_file, "wb") as file:
            file.write(response.content)
        print(f"PDF downloaded successfully: {output_file}")
    else:
        raise Exception("Failed to download the PDF.")

# Function 2: Extract data from PDF and save to CSV
def extract_pdf_to_csv(pdf_file, csv_file):
    data = []  # To store extracted rows
    header = None  # Placeholder for the header row
    header_seen = False  # Flag to track if the header is already set

    # Step 1: Extract tables from the PDF
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if not header_seen:  # First row encountered is the header
                        header = row
                        header_seen = True
                    elif row != header:  # Skip rows that are duplicate headers
                        data.append(row)

    # Step 2: Convert to DataFrame with proper headers
    df = pd.DataFrame(data, columns=header)  # Use the first header row as column names

    # Step 3: Save the DataFrame to a CSV file
    df.to_csv(csv_file, index=False)  # Save the CSV with header included
    print(f"Data extracted and saved to CSV: {csv_file}")


# Function 3: Process the Description column
def process_description(input_csv, output_csv):
    df = pd.read_csv(input_csv, header = 0)

    def clean_description(description):
        if pd.isna(description):
            return None
        # cleaned = description.replace(" ", "").replace("#", "").split("I-Beam")[0]
        cleaned = description.replace(" ", "").split('#')[0]
        return cleaned

    df['Description'] = df['Description'].apply(clean_description)
    df.to_csv(output_csv, index=False)
    print(f"Processed file saved as: {output_csv}")

# Function 4: Match with AISC database and append A values
def match_and_update(processed_csv, aisc_csv, final_csv):
    df_processed = pd.read_csv(processed_csv, header = 0)
    df_aisc = pd.read_csv(aisc_csv, header = 0)

    def clean_aisc_label(label):
        if pd.isna(label):
            return None
        return label[1:].replace("X", "x")

    df_aisc['Processed_Label'] = df_aisc['AISC_Manual_Label'].apply(clean_aisc_label)
    df_merged = pd.merge(
        df_processed,
        df_aisc[['Processed_Label', 'A']],
        left_on='Description',
        right_on='Processed_Label',
        how='left'
    )
    df_merged.drop(columns=['Processed_Label'], inplace=True)
    df_merged.to_csv(final_csv, index=False)
    print(f"Updated file saved as: {final_csv}")


import pandas as pd

def duplicate_entry_based_on_pieces(final_csv):
    """
    Duplicate entries in the CSV file based on the 'Pieces' column.
    """
    # Step 1: Load the processed CSV file
    df_processed = pd.read_csv(final_csv, header = 0)
    
    # Step 2: Create an empty list to store the duplicated rows
    duplicated_rows = []

    # Step 3: Iterate through each row in the dataframe
    for index, row in df_processed.iterrows():
        try:
            # Get the 'Pieces' value, default to 1 if it's missing or invalid
            pieces = row.get('Pieces', 1)
            pieces = int(pieces) if pd.notna(pieces) and str(pieces).isdigit() else 1
            
            # Step 4: Append the row to the list, repeating it based on 'Pieces'
            for _ in range(pieces):
                duplicated_rows.append(row)
        except ValueError:
            print(f"Warning: Invalid 'Pieces' value at row {index}, defaulting to 1.")
            duplicated_rows.append(row)

    # Step 5: Convert the list back into a DataFrame
    df_duplicated = pd.DataFrame(duplicated_rows)

    # Step 6: Drop the 'Pieces' column as it's no longer needed
    if 'Pieces' in df_duplicated.columns:
        df_duplicated.drop(columns=['Pieces'], inplace=True)

    # Step 7: Save the updated dataframe back to the final CSV
    df_duplicated.to_csv(final_csv, index=False)
    print(f"Entries duplicated based on 'Pieces' column and saved to: {final_csv}")

# Main Execution
if __name__ == "__main__":
    # File paths and URLs
    pdf_url = "https://www.midcitysteel.com/annex/Used_Surplus_Beam_List.pdf"
    pdf_file = "Used_Surplus_Beam_List.pdf"
    raw_csv_file = "Used_Surplus_Beam_List.csv"
    processed_csv_file = "Processed_Used_Surplus_Beam_List.csv"
    # aisc_csv_file = "aisc-shapes-database-v16.0.csv"
    aisc_csv_file = "https://raw.githubusercontent.com/BrianTruong23/test-upload/refs/heads/main/aisc-shapes-database-v16.0.csv"
    final_csv_file = "Updated_Processed_Used_Surplus_Beam_List.csv"

    # Call functions in sequence
    download_pdf(pdf_url, pdf_file)
    extract_pdf_to_csv(pdf_file, raw_csv_file)
    process_description(raw_csv_file, processed_csv_file)
    match_and_update(processed_csv_file, aisc_csv_file, final_csv_file)
    duplicate_entry_based_on_pieces(final_csv_file)

