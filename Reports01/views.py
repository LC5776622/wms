# import base64
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.core.exceptions import PermissionDenied 
from datetime import datetime
from Reports01.models import AuthorisedUser, CustomReports,  LocationModel
from django.contrib.auth import authenticate, login, logout
import pandas as pd
from django.conf import settings
import json
from .forms import CustomUserCreationForm , UserUpdateForm
from django.contrib.auth.models import Group, User
from .forms import  UploadAuthUser, UploadLocation
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required, user_passes_test


def user_in_add_group(user):
    if user.is_superuser:
         return True
    elif user.groups.filter(name='Read_Write').exists():
         return True
    else:
         raise PermissionDenied 

def user_in_change_group(user):
    if user.is_superuser:
         return True
    elif user.groups.filter(name='Read_Write_Edit').exists():
         return True
    else:
         raise PermissionDenied 

def user_in_delete_group(user):
    if user.is_superuser:
         return True
    elif user.groups.filter(name='Read_Write_Edit_Delete').exists():
         return True
    else:
         raise PermissionDenied 
    
def user_in_managers_group(user):
    if user.is_superuser:
         return True
    elif user.groups.filter(name='Admin-Managers').exists():
         return True
    else:
         raise PermissionDenied 

def user_in_leaders_group(user):
    if user.is_superuser:
         return True
    elif user.groups.filter(name='Admin-Leaders').exists():
         return True
    else:
         raise PermissionDenied 

def not_registered_user(user):
    if user.is_superuser or user.groups.filter(name='Admin-Leaders').exists():
        return True
    elif user.groups.filter().exists():
        raise PermissionDenied
    else:
        return True

def is_superuser(user):
    if user.is_superuser:
        return True
    else:
         raise PermissionDenied

