from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),
    # Ana sayfa: Akademisyen ve Öğrenci giriş butonlarını içeren basit bir şablon
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('qr_attendance/<int:session_id>/', accounts_views.qr_attendance, name='qr_attendance'),
    path('accounts/', include('accounts.urls')),
]
