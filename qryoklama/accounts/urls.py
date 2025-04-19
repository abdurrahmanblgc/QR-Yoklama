# accounts/urls.py
from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('ogrenci/kayit/', views.student_register, name='student_register'),
    path('ogrenci/giris/', views.student_login, name='student_login'),
    path('akademisyen/giris/', views.academic_login, name='academic_login'),
    path('ogrenci/panel/', views.student_panel, name='student_panel'),
    path('akademisyen/panel/', views.academic_panel, name='academic_panel'),
    path('akademisyen/ders/ekle/', views.course_create, name='course_create'),
    path('akademisyen/ders/<int:course_id>/', views.course_detail, name='course_detail'),
    path('akademisyen/ders/<int:course_id>/enroll/', views.course_enroll, name='course_enroll'),
    path('akademisyen/qr/olustur/', views.qr_session_create, name='qr_session_create'),
    path('akademisyen/qr/goruntule/<int:session_id>/', views.qr_session_display, name='qr_session_display'),
    path('akademisyen/qr/sonlandir/<int:session_id>/', views.qr_session_end, name='qr_session_end'),
    path('qr_attendance/<int:session_id>/', views.qr_attendance, name='qr_attendance'),
    path('akademisyen/yoklama/kayitlari/', views.attendance_record_list, name='attendance_record_list'),
    path('sifre-degistir/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('sifre-degistirildi/', auth_views.PasswordChangeDoneView.as_view(
            template_name='accounts/password_change_done.html'), name='password_change_done'),
    path('akademisyen/yoklama/detay/<int:session_id>/', views.attendance_detail, name='attendance_detail'),
    path('akademisyen/profil/', views.academic_profile, name='academic_profile'),
    path('logout/', views.custom_logout, name='logout'),
    path('ogrenci/yoklama/detay/<int:course_id>/', views.attendance_detail_student, name='attendance_detail_student'),

    path('ogrenci/sifre-unuttum/', auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset_form.html',
            email_template_name='accounts/password_reset_email.html',
            subject_template_name='accounts/password_reset_subject.txt',
            success_url=reverse_lazy('password_reset_done'),
            extra_email_context={'domain': 'tarsusuniversitesiqryoklama.online'}  # reset linkinde kullanılacak domain
        ), name='password_reset'),
    path('ogrenci/sifre-unuttum/done/', auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html'
        ), name='password_reset_done'),
    path('ogrenci/sifre-sifirla/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete')
        ), name='password_reset_confirm'),
    path('ogrenci/sifre-sifirla/done/', auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'
        ), name='password_reset_complete'),
    path('akademisyen/yoklama/gonder/<int:course_id>/', views.send_attendance_email, name='send_attendance_email'),
    path('akademisyen/yoklama/rapor-gonder/', views.send_academic_attendance_email, name='send_academic_attendance_email'),
]
