import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
from sensirion_i2c_driver import I2cConnection
from sensirion_shdlc_driver import ShdlcSerialPort, ShdlcConnection
from sensirion_shdlc_sensorbridge import SensorBridgePort, SensorBridgeShdlcDevice, SensorBridgeI2cProxy
from sensirion_i2c_stc import Stc3xI2cDevice
from sensirion_i2c_stc.stc3x.data_types import Stc31BinaryGas
from sensirion_i2c_driver import I2cConnection
from sensirion_shdlc_driver import ShdlcSerialPort, ShdlcConnection
from sensirion_shdlc_sensorbridge import SensorBridgePort, \
    SensorBridgeShdlcDevice, SensorBridgeI2cProxy
from sensirion_i2c_stc import Stc3xI2cDevice
from sensirion_i2c_stc.stc3x.data_types import Stc31BinaryGas
import csv
import tkinter.scrolledtext as scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
import os


#Function for scrolling screen 
def on_canvas_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))
    
    
# Sensors own functions......................................
#Alicat sensor function
def Alicat_Sensor_Data(port):                                
    try:
        ser = serial.Serial(port, baudrate=19200, timeout=1)
        response = ser.readline().decode().strip()
        flow_rate = response.split(",")[0]
        Alicat_Reading = flow_rate[18:23]
        print(Alicat_Reading)
        return Alicat_Reading
    except Exception as e:
        print(f"Error reading Alicat sensor data: {e}")
        return None
    
#CO2 high concentration sensor function
def CO2_High_Concentration_Sensor(port):
                        
    with ShdlcSerialPort(port, baudrate=460800) as serial_port:
        bridge = SensorBridgeShdlcDevice(ShdlcConnection(serial_port), slave_address=0)
        print("SensorBridge SN: {}".format(bridge.get_serial_number()))
        bridge.set_i2c_frequency(SensorBridgePort.ONE, frequency=400e3)
        bridge.set_supply_voltage(SensorBridgePort.ONE, voltage=3.3)
        bridge.switch_supply_on(SensorBridgePort.ONE)   
        i2c_transceiver = SensorBridgeI2cProxy(bridge, port=SensorBridgePort.ONE)
        stc3x = Stc3xI2cDevice(I2cConnection(i2c_transceiver))
        stc3x.set_bianry_gas(Stc31BinaryGas.Co2InAirRange100)
        gas_concentration, temperature = stc3x.measure_gas_concentration()
        print("{}, {}".format(gas_concentration, temperature))
        print("{:0.2f} vol% ({} ticks), {:0.2f} °F ({} ticks)".format(gas_concentration.vol_percent, gas_concentration.ticks,temperature.degrees_fahrenheit, temperature.ticks))
        CO2_high_output = ("{:0.2f}".format(gas_concentration.vol_percent))
        print(CO2_high_output)
        return CO2_high_output

#CO2 low concentration sensor function
def CO2_Low_Concentration_Sensor1(port):      
    ser = serial.Serial(port, baudrate=115200)  # Change 'COM3' to your Arduino's port
    ser.flushInput()
    ser.flushOutput()
    Co2_low_dataa = ser.read().decode('utf-8').strip()
    Co2_low_dataa = Co2_low_dataa[5:9]
    print("sensor data", Co2_low_dataa )
    return Co2_low_dataa
        

    #     ser1 = serial.Serial(port, baudrate=9600, bytesize=8, timeout=1, stopbits=serial.STOPBITS_ONE)
    #     ser1.flushInput()
    #     ser1.flushOutput()
    #     ser1.write(b'z\r\n')
    #     CO2_Low_Sensor1_Reading = ser1.readline()
    #     return CO2_Low_Sensor1_Reading
    # except Exception as e:
    #     print(f"Error reading CO2 low concentration sensor data: {e}")
    #     return None

# Graph plotting for sensor data....................................
# Common function for plotting function

