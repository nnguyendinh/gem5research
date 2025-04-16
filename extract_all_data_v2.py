from collections import defaultdict
import os
import pandas as pd

# Path to the directory containing simulation folders
stats_dir = 'runs/chipletization/decode_to_rename_v2/stats'
output_csv = 'cycle_counts.csv'

# Function to extract cycle count from stats.txt
def extract_cycle_count(file_path):
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith("system.switch_cpus.numCycles"):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        return int(parts[1])  # Return cycle count as integer
                    except ValueError:
                        return None  # If not a valid number
    return None  # If the stat is not found

# Collect all simulation folders
simulation_folders = [f for f in os.listdir(stats_dir) if os.path.isdir(os.path.join(stats_dir, f))]
simulation_data = []

# Step 1: Group by first and second prefix
grouped_folders = defaultdict(lambda: defaultdict(list))

for s in simulation_folders:
    parts = s.split('_')
    simulation, partition = parts[0], parts[2]
    grouped_folders[simulation][partition].append(s)

# Step 2: Process each simulation name
for simulation in grouped_folders:
    print(f"Processing simulation: {simulation}")

    for partition in grouped_folders[simulation]:
        print(f"  Processing partition: {partition}")

        sim_0_path = os.path.join(stats_dir, f"{simulation}_r_{partition}_i0", "stats.txt")
        sim_2_path = os.path.join(stats_dir, f"{simulation}_r_{partition}_i2", "stats.txt")

        # Extract cycle counts
        sim_0_cycles = extract_cycle_count(sim_0_path) if os.path.exists(sim_0_path) else None
        sim_2_cycles = extract_cycle_count(sim_2_path) if os.path.exists(sim_2_path) else None
        
        # print(simulation)
        if sim_0_cycles is not None and sim_2_cycles is not None:
            # Calculate percent difference
            percent_diff = 100 * abs(sim_2_cycles - sim_0_cycles) / ((sim_0_cycles + sim_0_cycles) / 2)
        else:
            percent_diff = None  # If data is missing

        # Process stats for the "_2" simulation
        sim_2_stats_path = os.path.join(stats_dir, f"{simulation}_r_{partition}_i2", "stats.txt")
        if os.path.exists(sim_2_stats_path):
            stats = {'simulation_id': f"{simulation}_r_{partition}", 'percent_diff_cycles': percent_diff}
            print(percent_diff)
            with open(sim_2_stats_path, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):  # Skip empty lines and comments
                        parts = line.split()
                        if len(parts) >= 2:
                            try:
                                stats[parts[0]] = float(parts[1])  # Convert value to float
                            except ValueError:
                                stats[parts[0]] = parts[1]  # If not float, keep as string
            simulation_data.append(stats)

# Convert to DataFrame and save as CSV
df = pd.DataFrame(simulation_data)
df = df.sort_values(by="simulation_id")  # Sort rows alphabetically by simulation_id
df.to_csv(output_csv, index=False)

print(f"Stats with cycle count percent differences saved to {output_csv}")
