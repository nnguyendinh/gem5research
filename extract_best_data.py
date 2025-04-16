import os
import csv
import argparse

# Function to extract parameters from config.ini
def extract_parameters(stats_file):
    params = {}
    with open(stats_file, 'r') as file:
        lines = file.readlines()
        for i, line in enumerate(lines):
            if line.startswith('system.switch_cpus.branchPred.corrected_0::total'):
                params['branch_correct'] = line.split()[1]
            elif line.startswith('system.switch_cpus.branchPred.mispredicted_0::total'):
                params['branch_miss'] = line.split()[1]
            elif line.startswith('system.switch_cpus.commit.branchMispredicts'):
                params['branch_miss_2'] = line.split()[1]
            elif line.startswith('system.cpu.icache.tags.dataAccesses'):
                params['icache_tags'] = line.split()[1]
            elif line.startswith('system.cpu.icache.demandAccesses::total'):
                params['icache_demands'] = line.split()[1]
            elif line.startswith('system.cpu.icache.ReadReq.accesses::total'):
                params['icache_reads'] = line.split()[1]
            elif line.startswith('system.cpu.icache.overallHits::total'):
                params['icache_hits'] = line.split()[1]
            elif line.startswith('system.switch_cpus.rename.squashedInsts'):
                params['rename_squashed'] = line.split()[1]
            elif line.startswith('system.switch_cpus.decode.squashCycles'):
                params['decode_squashed'] = line.split()[1]
            elif line.startswith('system.switch_cpus.iew.predictedTakenIncorrect'):
                params['pred_taken_wrong'] = line.split()[1]

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
        if os.path.isdir(sim_path) and sim_path.endswith("1"):
            sim_name = '_'.join(simulation_folder.split('_')[:-1])
            stats_file = os.path.join(sim_path, 'stats.txt')

            if os.path.exists(stats_file):
                params = extract_parameters(stats_file)

                simulation_data = {
                    'simulation_name': sim_name,
                    'branch_correct': params.get('branch_correct', ''),
                    'branch_miss': params.get('branch_miss', ''),
                    'branch_miss_2': params.get('branch_miss_2', ''),
                    'icache_tags': params.get('icache_tags', ''),
                    'icache_demands': params.get('icache_demands', ''),
                    'icache_reads': params.get('icache_reads', ''),
                    'icache_hits': params.get('icache_hits', ''),
                    'rename_squashed': params.get('rename_squashed', ''),
                    'decode_squashed': params.get('decode_squashed', ''),
                    'pred_taken_wrong': params.get('pred_taken_wrong', '')
                }
                simulations.append(simulation_data)

    # Sort the simulations by name and then by clock speed
    # simulations.sort(key=lambda x: (x['simulation_name'], x['clock'], x['fetchToDecodeDelay'], x['decodeToRenameDelay'], x['renameToIEWDelay']))

    simulations.sort(key=lambda x: (
        x['simulation_name']
    ))

    # Extract the last folder name from the main folder path for the CSV file name
    last_folder_name = os.path.basename(os.path.dirname(os.path.normpath(main_folder)))
    csv_filename = f"{last_folder_name}_simulation_data.csv"

    # Write to CSV file
    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['simulation_name', 'branch_correct', 'branch_miss', 'branch_miss_2', 'icache_tags', 'icache_demands', 'icache_reads', 'icache_hits', 'rename_squashed', 'decode_squashed', 'pred_taken_wrong']
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