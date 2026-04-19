# import base64
from django.shortcuts import render, redirect, reverse, HttpResponse
from datetime import datetime
from Reports01.models import AuthorisedUser, OPEX_Data, Expense_Heads, LocationModel, Forex
import pandas as pd
from django.db.models import Sum, Avg, Count
from django.conf import settings
from .forms import UploadOPEXForm, UploadExpenseHeads
from django.db.models import F, FloatField, Sum, ExpressionWrapper, Q
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from .templatetags import custom_filters
import json
from django.db import models
from django.core.paginator import Paginator
from .views import user_in_add_group, user_in_change_group, user_in_delete_group, user_in_managers_group, user_passes_test, is_superuser

@user_passes_test(is_superuser)
def GL_Input(request):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        if request.method == 'POST':
            form = UploadExpenseHeads(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES['glfile']
                data = pd.read_excel(file)
                expected_columns = ['GL', 'GL Name', 'Head']
                if list(data.columns) != expected_columns or len(data.columns) != len(expected_columns):
                    error_message = f"The Upload File should have these 3 columns only: {', '.join(expected_columns)}. Please refer to Sample File below."
                    return render(request, "OPEX/GL_Upload.html", {'form': form, 'error_message': error_message})
                count = 0
                duplicates = [] 
                for index, row in data.iterrows():
                    obj = Expense_Heads(
                        GL_Code= row['GL'],
                        GL_Name= row['GL Name'],
                        Expense_Head= row['Head'])
                    context = {}
                    data = Expense_Heads.objects.filter(GL_Code=obj.GL_Code, GL_Name=obj.GL_Name, Expense_Head=obj.Expense_Head)
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
                    return redirect(reverse('GL_Input') + '?success_message=' + success_message)
        else:
            form = UploadExpenseHeads()
        success_message = request.session.pop('success_message', '')
        return render(request, 'OPEX/GL_Upload.html', {'form': form, 'success_message': success_message})

def Forex_Input(request):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        current_year = datetime.today().year
        last_5_year = current_year-4
        next_5_year = current_year + 4
        year_range = []
        for i in range(last_5_year, next_5_year):
            year_range.append(i)


        username = request.user.username
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_country = UserLocation.user_country
        user_currency = OPEX_Data.objects.values('Currency').filter(Country=user_country)

        Countries = LocationModel.objects.all()
        Locations = {}
        for country in Countries:
            if country.country not in Locations:
                Locations[country.country] = []
            Locations[country.country].append(country.location)
        for country in Locations:
            Locations[country] = sorted(list(set(Locations[country])))

        if request.method =='POST':
            year = request.POST.get('year')
            country = request.POST.get('country')
            currency = request.POST.get('currency')
            usd_rate = request.POST.get('usd_rate')
            forex_input = Forex(year=year, country=country, currency=currency, usd_rate=usd_rate)
            context = {}
            data = Forex.objects.filter(year=year, country=country, currency=currency)
            if data.exists():
                error_message = (f"Warning!!! USD Conversion Rate for {country}, with value (1 USD = {currency} {usd_rate}), already has been entered for Year {year}.")
                request.session['error_message'] = error_message
                return redirect(reverse('Forex_Input') + '?error_message=' + error_message)
            forex_input.set_user(request.user)
            forex_input.save()
            
            success_message = (f"Success!!! USD Conversion Rate for {country} with a value of 1 USD = {currency} {usd_rate}, entered successfully for Year {year}.")
            request.session['success_message'] = success_message
            return redirect(reverse('Forex_Input') + '?success_message=' + success_message)
        else:
            success_message = request.session.pop('success_message', '')
            error_message = request.session.pop('error_message', '')
            context = {'success_message': success_message,
                       'error_message':error_message,
            'year_range':year_range,
            'current_year': current_year,
            'user_country': user_country,
            'user_currency':user_currency,
            'currencies':sorted(list(set(OPEX_Data.objects.values_list('Currency', flat=True)))),
            'countries':sorted(list(set(Countries.values_list('country', flat= True)))),}
            return render (request, 'OPEX/Forex_Input.html', context)

# Need To Update Counrtry/Location Input Validation in below code
@user_passes_test(user_in_managers_group)
def OPEX_Upload(request):
    if request.user.is_anonymous:
            return redirect('/login')
    else: 
        username = request.user.username
        admin_leaders = request.user.groups.filter(name='Admin-Leaders').exists()
        superuser = request.user.is_superuser
        UserLocation = AuthorisedUser.objects.get(userid=username) 
        user_country = UserLocation.user_country
        user_location = UserLocation.user_location

        location_opex = OPEX_Data.objects.all() if superuser or admin_leaders else OPEX_Data.objects.filter(Location=user_location)
        Countries = LocationModel.objects.all()
        Locations = {}
        for country in Countries:
            if country.country not in Locations:
                Locations[country.country] = []
            Locations[country.country].append(country.location)
        for country in Locations:
            Locations[country] = sorted(list(set(Locations[country])))
        if request.method == 'POST':
            form = UploadOPEXForm(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES['opexfile']
                data = pd.read_excel(file)
                expected_columns = ['Month', 'Location Name', 'BU', 'Currency', 'GL', 'GL Name', 'Head', 'Plan', 'Forecast','Accrual']
                if list(data.columns) != expected_columns or len(data.columns) != len(expected_columns):
                    error_message = f"The Upload File should have these columns only: {', '.join(expected_columns)}. Please refer to Sample File below."
                    return render(request, "OPEX/OPEX_Upload.html", {'form': form, 'error_message': error_message})
                count = 0
                duplicates = []
                for index, row in data.iterrows():
                    currency = row['Currency']
                    entity = row ['Location Name']
                    entity = entity.replace('Bengluru', 'Bangalore')
                    entity = entity.replace('Bengaluru', 'Bangalore')
                    country_name = []
                    location_name = []
                    inputMonth = row['Month']
                    if entity.__contains__('Pune') or entity.__contains__('PUN'):
                        location_name = 'Pune'
                    elif entity.__contains__('Gurgaon') or entity.__contains__('Gurugram') or entity.__contains__('GGN') or entity.__contains__('HRYN'):
                        location_name= 'Gurgaon'
                    elif entity.__contains__('Bengaluru') or entity.__contains__('Bangalore') or entity.__contains__('BLR'):
                        location_name= 'Bangalore'
                    elif entity.__contains__('Hyderabad') or entity.__contains__('HYD'):
                        location_name= 'Hyderabad'
                    elif entity.__contains__('Mumbai') or entity.__contains__('MUM'):
                        location_name= 'Mumbai'
                    elif entity.__contains__('Mohali') or entity.__contains__('MHL'):
                        location_name= 'Mohali'
                    elif entity.__contains__('Makati'):
                        location_name= 'Makati'
                    elif entity.__contains__('Manila'):
                        location_name= 'Manila'
                    elif entity.__contains__('Cebu'):
                        location_name= 'Cebu'
                    elif entity.__contains__('Chennai'):
                        location_name= 'Chennai'
                    elif entity.__contains__('Makati'):
                        location_name= 'Makati'
                    else:
                        location_name = entity
                    
                    if currency == 'INR':
                        country_name = 'India'
                    elif currency == 'PHP':
                        country_name = 'Philippines'
                    elif currency == 'AUD':
                        country_name = 'Australia'
                    else:
                        country_name = location_name
                    
                    try:
                        obj = OPEX_Data.objects.get(
                            Country = country_name,
                            Year= inputMonth.year,
                            Month=inputMonth.month,
                            Quarter = (inputMonth.month - 1)// 3 + 1,
                            Entity = entity,
                            Location=location_name,
                            Currency=currency,
                            GL__GL_Code=row['GL'],
                            GL_Code=row['GL'],
                            GL_Name=row['GL Name'],
                            GL_Desc=row['Head'] if pd.notna(row['Head']) else row['GL Name'],
                            Plan=float(round(row['Plan'], 2)) if pd.notna(row['Plan']) else 0.00
                        )
                    except OPEX_Data.DoesNotExist:
                        expense_head = Expense_Heads.objects.get(GL_Code=row['GL'])
                        obj = OPEX_Data(
                            Country = country_name,
                            Year=inputMonth.year,
                            Quarter = (inputMonth.month - 1)// 3 + 1,
                            Month=inputMonth.month,
                            Entity = entity,
                            Location=location_name,
                            BU=row['BU'],
                            Currency=currency,
                            GL = expense_head,
                            GL_Code=row['GL'],
                            Expense_Category=expense_head.Expense_Head,
                            GL_Name=row['GL Name'],
                            GL_Desc=row['Head'] if pd.notna(row['Head']) else row['GL Name'],
                            Plan=float(round(row['Plan'], 2)) if pd.notna(row['Plan']) else 0.00
                        )
                    obj.Forecast = float(round(row['Forecast'], 2)) if pd.notna(row['Forecast']) else obj.Plan
                    obj.Accrual = float(round(row['Accrual'], 2)) if pd.notna(row['Accrual']) else obj.Plan
                    obj.Plan_vs_Forecast = round(obj.Plan - obj.Forecast, 2)
                    obj.Plan_vs_Accrual = round(obj.Plan - obj.Accrual, 2)
                    obj.Forecast_vs_Accrual = round(obj.Forecast - obj.Accrual, 2)
                    
                    context = {}
                    
                    data = OPEX_Data.objects.filter(Year= obj.Year, Month = obj.Month, Location = obj.Location, BU = obj.BU, GL_Code = obj.GL_Code, GL_Name = obj.GL_Name, GL_Desc = obj.GL_Desc, Plan = obj.Plan, Forecast=obj.Forecast, Accrual=obj.Accrual )
                    
                    if data.exists():
                        duplicates.append(obj)
                    else:
                        obj.set_user(request.user)
                        obj.save()
                        count += 1
                if duplicates:
                        context = {'dataset3' :duplicates}
                        return render (request, "OPEX/OPEX_already_exists.html", context)
                else:
                    success_message = (f"{count} Records Uploaded Successfully.")
                    request.session['success_message'] = success_message
                    return redirect(reverse('OPEX_Upload') + '?success_message=' + success_message)  
        else:
            form = UploadOPEXForm()
            success_message = request.session.pop('success_message', '')
            context = { 'form':form, 'success_message':success_message,
                'countries' : sorted(list(set(Countries.values_list('country', flat=True)))),
                'locations' : json.dumps(Locations),
                'entities' : sorted(list(set(OPEX_Data.objects.values_list('Entity', flat=True)))),
                'location_entity': sorted(list(set(location_opex.values_list('Entity', flat=True)))),
                'user_country': user_country,
                'user_location': user_location}
        return render(request, 'OPEX/OPEX_Upload.html', context)

@user_passes_test(user_in_managers_group)
def OPEX_Input(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        if request.method == 'POST':
            month = request.POST.get('OpexMonth')
            currency = request.POST.get('Currency')
            Country = request.POST.get('OpexCountry')
            Year = int(datetime.strptime(month, '%Y-%m').year)
            Location= request.POST.get('OpexLocation')
            Entity = request.POST.get('OpexEntity')
            Month = int(datetime.strptime(month, '%Y-%m').month)
            Quarter = int((Month-1)//3 + 1)
            BU =  request.POST.get('BUC') 
            Currency =  currency
            GL = Expense_Heads.objects.get(GL_Code=request.POST.get('GL_Code'))
            GL_Code = request.POST.get('GL_Code')
            GL_Name = request.POST.get('GL_Name') 
            Expense_Category = Expense_Heads.objects.get(GL_Code=request.POST.get('GL_Code')).Expense_Head
            GL_Desc = request.POST.get('Description') 
            Plan = 0 if request.POST.get('Plan') == '' or request.POST.get('Plan') == None else request.POST.get('Plan')
            Forecast = 0.00
            Accrual = 0.00
            opex_input = OPEX_Data(GL=GL, Country = Country, Year = Year, Quarter=Quarter, Entity=Entity, GL_Code=GL_Code, Location = Location, Month = Month, Currency = Currency, GL_Name = GL_Name, Expense_Category=Expense_Category, BU = BU, GL_Desc= GL_Desc, Plan=float(Plan), Forecast=Forecast, Accrual=Accrual, Plan_vs_Forecast = float(Plan) - Forecast, Plan_vs_Accrual = float(Plan)-Forecast, Forecast_vs_Accrual = Forecast - Accrual)
            opex_input.set_user(request.user)
            opex_input.save()
            success_message = (f"OPEX Data Has Been Successfuly Entered for {Location} Location in the Month of {custom_filters.get_month_name(Month)}-{Year} Under {Expense_Category} Category for GL {GL_Code} With Plan Amount of {Plan}.")
            request.session['success_message'] = success_message
            return redirect(reverse('OPEX_Input') + '?success_message=' + success_message)
        else:
            success_message = request.session.pop('success_message', '')
            return render (request, 'OPEX/OPEX_Upload.html', {'success_message': success_message})  

def Opex_View(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        username = request.user.username
        UserLocation = AuthorisedUser.objects.get(userid=username)
        user_location = UserLocation.user_location
        opex_data = OPEX_Data.objects.all().order_by('Month', 'Location', 'Entity')
        filtered_data = opex_data.filter(Location=user_location)

        if request.user.groups.filter(name='Admin-Leaders').exists():
            opex_data = opex_data
        else:
            opex_data = filtered_data
        if not opex_data:
            return render(request, 'OPEX/OPEX_Data.html', {'error_message': 'No Records To Display!'})
        
        context = {}
        current_data = OPEX_Data.objects.filter(Year=datetime.today().year, Month=datetime.today().month)
        latest_report = OPEX_Data.objects.latest('Month')
        latest_data = opex_data.filter(Month=latest_report.Month, Year= latest_report.Year)

        if not current_data:
            opex_data = latest_data

        year = request.GET.get('year')
        quarter = request.GET.get('quarter')        
        month = request.GET.get('month')
        location = request.GET.get('location')
        category = request.GET.get('category')

        record_count = request.GET.get('record_count')
        records = 100 if record_count == '' or record_count == None else int(record_count)

        if month == None and location == None and category == None and quarter == None and year == None:
            opex_data = current_data
        else:
            if month !='All':
                opex_data = opex_data.filter(Month=month)
            if location !='All':
                opex_data = opex_data.filter(Location=location)
            if category !='All':
                opex_data = opex_data.filter(Expense_Category=category) 
            if year !='All':
                opex_data = opex_data.filter(Year=year)
            if quarter !='All':
                opex_data = opex_data.filter(Quarter=quarter)


        paginated_opex_data = Paginator(opex_data, records)
        page_number = request.GET.get('page')
        opex_page_obj = paginated_opex_data.get_page(page_number)
        context = {
            'opex_page_obj':opex_page_obj, 'records': records, 'year':year, 'quarter':quarter, 'month':month, 'location':location, 'category':category,
            'months': sorted(list(set(opex_data.values_list('Month', flat=True)))),
            'locations':sorted(list(set(OPEX_Data.objects.values_list('Location', flat=True)))),
            'categories' : sorted(list(set(OPEX_Data.objects.values_list('Expense_Category', flat=True)))),
            'quarters' : sorted(list(set(OPEX_Data.objects.values_list('Quarter',  flat=True)))),
            'years' :sorted(list(set(OPEX_Data.objects.values_list('Year',  flat=True))))
        }

        return render(request, 'OPEX/OPEX_Data.html', context)
    
@user_passes_test(user_in_managers_group)
def update_opex_data(request, opex_data_id):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        opex_data = OPEX_Data.objects.get(id=opex_data_id)

        if request.method == 'POST':
            opex_data.Plan = opex_data.Plan
            opex_data.Forecast = request.POST.get('Forecast')
            opex_data.Accrual = request.POST.get('Accrual')
            opex_data.Plan_vs_Forecast = round((float(opex_data.Plan) if pd.notna(opex_data.Plan) else 0.00) - (float(opex_data.Forecast) if pd.notna(opex_data.Forecast) else 0.00), 2)
            opex_data.Plan_vs_Accrual = round((float(opex_data.Plan) if pd.notna(opex_data.Plan) else 0.00) - (float(opex_data.Accrual) if pd.notna(opex_data.Accrual) else 0.00), 2)
            opex_data.Forecast_vs_Accrual = round((float(opex_data.Forecast) if pd.notna(opex_data.Forecast) else 0.00) - (float(opex_data.Accrual) if pd.notna(opex_data.Accrual) else 0.00), 2)
            opex_data.save()
            return redirect('OpexView')  
        context = {
            'opex_data': opex_data,
        }
    return render(request, 'OPEX\\update_opex_data.html', context)

@user_passes_test(is_superuser)
def Delete_Opex(request, id):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        opexdata = OPEX_Data.objects.get(pk=id)
        opexdata.delete()
        return redirect("OpexView")

# def Future_Opex(request):
#     if request.method == 'POST':
#         year = request.POST.get('year')
#         country = request.POST.get('country')
#         location = request.POST.get('location')
#         gl_code = request.POST.get('gl_code')
#         percent = request.POST.get('percent')
#         prev_years_data=OPEX_Data.objects.filter(Year=year-1, Location=location, GL_Code=gl_code).first()
#         if prev_years_data:
#             quarter = prev_years_data.Quarter
#             month = prev_years_data.Month
#             year = prev_years_data.Year+1
#             country = prev_years_data.Country
#             location = prev_years_data.Location
#             new_plan = prev_years_data.Plan * 1+ (percent/100)



def OPEX_Report(request):
    if request.user.is_anonymous:
            return redirect('/login')             
    else:
        def calculate_percentage_diff(initial_value, current_value):
            if initial_value is None or initial_value == 0 or current_value is None:
                return  None
            return (current_value - initial_value)/initial_value * 100
       
        data = OPEX_Data.objects.exclude(Location__in=('Taguig', 'Pasig', 'Cebu', 'Guwahati', 'Makati', 'Noida', 'India', 'Chandigarh', 'Philippines')).exclude(Expense_Category__in=('C&B', 'Legal', 'Allocation', 'Contract Headcount', 'Transport', 'Insurance', 'Permanent Headcount', 'Travel', 'Employment', 'Training'))
        if not data:
            return render(request, 'Charts/opex_report.html', {'error_message': 'No Records To Display!'}) 

        opex_data = data
        YoY = data
        comparision_data = data


        mnth = request.GET.get('month')
        loc = request.GET.get('location')
        curr = request.GET.get('currency')
        yrs = request.GET.get('year')
        qtr = request.GET.get('quarter')
        ctry = request.GET.get('country')

        context = {}
        latest_year = data.latest('Year').Year
        current_year = datetime.today().year
        latest_data = opex_data.filter(Year=current_year)
        
        if not latest_data:
            latest_data = opex_data.filter(Year=latest_year)
        if mnth == 'All' and ctry=='All'and loc == 'All' and qtr =='All' and yrs == 'All' or mnth == None and loc == None and ctry==None and qtr == None and yrs == None:
            opex_data = latest_data
        else:
            if mnth != 'All':
                opex_data = opex_data.filter(Month=mnth)
                YoY = YoY.filter(Month=mnth)
                comparision_data = comparision_data.filter(Month=mnth)
            if qtr != 'All':
                opex_data = opex_data.filter(Quarter=qtr)
                YoY = YoY.filter(Quarter=qtr)
                comparision_data = comparision_data.filter(Quarter=qtr)
            if ctry != 'All':
                opex_data = opex_data.filter(Country=ctry)
                YoY = YoY.filter(Country=ctry)
                comparision_data = comparision_data.filter(Country=ctry)
            if loc != 'All':
                opex_data = opex_data.filter(Location=loc)
                YoY = YoY.filter(Location=loc)
                comparision_data = comparision_data.filter(Location=loc)
            if yrs != 'All':
                opex_data = opex_data.filter(Year=yrs)

        for row in comparision_data.values('Country', 'Year'):
            forex_data = Forex.objects.get(year=row['Year'], country=row['Country'])
            usd_rate = forex_data.usd_rate


        def usd_conversion(val, val2, val3):
            forex_data = Forex.objects.get(country=val3, year=val2)
            usd_value = float(val/forex_data.usd_rate)
            return usd_value
            
        # Last 5 Years Comparision
        last_5_years = list(range(current_year-4, current_year +1))

        yearly_data_accrual = comparision_data.filter(Year__in=last_5_years)\
            .values('Country', 'Expense_Category') \
            .annotate(
            year1=Sum('Accrual', filter=Q(Year=last_5_years[0])), 
            year2=Sum('Accrual', filter=Q(Year=last_5_years[1])),
            year3=Sum('Accrual', filter=Q(Year=last_5_years[2])),
            year4=Sum('Accrual', filter=Q(Year=last_5_years[3])),
            year5=Sum('Accrual', filter=Q(Year=last_5_years[4]))).order_by('Expense_Category')
        
        for entry in yearly_data_accrual:
            entry['percentage_diff_year2'] = calculate_percentage_diff(entry['year1'], entry['year2'])
            entry['percentage_diff_year3'] = calculate_percentage_diff(entry['year2'], entry['year3'])
            entry['percentage_diff_year4'] = calculate_percentage_diff(entry['year3'], entry['year4'])
            entry['percentage_diff_year5'] = calculate_percentage_diff(entry['year4'], entry['year5'])
            entry['year1'] = (usd_conversion(entry['year1'], last_5_years[0], entry['Country']) if curr =='USD' else entry['year1']) if entry['year1'] != None else 0
            entry['year2'] = (usd_conversion(entry['year2'], last_5_years[1], entry['Country']) if curr =='USD' else entry['year2']) if entry['year2'] != None else 0
            entry['year3'] = (usd_conversion(entry['year3'], last_5_years[2], entry['Country']) if curr =='USD' else entry['year3']) if entry['year3'] != None else 0
            entry['year4'] = (usd_conversion(entry['year4'], last_5_years[3], entry['Country']) if curr =='USD' else entry['year4']) if entry['year4'] != None else 0
            entry['year5'] = (usd_conversion(entry['year5'], last_5_years[4], entry['Country']) if curr =='USD' else entry['year5']) if entry['year5'] != None else 0


        yearly_data_plan = comparision_data.filter(Year__in=last_5_years) \
            .values('Expense_Category', 'Country') \
            .annotate(
            year1=Sum('Plan', filter=Q(Year=last_5_years[0])), 
            year2=Sum('Plan', filter=Q(Year=last_5_years[1])),
            year3=Sum('Plan', filter=Q(Year=last_5_years[2])),
            year4=Sum('Plan', filter=Q(Year=last_5_years[3])),
            year5=Sum('Plan', filter=Q(Year=last_5_years[4]))).order_by('Expense_Category')
        
        for entry in yearly_data_plan:
            entry['percentage_diff_year2'] = calculate_percentage_diff(entry['year1'], entry['year2'])
            entry['percentage_diff_year3'] = calculate_percentage_diff(entry['year2'], entry['year3'])
            entry['percentage_diff_year4'] = calculate_percentage_diff(entry['year3'], entry['year4'])
            entry['percentage_diff_year5'] = calculate_percentage_diff(entry['year4'], entry['year5'])
            entry['year1'] = (usd_conversion(entry['year1'], last_5_years[0], entry['Country']) if curr =='USD' else entry['year1']) if entry['year1'] != None else 0
            entry['year2'] = (usd_conversion(entry['year2'], last_5_years[1], entry['Country']) if curr =='USD' else entry['year2']) if entry['year2'] != None else 0
            entry['year3'] = (usd_conversion(entry['year3'], last_5_years[2], entry['Country']) if curr =='USD' else entry['year3']) if entry['year3'] != None else 0
            entry['year4'] = (usd_conversion(entry['year4'], last_5_years[3], entry['Country']) if curr =='USD' else entry['year4']) if entry['year4'] != None else 0
            entry['year5'] = (usd_conversion(entry['year5'], last_5_years[4], entry['Country']) if curr =='USD' else entry['year5']) if entry['year5'] != None else 0

        # Plan_Vs_Accural Chart
        plan_vs_accrual_data = []
        for plan_cat in opex_data.values('Expense_Category').distinct():
            opex = opex_data.filter(Expense_Category=plan_cat['Expense_Category']).aggregate(
                plan_sum=ExpressionWrapper( models.Sum('Plan'), output_field=FloatField()),
                accrual_sum=ExpressionWrapper(models.Sum('Accrual'), output_field=FloatField()),
                plan_vs_accrual_diff=ExpressionWrapper( models.Sum(F('Plan') - F('Accrual')), output_field=FloatField()))
            
            if opex['plan_sum'] == 0 and opex['accrual_sum']  == 0:
                percentage = 0
            
            elif opex['accrual_sum'] == 0:
                percentage = 100
            
            elif opex['plan_sum'] == 0:
                percentage = 0

            elif opex['plan_vs_accrual_diff'] is None or opex['plan_sum'] is None:
                percentage = 0
            elif opex['plan_sum'] == 0 and opex ['accrual_sum'] > 0:
                percentage = 100
            else:
                percentage = ((opex['plan_vs_accrual_diff'] / opex['plan_sum']) * 100)

            plan_vs_accrual_data.append({
                'category': plan_cat['Expense_Category'],
                'percentage': round(percentage, 2)})
            
        plan_vs_accr_data_year = []
        for plan_year in comparision_data.filter(Year__in=last_5_years).values('Year').distinct():
            Year = comparision_data.filter(Year=plan_year['Year']).aggregate(
                plan_sum=ExpressionWrapper( models.Sum('Plan'), output_field=FloatField()),
                accrual_sum=ExpressionWrapper(models.Sum('Accrual'), output_field=FloatField()),
                plan_vs_accrual_diff=ExpressionWrapper( models.Sum(F('Plan') - F('Accrual')), output_field=FloatField()))
            
            if Year['plan_sum'] == 0 and Year['accrual_sum']  == 0:
                percentage = 0
            
            elif Year['accrual_sum'] == 0:
                percentage = 100
            
            elif Year['plan_sum'] == 0:
                percentage = 0

            elif Year['plan_vs_accrual_diff'] is None or Year['plan_sum'] is None:
                percentage = 0
            elif Year['plan_sum'] == 0 and Year ['accrual_sum'] > 0:
                percentage = 100
            else:
                percentage = ((Year['plan_vs_accrual_diff'] / Year['plan_sum']) * 100)

            plan_vs_accr_data_year.append({
                'year': plan_year['Year'],
                'percentage': round(percentage, 2)})

        # # Plan Vs Forecast Chart
        # plan_vs_fore_data = []
        # for fore_cat in opex_data.values('Expense_Category').distinct():
        #     opex = opex_data.filter(Expense_Category=fore_cat['Expense_Category']).aggregate(
        #         plan_sum=ExpressionWrapper( models.Sum('Plan'), output_field=FloatField()),
        #         forecast_sum=ExpressionWrapper( models.Sum('Forecast'), output_field=FloatField()),
        #         plan_vs_forecast_diff=ExpressionWrapper( models.Sum(F('Plan') - F('Forecast')), output_field=FloatField()))
            
        #     if opex['plan_sum'] == 0 and opex['forecast_sum'] == 0:
        #         percentage = 0
        #     elif opex['forecast_sum'] == 0:
        #         percentage = 100
        #     elif opex['plan_sum'] == 0:
        #         percentage = 0

        #     elif opex['plan_vs_forecast_diff'] is None or opex['plan_sum'] is None:
        #         percentage = 0
        #     elif opex['plan_sum'] == 0 and opex ['forecast_sum'] > 0:
        #         percentage = 100
        #     else:
        #         percentage = ((opex['plan_vs_forecast_diff'] / opex['plan_sum']) * 100)

        #     plan_vs_fore_data.append({
        #         'category': fore_cat['Expense_Category'],
        #         'percentage': round(percentage, 2)})

        #Forecast Vs Accrual Chart
        fore_vs_accr_data = []
        for acc_cat in opex_data.values('Expense_Category').distinct():
            opex = opex_data.filter(Expense_Category=acc_cat['Expense_Category']).aggregate(
                forecast_sum=ExpressionWrapper( models.Sum('Forecast'), output_field=FloatField()),
                accrual_sum=ExpressionWrapper( models.Sum('Accrual'), output_field=FloatField()),
                fore_vs_accr_diff=ExpressionWrapper( models.Sum(F('Forecast') - F('Accrual')), output_field=FloatField()))
            
            if opex['forecast_sum'] == 0 and opex['accrual_sum'] == 0:
                percentage = 0
            elif opex['accrual_sum'] == 0:
                percentage = 100
            elif opex['forecast_sum'] == 0:
                percentage = 100
            elif opex['fore_vs_accr_diff'] is None or opex['forecast_sum'] is None:
                percentage = 0
            elif opex['forecast_sum'] == 0 and opex ['accrual_sum'] > 0:
                percentage = 100
            else:
                percentage = ((opex['fore_vs_accr_diff'] / opex['forecast_sum']) * 100)

            fore_vs_accr_data.append({
                'category': acc_cat['Expense_Category'],
                'percentage': round(percentage, 2)})


        def highlight_diff(val):
            if curr == 'USD':
                val = val.replace('$ ','')
                val = int(val)
            else:
                val = int(val)/int(usd_rate)

                if int(val) <= 0:
                    return 'background-color :red; color:white;'
                elif int(val) > 0 and int(val) < 250:
                    return 'background-color :yellow; color:black;'
                else:
                    return ''


        # Plan Vs Accrual Pivot Table
        month_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        df1 = pd.DataFrame(list(opex_data.values("Month", "Expense_Category", 'Plan_vs_Accrual') ))
        df1['Category'] = df1['Month'].apply(lambda x: month_names[x-1])
        df1_pivot = df1.pivot_table(index='Expense_Category', columns=['Month', 'Category'], values='Plan_vs_Accrual', fill_value=0.00, aggfunc='sum', margins=True, margins_name='Total')
        df1_pivot = df1_pivot.applymap(lambda x: '$ {:.0f}'.format(x/usd_rate) if isinstance(x, (float)) else x) if curr == 'USD' else df1_pivot.applymap(lambda x: '{:.0f}'.format(x) if isinstance(x, (float)) else x)
        df1_pivot = df1_pivot.style.applymap(highlight_diff)

        # Plan Vs Forecast Pivot Table
        # df2 = pd.DataFrame(list(opex_data.values("Expense_Category", "Month", 'Plan_vs_Forecast')))
        # df2['Category'] = df2['Month'].apply(lambda x: month_names[x-1])
        # df2_pivot = df2.pivot_table(index='Expense_Category', columns=['Month', 'Category'], fill_value=0.00, aggfunc='sum', margins=True, margins_name='Total')
        # df2_pivot = df2_pivot.applymap(lambda x: '$ {:.0f}'.format(x/usd_rate) if isinstance(x, (float)) else x) if currency == 'USD' else df2_pivot.applymap(lambda x: '{:.0f}'.format(x) if isinstance(x, (float)) else x)
        # df2_pivot = df2_pivot.style.applymap(highlight_diff)

        # Forecast Vs Accrual Pivot Table

        df3 = pd.DataFrame(list(opex_data.values("Expense_Category", "Month", 'Forecast_vs_Accrual')))
        df3['Category'] = df3['Month'].apply(lambda x: month_names[x-1])
        df3_pivot = df3.pivot_table(index='Expense_Category', columns=['Month', 'Category'], fill_value=0.00, aggfunc='sum', margins=True, margins_name='Total')
        df3_pivot = df3_pivot.applymap(lambda x: '$ {:.0f}'.format(x/usd_rate) if isinstance(x, (float)) else x) if curr == 'USD' else df3_pivot.applymap(lambda x: '{:.0f}'.format(x) if isinstance(x, (float)) else x)
        df3_pivot = df3_pivot.style.applymap(highlight_diff)



        # Comparision of Last 3 Years
        # last_three_years = [current_year - i for i in range(3)]
        # df4 = pd.DataFrame(YoY.values("Year", "Expense_Category","Plan", "Forecast", 'Accrual'))
        # df4['Year'] = df4['Year'].astype(int)
        # filtered_df4 = df4[df4['Year'].isin(last_three_years)]
        # filtered_df4 = filtered_df4.pivot_table(index="Expense_Category", columns="Year", fill_value=0.00, aggfunc='sum')
        # filtered_df4 = filtered_df4.applymap(lambda x: '$ {:.0f}'.format(x/usd_rate) if isinstance(x, (float)) else x) if currency == 'USD' else filtered_df4.applymap(lambda x: '{:.0f}'.format(x) if isinstance(x, (float)) else x)

        df5 = pd.DataFrame(list(opex_data.values("Location", "Month", 'Plan_vs_Accrual')))
        df5['Location Name'] = df5['Month'].apply(lambda x: month_names[x-1])
        df5_pivot = df5.pivot_table(index='Location', columns=['Month', 'Location Name'], fill_value=0.00, aggfunc='sum', margins=True, margins_name='Total')
        # df5_pivot.sort_values(by='Location', inplace=True)
        df5_pivot = df5_pivot.applymap(lambda x: '$ {:.0f}'.format(x/usd_rate) if isinstance(x, (float)) else x) if curr == 'USD' else df5_pivot.applymap(lambda x: '{:.0f}'.format(x) if isinstance(x, (float)) else x)
        df5_pivot = df5_pivot.style.applymap(highlight_diff)

        context = {"dataset3": opex_data,
            'currency': curr,
            'yearly_data_accrual':yearly_data_accrual,
            'plan_vs_accr_data_year' :json.dumps(plan_vs_accr_data_year),
            'yearly_data_plan': yearly_data_plan,
            'year1': last_5_years[0],   
            'year2': last_5_years[1],  
            'year3': last_5_years[2],  
            'year4': last_5_years[3],  
            'year5': last_5_years[4],    
            'pivot_table1' : df1_pivot.to_html(classes='styled-pivot-table'), 
            # 'pivot_table2' : df2_pivot.to_html(), 
            'pivot_table3' : df3_pivot.to_html(), 
            # 'pivot_table4' : filtered_df4.to_html(),
            'pivot_table5': df5_pivot.to_html(classes='styled-pivot-table'), 
            'plan_vs_accrual_data': json.dumps(plan_vs_accrual_data), 
            # 'plan_vs_fore_data': json.dumps(plan_vs_fore_data), 
            'fore_vs_accr_data':json.dumps(fore_vs_accr_data),
            "months" : sorted(list(set(data.values_list('Month', flat=True)))),
            "quarters" : sorted(list(set(data.values_list('Quarter', flat=True)))),
            "locations" : sorted(list(set(data.values_list('Location', flat=True)))),
            "countries" : sorted(list(set(data.values_list('Country', flat=True)))),
            "years" : sorted(list(set(data.values_list('Year',  flat=True))))}
        return render(request, 'Charts/opex_report.html', context)
