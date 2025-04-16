import pandas as pd
import sys

def csv_to_python_dict(csv_file, output_file):
    # Read CSV
    df = pd.read_csv(csv_file)
    
    # Create the dictionary representation
    data_dict = "data = {\n"
    for column in df.columns:
        if column == 'percent_diff_cycles':
            values = df[column].tolist()
            data_dict += f"    '{column}': {values},\n"
    data_dict += "}\n"
    
    # Write to output Python file
    with open(output_file, 'w') as f:
        f.write(data_dict)
    
    print(f"Python file '{output_file}' has been created successfully!")

# Example usage
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py input.csv output.py")
    else:
        csv_to_python_dict(sys.argv[1], sys.argv[2])
