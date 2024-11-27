
# import serial
# import time
# import sounddevice as sd
# import numpy as np
# import wave
# import serial.tools.list_ports

# # Serial port settings
# SERIAL_PORT = None
# BAUD_RATE = 9600

# # Audio recording settings
# SAMPLE_RATE = 44100  # Sample rate in Hz
# CHANNELS = 1  # Mono recording

# def find_serial_port():
#     """Find an available serial port automatically."""
#     ports = list(serial.tools.list_ports.comports())
#     for port in ports:
#         try:
#             s = serial.Serial(port.device, BAUD_RATE, timeout=1)
#             s.close()
#             return port.device
#         except (serial.SerialException, OSError):
#             continue
#     return None

# def record_audio(filename, duration):
#     """Record audio from the microphone for the given duration and save it to a file."""
#     print(f"Recording audio for {duration} seconds...")
#     audio_data = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=np.int16)
#     sd.wait()  # Wait until the recording is finished
    
#     # Save the recording to a WAV file
#     with wave.open(filename, 'wb') as wf:
#         wf.setnchannels(CHANNELS)
#         wf.setsampwidth(2)  # 16-bit audio
#         wf.setframerate(SAMPLE_RATE)
#         wf.writeframes(audio_data.tobytes())
#     print(f"Audio saved as {filename}")

# def main():
#     global SERIAL_PORT
#     # Find and connect to the serial port
#     SERIAL_PORT = find_serial_port()
#     if SERIAL_PORT is None:
#         print("Error: Could not find a suitable serial port.")
#         return

#     try:
#         ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
#         time.sleep(2)  # Wait for the serial connection to initialize
#         print(f"Connected to serial port: {SERIAL_PORT}")
#     except serial.SerialException as e:
#         print(f"Error: Could not open serial port {SERIAL_PORT}. {e}")
#         return
    
#     print("Listening to serial port for brake commands...")
#     while True:
#         # Read a line from the serial port
#         if ser.in_waiting > 0:
#             line = ser.readline().decode('utf-8').strip()
            
#             # Print received line for debugging purposes
#             print(f"Received: {line}")
            
#             # Check for the "Start brake" message
#             if "Start brake" in line:
#                 # Extract the current position from the message
#                 if "current position:" in line:
#                     try:
#                         current_position = float(line.split(':')[1].strip())
#                         print(f"Start of brake detected. Current position: {current_position}")
                        
#                         # Record audio and save with the angle as filename
#                         filename = f"recording_{current_position:.2f}_degrees.wav"
#                         record_audio(filename, duration=1)  # Recording duration is 5 seconds
#                     except ValueError:
#                         print("Error parsing the current position.")

#             elif "End of brake" in line:
#                 print("End of brake detected.")

# if __name__ == "__main__":
#     main()






































# import serial
# import time
# import sounddevice as sd
# import numpy as np
# import wave
# import serial.tools.list_ports
# import threading
# import csv
# import os
# from scipy.fft import fft
# import matplotlib.pyplot as plt

# # Serial port settings
# SERIAL_PORT = None
# BAUD_RATE = 9600

# # Audio recording settings
# SAMPLE_RATE = 44100  # Sample rate in Hz
# CHANNELS = 1  # Mono recording

# # Default frequency list for analysis
# DEFAULT_FREQUENCIES = [50, 100, 200, 500, 1000, 2000, 5000]  # Hz
# CSV_FILENAME = "frequency_analysis.csv"

# def find_serial_port():
#     """Find an available serial port automatically."""
#     ports = list(serial.tools.list_ports.comports())
#     for port in ports:
#         try:
#             s = serial.Serial(port.device, BAUD_RATE, timeout=1)
#             s.close()
#             return port.device
#         except (serial.SerialException, OSError):
#             continue
#     return None

# def record_audio(filename, duration):
#     """Record audio from the microphone for the given duration and save it to a file."""
#     print(f"Recording audio for {duration} seconds...")
#     audio_data = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=np.int16)
#     sd.wait()  # Wait until the recording is finished
    
#     # Save the recording to a WAV file
#     with wave.open(filename, 'wb') as wf:
#         wf.setnchannels(CHANNELS)
#         wf.setsampwidth(2)  # 16-bit audio
#         wf.setframerate(SAMPLE_RATE)
#         wf.writeframes(audio_data.tobytes())
#     print(f"Audio saved as {filename}")

# def analyze_audio_thread(filename, frequencies=DEFAULT_FREQUENCIES):
#     """Thread to analyze audio once the recording is complete."""
#     analysis_thread = threading.Thread(target=analyze_audio, args=(filename, frequencies))
#     analysis_thread.start()

