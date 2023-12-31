# Imports the necessary packages
import tkinter as tk
import datetime
import os
import multiprocessing
import csv
from GUIs import main_menu_gui
from Custom_Packages import gloves
from Custom_Packages import eeg

# import from outside the folder
# import sys
# sys.path.append(r'c:\Users\Data acquisition\sensorimotorkit')
# from sensorimotorkit import acquire_images
from sensorimotorkit.acquire_images.main import main

# Stores all the properties of the windows in one place to make changes easier
def get_window_properties(prop):

    window_title = "Experiment"
    window_width = 1000
    window_height = 800
    window_x = 200
    window_y = 200 
    padx = 5
    pady = 5
    btn_width = 20
    btn_height = 2

    if prop == "window":
        return window_title, window_width, window_height, window_x, window_y
    if prop == "gui":
        return padx, pady, btn_width, btn_height, window_height

# Creates the window
def create_window():

    # Creates the window
    root = tk.Tk()

    # Sets the properties of the window
    title, width, height, x, y = get_window_properties("window")

    # Changes the window's properties
    root.title(title) # Sets the window title
    root.geometry(f"{width}x{height}+{x}+{y}") # Sets the window's dimensions
    return root

# Creates the folder for storing data
def create_storage(partID, protocol):
    current_date = datetime.datetime.now()
    formatted_date = current_date.strftime('%Y%m%d%H%M%S')
    folderID = protocol + "_" + formatted_date + "_" + partID
    base_path = "C:/Users/Data acquisition/bci-data-collection/Data"
    folder_path = base_path + "/" + folderID
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return folder_path

# Gets the instructions for data collection
def get_instructions():
    protocol_path = "C:/Users/Data acquisition/bci-data-collection/Protocols/Main"
    instructions_path = protocol_path + "/Instructions.csv"
    parameters_path = protocol_path + "/Parameters.csv"
    instructions = []
    with open(instructions_path, 'r') as file1:
        reader1 = csv.reader(file1)
        for rowa in reader1:
            instructions.append(rowa)
    instructions.pop(0)
    parameters = []
    with open(parameters_path, 'r') as file2:
        reader2 = csv.reader(file2)
        for rowb in reader2:
            parameters.append(rowb)
    return instructions, parameters   

# Collects the body camera data
def collect_bodycam(event, queue):
    main(duration=10)

# Collects the body camera data
def collect_gloves(event, queue):
    gloves.collect(10)

# Collects the body camera data
def collect_eeg(event, queue):
    #eeg.collect_eeg()
    return

