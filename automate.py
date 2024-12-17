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
    import pandas as pd  # Ensure pandas is imported

    # Read the input CSV file
    df = pd.read_csv(input_csv, header=0)

    # Function to clean the Description column
    def clean_description(description):
        if pd.isna(description):  # Handle missing values
            return None

        # Remove spaces and split on '#'
        cleaned = description.replace(" ", "").split('#')[0]
        
        # Further processing to round down numbers before 'x'
        try:
            base_part = cleaned.split("x")[0]  # Extract part before 'x'
            rounded_down = int(float(base_part))  # Convert to float, then round down to an integer
            final = f"{rounded_down}x{cleaned.split('x')[1]}"  # Reconstruct the description
            return final
        except (ValueError, IndexError):
            return cleaned  # Return the original cleaned value if processing fails

    # Apply the cleaning function to the Description column
    df['Description'] = df['Description'].apply(clean_description)

    # Function to convert lengths into inches
    def convert_length(length):
        try:
            # Extract feet and inches, handling cases where inches might be missing
            feet = int(length.split("'")[0]) if "'" in str(length) else 0
            inches = int(length.split("'")[1].replace('"', '')) if '"' in str(length) else 0
            final_length = feet * 12 + inches  # Convert to inches
            return final_length
        except (ValueError, IndexError):
            return None  # Handle invalid or missing length values

    # Apply the conversion function to the Lengths column
    df["Lengths"] = df["Lengths"].apply(convert_length)

    # Save the processed DataFrame to a new CSV file
    df.to_csv(output_csv, index=False)
    print(f"Processed file saved as: {output_csv}")


# Function 4: Match with AISC database and append A values
def match_and_update(processed_csv, aisc_csv, final_csv):
    df_processed = pd.read_csv(processed_csv, header = 0)
    df_aisc = pd.read_csv(aisc_csv, header = 0)

    def clean_aisc_label(label):
        if pd.isna(label):
            return None
        elif label[0:1] != "W":
            return label
        else:
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
            # print(pieces)
            # print(type(pieces))  # Check the type

            # Convert pieces to an integer if it's a valid float or int
            if pd.notna(pieces):  # Check if not NaN
                try:
                    # Convert to int after ensuring it’s a number
                    pieces = int(float(pieces))
                except (ValueError, TypeError):
                    pieces = 1
            else:
                pieces = 1

            # Step 4: Append the row to the list, repeating it based on 'Pieces'
            for _ in range(pieces):
                duplicated_rows.append(row)

        except Exception as e:
            print(f"Warning: Invalid 'Pieces' value at row {index}, defaulting to 1. Error: {e}")
            duplicated_rows.append(row)

    # Step 5: Convert the list back into a DataFrame
    df_duplicated = pd.DataFrame(duplicated_rows)

    # Step 6: Drop the 'Pieces' column as it's no longer needed
    if 'Pieces' in df_duplicated.columns:
        df_duplicated.drop(columns=['Pieces'], inplace=True)

    # Step 7: Save the updated dataframe back to the final CSV
    df_duplicated.to_csv(final_csv, index=False)
    print(f"Entries duplicated based on 'Pieces' column and saved to: {final_csv}")

# Main Execution For Automation
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

