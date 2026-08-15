#!/usr/bin/env python3
"""Tkinter application entry point for Goobs WiFi Scanner."""

from __future__ import annotations

import json
import threading
import time
import urllib.request
import webbrowser

import tkinter as tk
from tkinter import messagebox, ttk

from models.network import NetworkRecord
from services.speedtest import run_speedtest
from services.wifi_scan import scan_wifi_networks

APP_VERSION = "0.5.3"
REPO_LINK = "https://github.com/GoobyFRS/Goobs-WiFi-Scanner"
WIKI_LINK = "https://github.com/GoobyFRS/Goobs-WiFi-Scanner/wiki"
ISSUES_LINK = "https://github.com/GoobyFRS/Goobs-WiFi-Scanner/issues"

root: tk.Tk | None = None
tree: ttk.Treeview | None = None
timestamp_label: tk.Label | None = None
public_ip_label: tk.Label | None = None
speedtest_button: tk.Button | None = None
speedtest_result_label: tk.Label | None = None
speedtest_status_dot: tk.Label | None = None
PUBLIC_IP_URL = "https://api.ipify.org?format=json"


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
        The numeric signal percentage as an integer, or -1 when no valid value
        exists.
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
    if tree is None:
        return

    tree.delete(*tree.get_children())

    sorted_networks = sorted(networks, key=signal_sort_key, reverse=True)
    for net in sorted_networks:
        tag = signal_tag_for_percentage(
            getattr(net, "signal_strength", None)
            if not isinstance(net, (list, tuple))
            else net[2]
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

    setattr(root, "_scan_in_progress", False)
    root.after(6000, scan_wifi)


def _scan_worker():
    """Run a Wi-Fi scan in a background thread and push results to the UI.

    Raises:
        Exception: Any scan or parsing failure is surfaced to the UI as an
        error state.
    """
    try:
        networks = scan_wifi_networks()
        if root is not None:
            root.after(0, _apply_scan_results, networks)
    except Exception as exc:
        if root is not None:
            root.after(0, _apply_scan_results, [])
        if timestamp_label is not None:
            timestamp_label.config(text=f"Scan Error: {exc}")
        if root is not None:
            setattr(root, "_scan_in_progress", False)


def scan_wifi():
    """Start a Wi-Fi scan on a worker thread when no scan is already running.

    Returns:
        None: This function triggers background work and exits immediately.
    """
    if root is not None and getattr(root, "_scan_in_progress", False):
        return

    if root is not None:
        setattr(root, "_scan_in_progress", True)
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


def parse_public_ip_response(response_text: str) -> str:
    """Parse the ipify JSON response and return the public IPv4 address.

    Args:
        response_text: Raw JSON payload returned by the ipify API.

    Returns:
        The public IP string contained in the response.

    Raises:
        ValueError: If the API payload does not contain a valid IP address.
    """
    payload = json.loads(response_text)
    ip_address = payload.get("ip")

    if not isinstance(ip_address, str) or not ip_address.strip():
        raise ValueError("Public IP response missing 'ip' value.")

    return ip_address.strip()


def fetch_public_ip():
    """Fetch the current public IP from the ipify API.

    Returns:
        None: The GUI footer label is updated when the request succeeds or
        fails.
    """
    try:
        request = urllib.request.Request(
            PUBLIC_IP_URL,
            headers={"User-Agent": "Goobs-WiFi-Scanner/0.5.3"},
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = response.read().decode("utf-8")

        public_ip = parse_public_ip_response(payload)
        if public_ip_label is not None:
            public_ip_label.config(text=f"Public IP: {public_ip}")
    except Exception:
        if public_ip_label is not None:
            public_ip_label.config(text="Public IP: unavailable")
    finally:
        if root is not None:
            root.after(300000, fetch_public_ip)


def update_speedtest_state(color: str, text: str, *, enabled: bool = True):
    """Update the speedtest status dot, label, and button state.

    Args:
        color: Hex or named color string for the status dot.
        text: The result text to display below the button.
        enabled: Whether the button should be clickable.
    """
    if speedtest_status_dot is not None:
        speedtest_status_dot.config(bg=color)

    if speedtest_result_label is not None:
        speedtest_result_label.config(text=text)

    if speedtest_button is not None:
        speedtest_button.config(state=tk.NORMAL if enabled else tk.DISABLED)


def _run_speedtest_worker():
    """Execute the speedtest in a background thread."""
    try:
        result = run_speedtest()
        if root is not None:
            root.after(
                0,
                update_speedtest_state,
                "#27ae60",
                (
                    "UL: "
                    f"{result.upload_mbps:.2f} Mbps "
                    f"DL: {result.download_mbps:.2f} Mbps"
                ),
            )
    except Exception as exc:  # pragma: no cover - UI-handling path
        error_message = f"Speedtest Error: {exc}"
        if root is not None:
            root.after(
                0,
                lambda: update_speedtest_state(
                    "#c0392b",
                    "UL: 0.00 Mbps DL: 0.00 Mbps",
                    enabled=True,
                ),
            )
            root.after(
                0,
                lambda: timestamp_label.config(text=error_message)
                if timestamp_label is not None
                else None,
            )


def run_speedtest_ui():
    """Trigger a speedtest run from the GUI without blocking the app."""
    if root is not None and getattr(root, "_speedtest_in_progress", False):
        return

    if root is not None:
        setattr(root, "_speedtest_in_progress", True)
    update_speedtest_state("#f39c12", "Testing...", enabled=False)
    worker = threading.Thread(target=_run_speedtest_worker, daemon=True)
    worker.start()

    def complete_worker():
        if root is not None:
            setattr(root, "_speedtest_in_progress", False)
        if speedtest_button is not None:
            speedtest_button.config(state=tk.NORMAL)

    if root is not None:
        root.after(500, complete_worker)


def update_gui_timestamp():
    """Refresh the timestamp label in the UI once per second.

    Returns:
        None: The label is updated on the Tk event loop.
    """
    if timestamp_label is not None:
        current_time = time.strftime("%H:%M:%S")
        timestamp_label.config(text=f"Last Updated: {current_time}")
    if root is not None:
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
        None: The user chooses a destination file and the CSV is written
            to disk.

    Raises:
        Exception: Any file or GUI-related failure is shown to the user via
            a message box.
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
            writer.writerow(
                ["SSID", "MAC Address", "Signal Strength", "Channel"],
            )
            for row in rows:
                writer.writerow(row)
    except Exception as error:  # pragma: no cover - GUI-backed path
        messagebox.showerror(
            "Export Error",
            f"Failed to export CSV: {error}",
        )


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
    help_menu.add_command(
        label="Check for Updates",
        command=show_check_4_updates,
    )
    help_menu.add_command(label="Report an Issues", command=open_issues)
    help_menu.add_command(label="Open Wiki", command=open_wiki)
    menu_bar.add_cascade(label="Help", menu=help_menu)

    root_window.configure(menu=menu_bar)
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

    tk.Label(
        entry_frame,
        text="Reference:",
    ).grid(row=0, column=0, padx=(0, 5), sticky="w")
    reference_entry = tk.Entry(entry_frame, width=20)
    reference_entry.grid(row=0, column=1, padx=(0, 20))
    tkt_reference_placeholder(reference_entry, "INC000012345")

    tk.Label(
        entry_frame,
        text="Department:",
    ).grid(row=0, column=2, padx=(0, 5), sticky="w")
    department_entry = tk.Entry(entry_frame, width=20)
    department_entry.grid(row=0, column=3)
    tkt_reference_placeholder(department_entry, "Men's Shoes")

    scan_button = tk.Button(root_window, text="Scan Wi-Fi", command=scan_wifi)
    scan_button.pack(pady=10)

    speedtest_frame = tk.Frame(root_window)
    speedtest_frame.pack(anchor="se", padx=10, pady=(0, 10))

    status_dot = tk.Label(
        speedtest_frame,
        text="",
        width=2,
        height=1,
        bg="#7f8c8d",
        relief="solid",
    )
    status_dot.pack(side="left", padx=(0, 6))

    speedtest_button_widget = tk.Button(
        speedtest_frame,
        text="Speed Test",
        command=run_speedtest_ui,
    )
    speedtest_button_widget.pack(side="top")

    speedtest_result = tk.Label(
        speedtest_frame,
        text="UL: 0.00 Mbps DL: 0.00 Mbps",
        font=("TkDefaultFont", 8),
        fg="black",
    )
    speedtest_result.pack(side="top", pady=(4, 0))

    footer_frame = tk.Frame(root_window)
    footer_frame.pack(side="bottom", fill="x", padx=10, pady=(0, 5))

    timestamp_label_widget = tk.Label(footer_frame, text="", anchor="w")
    timestamp_label_widget.pack(side="left", fill="x", expand=True)

    public_ip_label_widget = tk.Label(
        footer_frame,
        text="Public IP: unavailable",
        anchor="e",
    )
    public_ip_label_widget.pack(side="right", padx=(10, 0))

    return (
        tree_widget,
        timestamp_label_widget,
        public_ip_label_widget,
        speedtest_button_widget,
        speedtest_result,
        status_dot,
    )


def main():
    """Create and run the Tkinter application.

    Returns:
        None: The application enters the Tk main loop and runs until exit.
    """
    global root, tree, timestamp_label, public_ip_label
    global speedtest_button, speedtest_result_label, speedtest_status_dot

    root = tk.Tk()
    root.title(f"Goobs WiFi Scanner - {APP_VERSION}")
    root.geometry("720x480")

    build_menu_bar(root)
    (
        tree,
        timestamp_label,
        public_ip_label,
        speedtest_button,
        speedtest_result_label,
        speedtest_status_dot,
    ) = build_layout(root)

    update_speedtest_state("#7f8c8d", "UL: 0.00 Mbps DL: 0.00 Mbps")
    scan_wifi()
    update_gui_timestamp()
    fetch_public_ip()
    root.mainloop()


if __name__ == "__main__":
    main()
