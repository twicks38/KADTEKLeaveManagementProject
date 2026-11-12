import calendar
from datetime import datetime
from leave_management.models import LeaveRequest
from hr_management.models import TeamMembership
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

def calendar_service(request, team_calendar, leave_request=None):
    #Gets current month as default changes with user navigation
    if leave_request is not None:
        month = int(request.GET.get('month', leave_request.start_date.month))
        year = int(request.GET.get('year', leave_request.start_date.year))

    else:
        month = int(request.GET.get('month', datetime.today().month))
        year = int(request.GET.get('year', datetime.today().year))
 
    calendar_start = calendar.Calendar(firstweekday=calendar.SUNDAY) #defines calendar shoould start on sunday
    month_calendar = calendar_start.monthdatescalendar(year, month) #sets which month the calendar is on
 
    first_day = datetime(year, month, 1).date() #first day in the month
    last_day = datetime(year, month, calendar.monthrange(year, month)[1]).date() #last day in the month

    #gets all of the user requests for the user and order by start date and if approved or not
    all_user_requests = []  #list created as it allows for the same logic flow

    #Leave requests for individual user
    if not team_calendar:
        user_requests = LeaveRequest.objects.filter(
            user = request.user,
            start_date__lte = last_day,
            end_date__gte = first_day,
            status__in=["Approved", "Pending"],
        ).order_by('start_date')
        all_user_requests.extend(user_requests)


    #If it is a team calendar run code below
    else:
        #gets the team ID of the manager logged in
        team_id = TeamMembership.objects.get(
            user = request.user,
            role__name = "Manager",
            active=True
        ).team

        #Gets the employees apart of the same team as the manager
        employees = User.objects.filter(
            teammembership__team=team_id,
            teammembership__active = True
        ).distinct()

     
        for employee in employees: #Loops through each employee and gets leave records
            user_request = LeaveRequest.objects.filter(
                user=employee,
                start_date__lte = last_day,
                end_date__gte = first_day,
                status__in = ["Approved", "Pending"],
            ).order_by("start_date")

            #Adds records to list
            all_user_requests.extend(user_request)

            


    calendar_weeks = [] #all of the weeks in the calendar will be stored here

    for week in month_calendar: 
        week_start = week[0]
        week_end = week[-1]


        week_request = [
            leave_request
            for leave_request in all_user_requests
            if leave_request.start_date <= week_end and leave_request.end_date >= week_start
        ]

        days = []

        for current_day in week:
            days.append({
                "date":current_day,
                "day":current_day.day,
                "is_current_month":  current_day.month == month
            })

        leave_segments = [] #this holds all of the leave request for the interface to use to place on calendar

        for current_leave in week_request:
            #Gets the start of the leave segment
            segment_start = max(current_leave.start_date,
                                week_start,
                                first_day
                )

            #gets the end of the leave segment 
            segment_end = min(
                current_leave.end_date,
                week_end,
                last_day
            )

            if segment_start >segment_end: #if valid it continues
                continue

            #determines where it should start
            start_column = (segment_start - week_start).days
            span = (segment_end - segment_start).days + 1 #determines how long the leave bar should be



            leave_segments.append({ #adds them to the segmentws as a dictionary to use in the interface
                "leave_request":current_leave,
                "start_column":start_column,
                "span": span,
                "end_column": start_column + span -1,
                "requesting": (leave_request is not None and current_leave.id == leave_request.id)
            })


        lanes = []#this holds all of the leave request bars (used more for manager view)

        for segment in leave_segments: #loops through each of the leave requests
            placed = False #if they haven't already been calcualted

            
            for lane_number, lane in enumerate(lanes): 
                overlaps = False 

                #Checks if there are any overlaps
                for exsiting_segment in lane:
                    if(segment["start_column"] <= exsiting_segment["end_column"]
                       and segment["end_column"] >= exsiting_segment["start_column"]):
                        overlaps = True
                        break #breaks out of the loop

                if not overlaps: #if no overlaps
                    lane.append(segment)
                    segment["lane"] = lane_number
                    placed = True
                    break #breaks out of loops

            #if the request hasn't been placed it works out where it should be
            if not placed:
                lanes.append([segment])
                segment["lane"] = len(lanes) - 1

        lane_count = max(len(lanes), 1) #adds how many lanes there are no top of each other to 

        calendar_weeks.append({ #adds this data to the calendar as a dictionary
            "days":days,
            "leave_segments":leave_segments,
            "lane_count":lane_count
        })

    #This section below is the calendar navigation for when changing months
    prev_month = month-1
    prev_year = year
 
    if prev_month < 1:
        prev_month = 12
        prev_year -= 1
 
    next_month = month + 1
    next_year = year
 
    if next_month > 12:
        next_month = 1
        next_year += 1
 
 
    context = { #adds it to the context which is given to the front end
        "calendar_weeks": calendar_weeks,
        "month": month,
        "year": year,
        "month_name": calendar.month_name[month],
        "prev_month": prev_month,
        "prev_year": prev_year,
        "next_month": next_month,
        "next_year": next_year,
        "team_calendar": team_calendar,
    }

    return context