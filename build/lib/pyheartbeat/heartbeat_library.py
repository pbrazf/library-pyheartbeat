import requests
import time
import threading
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

# -------------------------------
# Core Heartbeat Functionality
# -------------------------------

# Pulse control globals
url = ""
variable_parameter = True
pulse_thread = None

# 1. Configure pulse URL
def setUrl(url_):
    '''
    Define the endpoint for sending heartbeats.
    '''
    
    global url
    url = url_

# 2. Send a single pulse
def sendPulse(name, description, additional_info, show_response=False, api_token=None):
    '''
    Send a heartbeat pulse to the configured URL.
    '''
    
    if not url: raise RuntimeError("URL not set")

    payload = {
        "processName": name,
        "processDescription": description,
        "additionalData": additional_info
    }
    headers = {'Content-Type': 'application/json'}
    if api_token:
        headers['Authorization'] = f"Bearer {api_token}"
    try:
        response = requests.post(url, json=payload, headers=headers)
        if show_response:
            print(f">>> Heartbeat response: {response.status_code}")
    except Exception as e:
        print('*** Error sending pulse! *** >', e)

# 3. Thread loop sending pulses at fixed intervals
def pulse(interval, name, description, additional_info, show_response, show_logs, api_token):
    '''
    Background thread that sends pulses at the specified interval.
    '''
    
    if show_logs:
        print('>>> Heartbeat thread has started. <<<')
    while variable_parameter:
        sendPulse(name, description, additional_info, show_response, api_token)
        # wait interval seconds, waking up each second to check kill flag
        for _ in range(interval):
            if not variable_parameter:
                break
            time.sleep(1)

# 4. Start heartbeat (legacy, no business hours enforcement)
def heartbeat(
    interval=600,
    name='',
    description='',
    additional_info='',
    show_response=False,
    show_logs=False,
    api_token=None
):
    '''
    Begin sending pulses on a background thread at the specified interval.
    '''
    
    global variable_parameter, pulse_thread
    variable_parameter = True
    # avoid overlapping thread
    if pulse_thread is not None:
        pulse_thread.join(timeout=1.0)
    # start new thread
    pulse_thread = threading.Thread(
        target=pulse,
        args=(interval, name, description, additional_info, show_response, show_logs, api_token)
    )
    pulse_thread.start()

# 5. Kill heartbeat thread (with optional scheduler shutdown)
def killHeartbeat(disable_schedule: bool = True):
    '''
    Stop the heartbeat thread. If disable_schedule=True, also shutdown business-hour scheduler.
    '''
    
    global variable_parameter, pulse_thread, _scheduler
    variable_parameter = False
    time.sleep(1)
    if pulse_thread and pulse_thread.is_alive():
        print('!!! Heartbeat thread is still running. !!!')
    else:
        print('>>> Heartbeat thread has ended. <<<')
    # optionally shutdown scheduler
    if disable_schedule and _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        print('>>> Scheduler also shut down; no auto-restart. <<<')

# -------------------------------
# Scheduler for Business Hours
# -------------------------------

# Internal scheduler and config defaults
_scheduler = None
_start_hour = 9
_end_hour = 18
_days = 'mon,tue,wed,thu,fri'
_tz = 'America/Sao_Paulo'

# Helper ---------------------------
def _next_business_day(dt: datetime):
    '''
    Find the next business day after a given datetime.
    '''
    
    nxt = dt + timedelta(days=1)
    # loop until find a business day
    while nxt.strftime('%a').lower()[:3] not in _days:
        nxt += timedelta(days=1)
    return nxt
# ----------------------------------

# 6. Runtime business hours config
def setBusinessHours(start_hour: int, end_hour: int, days: str | list[str] = 'mon,tue,wed,thu,fri', tz: str = 'America/Sao_Paulo'):
    '''
    Configure business hours window and days (as CSV string or list of abbreviations).
    '''
    
    global _start_hour, _end_hour, _days, _tz
    _start_hour = start_hour
    _end_hour   = end_hour
    # normalize days into a comma-separated string
    if isinstance(days, list):
        _days = ','.join(days)
    else:
        _days = days
    _tz = tz

