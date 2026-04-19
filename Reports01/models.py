from django.contrib.auth.models import User
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
PERCENTAGE_VALIDATOR = [MinValueValidator(0), MaxValueValidator(100)]


class MBR_Data(models.Model):
    ReportYear = models.IntegerField()
    ReportMonth = models.CharField(max_length=30)
    ReportQuarter =models.CharField(max_length=2)
    ReportLocation = models.CharField(max_length=50)
    ReportCountry = models.CharField(max_length=50)
    AreaSQFT = models.FloatField()
    TotalSeats = models.IntegerField()
    Area_Per_Seat = models.DecimalField(max_digits=5, decimal_places=2)
    Headcount = models.IntegerField()
    OccupiedSeats = models.IntegerField()
    Vacant_Seats = models.IntegerField()
    Utilization = models.DecimalField(max_digits=6, decimal_places=4)
    Laptop = models.IntegerField()
    Desktop = models.IntegerField()
    Dongle = models.IntegerField()
    Accessories = models.IntegerField()
    Total_Assets = models.IntegerField()
    Work_Completed = models.TextField()
    Work_In_Progress = models.TextField()
    Date_Created = models.DateTimeField(auto_now_add=True)
    Date_Updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_created_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_updated_by')
    def save(self, *args, **kwargs):
        user = getattr(self, '_user', None)
        if user:
            if not self.pk:
                self.created_by = user
            self.updated_by = user
            del self._user
        super(MBR_Data, self).save(*args, **kwargs)
    def set_user(self, user):
        self._user = user

class Incident_Data(models.Model):
    Report_Year = models.IntegerField()
    Report_Quarter = models.PositiveSmallIntegerField()
    Report_Month = models.PositiveIntegerField()
    Report_Date = models.DateField()
    Report_Time = models.TimeField()
    Report_Country = models.CharField(max_length=30)
    Report_Location = models.CharField(max_length=50)
    Report_Sub_Loc = models.CharField(max_length=50)
    Inci_Nature = models.TextField(null=True, blank=True)
    Inci_Category = models.CharField(max_length=50)
    Equip_Category = models.CharField(max_length=50)
    Severity = models.CharField(max_length=15)
    Impact = models.BooleanField(default=False) #New
    Incident_Brief = models.TextField()
    Reported_By = models.CharField(max_length=50, null=True, blank=True) #New
    Impact_Desc = models.CharField(max_length=255, default="No Impact") #New
    Corrective_Act = models.TextField()
    Root_Cause = models.TextField()
    Preventive_Act = models.TextField()
    Prev_Act_Resp = models.CharField(max_length=255, null=True, blank=True) #New
    Act_Implement_Date = models.DateField(null=True, blank=True) #New
    Status = models.CharField(max_length=20)
    Closure_Date = models.DateField(blank=True, null=True)
    Remarks = models.TextField(null=True, blank=True)
    Date_Created = models.DateTimeField(auto_now_add=True)
    Date_Updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_created_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_updated_by')
    def save(self, *args, **kwargs):
        user = getattr(self, '_user', None)
        if user:
            if not self.pk:
                self.created_by = user
            self.updated_by = user
            del self._user
        super(Incident_Data, self).save(*args, **kwargs)
    def set_user(self, user):
        self._user = user

class Expense_Heads(models.Model):
    GL_Code = models.IntegerField()
    GL_Name = models.CharField(max_length=200, blank=True, null=True)
    Expense_Head = models.CharField(max_length=200, blank=True, null=True)
    Date_Created = models.DateTimeField(auto_now_add=True)
    Date_Updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_created_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_updated_by')
    def save(self, *args, **kwargs):
        user = getattr(self, '_user', None)
        if user:
            if not self.pk:
                self.created_by = user
            self.updated_by = user
            del self._user
        super(Expense_Heads, self).save(*args, **kwargs)
    def set_user(self, user):
        self._user = user