alicat_data_dict = {}

def plot_sensor_data(ax, time_list, data_list, label, x_label, y_label, title,data,canvas):
    data_list.append(data)
    time_list.append(time.strftime("%H:%M:%S"))
    data_points_to_display = 9
    if len(data_list) > data_points_to_display:
        time_list.pop(0)
        data_list.pop(0)
    if len(data_list) > 0:
        ax.clear()
        ax.plot(time_list, data_list, label=label)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)
        plt.xticks(rotation=45)
    canvas.draw()

# Alicat graph plotting function
alicat_data_list = []
Time1 = []
def Alicat_Sensor_graph_plotting(port_var, sensor_type):
    print("valueeee", port_var)
    if sensor_type == "Alicat_Sensor":
        data = Alicat_Sensor_Data(port_var)
        plot_sensor_data(ax1, Time1, alicat_data_list, 'Alicat Sensor Data', 'Time', 'Flow rate', 'Alicat flow Sensor Graph(SLPM)',data,canvas1)

# Co2 high concentration sensor graph plotting function
co2_high_data_list = []
Time2 = []
def Co2_High_Concentration_sensor_graph_plotting(port_var, sensor_type):
    if sensor_type == "CO2_High":
        data = float(CO2_High_Concentration_Sensor(port_var))
        plot_sensor_data(ax2, Time2, co2_high_data_list, 'CO2 High Concentration Sensor Data', 'Time', 'CO2 concentration(PPM)', 'CO2 high concentration Data Graph', data,canvas2)

# Co2 low concentration graph plotting function
co2_low_data_list = []
Time3 = []
def CO2_low_concentration_sensor_graph_plotting(port_var, sensor_type):
    if sensor_type == "CO2_Low":
        data = CO2_Low_Concentration_Sensor1(port_var)
        plot_sensor_data(ax3, Time3, co2_low_data_list, 'CO2 Low Concentration Sensor Data', 'Time', 'CO2 concentration(PPM)', 'CO2 low concentration Data Graph', data,canvas3)

#check sensor status.........................................................
def check_sensor_data():
    for i, (sensor_var, port_var, result_label) in enumerate(zip( sensor_vars, port_vars, result_labels), start=1):
        sensor_type = sensor_var.get()
        port = port_var.get()      
        print("function is running")  
        print("Port=",port)
        print("Sensorss=",sensor_type)
        if sensor_type != "Select Sensor" and port:
            data = None
            if sensor_type == "Alicat_Sensor":
                data = Alicat_Sensor_Data(port)
            elif sensor_type == "CO2_High":
                data = CO2_High_Concentration_Sensor(port)
            elif sensor_type == "CO2_Low":
                data = CO2_Low_Concentration_Sensor1(port)
            if data is not None:
                if data:                    
                    result_label.config(text=f"Sensor is connected, Data:= {data}, ", foreground="green")
                    #result_label.config(text=f"Sensor is connected {i} Data: {data}")
                    update_graph(port, sensor_type) 
                    start_activity()    
                    print("co2 low")                  
        else:
            result_label.config(text=f"Sensor {i}: Sensor is not connected", foreground="red")
            #result_label.config(text=f"Sensor {i}: Please select a sensor and a port.", foreground="red")

def update_available_ports():
    try:
        available_ports = [port.device for port in serial.tools.list_ports.comports()]        
        for port_dropdown in port_dropdowns:
            port_dropdown['values'] = available_ports
        print("Available Ports:", available_ports)
    except Exception as e:
        print(f"Error updating available ports: {e}")
      
#upgrade graph button
Upgrade_active = False
def toggle_Upgrade_graph():
    global Upgrade_active
    if Upgrade_active:
        Upgrade_active = False
        Upgrade_graph_Button.config(text="START updating graph", bg="green")
        print("..Graph not updating.....")
        
    else:
        Upgrade_active = True
        Upgrade_graph_Button.config(text="STOP updating graph", bg="red")
                      
        print("Graph updating started")
        

