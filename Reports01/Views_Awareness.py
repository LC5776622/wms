from django.shortcuts import render, redirect, reverse, get_object_or_404
from Reports01.models import AuthorisedUser, LocationModel, Course, Acknowledgement, Question, UserResponse, TrainingCalendar, UserScores, User
from django.conf import settings
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Count, Sum, F, FloatField, Q, ExpressionWrapper, Value, Case, When
from django.utils import timezone
import os
import json
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from .views import user_in_managers_group, user_passes_test, is_superuser, user_in_leaders_group

@user_passes_test(user_in_leaders_group)
def Upload_Course(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        if request.method == 'POST' and request.FILES['pdf_file']:
            user = request.user
            title = request.POST['title']
            version = request.POST['version']
            pdf_file = request.FILES['pdf_file']
            uploaded_at = timezone.now()
            uploaded_pdf = Course.objects.create(title=title, uploaded_by=user, uploaded_at=uploaded_at,  version=version, pdf_file=pdf_file)
            success_message = (f"'{title}' Training/Awareness Presentation Successfully Uploaded.")
            request.session['success_message'] = success_message
            return redirect(reverse('Upload_Course') + '?success_message=' + success_message)   
        else:
            success_message = request.session.pop('success_message', '')
            context = {'success_message': success_message,} 
            return render(request, 'Awareness/Upload.html', context)

@user_passes_test(user_in_leaders_group)
def Approve_Course(request, course_id):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        course = get_object_or_404(Course, id=course_id)
        if request.method == 'POST':
            course.approved_by = request.user
            course.approved_at =timezone.now()
            course.is_approved = True
            course.save()
            return redirect ('View_Courses')
        context= {
            'course':course, 
        }
        return render(request, 'Awareness/Approve_Course.html', context)

def View_Courses(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        user=request.user
        date = timezone.now()
        year = date.year
        quarter = (date.month -1) // 3 +1

        courses = Course.objects.filter(is_active=True)
        if not courses:
            return render(request, 'Awareness/View_Courses.html', {'error_message': 'No Awareness/ Training Course Available.'}) 
        acknowledged_courses = Acknowledgement.objects.filter(user=user, course_year=year, course_quarter=quarter, acknowledgement_status="Acknowledged").values_list('course__id', flat=True)
        # completed_courses = UserResponse.objects.filter(user=user, course_year=year, course_quarter=quarter).values_list('course__id', flat=True)
        completed_courses=UserScores.objects.filter(user=user, year=year, quarter=quarter, is_completed=True).values_list('course__id', flat=True)

        context = {
            'courses':courses,
            'acknowledged_courses':acknowledged_courses,
            'completed_courses':completed_courses,
        }
        return render(request, 'Awareness/View_Courses.html', context)

@user_passes_test(user_in_leaders_group)
def Archived_Courses(request):
        courses = Course.objects.filter(is_active=False)
        if not courses:
            return render(request, 'Awareness/Archived_Courses.html', {'error_message': 'No Older Versions Of Courses Available.'}) 
        course = request.GET.get('course')
        if course == None:
            courses = courses
        else:
            if course != 'All':
                courses = courses.filter(title=course)
        context = {
            'courses':courses,
            'course_list': sorted(set(list(Course.objects.values_list('title', flat=True))))
        }
        return render(request, 'Awareness/Archived_Courses.html', context)

@user_passes_test(user_in_leaders_group)
def Update_Course(request, course_id):
    if request.user.is_anonymous:
        return redirect('/login')
    else:

        existing_course = get_object_or_404(Course, id=course_id)
        
        if request.method == 'POST':
            user = request.user
            updated_pdf = request.FILES['pdf_file']
            change_desc = request.POST.get('ChangeDesc')
            updated_at = timezone.now()
            new_course = Course.objects.create(title=existing_course.title, change_desc=change_desc, updated_at=updated_at,  updated_by= user, pdf_file=updated_pdf, version=existing_course.version + .1, is_active=True)
            existing_course.is_active = False
            existing_course.archived_at = timezone.now()
            existing_course.save()
            questions_to_update= Question.objects.filter(course=existing_course)
            for question in questions_to_update:
                question.course = new_course
                question.save()
            return redirect ('View_Courses')
        context= {
            'existing_course':existing_course, 
        }
        return render(request, 'Awareness/Update_Course.html', context)
    
@user_passes_test(is_superuser)
def Delete_Course(request, id):
    if request.user.is_anonymous:
            return redirect('/login')
    else:
        file_model = get_object_or_404(Course, id=id)
        file_path = os.path.join(settings.MEDIA_ROOT, file_model.pdf_file.name)
        course_data = Course.objects.get(pk=id)
        course_data.delete()
        if os.path.exists(file_path):
            os.remove(file_path)
        file_model.delete()

        return redirect("View_Courses")

def Version_Control(request, course_id):
    course = get_object_or_404(Course, id=course_id)
   
    context = {
        'course':course,
    }
    return render (request, 'Awareness/Version_Control.html', context)

def Slide_Show(request, course_id):
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

        user=request.user
        date = timezone.now()
        year = date.year
        quarter = (date.month -1) // 3 +1
        acknowledged_courses = Acknowledgement.objects.filter(user=user, course_year=year, course_quarter=quarter, acknowledgement_status="Acknowledged").values_list('course__id', flat=True)
        response_data = UserResponse.objects.filter(course_id=course_id, userid=username, course_quarter=quarter, )
        completed_courses=UserScores.objects.filter(user=user, year=year, quarter=quarter, is_completed=True).values_list('course__id', flat=True)
        course = get_object_or_404(Course, id=course_id)
        uploaded_pdf = Course.objects.get(id=course_id)
        context = {
            'completed_courses': completed_courses,
            'response_data':response_data,
            'course':course, 'uploaded_pdf':uploaded_pdf,
                'acknowledged_courses':acknowledged_courses,
                    'subLocations': json.dumps(subLocations),
                    'locations':sorted(list(set(Locations.values_list('location', flat= True)))),
                    'countries':sorted(list(set(Locations.values_list('country', flat= True)))),
                    'user_country': user_country,
                    'user_location' : user_location,
                    'user_sub_loc' :user_sub_Loc}
        return render(request, 'Awareness/SlideShow.html', context)

def Acknowledgement_Input(request, course_id):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        date = datetime.today()
        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return render(request, 'error.html', {'error': 'Course Not Found!'})
        userid = request.user.username
        user_name = f"{request.user.last_name}, {request.user.first_name}"
        UserLocation = AuthorisedUser.objects.get(userid=userid)
        user_country = UserLocation.user_country
        user_location = UserLocation.user_location
        if request.method == 'POST':
            rating = request.POST.get('Rating')
            acknowledgement_status = "Acknowledged" if request.POST.get('radio') == 'on' else "Not Acknowledged"
            feedback_suggestion = request.POST.get('feedback_suggestion')
            acknowledgement_date = timezone.now()
            acknowledgement_input = Acknowledgement(course=course, course_year=date.year, rating=rating, course_quarter=(date.month -1) // 3 +1, course_month= date.month, course_name=course.title, course_version=course.version, user_country = user_country, user_location = user_location, userid=userid, user_name=user_name, acknowledgement_status=acknowledgement_status, feedback_suggestion=feedback_suggestion, user=request.user, acknowledgement_date=acknowledgement_date)
            acknowledgement_input.save()
            return redirect('Quiz_View', course_id=course_id)
            # success_message = (f"Hello {user_name}, Your acknowledgement has been successfully recorded for {course_name} course.")
            # request.session['success_message'] = success_message
            # return redirect(reverse('Acknowledgement') + '?success_message=' + success_message)
        
        # else:
            # success_message = request.session.pop('success_message', '')
            # context = {'success_message': success_message, 'course' : course}
        # return render (request, 'Awareness/Acknowledgement.html', {'course' : course})

def Acknowledgement_View(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        userid = request.user.username
        UserLocation = AuthorisedUser.objects.get(userid=userid)
        user_country = UserLocation.user_country
        user_location = UserLocation.user_location
        acknowledgements = Acknowledgement.objects.all().order_by('course_month')
        filtered_data = acknowledgements.filter(user_location=user_location)
        user_data = acknowledgements.filter(userid=userid)

        if request.user.groups.filter(name='Admin-Leaders').exists():
            acknowledgements = acknowledgements
        
        elif request.user.groups.filter(name='Admin-Managers').exists():
            acknowledgements = filtered_data

        else:
            acknowledgements = user_data

        if not acknowledgements:
            return render(request, 'Awareness/Acknowledgement_View.html', {'error_message': 'No Records To Display!'})

        context = {}  
        latest_report = Acknowledgement.objects.latest('course_month')
        latest_month = latest_report.course_month
        latest_data = acknowledgements.filter(course_month=latest_month)

        course_year = request.GET.get('course_year')
        course_quarter = request.GET.get('course_quarter')
        course_month = request.GET.get('course_month')
        user_country = request.GET.get('user_country')
        user_location = request.GET.get('user_location')

        if course_year == None and course_quarter==None and course_month == None and user_country==None and user_location == None:
            acknowledgements = latest_data
        else:
            if course_year != 'All':
                acknowledgements = acknowledgements.filter(course_year=course_year)
            if course_quarter != 'All':
                acknowledgements = acknowledgements.filter(course_quarter=course_quarter) 
            if course_month != 'All':
                acknowledgements = acknowledgements.filter(course_month=course_month)
            if user_country != 'All':
                acknowledgements = acknowledgements.filter(user_country=user_country) if request.user.groups.filter(name='Admin-Leaders').exists() else acknowledgements
            if user_location != 'All':
                acknowledgements = acknowledgements.filter(user_location=user_location) if request.user.groups.filter(name='Admin-Leaders').exists() else acknowledgements
        

        context['acknowledgements'] =acknowledgements
        context["course_years"] = sorted(list(set(Acknowledgement.objects.values_list('course_year',  flat=True))))
        context["course_quarters"] = sorted(list(set(Acknowledgement.objects.values_list('course_quarter', flat=True))))
        context["course_months"] = sorted(list(set(Acknowledgement.objects.values_list('course_month', flat=True))))
        context["user_countries"] = sorted(list(set(Acknowledgement.objects.values_list('user_country', flat=True))))
        context["user_locations"] = sorted(list(set(Acknowledgement.objects.values_list('user_location', flat=True))))
        return render(request,  'Awareness/Acknowledgement_View.html', context)

def Quiz_View(request, course_id):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        username = request.user.username
        UserLocation = AuthorisedUser.objects.get(userid=username)
        auth_user=AuthorisedUser.objects.values('id').filter(userid=username)
        user_country = UserLocation.user_country
        user_location = UserLocation.user_location
        date = datetime.today()
        month = date.month
        year = date.year
        quarter = (date.month -1) // 3 + 1

        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return render(request, 'error.html', {'error': 'Course Not Found!'}) 

        questions = Question.objects.filter(course=course)

        if request.method == 'POST':
            course_name = request.POST.get('course_name')
            userid = request.POST.get('userid')
            user_name = request.POST.get('user_name')
            for question in questions:
                selected_option = request.POST.get(f"question_{question.id}")
                if selected_option == question.correct_option:
                    is_correct = True
                else:
                    is_correct = False
                 
                UserResponse.objects.create(user_country = user_country, user_location=user_location, auth_user_id=auth_user, user=request.user, course_year=year, course_quarter=quarter, course_month=month, course_date=date, userid=userid, user_name=user_name, course=course, course_name=course_name, question=question, selected_option=selected_option, is_correct=is_correct)

                course_data = UserResponse.objects.filter(course=course, user=request.user)
                total_questions = len(course_data)
                correct_answers = 0
                for response in course_data:
                    if response.selected_option == response.question.correct_option:
                        correct_answers +=1
                percentage = round((correct_answers/total_questions) * 100, 2)
            UserScores.objects.create(country=user_country, location=user_location, user=request.user, auth_user_id=auth_user, course=course, course_name=course_name, year=year, quarter=quarter, month=month, percentage=percentage, is_completed = True if percentage > 80 else False, completion_date= date if percentage > 80 else None, )
            return redirect('Quiz_Results', course_id=course_id)

        context = {'questions':questions, 'course':course}
        return render(request, 'Awareness/Quiz.html', context)

def User_Responses(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
            userid = request.user.username
            UserLocation = AuthorisedUser.objects.get(userid=userid)
            user_country = UserLocation.user_country
            user_location = UserLocation.user_location
            response_data = UserResponse.objects.all().order_by('course_month')
            filtered_data = response_data.filter(user_location=user_location)
            user_data = response_data.filter(userid=userid)
            if request.user.groups.filter(name='Admin-Leaders').exists():
                response_data = response_data    
            elif request.user.groups.filter(name='Admin-Managers').exists():
                response_data = filtered_data
            else:
                response_data = user_data
            if not response_data:
                return render(request, 'Awareness/User_Response.html', {'error_message': 'No Records To Display!'})    
            user_responses = UserResponse.objects.filter(userid=userid)

            context = {}  
            latest_report = UserResponse.objects.latest('course_date')
            latest_date = latest_report.course_date
            latest_data = response_data.filter(course_date=latest_date)

            course_year = request.GET.get('course_year')
            course_quarter = request.GET.get('course_quarter')
            # course_month = request.GET.get('course_month')
            course_name= request.GET.get('course_name')
            user_country = request.GET.get('user_country')
            user_location = request.GET.get('user_location')


            if course_year == None and course_quarter==None and course_name== None and user_country==None and user_location == None:
                response_data = latest_data
            else:
                if course_year != 'All':
                    response_data = response_data.filter(course_year=course_year)
                if course_quarter != 'All':
                    response_data = response_data.filter(course_quarter=course_quarter) 
                if course_name != 'All':
                    response_data = response_data.filter(course_name=course_name)
                if user_country != 'All':
                    response_data = response_data.filter(user_country=user_country) if request.user.groups.filter(name='Admin-Leaders').exists() else response_data
                if user_location != 'All':
                    response_data = response_data.filter(user_location=user_location)  if request.user.groups.filter(name='Admin-Leaders').exists() else response_data

            context["user_responses"]  = user_responses
            context["response_dataset"] = response_data
            context["courses"] = sorted(list(set(response_data.values_list('course_name',  flat=True))))
            context["course_years"] = sorted(list(set(UserResponse.objects.values_list('course_year',  flat=True))))
            context["course_quarters"] = sorted(list(set(UserResponse.objects.values_list('course_quarter', flat=True))))
            context["courses"] = sorted(list(set(UserResponse.objects.values_list('course_name', flat=True))))
            context["user_countries"] = sorted(list(set(UserResponse.objects.values_list('user_country', flat=True))))
            context["user_locations"] = sorted(list(set(UserResponse.objects.values_list('user_location', flat=True))))
            return render(request, 'Awareness/User_Response.html', context)

def Quiz_Results(request, course_id):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        try:   
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return render(request, 'error.html', {'error': 'Quiz Reponses Not Found!'})

        userid = request.user.username
        user_name = f"{request.user.last_name}, {request.user.first_name}"
        questions = Question.objects.filter(course_id=course)
        user_responses = UserResponse.objects.filter(userid=userid).filter(course_id=course.id)
        if not user_responses:
            return render(request, 'Awareness/Quiz_Result.html', {'error_message': 'No Records To Display! Please Take A Quiz and Return Back to See the Results.'})  


        context = {}  
        latest_report = user_responses.latest('course_date')
        latest_date = latest_report.course_date
        latest_data = user_responses.filter(course_date=latest_date)

        total_questions = len(latest_data)
        correct_answers = 0
        for response in latest_data:
            if response.selected_option == response.question.correct_option:
                correct_answers +=1

        for date in latest_data:
            date.course_date = date.course_date.strftime("%d-%b-%Y")

        percentage = round((correct_answers/total_questions) * 100, 2)
        context = {
            'completion_date':date.course_date,
            'userid' : userid,
            'user_name' :user_name,
            'user_responses' : latest_data,
            'total_questions' : total_questions,
            'correct_answers' : correct_answers,
            'percentage':percentage,
            'course': course,
            'questions':questions
        }
        return render(request, 'Awareness/Quiz_Result.html', context)

def Retake_Quiz(request, course_id):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        course = Course.objects.get(pk=course_id)
        username = request.user.username
        # UserLocation = AuthorisedUser.objects.get(userid=username)
        auth_user=AuthorisedUser.objects.get(userid=username)
        user_country = auth_user.user_country
        user_location = auth_user.user_location
        date = datetime.today()
        month = date.month
        year = date.year
        quarter = (date.month -1) // 3 +1
        questions = Question.objects.filter(course_id=course_id)
        if request.method=='POST':
            course_name = request.POST.get('course_name')
            userid = request.POST.get('userid')
            user_name = request.POST.get('user_name')
            for question in questions:
                new_selected_option = request.POST.get(f"question_{question.id}")   
                if new_selected_option == question.correct_option:
                    is_correct = True
                else:
                    is_correct = False
                user_response, _= UserResponse.objects.get_or_create(user_country=user_country, user_location=user_location, userid=userid, auth_user=auth_user, course_name=course_name, course_year=year, course_quarter=quarter, user=request.user, user_name=user_name, course=course, question=question,)
                user_response.course_month=month
                user_response.course_date=date
                user_response.selected_option = new_selected_option
                user_response.is_correct=is_correct
                user_response.save()


                course_data = UserResponse.objects.filter(course=course, user=request.user)
                total_questions = len(course_data)
                correct_answers = 0
                for response in course_data:
                    if response.selected_option == response.question.correct_option:
                        correct_answers +=1
                percentage = round((correct_answers/total_questions) * 100, 2)
            user_scores, _= UserScores.objects.get_or_create(country=user_country, location=user_location, course_name=course_name, year=year, quarter=quarter, user=request.user, percentage=percentage, auth_user=auth_user, month=month, course=course)
            user_scores.percentage=percentage
            user_scores.is_completed = True if user_scores.percentage > 80 else False
            user_scores.completion_date= date if user_scores.percentage > 80 else None
            user_scores.save()
            return redirect("Quiz_Results", course_id=course_id)

        context = {'questions':questions, 'course':course}
        return render(request, 'Awareness/Retake_Quiz.html', context)

@user_passes_test(user_in_leaders_group)
def Add_Questions(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        if request.method == 'POST':
            course_id = request.POST['course']
            question_text = request.POST['question_text']
            option1 = request.POST['option1']
            option2 = request.POST['option2']
            option3 = request.POST['option3']
            option4 = request.POST['option4']
            correct_option = request.POST['correct_option']
            try:
                course = Course.objects.get(pk=course_id)
            except:
                return render(request, 'Awareness/Add_Questions.html', {'error': 'Invalid Course ID!'})
            question = Question.objects.create(course=course, course_name=course.title, question_text=question_text, option1=option1, option2=option2, option3=option3, option4=option4, correct_option=correct_option)
            return redirect('Add_Questions')

        courses = Course.objects.all()
        return render(request, 'Awareness/Add_Questions.html', {'courses' :courses})

@user_passes_test(user_in_leaders_group)
def View_Questions(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        questions = Question.objects.all()
        if not questions:
            return render(request, 'Awareness/View_Questions.html', {'error_message': 'No Records To Display!'})    
        course = request.GET.get('course')
        if course == None:
            questions = questions

        if course != 'All':
            questions = questions.filter(course_name=course)


        context = {'questions':questions,
                   'courses':set(list(Question.objects.values_list('course_name', flat=True)))}
        return render(request, 'Awareness/View_Questions.html', context)

@user_passes_test(is_superuser)
def Edit_Questions(request, question_id):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        questions = Question.objects.get(pk=question_id)
        if request.method == 'POST':
            questions.question_text = request.POST.get('question_text')
            questions.option1 = request.POST.get("option1")
            questions.option2 = request.POST.get("option2")
            questions.option3 = request.POST.get("option3")
            questions.option4 = request.POST.get("option4")
            questions.correct_option = request.POST.get("correct_option")
            questions.save()
            return redirect("View_Questions")
        context = {
            'questions':questions,
        }
        return render (request, 'Awareness/Edit_Questions.html', context)

@user_passes_test(user_in_managers_group)
def Schedule_Training(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:
        userid = request.user.username
        UserLocation = AuthorisedUser.objects.get(userid=userid)
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
            course_id = request.POST.get('course')
            session = request.POST.get('session')
            initial_date = datetime.strptime(request.POST.get('training_date'), '%Y-%m-%d').date()
            year = initial_date.year
            frequency = request.POST.get('frequency')
            if frequency == 'Monthly':
                repetitions = 12
                interval = timedelta(days=30)
            elif frequency =='Bi-Monthly':
                repetitions = 6
                interval = timedelta(days=63)
            elif frequency =='Quarterly':
                repetitions = 4
                interval = timedelta(days=84)
            elif frequency =='Half-Yearly':
                repetitions = 2
                interval = timedelta(days=175)
            else:
                repetitions = 1
                interval = timedelta(days=364)

            for i in range(repetitions):
                # end_date = initial_date + timedelta(days=364)
                country = country
                frequency = frequency
                location = location
                session = session
                course = Course.objects.get(pk=course_id)
                new_date = initial_date + i * interval
                month = new_date.month
                quarter = (month-1) // 3 +1
                if year == new_date.year:
                    TrainingCalendar.objects.create(country=country, location=location, course=course, session=session, frequency=frequency, planned_date=new_date, planned_year=year, planned_month=month, planned_quarter=quarter )
            return redirect('Schedule_Training')
        
        courses = Course.objects.filter(is_active=True)
        context = {'courses':courses,
            'user_country':user_country,
            'user_location': user_location,
            'locations':json.dumps(Locations),
            'countries':sorted(list(set(Countries.values_list('country', flat= True)))), }
        return render(request, 'Awareness/Schedule_Training.html', context)

def Calendar_View(request):
    current_year = datetime.today().year
    current_quarter = (datetime.today().month -1) //3 + 1
    trainings = TrainingCalendar.objects.select_related('course', 'verified_by')

    training_data = trainings.values(
            'id',
            'verified_by__username',
            'verified_by__first_name',
            'verified_by__last_name',
            'conducted_by',
            'planned_date',
            'planned_year',
            'planned_quarter',
            'frequency',
            'planned_month',
            'session',
            'actual_date',
            'verified_by',
            'verified_date',
            'course__title',
            'country',
            'location'
        ).order_by('planned_date')
    latest_data = training_data.filter(planned_quarter=current_quarter, planned_year=current_year)
    
    year = request.GET.get('year')
    quarter = request.GET.get('quarter')
    month = request.GET.get('month')
    location = request.GET.get('location')
    course = request.GET.get('course')

    if month == None and location == None and course == None and year==None and quarter==None:
        training_data = latest_data
    else:
        if year != 'All':
            training_data = training_data.filter(planned_year=year)
        if quarter != 'All':
            training_data = training_data.filter(planned_quarter=quarter)
        if month != 'All':
            training_data = training_data.filter(planned_month=month)
        if location != 'All':
            training_data = training_data.filter(location=location)
        if course != 'All':
            training_data = training_data.filter(course__title=course)

    # print(training_data)
    context = {
        'training_dataset':training_data,
        'years': sorted(list(set(TrainingCalendar.objects.values_list('planned_year', flat=True)))),
        'quarters': sorted(list(set(training_data.values_list('planned_quarter', flat=True)))),
        'months': sorted(list(set(training_data.values_list('planned_month', flat=True)))),
        'locations': sorted(list(set(training_data.values_list('location', flat=True)))),
        'courses': sorted(list(set(training_data.values_list('course__title', flat=True)))),


    }
    return render (request, 'Awareness/Training_Calendar.html', context)

def Update_Training(request, training_id):
    training_data = TrainingCalendar.objects.get(id=training_id)
    trainings = TrainingCalendar.objects.select_related('course').filter(id=training_id)
    if request.method == 'POST':
        training_data.agenda = request.POST.get('agenda')
        training_data.attendee_teams = request.POST.get('attendee_teams')
        training_data.attendees = request.POST.get('attendees')
        training_data.actual_date = request.POST.get('actual_date')
        training_data.conducted_by = request.POST.get('conducted_by')
        training_data.attendence_sheet = request.FILES['attendence_sheet']
        training_data.training_images = request.FILES['training_images']
        training_data.save()
        return redirect('Calendar_View')
    courses = trainings.values('course__title')
    context = {
        'training_data' : training_data,
        'courses':courses
    }
    return render (request, 'Awareness/Update_Training.html', context)

user_passes_test(user_in_leaders_group)
def Verify_Training(request, training_id):
    verifier = request.user
    training_data = TrainingCalendar.objects.get(id=training_id)
    trainings = TrainingCalendar.objects.select_related('course').filter(id=training_id)
    if request.method == 'POST':
        training_data.verified_by = verifier
        training_data.verified_date = datetime.today()
        training_data.verifier_remarks = request.POST['verifier_remarks']
        training_data.save()
        return redirect('Calendar_View')
    courses = trainings.values(
            'course__title',
            'verified_by__username',
            'verified_by__first_name',
            'verified_by__last_name',)
    context = {
        'training_data' : training_data,
        'courses':courses
    }
    return render (request, 'Awareness/Verify_Training.html', context)

def View_Training_Record(request, training_id):
    training_data = TrainingCalendar.objects.get(id=training_id)
    trainings = TrainingCalendar.objects.select_related('course').filter(id=training_id)
    if request.method == 'POST':
        training_data.actual_date = request.POST.get('actual_date')
        training_data.conducted_by = request.POST.get('conducted_by')
        training_data.attendence_sheet = request.FILES['attendence_sheet']
        training_data.training_images = request.FILES['training_images']
        training_data.save()
        return redirect('Calendar_View')
    courses = trainings.values(
            'course__title',
            'verified_by__username',
            'verified_by__first_name',
            'verified_by__last_name',)
    context = {
        'training_data' : training_data,
        'courses':courses
    }
    return render (request, 'Awareness/View_Training_Record.html', context)

def Awareness_Sumamry(request):
    if request.user.is_anonymous:
        return redirect('/login')
    else:    
        response_data = UserResponse.objects.all().order_by('course_month')
        if not response_data:
            return render(request, 'Charts/Awareness_Summary.html', {'error_message': 'No Records To Display!'})

        context = {}
        date = datetime.now().date()
        current_year = date.year
        current_quarter = (date.month -1)// 3 + 1
        
        user_responses = UserResponse.objects.select_related('user', 'auth_user', 'course', 'user_location', 'course_year', 'course_quarter', ).filter(auth_user__exclude_from_calculation=False, course__userscores__is_completed=True, user__userscores__is_completed=True)
        
        course_year = request.GET.get('course_year')
        course_quarter = request.GET.get('course_quarter')
        course_name = request.GET.get('course_name')
        user_country = request.GET.get('user_country')
        user_location = request.GET.get('user_location')

        latest_response_data = user_responses.filter(course_quarter=current_quarter)

        if course_year == None and course_quarter==None and course_name == None and user_country==None and user_location == None:
            summary_data = latest_response_data
        else:
            
            if course_year != 'All':
                user_responses = user_responses.filter(course_year=course_year)
            if course_quarter != 'All':
                user_responses = user_responses.filter(course_quarter=course_quarter) 
            if course_name != 'All':
                user_responses = user_responses.filter(course_name=course_name)

            if user_country != 'All':
                user_responses = user_responses.filter(user_country=user_country)
            if user_location != 'All':
                user_responses  =  user_responses.filter(user_location=user_location) 

        summary_data = user_responses.values(
            'course__userresponse__course_year',
            'course__userresponse__course_quarter',
            'course__userresponse__course_month',
            'user__userresponse__user_country',
            'user__userresponse__user_location',
            'course__title',
            'course__version',
        ).annotate(
            
        correct_responses = Sum(Case(When(is_correct=True, then=1), default=0)),
        incorrect_responses=Sum(Case(When(is_correct=False, then=1), default=0)),
        average_score = ExpressionWrapper((F('correct_responses') * 100)/ (F('correct_responses') + F('incorrect_responses')),
                                        output_field=FloatField()
                                          ),
        total_users=Count('auth_user', distinct=True),
        course_taken_by_users=Count('user', distinct=True),
        # course_taken_by_users = Count(Case(When(user__userscores__is_completed=True, then=1), default=0))
        )
        
        for row in summary_data:
            user_location = row.get('user__userresponse__user_location')
            location_users = AuthorisedUser.objects.filter(user_location=user_location, exclude_from_calculation=False).count()
            row['location_users'] = location_users
            if int(row['average_score']) >= 80 :
                row['course_taken_by_users'] = row['total_users'] 
            else:
                row['course_taken_by_users'] = 0
            row['course_taken_percentage'] = (row['course_taken_by_users'] * 100) /(row['location_users'])

        
        users = AuthorisedUser.objects.all()
        scores = UserScores.objects.filter(course__is_active=True)
        courses = Course.objects.filter(is_active=True)

        if course_year == 'All' and course_quarter =='All' and course_name == 'All' and user_country == 'All' and  user_location == 'All' or course_year == None and course_quarter == None and course_name == None and user_country == None and  user_location == None:
            users = users
            scores = scores
            courses = courses

        if course_year != 'All':
            scores = scores.filter(year=course_year)
        if course_quarter != 'All':
            scores = scores.filter(quarter=course_quarter) 
        if course_name != 'All':
            courses = courses.filter(title=course_name)
        if user_country != 'All':
            users = users.filter(user_location=user_country)
        if user_location != 'All':
            users  =  users.filter(user_location=user_location) 
        
        combined_data=[]
        for user in users:
            user_courses = {}
            for course in courses:
                user_courses[course] = None
            for score in scores:
                if user == score.auth_user:
                    user_courses[score.course] = {
                        'userid':user.userid,
                        'user_name':user.user_name,
                        'country':user.user_country,
                        'location':user.user_location,
                        'course':course.title,
                        'version':course.version,
                        'year': score.year,
                        'quarter':score.quarter,
                        'is_completed':score.is_completed,
                        'completion_date':score.completion_date,
                        'percentage':score.percentage,
                        'month':score.month,
        
                    }


            combined_data.append({
                        'user':user,
                        'courses': user_courses,
                        'country': user.user_country,
                        'location':user.user_location
                    })
            


        context = {
            'combined_data': combined_data,
            'current_year':current_year,
            'current_quarter': current_quarter,
            'summary_data':summary_data,
            "courses" : sorted(list(set(courses.values_list('title',  flat=True)))),
            "course_years" : sorted(list(set(summary_data.values_list('course__userresponse__course_year',  flat=True)))),
            "course_quarters" : sorted(list(set(summary_data.values_list('course__userresponse__course_quarter', flat=True)))),
            "user_countries" : sorted(list(set(summary_data.values_list('user__userresponse__user_country', flat=True)))),
            "user_locations" : sorted(list(set(summary_data.values_list('user__userresponse__user_location', flat=True)))),
        }
        return render(request, 'Charts/Awareness_Summary.html', context)



