# import base64
from django.shortcuts import render, redirect, reverse, HttpResponse
from django.core.exceptions import PermissionDenied 
from datetime import datetime
from Reports01.models import AuthorisedUser, MBR_Data, LocationModel
from django.contrib.auth import authenticate, login, logout
import pandas as pd
from django.db.models import Sum, Avg, Count
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
import json

from django.db import models
from django.core.paginator import Paginator
from .views import user_in_add_group, user_in_change_group, user_in_delete_group, user_in_managers_group, user_passes_test, is_superuser

@user_passes_test(user_in_add_group)
def MBR_Input (request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        username = request.user.username
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_country = UserLocation.user_country
        user_location = UserLocation.user_location
        Countries = LocationModel.objects.all()
        Locations = {}
        for country in Countries:
            if country.country not in Locations:
                Locations[country.country] = []
            Locations[country.country].append(country.location)
        for country in Locations:
            Locations[country] = sorted(list(set(Locations[country])))

        if request.method == 'POST':
            month = request.POST.get('inputMonth')
            quarter = []
            if month.__contains__('-01') or month.__contains__('-02') or month.__contains__('-03'):
                quarter = 'Q1'
            elif month.__contains__('-04') or month.__contains__('-05') or month.__contains__('-06'):
                quarter = 'Q2'
            elif month.__contains__('-07') or month.__contains__('-08') or month.__contains__('-09'):
                quarter = 'Q3'
            else:
                quarter = 'Q4'

            ReportMonth = month
            ReportYear = datetime.strptime(month, '%Y-%m').strftime('%Y')
            ReportQuarter = quarter
            ReportCountry = request.POST.get('inputCountry')
            ReportLocation = request.POST.get('inputLocation')
            AreaSQFT = request.POST.get('AreaSQFT')
            TotalSeats = request.POST.get('TotalSeats')
            Headcount = request.POST.get('Headcount')
            OccupiedSeats = request.POST.get('OccupiedSeats')
            Laptop = request.POST.get('Laptop')
            Desktop = request.POST.get('Desktop')
            Dongle = request.POST.get('Dongle')
            Accessories = request.POST.get('Accessories')
            Work_Completed = request.POST.get('Completed')
            Work_In_Progress = request.POST.get('WIP')
            mbr_input = MBR_Data(ReportYear = ReportYear, ReportMonth = ReportMonth, ReportQuarter=ReportQuarter, ReportCountry=ReportCountry, ReportLocation = ReportLocation, AreaSQFT = AreaSQFT, TotalSeats =  TotalSeats, Area_Per_Seat = ( 0 if int(TotalSeats) == 0 or float(AreaSQFT) == 0.00 else (float(AreaSQFT)/int(TotalSeats)) ),
            Headcount = Headcount, OccupiedSeats = OccupiedSeats, Vacant_Seats = (0 if TotalSeats == 0  else (int(TotalSeats) - int(OccupiedSeats))), Utilization = (( 0 if int(TotalSeats) == 0 or int(OccupiedSeats) == 0 else int(OccupiedSeats)/int(TotalSeats))), Laptop = Laptop, Desktop = Desktop, Dongle = Dongle, Accessories = Accessories, Total_Assets = (int(Laptop) + int(Desktop) + int(Dongle) + int(Accessories)),
            Work_Completed = Work_Completed, Work_In_Progress = Work_In_Progress)
            context = {}
            data = MBR_Data.objects.filter(ReportMonth=ReportMonth, ReportLocation=ReportLocation)
            for row in data:    
                row.ReportMonth = datetime.strptime(row.ReportMonth, '%Y-%m').strftime('%b-%Y')                
            context["duplicateMBR"] = data
            if data.exists():
                return render (request, "MBR/mbr_already_exists.html", context)   
            mbr_input.set_user(request.user)
            mbr_input.save()

            success_message = (f"MBR Data Successfully Entered for {ReportLocation} Location for the Month of {datetime.strptime(ReportMonth, '%Y-%m').strftime('%b-%Y')}.")
            request.session['success_message'] = success_message
            return redirect(reverse('MBRInput') + '?success_message=' + success_message)
        
        else:
            success_message = request.session.pop('success_message', '')
            context = {'success_message': success_message, 
            'user_country': user_country,
            'user_location' : user_location,
            'locations':json.dumps(Locations),
            'countries':sorted(list(set(Countries.values_list('country', flat= True)))),}
            return render (request, 'MBR/00_MBR_Input.html', context)

def Space_Data(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        username = request.user.username
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_location = UserLocation.user_location
        mbr_data = MBR_Data.objects.all().order_by('ReportMonth')
        filtered_data = mbr_data.filter(ReportLocation=user_location)

        if request.user.groups.filter(name='Admin-Leaders').exists():
            mbr_data = mbr_data
        else:
            mbr_data = filtered_data

        if not mbr_data:
            return render(request, 'MBR/01_Space_Data.html', {'error_message': 'No Records To Display!'})    
        
        context = {}  
        latest_report = MBR_Data.objects.latest('ReportMonth')
        latest_month = latest_report.ReportMonth
        latest_data = mbr_data.filter(ReportMonth=latest_month)

        year = request.GET.get('year')
        quarter = request.GET.get('quarter')
        month = request.GET.get('month')
        location = request.GET.get('location')
        country = request.GET.get('country')

        if year == None and quarter==None and month == None and country==None and location == None:
            mbr_data = latest_data
        elif year == 'All' and quarter=='All' and month == 'All' and country=='All' and location == 'All':
            mbr_data = mbr_data
        else:
            if year != 'All':
                mbr_data = mbr_data.filter(ReportYear=year)
            if quarter != 'All':
                mbr_data = mbr_data.filter(ReportQuarter=quarter) 
            if month != 'All':
                mbr_data = mbr_data.filter(ReportMonth=month)
            if country != 'All':
                mbr_data = mbr_data.filter(ReportCountry=country)
            if location != 'All':
                mbr_data = mbr_data.filter(ReportLocation=location)  

        for row in mbr_data:
            row.ReportMonth = datetime.strptime(row.ReportMonth, "%Y-%m").strftime("%b-%Y")   
            row.Utilization = "{:.2f}%".format(row.Utilization * 100)

        context["mbr_dataset"] = mbr_data
        context["years"] = sorted(list(set(MBR_Data.objects.values_list('ReportYear',  flat=True))))
        context["quarters"] = sorted(list(set(MBR_Data.objects.values_list('ReportQuarter', flat=True))))
        context["months"] = sorted(list(set(MBR_Data.objects.values_list('ReportMonth', flat=True))))
        context["countries"] = sorted(list(set(MBR_Data.objects.values_list('ReportCountry', flat=True))))
        context["locations"] = sorted(list(set(MBR_Data.objects.values_list('ReportLocation', flat=True))))
        return render(request, 'MBR/01_Space_Data.html', context)

def eSupport_Data (request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        username = request.user.username
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_location = UserLocation.user_location
        mbr_data = MBR_Data.objects.all().order_by('ReportMonth')
        filtered_data = mbr_data.filter(ReportLocation=user_location)

        if request.user.groups.filter(name='Admin-Leaders').exists():
            mbr_data = mbr_data
        else:
            mbr_data = filtered_data
        if not mbr_data:
            return render(request, 'MBR/02_eSupport_Data.html', {'error_message': 'No Records To Display!'})    
        context = {} 
        latest_report = MBR_Data.objects.latest('ReportYear')
        latest_year = latest_report.ReportYear
        latest_data = mbr_data.filter(ReportYear=latest_year)

        year = request.GET.get('year')
        quarter = request.GET.get('quarter')
        month = request.GET.get('month')
        location = request.GET.get('location')
        country = request.GET.get('country')

        if year == None and quarter==None and month == None and country==None and location == None:
            mbr_data = latest_data
        elif year == 'All' and quarter=='All' and month == 'All' and country=='All' and location == 'All':
            mbr_data = mbr_data
        else:
            if year != 'All':
                mbr_data = mbr_data.filter(ReportYear=year)
            if quarter != 'All':
                mbr_data = mbr_data.filter(ReportQuarter=quarter) 
            if month != 'All':
                mbr_data = mbr_data.filter(ReportMonth=month)
            if country != 'All':
                mbr_data = mbr_data.filter(ReportCountry=country)
            if location != 'All':
                mbr_data = mbr_data.filter(ReportLocation=location)       
                        
        for row in mbr_data:
            row.ReportMonth = datetime.strptime(row.ReportMonth, "%Y-%m").strftime("%b-%Y")   

        context["mbr_dataset"] = mbr_data
        context["years"] = sorted(list(set(MBR_Data.objects.values_list('ReportYear',  flat=True))))
        context["quarters"] = sorted(list(set(MBR_Data.objects.values_list('ReportQuarter', flat=True))))
        context["months"] = sorted(list(set(MBR_Data.objects.values_list('ReportMonth', flat=True))))
        context["countries"] = sorted(list(set(MBR_Data.objects.values_list('ReportCountry', flat=True))))
        context["locations"] = sorted(list(set(MBR_Data.objects.values_list('ReportLocation', flat=True))))
        return render(request, 'MBR/02_eSupport_Data.html', context)

def Facility_Updates(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        username = request.user.username
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_location = UserLocation.user_location
        mbr_data = MBR_Data.objects.all().order_by('ReportMonth')
        filtered_data = mbr_data.filter(ReportLocation=user_location)

        if request.user.groups.filter(name='Admin-Leaders').exists():
            mbr_data = mbr_data
        else:
            mbr_data = filtered_data

        if not mbr_data:
            return render(request, 'MBR/03_Facility_Updates.html', {'error_message': 'No Records To Display!'})    
        
        context = {}
        latest_report = MBR_Data.objects.latest('ReportYear')
        latest_year = latest_report.ReportYear
        latest_data = mbr_data.filter(ReportYear=latest_year)

        year = request.GET.get('year')
        quarter = request.GET.get('quarter')
        month = request.GET.get('month')
        location = request.GET.get('location')
        country = request.GET.get('country')

        if year == None and quarter==None and month == None and country==None and location == None:
            mbr_data = latest_data
        elif year == 'All' and quarter=='All' and month == 'All' and country=='All' and location == 'All':
            mbr_data = mbr_data
        else:
            if year != 'All':
                mbr_data = mbr_data.filter(ReportYear=year)
            if quarter != 'All':
                mbr_data = mbr_data.filter(ReportQuarter=quarter) 
            if month != 'All':
                mbr_data = mbr_data.filter(ReportMonth=month)
            if country != 'All':
                mbr_data = mbr_data.filter(ReportCountry=country)
            if location != 'All':
                mbr_data = mbr_data.filter(ReportLocation=location) 
                     
        for row in mbr_data:
            row.ReportMonth = datetime.strptime(row.ReportMonth, "%Y-%m").strftime("%b-%Y")   

        context["mbr_dataset"] = mbr_data
        context["years"] = sorted(list(set(MBR_Data.objects.values_list('ReportYear',  flat=True))))
        context["quarters"] = sorted(list(set(MBR_Data.objects.values_list('ReportQuarter', flat=True))))
        context["months"] = sorted(list(set(MBR_Data.objects.values_list('ReportMonth', flat=True))))
        context["countries"] = sorted(list(set(MBR_Data.objects.values_list('ReportCountry', flat=True))))
        context["locations"] = sorted(list(set(MBR_Data.objects.values_list('ReportLocation', flat=True))))
        return render(request, 'MBR/03_Facility_Updates.html', context)

@user_passes_test(user_in_managers_group)
def update_mbr_data(request, mbr_data_id):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        username = request.user.username
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_country = UserLocation.user_country
        user_location = UserLocation.user_location
        Countries = LocationModel.objects.all()
        Locations = {}
        for country in Countries:
            if country.country not in Locations:
                Locations[country.country] = []
            Locations[country.country].append(country.location)
        for country in Locations:
            Locations[country] = sorted(list(set(Locations[country])))

        mbr_data = MBR_Data.objects.get(id=mbr_data_id)
        if request.method == 'POST':
            Month = request.POST.get('inputMonth')
            
            Quarter = []
            if Month.__contains__('-01') or Month.__contains__('-02') or Month.__contains__('-03'):
                Quarter = 'Q1'
            elif Month.__contains__('-04') or Month.__contains__('-05') or Month.__contains__('-06'):
                Quarter = 'Q2'
            elif Month.__contains__('-07') or Month.__contains__('-08') or Month.__contains__('-09'):
                Quarter = 'Q3'
            else:
                Quarter = 'Q4'

            mbr_data.ReportQuarter = Quarter
            mbr_data.ReportMonth = Month
            mbr_data.ReportYear = datetime.strptime(request.POST.get('inputMonth'),'%Y-%m').strftime('%Y')
            mbr_data.ReportCountry = request.POST.get('inputCountry')
            mbr_data.ReportLocation = request.POST.get('inputLocation')
            mbr_data.AreaSQFT = request.POST.get('AreaSQFT')
            mbr_data.TotalSeats = request.POST.get('TotalSeats')
            mbr_data.Headcount = request.POST.get('Headcount')
            mbr_data.OccupiedSeats = request.POST.get('OccupiedSeats')
            mbr_data.Vacant_Seats = (0 if mbr_data.TotalSeats == 0 else (int(mbr_data.TotalSeats) - int(mbr_data.OccupiedSeats)))
            mbr_data.Utilization = ( 0 if int(mbr_data.TotalSeats) == 0 or int(mbr_data.OccupiedSeats) == 0 else int(mbr_data.OccupiedSeats)/int(mbr_data.TotalSeats))
            mbr_data.Area_Per_Seat = ( 0 if int(mbr_data.TotalSeats) == 0 or float(mbr_data.AreaSQFT) == 0.00 else (float(mbr_data.AreaSQFT)/int(mbr_data.TotalSeats)) )
            mbr_data.Laptop = request.POST.get('Laptop')
            mbr_data.Desktop = request.POST.get('Desktop')
            mbr_data.Dongle = request.POST.get('Dongle')
            mbr_data.Accessories = request.POST.get('Accessories')
            mbr_data.Work_Completed = request.POST.get('Completed')
            mbr_data.Work_In_Progress = request.POST.get('WIP')
            mbr_data.Total_Assets = (int(mbr_data.Laptop) + int(mbr_data.Desktop)+ int(mbr_data.Dongle)+ int(mbr_data.Accessories))
            mbr_data.set_user(request.user)
            mbr_data.save()
            return redirect('SpaceData')
        context = {'mbr_data': mbr_data,
            'user_country': user_country,
            'user_location' : user_location,
            'locations':json.dumps(Locations),
            'countries':sorted(list(set(Countries.values_list('country', flat= True))))}
        return render(request, 'MBR/update_mbr_data.html', context)

@user_passes_test(is_superuser)
def Delete_MBR(request, id):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        mbrdata = MBR_Data.objects.get(pk=id)
        mbrdata.delete()
        return redirect("SpaceData")

def MBR_Report(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        mbr_data = MBR_Data.objects.all()
        if not mbr_data:
            return render(request, 'Charts/mbr_report.html', {'error_message': 'No Records To Display!'})
        context = {}
        table_data = MBR_Data.objects.values("ReportLocation").annotate( Laptop=Sum("Laptop"), Desktop=Sum("Desktop"), Dongle=Sum("Dongle"), Accessories=Sum("Accessories"), Total = Sum('Total_Assets'))
    
        year = request.GET.get('year')
        month = request.GET.get('month')
        location = request.GET.get('location')
        quarter = request.GET.get('quarter')

        latest_report = MBR_Data.objects.latest('ReportMonth')
        latest_month = latest_report.ReportMonth
        latest_data = mbr_data.filter(ReportMonth=latest_month)
        

        if month == 'All' and location == 'All' and quarter =='All' and year == 'All':
            mbr_data = mbr_data
            update_data = latest_data.filter(Work_In_Progress__isnull=False, Work_Completed__isnull=False)
        elif year == None and quarter == None and month ==None and location == None:
            mbr_data = latest_data
            update_data = latest_data.filter(Work_In_Progress__isnull=False, Work_Completed__isnull=False)
        else:
            if year != 'All':
                mbr_data = mbr_data.filter(ReportYear=year)
                update_data = latest_data.filter(Work_In_Progress__isnull=False, Work_Completed__isnull=False)
            if month != 'All':
                mbr_data = mbr_data.filter(ReportMonth= month)
                update_data = mbr_data.filter(ReportMonth= month).filter(Work_In_Progress__isnull=False, Work_Completed__isnull=False)
            if quarter != 'All':
                mbr_data = mbr_data.filter(ReportQuarter= quarter)
                update_data = latest_data.filter(Work_In_Progress__isnull=False, Work_Completed__isnull=False)
            if location != 'All':
                mbr_data= mbr_data.filter(ReportLocation=location)
                update_data= mbr_data.filter(ReportLocation=location).filter(Work_In_Progress__isnull=False, Work_Completed__isnull=False)

        for row in mbr_data:
            row.ReportMonth = datetime.strptime(row.ReportMonth, "%Y-%m").strftime("%b-%y")
            row.Utilization = "{:.2f}%".format(row.Utilization * 100)
            row.ReportLocation = row.ReportCountry if row.ReportCountry == 'Philippines' else row.ReportLocation
            
        for row in update_data:
            row.ReportLocation = row.ReportCountry if row.ReportCountry == 'Philippines' else row.ReportLocation

        space_data = mbr_data.values('ReportLocation').annotate(area_sqft=Avg('AreaSQFT'))    
        seats_data = mbr_data.values('ReportLocation').annotate(total_seat=Avg('TotalSeats'))
        headcount = mbr_data.values('ReportLocation').annotate(total_hc=Avg('Headcount'))

        laptop_total = mbr_data.values('ReportLocation').annotate(total_laptops=Sum('Laptop'))
        desktop_total = mbr_data.values('ReportLocation').annotate(total_desktops=Sum('Desktop'))
        dongle_total = mbr_data.values('ReportLocation').annotate(total_dongles=Sum('Dongle'))
        accessories_total = mbr_data.values('ReportLocation').annotate(total_accessories=Sum('Accessories'))

        facility_labels = [data['ReportLocation'] for data in space_data]
        area_sqfts = [data['area_sqft'] for data in space_data]
        total_seats = [data['total_seat'] for data in seats_data]
        Total_HC = [data['total_hc'] for data in headcount]
        
        space_chart = {'type': 'bar','data': {'labels': facility_labels,
            'datasets': [{'label': 'Area SQFT', 'data': area_sqfts, 'backgroundColor': '#4BCD3E', 'borderColor': '#4BCD3E', 'borderWidth': 1 }] }, 
            'options': { 'maintainAspectRatio': 'false',
    'responsive': 'true', 'scales': { 'yAxes': [{ 'ticks': { 'beginAtZero': True }}]}}}
        
        seats_hc_chart = { 'type': 'bar', 'data': { 'labels': facility_labels, 
            'datasets': [{ 'label': 'Total Seats', 'data': total_seats, 'backgroundColor': '#4BCD3E', 'borderColor': '#4BCD3E','borderWidth': 1 },
            {'label':'Total Headcount', 'data': Total_HC, 'backgroundColor': '#012834', 'borderColor': '#012834', 'borderWidth': 1}]},
            'options':{'scales': {'yAxes': [{'ticks': { 'beginAtZero': True}}]}}}
        
        location_labels = [data['ReportLocation'] for data in laptop_total]
        Total_Laptop = [data['total_laptops'] for data in laptop_total]
        Total_Desktop = [data['total_desktops'] for data in desktop_total]
        Total_Dongle = [data['total_dongles'] for data in dongle_total]
        Total_Accessories = [data['total_accessories'] for data in accessories_total]

        assets_chart = {'type': 'bar', 'data': {'labels': location_labels,
                    'datasets': [{ 'label': 'Laptop', 'data': Total_Laptop, 'backgroundColor': '#4BCD3E', 'borderColor': '#4BCD3E', 'borderWidth': 1},
                    {'label': 'Desktop','data': Total_Desktop, 'backgroundColor': '#012834', 'borderColor': '#012834', 'borderWidth': 1},
                    {'label': 'Dongle','data': Total_Dongle, 'backgroundColor': '#3BCFF0', 'borderColor': '#3BCFF0','borderWidth': 1},
                    {'label': 'Accessories', 'data': Total_Accessories, 'backgroundColor': '#A18CDE', 'borderColor': '#A18CDE', 'borderWidth': 1}]},
                    'options': { 'scales': { 'yAxes': [{ 'ticks': { 'beginAtZero': True }}]}}}
        
        laptop = mbr_data.aggregate(Sum('Laptop'))['Laptop__sum'] or 0
        desktop = mbr_data.aggregate(Sum('Desktop'))['Desktop__sum'] or 0
        dongle = mbr_data.aggregate(Sum('Dongle'))['Dongle__sum'] or 0
        accessories = mbr_data.aggregate(Sum('Accessories'))['Accessories__sum'] or 0
        total = float(laptop) + float(desktop) + float(dongle) + float(accessories)

        laptops_per = round (laptop/total * 100, 2) if total != 0 else 0
        desktops_per = round(desktop/total * 100, 2) if total != 0 else 0
        dongles_per = round(dongle/total * 100, 2) if total != 0 else 0
        accessories_per = round(accessories/total * 100, 2) if total != 0 else 0
        
        d_chart_data = {'laptops': laptops_per, 'desktops': desktops_per, 'dongles': dongles_per, 'accessories': accessories_per}

        d_chart = {'labels': ['Laptop', 'Desktop', 'Dongle', 'Accessories'],
            'data': [d_chart_data['laptops'], d_chart_data['desktops'], d_chart_data['dongles'], d_chart_data['accessories']],
            'backgroundColor': ['#4BCD3E', '#012834', '#3BCFF0', '#A18CDE'] }
      
        context = {"mbr_dataset" : mbr_data,
        "years" : sorted(list(set(MBR_Data.objects.values_list('ReportYear', flat=True)))),
        "months" : sorted(list(set(mbr_data.values_list('ReportMonth', flat=True)))),
        "quarters" : sorted(list(set(mbr_data.values_list('ReportQuarter', flat=True)))),
        "locations" : sorted(list(set(MBR_Data.objects.values_list('ReportLocation', flat=True)))),
        "space_data" : space_data, 'table_data' : table_data, 'update_data':update_data,
        "space_chart" : json.dumps(space_chart), "seats_hc_chart": json.dumps(seats_hc_chart), "d_chart_data" : json.dumps(d_chart), "asset_chart" : json.dumps(assets_chart)}

        return render(request, "Charts/mbr_report.html", context)
