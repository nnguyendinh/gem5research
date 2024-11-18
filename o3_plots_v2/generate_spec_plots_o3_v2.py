import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import sys

# Function to generate a grouped bar chart
def generate_grouped_bar_chart(csv_file):
    # Read the CSV file
    data = pd.read_csv(csv_file)
    
    # Generate a full parameter label including the clock
    data['parameter_label'] = data.apply(lambda row: f"Pipeline Delay Cycles:{row['iewToFetchDelay']}", axis=1)
    
    # Get unique simulation names and parameter labels excluding the clock
    simulation_names = data['simulation_name'].unique()
    parameter_labels = data['parameter_label'].unique()
    
    # Create a color map for each parameter label
    colors = plt.cm.tab10(np.linspace(0, 1, len(parameter_labels)))
    color_map = dict(zip(parameter_labels, colors))
    
    # Create a figure and axis
    fig, ax = plt.subplots(figsize=(15, 8))
    
    # Create an index for the simulation names
    indices = np.arange(len(simulation_names))
    
    # Define the width of the bars and the gap between groups
    bar_width = 0.2
    group_gap = 0.3
    
    # Plot each parameter label
    for i, param_label in enumerate(parameter_labels):
        param_data = data[data['parameter_label'] == param_label]
        cycle_counts = [param_data[param_data['simulation_name'] == sim]['cycle_count'].values[0] if sim in param_data['simulation_name'].values else 0 for sim in simulation_names]
        positions = indices + i * (bar_width + group_gap / len(parameter_labels))
        ax.bar(positions, cycle_counts, bar_width, label=param_label, color=color_map[param_label])
    
    # Set the labels and title
    ax.set_xlabel('Simulation Names')
    ax.set_ylabel('Cycle Count')
    ax.set_title('Cycle Count by Simulation and Parameter Settings')
    ax.set_xticks(indices + (len(parameter_labels) * (bar_width + group_gap / len(parameter_labels))) / 2)
    ax.set_xticklabels(simulation_names)
    
    # Create a custom legend
    handles = [plt.Rectangle((0, 0), 1, 1, color=color_map[label]) for label in parameter_labels]
    ax.legend(handles, parameter_labels, title='Parameter Settings', bbox_to_anchor=(1.05, 1), loc='upper left')
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