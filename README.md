# Python Heartbeat Library

A lightweight utility for sending regular “pulses” (heartbeats) to an HTTP endpoint. These pulses confirm that your main script is running. If the main script stops, the heartbeat halts too—making it easy to detect failures. In addition to the original always-on mode, you can now schedule heartbeats to run only during configurable business hours via APScheduler.

# Installation

You can install the Python Heartbeat Library using pip:

```python
pip install pyheartbeat
```

Note: APScheduler is already included as a dependency, so business-hours scheduling works out of the box.

# Example

1. Legacy Mode (Always On)
Use this mode when you want a heartbeat thread that simply runs at a fixed interval, 24/7.
```python
======================================================================================================
from pyheartbeat import setUrl, heartbeat, killHeartbeat

# 1. Point to your monitoring endpoint
setUrl("https://your-endpoint/heartbeat")

# 2. Start the heartbeat thread
heartbeat(
    interval=600,                  # seconds between pulses
    name="scrapper-x",             # logical process name
    description="process monitor", # human-readable description
    additional_info="production",  # any extra metadata
    show_response=True,            # print HTTP status codes
    show_logs=True,                # print thread start/stop logs
    api_token="YOUR_API_TOKEN"     # optional authentication token
)

# ... your main application logic ...

# 3. Stop the heartbeat when you’re done
killHeartbeat(disable_schedule = False)
======================================================================================================
```

2. Business-Hours Mode (New)
Schedule heartbeats to start and stop automatically each day within a configurable business-hours window.
```python
======================================================================================================
from pyheartbeat import (
    setUrl, setBusinessHours, businessHeartbeat,
    killHeartbeat
)

# 1. Configure the endpoint
setUrl("https://your-endpoint/heartbeat")

# 2. Set business hours window (09:00–18:00 Mon–Fri)
setBusinessHours(
    start_hour=9,
    end_hour=18,
    days='mon-fri',
    tz='America/Sao_Paulo'
)

# 3. Schedule the heartbeat to run only during business hours
businessHeartbeat(
    interval=600,                   # send a pulse every 600 seconds
    name="scrapper-x",              # logical name of the process
    description="process monitor",  # human-readable description
    additional_info="production",   # any extra metadata
    show_response=True,             # print HTTP status codes
    show_logs=True,                 # print thread start/stop logs
    show_scheduler_logs=False,      # print scheduler logs
    api_token="YOUR_API_TOKEN"      # optional authentication token
)

# ... your main script runs here ...

# 4a. Stop only the heartbeat thread (it will automatically restart tomorrow)
killHeartbeat()

# 4b. Stop the heartbeat thread and disable automatic restart tomorrow
killHeartbeat(disable_schedule=True)
======================================================================================================
```

# License

This project is licensed under the MIT License - see the LICENSE file for details.
