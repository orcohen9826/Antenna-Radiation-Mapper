import serial
import time
import sounddevice as sd
import numpy as np
import wave
import serial.tools.list_ports
import threading
import csv
import os
import queue
from scipy.fft import fft
import matplotlib.pyplot as plt
from graphFromCsv import plot_polar_radiation_pattern , plot_gain_vs_angle , plot_gain_for_all_frequencies , plot_polar_radiation_pattern

# Serial port settings
SERIAL_PORT = None
BAUD_RATE = 9600

# Audio recording settings
SAMPLE_RATE = 44100  # Sample rate in Hz
CHANNELS = 1  # Mono recording

# Default frequency list for analysis 100 hz to 20khz with 100 hz interval
DEFAULT_FREQUENCIES = range(100, 20001, 100)  # Hz
CUT_OFF_FREQUENCY = 2000
CSV_FILENAME = "frequency_analysis.csv"
FREQUENCIES_TO_PLOT = [100, 500, 1000, 2000, 5000, 10000, 20000] # Hz , frequencies to plot in polar radiation pattern

# Queue for FFT data to be processed by the main thread
fft_queue = queue.Queue()

# Create a persistent figure and axis for real-time FFT updates
plt.ion()  # Turn on interactive mode for updating the plot
fig, ax = plt.subplots()
line, = ax.plot([], [], lw=2)
ax.set_xlabel('Frequency (Hz)')
ax.set_ylabel('Magnitude')
ax.set_title('Real-time FFT Analysis')
ax.grid()

# Set limits for initial plot
ax.set_xlim(20, 20000)  # Adjust frequency range from 20 Hz to 20 kHz
ax.set_ylim(0, 10000000)  # Adjust to an exponent of 7 for magnitude range
ax.set_xscale('linear')  # Set the x-axis to a linear scale

# Function to find and initialize the serial port supporting Custom handshake protocol
def find_and_init_serial_port():
    '''send to each port a hndshake message "Recorder handshaked" and wait for a " Mapper handshaked " message to confirm the port'''
    attempts = 3
    for port in serial.tools.list_ports.comports():
        print(f"Trying port: {port.device}")
        for _ in range(attempts):
            try:
                #if ser already open close it
                if 'ser' in locals() or 'ser' in globals():
                    ser.close()
                ser = serial.Serial(port.device, BAUD_RATE, timeout=1 , write_timeout=1)
                time.sleep(2)  # Wait for the serial connection to initialize
                print(f"looking for handshake on port: {port.device}")
                #timout for write is 1 second
                ser.write("Recorder handshaked".encode())
                time.sleep(1)
                if ser.in_waiting > 0:
                    try:
                        line = ser.readline().decode('utf-8').strip()
                        if "Mapper handshaked" in line:
                            print(f"Connected Successfully to serial port: {port.device}")
                            return ser
                    except UnicodeDecodeError:
                        
                        pass
            
            except serial.SerialException as e:
                print(f" Could not open serial port {port.device}. {e}")

        ser.close()    
    return None
                
# Function to record audio from the default microphone
def record_audio(filename, duration):
    """Record audio from the microphone for the given duration and save it to a file."""
    print(f"Recording audio for {duration} seconds...")
    audio_data = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=np.int16)
    sd.wait()  # Wait until the recording is finished
    
    # Save the recording to a WAV file

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit audio
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_data.tobytes())
    print(f"Audio saved as {filename}")

# Function to analyze audio in a separate thread
def analyze_audio_thread(filename, frequencies=DEFAULT_FREQUENCIES):
    """Thread to analyze audio once the recording is complete."""
    analysis_thread = threading.Thread(target=analyze_audio, args=(filename, frequencies))
    analysis_thread.start()

# Function to analyze audio using FFT
def analyze_audio(filename, frequencies=DEFAULT_FREQUENCIES):
    """Perform FFT on the recorded audio and put the results in the queue for main thread processing."""
    # Load audio file
    with wave.open(filename, 'rb') as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        audio_data = wf.readframes(n_frames)
        audio_data = np.frombuffer(audio_data, dtype=np.int16)
    
    # Perform FFT
    fft_result = fft(audio_data)
    freqs = np.fft.fftfreq(len(fft_result), d=1/SAMPLE_RATE)
    magnitudes = np.abs(fft_result)
    
    # Filter frequencies between 20 Hz and 20 kHz
    valid_indices = np.where((freqs >= 20) & (freqs <= 20000))
    freqs = freqs[valid_indices]
    magnitudes = magnitudes[valid_indices]
    
    # Put FFT results in the queue
    fft_queue.put((freqs, magnitudes, filename, frequencies))

