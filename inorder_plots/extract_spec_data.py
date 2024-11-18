import os
import csv
import argparse

# Function to extract parameters from config.ini
def extract_parameters(config_file):
    params = {}
    with open(config_file, 'r') as file:
        lines = file.readlines()
        for i, line in enumerate(lines):
            if line.startswith('decodeToExecuteForwardDelay'):
                params['decodeToExecuteForwardDelay'] = line.strip().split('=')[1].strip()
            elif line.startswith('executeBranchDelay'):
                params['executeBranchDelay'] = line.strip().split('=')[1].strip()
            elif line.startswith('fetch2ToDecodeForwardDelay'):
                params['fetch2ToDecodeForwardDelay'] = line.strip().split('=')[1].strip()
            elif line.startswith('[system.clk_domain]'):
                if i + 2 < len(lines) and lines[i + 2].startswith('clock'):
                    params['clock'] = lines[i + 2].strip().split('=')[1].strip()
    return params

# Function to extract cycle count from stats.txt
def extract_cycle_count(stats_file):
    with open(stats_file, 'r') as file:
        for line in file:
            if line.startswith('system.switch_cpus.numCycles'):
                # Split the line and extract the cycle count before the comment
                return line.split()[1]
    return None

# Main function to process all simulations
def process_simulations(main_folder):
    simulations = []

    for simulation_folder in os.listdir(main_folder):
        sim_path = os.path.join(main_folder, simulation_folder)
        if os.path.isdir(sim_path):
            sim_name = '_'.join(simulation_folder.split('_')[:-1])
            config_file = os.path.join(sim_path, 'config.ini')
            stats_file = os.path.join(sim_path, 'stats.txt')

            if os.path.exists(config_file) and os.path.exists(stats_file):
                params = extract_parameters(config_file)
                cycle_count = extract_cycle_count(stats_file)

                simulation_data = {
                    'simulation_name': sim_name,
                    'decodeToExecuteForwardDelay': params.get('decodeToExecuteForwardDelay', ''),
                    'executeBranchDelay': params.get('executeBranchDelay', ''),
                    'fetch2ToDecodeForwardDelay': params.get('fetch2ToDecodeForwardDelay', ''),
                    'clock': params.get('clock', ''),
                    'cycle_count': cycle_count
                }
                simulations.append(simulation_data)

    # Sort the simulations by name and then by clock speed
    # simulations.sort(key=lambda x: (x['simulation_name'], x['clock'], x['decodeToExecuteForwardDelay'], x['executeBranchDelay'], x['fetch2ToDecodeForwardDelay']))

    simulations.sort(key=lambda x: (
        x['simulation_name'],
        x['clock'],
        int(x['decodeToExecuteForwardDelay']),
        int(x['executeBranchDelay']),
        int(x['fetch2ToDecodeForwardDelay'])
    ))

    # Extract the last folder name from the main folder path for the CSV file name
    last_folder_name = os.path.basename(os.path.dirname(os.path.normpath(main_folder)))
    csv_filename = f"{last_folder_name}_simulation_data.csv"

    # Write to CSV file
    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['simulation_name', 'decodeToExecuteForwardDelay', 'executeBranchDelay', 'fetch2ToDecodeForwardDelay', 'clock', 'cycle_count']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for sim in simulations:
            writer.writerow(sim)
    print(f"CSV file '{csv_filename}' created successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process simulation data.")
    parser.add_argument("main_folder_path", type=str, help="The path to the main folder containing simulation data.")
    args = parser.parse_args()
    process_simulations(args.main_folder_path + '/stats')