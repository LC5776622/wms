# import base64
from django.shortcuts import render, redirect, reverse, HttpResponse
from django.core.exceptions import PermissionDenied 
from Reports01.models import AuthorisedUser, Vendor_Data, LocationModel
import pandas as pd
from django.conf import settings
from .forms import UploadVendor
from django.contrib.auth.decorators import user_passes_test
import json
from django.db import models
from django.core.paginator import Paginator
from .views import user_in_add_group, user_in_change_group, user_in_delete_group, user_in_managers_group, user_passes_test, is_superuser

@user_passes_test(user_in_add_group)
def Vendor_Input(request):
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
            country = request.POST.get('country')
            location = request.POST.get('location')
            category = request.POST.get('category')
            vendor_desc = request.POST.get('vendorDesc')
            vendor = request.POST.get("vendor")
            business_address = request.POST.get("address")
            business_email = request.POST.get("email")
            contact_person = request.POST.get("contactPerson")
            contact_no = request.POST.get("contactNo")
            vendor_input = Vendor_Data(country=country, location=location, category=category, vendor_desc=vendor_desc, vendor=vendor, business_address=business_address, business_email=business_email, contact_person=contact_person, contact_no=contact_no)   
            context = {}
            data = Vendor_Data.objects.filter(country=country, location=location, category=category, vendor_desc=vendor_desc, vendor=vendor)
            context ["vendordataset"] = data
            if data.exists():
                 return render(request, 'Vendors/Vendor_already_exists.html', context)
            vendor_input.set_user(request.user)
            vendor_input.save()
            success_message = (f"Details of Vendor {vendor} Under {category} Category Have Been Entered Successfully.")
            request.session['success_message'] = success_message
            return redirect(reverse('Vendor_Input') + '?success_message=' + success_message)
        else:
            success_message = request.session.pop('success_message', '')
            context = {'success_message': success_message, 
                'user_country': user_country,'user_location' : user_location,
                'locations':json.dumps(Locations),
                'countries':sorted(list(set(Countries.values_list('country', flat= True)))),}
            return render(request, 'Vendors/Vendor_Input.html', context)

@user_passes_test(is_superuser)
def Vendor_Upload(request):
    if request.user.is_anonymous:
         return redirect('/login')
    else:
        if request.method == 'POST':
            form = UploadVendor(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES['vendorfile']
                data = pd.read_excel(file)
                expected_columns = ['Country', 'Location', 'Category', 'Description', 'Vendor Name', 'Address', 'Email', 'Contact Person', 'Contact No.']
                if list(data.columns) != expected_columns or len(data.columns) != len(expected_columns):
                    error_message = f"The Upload File should have these columns only: {', '.join(expected_columns)}. Please refer to Sample File below."
                    return render(request, "Vendors/Vendor_Input.html", {'form': form, 'error_message': error_message})
                count = 0
                duplicates = []  
                for index, row in data.iterrows():
                    obj = Vendor_Data(
                        country= row['Country'],
                        location= row['Location'],
                        category= row['Category'],
                        vendor_desc= row['Description'],
                        vendor= row['Vendor Name'],
                        business_address= row['Address'],
                        business_email= row['Email'],
                        contact_person= row['Contact Person'] ,
                        contact_no= row['Contact No.'],)
                    context = {}
                    data = Vendor_Data.objects.filter(country=obj.country, location=obj.location, category=obj.category, vendor_desc=obj.vendor_desc, vendor=obj.vendor)
                    if data.exists():
                        duplicates.append(obj)
                    else:
                        obj.set_user(request.user)
                        obj.save()
                        count += 1
                if duplicates:
                    context = {'dataset05': duplicates}
                    return render(request, "Vendors/Vendor_already_exists2.html", context)
                else:
                    success_message = (f"{count} Records Uploaded Successfully.")
                    request.session['success_message'] = success_message
                    return redirect(reverse('Vendor_Upload') + '?success_message=' + success_message)
        else:
            form = UploadVendor()
        success_message = request.session.pop('success_message', '')
        return render(request, 'Vendors/Vendor_Input.html', {'form': form, 'success_message': success_message})


def Vendor_View(request):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        username = request.user.username
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_location = UserLocation.user_location
        vendor_data = Vendor_Data.objects.all().order_by('category', 'location')
        filtered_data = vendor_data.filter(location=user_location)
        if request.user.groups.filter(name='Admin-Leaders').exists():
            vendor_data = vendor_data
        else:
            vendor_data = filtered_data

        context = {}
        vendor_location = request.GET.get('vendor_location')
        vendor_category = request.GET.get('vendor_category')

        if vendor_category == None and vendor_location == None:
            vendor_data = vendor_data
        else:
            if vendor_location != 'All':
                vendor_data = vendor_data.filter(location=vendor_location)
            if vendor_category != 'All':
                vendor_data = vendor_data.filter(category=vendor_category)
        context ["vendor_dataset"] = vendor_data
        context["vendor_countries"] = sorted(list(set(Vendor_Data.objects.values_list('country', flat=True))))
        context["vendor_locations"] = sorted(list(set(vendor_data.values_list('location', flat=True))))
        context["vendor_categories"] = sorted(list(set(vendor_data.values_list('category', flat=True))))
        return render(request, 'Vendors/Vendor_Data.html', context)

@user_passes_test(user_in_change_group)
def update_vendor_data(request, vendor_data_id):
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
        vendor_data = Vendor_Data.objects.get(id=vendor_data_id)
        
        if request.method == 'POST':
            vendor_data.country = request.POST.get('country')
            vendor_data.location = request.POST.get('location')
            vendor_data.category = request.POST.get("category")
            vendor_data.vendor_desc = request.POST.get('vendorDesc')
            vendor_data.vendor = request.POST.get('vendor')
            vendor_data.business_address = request.POST.get('address')
            vendor_data.business_email = request.POST.get('email')
            vendor_data.contact_person = request.POST.get('contactPerson')
            vendor_data.contact_no = request.POST.get('contactNo')

            vendor_data.save()
            return redirect('VendorView')
        
        context = {
            'vendor_data': vendor_data,
            'user_country': user_country,'user_location' : user_location,
            'locations':json.dumps(Locations),
            'countries':sorted(list(set(Countries.values_list('country', flat= True)))),
        }
        return render(request, 'Vendors\\update_vendor_data.html', context)

@user_passes_test(user_in_delete_group)
def Delete_Vendor(request, id):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        vendor_data = Vendor_Data.objects.get(pk=id)
        vendor_data.delete()
        return redirect("VendorView")