class OPEX_Data(models.Model):
    Country = models.CharField(max_length=50)
    Year = models.PositiveIntegerField()
    Quarter = models.PositiveSmallIntegerField()
    Month = models.PositiveIntegerField()
    Location = models.CharField(max_length=25)
    Entity = models.CharField(max_length=25)
    BU = models.CharField(max_length=50, blank=True, null=True)
    Currency = models.CharField(max_length=10, blank=True, null=True)
    GL = models.ForeignKey(Expense_Heads, on_delete=models.CASCADE, related_name='data', null=True, blank=True)
    GL_Code = models.IntegerField()
    Expense_Category = models.CharField(max_length=300, blank=True, null=True)
    GL_Name = models.CharField(max_length=300, blank=True, null=True)
    GL_Desc = models.CharField(max_length=300, blank=True, null=True)
    Plan = models.FloatField()
    Forecast = models.FloatField()
    Accrual = models.FloatField()
    Plan_vs_Forecast = models.FloatField()
    Plan_vs_Accrual = models.FloatField()
    Forecast_vs_Accrual = models.FloatField()
    Date_Created = models.DateTimeField(auto_now_add=True)
    Date_Updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_created_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_updated_by')
    def save(self, *args, **kwargs):
        user = getattr(self, '_user', None)
        if user:
            if not self.pk:
                self.created_by = user
            self.updated_by = user
            del self._user
        super(OPEX_Data, self).save(*args, **kwargs)
    def set_user(self, user):
        self._user = user

class Invoice_Data(models.Model):
    Invoice_Year = models.IntegerField()
    Invoice_Quarter = models.CharField(max_length=2)
    Invoice_Month = models.CharField(max_length=20)
    Invoice_Country = models.CharField(max_length=20)
    Invoice_Location = models.CharField(max_length=20)
    Expense_Type = models.CharField(max_length=50, blank=True, null=True)
    Invoice_Vendor = models.CharField(max_length=50, blank=True, null=True)
    Invoice_No = models.CharField(max_length=50, blank=True, null=True)
    Invoice_PO = models.CharField(max_length=300, blank=True, null=True)
    Invoice_Date = models.CharField(max_length=20, blank=True, null=True)
    Invoice_Amount = models.CharField(max_length=300, blank=True, null=True)
    Invoice_Payment_Date = models.CharField(max_length=50, blank=True, null=True)
    Invoice_Processed_By = models.CharField(max_length=50, blank=True, null=True)
    Invoice_Status = models.CharField(max_length=50, blank=True, null=True)
    Date_Created = models.DateTimeField(auto_now_add=True)
    Date_Updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_created_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_updated_by')
    def save(self, *args, **kwargs):
        user = getattr(self, '_user', None)
        if user:
            if not self.pk:
                self.created_by = user
            self.updated_by = user
            del self._user
        super(Invoice_Data, self).save(*args, **kwargs)
    def set_user(self, user):
        self._user = user

class Vendor_Data(models.Model):
    country = models.CharField(max_length=100)
    location = models.CharField(max_length=20)
    category = models.CharField(max_length=100)
    vendor_desc = models.CharField(max_length=200)
    vendor = models.CharField(max_length=200)
    business_address = models.CharField(max_length=500, blank=True, null=True)
    business_email = models.CharField(max_length=200, blank=True, null=True)
    contact_person = models.CharField(max_length=200, blank=True, null=True)
    contact_no = models.CharField(max_length=100, blank=True, null=True)
    Date_Created = models.DateTimeField(auto_now_add=True)
    Date_Updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_created_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_updated_by')
    def save(self, *args, **kwargs):
        user = getattr(self, '_user', None)
        if user:
            if not self.pk:
                self.created_by = user
            self.updated_by = user
            del self._user
        super(Vendor_Data, self).save(*args, **kwargs)
    def set_user(self, user):
        self._user = user

class LocationModel(models.Model):
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    location = models.CharField(max_length=20)
    locationcode = models.CharField(max_length=4)
    sub_locs = models.CharField(max_length=100)
    address = models.CharField(max_length=500, blank=True, null=True)
    contact = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(max_length=200, blank=True, null=True)
    Date_Created = models.DateTimeField(auto_now_add=True)
    Date_Updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_created_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_updated_by')
    def save(self, *args, **kwargs):
        user = getattr(self, '_user', None)
        if user:
            if not self.pk:
                self.created_by = user
            self.updated_by = user
            del self._user
        super(LocationModel, self).save(*args, **kwargs)
    def set_user(self, user):
        self._user = user

