# Speedtest UI Implementation Plan

## Goal

Add a user-triggered speed test in the lower-right section of the main Wi-Fi scanner window. The action should be fast, non-blocking, and visually compact: a small button, a status dot, and a tiny text readout showing upload and download throughput.

### Required behavior

- Triggered by a button in the bottom-right corner of the main window
- Results shown directly beneath the button in small black text
- A color dot indicates the current speedtest state
- Output format:
  - UL: x Mbps DL: x Mbps
- Runs without freezing the UI
- Handles idle, running, success, and failure states clearly

---

## UI placement

The main layout is controlled in [app/main.py](../app/main.py). The current window uses a vertical flow layout with the scan button and timestamp label. The speedtest control should be added as a small floating panel anchored to the lower-right area.

### Proposed layout

- Add a compact container near the bottom-right side of the root window
- Place the status dot and button side-by-side in a single row
- Put the results text directly underneath the button
- Keep the text small and black for readability
- Use `place()` or a right-aligned frame to keep it pinned to the lower-right corner instead of the normal top-down packing flow

Example structure:

- `speedtest_frame`
  - `status_dot` (canvas or label with colored circle)
  - `speedtest_button` (text: Speed Test)
  - `speedtest_result_label` (text: UL: 0.00 Mbps DL: 0.00 Mbps)

### Recommended sizing

- Button: compact, approximately 100x28 px
- Dot: 10-12 px diameter
- Result text: 8-10 pt, black, single-line
- Panel padding: small margin from the window edge

---

## State model

Use a simple explicit state machine so the UI remains predictable.

- `idle`: gray dot, no test started, no result or last known result retained
- `running`: amber/yellow dot, button disabled, label shows "Testing..." or a prior result is kept until replaced
- `success`: green dot, updated results displayed in black text
- `error`: red dot, shows prior last-known value or a message like "Test failed"

### Suggested mapping

- Gray: no current test
- Yellow: test in progress
- Green: pass/successful result
- Red: failed or timeout

---

## Trigger flow

The speed test should be launched from the button command in the UI thread, but the actual network work should run in a background thread.

### Flow

1. User clicks Speed Test button
2. UI changes to `running` state
3. Button is temporarily disabled
4. A worker thread runs the speedtest task
5. The worker collects upload and download values in Mbps
6. UI thread receives the result through `root.after(...)`
7. UI updates the result label and status dot to green or red

### Thread safety

- Do not run network calls directly on the Tk event loop
- Use `threading.Thread(..., daemon=True)` and a callback to the root window
- Always update widgets from the main thread using `root.after(0, callback, result)`

This pattern matches the existing worker approach already used in [app/main.py](../app/main.py) for Wi-Fi scanning.

---

## Backend implementation

Create a small helper service for the speed test logic, separate from the Tk code.

### Recommended file

- [services](../services) or a new module such as `services/speedtest_service.py`

### Responsibilities

- Start a speed test operation
- Run the external speedtest command or library
- Parse JSON or CLI output into upload/download values in Mbps
- Return a simple structured result
  - `download_mbps`
  - `upload_mbps`
  - `status` or `error_message`

### Preferred approach

Given this project already avoids unnecessary dependencies and favors simple tools, the cleanest option is:

- use a lightweight command-line speedtest client if available in the environment
- wrap it in a bounded subprocess helper
- parse the metrics into a stable result object

If the project decides to use a Python library instead, keep the same adapter-layer abstraction so the UI never depends on the raw library API.

---

## Result formatting

The result label should be small and black, positioned directly under the button.

### Example output

- UL: 12.45 Mbps DL: 88.30 Mbps
- UL: 0.00 Mbps DL: 0.00 Mbps when no result is available

### Format rules

- Keep the label on one line
- Use a compact font size
- Use `anchor="center"` or left alignment inside the control container
- Preserve the format exactly as requested for consistency

---

## Error handling

A speed test can fail for several reasons:

- no internet connection
- timeout waiting for server response
- external speedtest tool missing
- network interface unavailable

### Handling plan

- Set status dot to red when the command fails
- Show a clean message in the result area or leave the last known good result unchanged
- Log the exception with context, but keep the GUI user-facing message simple
- Disable retry only briefly while the worker is active

---

## Integration points

### Files to update

- [app/main.py](../app/main.py): add the control container, button, dot, and result label
- [services](../services): add the speedtest execution and parsing logic
- [tests](../tests): add unit coverage for parsing and state changes

### Main GUI flow

- Create the speedtest row in `build_layout()`
- Define a `run_speed_test()` function that starts the worker
- Define `apply_speed_test_result()` to update the dot and label on the Tk thread
- Keep the logic separate from the Wi-Fi scanner logic to avoid cross-coupling

---

## Acceptance checklist

- [ ] Speed Test button is positioned in the bottom-right area of the main window
- [ ] Result label sits directly below the button in small black text
- [ ] Status dot shows idle/running/success/error states clearly
- [ ] Speed test runs asynchronously without freezing the app
- [ ] Upload and download values are formatted as Mbps
- [ ] Failure cases show a red status and do not crash the application
- [ ] Tests cover the parsing and status transitions

---

## Suggested implementation sequence

1. Add the compact bottom-right UI container in [app/main.py](../app/main.py)
2. Create a small result model and speedtest adapter service
3. Wire the button to a background worker
4. Add the dot state transitions for idle/running/success/error
5. Format and display the UL/DL text exactly as required
6. Validate with focused tests and manual UI checks

This keeps the change small, readable, and aligned with the application’s current Tkinter structure.

