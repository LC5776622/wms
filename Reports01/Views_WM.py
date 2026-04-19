# import base64
from django.shortcuts import render, redirect, reverse, HttpResponse
from django.core.exceptions import PermissionDenied 
from datetime import datetime
from Reports01.models import AuthorisedUser, RoutineDisposal, ESG, Non_Routine_Disposal, E_Waste_Disposal, LocationModel, DisposalSummary
import pandas as pd
from django.db.models import Sum
import os
from django.conf import settings
from django.contrib.auth.models import Group
from .forms import UploadRoutine, UploadNonRoutine, UploadEWaste
from django.forms import formset_factory
from django.db.models import F, FloatField, Sum, ExpressionWrapper
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
import json
from .templatetags  import custom_filters
from django.core.paginator import Paginator
from .views import user_in_add_group, user_in_change_group, user_in_delete_group, user_in_managers_group, user_in_leaders_group, user_passes_test, is_superuser

@user_passes_test(user_in_add_group)
def WM_Routine_Input(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        username = request.user.username
        superuser = request.user.is_superuser
        admin_leaders = request.user.groups.filter(name='Admin-Leaders').exists()
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_country = UserLocation.user_country
        user_location = UserLocation.user_location
        UserFilter = AuthorisedUser.objects.filter(exclude_from_calculation=False, is_manager=False) if superuser or admin_leaders else AuthorisedUser.objects.filter(user_location=user_location, exclude_from_calculation=False, is_manager=False)
        Verifiers = AuthorisedUser.objects.filter(exclude_from_calculation=False, is_manager=True) if superuser or admin_leaders else AuthorisedUser.objects.filter(user_location=user_location, exclude_from_calculation=False, is_manager=True)
        Countries = LocationModel.objects.all()
        Locations = {}
        for country in Countries:
            if country.country not in Locations:
                Locations[country.country] = []
            Locations[country.country].append(country.location)
        for country in Locations:
            Locations[country] = sorted(list(set(Locations[country])))

        if request.method =='POST':
            Disposal_Date = datetime.strptime(request.POST.get('disposalDate'), '%Y-%m-%d')
            Year = Disposal_Date.year
            Month = Disposal_Date.month
            Quarter = (Month-1)//3 +1 
            Country = request.POST.get('Country')
            Location = request.POST.get('Location')
            Function = request.POST.get('Function')
            Waste_Type = request.POST.get('wasteType')
            Waste_State = request.POST.get('wasteState')
            Disposal_Type = request.POST.get('disposalType')
            Severity = request.POST.get('Severity')
            Description = request.POST.get('itemDesc')
            Unit = 'KG' if Description.lower().__contains__('face') or Description.lower().__contains__('mask') else request.POST.get('Unit')
            Quantity = float(request.POST.get('Quantity'))*0.004 if Description.lower().__contains__('face') or Description.lower().__contains__('mask') else request.POST.get('Quantity')
            Disposed_By = request.POST.get('disposedBy')
            Verified_By = request.POST.get('verifiedBy')
            Remarks = request.POST.get('Remarks')
            routine_input = RoutineDisposal(Disposal_Date=Disposal_Date, Month=Month, Quarter=Quarter, Year=Year, Country=Country, Location=Location, Function=Function, Waste_Type=Waste_Type, Waste_State=Waste_State, Severity=Severity, Disposal_Type=Disposal_Type, Description=Description, Unit=Unit, Quantity=Quantity, Disposed_By=Disposed_By, Verified_By=Verified_By, Remarks=Remarks)
            context = {}
            data=RoutineDisposal.objects.filter(Location=Location, Function=Function, Waste_Type=Waste_Type, Waste_State=Waste_State, Disposal_Type=Disposal_Type, Severity=Severity, Description=Description, Unit=Unit, Quantity=Quantity, Disposal_Date=Disposal_Date,)
            context['duplicateRoutine'] = data
            if data.exists():
                return render(request, 'Waste Management/Routine/Already_Exists.html', context)
            routine_input.set_user(request.user)
            routine_input.save()
            success_message = (f"Routine Waste Disposal Data For {Location} Location Entered Successfully, as Disposed on {Disposal_Date.strftime('%d-%b-%Y')}.")

            request.session['success_message'] = success_message
            return redirect(reverse('WM_Routine_Input') + '?success_message=' + success_message)
        
        else:
            success_message = request.session.pop('success_message', '')
            context = {'success_message': success_message, 
            'user_country': user_country,
            'Verifiers': sorted(list(set(Verifiers.values_list('user_name', flat=True)))),
            'UserFilter': sorted(list(set(UserFilter.values_list('user_name', flat= True)))), 
            'user_location' : user_location,
            'locations':json.dumps(Locations),
            'countries':sorted(list(set(Countries.values_list('country', flat= True))))}  
            return render (request, 'Waste Management/Routine/Routine_Disposal_Input.html', context)  

@user_passes_test(user_in_add_group)
def WM_Routine_Upload(request):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        username = request.user.username
        admin_leaders = request.user.groups.filter(name='Admin-Leaders').exists()
        superuser = request.user.is_superuser
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_location = UserLocation.user_location

        if request.method == 'POST':
            form = UploadRoutine(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES['routinefile']
                data = pd.read_excel(file)
                expected_columns = ['Disposal Date', 'Country', 'Location', 'Function', 'Item Description', 'Waste Type', 'Waste State', 'Disposal Type', 'Waste Severity', 'Unit', 'Quantity', 'Disposed By', 'Verified By', 'Remarks']
                if list(data.columns) != expected_columns or len(data.columns) != len(expected_columns):
                    error_message = f"The Upload File should have these 14 columns only: {', '.join(expected_columns)}. Please refer to Sample File below."
                    return render(request, "Waste Management/Routine/Routine_Disposal_Input.html", {'form': form, 'error_message': error_message})
                count = 0
                duplicates = [] 
                for index, row in data.iterrows():
                    date= (row['Disposal Date'])
                    obj = RoutineDisposal(
                        Disposal_Date = date,
                        Year = date.year,
                        Month = date.month,
                        Quarter = (date.month-1)//3 +1, 
                        Country= row['Country'],
                        Location= row['Location'],
                        Function= row['Function'],
                        Description= row['Item Description'],
                        Waste_Type= row['Waste Type'],
                        Waste_State= row['Waste State'],
                        Severity= row['Waste Severity'],
                        Disposal_Type= row['Disposal Type'],
                        Unit= row['Unit'],
                        Quantity= row['Quantity'],
                        Disposed_By= row['Disposed By'],
                        Verified_By= row['Verified By'],
                        Remarks= row['Remarks'])
                    context = {}
                    data = RoutineDisposal.objects.filter(Disposal_Date=obj.Disposal_Date, Location=obj.Location, Function=obj.Function, Description=obj.Description, Waste_Type=obj.Waste_Type,Waste_State=obj.Waste_State, Severity=obj.Severity, Disposal_Type=obj.Disposal_Type, Unit=obj.Unit, Quantity=obj.Quantity)

                    if data.exists():
                        duplicates.append(obj)
                    else:
                        if obj.Location != user_location and not superuser or not admin_leaders:
                            error_message = f" Invalid Location. You Are Only Authorised to Upload Data for '{user_location}' Location."
                            return render(request, "Waste Management/Routine/Routine_Disposal_Input.html", {'form': form, 'error_message': error_message})
                        else:
                            obj.set_user(request.user)
                            obj.save()
                            count += 1
                if duplicates:
                    context = {'routine_dataset': duplicates}
                    return render(request, "Waste Management/Routine/Routine_Exists_Table.html", context)
                else:
                    success_message = (f"{count} Records Uploaded Successfully.")
                    request.session['success_message'] = success_message
                    return redirect(reverse('WM_Routine_Upload') + '?success_message=' + success_message)
        else:
            form = UploadRoutine()
        success_message = request.session.pop('success_message', '')
        return render(request, 'Waste Management/Routine/Routine_Disposal_Input.html', {'form': form, 'success_message': success_message})

def WM_Routine_View(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        username = request.user.username
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_location = UserLocation.user_location
        routine_data = RoutineDisposal.objects.all().order_by('Month')
        filtered_data = routine_data.filter(Location=user_location)

        if request.user.groups.filter(name='Admin-Leaders').exists():
            routine_data = routine_data
        else:
            routine_data = filtered_data

        if not routine_data:
            return render(request, 'Waste Management/Routine/Routine_View.html', {'error_message': 'No Records To Display!'})    
        
        context = {}  
        current_data = RoutineDisposal.objects.filter(Year=datetime.today().year, Month=datetime.today().month)
        latest_report = RoutineDisposal.objects.latest('Month')
        latest_data = routine_data.filter(Month=latest_report.Month)

        if not current_data:
            routine_data = latest_data


        year = request.GET.get('year')
        quarter = request.GET.get('quarter')
        month = request.GET.get('month')
        location = request.GET.get('location')
        country = request.GET.get('country')

        if year == None and quarter==None and month == None and country==None and location == None or year == 'All' and quarter=='All' and month == 'All' and country=='All' and location == 'All':
            routine_data = current_data
        else:
            if year != 'All':
                routine_data = routine_data.filter(Year=year)
            if quarter != 'All':
                routine_data = routine_data.filter(Quarter=quarter) 
            if month != 'All':
                routine_data = routine_data.filter(Month=month)
            if country != 'All':
                routine_data = routine_data.filter(Country=country)
            if location != 'All':
                routine_data = routine_data.filter(Location=location)  

        context["routine_dataset"] = routine_data
        context["years"] = sorted(list(set(RoutineDisposal.objects.values_list('Year',  flat=True))))
        context["quarters"] = sorted(list(set(RoutineDisposal.objects.values_list('Quarter', flat=True))))
        context["months"] = sorted(list(set(RoutineDisposal.objects.values_list('Month', flat=True))))
        context["countries"] = sorted(list(set(RoutineDisposal.objects.values_list('Country', flat=True))))
        context["locations"] = sorted(list(set(RoutineDisposal.objects.values_list('Location', flat=True))))
        context["types"] = sorted(list(set(RoutineDisposal.objects.values_list('Waste_Type', flat=True))))
        return render(request, 'Waste Management/Routine/Routine_View.html', context)

@user_passes_test(user_in_leaders_group)
def Update_Routine(request, routine_data_id):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        username = request.user.username
        superuser = request.user.is_superuser
        admin_leaders = request.user.groups.filter(name='Admin-Leaders').exists()
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_country = UserLocation.user_country
        user_location = UserLocation.user_location
        UserFilter = AuthorisedUser.objects.filter(exclude_from_calculation=False) if superuser or admin_leaders else AuthorisedUser.objects.filter(user_location=user_location, exclude_from_calculation=False)
        Countries = LocationModel.objects.all()
        Locations = {}
        for country in Countries:
            if country.country not in Locations:
                Locations[country.country] = []
            Locations[country.country].append(country.location)
        for country in Locations:
            Locations[country] = sorted(list(set(Locations[country])))

        routine_data = RoutineDisposal.objects.get(id=routine_data_id)
        routine_data.Disposal_Date = routine_data.Disposal_Date.strftime('%Y-%m-%d')
        if request.method == 'POST':
            Date = datetime.strptime(request.POST.get('disposalDate'), '%Y-%m-%d')
            routine_data.Year = Date.year
            routine_data.Quarter = (Date.month-1)//3+1
            routine_data.Month = Date.month
            routine_data.Disposal_Date = Date
            routine_data.Country = request.POST.get('Country')
            routine_data.Location = request.POST.get('Location')
            routine_data.Function = request.POST.get('Function')
            routine_data.Waste_Type = request.POST.get('wasteType')
            routine_data.Waste_State = request.POST.get('wasteState')
            routine_data.Severity = request.POST.get('Severity')
            routine_data.Disposal_Type = request.POST.get('disposalType')
            routine_data.Description = request.POST.get('itemDesc')
            routine_data.Unit ='KG' if routine_data.Description.lower().__contains__('face') or routine_data.Description.lower().__contains__('mask') else request.POST.get('Unit')
            routine_data.Quantity = float(request.POST.get('Quantity'))*0.004 if routine_data.Description.lower().__contains__('face') or routine_data.Description.lower().__contains__('mask') else request.POST.get('Quantity')
            routine_data.Disposed_By = request.POST.get('disposedBy')
            routine_data.Verified_By = request.POST.get('verifiedBy')
            routine_data.Remarks = request.POST.get('Remarks')
            routine_data.set_user(request.user)
            routine_data.save()
            return redirect('Routine_View')
        context = {'routine_data': routine_data,
            'user_country': user_country,
            'user_location' : user_location,
            'locations':json.dumps(Locations),
            'UserFilter': sorted(list(set(UserFilter.values_list('user_name', flat= True)))), 
            'countries':sorted(list(set(Countries.values_list('country', flat= True))))}
        return render(request, 'Waste Management/Routine/Update_Routine_Disposal.html', context)


@user_passes_test(is_superuser)
def Delete_Routine_Disposal(request, id):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        routine_data = RoutineDisposal.objects.get(pk=id)
        routine_data.delete()
        return redirect("Routine_View")

@user_passes_test(user_in_add_group)
def WM_Non_Routine_Input(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        username = request.user.username
        superuser = request.user.is_superuser
        admin_leaders = request.user.groups.filter(name='Admin-Leaders').exists()
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_country = UserLocation.user_country
        user_location = UserLocation.user_location
        UserFilter = AuthorisedUser.objects.filter(exclude_from_calculation=False, is_manager=False) if superuser or admin_leaders else AuthorisedUser.objects.filter(user_location=user_location, exclude_from_calculation=False, is_manager=False)
        Verifiers = AuthorisedUser.objects.filter(exclude_from_calculation=False, is_manager=True) if superuser or admin_leaders else AuthorisedUser.objects.filter(user_location=user_location, exclude_from_calculation=False, is_manager=True)
       
        Countries = LocationModel.objects.all()
        Locations = {}
        for country in Countries:
            if country.country not in Locations:
                Locations[country.country] = []
            Locations[country.country].append(country.location)
        for country in Locations:
            Locations[country] = sorted(list(set(Locations[country])))

        if request.method =='POST':
            Disposal_Date = datetime.strptime(request.POST.get('disposalDate'),"%Y-%m-%d")            
            Month = Disposal_Date.month
            Quarter = (Month-1)//3+1
            Year = Disposal_Date.year
            Country = request.POST.get('Country')
            Location = request.POST.get('Location')
            Function = request.POST.get('Function')
            Disposal_Type = request.POST.get('disposalType')
            Description = request.POST.get('itemDesc')
            Category = request.POST.get('Category')
            Waste_Type = request.POST.get('wasteType')
            Waste_State = request.POST.get('wasteState')
            Severity = request.POST.get('Severity')
            Unit = request.POST.get('Unit')
            Quantity = request.POST.get('Quantity')
            Disposed_By = request.POST.get('disposedBy')
            Verified_By = request.POST.get('verifiedBy')
            Remarks = request.POST.get('Remarks')
            non_routine_input = Non_Routine_Disposal(Disposal_Date=Disposal_Date, Month=Month, Quarter=Quarter, Year=Year, Country=Country, Location=Location, Function=Function, Waste_Type=Waste_Type, Waste_State=Waste_State, Severity=Severity, Description=Description, Category=Category, Unit=Unit, Quantity=Quantity, Disposed_By=Disposed_By, Verified_By=Verified_By, Remarks=Remarks)
            context = {}
            data=Non_Routine_Disposal.objects.filter(Location=Location, Function=Function, Waste_Type=Waste_Type, Waste_State=Waste_State, Disposal_Type=Disposal_Type, Severity=Severity, Description=Description, Unit=Unit, Category=Category, Quantity=Quantity, Disposal_Date=Disposal_Date,)
            context['duplicateNonRoutine'] = data
            if data.exists():
                return render(request, 'Waste Management/Non-Routine/Already_Exists.html', context)
            non_routine_input.set_user(request.user)
            non_routine_input.save()
            success_message = (f"Non-Routine Waste Disposal Data For {Location} Location Entered Successfully, as Disposed on {Disposal_Date.strftime('%d-%b-%Y')}.")
            request.session['success_message'] = success_message
            return redirect(reverse('WM_Non_Routine_Input') + '?success_message=' + success_message)
        
        else:
            success_message = request.session.pop('success_message', '')
            context = {'success_message': success_message,
            'UserFilter': sorted(list(set(UserFilter.values_list('user_name', flat= True)))), 
            'Verifiers': sorted(list(set(Verifiers.values_list('user_name', flat=True)))),
            'user_country': user_country,
            'user_location' : user_location,
            'locations':json.dumps(Locations),
            'countries':sorted(list(set(Countries.values_list('country', flat= True))))}  
            return render (request, 'Waste Management/Non-Routine/Non_Routine_Disp_Input.html', context)

@user_passes_test(user_in_add_group)
def WM_Non_Routine_Upload(request):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        if request.method == 'POST':
            username = request.user.username
            admin_leaders = request.user.groups.filter(name='Admin-Leaders').exists()
            superuser = request.user.is_superuser
            UserLocation = AuthorisedUser.objects.get(userid=username)
            user_country = UserLocation.user_country
            user_location = UserLocation.user_location

            form = UploadNonRoutine(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES['nonroutinefile']
                df = pd.read_excel(file)
                expected_columns = ['Disposal Date', 'Country', 'Location', 'Function', 'Item Description', 'Item Category', 'Waste Type',  'Waste State', 'Disposal Type', 'Waste Severity', 'Unit', 'Quantity', 'Disposed By', 'Verified By', 'Remarks']
                if list(df.columns) != expected_columns or len(df.columns) != len(expected_columns):
                    error_message = f"The Upload File should have these 15 columns only: {', '.join(expected_columns)}. Please refer to Sample File below."
                    return render(request, "Waste Management/Non-Routine/Non_Routine_Disp_Input.html", {'form': form, 'error_message': error_message})
                count = 0
                duplicates = [] 
                for index, row in df.iterrows():
                    date= row['Disposal Date']
                    obj = Non_Routine_Disposal(
                        Year = date.year,
                        Quarter = (date.month-1)//3+1,
                        Month = date.month,
                        Disposal_Date = date,
                        Country= row['Country'],
                        Location= row['Location'],
                        Function= row['Function'],
                        Description= row['Item Description'],
                        Category = row['Item Category'],
                        Waste_Type= row['Waste Type'],
                        Waste_State= row['Waste State'],
                        Disposal_Type= row['Disposal Type'],
                        Severity= row['Waste Severity'],
                        Unit= row['Unit'],
                        Quantity= row['Quantity'],
                        Disposed_By= row['Disposed By'],
                        Verified_By= row['Verified By'],
                        Remarks= row['Remarks'])
                    context = {}
                    data = Non_Routine_Disposal.objects.filter(Disposal_Date=obj.Disposal_Date, Location=obj.Location, Function=obj.Function, Description=obj.Description, Category=obj.Category, Waste_Type=obj.Waste_Type, Waste_State=obj.Waste_State, Disposal_Type=obj.Disposal_Type, Severity=obj.Severity, Unit=obj.Unit, Quantity=obj.Quantity)

                    if data.exists():
                        duplicates.append(obj)
                    else:
                        if obj.Location == user_location and obj.Country == user_country:
                            obj.set_user(request.user)
                            obj.save()
                            count += 1
                        elif superuser or admin_leaders:
                            obj.set_user(request.user)
                            obj.save()
                            count += 1
                        else:
                            error_message = f" Invalid Location. You Are Only Authorised to Upload Data for '{user_location}' Location."
                            return render(request, "Waste Management/Non-Routine/Non_Routine_Disp_Input.html", {'form': form, 'error_message': error_message})


                grouped_data =df.groupby(['Disposal Date', 'Location']).first().reset_index()
                for index, row in grouped_data.iterrows():
                    date = row['Disposal Date']
                    year=row['Disposal Date'].year
                    month= row['Disposal Date'].month
                    quarter=(row['Disposal Date'].month-1)//3+1
                    country = row ['Country']
                    location=row['Location']
                    type='Non-Routine Waste Disposal/ Scrap Activity'
                    existing_entry = DisposalSummary.objects.filter(Date=date, Location=location, Type=type).first()
                    if existing_entry:
                        if existing_entry.Date == date and existing_entry.Location==location and existing_entry.Type==type:
                            existing_entry.Count = F('Count') + 1
                            existing_entry.save()
                    else:
                        summary_data = DisposalSummary(Date=date, Year=year, Quarter=quarter, Month=month, Country=country, Location=location, Type=type, Entered_By=request.user, Count=1)
                        summary_data.save()
                
                if duplicates:
                    context = {'non_routine_dataset': duplicates}
                    success_message = (f"{len(duplicates)} Records Already Exist.")
                    request.session['success_message'] = success_message
                    return render(request, "Waste Management/Non-Routine/Non_Routine_Exists_Table.html", context)
                    # return HttpResponse("Data Already Exists.")
                else:
                    success_message = (f"{count} Records Uploaded Successfully.")
                    request.session['success_message'] = success_message
                    return redirect(reverse('WM_Non_Routine_Upload') + '?success_message=' + success_message)
        else:
            form = UploadNonRoutine()
        success_message = request.session.pop('success_message', '')
        return render(request, 'Waste Management/Non-Routine/Non_Routine_Disp_Input.html', {'form': form, 'success_message': success_message})

def WM_Non_Routine_View(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        username = request.user.username
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_location = UserLocation.user_location
        non_routine_data = Non_Routine_Disposal.objects.all().order_by('Month')
        filtered_data = non_routine_data.filter(Location=user_location)

        if request.user.groups.filter(name='Admin-Leaders').exists():
            non_routine_data = non_routine_data
        else:
            non_routine_data = filtered_data

        if not non_routine_data:
            return render(request, 'Waste Management/Non-Routine/Non_Routine_View.html', {'error_message': 'No Records To Display!'})    
        
        context = {} 
        current_data = Non_Routine_Disposal.objects.filter(Year=datetime.today().year, Month=datetime.today().month) 
        latest_report = Non_Routine_Disposal.objects.latest('Month')
        latest_data = non_routine_data.filter(Month=latest_report.Month)

        if not current_data:
            non_routine_data = latest_data

        year = request.GET.get('year')
        quarter = request.GET.get('quarter')
        month = request.GET.get('month')
        location = request.GET.get('location')
        country = request.GET.get('country')

        if year == None and quarter==None and month == None and country==None and location == None:
            non_routine_data = latest_data
        elif year == 'All' and quarter=='All' and month == 'All' and country=='All' and location == 'All':
            non_routine_data = latest_data
        else:
            if year != 'All':
                non_routine_data = non_routine_data.filter(Year=year)
            if quarter != 'All':
                non_routine_data = non_routine_data.filter(Quarter=quarter) 
            if month != 'All':
                non_routine_data = non_routine_data.filter(Month=month)
            if country != 'All':
                non_routine_data = non_routine_data.filter(Country=country)
            if location != 'All':
                non_routine_data = non_routine_data.filter(Location=location)  

        context["non_routine_dataset"] = non_routine_data
        context["years"] = sorted(list(set(Non_Routine_Disposal.objects.values_list('Year',  flat=True))))
        context["quarters"] = sorted(list(set(Non_Routine_Disposal.objects.values_list('Quarter', flat=True))))
        context["months"] = sorted(list(set(Non_Routine_Disposal.objects.values_list('Month', flat=True))))
        context["countries"] = sorted(list(set(Non_Routine_Disposal.objects.values_list('Country', flat=True))))
        context["locations"] = sorted(list(set(Non_Routine_Disposal.objects.values_list('Location', flat=True))))

        return render(request, 'Waste Management/Non-Routine/Non_Routine_View.html', context)

@user_passes_test(user_in_leaders_group)
def Update_Non_Routine(request, non_routine_data_id):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        username = request.user.username
        superuser = request.user.is_superuser
        admin_leaders = request.user.groups.filter(name='Admin-Leaders').exists()
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_country = UserLocation.user_country
        user_location = UserLocation.user_location
        UserFilter = AuthorisedUser.objects.filter(exclude_from_calculation=False) if superuser or admin_leaders else AuthorisedUser.objects.filter(user_location=user_location, exclude_from_calculations=False)
        Countries = LocationModel.objects.all()
        Locations = {}
        for country in Countries:
            if country.country not in Locations:
                Locations[country.country] = []
            Locations[country.country].append(country.location)
        for country in Locations:
            Locations[country] = sorted(list(set(Locations[country])))

        non_routine_data = Non_Routine_Disposal.objects.get(id=non_routine_data_id)
        non_routine_data.Disposal_Date = non_routine_data.Disposal_Date.strftime("%Y-%m-%d")
        if request.method == 'POST':
            Date = datetime.strptime(request.POST.get('disposalDate'), '%Y-%m-%d')
            non_routine_data.Year = Date.year
            non_routine_data.Quarter = (Date.month-1)//3 +1
            non_routine_data.Month = Date.month
            non_routine_data.Disposal_Date = Date
            non_routine_data.Country = request.POST.get('Country')
            non_routine_data.Location = request.POST.get('Location')
            non_routine_data.Function = request.POST.get('Function')
            non_routine_data.Description = request.POST.get('itemDesc')
            non_routine_data.Waste_Type = request.POST.get('wasteType')
            non_routine_data.Waste_State = request.POST.get('wasteState')
            non_routine_data.Severity = request.POST.get('Severity')
            non_routine_data.Disposal_Type = request.POST.get('disposalType')
            non_routine_data.Unit = request.POST.get('Unit')
            non_routine_data.Quantity = request.POST.get('Quantity')
            non_routine_data.Disposed_By = request.POST.get('disposedBy')
            non_routine_data.Verified_By = request.POST.get('verifiedBy')
            non_routine_data.Remarks = request.POST.get('Remarks')
            non_routine_data.set_user(request.user)
            non_routine_data.save()
            return redirect('Non_Routine_View')
        context = {'non_routine_data': non_routine_data,
            'UserFilter': sorted(list(set(UserFilter.values_list('user_name', flat= True)))), 
            'user_country': user_country,
            'user_location' : user_location,
            'locations':json.dumps(Locations),
            'countries':sorted(list(set(Countries.values_list('country', flat= True))))}
        return render(request, 'Waste Management/Non-Routine/Update_Non_Routine_Disp.html', context)

@user_passes_test(is_superuser)
def Delete_Non_Routine_Disposal(request, id):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        non_routine_data = Non_Routine_Disposal.objects.get(pk=id)
        non_routine_data.delete()
        return redirect("Non_Routine_View")

@user_passes_test(user_in_add_group) 
def WM_EWaste_Input(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        username = request.user.username
        superuser = request.user.is_superuser
        admin_leaders = request.user.groups.filter(name='Admin-Leaders').exists()
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_country = UserLocation.user_country
        user_location = UserLocation.user_location
        UserFilter = AuthorisedUser.objects.filter(exclude_from_calculation=False) if superuser or admin_leaders else AuthorisedUser.objects.filter(user_location=user_location, exclude_from_calculation=False)
        Countries = LocationModel.objects.all()
        Locations = {}
        for country in Countries:
            if country.country not in Locations:
                Locations[country.country] = []
            Locations[country.country].append(country.location)
        for country in Locations:
            Locations[country] = sorted(list(set(Locations[country])))
        if request.method =='POST':
            Disposal_Date = datetime.strptime(request.POST.get('disposalDate'), '%Y-%m-%d')
            Month = Disposal_Date.month
            Quarter = (Month-1)//3+1
            Year = Disposal_Date.year
            Country = request.POST.get('Country')
            Location = request.POST.get('Location')
            Function = request.POST.get('Function')
            Description = request.POST.get('itemDesc')
            Category = request.POST.get('Category')
            Disposal_Type = request.POST.get('disposalType')           
            Severity = request.POST.get('Severity')
            Unit = request.POST.get('Unit')
            Quantity = request.POST.get('Quantity')
            Disposed_By = request.POST.get('disposedBy')
            Verified_By = request.POST.get('verifiedBy')
            Remarks = request.POST.get('Remarks')
            e_waste_input = E_Waste_Disposal(Disposal_Date=Disposal_Date, Month=Month, Quarter=Quarter, Year=Year, Country=Country, Location=Location, Function=Function, Description=Description, Disposal_Type=Disposal_Type, Category=Category, Severity=Severity, Unit=Unit, Quantity=Quantity, Disposed_By=Disposed_By, Verified_By=Verified_By, Remarks=Remarks)
            context = {}
            data=E_Waste_Disposal.objects.filter(Location=Location, Function=Function, Disposal_Type=Disposal_Type, Severity=Severity, Description=Description, Unit=Unit,  Category=Category, Quantity=Quantity, Disposal_Date=Disposal_Date,)
            context['duplicateE_Waste'] = data
            if data.exists():
                return render(request, 'Waste Management/Non-Routine/Already_Exists.html', context)
            e_waste_input.set_user(request.user)
            e_waste_input.save()
            success_message = (f"E-Waste Disposal Data For {Location} Location Entered Successfully, as Disposed on {Disposal_Date.strftime('%d-%b-%Y')}.")
            request.session['success_message'] = success_message
            return redirect(reverse('WM_EWaste_Input') + '?success_message=' + success_message)
        
        else:
            success_message = request.session.pop('success_message', '')
            context = {'success_message': success_message, 
            'user_country': user_country,
            'user_location' : user_location,
            'locations':json.dumps(Locations),
            'UserFilter':sorted(list(set(UserFilter.values_list('user_name', flat= True)))),
            'countries':sorted(list(set(Countries.values_list('country', flat= True))))}  
            return render (request, 'Waste Management/E-Waste/E-Waste_Disposal_Input.html', context)
    
@user_passes_test(user_in_add_group)
def WM_EWaste_Upload(request):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        username = request.user.username
        admin_leaders = request.user.groups.filter(name='Admin-Leaders').exists()
        superuser = request.user.is_superuser
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_country = UserLocation.user_country
        user_location = UserLocation.user_location
        if request.method == 'POST':
            form = UploadEWaste(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES['ewastefile']
                df = pd.read_excel(file)
                expected_columns = ['Disposal Date', 'Country', 'Location', 'Function', 'Item Description', 'Item Category', 'Disposal Type', 'Waste Severity', 'Unit', 'Quantity', 'Disposed By', 'Verified By', 'Remarks']
                if list(df.columns) != expected_columns or len(df.columns) != len(expected_columns):
                    error_message = f"The Upload File should have these 13 columns only: {', '.join(expected_columns)}. Please refer to Sample File below."
                    return render(request, "Waste Management/E-Waste/E-Waste_Disposal_Input.html", {'form': form, 'error_message': error_message})
                count = 0
                duplicates = []

                for index, row in df.iterrows():
                    date= row['Disposal Date']
                    obj = E_Waste_Disposal(
                        Year = date.year,
                        Quarter = (date.month-1)//3+1,
                        Month = date.month,
                        Disposal_Date = date,
                        Country= row['Country'],
                        Location= row['Location'],
                        Function= row['Function'],
                        Description= row['Item Description'],
                        Category = row['Item Category'],
                        Disposal_Type= row['Disposal Type'],
                        Severity= row['Waste Severity'],
                        Unit= row['Unit'],
                        Quantity= row['Quantity'],
                        Disposed_By= row['Disposed By'],
                        Verified_By= row['Verified By'],
                        Remarks= row['Remarks'])
                    context = {}
                    data = E_Waste_Disposal.objects.filter(Disposal_Date=obj.Disposal_Date, Location=obj.Location, Function=obj.Function, Description=obj.Description, Category=obj.Category, Disposal_Type=obj.Disposal_Type, Severity=obj.Severity, Unit=obj.Unit, Quantity=obj.Quantity)

                    if data.exists():
                        duplicates.append(obj)
                    else:
                        if obj.Location == user_location and obj.Country == user_country:
                            obj.set_user(request.user)
                            obj.save()
                            count += 1
                        elif superuser or admin_leaders:
                            obj.set_user(request.user)
                            obj.save()
                            count += 1
                        else:
                            error_message = f" Invalid Location. You Are Only Authorised to Upload Data for '{user_location}' Location."
                            return render(request, "Waste Management/E-Waste/E-Waste_Disposal_Input.html", {'form': form, 'error_message': error_message})
                        
                grouped_data =df.groupby(['Disposal Date', 'Location']).first().reset_index()
                for index, row in grouped_data.iterrows():
                    date = row['Disposal Date']
                    year=row['Disposal Date'].year
                    month= row['Disposal Date'].month
                    quarter=(row['Disposal Date'].month-1)//3+1
                    country = row ['Country']
                    location=row['Location']
                    type='E-Waste Disposal/ Scrap Activity'
                    existing_entry = DisposalSummary.objects.filter(Date=date, Location=location, Type=type).first()
                    if existing_entry:
                        if existing_entry.Date == date and existing_entry.Location==location and existing_entry.Type==type:
                            existing_entry.Count = F('Count') + 1
                            existing_entry.save()
                    else:
                        summary_data = DisposalSummary(Date=date, Year=year, Quarter=quarter, Month=month, Country=country, Location=location, Type=type, Entered_By=request.user, Count=1)
                        summary_data.save()
                if duplicates:
                    context = {'e_waste_dataset': duplicates}
                    success_message = (f"{len(duplicates)} Records Already Exist.")
                    request.session['success_message'] = success_message
                    return render(request, "Waste Management/E-Waste/E-Waste_Exists_Table.html", context)
                else:
                    success_message = (f"{count} Records Uploaded Successfully.")
                    request.session['success_message'] = success_message
                    return redirect(reverse('WM_EWaste_Upload') + '?success_message=' + success_message)
        else:
            form = UploadNonRoutine()
        success_message = request.session.pop('success_message', '')
        return render(request, 'Waste Management/E-Waste/E-Waste_Disposal_Input.html', {'form': form, 'success_message': success_message})
    
def WM_E_Waste_View(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        username = request.user.username
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_location = UserLocation.user_location
        e_waste_data = E_Waste_Disposal.objects.all().order_by('Month')
        filtered_data = e_waste_data.filter(Location=user_location)

        if request.user.groups.filter(name='Admin-Leaders').exists():
            e_waste_data = e_waste_data
        else:
            e_waste_data = filtered_data

        if not e_waste_data:
            return render(request, 'Waste Management/E-Waste/E-Waste_View.html', {'error_message': 'No Records To Display!'})    
        
        context = {}
        current_data = E_Waste_Disposal.objects.filter(Year=datetime.today().year, Month=datetime.today().month)  
        latest_report = E_Waste_Disposal.objects.latest('Month')
        latest_data = e_waste_data.filter(Month=latest_report.Month)

        if not current_data:
            e_waste_data = latest_data

        year = request.GET.get('year')
        quarter = request.GET.get('quarter')
        month = request.GET.get('month')
        location = request.GET.get('location')
        country = request.GET.get('country')

        if year == None and quarter==None and month == None and country==None and location == None:
            e_waste_data = latest_data
        elif year == 'All' and quarter=='All' and month == 'All' and country=='All' and location == 'All':
            e_waste_data = e_waste_data
        else:
            if year != 'All':
                e_waste_data = e_waste_data.filter(Year=year)
            if quarter != 'All':
                e_waste_data = e_waste_data.filter(Quarter=quarter) 
            if month != 'All':
                e_waste_data = e_waste_data.filter(Month=month)
            if country != 'All':
                e_waste_data = e_waste_data.filter(Country=country)
            if location != 'All':
                e_waste_data = e_waste_data.filter(Location=location)  


        context["e_waste_dataset"] = e_waste_data
        context["years"] = sorted(list(set(E_Waste_Disposal.objects.values_list('Year',  flat=True))))
        context["quarters"] = sorted(list(set(E_Waste_Disposal.objects.values_list('Quarter', flat=True))))
        context["months"] = sorted(list(set(E_Waste_Disposal.objects.values_list('Month', flat=True))))
        context["countries"] = sorted(list(set(E_Waste_Disposal.objects.values_list('Country', flat=True))))
        context["locations"] = sorted(list(set(E_Waste_Disposal.objects.values_list('Location', flat=True))))

        return render(request, 'Waste Management/E-Waste/E-Waste_View.html', context)

@user_passes_test(user_in_leaders_group)
def Update_E_Waste(request, e_waste_data_id):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        username = request.user.username
        superuser = request.user.is_superuser
        admin_leaders = request.user.groups.filter(name='Admin-Leaders').exists()
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_country = UserLocation.user_country
        user_location = UserLocation.user_location
        UserFilter = AuthorisedUser.objects.filter(exclude_from_calculation=False) if superuser or admin_leaders else AuthorisedUser.objects.filter(user_location=user_location, exclude_from_calculation=False)
        Countries = LocationModel.objects.all()
        Locations = {}
        for country in Countries:
            if country.country not in Locations:
                Locations[country.country] = []
            Locations[country.country].append(country.location)
        for country in Locations:
            Locations[country] = sorted(list(set(Locations[country])))

        e_waste_data = E_Waste_Disposal.objects.get(id=e_waste_data_id)
        e_waste_data.Disposal_Date = e_waste_data.Disposal_Date.strftime('%Y-%m-%d')
        if request.method == 'POST':
            date = datetime.strptime(request.POST.get('disposalDate'), '%Y-%m-%d')
            e_waste_data.Year = date.year
            e_waste_data.Quarter = (date.month-1)//3+1
            e_waste_data.Month = date.month
            e_waste_data.Disposal_Date = date
            e_waste_data.Country = request.POST.get('Country')
            e_waste_data.Location = request.POST.get('Location')
            e_waste_data.Function = request.POST.get('Function')
            e_waste_data.Description = request.POST.get('itemDesc')
            e_waste_data.Severity = request.POST.get('Severity')
            e_waste_data.Disposal_Type = request.POST.get('disposalType')
            e_waste_data.Unit = request.POST.get('Unit')
            e_waste_data.Quantity = request.POST.get('Quantity')
            e_waste_data.Disposed_By = request.POST.get('disposedBy')
            e_waste_data.Verified_By = request.POST.get('verifiedBy')
            e_waste_data.Remarks = request.POST.get('Remarks')
            e_waste_data.set_user(request.user)
            e_waste_data.save()
            return redirect('E_Waste_View')
        context = {'e_waste_data': e_waste_data,
            'user_country': user_country,
            'user_location' : user_location,
            'locations':json.dumps(Locations),
            'UserFilter':sorted(list(set(UserFilter.values_list('user_name', flat= True)))),
            'countries':sorted(list(set(Countries.values_list('country', flat= True))))}
        return render(request, 'Waste Management/E-Waste/Update_E-Waste_Disp.html', context)

@user_passes_test(is_superuser)
def Delete_E_Waste(request, id):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        non_routine_data = E_Waste_Disposal.objects.get(pk=id)
        non_routine_data.delete()
        return redirect("E_Waste_View")

def ESG_Input(request):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        username = request.user.username
        superuser = request.user.is_superuser
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_country = UserLocation.user_country
        user_location = UserLocation.user_location
        UserFilter = AuthorisedUser.objects.all() if superuser else AuthorisedUser.objects.filter(user_location=user_location)
        Countries = LocationModel.objects.all()
        Locations = {}
        for country in Countries:
            if country.country not in Locations:
                Locations[country.country] = []
            Locations[country.country].append(country.location)
        for country in Locations:
            Locations[country] = sorted(list(set(Locations[country])))

        if request.method =='POST':
            Month = datetime.strptime(request.POST.get('disposalMonth'), '%Y-%m').month
            Year = datetime.strptime(request.POST.get('disposalMonth'), '%Y-%m').year
            Quarter = (Month-1)//3 +1
            Country = request.POST.get('Country')
            Location = request.POST.get('Location')
            Function = request.POST.get('Function')
            Description = request.POST.get('itemDesc')
            Category = request.POST.get('Category')
            Type = request.POST.get('Type')           
            Severity = request.POST.get('Severity')
            Unit = request.POST.get('Unit')
            Quantity = request.POST.get('Quantity')
            Entered_By = request.user
            Remarks = request.POST.get('Remarks')
            ESG_Evidence1 = request.FILES.get('evidence1')
            ESG_Evidence2 = request.FILES.get('evidence2')
            ESG_Evidence3 = request.FILES.get('evidence3')
            ESG_Evidence4 = request.FILES.get('evidence4')
            esg_input = ESG( Month=Month, Quarter=Quarter, Year=Year, Country=Country, Location=Location, Function=Function, Description=Description, Type=Type, Category=Category, Severity=Severity, Unit=Unit, Quantity=Quantity, Entered_By=Entered_By, Remarks=Remarks, ESG_Evidence1=ESG_Evidence1, ESG_Evidence2=ESG_Evidence2, ESG_Evidence3=ESG_Evidence3, ESG_Evidence4=ESG_Evidence4)
            context = {}
            data=ESG.objects.filter(Location=Location, Function=Function, Type=Type, Severity=Severity, Description=Description, Unit=Unit, Category=Category, Quantity=Quantity, Month=Month)
            context['duplicateESG'] = data
            if data.exists():
                return render(request, 'Waste Management/ESG/Already_Exists.html', context)
            esg_input.save()
            success_message = (f"ESG Data For {Location} Location Entered Successfully,for the Month of {custom_filters.get_month_name(Month)}-{Year}.")
            request.session['success_message'] = success_message
            return redirect(reverse('ESG_Input') + '?success_message=' + success_message)
        
        else:
            success_message = request.session.pop('success_message', '')
        context = {'success_message': success_message,
            'user_country': user_country,
            'user_location' : user_location,
            'locations':json.dumps(Locations),
            'UserFilter':sorted(list(set(UserFilter.values_list('user_name', flat= True)))),
            'countries':sorted(list(set(Countries.values_list('country', flat= True))))}  

        return render(request, 'Waste Management/ESG/ESG_Input.html', context)

def ESG_Data(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        username = request.user.username
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_location = UserLocation.user_location
        esg_data = ESG.objects.all().order_by('Month')
        filtered_data = esg_data.filter(Location=user_location)

        if request.user.groups.filter(name='Admin-Leaders').exists():
            esg_data = esg_data
        else:
            esg_data = filtered_data

        if not esg_data:
            return render(request, 'Waste Management/ESG/ESG_Data.html', {'error_message': 'No Records To Display!'})    
        
        context = {}  
        latest_report = ESG.objects.latest('Month')
        latest_data = esg_data.filter(Month=latest_report.Month, Year=latest_report.Year)

        year = request.GET.get('year')
        quarter = request.GET.get('quarter')
        month = request.GET.get('month')
        location = request.GET.get('location')
        country = request.GET.get('country')

        if year == None and quarter==None and month == None and country==None and location == None:
            esg_data = latest_data
        elif year == 'All' and quarter=='All' and month == 'All' and country=='All' and location == 'All':
            esg_data = esg_data
        else:
            if year != 'All':
                esg_data = esg_data.filter(Year=year)
            if quarter != 'All':
                esg_data = esg_data.filter(Quarter=quarter) 
            if month != 'All':
                esg_data = esg_data.filter(Month=month)
            if country != 'All':
                esg_data = esg_data.filter(Country=country)
            if location != 'All':
                esg_data = esg_data.filter(Location=location)   

        context["esg_dataset"] = esg_data
        context["years"] = sorted(list(set(ESG.objects.values_list('Year',  flat=True))))
        context["quarters"] = sorted(list(set(ESG.objects.values_list('Quarter', flat=True))))
        context["months"] = sorted(list(set(ESG.objects.values_list('Month', flat=True))))
        context["countries"] = sorted(list(set(ESG.objects.values_list('Country', flat=True))))
        context["locations"] = sorted(list(set(ESG.objects.values_list('Location', flat=True))))

        return render(request, 'Waste Management/ESG/ESG_Data.html', context)

def Update_ESG(request, esg_id):
        if request.user.is_anonymous:
            return redirect('/login')
        else:
            username = request.user.username
            superuser = request.user.is_superuser
            admin_leaders = request.user.groups.filter(name='Admin-Leaders').exists()
            UserLocation = AuthorisedUser.objects.get(userid=username)
            user_country = UserLocation.user_country
            user_location = UserLocation.user_location
            UserFilter = AuthorisedUser.objects.filter(exclude_from_calculation=False) if superuser or admin_leaders else AuthorisedUser.objects.filter(user_location=user_location, exclude_from_calculation=False)
            Countries = LocationModel.objects.all()
            Locations = {}
            for country in Countries:
                if country.country not in Locations:
                    Locations[country.country] = []
                Locations[country.country].append(country.location)
            for country in Locations:
                Locations[country] = sorted(list(set(Locations[country])))

            esg_data = ESG.objects.get(id=esg_id)
            if request.method == 'POST':
                esg_data.Month = datetime.strptime(request.POST.get('disposalMonth'), '%Y-%m').month
                esg_data.Year = datetime.strptime(request.POST.get('disposalMonth'), '%Y-%m').year
                esg_data.Quarter = (esg_data.Month-1)//3 +1
                esg_data.Country = request.POST.get('Country')
                esg_data.Location = request.POST.get('Location')
                esg_data.Function = request.POST.get('Function')
                esg_data.Description = request.POST.get('itemDesc')
                esg_data.Category = request.POST.get('Category')
                esg_data.Type = request.POST.get('disposalType')           
                esg_data.Severity = request.POST.get('Severity')
                esg_data.Unit = request.POST.get('Unit')
                esg_data.Quantity = request.POST.get('Quantity')
                esg_data.Entered_By = request.user
                esg_data.Remarks = request.POST.get('Remarks')                
                new_evidence1 = request.FILES.get('evidence1')
                new_evidence2 = request.FILES.get('evidence2')
                new_evidence3 = request.FILES.get('evidence3')
                new_evidence4 = request.FILES.get('evidence4')

                for field in ['ESG_Evidence1', 'ESG_Evidence2', 'ESG_Evidence3', 'ESG_Evidence4']:
                    old_file = getattr(esg_data, field)
                    if old_file:
                        file_path = old_file.path
                        if os.path.exists(file_path):
                            os.remove(file_path)

                if new_evidence1:
                    esg_data.ESG_Evidence1 = new_evidence1
                if new_evidence2:
                    esg_data.ESG_Evidence2 = new_evidence2
                if new_evidence3:
                    esg_data.ESG_Evidence3 = new_evidence3
                if new_evidence4:
                    esg_data.ESG_Evidence4 = new_evidence4                 
                esg_data.Updated_By = request.user
                esg_data.Verified = False
                esg_data.Verified_By = None
                esg_data.save()     
                return redirect('ESG_Data')
            
            esg_data.Month = f'{esg_data.Year}-{esg_data.Month}' if esg_data.Month >= 10 else f'{esg_data.Year}-0{esg_data.Month}'
            context = {'esg_data': esg_data,
                'user_country': user_country,
                'user_location' : user_location,
                'locations':json.dumps(Locations),
                'UserFilter':sorted(list(set(UserFilter.values_list('user_name', flat= True)))),
                'countries':sorted(list(set(Countries.values_list('country', flat= True))))}
            return render(request, 'Waste Management/ESG/Update_ESG.html', context)

@user_passes_test(is_superuser)
def Delete_ESG(request, id):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        esg_data = ESG.objects.get(pk=id)
        esg_data.delete()
        return redirect("ESG_Data")


def ESG_Details(request, esg_id):
        if request.user.is_anonymous:
            return redirect('/login')
        else:
            username = request.user.username
            superuser = request.user.is_superuser
            admin_leaders = request.user.groups.filter(name='Admin-Leaders').exists()
            UserLocation = AuthorisedUser.objects.get(userid=username)
            user_country = UserLocation.user_country
            user_location = UserLocation.user_location
            UserFilter = AuthorisedUser.objects.filter(exclude_from_calculation=False) if superuser or admin_leaders else AuthorisedUser.objects.filter(user_location=user_location, exclude_from_calculation=False)
            Countries = LocationModel.objects.all()
            Locations = {}
            for country in Countries:
                if country.country not in Locations:
                    Locations[country.country] = []
                Locations[country.country].append(country.location)
            for country in Locations:
                Locations[country] = sorted(list(set(Locations[country])))

            esg_data = ESG.objects.get(id=esg_id)
            if request.method == 'POST':
                esg_data.Verified = True
                esg_data.Verified_By = request.user
                esg_data.save()
                success_message = (f"E-Waste Disposal Data For {esg_data.Location} Location Entered Successfully for the month of {custom_filters.get_month_name(esg_data.Month)}-{esg_data.Year}.")
                request.session['success_message'] = success_message
                return redirect(reverse('ESG_Data') + '?success_message=' + success_message)
            else:
                success_message = request.session.pop('success_message', '')
                context = {'esg_data': esg_data,
                    'user_country': user_country,
                    'user_location' : user_location,
                    'locations':json.dumps(Locations),
                    'UserFilter':sorted(list(set(UserFilter.values_list('user_name', flat= True)))),
                    'countries':sorted(list(set(Countries.values_list('country', flat= True))))}
            return render(request, 'Waste Management/ESG/ESG_Details.html', context)

def Disp_Summary_Data(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        username = request.user.username
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_location = UserLocation.user_location
        summary_data = DisposalSummary.objects.all().order_by('Month')
        filtered_data = summary_data.filter(Location=user_location)

        if request.user.groups.filter(name='Admin-Leaders').exists():
            summary_data = summary_data
        else:
            summary_data = filtered_data
        if not summary_data:
            return render(request, 'Waste Management/Summary/Summary_View_Table.html', {'error_message': 'No Records To Display!'})    
        

        context = {}  
        latest_report = DisposalSummary.objects.latest('Date')
        latest_date = latest_report.Date
        latest_data = summary_data.filter(Date=latest_date)

        year = request.GET.get('year')
        quarter = request.GET.get('quarter')
        month = request.GET.get('month')
        location = request.GET.get('location')
        country = request.GET.get('country')

        if year == None and quarter==None and month == None and country==None and location == None or year == 'All' and quarter=='All' and month == 'All' and country=='All' and location == 'All':
            summary_data = latest_data
        else:
            if year != 'All':
                summary_data = summary_data.filter(Year=year)
            if quarter != 'All':
                summary_data = summary_data.filter(Quarter=quarter) 
            if month != 'All':
                summary_data = summary_data.filter(Month=month)
            if country != 'All':
                summary_data = summary_data.filter(Country=country)
            if location != 'All':
                summary_data = summary_data.filter(Location=location)  

        summary_dataset = summary_data.select_related('Entered_By', 'Verified_By')\
            .values('Entered_By__first_name',
                    'Entered_By__last_name',
                    'Entered_By__username',
                    'Verified_By__first_name',
                    'Verified_By__last_name',
                    'Verified_By__username', 
                    'UID', 'Year', 'Quarter', 'Month', 'Date', 'Country', 'Location', 'Type', 'Verified', 'Evidence1',                
                    )

        for row in summary_dataset:
            non_routine_count = Non_Routine_Disposal.objects.filter(Disposal_Date=row['Date'], Location=row['Location']).count()
            e_waste_count = E_Waste_Disposal.objects.filter(Disposal_Date=row['Date'], Location=row['Location']).count()
            row['Items'] = non_routine_count if row['Type'] == 'Non-Routine Waste Disposal/ Scrap Activity' else e_waste_count

        context["summary_dataset"] = summary_dataset
        context["years"] = sorted(list(set(DisposalSummary.objects.values_list('Year',  flat=True))))
        context["quarters"] = sorted(list(set(DisposalSummary.objects.values_list('Quarter', flat=True))))
        context["months"] = sorted(list(set(DisposalSummary.objects.values_list('Month', flat=True))))
        context["countries"] = sorted(list(set(DisposalSummary.objects.values_list('Country', flat=True))))
        context["locations"] = sorted(list(set(DisposalSummary.objects.values_list('Location', flat=True))))

        return render(request, 'Waste Management/Summary/Summary_View_Table.html', context)    

def Upload_Evidences(request, disp_id):
        if request.user.is_anonymous:
            return redirect('/login')
        else:
            username = request.user.username
            superuser = request.user.is_superuser
            admin_leaders = request.user.groups.filter(name='Admin-Leaders').exists()
            UserLocation = AuthorisedUser.objects.get(userid=username)
            user_country = UserLocation.user_country
            user_location = UserLocation.user_location
            UserFilter = AuthorisedUser.objects.filter(exclude_from_calculation=False) if superuser or admin_leaders else AuthorisedUser.objects.filter(user_location=user_location, exclude_from_calculation=False)
            Countries = LocationModel.objects.all()
            Locations = {}
            for country in Countries:
                if country.country not in Locations:
                    Locations[country.country] = []
                Locations[country.country].append(country.location)
            for country in Locations:
                Locations[country] = sorted(list(set(Locations[country])))

            summary_data = DisposalSummary.objects.get(UID=disp_id)
            waste_type = None
            if summary_data.Type=="Non-Routine Waste Disposal/ Scrap Activity":
                disp_details = Non_Routine_Disposal.objects.filter(Location=summary_data.Location, Disposal_Date=summary_data.Date)
                waste_type= True
            else:
                disp_details = E_Waste_Disposal.objects.filter(Location=summary_data.Location, Disposal_Date=summary_data.Date)
                waste_type= False

            if request.method == 'POST':
                new_evidence1 = request.FILES.get('evidence1')
                new_evidence2 = request.FILES.get('evidence2')
                new_evidence3 = request.FILES.get('evidence3')
                new_evidence4 = request.FILES.get('evidence4')

                for field in ['Evidence1', 'Evidence2', 'Evidence3', 'Evidence4']:
                    old_file = getattr(summary_data, field)
                    if old_file:
                        file_path = old_file.path
                        if os.path.exists(file_path):
                            os.remove(file_path)

                if new_evidence1:
                    summary_data.Evidence1 = new_evidence1
                if new_evidence2:
                    summary_data.Evidence2 = new_evidence2
                if new_evidence3:
                    summary_data.Evidence3 = new_evidence3
                if new_evidence4:
                    summary_data.Evidence4 = new_evidence4                 
                summary_data.Updated_By = request.user
                summary_data.Verified = False
                summary_data.Verified_By = None
                summary_data.save()     
   
                return redirect('Disp_Details', disp_id=disp_id)
            
            context = {'summary_data': summary_data,
                    'disp_details': disp_details, 
                    'waste_type':waste_type,
                'user_country': user_country,
                'user_location' : user_location,
                'locations':json.dumps(Locations),
                'UserFilter':sorted(list(set(UserFilter.values_list('user_name', flat= True)))),
                'countries':sorted(list(set(Countries.values_list('country', flat= True))))}
            return render(request, 'Waste Management/Summary/Upload_Evidences.html', context)

def Disp_Details(request, disp_id):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        summary_data = DisposalSummary.objects.get(UID=disp_id)
        waste_type = None
        if summary_data.Type=="Non-Routine Waste Disposal/ Scrap Activity":
            disp_details = Non_Routine_Disposal.objects.filter(Location=summary_data.Location, Disposal_Date=summary_data.Date)
            waste_type= True
        else:
            disp_details = E_Waste_Disposal.objects.filter(Location=summary_data.Location, Disposal_Date=summary_data.Date)
            waste_type= False
        if request.method == 'POST':
            summary_data.Verified = True
            summary_data.Verified_By = request.user
            summary_data.save()
        
            return redirect('Disp_Summary_Data')
        context = {
            'summary_data' : summary_data,
            'disp_details': disp_details, 
            'waste_type':waste_type
        }
        return render (request, 'Waste Management/Summary/View_Disposal_Details.html', context)

def Waste_Management_Report(request):
    if request.user.is_anonymous:
            return redirect('/login')             
    else:
        try:
            routine_data = RoutineDisposal.objects.all()
            non_routine_data = Non_Routine_Disposal.objects.all()
            e_waste_data = E_Waste_Disposal.objects.all()
            esg_data = ESG.objects.all()


        except RoutineDisposal.DoesNotExist:
            routine_data = None
        except Non_Routine_Disposal.DoesNotExist:
            non_routine_data = None
        except E_Waste_Disposal.DoesNotExist:
            e_waste_data = None
        except ESG.DoesNotExist:
            esg_data = None


        if not routine_data and not non_routine_data and not e_waste_data:
            return render(request, 'Charts/WMP_Report.html', {'error_message': 'No Records To Display!'})
            
        R_YoY = routine_data
        NR_YoY = non_routine_data
        EW_YoY = e_waste_data
        ESG_YoY = esg_data  

        context = {}
           
        current_year = datetime.today().year
        R_latest_data = routine_data.filter(Year=current_year)
        NR_latest_data = non_routine_data.filter(Year=current_year)
        EW_latest_data = e_waste_data.filter(Year=current_year)
        ESG_latest_data = esg_data.filter(Year=current_year)

        year = request.GET.get('year')
        quarter = request.GET.get('quarter')
        month = request.GET.get('month')
        location = request.GET.get('location')
        # category = request.GET.get('category')

        try:
            if year == None and quarter == None and month == None  and location == None  or year == 'All' and  quarter == 'All' and month == 'All' and location == 'All':
                routine_data = R_latest_data
                non_routine_data = NR_latest_data
                e_waste_data = EW_latest_data
                esg_data = ESG_latest_data
            else:
                if year != 'All':
                    routine_data = routine_data.filter(Year = year)
                    non_routine_data = non_routine_data.filter(Year = year)
                    e_waste_data = e_waste_data.filter(Year = year)
                    esg_data = esg_data.filter(Year = year)

                if quarter != 'All':
                    routine_data = routine_data.filter(Quarter = quarter)
                    non_routine_data = non_routine_data.filter(Quarter = quarter)
                    e_waste_data = e_waste_data.filter(Quarter = quarter)
                    esg_data = esg_data.filter(Quarter = quarter)
                    R_YoY = R_YoY.filter(Quarter = quarter)
                    NR_YoY = NR_YoY.filter(Quarter = quarter)
                    EW_YoY = EW_YoY.filter(Quarter = quarter)
                    ESG_YoY = ESG_YoY.filter(Quarter = quarter)

                if month != 'All':
                    routine_data = routine_data.filter(Month=month)
                    non_routine_data = non_routine_data.filter(Month=month)
                    e_waste_data = e_waste_data.filter(Month=month)
                    esg_data = esg_data.filter(Month=month)
                    R_YoY = R_YoY.filter(Month=month)
                    NR_YoY = NR_YoY.filter(Month=month)
                    EW_YoY = EW_YoY.filter(Month=month)
                    ESG_YoY = ESG_YoY.filter(Month=month)

                if location != 'All':
                    routine_data = routine_data.filter(Location=location)
                    non_routine_data = non_routine_data.filter(Location=location)
                    e_waste_data = e_waste_data.filter(Location=location)
                    esg_data = esg_data.filter(Location=location)
                    R_YoY = R_YoY.filter(Location=location)
                    NR_YoY = NR_YoY.filter(Location=location)
                    EW_YoY = EW_YoY.filter(Location=location)
                    ESG_YoY = ESG_YoY.filter(Location=location)

                # if category != 'All':
                #     routine_data = routine_data.filter(Disposal_Type=category)
                #     non_routine_data = non_routine_data.filter(Disposal_Type=category)
                #     e_waste_data = e_waste_data.filter(Disposal_Type=category)
                #     R_YoY = R_YoY.filter(Disposal_Type=category)
                #     NR_YoY = NR_YoY.filter(Disposal_Type=category)
                #     EW_YoY = EW_YoY.filter(Disposal_Type=category)

        except Non_Routine_Disposal.DoesNotExist:
            non_routine_data = Non_Routine_Disposal.objects.none()
        except E_Waste_Disposal.DoesNotExist:
            e_waste_data = E_Waste_Disposal.objects.none()

        type_data = routine_data.values('Month', 'Waste_Type') \
        .annotate(total_waste=Sum('Quantity')) \
        .order_by('Month', 'Waste_Type').exclude(Waste_Type__in=['Bio-Medical Waste'])

        waste_labels = sorted(list(set(type_data.values_list('Month', flat=True))))
        waste_types = sorted(list(set(type_data.values_list('Waste_Type', flat=True))))
        waste_type_dataset = []
        for waste in waste_types:
            waste_type_data = type_data.filter(Waste_Type=waste)
            totals = []
            for month in waste_labels:
                month_record = waste_type_data.filter(Month=month).first()
                total = month_record.get('total_waste', 0) if month_record else '-'
                totals.append(round(float(total), 2) if total != '-' else '-')
            waste_type_dataset.append({
                'label':waste,
                'data':totals,
            })

            
        bio_data = routine_data.values('Month').annotate(type_total=Sum('Quantity'))
        bio_waste = bio_data.exclude(Waste_Type__in=['Wet Waste', 'Dry Waste', 'Plastic Waste'])
        bio_labels = [data['Month'] for data in bio_data]
        bio_total = []
        for label in bio_labels:
            bio_total.append(bio_waste.filter(Month=label).aggregate(sum=Sum('Quantity'))['sum'])
        
        bio_chart = {'type': 'bar','data': {'labels': [custom_filters.get_month_name(data) for data in bio_labels],
            'datasets':[{'label': 'Bio-Medical Waste(KG)','data': bio_total,'backgroundColor': '#FFFF00', 'borderColor': '#F4BF3A', 'borderWidth': 1}]},
            'options': { 'scales': {'yAxes': [{ 'ticks': { 'beginAtZero': True}}]}}}



        disposal_data = routine_data.values('Month', 'Disposal_Type') \
        .annotate(waste_total=Sum('Quantity')) \
        .order_by('Month', 'Disposal_Type')
        disposal_labels = sorted(list(set(disposal_data.values_list('Month', flat=True))))
        disposal_types = sorted(list(set(disposal_data.values_list('Disposal_Type', flat=True))))
        disposal_type_dataset = []
        for disposal in disposal_types:
            disposal_type_data = disposal_data.filter(Disposal_Type=disposal)
            total_disposals = []
            for month in disposal_labels:
                month_record = disposal_type_data.filter(Month=month).first()
                total = month_record.get('waste_total', 0) if month_record else '-'
                total_disposals.append(round(float(total), 2) if total != '-' else '-')
            disposal_type_dataset.append({
                'label':disposal,
                'data':total_disposals,
            })
    
        month_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        if routine_data:
            df1 = pd.DataFrame(list(routine_data.values("Month", "Waste_Type", 'Quantity')))
            df1['MonthName'] = df1['Month'].apply(lambda x: month_names[x-1])
            custom_sort_order = {month_names[i]:i+1 for i in range(12)}
            df1['MonthSort'] = df1['Month'].map(custom_sort_order)
            df1 = df1.sort_values(by='MonthSort')
            df1.drop(columns=['MonthSort'], inplace=True)
            df1 = df1.pivot_table(index=['Month', 'MonthName'], columns='Waste_Type', fill_value=0.00,aggfunc='sum', margins=True, margins_name='Total')
        
        if non_routine_data:
            df2 = pd.DataFrame(list(non_routine_data.values("Month", "Category", 'Quantity')))
            df2['MonthName'] = df2['Month'].apply(lambda x: month_names[x-1])
            custom_sort_order = {month_names[i]:i+1 for i in range(12)}
            df2['MonthSort'] = df2['Month'].map(custom_sort_order)
            df2 = df2.sort_values(by='MonthSort')
            df2.drop(columns=['MonthSort'], inplace=True)
            df2 = df2.pivot_table(index=['Month', 'MonthName'], columns='Category', fill_value=0.00,aggfunc='sum', margins=True, margins_name='Grand Total')
        
        if e_waste_data:
            df3 = pd.DataFrame(list(e_waste_data.values("Month", "Category", 'Quantity')))
            df3['MonthName'] = df3['Month'].apply(lambda x: month_names[x-1])
            custom_sort_order = {month_names[i]:i+1 for i in range(12)}
            df3['MonthSort'] = df3['Month'].map(custom_sort_order)
            df3 = df3.sort_values(by='MonthSort')
            df3.drop(columns=['MonthSort'], inplace=True)
            df3 = df3.pivot_table(index=['Month', 'MonthName'], columns='Category', fill_value=0.00,aggfunc='sum', margins=True, margins_name='Grand Total')

        if esg_data:
            df4 = pd.DataFrame(list(esg_data.values("Month", "Category", 'Unit', 'Quantity')))
            df4['MonthName'] = df4['Month'].apply(lambda x: month_names[x-1])
            custom_sort_order = {month_names[i]:i+1 for i in range(12)}
            df4['MonthSort'] = df4['Month'].map(custom_sort_order)
            df4 = df4.sort_values(by='MonthSort')
            df4.drop(columns=['MonthSort'], inplace=True)
            df4_pivot = df4.pivot_table(index=['Month', 'MonthName'], columns=['Category', 'Unit'], fill_value=0.00,aggfunc='sum', margins=True, margins_name='Grand Total')

            df5 = pd.DataFrame(list(esg_data.values("Location", "Category", 'Unit', 'Quantity')))
            df5 = df5.sort_values(by='Location')
            df5_pivot = df5.pivot_table(index=['Category', 'Unit'], columns='Location', fill_value=0.00,aggfunc='sum', margins=True, margins_name='Grand Total')

        context = {
            "routine_data":routine_data,
            "non_routine_data": non_routine_data,
            "e_waste_data": e_waste_data,
            "pivot_table1": df1.to_html() if routine_data else None,
            "pivot_table2" :df2.to_html() if non_routine_data else None,
            "pivot_table3" :df3.to_html() if e_waste_data else None,
            "pivot_table4": df4_pivot.to_html() if esg_data else None,
            "pivot_table5": df5_pivot.to_html() if esg_data else None,
            'type_chart': waste_type_dataset, 'waste_labels':waste_labels, 
            'bio_chart':json.dumps(bio_chart),
            'disposal_chart':disposal_type_dataset, 'disposal_labels':disposal_labels,
            'months' : sorted(list(set(RoutineDisposal.objects.values_list('Month',flat=True)))),
            "quarters" : sorted(list(set(RoutineDisposal.objects.values_list('Quarter',flat=True)))),
            "locations" : sorted(list(set(RoutineDisposal.objects.values_list('Location',flat=True)))),
            # "categories" : sorted(list(set(RoutineDisposal.objects.values_list( 'Disposal_Type', flat=True)))),
            "years" : sorted(list(set(RoutineDisposal.objects.values_list('Year',  flat=True))))}
        return render(request, 'Charts/WMP_Report.html', context)