class CustomReports(models.Model):
    date = models.DateField(auto_now=True)
    country = models.CharField(max_length=50)
    location = models.CharField(max_length=50)
    report_name = models.CharField(max_length=100)
    url = models.URLField(max_length=1000)
    Date_Created = models.DateTimeField(auto_now_add=True)
    Date_Updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_created_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_updated_by')
    def save(self, *args, **kwargs):
        user = getattr(self, '_user', None)
        if user:
            if not self.pk:
                self.created_by = user
            self.updated_by = user
            del self._user
        super(CustomReports, self).save(*args, **kwargs)
    def set_user(self, user):
        self._user = user
    
class AuthorisedUser(models.Model):
    userid = models.CharField(max_length=9)
    user_name = models.CharField(max_length=100)
    user_country = models.CharField(max_length=100)
    user_location = models.CharField(max_length=50)
    exclude_from_calculation = models.BooleanField(default=False)
    is_manager = models.BooleanField(default=False)
    Date_Created = models.DateTimeField(auto_now_add=True)
    Date_Updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_created_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_updated_by')
    def save(self, *args, **kwargs):
        user = getattr(self, '_user', None)
        if user:
            if not self.pk:
                self.created_by = user
            self.updated_by = user
            del self._user
        super(AuthorisedUser, self).save(*args, **kwargs)
    def set_user(self, user):
        self._user = user

class RoutineDisposal(models.Model):
    Year= models.PositiveIntegerField()
    Month = models.PositiveSmallIntegerField()
    Quarter = models.PositiveSmallIntegerField()
    Disposal_Date = models.DateField()
    Country = models.CharField(max_length=20)
    Location = models.CharField(max_length=20)
    Function = models.CharField(max_length=20)
    Description = models.CharField(max_length=200)
    Waste_Type = models.CharField(max_length=50)
    Waste_State = models.CharField(max_length=20)
    Severity = models.CharField(max_length=20)
    Disposal_Type = models.CharField(max_length=20)
    Unit = models.CharField(max_length=20)
    Quantity = models.FloatField()
    Disposed_By = models.CharField(max_length=50)
    Verified_By = models.CharField(max_length=50)
    Remarks = models.CharField(max_length=200, null=True, blank=True)
    Date_Created = models.DateTimeField(auto_now_add=True)
    Date_Updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_created_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_updated_by')
    def save(self, *args, **kwargs):
        user = getattr(self, '_user', None)
        if user:
            if not self.pk:
                self.created_by = user
            self.updated_by = user
            del self._user
        super(RoutineDisposal, self).save(*args, **kwargs)
    def set_user(self, user):
        self._user = user

class Non_Routine_Disposal(models.Model):
    Year= models.PositiveIntegerField()
    Month = models.PositiveSmallIntegerField()
    Quarter = models.PositiveSmallIntegerField()
    Disposal_Date = models.DateField()
    Country = models.CharField(max_length=20)
    Location = models.CharField(max_length=20)
    Function = models.CharField(max_length=20)
    Description = models.CharField(max_length=100)
    Category = models.CharField(max_length=50)   
    Waste_Type = models.CharField(max_length=20) 
    Waste_State = models.CharField(max_length=20)
    Disposal_Type = models.CharField(max_length=20)
    Severity = models.CharField(max_length=20)
    Unit = models.CharField(max_length=20)
    Quantity = models.FloatField()
    Disposed_By = models.CharField(max_length=30)
    Verified_By = models.CharField(max_length=30)
    Remarks = models.CharField(max_length=200, null=True, blank=True)
    Type = models.CharField(max_length=100)
    Date_Created = models.DateTimeField(auto_now_add=True)
    Date_Updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_created_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_updated_by')
    def save(self, *args, **kwargs):
        user = getattr(self, '_user', None)
        if user:
            if not self.pk:
                self.created_by = user
            self.updated_by = user
            del self._user
        super(Non_Routine_Disposal, self).save(*args, **kwargs)
    def set_user(self, user):
        self._user = user