##################################################################################
#data logging function.........................................
#To check logging data button state
# Function to start or stop data logging
data_logging_active = False
def toggle_data_logging():
    global data_logging_active
    if data_logging_active:
        data_logging_active = False
        Logging_Data_Button.config(text="START LOGGING DATA")  #, bg="green")
        print("data1")
        filename_entry.config(state="normal")
    else:
        if filename_entry.get():
            data_logging_active = True
            Filenameerror_label.config(text="", fg="green")
            Logging_Data_Button.config(text="STOP LOGGING DATA")#, bg="red")
            filename_entry.config(state="disabled")
            Filenameerror_label.config(bg="")
        else:
            Filenameerror_label.config(text="Please enter the file name", fg="red")

            print("Please enter the file name")  
               
        print("data1")
#Data save into csv file
def save_all_sensor_data_to_csv():
    print("save_all_sensor_data_to_csv")
    csv_headers = []
    csv_data = []
    for i, (Sensor_name_var, sensor_var, port_var, result_label) in enumerate(zip(Sensor_name_vars,sensor_vars, port_vars, result_labels), start=1):
        sensor_type = sensor_var.get()
        Sensor_Name = Sensor_name_var.get()
        port = port_var.get()
        #csv_headers.append(f"{Sensor_Name} ({sensor_type})")
        csv_headers.append(Sensor_Name + "(" + sensor_type + ")")
        if sensor_type == "CO2_High":
            csv_data.append(CO2_High_Concentration_Sensor(port))            
        elif sensor_type == "Alicat_Sensor":
            csv_data.append(Alicat_Sensor_Data(port))
        elif sensor_type == "CO2_Low":
            csv_data.append(CO2_Low_Concentration_Sensor1(port))
        # ...    
    filename = filename_entry.get()
    if not filename:
        print("Please enter a filename.")
        return
    file_exists = os.path.isfile(filename + '.csv') 
    if filename:       
        with open(f"{filename}.csv", mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['Timestamp'] + csv_headers)
            writer.writerow([time.strftime("%H:%M:%S")] + csv_data )
            # csv_data = [Sensor 1 value],[Sensor 2 value], ...
            print(f"Data saved to {filename}.csv")

# Function to stop the update_graph function
def stop_activity():
    global stop_update_flag
    stop_update_flag = True

stop_update_flag = False                                        #if stop button is press than only it will not run - create to stop running this function loop
def update_graph(port_var, sensor_type):                        #stop_update_flag need to be true to run this function
    print("update graph")

     
    print(stop_update_flag)
    if not stop_update_flag:  # Check the flag
        print(port_var)
        if Upgrade_active: 
               # If upgrade graph button is pressed  
            Alicat_Sensor_graph_plotting(port_var, sensor_type)
            Co2_High_Concentration_sensor_graph_plotting(port_var, sensor_type)
            CO2_low_concentration_sensor_graph_plotting(port_var, sensor_type)
            
        if data_logging_active:                                  # If logging data button is pressed
            save_all_sensor_data_to_csv()
    root.after(1000, lambda: update_graph(port_var, sensor_type))

#Reset software
def reset():

    clear_graphs()
    for label in result_labels:
        label.config(text="".ljust(58))
    for port_dropdown in port_dropdowns:
        port_dropdown.set("")
    for Sensor_name_var in Sensor_name_vars:
        Sensor_name_var.set("")
    for sensor_var in sensor_vars:
        sensor_var.set("Select Sensor")
    filename_entry.config(text="")
    stop_activity()
    
def clear_graphs():
    global alicat_data_list, Time1, co2_high_data_list, Time2, co2_low_data_list
    alicat_data_list = []
    Time1 = []
    co2_high_data_list = []
    Time2 = []
    co2_low_data_list = []
    ax1.clear()
    ax2.clear()
    ax3.clear()
    canvas1.draw()
    canvas2.draw()
    canvas3.draw()
    
    