# def analyze_audio(filename, frequencies=DEFAULT_FREQUENCIES):
#     """Perform FFT on the recorded audio and save the results."""
#     # Load audio file
#     with wave.open(filename, 'rb') as wf:
#         n_channels = wf.getnchannels()
#         sampwidth = wf.getsampwidth()
#         framerate = wf.getframerate()
#         n_frames = wf.getnframes()
#         audio_data = wf.readframes(n_frames)
#         audio_data = np.frombuffer(audio_data, dtype=np.int16)
    
#     # Perform FFT
#     fft_result = fft(audio_data)
#     freqs = np.fft.fftfreq(len(fft_result), d=1/SAMPLE_RATE)
#     magnitudes = np.abs(fft_result)
    
#     # Plot FFT result
#     plt.figure()
#     plt.plot(freqs[:len(freqs)//2], 20 * np.log10(magnitudes[:len(magnitudes)//2]))
#     plt.xlabel('Frequency (Hz)')
#     plt.ylabel('Magnitude (dB)')
#     plt.title(f'FFT of {filename}')
#     plt.grid()
#     plt.show()
    
#     # Extract the magnitude of the specified frequencies
#     angle = filename.split('_')[1]  # Extract angle from filename
#     angle = angle.replace('degrees.wav', '')
#     extracted_data = [angle]
    
#     for freq in frequencies:
#         # Find the closest frequency index in the FFT result
#         index = np.argmin(np.abs(freqs - freq))
#         magnitude_db = 20 * np.log10(magnitudes[index])
#         extracted_data.append(magnitude_db)
    
#     # Save data to CSV
#     save_to_csv(extracted_data, frequencies)

# def save_to_csv(data, frequencies):
#     """Save the extracted frequency data to a CSV file."""
#     header = ["Angle (degrees)"] + [f"{freq} Hz" for freq in frequencies]
#     file_exists = os.path.isfile(CSV_FILENAME)
    
#     with open(CSV_FILENAME, mode='a', newline='') as file:
#         writer = csv.writer(file)
#         if not file_exists:
#             writer.writerow(header)
#         writer.writerow(data)

# def rename_recordings():
#     """Prompt the user to rename the CSV file when movement is complete."""
#     new_name = input("Movement complete. Enter a new name for the CSV file (without extension): ")
#     if new_name:
#         new_filename = f"{new_name}.csv"
#         os.rename(CSV_FILENAME, new_filename)
#         print(f"CSV file renamed to {new_filename}")

# def main():
#     global SERIAL_PORT
#     # Find and connect to the serial port
#     SERIAL_PORT = find_serial_port()
#     if SERIAL_PORT is None:
#         print("Error: Could not find a suitable serial port.")
#         return

#     try:
#         ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
#         time.sleep(2)  # Wait for the serial connection to initialize
#         print(f"Connected to serial port: {SERIAL_PORT}")
#     except serial.SerialException as e:
#         print(f"Error: Could not open serial port {SERIAL_PORT}. {e}")
#         return
    
#     print("Listening to serial port for brake commands...")
#     while True:
#         # Read a line from the serial port
#         if ser.in_waiting > 0:
#             line = ser.readline().decode('utf-8').strip()
            
#             # Print received line for debugging purposes
#             print(f"Received: {line}")
            
#             # Check for the "Start brake" message
#             if "Start brake" in line:
#                 # Extract the current position from the message
#                 if "current position:" in line:
#                     try:
#                         current_position = float(line.split(':')[1].strip())
#                         print(f"Start of brake detected. Current position: {current_position}")
                        
#                         # Record audio and save with the angle as filename
#                         filename = f"recording_{current_position:.2f}_degrees.wav"
#                         record_audio(filename, duration=1)  # Recording duration is 5 seconds
                        
#                         # Analyze the audio in a separate thread
#                         analyze_audio_thread(filename)
#                     except ValueError:
#                         print("Error parsing the current position.")

#             elif "End of brake" in line:
#                 print("End of brake detected.")
#             elif "Movement complete" in line:
#                 rename_recordings()

# if __name__ == "__main__":
#     main()

























































# import serial
# import time
# import sounddevice as sd
# import numpy as np
# import wave
# import serial.tools.list_ports
# import threading
# import csv
# import os
# import queue
# from scipy.fft import fft
# import matplotlib.pyplot as plt

# # Serial port settings
# SERIAL_PORT = None
# BAUD_RATE = 9600

# # Audio recording settings
# SAMPLE_RATE = 44100  # Sample rate in Hz
# CHANNELS = 1  # Mono recording

# # Default frequency list for analysis
# DEFAULT_FREQUENCIES = [50, 100, 200, 500, 1000, 2000, 5000]  # Hz
# CSV_FILENAME = "frequency_analysis.csv"