class E_Waste_Disposal(models.Model):
    Year= models.PositiveIntegerField()
    Month = models.PositiveSmallIntegerField()
    Quarter = models.PositiveSmallIntegerField()
    Disposal_Date = models.DateField()
    Country = models.CharField(max_length=30)
    Location = models.CharField(max_length=30)
    Function = models.CharField(max_length=30)
    Description = models.CharField(max_length=100)
    Category = models.CharField(max_length=50)
    Disposal_Type = models.CharField(max_length=30)
    Severity = models.CharField(max_length=30)
    Unit = models.CharField(max_length=30)
    Quantity = models.IntegerField()
    Disposed_By = models.CharField(max_length=30)
    Verified_By = models.CharField(max_length=30)
    Remarks = models.CharField(max_length=200, null=True, blank=True)
    Type = models.CharField(max_length=100)
    Date_Created = models.DateTimeField(auto_now_add=True)
    Date_Updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_created_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_updated_by')
    def save(self, *args, **kwargs):
        user = getattr(self, '_user', None)
        if user:
            if not self.pk:
                self.created_by = user
            self.updated_by = user
            del self._user
        super(E_Waste_Disposal, self).save(*args, **kwargs)
    def set_user(self, user):
        self._user = user

class ESG(models.Model):
    Year= models.PositiveIntegerField()
    Month = models.PositiveSmallIntegerField()
    Quarter = models.PositiveSmallIntegerField()
    Country = models.CharField(max_length=30)
    Location = models.CharField(max_length=30)
    Function = models.CharField(max_length=30)
    Description = models.CharField(max_length=200)
    Category = models.CharField(max_length=100)
    Type = models.CharField(max_length=30)
    Severity = models.CharField(max_length=30)
    Unit = models.CharField(max_length=30)
    Quantity = models.FloatField()
    Entered_By = models.ForeignKey(User, on_delete=models.CASCADE, related_name='esg_entered_by')
    Verified = models.BooleanField(default=False)
    Verified_By = models.ForeignKey(User, on_delete=models.CASCADE, related_name='esg_verified_by', null=True, blank=True)
    Remarks = models.CharField(max_length=255, null=True, blank=True)
    ESG_Evidence1 = models.FileField(upload_to='ESG_Evidences/', null=True, blank=True)
    ESG_Evidence2 = models.FileField(upload_to='ESG_Evidences/', null=True, blank=True)
    ESG_Evidence3 = models.FileField(upload_to='ESG_Evidences/', null=True, blank=True)
    ESG_Evidence4 = models.FileField(upload_to='ESG_Evidences/', null=True, blank=True)
    Created_On = models.DateTimeField(auto_now_add=True)
    Updated_On = models.DateTimeField(auto_now=True)
    Updated_By = models.ForeignKey(User, on_delete=models.CASCADE, related_name='esg_updated_by', null=True, blank=True)


class DisposalSummary(models.Model):
    UID = models.AutoField(primary_key=True)
    Year = models.PositiveIntegerField()
    Month = models.PositiveSmallIntegerField()
    Quarter=models.PositiveSmallIntegerField()
    Date = models.DateField()
    Country=models.CharField(max_length=25)
    Location = models.CharField(max_length=30)
    Type=models.CharField(max_length=100)
    Entered_By = models.ForeignKey(User, on_delete=models.CASCADE, related_name='entered_by')
    Verified = models.BooleanField(default=False)
    Verified_By = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verified_by', null=True, blank=True)
    Evidence1 = models.FileField(upload_to='Waste Management/Evidences/', null=True, blank=True)
    Evidence2 = models.FileField(upload_to='Waste Management/Evidences/', null=True, blank=True)
    Evidence3 = models.FileField(upload_to='Waste Management/Evidences/', null=True, blank=True)
    Evidence4 = models.FileField(upload_to='Waste Management/Evidences/', null=True, blank=True)
    Count = models.IntegerField(default=0)
    class Meta:
        unique_together = ['Date', 'Location', 'Type']

class Course(models.Model):
    title = models.CharField(max_length=200)
    version = models.FloatField()
    pdf_file = models.FileField(upload_to='pdf_files/')
    is_active = models.BooleanField(default=True)
    uploaded_by =models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='%(class)s_uploaded_by')
    uploaded_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='%(class)s_updated_by')
    updated_at = models.DateTimeField(null=True, blank=True)
    change_desc = models.CharField(max_length=500, null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='%(class)s_approved_by')
    approved_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return self.title