def start_activity():
    global stop_update_flag
    stop_update_flag = False

root = tk.Tk()
root.title("Sensor Data Checker")

# Create a Canvas widget
canvas = tk.Canvas(root)
canvas.grid(row=0, column=0, sticky="nsew")

# Create a Vertical Scrollbar
vsb = ttk.Scrollbar(root, orient=tk.VERTICAL, command=canvas.yview)
vsb.grid(row=0, column=1, sticky="ns")
canvas.configure(yscrollcommand=vsb.set)

# Create a Frame to hold your content
content_frame = ttk.Frame(canvas)
canvas.create_window((0, 0), window=content_frame, anchor=tk.NW)

sensor_vars = []
result_labels = []
port_vars = []
port_dropdowns = []
Sensor_name_vars = []
frames = []
delete_buttons = []

def add_sensor():
    #frame = tk.Frame(frame1, bg="blue")
    frame = tk.Frame(content_frame, bg="blue")
    frame.grid(row=len(frames) + 1, column=0, padx=2, pady=2)
    frames.append(frame)
    print(frames)

    headings = ["Sensor Name", "Sensor Type", "Port", "Result"]

    if len(frames) == 1:
        for col, heading in enumerate(headings):
            label = tk.Label(frame, text=heading, padx=10, pady=5)
            label.grid(row=0,  column=col, padx=2, pady=2)

    Sensor_name_var = tk.StringVar()
    Sensor_name_entry = ttk.Entry(frame, textvariable=Sensor_name_var)
    Sensor_name_entry.grid(row=1, column=0, padx=2, pady=2)
    Sensor_name_vars.append(Sensor_name_var)

    sensor_var = tk.StringVar()
    sensor_var.set("Select Sensor")
    sensor_dropdown = ttk.Combobox(frame, textvariable=sensor_var, values=["Select Sensor", "Alicat_Sensor", "CO2_High", "CO2_Low"])
    sensor_dropdown.grid(row=1, column=1, padx=2, pady=2)
    sensor_vars.append(sensor_var)

    port_var = tk.StringVar()
    port_dropdown = ttk.Combobox(frame, textvariable=port_var)
    port_dropdown.grid(row=1, column=2, padx=2, pady=2)
    port_vars.append(port_var)
    port_dropdowns.append(port_dropdown)

    #result_label = tk.Label(frame, text="                ", padx=2, pady=2) 
    result_label = tk.Label(frame, text="".ljust(58), padx=2, pady=2)                                                #16gap  
    result_label.grid(row=1, column=3, padx=2, pady=2)
    result_labels.append(result_label)

    delete_button = tk.Button(frame, text="Delete", command=lambda f=frame: delete_sensor(f))
    delete_button.grid(row=1, column=4, padx=2, pady=2)
    delete_buttons.append(delete_button)

    update_available_ports()
    update_graph_position()
    canvas.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))

def delete_sensor(frame_to_delete):
    index = frames.index(frame_to_delete)
    if 0 <= index < len(frames):
        frame_to_delete.grid_remove()
        #frame_to_delete.destroy()
        Sensor_name_vars.pop(index)
        sensor_vars.pop(index)
        port_vars.pop(index)
        result_labels.pop(index)
        delete_buttons[index].destroy()
        delete_buttons.pop(index)
        frames.pop(index)

        print(delete_buttons)
        print(len(frames))
        update_graph_position()
        update_available_ports()


