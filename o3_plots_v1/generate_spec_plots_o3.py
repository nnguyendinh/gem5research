import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys

# Function to generate a grouped bar chart
def generate_grouped_bar_chart(csv_file):
    # Read the CSV file
    data = pd.read_csv(csv_file)
    
    # Generate a full parameter label including the clock
    data['parameter_label'] = data.apply(lambda row: f"f:{row['fetchToDecodeDelay']} d:{row['decodeToRenameDelay']} r:{row['renameToIEWDelay']}", axis=1)
    
    # Get unique simulation names and parameter labels excluding the clock
    simulation_names = data['simulation_name'].unique()
    parameter_labels = data['parameter_label'].unique()
    clocks = [500, 1000]  # We know the clocks are 500 and 1000
    
    # Define colors for each unique parameter label and clock combination
    full_labels = [f"{param_label}, clock:{clock}" for param_label in parameter_labels for clock in clocks]
    colors = plt.cm.tab10(np.linspace(0, 1, len(full_labels)))
    color_map = dict(zip(full_labels, colors))
    
    # Create a figure and axis
    fig, ax = plt.subplots(figsize=(15, 8))
    
    # Create an index for the simulation names
    indices = np.arange(len(simulation_names))
    
    # Define the width of the bars and the gap between groups
    bar_width = 0.1
    group_gap = 0.3
    
    # Plot each parameter setting and alternate clock values
    for i, param_label in enumerate(parameter_labels):
        param_data = data[data['parameter_label'] == param_label]
        
        for j, clock in enumerate(clocks):
            clock_data = param_data[param_data['clock'] == clock]
            cycle_counts = [clock_data[clock_data['simulation_name'] == sim]['cycle_count'].values[0] if sim in clock_data['simulation_name'].values else 0 for sim in simulation_names]
            positions = indices + (i * 2 * bar_width) + j * bar_width + (i // 6) * group_gap
            full_label = f"{param_label}, clock:{clock}"
            ax.bar(positions, cycle_counts, bar_width, label=full_label, color=color_map[full_label])
    
    # Set the labels and title
    ax.set_xlabel('Simulation Names')
    ax.set_ylabel('Cycle Count')
    ax.set_title('Cycle Count by Simulation and Parameter Settings')
    ax.set_xticks(indices + (len(parameter_labels) * 2 * bar_width + (len(parameter_labels) // 6) * group_gap) / 2)
    ax.set_xticklabels(simulation_names)
    
    # Create a custom legend
    handles = [plt.Rectangle((0, 0), 1, 1, color=color_map[label]) for label in full_labels]
    labels = full_labels
    ax.legend(handles, labels, title='Parameter Settings', bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)
    
    # Adjust layout to make room for the legend
    plt.tight_layout()
    
    # Save the plot as a PNG file based on the CSV file name
    plt.savefig(csv_file.replace('.csv', '_plot.png'))
    
    # Show the plot
    plt.show()

# Check if a CSV file is provided as command line argument
if len(sys.argv) != 2:
    print("Usage: python script_name.py input_file.csv")
    sys.exit(1)

# Get the CSV file name from command line argument
csv_file = sys.argv[1]

# Generate and save the grouped bar chart
generate_grouped_bar_chart(csv_file)