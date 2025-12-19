from datetime import datetime, timedelta, date
from rest_framework.response import Response



def custom_response_upload(data, message, http_status, pagination=None, status_str=None):

    """

    Standardized response wrapper.

    Arguments:

    - data: The payload (list or dict)

    - message: Human readable message

    - http_status: HTTP Status Code (e.g., 200, 400, 201) - NOTE: This name changed from 'status' to 'http_status'

    - pagination: Pagination dictionary (optional)

    - status_str: 'success' or 'error' string (optional, auto-detected if not provided)

    """

   

    # 1. Agar status_str pass nahi kiya, to HTTP code se auto-detect karein

    if status_str is None:

        if 200 <= http_status < 300:

            status_str = "success"

        else:

            status_str = "error"



    response_data = {

        "status": status_str,

        "message": message,

        "data": data,

    }

   

    # 2. Pagination data add karein

    if pagination:

        response_data["pagination"] = pagination



    # 3. Response return karein

    return Response(response_data, status=http_status)

def calculate_attendance_status(checkin_time, checkout_time, policy):
    """
    Policy ke hisaab se status aur hours calculate karega.
    """
    if not checkin_time or not checkout_time:
        return 'Absent', 0.0

    # 1. Total Hours Calculation
    # Convert simple time to dummy datetime for subtraction if needed
    # Lekin Pandas usually timestamp deta hai, so we assume full datetime objects here
    duration = checkout_time - checkin_time
    total_hours = round(duration.total_seconds() / 3600, 2)

    status = 'Present'

    # 2. Check Late Arrival
    # Policy Shift Start (Time) ko Checkin (Datetime) se compare karna
    # Humein checkin_time ka sirf time part chahiye
    checkin_time_only = checkin_time.time()
    
    # Grace Period logic
    # Shift Start: 09:00:00
    # Grace: 10 mins
    # Late Time: 09:10:00
    
    # Policy time ko full datetime banayen comparison k liye
    shift_start_dt = datetime.combine(date.today(), policy.shiftstart)
    late_limit = shift_start_dt + timedelta(minutes=policy.graceperiodmins)
    
    # Checkin time ko bhi aaj ki date k sath combine karein compare karne k liye
    checkin_dt = datetime.combine(date.today(), checkin_time_only)

    if checkin_dt > late_limit:
        status = 'Late'

    # 3. Check Half Day
    # Agar banda bohot late aya (e.g. 12 baje k baad)
    half_day_limit = shift_start_dt + timedelta(minutes=policy.halfdayaftermins)
    if checkin_dt > half_day_limit:
        status = 'Half Day'

    return status, total_hours