# Function to update the FFT live plot with new data
def update_plot(freqs, magnitudes):
    """Update the FFT plot with the new data."""
    ax.set_xlim(20, 20000)  # Set frequency range from 20 Hz to 20 kHz
    line.set_data(freqs, magnitudes)
    ax.relim()  # Recalculate limits for the new data
    ax.autoscale_view()  # Autoscale the view to fit the new data
    fig.canvas.draw()
    fig.canvas.flush_events()

# Function to save extracted frequency data to a CSV file
def save_to_csv(data, frequencies):
    """Save the extracted frequency data to a CSV file."""
    header = ["Angle (degrees)"] + [f"{int(freq)} Hz" for freq in frequencies]
    file_exists = os.path.isfile(CSV_FILENAME)
    
    with open(CSV_FILENAME, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(header)
        writer.writerow(data)

# Function to rename the CSV file after movement is complete
def rename_recordings():
    """Prompt the user to rename the CSV file when movement is complete."""
    global CSV_FILENAME
    new_name = input("Movement complete. Enter a new name for the CSV file (without extension): ")
    if new_name:
        new_filename = f"{new_name}.csv"
        folder_name = os.path.dirname(CSV_FILENAME)
        new_filename = os.path.join(folder_name, new_filename)
        os.rename(CSV_FILENAME, new_filename)
        CSV_FILENAME = new_filename
        print(f"CSV file renamed to {new_filename}")
        # Plot radiation patterns after renaming the file
        plot_csv_data(CSV_FILENAME)

# Function to plot at the end of the program the csv data
def plot_csv_data(CSV_FILENAME):
        plot_gain_vs_angle(CSV_FILENAME,CUT_OFF_FREQUENCY)
        plot_gain_for_all_frequencies(CSV_FILENAME)
        plot_polar_radiation_pattern(CSV_FILENAME, FREQUENCIES_TO_PLOT)

def main():
    global SERIAL_PORT , CSV_FILENAME
    # Find and connect to the serial port
    ser = find_and_init_serial_port()
    
    if ser is None:
        print("Error: Could not find a suitable serial port.")
        print("Please make sure the device is connected and try again.")
        return

    print("Listening to serial port You can start the movement now.")
                            # join folder to filename and create it with time signature mmdd hhmmss

    folder_name = "recordings" + time.strftime("%m%d %H%M%S")
    # update the csv filename to include the folder name
    CSV_FILENAME = os.path.join(folder_name, CSV_FILENAME)

    os.makedirs(folder_name, exist_ok=True)
    while True:            
        # Read a line from the serial port
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            
            # Print received line for debugging purposes
            print(f"Received: {line}")
            
            # Check for the "Start brake" message
            if "Start brake" in line:
                # Extract the current position from the message
                if "current position:" in line:
                    try:
                        current_position = float(line.split(':')[1].strip())
                        print(f"Start of brake detected. Current position: {current_position}")
                        
                        # Record audio and save with the angle as filename
                        filename = f"recording_{int(current_position)}_degrees.wav"

                        filename = os.path.join(folder_name, filename)
                        
                        record_audio(filename, duration=1)  # Recording duration is 1 seconds
                        
                        # Analyze the audio in a separate thread
                        analyze_audio_thread(filename)
                    except ValueError:
                        print("Error parsing the current position.")

            elif "End of brake" in line:
                print("End of brake detected.")
            elif "Movement complete" in line:
                rename_recordings()
                ser.close()
                break
            

        # Check if there is any FFT data in the queue to be processed
        try:
            freqs, magnitudes, filename, frequencies = fft_queue.get_nowait()
            update_plot(freqs, magnitudes)
            
            # Extract the magnitude of the specified frequencies
            angle = filename.split('_')[1]  # Extract angle from filename
            angle = angle.replace('degrees.wav', '')
            extracted_data = [int(angle)]
            
            for freq in frequencies:
                # Find the closest frequency index in the FFT result
                index = np.argmin(np.abs(freqs - freq))
                magnitude_db = int(20 * np.log10(magnitudes[index]))
                extracted_data.append(magnitude_db)
            
            # Save data to CSV
            save_to_csv(extracted_data, frequencies)
        except queue.Empty:
            pass

if __name__ == "__main__":
    main()

