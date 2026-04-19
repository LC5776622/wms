# import base64
from django.shortcuts import render, redirect, reverse, HttpResponse
from datetime import datetime
from Reports01.models import AuthorisedUser, Incident_Data, LocationModel
import pandas as pd
from django.db.models import Count
from .forms import UploadIncidents
from .templatetags import custom_filters
from django.conf import settings
from calendar import month_name
from django.contrib.auth.decorators import user_passes_test, login_required
import json
from django.db.models.functions import TruncMonth
from django.core.paginator import Paginator
from .views import user_in_add_group, user_in_change_group, user_in_delete_group, user_in_managers_group, user_passes_test, is_superuser


@user_passes_test(is_superuser)
def Incident_Upload(request):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        if request.method == 'POST':
            form = UploadIncidents(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES['incidentfile']
                data = pd.read_excel(file)
                expected_columns = ['Date', 'Time', 'Country', 'Location', 'Sub-Location', 'Severity', 'Incident Type', 'Category', 'Equipment Category', 'Nature Of Incident', 'Brief About Incident', 'Root Cause', 'Immediate Corrective Action', 'Preventive Action', 'Status', 'Closure Date', 'Remarks']
                if list(data.columns) != expected_columns or len(data.columns) != len(expected_columns):
                    error_message = f"The Upload File should have these {len(data.columns)} columns only: {', '.join(expected_columns)}. Please refer to Sample File below."
                    return render(request, "Incidents/Incident_Upload.html", {'form': form, 'error_message': error_message})
                count = 0
                duplicates = []
                for index, row in data.iterrows():
                    date = (row['Date'])
                    obj = Incident_Data(
                        Report_Date = date,
                        Report_Year = date.year,
                        Report_Month = date.month,
                        Report_Quarter = (date.month - 1)//3 + 1,
                        Report_Time = row['Time'],
                        Report_Country = row['Country'],
                        Report_Location = row['Location'],
                        Report_Sub_Loc = row['Sub-Location'],
                        Inci_Nature = row['Nature Of Incident'],
                        Inci_Category = row['Category'],
                        Equip_Category = row['Equipment Category'],
                        Severity = row['Severity'],
                        Incident_Brief = row['Brief About Incident'],
                        Corrective_Act = row['Immediate Corrective Action'],
                        Root_Cause = row['Root Cause'],
                        Preventive_Act = row['Preventive Action'],
                        Status = row['Status'],
                        Closure_Date =  None if row['Status'] == 'Open' or row['Status'] == 'In Progress' else row['Closure Date'],
                        Remarks = '-' if row['Remarks'] =='' or row['Remarks'] == None else row['Remarks'], )
                    context = {}
                    data = Incident_Data.objects.filter(Report_Date=obj.Report_Date, Report_Location=obj.Report_Location, Report_Sub_Loc=obj.Report_Sub_Loc, Inci_Nature=obj.Inci_Nature, Inci_Category= obj.Inci_Category )
                    if data.exists():
                        duplicates.append(obj)
                    else:
                        obj.set_user(request.user)
                        obj.save()
                        count += 1
                if duplicates:
                    context = {'dataset6': duplicates}
                    # success_message = (f"{len(duplicates)} Records Already Exist.")
                    # request.session['success_message'] = success_message
                    return render(request, "OPEX/GL_already_exists.html", context)
                else:
                    success_message = (f"{count} Records Uploaded Successfully.")
                    request.session['success_message'] = success_message
                    return redirect(reverse('IncidentInput') + '?success_message=' + success_message)
        else:
            form = UploadIncidents()
            success_message = request.session.pop('success_message', '')
            return render(request, 'Incidents/00_Incident_Input.html', {'form': form,'success_message':success_message})

@user_passes_test(user_in_add_group)
def Incident_Input (request):
        if request.user.is_anonymous:
            return redirect('/login')
        else:
            username = request.user.username
            UserLocation = AuthorisedUser.objects.get(userid=username)
            user_country = UserLocation.user_country
            user_location = UserLocation.user_location
            Locations = LocationModel.objects.all().order_by('location')
            user_sub_Loc = Locations.filter(location=user_location)
            subLocations = {}
            for location in Locations:
                if location.location not in subLocations:
                    subLocations[location.location] = []
                subLocations[location.location].append(location.sub_locs)

            if request.method == 'POST':
                Report_Country = request.POST.get('input_Country')
                Report_Location = request.POST.get('input_Loc')
                Report_Sub_Loc = request.POST.get('input_Sub_Loc')
                Report_Date = datetime.strptime(request.POST.get('input_Date'), '%Y-%m-%d')
                Report_Month = Report_Date.month
                Report_Quarter = (Report_Month - 1)// 3 + 1
                Report_Year = Report_Date.year
                Report_Time = request.POST.get('input_Time')
                Reported_By = request.POST.get('ReportedBy')
                Inci_Nature = request.POST.get('Inci_Nature')
                Inci_Category = request.POST.get('Inci_Cat')
                Equip_Category = request.POST.get('Equip_Cat')
                Severity = request.POST.get('Severity')
                Impact = True if request.POST.get('Impact') else False
                Impact_Desc = request.POST.get('ImpactDesc') if Impact else "No Impact"
                Incident_Brief = request.POST.get('Inci_Brief')
                Corrective_Act = request.POST.get('Corrective')
                Root_Cause = request.POST.get('Root_Cause')
                Preventive_Act = request.POST.get('Preventive')
                Prev_Act_Resp = None if request.POST.get('PrevActResp') == '' or request.POST.get('PrevActResp') == None else request.POST.get('PrevActResp')
                Act_Implement_Date = None if request.POST.get('ImpleDate') == '' or request.POST.get('ImpleDate') == None else datetime.strptime(request.POST.get('ImpleDate'),'%Y-%m-%d')
                Status = request.POST.get('Status')
                Closure_Date = None if Status == 'Open' or Status == 'In Progress' else datetime.strptime(request.POST.get('Clousre_Date'),'%Y-%m-%d')
                Remarks = '-' if request.POST.get('Remarks') == '' or request.POST.get('Remarks') == None else request.POST.get('Remarks')
                incident_input = Incident_Data(Report_Year = Report_Year, Report_Quarter=Report_Quarter, Impact=Impact, Impact_Desc=Impact_Desc, Reported_By=Reported_By, Report_Month = Report_Month, Report_Date = Report_Date, Report_Time = Report_Time,Report_Country=Report_Country, Report_Location = Report_Location, Report_Sub_Loc= Report_Sub_Loc, Inci_Nature=Inci_Nature, Inci_Category= Inci_Category,Equip_Category=Equip_Category,Severity=Severity,Incident_Brief=Incident_Brief,Corrective_Act=Corrective_Act, Root_Cause=Root_Cause, Preventive_Act = Preventive_Act, Prev_Act_Resp=Prev_Act_Resp, Act_Implement_Date=Act_Implement_Date, Status = Status, Closure_Date = Closure_Date, Remarks = Remarks)
                context = {}
                data = Incident_Data.objects.filter(Report_Year=Report_Year, Report_Month=Report_Month, Report_Location=Report_Location, Reported_By=Reported_By, Report_Date=Report_Date, Report_Time=Report_Time, Inci_Category=Inci_Category, Equip_Category=Equip_Category)
                for row in data:    
                    row.Report_Date = row.Report_Date.strftime('%d-%b-%Y')
                context["DuplicateInci"] = data
                if data.exists():
                    return render (request, "Incidents/already_exists.html", context)
                incident_input.set_user(request.user)
                incident_input.save()
                success_message = (f"Data for the incident from {Report_Location} location, reported on {Report_Date.strftime('%d-%b-%Y')} at {Report_Time}, has been submitted successfully.")
                request.session['success_message'] = success_message
                return redirect(reverse('IncidentInput') + '?success_message=' + success_message)
            else:
                success_message = request.session.pop('success_message', '')
                context = {
                    'success_message' :success_message,
                    'subLocations': json.dumps(subLocations),
                    'locations':sorted(list(set(Locations.values_list('location', flat= True)))),
                    'countries':sorted(list(set(Locations.values_list('country', flat= True)))),
                    'user_country': user_country,
                    'user_location' : user_location,
                    'user_sub_loc' :user_sub_Loc
                }
                return render (request, 'Incidents/00_Incident_Input.html', context)

def Incidents_Data(request):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        username = request.user.username
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_location = UserLocation.user_location
        incident_data = Incident_Data.objects.all().order_by('Report_Month', 'Report_Date', 'Report_Location')
        filtered_data = incident_data.filter(Report_Location=user_location)
        if request.user.groups.filter(name='Admin-Leaders').exists():
            incident_data = incident_data
        else:
            incident_data = filtered_data

        if not incident_data:
            return render(request, 'Incidents/01_Incident_Data.html', {'error_message': 'No Records To Display!'})
        context = {}
        latest_report = incident_data.latest('Report_Date')
        latest_date = latest_report.Report_Date
        latest_data = incident_data.filter(Report_Date=latest_date)

        year =request.GET.get('year')
        quarter = request.GET.get('quarter')
        month = request.GET.get('month')
        location = request.GET.get('location')
        category = request.GET.get('category')
        severity= request.GET.get('severity')           

        if year == None and month == None and quarter==None and severity == None and category==None and location == None or year == 'All' and month == 'All' and quarter=='All' and severity == 'All' and category=='All' and location == 'All':
            incident_data = latest_data
        else:
            if year != 'All':
                incident_data = incident_data.filter(Report_Year=year)
            if quarter != 'All':
                incident_data = incident_data.filter(Report_Quarter=quarter)
            if month != 'All':
                incident_data = incident_data.filter(Report_Month=month)
            if location != 'All':
                incident_data = incident_data.filter(Report_Location=location)
            if category != 'All':
                incident_data = incident_data.filter(Inci_Category=category)
            if severity != 'All':
                incident_data = incident_data.filter(Severity=severity)     

        for row in incident_data:
                row.Inci_Category = row.Inci_Category.replace('&', 'And')

        context = {'incident_data': incident_data,
            "years" : sorted(list(set(Incident_Data.objects.values_list('Report_Year',  flat=True)))),
            "quarters" : sorted(list(set(Incident_Data.objects.values_list('Report_Quarter',  flat=True)))),
            "months" : sorted(list(set(Incident_Data.objects.values_list('Report_Month', flat=True)))),
            "locations" : sorted(list(set(Incident_Data.objects.values_list('Report_Location', flat=True)))),
            "categories" : sorted(list(set(Incident_Data.objects.values_list('Inci_Category', flat=True)))),
            "severities" : sorted(list(set(Incident_Data.objects.values_list('Severity', flat=True))))}
   
        return render(request, 'Incidents/01_Incident_Data.html', context)
    
def Incident_View(request, incident_data_id):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        incident_data = Incident_Data.objects.get(id=incident_data_id)
        incident_data.Closure_Date ='-' if incident_data.Closure_Date == None else incident_data.Closure_Date
    
        context = {'incident_data': incident_data}
        return render(request, 'Incidents/Incident_View.html', context)

@user_passes_test(user_in_change_group)
def update_incident_data(request, incident_data_id):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        username = request.user.username
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_country = UserLocation.user_country
        user_location = UserLocation.user_location
        Locations = LocationModel.objects.all()
        user_sub_Loc = Locations.filter(location=user_location)
        subLocations = {}
        for location in Locations:
            if location.location not in subLocations:
                subLocations[location.location] = []
            subLocations[location.location].append(location.sub_locs)
        data = Incident_Data.objects.all()

        incident_data = data.get(id=incident_data_id)  
        incident_data.Report_Date = incident_data.Report_Date.strftime("%Y-%m-%d")
        incident_data.Report_Time = incident_data.Report_Time.strftime("%H:%M")
        incident_data.Closure_Date = incident_data.Closure_Date.strftime("%Y-%m-%d") if incident_data.Closure_Date != None else None
        incident_data.Act_Implement_Date = incident_data.Act_Implement_Date.strftime("%Y-%m-%d") if incident_data.Act_Implement_Date != None else None
        if request.method == 'POST':
            date = datetime.strptime(request.POST.get('input_Date'), '%Y-%m-%d')
            incident_data.Report_Year = date.year
            incident_data.Report_Month = date.month
            incident_data.Report_Quarter = (date.month - 1)// 3 + 1
            incident_data.Report_Date = request.POST.get('input_Date')
            incident_data.Report_Time = request.POST.get('input_Time')
            incident_data.Report_Country = request.POST.get('input_Country')
            incident_data.Report_Location = request.POST.get('input_Loc')
            incident_data.Report_Sub_Loc = request.POST.get('input_Sub_Loc')
            incident_data.Reported_By = request.POST.get('ReportedBy')
            incident_data.Inci_Nature = request.POST.get('Inci_Nature')
            incident_data.Inci_Category = request.POST.get('Inci_Cat')
            incident_data.Equip_Category = request.POST.get('Equip_Cat')
            incident_data.Severity = request.POST.get('Severity')
            incident_data.Impact = True if request.POST.get('Impact') else False
            incident_data.Impact_Desc = request.POST.get('ImpactDesc') if incident_data.Impact else "No Impact"
            incident_data.Incident_Brief = request.POST.get('Inci_Brief')
            incident_data.Corrective_Act = request.POST.get('Corrective')
            incident_data.Root_Cause = request.POST.get('Root_Cause')
            incident_data.Preventive_Act = request.POST.get('Preventive')
            incident_data.Prev_Act_Resp = None if request.POST.get('PrevActResp') == '' or request.POST.get('PrevActResp') == None else request.POST.get('PrevActResp')
            incident_data.Act_Implement_Date = None if request.POST.get('ImpleDate') == '' or request.POST.get('ImpleDate') == None else datetime.strptime(request.POST.get('ImpleDate'),'%Y-%m-%d')
            incident_data.Status = request.POST.get('Status')
            incident_data.Closure_Date = None if incident_data.Status == 'Open' or incident_data.Status == 'In Progress'  else datetime.strptime(request.POST.get('Clousre_Date'),'%Y-%m-%d')
            incident_data.Remarks = '-' if request.POST.get('Remarks') == '' or request.POST.get('Remarks') == None else request.POST.get('Remarks')
            incident_data.set_user(request.user)      
            incident_data.save()
            return redirect('IncidentData')
        
        context1 = {
            'incident_data': incident_data,
            'subLocations': json.dumps(subLocations),
            'locations':sorted(list(set(Locations.values_list('location', flat= True)))),
            'countries':sorted(list(set(Locations.values_list('country', flat= True)))),
            'user_country': user_country,
            'user_location' : user_location,
            'user_sub_loc' :user_sub_Loc
        }
        return render(request, 'Incidents/update_incident_data.html', context1)

@user_passes_test(user_in_delete_group)
def Delete_Incident(request, id):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        incident_data = Incident_Data.objects.get(pk=id)
        incident_data.delete()
        return redirect("IncidentData")

def get_month_name(numeric_month):
    month_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    return month_names[numeric_month - 1]

def Incident_Report(request, month_names=None):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        incident_data = Incident_Data.objects.all()
        
        if not incident_data:
            return render(request, 'Charts/incident_report.html', {'error_message': 'No Records To Display!'})
        
        context = {}
        current_year = datetime.today().year
        latest_data = incident_data.filter(Report_Year=current_year)

        year =request.GET.get('year')
        quarter = request.GET.get('quarter')
        month = request.GET.get('month')
        country= request.GET.get('country')
        location = request.GET.get('location')

        if month == None and country == None and location == None and quarter == None and year == None or month == 'All' and country =='All' and location == 'All' and quarter == 'All' and year == 'All':
            incident_data = latest_data
        else:
            if country != 'All':
                incident_data = incident_data.filter(Report_Country=country)
            if location != 'All':
                incident_data = incident_data.filter(Report_Location=location)
            if month != 'All':
                incident_data = incident_data.filter(Report_Month=month)
            if quarter != 'All': 
                incident_data = incident_data.filter(Report_Quarter=quarter)
            if year != 'All':
                incident_data = incident_data.filter(Report_Year=year)
                        

        cat_data = incident_data.values('Inci_Category', 'Report_Month') \
        .annotate(total_count=Count('Inci_Category')) \
        .order_by('Report_Month', 'Inci_Category')

        labels = sorted(list(set(cat_data.values_list('Report_Month', flat=True))))
        categories = sorted(list(set(cat_data.values_list('Inci_Category', flat=True))))
        category_dataset = []
        for category in categories:
            category_data = cat_data.filter(Inci_Category=category)
            counts = []
            for month in labels:
                month_record = category_data.filter(Report_Month=month).first()
                count = month_record.get('total_count', 0) if month_record else '-'
                counts.append(count)
            category_dataset.append({
                'label':category,
                'data':counts,
            })



        sev_data = incident_data.values('Severity', 'Report_Location') \
        .annotate(total_count=Count('Report_Date')) \
        .order_by('Report_Location', 'Severity')

        sev_labels = sorted(list(set(sev_data.values_list('Report_Location', flat=True))))
        serverities = sorted(list(set(sev_data.values_list('Severity', flat=True))))
        severity_dataset = []
        for severity in serverities:
            severity_data = sev_data.filter(Severity=severity)
            counts = []
            for loc in sev_labels:
                month_record = severity_data.filter(Report_Location=loc).first()
                count = month_record.get('total_count', 0) if month_record else '-'
                counts.append(count)
            severity_dataset.append({
                'label':severity,
                'data':counts,
            })



        month_data = incident_data.values('Report_Month').annotate(count=Count('Report_Month')).order_by('Report_Month')
        month_chart = [{'month' : get_month_name(item['Report_Month']), 'count': item['count']} for item in month_data]

        month_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        df1 = pd.DataFrame(list(incident_data.values('Report_Location', 'Report_Month', 'Report_Date')))
        df1['Location'] = df1['Report_Month'].apply(lambda x: month_names[x-1])
        custom_sort_order = {month_names[i]:i+1 for i in range(12)}
        df1['MonthSort'] = df1['Location'].map(custom_sort_order)
        df1 = df1.sort_values(by='MonthSort')
        df1.drop(columns=['MonthSort'], inplace=True)
        df1 = df1.pivot_table(index='Report_Location', columns=['Report_Month','Location'], fill_value=0, aggfunc='count', margins=True, margins_name='Total')
        

        df2 = pd.DataFrame(list(incident_data.values('Inci_Category', 'Report_Month', 'Report_Date')))
        df2['Month'] = df2['Report_Month'].apply(lambda x: month_names[x-1])
        custom_sort_order = {month_names[i]:i+1 for i in range(12)}
        df2['MonthSort'] = df2['Month'].map(custom_sort_order)
        df2 = df2.sort_values(by='MonthSort')
        df2.drop(columns=['MonthSort'], inplace=True)
        df2_pivot = df2.pivot_table(index=['Report_Month', 'Month'], columns='Inci_Category', fill_value=0, aggfunc='count', margins=True, margins_name='Total')  


        df4 = pd.DataFrame(list(incident_data.values('Severity', 'Report_Month', 'Report_Date')))
        df4['Month'] = df4['Report_Month'].apply(lambda x:month_names[x-1])
        custom_sort_order = {month_names[i]:i+1 for i in range(12)}
        df4['MonthSort'] = df4['Month'].map(custom_sort_order)
        df4 = df4.sort_values(by='MonthSort')
        df4.drop(columns=['MonthSort'], inplace=True)
        df4 = df4.pivot_table(index=['Report_Month', 'Month'], columns='Severity', fill_value=0, aggfunc='count', margins=True, margins_name='Total')

        
        context = {'incident_data': incident_data,
            'pivot_table1' :df1.to_html(),'pivot_table2' :df2_pivot.to_html(), 'pivot_table4' :df4.to_html(),
            'month_chart': json.dumps(month_chart), 
            'severity_chart': severity_dataset, 'sev_labels':sev_labels, 'category_chart': category_dataset, 'labels':labels,
            "months" : sorted(list(set(Incident_Data.objects.values_list('Report_Month', flat=True)))),
            "countries" : sorted(list(set(Incident_Data.objects.values_list('Report_Country', flat=True)))),
            "locations" : sorted(list(set(Incident_Data.objects.values_list('Report_Location', flat=True)))),
            "years" : sorted(list(set(Incident_Data.objects.values_list('Report_Year',  flat=True)))),
            "quarters" : sorted(list(set(Incident_Data.objects.values_list('Report_Quarter',  flat=True))))}
        return render(request, 'Charts/incident_report.html', context)
