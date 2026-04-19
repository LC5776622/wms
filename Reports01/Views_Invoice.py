# import base64
from django.shortcuts import render, redirect, reverse, HttpResponse
from django.core.exceptions import PermissionDenied 
from datetime import datetime
from Reports01.models import Invoice_Data, LocationModel, AuthorisedUser, Vendor_Data
# import pandas as pd
# from django.db.models import Sum, Avg, Count
from django.conf import settings
# from django.contrib.auth.models import Group
# from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
# from django.contrib.auth.decorators import login_required
# import json
# from django.core.paginator import Paginator
from .views import user_in_add_group, user_in_change_group, user_in_delete_group, user_in_managers_group, user_passes_test, is_superuser

@user_passes_test(user_in_add_group)
def Invoice_Input(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        username = request.user.username
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_country = UserLocation.user_country
        user_location = UserLocation.user_location
        LocationUsers = AuthorisedUser.objects.filter(user_location=user_location)

        if request.method == 'POST':
            month = request.POST.get('invoiceMonth')
            quarter = []
            if month.__contains__('-01') or month.__contains__('-02') or month.__contains__('-03'):
                quarter = 'Q1'
            elif month.__contains__('-04') or month.__contains__('-05') or month.__contains__('-06'):
                quarter = 'Q2'
            elif month.__contains__('-07') or month.__contains__('-08') or month.__contains__('-09'):
                quarter = 'Q3'
            else:
                quarter = 'Q4'

            invoice_month = month
            invoice_quarter = quarter
            invoice_year = datetime.strptime(month, '%Y-%m').strftime('%Y')
            invoice_country = request.POST.get('country')
            invoice_location = request.POST.get('location')
            expense_type = request.POST.get("category")
            invoice_vendor = request.POST.get('vendor')
            invoice_no = request.POST.get('invoiceNo')
            invoice_po = request.POST.get('invoicePO')
            invoice_date = request.POST.get('invoiceDate')
            invoice_amount = request.POST.get('invoiceAmount')
            processed_by = request.POST.get('processedBy')
            invoice_status = request.POST.get('invoiceStatus')
            payment_date =''if invoice_status == 'In Process' else request.POST.get('paymentDate')
            invoice_input = Invoice_Data(Invoice_Year = invoice_year, Invoice_Quarter=invoice_quarter, Invoice_Month=invoice_month, Invoice_Country=invoice_country, Invoice_Location=invoice_location, Expense_Type=expense_type, Invoice_Vendor=invoice_vendor, Invoice_No=invoice_no, Invoice_PO=invoice_po, Invoice_Date=invoice_date, Invoice_Amount=invoice_amount, Invoice_Processed_By=processed_by, Invoice_Payment_Date=payment_date, Invoice_Status=invoice_status)   
            context = {}
            data = Invoice_Data.objects.filter(Invoice_Month=invoice_month, Invoice_Location=invoice_location, Invoice_Vendor=invoice_vendor, Invoice_No = invoice_no)
            for row in data:
                 row.Invoice_Month = datetime.strptime(row.Invoice_Month, '%Y-%m')
                 row.Invoice_Month = row.Invoice_Month.strftime('%b-%Y')
            context["InvDataset"] = data
            if data.exists():
                 return render(request, 'Invoices/invoice_already_exists.html', context)
            invoice_input.set_user(request.user)
            invoice_input.save()
            success_message = (f"Details of Invoice Number {invoice_no} of {invoice_vendor} Have Been Entered Successfully.")
            request.session['success_message'] = success_message
            return redirect(reverse('Invoice_Input') + '?success_message=' + success_message)
        else:
            success_message = request.session.pop('success_message', '')
            context = {'success_message' : success_message, 
                'user_country': user_country,'user_location' : user_location,
                'AllCountries': sorted(LocationModel.objects.values_list('country', flat=True).distinct()),
                'userLocation':sorted(list(set(LocationUsers.values_list('user_location', flat= True)))),
                'locationUsers':sorted(list(set(LocationUsers.values_list('user_name', flat= True)))),
                'allUsers':sorted(list(set(AuthorisedUser.objects.values_list('user_name', flat= True)))), 
                'locations' : sorted(Vendor_Data.objects.values_list('location', flat=True).distinct()),
                'categories' : sorted(Vendor_Data.objects.values_list('category', flat=True).distinct()),
                'vendors' : Vendor_Data.objects.all().order_by('vendor')} 
            return render(request, 'Invoices/Invoice_Input.html', context)

def Invoice_View(request):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        username = request.user.username
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_location = UserLocation.user_location
        inv_data = Invoice_Data.objects.all().order_by('Invoice_Month', 'Invoice_Location')
        filtered_data = inv_data.filter(Invoice_Location=user_location)

        if request.user.groups.filter(name='Admin-Leaders').exists():
            inv_data = inv_data
        else:
            inv_data = filtered_data      
        
        if not inv_data:
            return render(request, 'Invoices/Invoice_Data.html', {'error_message': 'No Records To Display!'})
        context = {}
        latest_report = inv_data.latest('Invoice_Year')
        latest_year = latest_report.Invoice_Year
        latest_data = inv_data.filter(Invoice_Year=latest_year)

        invoice_year =request.GET.get('invoice_year')
        invoice_month = request.GET.get('invoice_month')
        invoice_location = request.GET.get('invoice_location')
        invoice_category = request.GET.get('invoice_category')

        if invoice_year == None and invoice_month == None and invoice_location == None and invoice_category == None:
            inv_data = latest_data
        else:
            if invoice_year != 'All':
                inv_data = inv_data.filter(Invoice_Year=invoice_year)
            if invoice_month != 'All':
                inv_data = inv_data.filter(Invoice_Month=invoice_month)
            if invoice_location != 'All':
                inv_data = inv_data.filter(Invoice_Location=invoice_location)
            if invoice_category != 'All':
                inv_data = inv_data.filter(Expense_Type=invoice_category)           

        for row in inv_data:           
            row.Invoice_Month = datetime.strptime(row.Invoice_Month, '%Y-%m').strftime('%b-%Y')
            row.Invoice_Date = datetime.strptime(row.Invoice_Date, '%Y-%m-%d').strftime('%d-%b-%y')
            row.Invoice_Payment_Date = 'NA' if row.Invoice_Payment_Date == '' or row.Invoice_Payment_Date == None else datetime.strptime(row.Invoice_Payment_Date, '%Y-%m-%d').strftime('%d-%b-%y')
            row.Invoice_Vendor = row.Invoice_Vendor.replace("&", "And")
            row.Expense_Type = row.Expense_Type.replace("&", "And")
            context = {'inv_data': inv_data,
            "invoice_years" : sorted(list(set(Invoice_Data.objects.values_list('Invoice_Year', flat=True)))),
            "invoice_months" : sorted(list(set(inv_data.values_list('Invoice_Month', flat=True)))),
            "invoice_locations" : sorted(list(set(inv_data.values_list('Invoice_Location', flat=True)))),
            "invoice_categories" : sorted(list(set(inv_data.values_list('Expense_Type',  flat=True))))}
        return render(request, 'Invoices/Invoice_Data.html', context)

@user_passes_test(user_in_change_group)
def update_invoice_data(request, invoice_data_id):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        locations = Vendor_Data.objects.values_list('location', flat=True).distinct()
        categories = Vendor_Data.objects.values_list('category', flat=True).distinct()
        vendors = Vendor_Data.objects.all()

        username = request.user.username
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_country = UserLocation.user_country
        user_location = UserLocation.user_location
        LocationUsers = AuthorisedUser.objects.filter(user_location=user_location)
        invoice_data = Invoice_Data.objects.get(id=invoice_data_id)
        
        if request.method == 'POST':
            month = request.POST.get('invoiceMonth')
            quarter = []
            if month.__contains__('-01') or month.__contains__('-02') or month.__contains__('-03'):
                quarter = 'Q1'
            elif month.__contains__('-04') or month.__contains__('-05') or month.__contains__('-06'):
                quarter = 'Q2'
            elif month.__contains__('-07') or month.__contains__('-08') or month.__contains__('-09'):
                quarter = 'Q3'
            else:
                quarter = 'Q4'
            invoice_data.Invoice_Year = datetime.strptime(month,'%Y-%m').strftime('%Y')
            invoice_data.Invoice_Month = month
            invoice_data.Invoice_Quarter = quarter
            invoice_data.Invoice_Country = request.POST.get('country')
            invoice_data.Invoice_Location = request.POST.get('location')
            invoice_data.Expense_Type = request.POST.get("category")
            invoice_data.Invoice_Vendor = request.POST.get('vendor')
            invoice_data.Invoice_No = request.POST.get('invoiceNo')
            invoice_data.Invoice_PO = request.POST.get('invoicePO')
            invoice_data.Invoice_Date = request.POST.get('invoiceDate')
            invoice_data.Invoice_Amount = request.POST.get('invoiceAmount')
            invoice_data.Invoice_Processed_By = request.POST.get('ProcessedBy')
            invoice_data.Invoice_Status = request.POST.get('invoiceStatus')
            invoice_data.Invoice_Payment_Date = '' if invoice_data.Invoice_Status == 'In Process' else request.POST.get('paymentDate')
            invoice_data.set_user(request.user) 
            invoice_data.save()
            return redirect('InvoiceView')
        
        context = {'invoice_data': invoice_data,
            'user_country': user_country,'user_location' : user_location,
            'AllCountries': sorted(AuthorisedUser.objects.values_list('user_country', flat=True).distinct()),
            'locations': locations, 'categories': categories, 'vendors': vendors,
            'userLocation':sorted(list(set(LocationUsers.values_list('user_location', flat= True)))),
            'locationUsers':sorted(list(set(LocationUsers.values_list('user_name', flat= True)))),
            'allUsers':sorted(list(set(AuthorisedUser.objects.values_list('user_name', flat= True)))), 
        }
        return render(request, 'Invoices/update_invoice_data.html', context)

@user_passes_test(user_in_delete_group)
def Delete_Invoice(request, id):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        invoicedata = Invoice_Data.objects.get(pk=id)
        invoicedata.delete()
        return redirect("InvoiceView")
 