def run_experiment(root, save_path, instructions, parameters):
    event_bodycam = multiprocessing.Event()
    queue_bodycam = multiprocessing.Queue()
    proc_bodycam = multiprocessing.Process(target=collect_bodycam, args=(event_bodycam,queue_bodycam))
    proc_bodycam.start()

    event_gloves = multiprocessing.Event()
    queue_gloves = multiprocessing.Queue()
    proc_gloves = multiprocessing.Process(target=collect_gloves, args=(event_gloves,queue_gloves))
    proc_gloves.start()

    # event_eeg = multiprocessing.Event()
    # queue_eeg = multiprocessing.Queue()
    # proc_eeg = multiprocessing.Process(target=collect_eeg, args=(event_eeg,queue_eeg))
    # proc_eeg.start()

    # Gets the GUI element parameters parameters
    px, py, btn_width, btn_height, window_height = get_window_properties("gui")

    # Stores whether the experiment is running
    running = tk.BooleanVar(root, False)
    started = tk.BooleanVar(root, False)
    collecting = tk.BooleanVar(root, False)
    instruction_index = tk.IntVar(root, 0)
    last_update_time = [None]
    time_passed = [datetime.timedelta(0)]

    # Creates the frame that stores the GUI elements
    frame = tk.Frame(root)
    frame.pack(pady=(window_height//4))

    # Creates the label that displays the time
    timer_lbl = tk.Label(frame, text="0:00:000")
    timer_lbl.grid(row=0, column=0, padx=px, pady=py)

    # Creates the label that displays the instruction
    instruction_lbl = tk.Label(frame, text=instructions[0][5])
    instruction_lbl.grid(row=0, column=1, padx=px, pady=py)

    def update_timer_display():

        if running.get():
            delta = datetime.datetime.now() - last_update_time[0]
            time_passed[0] += delta
            last_update_time[0] = datetime.datetime.now()

        # Compute total seconds
        total_seconds = time_passed[0].seconds + time_passed[0].microseconds / 1e6
        minutes, remainder = divmod(total_seconds, 60)
        seconds = int(remainder)
        milliseconds = int((remainder - seconds) * 1000)

        

        # Checks if a timestamp has been crossed
        if instruction_index.get() < len(instructions):
            if total_seconds >= float(instructions[instruction_index.get()][1]):
                instruction_index.set(instruction_index.get() + 1)
                instruction_lbl.config(text=instructions[instruction_index.get()][5])
                state = instructions[instruction_index.get()][6]
                if state == "Add " and not collecting.get():
                    event_bodycam.set()
                    event_gloves.set()
                    # event_eeg.set()
                    collecting.set(True)
                elif state == "Save " and collecting.get():
                    event_bodycam.clear()
                    event_gloves.clear()
                    # event_eeg.clear()
                    bodycam_data = queue_bodycam.get()
                    gloves_data = queue_gloves.get()
                    # eeg_data = queue_eeg.get()
                    collecting.set(False)
                elif state == "End ":
                    proc_bodycam.terminate()
                    proc_gloves.terminate()
                    # proc_eeg.terminate()
                    proc_bodycam.join()
                    proc_gloves.join()
                    # proc_eeg.join()
                    running.set(False)
        else:
            instruction_lbl.config(text="experiment finished")
        # Update the display
        timer_lbl.config(text="{:02}:{:02}:{:03}".format(minutes, seconds, milliseconds))
            
        # Schedule the function to be called after 50ms for more frequent updates
        root.after(10, update_timer_display)

    # Creates the button to start data collection
    def start_acquisition():
        if not running.get() and not started.get():
            running.set(True)
            started.set(True)
            last_update_time[0] = datetime.datetime.now()
            update_timer_display()
    start_btn = tk.Button(frame, text="Start", command=lambda:start_acquisition(), width=btn_width, height=btn_height)
    start_btn.grid(row=4, column=0, padx=px, pady=py)

    # Creates the button to pause data collection
    def pause():
        if running.get():
            running.set(False)
            delta = datetime.datetime.now() - last_update_time[0]
            time_passed[0] += delta
    pause_btn = tk.Button(frame, text="Pause", command=lambda:pause(), width=btn_width, height=btn_height)
    pause_btn.grid(row=4, column=1, padx=px, pady=py)

    # Creates the button to resume data collection
    def resume():
        if not running.get():
            running.set(True)
            last_update_time[0] = datetime.datetime.now()
    resume_btn = tk.Button(frame, text="Resume", command=lambda:resume(), width=btn_width, height=btn_height)
    resume_btn.grid(row=4, column=2, padx=px, pady=py)

    # Creates the button to end data collection
    def end_acquisition(root):
        proc_bodycam.terminate()
        proc_gloves.terminate()
        proc_bodycam.join()
        proc_gloves.join()
        root.destroy()
        main_menu_gui.open()
    end_btn = tk.Button(frame, text="End", command=lambda:end_acquisition(root), width=btn_width, height=btn_height)
    end_btn.grid(row=4, column=3, padx=px, pady=py)
    return


# Opens the main menu -- called by other scripts
def open_window(partID, protocol):
    root = create_window()
    save_path = create_storage(partID, protocol)
    instructions, parameters = get_instructions()
    run_experiment(root, save_path, instructions, parameters)
    root.mainloop()




