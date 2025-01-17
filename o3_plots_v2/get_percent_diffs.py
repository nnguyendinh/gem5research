import pandas as pd

# Read the CSV file into a DataFrame
csv_file = "rename_to_iew_simulation.csv"  # Replace with the actual filename
data = pd.read_csv(csv_file)

# Group by simulation_name and calculate percent difference
percent_differences = []
for sim_name in data['simulation_name'].unique():
    # Filter data for the current simulation_name
    sim_data = data[data['simulation_name'] == sim_name]
    
    # Extract cycle counts for iewToFetchDelay = 1 and 4
    cycle_1 = sim_data[sim_data['iewToFetchDelay'] == 1]['cycle_count'].values[0]
    cycle_4 = sim_data[sim_data['iewToFetchDelay'] == 4]['cycle_count'].values[0]
    
    # Calculate percent difference
    percent_diff = 100 * abs(cycle_4 - cycle_1) / ((cycle_4 + cycle_1) / 2)
    percent_differences.append((sim_name, percent_diff))

# Print the results
print("Percent Differences (IEWtoFetchDelay = 1 vs 4):")
for sim_name, percent_diff in percent_differences:
    print(f"{sim_name}: {percent_diff:.2f}%")
