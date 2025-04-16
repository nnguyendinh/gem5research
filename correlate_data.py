import pandas as pd
# import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler

# Load the stats from "after" simulations into a structured format
# Replace 'path/to/stats.csv' with the actual path to your data file
# Assumes a CSV file where each row corresponds to a simulation, and columns are stats and performance metrics
stats_file = 'cycle_counts.csv'
data = pd.read_csv(stats_file)
pd.set_option('display.max_rows', None)

# Example structure of 'data':
# | stat1 | stat2 | ... | cycle_count_percent_diff |
# |-------|-------|-----|--------------------------|
# |  val  |  val  | ... |            val           |

# Set the column for performance degradation (percent difference in cycle counts)
performance_column = 'percent_diff_cycles'

# print("Missing values per column:")
# print(data.isna().sum())

# Exclude parameters that do not appear in all simulations
# Drops columns with any missing values (NaNs)
filtered_data = data.dropna(axis=1)

# Initialize the scaler for Z-score normalization
scaler = StandardScaler()

# print(filtered_data.iloc[:,0:5])

columns_to_normalize = filtered_data.columns[3:]  # Exclude the first 3 columns

# Apply Z-score normalization
filtered_data.loc[:, columns_to_normalize] = scaler.fit_transform(filtered_data[columns_to_normalize])

# Compute correlations with the performance column
correlations = filtered_data.corr()[performance_column]

# Sort correlations
sorted_correlations = correlations.sort_values()

# Display top positive and negative correlations
print("Top positive correlations:")
print(sorted_correlations[sorted_correlations > 0.7])  # Adjust threshold as needed

print("Top negative correlations:")
print(sorted_correlations[sorted_correlations < -0.7])  # Adjust threshold as needed

# Parameter name
parameter_name = "system.switch_cpus.statIssuedInstType_0::MemWrite"

# Print the correlation value for the specific parameter
if parameter_name in correlations:
    print(f"Correlation for {parameter_name}: {correlations[parameter_name]}")
else:
    print(f"{parameter_name} is not found in the data.")


# # Visualize correlations using a heatmap
# plt.figure(figsize=(10, 8))
# sns.heatmap(correlations.to_frame(), annot=True, cmap='coolwarm', cbar=True)
# plt.title("Correlation Heatmap with Performance Degradation")
# plt.show()