# # Queue for FFT data to be processed by the main thread
# fft_queue = queue.Queue()

# # Create a persistent figure and axis for real-time FFT updates
# plt.ion()  # Turn on interactive mode for updating the plot
# fig, ax = plt.subplots()
# line, = ax.plot([], [], lw=2)
# ax.set_xlabel('Frequency (Hz)')
# ax.set_ylabel('Magnitude (dB)')
# ax.set_title('Real-time FFT Analysis')
# ax.grid()

# # Set limits for initial plot
# ax.set_xlim(0, 5000)  # Adjust as needed for frequency range of interest
# ax.set_ylim(-100, 100)  # Adjust as needed for magnitude range

# def find_serial_port():
#     """Find an available serial port automatically."""
#     ports = list(serial.tools.list_ports.comports())
#     for port in ports:
#         try:
#             s = serial.Serial(port.device, BAUD_RATE, timeout=1)
#             s.close()
#             return port.device
#         except (serial.SerialException, OSError):
#             continue
#     return None

# def record_audio(filename, duration):
#     """Record audio from the microphone for the given duration and save it to a file."""
#     print(f"Recording audio for {duration} seconds...")
#     audio_data = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=np.int16)
#     sd.wait()  # Wait until the recording is finished
    
#     # Save the recording to a WAV file
#     with wave.open(filename, 'wb') as wf:
#         wf.setnchannels(CHANNELS)
#         wf.setsampwidth(2)  # 16-bit audio
#         wf.setframerate(SAMPLE_RATE)
#         wf.writeframes(audio_data.tobytes())
#     print(f"Audio saved as {filename}")

# def analyze_audio_thread(filename, frequencies=DEFAULT_FREQUENCIES):
#     """Thread to analyze audio once the recording is complete."""
#     analysis_thread = threading.Thread(target=analyze_audio, args=(filename, frequencies))
#     analysis_thread.start()

# def analyze_audio(filename, frequencies=DEFAULT_FREQUENCIES):
#     """Perform FFT on the recorded audio and put the results in the queue for main thread processing."""
#     # Load audio file
#     with wave.open(filename, 'rb') as wf:
#         n_channels = wf.getnchannels()
#         sampwidth = wf.getsampwidth()
#         framerate = wf.getframerate()
#         n_frames = wf.getnframes()
#         audio_data = wf.readframes(n_frames)
#         audio_data = np.frombuffer(audio_data, dtype=np.int16)
    
#     # Perform FFT
#     fft_result = fft(audio_data)
#     freqs = np.fft.fftfreq(len(fft_result), d=1/SAMPLE_RATE)
#     magnitudes = 20 * np.log10(np.abs(fft_result))
    
#     # Put FFT results in the queue
#     fft_queue.put((freqs, magnitudes, filename, frequencies))

# def update_plot(freqs, magnitudes):
#     """Update the FFT plot with the new data."""
#     ax.set_xlim(0, max(freqs[:len(freqs)//2]))  # Set frequency range based on the FFT result
#     line.set_data(freqs[:len(freqs)//2], magnitudes[:len(magnitudes)//2])
#     ax.relim()  # Recalculate limits for the new data
#     ax.autoscale_view()  # Autoscale the view to fit the new data
#     fig.canvas.draw()
#     fig.canvas.flush_events()

# def save_to_csv(data, frequencies):
#     """Save the extracted frequency data to a CSV file."""
#     header = ["Angle (degrees)"] + [f"{freq} Hz" for freq in frequencies]
#     file_exists = os.path.isfile(CSV_FILENAME)
    
#     with open(CSV_FILENAME, mode='a', newline='') as file:
#         writer = csv.writer(file)
#         if not file_exists:
#             writer.writerow(header)
#         writer.writerow(data)

# def rename_recordings():
#     """Prompt the user to rename the CSV file when movement is complete."""
#     new_name = input("Movement complete. Enter a new name for the CSV file (without extension): ")
#     if new_name:
#         new_filename = f"{new_name}.csv"
#         os.rename(CSV_FILENAME, new_filename)
#         print(f"CSV file renamed to {new_filename}")

# def main():
#     global SERIAL_PORT
#     # Find and connect to the serial port
#     SERIAL_PORT = find_serial_port()
#     if SERIAL_PORT is None:
#         print("Error: Could not find a suitable serial port.")
#         return

#     try:
#         ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
#         time.sleep(2)  # Wait for the serial connection to initialize
#         print(f"Connected to serial port: {SERIAL_PORT}")
#     except serial.SerialException as e:
#         print(f"Error: Could not open serial port {SERIAL_PORT}. {e}")
#         return
    
#     print("Listening to serial port for brake commands...")
#     while True:
#         # Read a line from the serial port
#         if ser.in_waiting > 0:
#             line = ser.readline().decode('utf-8').strip()
            
