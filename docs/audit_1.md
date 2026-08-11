# Goobs WiFi Scanner: `main.py` Audit

**Review date:** 2026-08-10  
**Scope:** `main.py` and the behavior implied by the current README  
**Reviewer note:** This is a static review. The machine used for review did not have a usable Python interpreter, so runtime tests were not executed.

## Executive Summary

`main.py` is a workable prototype, but it is not yet robust enough for repeated field use. The most important fixes are:

1. Remove `shell=True` and run `netsh` with a bounded timeout.
2. Move the scan subprocess off Tkinter's main thread so the window cannot freeze.
3. Make parsing and sorting tolerate missing or malformed fields.
4. Prevent duplicate refresh timers and handle scan failures without destroying the existing view.
5. Separate scan/parsing logic from GUI construction so it can be tested.

There is no obvious direct command injection in the current constant command string. However, `shell=True` adds an unnecessary command interpreter and creates avoidable future security risk if the command ever includes user input or configuration.

## Findings

### High: Blocking process call freezes the GUI

**Evidence:** `scan_wifi()` calls `subprocess.run(...)` synchronously, and both startup and the button callback call `scan_wifi()` on Tkinter's event-loop thread.

**Impact:** A hung or slow WLAN service can make the window stop repainting and stop accepting input. The six-second refresh callback can also overlap with a manually initiated scan from the user's perspective.

**Remediation:** Run the scan worker in a bounded background thread or process. Return results to Tkinter using `root.after(...)`; only update widgets on the Tkinter thread. Disable the scan button while a scan is active, or ignore a second request. Add a timeout and a clear error state.

**Acceptance test:** Simulate a scan that sleeps longer than the UI interval. The window must repaint, the user must be able to close it, and only one scan may run at a time.

### High: Parser and sorter can crash on valid incomplete output

**Evidence:** Each BSSID starts with signal and channel values set to `"No Data"`, but sorting converts every value other than `"N/A"` with `int(x[2].strip('%'))`. A BSSID with no signal therefore raises `ValueError`.

**Impact:** A malformed, localized, permission-denied, or temporarily incomplete `netsh` response can terminate the callback and stop refreshes. The same applies to unexpected numeric formats.

**Remediation:** Represent scan records with a typed structure or dictionary and store missing values as `None`. Sort with a helper such as `signal if signal is not None else -1`; never parse display strings to sort. Validate signal range `0..100`, channel format, and MAC format before displaying.

**Acceptance test:** Feed the parser output containing a BSSID with no signal, no channel, malformed signal text, duplicate SSIDs, and an empty result. No exception is allowed; missing values remain visibly marked as unavailable.

### High: `shell=True` is unnecessary process execution risk

**Evidence:** The code passes a constant string to `subprocess.run(..., shell=True)`.

**Impact:** The current literal does not expose a user-controlled injection path, but invoking a shell expands the attack surface and makes a future change dangerous. Shell resolution also complicates quoting and executable selection.

**Remediation:** Use an argument list and `shell=False` (the default), for example `subprocess.run(["netsh", "wlan", "show", "networks", "mode=bssid"], ...)`. Prefer a trusted system executable path if deployment requirements justify it. Add `timeout`, inspect `returncode`, and capture/report `stderr` without exposing unnecessary implementation details.

**Acceptance test:** Confirm the subprocess receives separate arguments, times out predictably, and reports a nonzero exit code without crashing the GUI.

### Medium: Refresh callbacks are scheduled repeatedly

**Evidence:** Every execution of `scan_wifi()`, including manual button clicks, calls `root.after(6000, scan_wifi)`.

**Impact:** Each manual scan adds another periodic callback. Over time this causes excess subprocess launches, stale results, UI contention, and harder shutdown behavior.

**Remediation:** Schedule the periodic callback in one place. Keep the returned `after` identifier, cancel it during shutdown, and schedule the next refresh only after the current scan completes. Do not let a manual scan create a second timer.

**Acceptance test:** Click Scan Wi-Fi repeatedly, wait through several intervals, and verify one subprocess invocation per interval plus the explicitly requested manual scans.

### Medium: Scan failures are not handled

**Evidence:** `subprocess.run` exceptions, timeouts, missing executables, nonzero exit codes, and `stderr` are not handled. The result table is cleared before the new result is known to be usable.

**Impact:** Users receive a traceback or a silently empty table instead of an actionable message. A transient failure destroys the last known good data.

**Remediation:** Add a narrow exception-handling boundary around the worker. Preserve the last successful rows on failure, display a concise status message, log diagnostic details without secrets, and keep the refresh loop alive. Handle `FileNotFoundError`, `TimeoutExpired`, and nonzero return codes separately.

**Acceptance test:** Simulate each failure mode and verify the application remains open, the prior data remains intact, and the status explains the problem.

### Medium: Module import starts the application immediately

**Evidence:** Tkinter widgets are created and `root.mainloop()` runs at module scope.

**Impact:** Unit tests cannot import parsing functions without opening a window or starting scans. Packaging, reuse, and controlled shutdown are also harder.

**Remediation:** Put GUI construction and startup in `main()`, guard it with `if __name__ == "__main__":`, and keep parsing/process functions independent of Tkinter globals. Pass dependencies into functions or a small application class rather than relying on `root`, `tree`, and labels as implicit globals.