# 7. Start heartbeat automatically on business hours
def businessHeartbeat(
    interval=600,
    name='',
    description='',
    additional_info='',
    show_response=False,
    show_logs=False,
    show_scheduler_logs=False,
    api_token=None
):
    '''
    - If now ∈ business hours: start heartbeat immediately + stop today at end_hour.
    - Otherwise: schedule a one-shot start at next business-day start_hour.
    In both cases, schedule the daily cron for future days.
    '''

    global _scheduler

    now = datetime.now()
    allowed_days = _days.split(',')
    weekday = now.strftime('%a').lower()[:3]
    start_today = now.replace(hour=_start_hour, minute=0, second=0, microsecond=0)
    end_today   = now.replace(hour=_end_hour,   minute=0, second=0, microsecond=0)

    # prepare scheduler
    if _scheduler:
        _scheduler.remove_all_jobs()
        if show_scheduler_logs:
            print("%%% [_scheduler] jobs reset! %%%")
    else:
        _scheduler = BackgroundScheduler(timezone=_tz)
        if show_scheduler_logs:
            print(f"%%% [_scheduler] instanciado com timezone={_tz}! %%%")

    if weekday in allowed_days and start_today <= now < end_today:
        # 1) Dentro de expediente → start agora + stop hoje
        if show_scheduler_logs:
            print(f"%%% Agendando pulseThread IMEDIATO e STOP às {end_today}! %%%")
        heartbeat(interval, name, description, additional_info,
                  show_response, show_logs, api_token)
        run_stop = end_today
        # o primeiro ciclo cron (start) só deve ocorrer amanhã
        first_cycle = _next_business_day(now).replace(
            hour=_start_hour, minute=0, second=0, microsecond=0
        )
    else:
        # 2) Fora de expediente → não start agora. Agenda um start único.
        if weekday in allowed_days and now < start_today:
            run_start = start_today
        else:
            nxt = _next_business_day(now)
            run_start = nxt.replace(hour=_start_hour, minute=0,
                                    second=0, microsecond=0)

        if show_scheduler_logs:
            print(f"%%% Fora do expediente → agendando START único em {run_start}! %%%")
        _scheduler.add_job(
            lambda: businessHeartbeat(
                interval, name, description, additional_info,
                show_response, show_logs, show_scheduler_logs, api_token
            ),
            'date',
            run_date=run_start,
            id='bh_start_once'
        )

        # como não startou hoje, o primeiro stop virá no mesmo day-of-week do run_start
        run_stop = run_start.replace(hour=_end_hour, minute=0, second=0, microsecond=0)
        # e o cron de ciclos futuros começa no dia seguinte ao run_start
        first_cycle = _next_business_day(run_start).replace(
            hour=_start_hour, minute=0, second=0, microsecond=0
        )

    # schedule one-shot stop at run_stop
    if show_scheduler_logs:
        print(f"%%% Agendando STOP único em {run_stop}! %%%")
    _scheduler.add_job(
        lambda: killHeartbeat(disable_schedule=False),
        'date',
        run_date=run_stop,
        id='bh_stop_once'
    )

    # schedule daily cron cycles after first_cycle
    if show_scheduler_logs:
        print(f"%%% Agendando CRON START diário às {first_cycle} (dias {_days})! %%%")
    _scheduler.add_job(
        lambda: businessHeartbeat(
            interval, name, description, additional_info,
            show_response, show_logs, show_scheduler_logs, api_token
        ),
        'cron',
        day_of_week=_days,
        hour=_start_hour, minute=0,
        start_date=first_cycle,
        id='bh_start_daily'
    )

    if show_scheduler_logs:
        print(f"%%% Agendando CRON STOP diário às {first_cycle.replace(hour=_end_hour)} (dias {_days})! %%%")
    _scheduler.add_job(
        lambda: killHeartbeat(disable_schedule=False),
        'cron',
        day_of_week=_days,
        hour=_end_hour, minute=0,
        start_date=first_cycle,
        id='bh_stop_daily'
    )

    _scheduler.start()
    if show_scheduler_logs:
        print(f"%%% Scheduler INICIADO: {len(_scheduler.get_jobs())} jobs no total! %%%")