def update_graph_position():
    if len(frames) > 0:
        num_graphs = len(graph_widgets)
        row_position = len(frames) + num_graphs + 4
        for graph_widget in graph_widgets:
            add_sensor_button.grid(row=row_position-3, column=2, padx=2, pady=2) 
            check_button.grid(row=row_position-2, column=2, padx=2, pady=2)
            update_ports_button.grid(row=row_position-1, column=2, padx=2, pady=2) 
                         
            canvas1.get_tk_widget().grid(row=row_position, column=0,columnspan=3, padx=2, pady=2)            
            canvas2.get_tk_widget().grid(row=row_position, column=3, columnspan=3, padx=2, pady=2)          
            canvas3.get_tk_widget().grid(row=row_position+1, column=0,columnspan=3, padx=2, pady=2)         
            canvas4.get_tk_widget().grid(row=row_position+1, column=3, columnspan=3, padx=2, pady=2)
            row_position += 1

            
Logging_Data_Button = tk.Button(content_frame, text = "START LOGGING DATA", width=18, command=toggle_data_logging)
Logging_Data_Button.grid(row=0, column=5, padx=10, pady=2)
button_state = Logging_Data_Button.cget("state") 
print(button_state)

Upgrade_graph_Button = tk.Button(content_frame, text = "Upgrade graph", width=18, command=toggle_Upgrade_graph)
Upgrade_graph_Button.grid(row=1, column=5, padx=10, pady=2)
Upgrade_graph_Button_state = Upgrade_graph_Button.cget("state")

Reset_button = tk.Button(content_frame, text="Reset", command=reset, width=18,  bg="orange")
Reset_button.grid(row=2, column=5, columnspan=3, padx=10, pady=2)

Filenameerror_label = tk.Label(content_frame)
Filenameerror_label.grid(row=1, column=3,columnspan=3, padx=10, pady=2)

filename_label = tk.Label(content_frame, text="Enter File Name:")
filename_label.grid(row=0, column=3,columnspan=3, padx=10, pady=2)

filename_var = tk.StringVar()
filename_entry = ttk.Entry(content_frame, textvariable=filename_var, width=12)
filename_entry.grid(row=0, column=4,columnspan=3, padx=10, pady=2)



fig1, ax1 = plt.subplots(figsize=(8, 5))
plt.xticks(rotation=45)
fig2, ax2 = plt.subplots(figsize=(8, 5))
plt.xticks(rotation=45)
fig3, ax3 = plt.subplots(figsize=(8, 5))
plt.xticks(rotation=45)
fig4, ax4 = plt.subplots(figsize=(8, 5))
plt.xticks(rotation=45)


canvas1 = FigureCanvasTkAgg(fig1, master=content_frame)
canvas1.get_tk_widget().grid(row=7, column=0,columnspan=3, padx=2, pady=2)
canvas2 = FigureCanvasTkAgg(fig2, master=content_frame)
canvas2.get_tk_widget().grid(row=7, column=3, columnspan=3, padx=2, pady=2)
canvas3 = FigureCanvasTkAgg(fig3, master=content_frame)
canvas3.get_tk_widget().grid(row=8, column=0, padx=2,columnspan=3, pady=2)
canvas4 = FigureCanvasTkAgg(fig4, master=content_frame)
canvas4.get_tk_widget().grid(row=8, column=3, columnspan=3, padx=2, pady=2)
update_available_ports()

add_sensor_button = tk.Button(content_frame, text="Add Sensor", width=18, command=add_sensor)
add_sensor_button.grid(row=0, column=2, padx=2, pady=2)

check_button = tk.Button(content_frame, text="Check Sensor Data", width=18, command=check_sensor_data)
check_button.grid(row=1, column=2, padx=2, pady=2)

update_ports_button = tk.Button(content_frame, text="Update Available Ports", width=18, command=update_available_ports)
update_ports_button.grid(row=2, column=2, padx=2, pady=2)


graph_widgets = [canvas1, canvas2, canvas3, canvas4]

canvas.bind("<Configure>", on_canvas_configure)

canvas.update_idletasks()
canvas.configure(scrollregion=canvas.bbox("all"))

# Ensure that the frame expands properly when the window is resized
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# Start the Tkinter main loop
root.mainloop()