class Acknowledgement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    course_version = models.FloatField()
    course_year = models.PositiveIntegerField()
    course_quarter = models.PositiveSmallIntegerField()
    course_month = models.PositiveIntegerField()
    user_country = models.CharField(max_length=20)
    user_location = models.CharField(max_length=25)
    userid = models.CharField(max_length=10)
    user_name= models.CharField(max_length=100)
    course_name = models.CharField(max_length=200)
    rating = models.PositiveSmallIntegerField()
    acknowledgement_status = models.CharField(max_length=20)
    feedback_suggestion = models.TextField( null=True, blank=True)
    acknowledgement_date = models.DateTimeField()
    def save(self, *args, **kwargs):
        user = getattr(self, '_user', None)
        if user:
            if not self.pk:
                self.created_by = user
            self.updated_by = user
            del self._user
        super(Acknowledgement, self).save(*args, **kwargs)
    def set_user(self, user):
        self._user = user

class Question(models.Model):
    course= models.ForeignKey(Course, on_delete=models.CASCADE) #Added @ 06-08-2023 20:30 
    course_name = models.CharField(max_length=500)
    question_text = models.CharField(max_length=500)
    option1 = models.CharField(max_length=255)
    option2 = models.CharField(max_length=255)
    option3 = models.CharField(max_length=255)
    option4 = models.CharField(max_length=255)
    correct_option =  models.CharField(max_length=255)
    def __str__(self):
        return self.question_text
    
class UserResponse(models.Model):
    auth_user = models.ForeignKey(AuthorisedUser, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    userid = models.CharField(max_length=25)
    user_name = models.CharField(max_length=100)
    user_country = models.CharField(max_length=25)
    user_location = models.CharField(max_length=40)
    course_year = models.PositiveIntegerField()
    course_quarter = models.PositiveSmallIntegerField()
    course_month = models.PositiveIntegerField()
    course_date = models.DateField()
    completed_at = models.DateTimeField(auto_now=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    course_name = models.CharField(max_length=500)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.user_name} - {self.question.question_text}"

class UserScores(models.Model):
    year = models.PositiveSmallIntegerField()
    quarter = models.PositiveSmallIntegerField()
    month = models.CharField(max_length=20)
    is_completed = models.BooleanField(default=False)
    completion_date = models.DateTimeField(null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    course_name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    auth_user = models.ForeignKey(AuthorisedUser, on_delete=models.CASCADE)
    country = models.CharField(max_length=25)
    location = models.CharField(max_length=25)
    percentage = models.PositiveIntegerField()
    def __str__(self):
        return f"{self.course.title} - {self.user.first_name} - {self.user.last_name}"

# Need To Update Actual Date. Planned Date Not Required.
class TrainingCalendar(models.Model):
    country = models.CharField(max_length=50)
    location = models.CharField(max_length=50)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    session = models.CharField(max_length=200)
    frequency = models.CharField(max_length=55)
    planned_year = models.PositiveIntegerField()
    planned_quarter = models.PositiveSmallIntegerField()
    planned_month= models.PositiveIntegerField()
    planned_date = models.DateField()
    actual_date = models.DateField(null=True, blank=True)
    agenda = models.CharField(max_length=500)
    attendee_teams = models.CharField(max_length=255)
    attendees = models.CharField(max_length=1000)
    conducted_by = models.CharField(max_length=30)
    attendence_sheet = models.FileField(upload_to='training_evidence/')
    training_images = models.ImageField(upload_to='training_images/')
    verified = models.BooleanField(default=False)
    verified_date = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    verifier_remarks = models.CharField(max_length=500, null=True, blank=True)

class Forex(models.Model):
    year = models.PositiveIntegerField()
    country = models.CharField(max_length=30)
    currency = models.CharField(max_length=10)
    usd_rate = models.FloatField()
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_created_by')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_updated_by')
    def save(self, *args, **kwargs):
        user = getattr(self, '_user', None)
        if user:
            if not self.pk:
                self.created_by = user
            self.updated_by = user
            del self._user
        super(Forex, self).save(*args, **kwargs)
    def set_user(self, user):
        self._user = user