#             # Print received line for debugging purposes
#             print(f"Received: {line}")
            
#             # Check for the "Start brake" message
#             if "Start brake" in line:
#                 # Extract the current position from the message
#                 if "current position:" in line:
#                     try:
#                         current_position = float(line.split(':')[1].strip())
#                         print(f"Start of brake detected. Current position: {current_position}")
                        
#                         # Record audio and save with the angle as filename
#                         filename = f"recording_{current_position:.2f}_degrees.wav"
#                         record_audio(filename, duration=1)  # Recording duration is 5 seconds
                        
#                         # Analyze the audio in a separate thread
#                         analyze_audio_thread(filename)
#                     except ValueError:
#                         print("Error parsing the current position.")

#             elif "End of brake" in line:
#                 print("End of brake detected.")
#             elif "Movement complete" in line:
#                 rename_recordings()

#         # Check if there is any FFT data in the queue to be processed
#         try:
#             freqs, magnitudes, filename, frequencies = fft_queue.get_nowait()
#             update_plot(freqs, magnitudes)
            
#             # Extract the magnitude of the specified frequencies
#             angle = filename.split('_')[1]  # Extract angle from filename
#             angle = angle.replace('degrees.wav', '')
#             extracted_data = [angle]
            
#             for freq in frequencies:
#                 # Find the closest frequency index in the FFT result
#                 index = np.argmin(np.abs(freqs - freq))
#                 magnitude_db = magnitudes[index]
#                 extracted_data.append(magnitude_db)
            
#             # Save data to CSV
#             save_to_csv(extracted_data, frequencies)
#         except queue.Empty:
#             pass

# if __name__ == "__main__":
#     main()















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

# Default frequency list for analysis
DEFAULT_FREQUENCIES = [50, 100, 200, 500, 1000, 2000, 5000]  # Hz
CSV_FILENAME = "frequency_analysis.csv"

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

def find_serial_port():
    """Find an available serial port automatically."""
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        try:
            s = serial.Serial(port.device, BAUD_RATE, timeout=1)
            s.close()
            return port.device
        except (serial.SerialException, OSError):
            continue
    return None

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

def analyze_audio_thread(filename, frequencies=DEFAULT_FREQUENCIES):
    """Thread to analyze audio once the recording is complete."""
    analysis_thread = threading.Thread(target=analyze_audio, args=(filename, frequencies))
    analysis_thread.start()

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

def update_plot(freqs, magnitudes):
    """Update the FFT plot with the new data."""
    ax.set_xlim(20, 20000)  # Set frequency range from 20 Hz to 20 kHz
    line.set_data(freqs, magnitudes)
    ax.relim()  # Recalculate limits for the new data
    ax.autoscale_view()  # Autoscale the view to fit the new data
    fig.canvas.draw()
    fig.canvas.flush_events()

def save_to_csv(data, frequencies):
    """Save the extracted frequency data to a CSV file."""
    header = ["Angle (degrees)"] + [f"{int(freq)} Hz" for freq in frequencies]
    file_exists = os.path.isfile(CSV_FILENAME)
    
    with open(CSV_FILENAME, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(header)
        writer.writerow(data)

def rename_recordings():
    """Prompt the user to rename the CSV file when movement is complete."""
    new_name = input("Movement complete. Enter a new name for the CSV file (without extension): ")
    if new_name:
        new_filename = f"{new_name}.csv"
        os.rename(CSV_FILENAME, new_filename)
        print(f"CSV file renamed to {new_filename}")
        # Plot radiation patterns after renaming the file
        plot_gain_vs_angle(CSV_FILENAME, 3039.39)
        plot_gain_for_all_frequencies(CSV_FILENAME)
        plot_polar_radiation_pattern(CSV_FILENAME, DEFAULT_FREQUENCIES)

def main():
    global SERIAL_PORT
    # Find and connect to the serial port
    SERIAL_PORT = find_serial_port()
    if SERIAL_PORT is None:
        print("Error: Could not find a suitable serial port.")
        return

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # Wait for the serial connection to initialize
        print(f"Connected to serial port: {SERIAL_PORT}")
    except serial.SerialException as e:
        print(f"Error: Could not open serial port {SERIAL_PORT}. {e}")
        return
    
    print("Listening to serial port for brake commands...")
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
                        record_audio(filename, duration=1)  # Recording duration is 1 seconds
                        
                        # Analyze the audio in a separate thread
                        analyze_audio_thread(filename)
                    except ValueError:
                        print("Error parsing the current position.")

            elif "End of brake" in line:
                print("End of brake detected.")
            elif "Movement complete" in line:
                rename_recordings()

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

