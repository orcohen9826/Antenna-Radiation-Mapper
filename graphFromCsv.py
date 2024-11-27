import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_gain_vs_angle(csv_file, target_frequency):
    """
    Generates a graph (Graph 1) showing Gain vs Angle for a specific frequency.
    
    Args:
    csv_file (str): Path to the CSV file containing the data.
    target_frequency (float): The exact frequency (in Hz) for which the graph is plotted.
    """
    # Load CSV data
    data = pd.read_csv(csv_file)
    angles = data.iloc[:, 0]  # First column: Angles
    
    # Ensure the target frequency exists in the data or find the closest match
    frequency_columns = data.columns[1:]  # All other columns: Frequencies
    available_frequencies = frequency_columns.str.replace(" Hz", "").astype(float)
    
    # Match target frequency to the correct column
    if target_frequency not in available_frequencies.values:
        raise ValueError(f"The frequency {target_frequency} Hz is not in the CSV file.")
    
    # Convert to Series to access `.iloc`
    available_frequencies = pd.Series(available_frequencies.values, index=frequency_columns)
    target_column = available_frequencies[available_frequencies == target_frequency].index[0]
    gains = data[target_column]  # Retrieve Gain for the specified frequency
    
    # Plotting
    plt.figure(figsize=(8, 5))
    plt.plot(angles, gains, marker='o', label=f'{target_frequency} Hz', color='blue')
    plt.title(f"Gain vs Angle at {target_frequency} Hz", fontsize=14)
    plt.xlabel("Angle (degrees)", fontsize=12)
    plt.ylabel("Gain (dB)", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.show()

def plot_gain_for_all_frequencies(csv_file):
    """
    Generates a graph (Graph 2) showing Gain vs Angle for all frequencies.
    
    Args:
    csv_file (str): Path to the CSV file containing the data.
    """
    # Load CSV data
    data = pd.read_csv(csv_file)
    angles = data.iloc[:, 0]  # First column: Angles
    frequency_columns = data.columns[1:]  # All other columns: Frequencies
    available_frequencies = frequency_columns.str.replace(" Hz", "").astype(float)
    
    # Plotting
    plt.figure(figsize=(10, 6))
    for freq, col in zip(available_frequencies, frequency_columns):
        plt.plot(angles, data[col], label=f'{freq} Hz')
    
    plt.title("Gain vs Angle for Multiple Frequencies", fontsize=14)
    plt.xlabel("Angle (degrees)", fontsize=12)
    plt.ylabel("Gain (dB)", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(title="Frequency (Hz)", fontsize=10, ncol=2)  # Adjust columns for readability
    plt.tight_layout()
    plt.show()




def plot_polar_radiation_pattern(csv_file, frequencies):
    """
    Plots polar radiation patterns for the given frequencies.
    Extends data from 0-180 degrees to 0-360 degrees with mirrored values.
    
    Args:
    csv_file (str): Path to the CSV file containing antenna data.
    frequencies (list): A list of frequencies (in Hz) to plot.
    """
    # Load the CSV data
    df = pd.read_csv(csv_file)
    
    # Extract available frequencies from column names (remove " Hz")
    available_frequencies = df.columns[1:].str.replace(" Hz", "").astype(float)
    available_frequencies = pd.Series(available_frequencies)  # Convert to Series for proper indexing
    
    # Ensure the frequencies exist in the data or find the closest frequencies
    actual_frequencies = []
    for freq in frequencies:
        if freq in available_frequencies.values:
            actual_frequencies.append(freq)
        else:
            closest_freq = available_frequencies.iloc[(available_frequencies - freq).abs().argmin()]
            actual_frequencies.append(closest_freq)
            print(f"Frequency {freq} Hz not found. Using closest frequency: {closest_freq} Hz.")
    
    # Convert frequencies to match the column names in the DataFrame
    selected_columns = [f"{freq} Hz" for freq in actual_frequencies]
    
    # Extract the angles and gain values for the selected frequencies
    angles = np.radians(df["Angle (degrees)"])  # Convert degrees to radians for polar plot
    
    # Extend the data for 180°-360° by mirroring the data
    extended_angles = np.concatenate([angles, angles + np.pi])  # Add 180° in radians
    plt.figure(figsize=(10, 8), dpi=100)
    ax = plt.subplot(111, polar=True)
    
    for freq, col in zip(actual_frequencies, selected_columns):
        gain = df[col]
        mirrored_gain = np.concatenate([gain, gain[::-1]])  # Mirror the gain values
        ax.plot(extended_angles, mirrored_gain, label=f"{freq} Hz")
    
    # Customize the plot
    ax.set_theta_zero_location("N")  # Zero degrees at the top
    ax.set_theta_direction(-1)  # Clockwise direction
    plt.title("Polar Radiation Patterns for Selected Frequencies", va='bottom', fontsize=14)
    plt.legend(title="Frequencies", fontsize=10, loc="upper right", bbox_to_anchor=(1.1, 1.1))
    plt.tight_layout()
    plt.show()

# Example usage:
def main():
    plot_gain_vs_angle('Antenna_Data_in_Correct_Format.csv', 3039.39)
    plot_gain_for_all_frequencies('Antenna_Data_in_Correct_Format.csv')
    plot_polar_radiation_pattern('Antenna_Data_in_Correct_Format.csv', [3039.39, 2000, 5000, 4000, 1000])

if __name__ == "__main__":
    main()