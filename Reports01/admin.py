from django.contrib import admin
from Reports01.models import MBR_Data, Incident_Data,TrainingCalendar, ESG, DisposalSummary, OPEX_Data, UserResponse, Question, Acknowledgement,  Expense_Heads, Vendor_Data, Invoice_Data, LocationModel, AuthorisedUser, RoutineDisposal, Non_Routine_Disposal, E_Waste_Disposal

# Register your models here.

admin.site.register(MBR_Data)
admin.site.register(Invoice_Data)
admin.site.register(OPEX_Data)
admin.site.register(Vendor_Data)
admin.site.register(Incident_Data)
admin.site.register(Expense_Heads)
admin.site.register(LocationModel)
admin.site.register(AuthorisedUser)
admin.site.register(RoutineDisposal)
admin.site.register(Non_Routine_Disposal)
admin.site.register(E_Waste_Disposal)
admin.site.register(Acknowledgement)
admin.site.register(Question)
admin.site.register(UserResponse)
admin.site.register(TrainingCalendar)
admin.site.register(DisposalSummary)
admin.site.register(ESG)