def index (request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        time = datetime.now().strftime('%H')
        time = int(time)
        greeting = ''
        if time < 12:
            greeting = "Good Morning! "
        elif time >= 12 and time <= 16:
            greeting = "Good Afternoon! "
        else:
            greeting = "Good Evening! "
        reports = CustomReports.objects.all() 
        return render(request, 'index.html', {'reports' : reports, "greeting" : greeting})
    
@user_passes_test(user_in_add_group)
def CustomReport_Input(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        if request.method == 'POST':
            country = request.POST.get('Country')
            location = request.POST.get('Location')
            report_name = request.POST.get('ReportName')
            url = request.POST.get('ReportURL')
            report_input = CustomReports(country=country, location=location, report_name = report_name, url = url)
            context = {}
            data = CustomReports.objects.filter(url = url)
            context['reporturl'] : data
            if data.exists():
                return render(request, 'Reports/Report_already_exists.html', context)
            report_input.set_user(request.user)
            report_input.save()
        
            success_message = (f"You have successfully added a new report {report_name}.")
            request.session['success_message'] = success_message
            return redirect(reverse('CustomReport_Input') + '?success_message=' + success_message)
        
        else:
            success_message = request.session.pop('success_message', '')
            return render (request, 'Reports/Reports_Input.html', {'success_message': success_message})
        
def CustomReport_View(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        reports = CustomReports.objects.all()           
    return render (request, 'Reports/View_Reports.html', {'reports': reports})

def Reports_Data(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        reports = CustomReports.objects.all()  
        if not reports:
            return render(request, 'Reports/Reports_Data.html', {'error_message': 'No Records To Display!'})           
    return render (request, 'Reports/Reports_Data.html', {'reports': reports})

@user_passes_test(is_superuser)
def Update_Reports(request, reports_data_id):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        reports_data = CustomReports.objects.get(id=reports_data_id)
        if request.method == 'POST':
            reports_data.country = request.POST.get('Country')
            reports_data.location = request.POST.get('Location')
            reports_data.report_name = request.POST.get('ReportName')
            reports_data.url = request.POST.get('ReportURL')  
            reports_data.set_user(request.user)
            reports_data.save()
            return redirect('ReportsData')
        context = {
            'reports_data': reports_data}
        return render(request, 'Reports/update_reports_data.html', context)

@user_passes_test(is_superuser)
def Delete_Reports(request, id):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        reports_data = CustomReports.objects.get(pk=id)
        reports_data.delete()
        return redirect("ReportsData")

@user_passes_test(user_in_leaders_group)
def Location_Input(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        if request.method == 'POST':
            country = request.POST.get('Country')
            city = request.POST.get('City')
            location = request.POST.get('Location')
            locationcode = request.POST.get('LocationCode')
            sub_locs = request.POST.get('subLoc')
            address = 'NA' if request.POST.get("Address") == '' else request.POST.get("Address")
            contact = 'NA' if request.POST.get("contactNumber") == '' else request.POST.get("contactNumber")
            email = 'NA' if request.POST.get("Email") == '' else request.POST.get("Email")
            location_input = LocationModel(country=country, city=city, location=location, locationcode=locationcode, sub_locs=sub_locs, address=address, contact=contact, email=email)   
            context = {}
            data = LocationModel.objects.filter(country=country, location=location, sub_locs=sub_locs)
            context ["locations"] = data
            if data.exists():
                 return render(request, 'Locations/Location_already_exists.html', context)
            location_input.set_user(request.user)
            location_input.save()
            success_message = (f"Location Data Entered Successfully for {location} Location.")
            request.session['success_message'] = success_message
            return redirect(reverse('Location_Input') + '?success_message=' + success_message)
        else:
            success_message = request.session.pop('success_message', '')
            return render(request, 'Locations/Location_Input.html', {'success_message': success_message})

@user_passes_test(user_in_leaders_group)
def Location_Upload(request):
    if request.user.is_anonymous:
         return redirect('/login')
    else:
        if request.method == 'POST':
            form = UploadLocation(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES['locationfile']
                data = pd.read_excel(file)
                expected_columns = ['Country', 'City', 'Location', 'Location Code', 'Sub-Location', 'Contact No.', 'Address', 'Email']
                if list(data.columns) != expected_columns or len(data.columns) != len(expected_columns):
                    error_message = f"The Upload File should have these columns only: {', '.join(expected_columns)}. Please refer to Sample File below."
                    return render(request, "Locations/Location_Input.html", {'form': form, 'error_message': error_message})
                count = 0
                duplicates = []  
                for index, row in data.iterrows():
                    obj = LocationModel(
                        country= row['Country'],
                        city= row['City'],
                        location= row['Location'],
                        locationcode = row['Location Code'],
                        sub_locs= row['Sub-Location'],
                        address= row['Address'] if pd.notna(row['Address'])  else 'NA',
                        contact= row['Contact No.'] if pd.notna(row['Contact No.'])  else 'NA',
                        email = row['Email']  if pd.notna(row['Email']) else 'NA')
                    context = {}
                    data = LocationModel.objects.filter(country=obj.country, city=obj.city, location=obj.location, sub_locs=obj.sub_locs)
                    if data.exists():
                        duplicates.append(obj)
                    else:
                        obj.set_user(request.user)
                        obj.save()
                        count += 1
                if duplicates:
                    context = {'locations': duplicates}
                    return render(request, "Locations/Location_already_exists2.html", context)
                else:
                    success_message = (f"{count} Records Uploaded Successfully.")
                    request.session['success_message'] = success_message
                    return redirect(reverse('Location_Upload') + '?success_message=' + success_message)
        else:
            form = UploadLocation()
        success_message = request.session.pop('success_message', '')
        return render(request, 'Locations/Location_Input.html', {'form': form, 'success_message': success_message})

def Location_View(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        location_data = LocationModel.objects.all()  
        if not location_data:
            return render(request, 'Locations/Location_View.html', {'error_message': 'No Records To Display!'})           
    return render (request, 'Locations/Location_View.html', {'location_data': location_data})

@user_passes_test(user_in_leaders_group)
def Update_Locations(request, location_data_id):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        location_data = LocationModel.objects.get(id=location_data_id)
        if request.method == 'POST':
            location_data.country = request.POST.get('Country')
            location_data.city = request.POST.get('City')
            location_data.location = request.POST.get('Location')
            location_data.locationcode = request.POST.get('LocationCode')
            location_data.sub_locs = request.POST.get('subLoc') 
            location_data.address = 'NA' if request.POST.get("Address") == '' else request.POST.get("Address")
            location_data.contact = 'NA' if request.POST.get("contactNumber") == '' else request.POST.get("contactNumber")
            location_data.email = 'NA' if request.POST.get("Email") == '' else request.POST.get("Email")
            location_data.set_user(request.user)   
            location_data.save()
            return redirect('Location_View')
        context = {
            'location_data': location_data}
        return render(request, 'Locations/Update_Locations.html', context)

@user_passes_test(is_superuser)
def Delete_Locations(request, id):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        location_data = LocationModel.objects.get(pk=id)
        location_data.delete()
        return redirect("Location_View")

@user_passes_test(is_superuser)
def AuthUser_Upload(request):
    if request.method == 'POST':
        form = UploadAuthUser(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['userfile']
            data = pd.read_excel(file)
            expected_columns = ['EID', 'Employee Name', 'Country', 'Location']
            if list(data.columns) != expected_columns or len(data.columns) != len(expected_columns):
                error_message = f"The Upload File should have these columns only: {', '.join(expected_columns)}. Please refer to Sample File below."
                return render(request, "Users/AuthUserUpload.html", {'form': form, 'error_message': error_message})
            count = 0
            duplicates = [] 
            for index, row in data.iterrows():
                obj = AuthorisedUser(
                    userid= row['EID'],
                    user_name= row['Employee Name'],
                    user_country= row['Country'],
                    user_location = row['Location'])
                context = {}
                data = AuthorisedUser.objects.filter(userid=obj.userid)
                if data.exists():
                    duplicates.append(obj)
                else:
                    obj.set_user(request.user)
                    obj.save()
                    count += 1
            if duplicates:
                context = {'auth_users': duplicates}
                return render(request, "Users/User_already_exists.html", context)
            else:
                success_message = (f"{count} Records Uploaded Successfully.")
                request.session['success_message'] = success_message
                return redirect(reverse('AuthUser_Upload') + '?success_message=' + success_message)
    else:
        form = UploadAuthUser()
    success_message = request.session.pop('success_message', '')
    return render(request, 'Users/AuthUserUpload.html', {'form': form, 'success_message': success_message})

@user_passes_test(is_superuser)
def AuthUser_View(request):
        if request.user.is_anonymous:
            return redirect('/login')
        else:
            auth_users = AuthorisedUser.objects.all()  
            if not auth_users:
                return render(request, 'Users/AuthUsers_View.html', {'error_message': 'No Records To Display!'})           
        return render (request, 'Users/AuthUsers_View.html', {'auth_users': auth_users})

user_passes_test(is_superuser)
def AuthUser_Update(request, auth_user_id):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        Countries = LocationModel.objects.all()
        Locations = {}
        for country in Countries:
            if country.country not in Locations:
                Locations[country.country] = []
            Locations[country.country].append(country.location)
        for country in Locations:
            Locations[country] = sorted(list(set(Locations[country])))
        auth_user = AuthorisedUser.objects.get(id=auth_user_id)
        if request.method == 'POST':
            auth_user.userid = request.POST.get('EID')
            auth_user.user_name = request.POST.get('EmpName')
            auth_user.user_country = request.POST.get('EmpCountry')
            auth_user.user_location = request.POST.get('EmpLocation')
            auth_user.exclude_from_calculation = request.POST.get('Excluded')
            auth_user.is_manager = request.POST.get('IsManager')       
            auth_user.set_user(request.user)   
            auth_user.save()
            return redirect('AuthUser_View')
        context = {'auth_user': auth_user,
            'locations':json.dumps(Locations),
            'countries':sorted(list(set(Countries.values_list('country', flat= True))))}
        return render(request, 'Users/Update_AuthUsers.html', context)

@user_passes_test(is_superuser)
def AuthUser_Delete(request, id):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        auth_user = AuthorisedUser.objects.get(pk=id)
        auth_user.delete()
        return redirect("AuthUser_View")

@user_passes_test(not_registered_user) 
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            if AuthorisedUser.objects.filter(userid=username).exists():
                user = form.save()
                user.groups.add(Group.objects.get(name='Read-Only'))
                messages.success(request, 'Account created successfully')
                return render(request, 'Users/add_user_success.html')
            else:
                error_message = " You do not have permission to register on this application."
                return render(request, 'Users/user_registration.html', {'form': form, 'error_message': error_message})
    else:
        form = CustomUserCreationForm()
    return render(request, 'Users/user_registration.html', {'form': form})

def LoginUser(request):
    if request.method == 'POST':
        # check if user has entered correct credintials
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            error_message = ("Error: Incorrect Username or Password!")
            request.session['error_message'] = error_message
            return redirect(reverse('Login') + '?error_message=' + error_message)
    else:
        error_message = request.session.pop('error_message', '')
        return render(request, 'login.html', {'error_message' : error_message})

def LogoutUser(request):
    logout(request)
    return redirect('/login')

@login_required
def ProfileView(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        user = request.user
        if request.method =='POST':
            form = PasswordChangeForm(user=user, data=request.POST)
            if form.is_valid():
                form.save
                messages.success(request, "Your Password Was Suceessfully Updated!")
                return redirect('UserProfile')
        else:
            form = PasswordChangeForm(user=user)
        context = {
            'user':user,
            'username' :user.username,
            'first_name':user.first_name,
            'last_name' : user.last_name,
            'email' : user.email,
            'form':form,}
        return render(request, 'Users/user_profile.html', context)


@user_passes_test(user_in_leaders_group)
def Registered_Users(request):
    registered_users = User.objects.all().exclude(is_superuser=True)
    return render(request, 'Users/Registered_User.html', {'registered_users': registered_users})

def Update_User_Profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method =='POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Profile for {user.last_name}, {user.first_name} ({user.username}) has been updated.")
            return redirect('Registered_Users')
    else:
        form = UserUpdateForm(instance=user)
        context = {
            'form':form,
            'user':user
        }
        return render(request, 'Users/Update_User_Profile.html', context)