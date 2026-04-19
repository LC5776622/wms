from django.urls import path
from . import views,  Views_Incident, Views_Invoice, Views_MBR, Views_OPEX, Views_Vendor, Views_WM, Views_Awareness

urlpatterns = [
    # Data Input
    path('', views.index, name='index'),
    path('mbrinput', Views_MBR.MBR_Input, name='MBRInput'),
    path('incidentinput', Views_Incident.Incident_Input, name='IncidentInput'),
    path('upload_incidents', Views_Incident.Incident_Upload, name='Incident_Upload'),
    path('forex_input', Views_OPEX.Forex_Input, name='Forex_Input'),
    path('opexupload', Views_OPEX.OPEX_Upload, name='OPEX_Upload'),
    path('opexinput', Views_OPEX.OPEX_Input, name='OPEX_Input'),
    path('glinput', Views_OPEX.GL_Input, name='GL_Input'),
    path('invoiceinput', Views_Invoice.Invoice_Input, name='Invoice_Input'),
    path('vendorinput', Views_Vendor.Vendor_Input, name='Vendor_Input'),
    path('vendorupload', Views_Vendor.Vendor_Upload, name='Vendor_Upload'),
    path('wmr_input', Views_WM.WM_Routine_Input, name='WM_Routine_Input'),
    path('wmr_upload', Views_WM.WM_Routine_Upload, name='WM_Routine_Upload'),
    path('wmnr_input', Views_WM.WM_Non_Routine_Input, name='WM_Non_Routine_Input'),
    path('wmnr_upload', Views_WM.WM_Non_Routine_Upload, name='WM_Non_Routine_Upload'),
    path('wmew_input', Views_WM.WM_EWaste_Input, name='WM_EWaste_Input'), 
    path('wmew_upload', Views_WM.WM_EWaste_Upload, name='WM_EWaste_Upload'),
    path('esg_input', Views_WM.ESG_Input, name='ESG_Input'),
    path('locationinput', views.Location_Input, name="Location_Input"),
    path('locationupload', views.Location_Upload, name="Location_Upload"),

    
    # View Data
    path('spacedata', Views_MBR.Space_Data, name='SpaceData'),
    path('esupportdata', Views_MBR.eSupport_Data, name='eSupport'),
    path('updates', Views_MBR.Facility_Updates, name='FacilityUpdates'),
    path('incidentdata', Views_Incident.Incidents_Data, name='IncidentData'),
    path('IncidentView/<int:incident_data_id>/', Views_Incident.Incident_View, name='Incident_View'),
    path('RoutineView', Views_WM.WM_Routine_View, name='Routine_View'),
    path('NonRoutineView', Views_WM.WM_Non_Routine_View, name='Non_Routine_View'),
    path('EWasteView', Views_WM.WM_E_Waste_View, name='E_Waste_View'),
    path('ESG_Data', Views_WM.ESG_Data, name='ESG_Data'),
    path('Disp_Summary_Data', Views_WM.Disp_Summary_Data, name='Disp_Summary_Data'),
    path('Disp_Details/<int:disp_id>/', Views_WM.Disp_Details, name='Disp_Details'),
    path('opexview/', Views_OPEX.Opex_View, name='OpexView'),
    path('invoiceview', Views_Invoice.Invoice_View, name='InvoiceView'),
    path('vendorview', Views_Vendor.Vendor_View, name='VendorView'),
    path('locationview', views.Location_View, name='Location_View'),
    
   
    # Update
    path('updatembr/<int:mbr_data_id>/', Views_MBR.update_mbr_data, name='update_mbr_data'),
    path('updateincident/<int:incident_data_id>/', Views_Incident.update_incident_data, name='update_incident_data'),
    path('updateRoutineDisposal/<int:routine_data_id>/', Views_WM.Update_Routine, name='Update_Routine_Disposal'),
    path('updateNonRoutineDisposal/<int:non_routine_data_id>/', Views_WM.Update_Non_Routine, name='Update_Non_Routine_Disposal'),
    path('updateEWateDisposal/<int:e_waste_data_id>/', Views_WM.Update_E_Waste, name='Update_E_Waste'),
    path('Upload_Evidences/<int:disp_id>/', Views_WM.Upload_Evidences, name='Upload_Evidences'),
    path('Update_ESG/<int:esg_id>/', Views_WM.Update_ESG, name='Update_ESG'),
    path('ESG_Details<int:esg_id>/', Views_WM.ESG_Details, name='ESG_Details'),
    path('updateopex/<int:opex_data_id>/', Views_OPEX.update_opex_data, name='update_opex_data'),
    path('updateinvoice/<int:invoice_data_id>/', Views_Invoice.update_invoice_data, name='update_invoice_data'),
    path('updatevendor/<int:vendor_data_id>/', Views_Vendor.update_vendor_data, name='update_vendor_data'),
    path('updatelocation<int:location_data_id>/', views.Update_Locations, name='Update_Locations'),
    
    # Delete
    path('deletembr/<int:id>', Views_MBR.Delete_MBR, name='delete_mbr'),
    path('deleteincident/<int:id>', Views_Incident.Delete_Incident, name='delete_incident'),
    path('deleteRoutine/<int:id>', Views_WM.Delete_Routine_Disposal, name='Delete_Routine'),
    path('deleteNonRoutine/<int:id>', Views_WM.Delete_Non_Routine_Disposal, name='Delete_Non_Routine'),
    path('deleteEWaste/<int:id>', Views_WM.Delete_E_Waste, name='Delete_E_Waste'),
    path('Delete_ESG/<int:id>', Views_WM.Delete_ESG, name='Delete_ESG'),
    path('deleteopex/<int:id>', Views_OPEX.Delete_Opex, name='delete_opex'),
    path('deleteinvoice/<int:id>', Views_Invoice.Delete_Invoice, name='delete_invoice'),
    path('deletevendor/<int:id>', Views_Vendor.Delete_Vendor, name='delete_vendor'),
    path('deletelocation/<int:id>', views.Delete_Locations, name='Delete_Locations'),

    
    # Reports
    path('mbrreport', Views_MBR.MBR_Report, name='MBR_Report'),
    path('incidentreport', Views_Incident.Incident_Report, name='Incident_Report'),
    path('WMreport', Views_WM.Waste_Management_Report, name='WM_Report'),
    path('opexreport', Views_OPEX.OPEX_Report, name='OPEX_Report'),
    path('customreportsinput', views.CustomReport_Input, name='CustomReport_Input'),
    path('customreportsview', views.CustomReport_View, name='CustomReport_View'),
    path('customreportsdata', views.Reports_Data, name='ReportsData'),
    path('updatecustomreports/<int:reports_data_id>/', views.Update_Reports, name='Update_CustomReports'),
    path('deletereport/<int:id>', views.Delete_Reports, name='Delete_Reports'),

    #Awareness
    path('schedule_training', Views_Awareness.Schedule_Training, name='Schedule_Training'),
    path('UplaodCourse', Views_Awareness.Upload_Course, name='Upload_Course'),
    path('approve_course/<int:course_id>/', Views_Awareness.Approve_Course, name='Approve_Course'),
    path('training_calendar', Views_Awareness.Calendar_View, name='Calendar_View'),
    path('update_training/<int:training_id>/', Views_Awareness.Update_Training, name='Update_Training'),
    path('view_training_record/<int:training_id>/', Views_Awareness.View_Training_Record, name='View_Training_Record'),
    path('verify_training/<int:training_id>/', Views_Awareness.Verify_Training, name='Verify_Training'),
    path('ViewCourses', Views_Awareness.View_Courses, name='View_Courses'),
    path('archived_courses', Views_Awareness.Archived_Courses, name='Archived_Courses'),
    
    path('version_control/<int:course_id>/', Views_Awareness.Version_Control, name='Version_Control'),
    path('SlideShow/<int:course_id>/', Views_Awareness.Slide_Show, name='Slide_Show'),
    path('UpdateCourse/<int:course_id>/', Views_Awareness.Update_Course, name='Update_Course'),
    path('DeleteCourse/<int:id>', Views_Awareness.Delete_Course, name='Delete_Course'),
    path('acknowledgement/<int:course_id>/', Views_Awareness.Acknowledgement_Input, name='Acknowledgement'),
    path('acknowledgement_view', Views_Awareness.Acknowledgement_View, name='Acknowledgement_View'),
    path('quiz_view/<int:course_id>/', Views_Awareness.Quiz_View, name='Quiz_View'),
    path('quiz_result/<int:course_id>/', Views_Awareness.Quiz_Results, name='Quiz_Results'),
    path('retake_quiz/<int:course_id>/', Views_Awareness.Retake_Quiz, name='Retake_Quiz'),
    path('add_questions/', Views_Awareness.Add_Questions, name='Add_Questions'),
    path('view_questions', Views_Awareness.View_Questions, name='View_Questions'),
    path('edit_question/<int:question_id>/', Views_Awareness.Edit_Questions, name='Edit_Questions'),
    path('User_Responses', Views_Awareness.User_Responses, name='User_Responses'),
    path('awareness_sumamry', Views_Awareness.Awareness_Sumamry, name='Awareness_Sumamry'),


    
    #Users
    path('authUserUpload', views.AuthUser_Upload, name='AuthUser_Upload'),
    path('authUserView', views.AuthUser_View, name='AuthUser_View'),
    path('authUserUpdate/<int:auth_user_id>/', views.AuthUser_Update, name='AuthUser_Update'),
    path('authUserDelete/<int:id>', views.AuthUser_Delete, name='AuthUser_Delete'),
    path('register/', views.register, name='Register'),
    path('registered_users/', views.Registered_Users, name='Registered_Users'),
    path('update_user_profile/<int:user_id>/', views.Update_User_Profile, name='Update_User_Profile'),
    path('login', views.LoginUser, name='Login'),
    path('userprofile/', views.ProfileView, name="UserProfile"),
    path('logout', views.LogoutUser, name='Logout'),

   
    ]

