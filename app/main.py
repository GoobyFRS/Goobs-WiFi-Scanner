#!/usr/bin/env python3
"""Tkinter application entry point for Goobs WiFi Scanner."""

from __future__ import annotations

import threading
import time
import webbrowser

import tkinter as tk
from tkinter import ttk

from models.network import NetworkRecord
from services.wifi_scan import scan_wifi_networks

APP_VERSION = "0.5.1"
REPO_LINK = "https://github.com/GoobyFRS/Goobs-WiFi-Scanner"
WIKI_LINK = "https://github.com/GoobyFRS/Goobs-WiFi-Scanner/wiki"
ISSUES_LINK = "https://github.com/GoobyFRS/Goobs-WiFi-Scanner/issues"

root: tk.Tk
tree: ttk.Treeview
timestamp_label: tk.Label


def _open_link(url: str):
    """Open a GitHub URL in the user's default browser.

    Args:
        url: The URL to open.

    Returns:
        None: The browser launch is delegated to the OS.
    """
    webbrowser.open(url)

def signal_tag_for_percentage(signal_value):
    """Map a signal strength value to a Treeview color tag.
    Args:
        signal_value: Signal value as a numeric percentage string or integer.
    Returns:
        The tag name for the signal quality, or None if the value is invalid.
    """
    if signal_value is None:
        return None

    try:
        percentage = int(str(signal_value).replace("%", "").strip())
    except (TypeError, ValueError):
        return None

    if percentage >= 80:
        return "sig-strong"
    if percentage >= 65:
        return "sig-good"
    if percentage >= 50:
        return "sig-fair"
    if percentage >= 0:
        return "sig-weak"
    return None


def signal_sort_key(network):
    """Return a sortable signal value for a network record.
    Args:
        network: A network record or tuple containing a signal strength field.
    Returns:
        The numeric signal percentage as an integer, or -1 when no valid value exists.
    """
    signal_value = getattr(network, "signal_strength", None)
    if signal_value is None and isinstance(network, (list, tuple)):
        signal_value = network[2]
    if signal_value is None:
        return -1

    try:
        return int(str(signal_value).replace("%", "").strip())
    except (TypeError, ValueError):
        return -1


def _apply_scan_results(networks):
    """Render scan results in the main Treeview widget.
    Args:
        networks: A list of network records or row tuples returned from a scan.
    """
    tree.delete(*tree.get_children())

    sorted_networks = sorted(networks, key=signal_sort_key, reverse=True)
    for net in sorted_networks:
        tag = signal_tag_for_percentage(
            getattr(net, "signal_strength", None) if not isinstance(net, (list, tuple)) else net[2]
        )

        values = (
            (net.ssid, net.mac_address, net.signal_strength, net.channel)
            if isinstance(net, NetworkRecord)
            else net
        )

        if tag:
            tree.insert("", tk.END, values=values, tags=(tag,))
        else:
            tree.insert("", tk.END, values=values)

    root._scan_in_progress = False
    root.after(6000, scan_wifi)

def _scan_worker():
    """Run a Wi-Fi scan in a background thread and push results to the UI.
    Raises:
        Exception: Any scan or parsing failure is surfaced to the UI as an error state.
    """
    try:
        networks = scan_wifi_networks()
        root.after(0, _apply_scan_results, networks)
    except Exception as exc:
        root.after(0, _apply_scan_results, [])
        timestamp_label.config(text=f"Scan Error: {exc}")
        root._scan_in_progress = False


def scan_wifi():
    """Start a Wi-Fi scan on a worker thread when no scan is already running.

    Returns:
        None: This function triggers background work and exits immediately.
    """
    if getattr(root, "_scan_in_progress", False):
        return

    root._scan_in_progress = True
    thread = threading.Thread(target=_scan_worker, daemon=True)
    thread.start()


def show_check_4_updates():
    """Open the project GitHub repository in the default browser.
    Returns:
        None: This function delegates to the system browser.
    """
    _open_link(REPO_LINK)


def open_wiki():
    """Open the project wiki in the default browser.
    Returns:
        None: This function delegates to the system browser.
    """
    _open_link(WIKI_LINK)


def open_issues():
    """Open the GitHub issues page in the default browser.
    Returns:
        None: This function delegates to the system browser.
    """
    _open_link(ISSUES_LINK)


def exit_app():
    """Quit the application cleanly.
    Returns:
        None: The Tk root window is closed.
    """
    root.quit()


def update_gui_timestamp():
    """Refresh the timestamp label in the UI once per second.
    Returns:
        None: The label is updated on the Tk event loop.
    """
    current_time = time.strftime("%H:%M:%S")
    timestamp_label.config(text=f"Last Updated: {current_time}")
    root.after(1000, update_gui_timestamp)


