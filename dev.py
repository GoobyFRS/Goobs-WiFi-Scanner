#!/usr/bin/env python3
"""
Goobs WiFi Scanner - A lightweight network diagnostics tool for IT professionals
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import re
import webbrowser
import time
import csv
from typing import List, Tuple, Optional
from dataclasses import dataclass

APP_VERSION = "0.2.0"
SCAN_INTERVAL_MS = 6000
TIMESTAMP_UPDATE_MS = 1000
GITHUB_URL = "https://github.com/GoobyFRS/Goobs-WiFi-Scanner"


@dataclass
class WiFiNetwork:
    """Represents a WiFi network with its properties"""
    ssid: str
    mac_address: str
    signal_strength: str
    channel: str

    def to_tuple(self) -> Tuple[str, str, str, str]:
        """Convert to tuple for treeview insertion"""
        return (self.ssid, self.mac_address, self.signal_strength, self.channel)

    @property
    def signal_percentage(self) -> int:
        """Extract numeric signal percentage for sorting"""
        try:
            return int(self.signal_strength.strip('%'))
        except (ValueError, AttributeError):
            return -1


class WiFiScanner:
    """Handles WiFi scanning operations"""
    
    @staticmethod
    def scan() -> List[WiFiNetwork]:
        """
        Scan for available WiFi networks using Windows netsh command
        
        Returns:
            List of WiFiNetwork objects
        """
        try:
            command = ["netsh wlan show networks mode=bssid"]
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            
            if result.returncode != 0:
                # Show actual error output for debugging
                error_msg = f"Command failed with return code {result.returncode}\n"
                if result.stderr:
                    error_msg += f"Error: {result.stderr}\n"
                if result.stdout:
                    error_msg += f"Output: {result.stdout[:200]}"
                raise RuntimeError(error_msg)
            
            return WiFiScanner._parse_output(result.stdout)
        
        except subprocess.TimeoutExpired:
            messagebox.showerror("Scan Error", "WiFi scan timed out")
            return []
        except FileNotFoundError:
            messagebox.showerror("Scan Error", "Could not find netsh command. This tool requires Windows.")
            return []
        except Exception as e:
            messagebox.showerror("Scan Error", f"Failed to scan WiFi networks:\n{str(e)}")
            return []
    
    @staticmethod
    def _parse_output(output: str) -> List[WiFiNetwork]:
        """Parse netsh command output into WiFiNetwork objects"""
        networks = []
        current_ssid = None
        current_bssid = None
        current_signal = "N/A"
        current_channel = "N/A"

        for line in output.split("\n"):
            line = line.strip()

            # Match SSID
            ssid_match = re.match(r"SSID \d+ : (.+)", line)
            if ssid_match:
                current_ssid = ssid_match.group(1).strip() or "Hidden SSID"
                continue

            # Match BSSID (MAC address)
            mac_match = re.match(r"BSSID \d+ *: ([0-9A-Fa-f:-]+)", line)
            if mac_match and current_ssid:
                # Save previous BSSID if exists
                if current_bssid:
                    networks.append(WiFiNetwork(
                        ssid=current_ssid,
                        mac_address=current_bssid,
                        signal_strength=current_signal,
                        channel=current_channel
                    ))
                
                current_bssid = mac_match.group(1)
                current_signal = "N/A"
                current_channel = "N/A"
                continue

            # Match signal strength
            signal_match = re.match(r"Signal\s*:\s*(\d+)%", line)
            if signal_match and current_bssid:
                current_signal = f"{signal_match.group(1)}%"
                continue

            # Match channel
            channel_match = re.match(r"Channel\s*:\s*(\d+)", line)
            if channel_match and current_bssid:
                current_channel = channel_match.group(1)
                continue

        # Don't forget the last network
        if current_bssid and current_ssid:
            networks.append(WiFiNetwork(
                ssid=current_ssid,
                mac_address=current_bssid,
                signal_strength=current_signal,
                channel=current_channel
            ))

        return networks


class PlaceholderEntry(tk.Entry):
    """Entry widget with placeholder text support"""
    
    def __init__(self, parent, placeholder: str = "", **kwargs):
        super().__init__(parent, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = "gray"
        self.default_color = self["fg"]
        
        self._showing_placeholder = False
        self._show_placeholder()
        
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
    
    def _show_placeholder(self):
        """Display placeholder text"""
        if not self.get():
            self.insert(0, self.placeholder)
            self.config(fg=self.placeholder_color)
            self._showing_placeholder = True
    
    def _on_focus_in(self, event):
        """Remove placeholder on focus"""
        if self._showing_placeholder:
            self.delete(0, tk.END)
            self.config(fg=self.default_color)
            self._showing_placeholder = False
    
    def _on_focus_out(self, event):
        """Restore placeholder if empty"""
        if not self.get():
            self._show_placeholder()
    
    def get_value(self) -> str:
        """Get actual value (empty string if showing placeholder)"""
        return "" if self._showing_placeholder else self.get()


class WiFiScannerApp:
    """Main application class"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"Goobs WiFi Scanner v{APP_VERSION}")
        self.root.geometry("800x500")
        
        # Initialize variables
        self.scan_job_id: Optional[str] = None
        self.timestamp_job_id: Optional[str] = None
        
        # Build UI
        self._create_menu_bar()
        self._create_main_table()
        self._create_reference_fields()
        self._create_control_buttons()
        self._create_status_bar()
        
        # Start operations
        self.scan_wifi()
        self._update_timestamp()
    
    def _create_menu_bar(self):
        """Create application menu bar"""
        menu_bar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Export CSV", command=self.export_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_app)
        menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Help menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="Check for Updates", command=self.check_updates)
        help_menu.add_command(label="About", command=self.show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menu_bar)
    
    def _create_main_table(self):
        """Create the main network list table"""
        # Frame for table and scrollbar
        tree_frame = tk.Frame(self.root)
        tree_frame.pack(expand=True, fill="both", padx=10, pady=(10, 0))
        
        # Scrollbar
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
        tree_scroll.pack(side="right", fill="y")
        
        # Treeview
        columns = ("SSID", "MAC Address", "Signal Strength", "Channel")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=tree_scroll.set
        )
        tree_scroll.config(command=self.tree.yview)
        
        # Configure columns
        column_widths = {"SSID": 200, "MAC Address": 150, "Signal Strength": 120, "Channel": 80}
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths.get(col, 100))
        
        self.tree.pack(expand=True, fill="both")
    
    def _create_reference_fields(self):
        """Create reference data entry fields"""
        entry_frame = tk.Frame(self.root)
        entry_frame.pack(fill="x", padx=10, pady=10)
        
        # Incident Reference
        tk.Label(entry_frame, text="Reference:").grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.reference_entry = PlaceholderEntry(entry_frame, placeholder="INC000012345", width=20)
        self.reference_entry.grid(row=0, column=1, padx=(0, 20))
        
        # Department
        tk.Label(entry_frame, text="Department:").grid(row=0, column=2, padx=(0, 5), sticky="w")
        self.department_entry = PlaceholderEntry(entry_frame, placeholder="Men's Shoes", width=20)
        self.department_entry.grid(row=0, column=3)
    
    def _create_control_buttons(self):
        """Create control buttons"""
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.scan_button = tk.Button(
            button_frame,
            text="Scan WiFi",
            command=self.scan_wifi,
            width=15
        )
        self.scan_button.pack()
    
    def _create_status_bar(self):
        """Create status bar with timestamp"""
        self.timestamp_label = tk.Label(
            self.root,
            text="Ready",
            anchor="w",
            padx=10,
            relief=tk.SUNKEN
        )
        self.timestamp_label.pack(side="bottom", fill="x")
    
    def scan_wifi(self):
        """Perform WiFi scan and update display"""
        # Cancel existing scheduled scan
        if self.scan_job_id:
            self.root.after_cancel(self.scan_job_id)
        
        # Perform scan
        networks = WiFiScanner.scan()
        
        # Sort by signal strength (strongest first)
        networks.sort(key=lambda n: n.signal_percentage, reverse=True)
        
        # Update tree
        self.tree.delete(*self.tree.get_children())
        for network in networks:
            self.tree.insert("", tk.END, values=network.to_tuple())
        
        # Schedule next scan
        self.scan_job_id = self.root.after(SCAN_INTERVAL_MS, self.scan_wifi)
    
    def _update_timestamp(self):
        """Update timestamp display"""
        current_time = time.strftime("%H:%M:%S")
        self.timestamp_label.config(text=f"Last Updated: {current_time}")
        self.timestamp_job_id = self.root.after(TIMESTAMP_UPDATE_MS, self._update_timestamp)
    
    def export_csv(self):
        """Export current scan results to CSV"""
        # Generate default filename
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        default_name = f"wireless_scan_{timestamp}.csv"
        
        # Get save location
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            # Collect data from treeview
            rows = []
            for iid in self.tree.get_children():
                rows.append(self.tree.item(iid, "values"))
            
            # Write CSV
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                
                # Write headers
                writer.writerow(["SSID", "MAC Address", "Signal Strength", "Channel"])
                
                # Write reference data if provided
                ref = self.reference_entry.get_value()
                dept = self.department_entry.get_value()
                if ref or dept:
                    writer.writerow([])
                    writer.writerow(["Reference:", ref])
                    writer.writerow(["Department:", dept])
                    writer.writerow([])
                
                # Write network data
                for row in rows:
                    writer.writerow(row)
            
            messagebox.showinfo("Export Successful", f"Data exported to:\n{filepath}")
        
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export CSV:\n{str(e)}")
    
    def check_updates(self):
        """Open GitHub repository to check for updates"""
        webbrowser.open(GITHUB_URL)
    
    def show_about(self):
        """Show about dialog"""
        about_text = f"""Goobs WiFi Scanner v{APP_VERSION}

A lightweight network diagnostics tool for IT professionals.

Scan WiFi networks and export results for troubleshooting."""
        messagebox.showinfo("About", about_text)
    
    def exit_app(self):
        """Clean exit"""
        # Cancel scheduled jobs
        if self.scan_job_id:
            self.root.after_cancel(self.scan_job_id)
        if self.timestamp_job_id:
            self.root.after_cancel(self.timestamp_job_id)
        
        self.root.quit()


def main():
    """Application entry point"""
    root = tk.Tk()
    app = WiFiScannerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()