**Acceptance test:** Import the module in a test process. No window, subprocess, timer, or network operation should start.

### Medium: Global widget dependencies make state and lifecycle fragile

**Evidence:** `scan_wifi`, `exit_app`, `update_gui_timestamp`, and `export_csv` access global widgets and the global root.

**Impact:** Functions are difficult to test and can run after widgets are destroyed or before all widgets exist. This increases the chance of callback errors during shutdown.

**Remediation:** Encapsulate widget references and timer IDs in an application object, or pass the required widgets explicitly. Add a `WM_DELETE_WINDOW` handler that cancels timers, prevents new work, and waits for or safely abandons the worker before destroying the root.

### Medium: CSV export has an unreliable error path and weak data contract

**Evidence:** `export_csv()` calls `tk.messagebox.showerror` without importing `messagebox`; it catches every `Exception`. It exports only the visible table fields and does not include the reference or department fields.

**Impact:** An export failure may trigger a second `AttributeError`, hiding the original cause. Broad catching makes programming errors look like user-facing export failures. Users may assume reference metadata was saved when it was not.

**Remediation:** Import `filedialog` and `messagebox` explicitly. Catch expected I/O and encoding errors, log unexpected exceptions, and state the export schema in the UI or documentation. Decide whether reference/department values belong in the CSV, and do not export placeholder text as real user data.

**Acceptance test:** Cancel export, export an empty table, export to an invalid/unwritable path, and export SSIDs containing commas, quotes, Unicode, and line breaks.

### Medium: Placeholder text is treated as input

**Evidence:** The placeholder implementation inserts `INC000012345` and `Men's Shoes` into the actual `Entry` values. Those fields are not validated or used in scanning/export.

**Impact:** Downstream code can mistake example text for user data. The placeholder behavior is also less accessible than a native placeholder-style hint because it changes the value and color manually.

**Remediation:** Store real input separately from presentation, or use a blank value plus a visible hint. Validate length and allowed characters at the point of use, define whether the fields are required, and either persist them in exports or remove the controls until implemented.

### Low: Output parsing is locale- and format-dependent

**Evidence:** The parser matches English labels and assumes the exact `netsh` text layout. It strips each line and uses display text as the data model.

**Impact:** Windows language settings, command output changes, hidden SSIDs, or unexpected whitespace can produce missing or incorrectly associated records. `current_bssid` is not explicitly reset when a new SSID begins.

**Remediation:** Prefer a documented machine-readable API if available. Otherwise, isolate the parser, define supported locales, use explicit record state, reset state at SSID boundaries, and test representative output fixtures including hidden networks and missing fields.

### Low: External update URL and version metadata are not controlled centrally

**Evidence:** The update action opens a hardcoded GitHub URL. `APP_VERSION` is `0.1.4`, while the README reports `0.3.0`.

**Impact:** Users can be sent to stale or unintended update locations after a future change, and displayed/build versions can disagree.

**Remediation:** Use one version source, validate the repository URL during release review, and clarify that “Check for Updates” currently opens a project page rather than checking a release API. Check and report the boolean result from `webbrowser.open` if useful.

## Security Checklist

- [ ] No shell invocation for fixed commands; use argument arrays and `shell=False`.
- [ ] Subprocess timeout, return-code, and stderr handling implemented.
- [ ] No user-controlled strings reach command arguments or shell syntax.
- [ ] Export path handled through the file dialog and opened with safe, explicit encoding.
- [ ] SSID/BSSID data treated as potentially sensitive local-network information; document export/storage behavior.
- [ ] No secrets, credentials, or raw command output written to logs or error dialogs.
- [ ] User-entered reference and department values validated before persistence or export.
- [ ] Dependencies and packaged executable are built from a reviewed, reproducible environment.

## Recommended Implementation Order

1. Extract a pure `parse_netsh_output(text)` function and add fixtures/tests for incomplete output.
2. Replace shell execution with argument-based execution, timeout, return-code checks, and typed error results.
3. Add a single-flight worker and one cancellable refresh timer.
4. Move startup into `main()` and remove implicit GUI globals from scan logic.
5. Harden CSV export and define its schema, including metadata behavior.
6. Add shutdown handling, user-facing status/error reporting, and version-source cleanup.

## Minimum Regression Tests

- Parser handles normal, empty, hidden, duplicate, localized/unexpected, and incomplete output.
- Sorter handles `None` signal values without exceptions.
- Scan worker handles success, timeout, missing executable, nonzero exit code, and invalid text.
- Manual scans do not multiply scheduled refresh callbacks.
- Importing the module has no GUI or subprocess side effects.
- CSV export correctly quotes arbitrary SSIDs and handles cancellation and write failures.
- Closing the window cancels timers and leaves no worker callback attempting to update destroyed widgets.

## Validation Constraints

The available `python` command resolved to the Windows Store execution alias, not an installed interpreter. Run the project's documented virtual-environment setup, then execute at minimum:

```powershell
python -m py_compile main.py
python -m unittest discover
```

Add a test runner and lint/type-check commands to the project once the extracted components exist. Avoid declaring the audit complete based only on a successful compile; the highest-risk defects are runtime and lifecycle defects.
