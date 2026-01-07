#/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import subprocess
import re
import webbrowser
import time

APP_VERSION = str("0.1.4")

def scan_wifi():
    """ Powershell command example output
    SSID 2 : THE_NEIGHBORS_WIFI
    Network type            : Infrastructure
    Authentication          : WPA2-Personal
    Encryption              : CCMP
    BSSID 1                 : a0:b1:c2:d3:e4:cb
         Signal             : 24%
         Radio type         : 802.11ax
         Channel            : 44
         Basic rates (Mbps) : 6 12 24
         Other rates (Mbps) : 9 18 36 48 54
    BSSID 2                 : a0:b1:c2:d3:e4:ca
         Signal             : 38%
         Radio type         : 802.11ac
         Channel            : 1
         Basic rates (Mbps) : 1 2 5.5 11
         Other rates (Mbps) : 6 9 12 18 24 36 48 54
    BSSID 3                 : a0:b1:c2:d3:e4:3b
    """
    command = "netsh wlan show networks mode=bssid"
    ps_cmd_output = subprocess.run(command, capture_output=True, text=True, shell=True)
    
    networks = []
    current_ssid = None
    current_bssid = None

    for line in ps_cmd_output.stdout.split("\n"):
        line = line.strip()

        ssid_match = re.match(r"SSID \d+ : (.+)", line)
        mac_match = re.match(r"BSSID \d+ *: ([0-9A-Fa-f:-]+)", line)
        signal_match = re.match(r"Signal\s*:\s*(\d+)%", line)
        channel_match = re.match(r"Channel\s*:\s*(\d+)", line)

        if ssid_match:
            current_ssid = ssid_match.group(1).strip() or "Hidden SSID"
        elif mac_match and current_ssid:
            current_bssid = mac_match.group(1)
            networks.append([current_ssid, current_bssid, "No Data", "No Data"])
        elif signal_match and current_bssid:
            networks[-1][2] = f"{signal_match.group(1)}%"
        elif channel_match and current_bssid:
            networks[-1][3] = channel_match.group(1)

    tree.delete(*tree.get_children())

    sorted_networks = sorted(networks, key=lambda x: int(x[2].strip('%')) if x[2] != "N/A" else -1, reverse=True)

    for net in sorted_networks:
        tree.insert("", tk.END, values=net)

    root.after(6000, scan_wifi)  # Auto-refresh the wireless data every 6 seconds. Increase if performance issues are encountered.

# Open webbrowser and send to the GitHub repo to check for updates. Called from top layer menu bar.
def show_check_4_updates():
    webbrowser.open("https://github.com/GoobyFRS/Goobs-WiFi-Scanner")

# Clean user-prompt-able exit method. Called from top layer menu bar.
def exit_app():
    root.quit()

def update_gui_timestamp():
    current_time = time.strftime("%H:%M:%S")
    timestamp_label.config(text=f"Last Updated: {current_time}")
    root.after(1000, update_gui_timestamp)  # Update every one seconds.

# Create and define the text boxes to support user-provided reference data.
def tkt_reference_placeholder(entry, placeholder):
    # Adds a placeholder effect to the entry field
    def on_focus_in(event): # Event is called during runtime. DO NOT CHANGE.
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(fg="black")  # User-Input data in Black instead of grey.

    def on_focus_out(event):
        if not entry.get():
            entry.insert(0, placeholder)
            entry.config(fg="gray")  # User-Input data in Black instead of grey.

    entry.insert(0, placeholder)
    entry.config(fg="gray")
    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)

""" COMMENTED OUT UNTIL FIRST BUILD """
def export_csv():
    # Build a default filename with timestamp
    ts = time.strftime("%Y%m%d_%H%M%S")
    default_name = f"wireless_scan_{ts}.csv"
    try:
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default_name,
                                            filetypes=[("CSV files", "*.csv"), ("All files", "*")])
        if not path:
            return

        # Collect rows from the treeview
        rows = []
        for iid in tree.get_children():
            vals = tree.item(iid, "values")
            rows.append(vals)

        # Write CSV
        import csv
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["SSID", "MAC Address", "Signal Strength", "Channel"]) 
            for r in rows:
                writer.writerow(r)
    except Exception as e:
        tk.messagebox.showerror("Export Error", f"Failed to export CSV: {e}")
#"""

# ALL APPLICATION FUNCTIONS BELONG ABOVE THIS LINE!
# ALL GUI BUILDING BELOG BELOW THIS LINE!

# Build the main application window.
root = tk.Tk()
root.title(f"Goobs WiFi Scanner {APP_VERSION}") # Please update title to reflect new versioning.
root.geometry("720x480")

# Create the top layer menu bar.
menu_bar = tk.Menu(root)

# File menu in the top layer menu bar.
file_menu = tk.Menu(menu_bar, tearoff=0)

file_menu.add_command(label="Export CSV", command=export_csv) # Remove comment 
file_menu.add_separator()
file_menu.add_command(label="Exit", command=exit_app)
menu_bar.add_cascade(label="File", menu=file_menu)

# Help menu in the top layer menu bar.
help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="Check for Updates", command=show_check_4_updates)
menu_bar.add_cascade(label="Help", menu=help_menu)

# Attach/Append menu bar to primary window.
root.config(menu=menu_bar)

# MAIN DATA TABLE DISPLAY BELOW THIS LINE!
# Define table columns.
columns = ("SSID", "MAC Address", "Signal Strength", "Channel")
tree_frame = tk.Frame(root)
tree_frame.pack(expand=True, fill="both")

tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
tree_scroll.pack(side="right", fill="y")

tree = ttk.Treeview(tree_frame, columns=columns, show="headings", yscrollcommand=tree_scroll.set)
tree_scroll.config(command=tree.yview)

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=140)

tree.pack(expand=True, fill="both")

entry_frame = tk.Frame(root)
entry_frame.pack(fill="x", padx=10, pady=5)

# Incident Reference text box.
tk.Label(entry_frame, text="Reference:").grid(row=0, column=0, padx=(0, 5), sticky="w")
reference_entry = tk.Entry(entry_frame, width=20)
reference_entry.grid(row=0, column=1, padx=(0, 20))
tkt_reference_placeholder(reference_entry, "INC000012345")

# Department Reference text box.
tk.Label(entry_frame, text="Department:").grid(row=0, column=2, padx=(0, 5), sticky="w")
department_entry = tk.Entry(entry_frame, width=20)
department_entry.grid(row=0, column=3)
tkt_reference_placeholder(department_entry, "Men's Shoes")
# END SPACE DEDICATED TO REFERNCE BOXES

# Add a manual scan button.
scan_button = tk.Button(root, text="Scan Wi-Fi", command=scan_wifi)
scan_button.pack(pady=10)

# Append Timestamp to the bottom left of the window.
timestamp_label = tk.Label(root, text="", anchor="w", padx=10)
timestamp_label.pack(side="bottom", fill="x")

# END OF GUI BUILDING! ALL GUI BUILDING CODE SHOULD GO ABOVE.
# START SCRIPT EXECUTION WORKFLOW
# Run an initial wireless scan when the window launches.
scan_wifi()

# Enable and display a running timestamp.
update_gui_timestamp()

# Start the Tkinter event loop.
root.mainloop()