def tkt_reference_placeholder(entry, placeholder):
    """Attach placeholder behavior to a text entry widget.
    Args:
        entry: The Tkinter entry widget to decorate.
        placeholder: Placeholder text shown when the field is empty.
    Returns:
        None: The widget is configured in-place.
    """

    def on_focus_in(event):
        """Clear the placeholder text when the field receives focus."""
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(fg="black")

    def on_focus_out(event):
        """Restore the placeholder text when the field is empty on blur."""
        if not entry.get():
            entry.insert(0, placeholder)
            entry.config(fg="gray")

    entry.insert(0, placeholder)
    entry.config(fg="gray")
    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)


def export_csv():
    """Export the current Treeview rows to a CSV file.
    Returns:
        None: The user chooses a destination file and the CSV is written to disk.
    Raises:
        Exception: Any file or GUI-related failure is shown to the user via a message box.
    """
    ts = time.strftime("%Y%m%d_%H%M%S")
    default_name = f"wireless_scan_{ts}.csv"
    try:
        from tkinter import filedialog

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV files", "*.csv"), ("All files", "*")],
        )
        if not path:
            return

        rows = []
        for iid in tree.get_children():
            values = tree.item(iid, "values")
            rows.append(values)

        import csv

        with open(path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["SSID", "MAC Address", "Signal Strength", "Channel"])
            for row in rows:
                writer.writerow(row)
    except Exception as error:  # pragma: no cover - GUI-backed path
        tk.messagebox.showerror("Export Error", f"Failed to export CSV: {error}")


def build_menu_bar(root_window: tk.Misc) -> tk.Menu:
    """Build the application menu bar with consistent menu structure.

    Args:
        root_window: The root Tk window used to attach the menu bar.

    Returns:
        A configured Tk menu bar with file and help menus.
    """
    menu_bar = tk.Menu(root_window)

    file_menu = tk.Menu(menu_bar, tearoff=0)
    file_menu.add_command(label="Export CSV", command=export_csv)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=exit_app)
    menu_bar.add_cascade(label="File", menu=file_menu)

    help_menu = tk.Menu(menu_bar, tearoff=0)
    help_menu.add_command(label="Check for Updates", command=show_check_4_updates)
    help_menu.add_command(label="Wiki", command=open_wiki)
    help_menu.add_command(label="Issues", command=open_issues)
    menu_bar.add_cascade(label="Help", menu=help_menu)

    root_window.config(menu=menu_bar)
    return menu_bar


def build_layout(root_window: tk.Tk):
    """Create the main application layout with a consistent widget structure.

    Args:
        root_window: The main Tk window to populate.

    Returns:
        None: The widgets are created and packed in place.
    """
    columns = ("SSID", "MAC Address", "Signal Strength", "Channel")
    tree_frame = tk.Frame(root_window)
    tree_frame.pack(expand=True, fill="both")

    tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
    tree_scroll.pack(side="right", fill="y")

    tree_widget = ttk.Treeview(
        tree_frame,
        columns=columns,
        show="headings",
        yscrollcommand=tree_scroll.set,
    )
    tree_scroll.config(command=tree_widget.yview)

    for column in columns:
        tree_widget.heading(column, text=column)
        tree_widget.column(column, width=140)

    tree_widget.tag_configure("sig-strong", background="#2ecc71")
    tree_widget.tag_configure("sig-good", background="#a9dfbf")
    tree_widget.tag_configure("sig-fair", background="#f9e79f")
    tree_widget.tag_configure("sig-weak", background="#f5b7b1")

    tree_widget.pack(expand=True, fill="both")

    entry_frame = tk.Frame(root_window)
    entry_frame.pack(fill="x", padx=10, pady=5)

    tk.Label(entry_frame, text="Reference:").grid(row=0, column=0, padx=(0, 5), sticky="w")
    reference_entry = tk.Entry(entry_frame, width=20)
    reference_entry.grid(row=0, column=1, padx=(0, 20))
    tkt_reference_placeholder(reference_entry, "INC000012345")

    tk.Label(entry_frame, text="Department:").grid(row=0, column=2, padx=(0, 5), sticky="w")
    department_entry = tk.Entry(entry_frame, width=20)
    department_entry.grid(row=0, column=3)
    tkt_reference_placeholder(department_entry, "Men's Shoes")

    scan_button = tk.Button(root_window, text="Scan Wi-Fi", command=scan_wifi)
    scan_button.pack(pady=10)

    timestamp_label_widget = tk.Label(root_window, text="", anchor="w", padx=10)
    timestamp_label_widget.pack(side="bottom", fill="x")

    return tree_widget, timestamp_label_widget


def main():
    """Create and run the Tkinter application.

    Returns:
        None: The application enters the Tk main loop and runs until exit.
    """
    global root, tree, timestamp_label

    root = tk.Tk()
    root.title(f"Goobs WiFi Scanner - {APP_VERSION}")
    root.geometry("720x480")

    build_menu_bar(root)
    tree, timestamp_label = build_layout(root)

    scan_wifi()
    update_gui_timestamp()
    root.mainloop()

if __name__ == "__main__":
    main()
