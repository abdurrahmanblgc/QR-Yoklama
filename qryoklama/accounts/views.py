from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import StudentProfile

def student_register(request):
    if request.method == 'POST':
        # Formdan gelen veriler
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        accept_privacy = request.POST.get('accept_privacy', None)
        student_number = request.POST.get('student_number', '').strip()
        student_class = request.POST.get('student_class', '').strip()  # '1', '2', '3' veya '4'
        department = request.POST.get('department', '').strip()

        # Tüm alanların doldurulup doldurulmadığını kontrol et
        if not all([first_name, last_name, email, password, confirm_password, student_number, student_class, department]):
            messages.error(request, "Tüm alanları doldurmalısınız.")
            return render(request, 'accounts/student_register.html', locals())

        # Email doğrulaması: @tarsus.edu.tr ile bitmeli
        if not email.endswith('@tarsus.edu.tr'):
            messages.error(request, "Email adresi @tarsus.edu.tr ile bitmelidir.")
            return render(request, 'accounts/student_register.html', locals())

        # Şifre kontrolü
        if password != confirm_password:
            messages.error(request, "Şifreler eşleşmiyor.")
            return render(request, 'accounts/student_register.html', locals())

        # Gizlilik sözleşmesi onayı kontrolü
        if accept_privacy != 'on':
            messages.error(request, "Gizlilik sözleşmesini kabul etmelisiniz.")
            return render(request, 'accounts/student_register.html', locals())

        # Sınıf seçimi kontrolü
        if student_class not in ['1', '2', '3', '4']:
            messages.error(request, "Sınıf seçimi geçersiz.")
            return render(request, 'accounts/student_register.html', locals())

        # Bölüm kontrolü (şu an için sadece 'Yönetim Bilişim Sistemleri')
        if department != "Yönetim Bilişim Sistemleri":
            messages.error(request, "Seçilebilecek bölüm: Yönetim Bilişim Sistemleri.")
            return render(request, 'accounts/student_register.html', locals())

        # Aynı email ile kayıtlı kullanıcı kontrolü
        if User.objects.filter(email=email).exists():
            messages.error(request, "Bu email ile kayıtlı bir kullanıcı zaten var.")
            return render(request, 'accounts/student_register.html', locals())

        # Kullanıcı oluşturma (username olarak email kullanılıyor)
        username = email
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Öğrenci profilini oluşturma
        StudentProfile.objects.create(
            user=user,
            student_number=student_number,
            student_class=int(student_class),
            department=department
        )

        login(request, user)
        messages.success(request, "Kayıt başarılı, sisteme giriş yapıldı.")
        return redirect('student_panel')

    return render(request, 'accounts/student_register.html')


def academic_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_superuser:
                login(request, user)
                return redirect('academic_panel')
            else:
                messages.error(request, "Bu giriş akademisyenlere özeldir.")
        else:
            messages.error(request, "Kullanıcı adı veya şifre hatalı.")
    return render(request, 'accounts/academic_login.html')


def student_login(request):
    next_url = request.GET.get('next')  # URL'den next parametresini alıyoruz
    if request.method == 'POST':
        username = request.POST.get('username')  # Email kullanılıyor
        password = request.POST.get('password')
        device_id = request.POST.get('device_id', '').strip()  # Cihaz kimliği
        if not device_id:
            messages.error(request, "Cihaz kimliği alınamadı. Lütfen tekrar deneyiniz.")
            return render(request, 'accounts/student_login.html', {'next': next_url})
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if not user.is_superuser:
                profile = user.studentprofile
                # Eğer cihaz eşleştirmesi daha önce yapılmamışsa, device_id kaydedilsin.
                if not profile.paired_device:
                    profile.paired_device = device_id
                    profile.save()
                    messages.info(request, "Cihazınız başarıyla eşleştirildi. Bundan sonra yalnızca bu cihaz üzerinden giriş yapabilirsiniz.")
                else:
                    # Eğer eşleştirilmiş cihaz mevcutsa, yeni gelen device_id ile karşılaştır
                    if profile.paired_device != device_id:
                        messages.error(request, "Bu cihaz, kayıtlı cihazınızla eşleşmiyor. Lütfen eşleştirilmiş cihazınızdan giriş yapın.")
                        return render(request, 'accounts/student_login.html', {'next': next_url})
                login(request, user)
                # Şifre değiştirme kontrolü
                if user.studentprofile.must_change_password:
                    messages.info(request, "Lütfen ilk girişte şifrenizi değiştiriniz.")
                    return redirect('password_change')
                if next_url:
                    return redirect(next_url)
                return redirect('student_panel')
            else:
                messages.error(request, "Bu giriş öğrenciler içindir.")
        else:
            messages.error(request, "Kullanıcı adı veya şifre hatalı.")
    return render(request, 'accounts/student_login.html', {'next': next_url})




from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy

class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('password_change_done')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Şifre değiştirildikten sonra must_change_password bayrağını False yapıyoruz.
        self.request.user.studentprofile.must_change_password = False
        self.request.user.studentprofile.save()
        return response

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import AttendanceRecord, Course

def student_panel(request):
    # Giriş yapmış öğrenciye ait yoklama kayıtlarını getiriyoruz.
    records = AttendanceRecord.objects.filter(student=request.user).select_related('qr_session', 'qr_session__course').order_by('qr_session__course__course_code', 'qr_session__week_number')
    
    # Kayıtları ders bazında grupluyoruz
    grouped_records = {}
    for record in records:
        course = record.qr_session.course
        if course not in grouped_records:
            grouped_records[course] = {'records': [], 'total': 0, 'present': 0}
        grouped_records[course]['records'].append(record)
        grouped_records[course]['total'] += 1
        if record.present:
            grouped_records[course]['present'] += 1

    return render(request, 'accounts/student_panel.html', {'grouped_records': grouped_records})


def attendance_detail_student(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    # Seçilen ders için öğrencinin tüm yoklama kayıtlarını sırayla getiriyoruz.
    records = AttendanceRecord.objects.filter(student=request.user, qr_session__course=course).select_related('qr_session').order_by('qr_session__week_number', 'qr_session__session_number')
    return render(request, 'accounts/attendance_detail_student.html', {'course': course, 'records': records})




from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import StudentProfile, Course, Enrollment

# Önceki öğrenci ve akademisyen giriş/girişim view'leriniz burada yer alıyor...
# (student_register, student_login, academic_login, student_panel vs.)

def academic_panel(request):
    # Sadece giriş yapan akademisyenin oluşturduğu dersleri getiriyoruz.
    courses = Course.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'accounts/academic_panel.html', {'courses': courses})







def course_update(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        course_code = request.POST.get('course_code', '').strip()
        course_name = request.POST.get('course_name', '').strip()

        if not course_code or not course_name:
            messages.error(request, "Lütfen ders kodu ve ders adını giriniz.")
            return redirect('course_update', course_id=course.id)

        # Güncelleme yaparken, mevcut dersin dışında aynı ders kodu varsa hata verelim.
        if Course.objects.filter(course_code__iexact=course_code).exclude(id=course.id).exists():
            messages.error(request, "Bu ders kodu zaten mevcut.")
            return redirect('course_update', course_id=course.id)

        course.course_code = course_code  # save() metodunda küçük harfe dönüştürülecek.
        course.course_name = course_name
        course.save()

        messages.success(request, "Ders başarıyla güncellendi.")
        return redirect('academic_panel')
    else:
        return render(request, 'accounts/course_update.html', {'course': course})

def course_create(request):
    if request.method == 'POST':
        course_code = request.POST.get('course_code', '').strip()
        course_name = request.POST.get('course_name', '').strip()

        if not course_code or not course_name:
            messages.error(request, "Lütfen ders kodu ve ders adını giriniz.")
            return render(request, 'accounts/course_create.html')

        # Ders kodu kontrolü (küçük-büyük harf duyarsız)
        if Course.objects.filter(course_code__iexact=course_code).exists():
            messages.error(request, "Bu ders kodu zaten mevcut.")
            return render(request, 'accounts/course_create.html')

        Course.objects.create(
            course_code=course_code,
            course_name=course_name,
            created_by=request.user
        )
        messages.success(request, "Ders başarıyla eklendi.")
        return redirect('academic_panel')
    else:
        return render(request, 'accounts/course_create.html')
    
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        course_code = request.POST.get('course_code', '').strip()
        course_name = request.POST.get('course_name', '').strip()
        if not course_code or not course_name:
            messages.error(request, "Lütfen ders kodu ve ders adını giriniz.")
            return redirect('course_detail', course_id=course.id)
        if Course.objects.filter(course_code__iexact=course_code).exclude(id=course.id).exists():
            messages.error(request, "Bu ders kodu zaten mevcut.")
            return redirect('course_detail', course_id=course.id)
        course.course_code = course_code
        course.course_name = course_name
        course.save()
        messages.success(request, "Ders başarıyla güncellendi.")
        return redirect('course_detail', course_id=course.id)
    enrollments = course.enrollments.all()
    return render(request, 'accounts/course_detail.html', {'course': course, 'enrollments': enrollments})

def course_enroll(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        # Seçilen öğrenciler checkbox ile gönderiliyor (birden fazla seçilebilecek)
        student_ids = request.POST.getlist('student_ids')
        if not student_ids:
            messages.error(request, "Lütfen en az bir öğrenci seçiniz.")
            return redirect('course_enroll', course_id=course.id)
        for student_id in student_ids:
            try:
                student = User.objects.get(id=student_id, is_superuser=False)
                if not course.enrollments.filter(student=student).exists():
                    Enrollment.objects.create(course=course, student=student)
            except User.DoesNotExist:
                continue
        messages.success(request, "Seçilen öğrenciler başarıyla derse eklendi.")
        return redirect('course_detail', course_id=course.id)
    else:
        # Halihazırda derse kayıtlı öğrencileri dışarıda bırakıyoruz
        enrolled_student_ids = course.enrollments.values_list('student_id', flat=True)
        # Sistemden, superuser olmayan öğrencilerin profillerini alıyoruz
        students = StudentProfile.objects.filter(user__is_superuser=False)\
                    .exclude(user__id__in=enrolled_student_ids)\
                    .order_by('student_class')
        # Öğrencileri sınıf bazında gruplandırıyoruz
        grouped_students = {}
        for student in students:
            group = student.student_class
            if group not in grouped_students:
                grouped_students[group] = []
            grouped_students[group].append(student)
        return render(request, 'accounts/course_enroll.html', {
            'course': course,
            'grouped_students': grouped_students
        })
    


import io, base64, qrcode
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Course, Enrollment, QrSession, AttendanceRecord, StudentProfile
import datetime
# --- Önceki view'ler (öğrenci, akademisyen girişleri, ders ekleme, detay vs.) burada mevcut ---

import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Course, QrSession, Enrollment, AttendanceRecord

# Ders başlangıç ve yoklama alınacak dönem (14 hafta)
CLASS_START = datetime.date(2025, 2, 3)
CLASS_END = CLASS_START + datetime.timedelta(days=98 - 1)  # 14 hafta boyunca

# Sınav tarih aralıkları (örneğin, Ara Sınav ve Yarıyıl Sonu Sınavı)
EXAM_PERIODS = [
    (datetime.date(2025, 3, 22), datetime.date(2025, 3, 28)),
    (datetime.date(2025, 5, 20), datetime.date(2025, 5, 30)),
]

def qr_session_create(request):
    # Akademisyenin oluşturduğu dersleri getiriyoruz.
    courses = Course.objects.filter(created_by=request.user)
    
    total_weeks = 14  # Sabit 14 hafta
    week_range = range(1, total_weeks + 1)
    
    # Exam weeks hesaplaması: Eğer haftanın en az 4 günü sınav dönemine denk geliyorsa o hafta seçilemez.
    exam_weeks = []
    for week in week_range:
        week_start = CLASS_START + datetime.timedelta(days=(week - 1) * 7)
        week_end = week_start + datetime.timedelta(days=6)
        for exam_start, exam_end in EXAM_PERIODS:
            latest_start = max(week_start, exam_start)
            earliest_end = min(week_end, exam_end)
            delta = (earliest_end - latest_start).days + 1 if earliest_end >= latest_start else 0
            if delta >= 4:
                exam_weeks.append(week)
                break
    
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        week_number = request.POST.get('week_number')
        session_number = request.POST.get('session_number', '1')  # Oturum numarası, varsayılan 1
        if not all([course_id, week_number, session_number]):
            messages.error(request, "Lütfen tüm alanları doldurunuz.")
            return render(request, 'accounts/qr_session_create.html', {
                'courses': courses,
                'week_range': week_range,
                'exam_weeks': exam_weeks,
            })
        try:
            week_number = int(week_number)
            session_number = int(session_number)
        except ValueError:
            messages.error(request, "Geçersiz değer girdiniz.")
            return render(request, 'accounts/qr_session_create.html', {
                'courses': courses,
                'week_range': week_range,
                'exam_weeks': exam_weeks,
            })
        if week_number in exam_weeks:
            messages.error(request, "Sınav haftalarında yoklama alınamaz.")
            return render(request, 'accounts/qr_session_create.html', {
                'courses': courses,
                'week_range': week_range,
                'exam_weeks': exam_weeks,
            })
        course = get_object_or_404(Course, id=course_id)
        # Aynı hafta ve oturum numarası için önceden oluşturulmuş bir QR oturumu kontrol edilebilir.
        # Eğer istenirse akademisyen uyarılabilir. Burada direk yeni oturum oluşturuyoruz.
        qr_session = QrSession.objects.create(
            course=course,
            week_number=week_number,
            session_number=session_number,
            created_by=request.user
        )
        # Dersin kayıtlı tüm öğrencileri için yoklama kaydı oluştur (varsayılan olarak "yok")
        for enrollment in course.enrollments.all():
            AttendanceRecord.objects.get_or_create(qr_session=qr_session, student=enrollment.student)
        messages.success(request, "QR Oturumu oluşturuldu.")
        return redirect('qr_session_display', session_id=qr_session.id)
    else:
        return render(request, 'accounts/qr_session_create.html', {
            'courses': courses,
            'week_range': week_range,
            'exam_weeks': exam_weeks,
        })


def qr_session_display(request, session_id):
    qr_session = get_object_or_404(QrSession, id=session_id)
    # Sabit alan adını kullanarak tam URL oluşturuyoruz:
    attendance_url = f"https://tarsusuniversitesiqryoklama.online/qr_attendance/{session_id}/"
    
    # QR kod oluşturma işlemi:
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(attendance_url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return render(request, 'accounts/qr_session_display.html', {
        'qr_session': qr_session,
        'qr_code': img_str
    })
# 3. QR Oturumunu Sonlandırma (Yoklamayı bitirme)
def qr_session_end(request, session_id):
    qr_session = get_object_or_404(QrSession, id=session_id)
    qr_session.is_active = False
    qr_session.ended_at = timezone.now()
    qr_session.save()
    messages.success(request, "QR Oturumu sonlandırıldı.")
    return redirect('academic_panel')  # veya yoklama kayıtları sayfasına yönlendirin

# 4. Öğrenci, QR Kod taraması ile yoklamayı alır
@login_required
def qr_attendance(request, session_id):
    qr_session = get_object_or_404(QrSession, id=session_id, is_active=True)
    try:
        record = AttendanceRecord.objects.get(qr_session=qr_session, student=request.user)
    except AttendanceRecord.DoesNotExist:
        messages.error(request, "Bu derse kayıtlı değilsiniz.")
        return redirect('student_panel')
    record.present = True
    record.save()
    messages.success(request, "Yoklamanız alındı.")
    return redirect('student_panel')

def attendance_record_list(request):
    # Sadece giriş yapan akademisyenin oluşturduğu QR oturumlarını getiriyoruz.
    sessions = QrSession.objects.filter(created_by=request.user).order_by('course__course_code', 'week_number')
    
    # Her session için toplam ve mevcut yoklama sayısını hesaplıyoruz.
    for session in sessions:
        session.total_count = session.attendance_records.count()
        session.present_count = session.attendance_records.filter(present=True).count()
    
    grouped_sessions = {}
    for session in sessions:
        course = session.course
        if course not in grouped_sessions:
            grouped_sessions[course] = []
        grouped_sessions[course].append(session)
    return render(request, 'accounts/attendance_record_list.html', {'grouped_sessions': grouped_sessions})



def attendance_detail(request, session_id):
    qr_session = get_object_or_404(QrSession, id=session_id, created_by=request.user)
    records = qr_session.attendance_records.all()
    present_records = records.filter(present=True)
    absent_records = records.filter(present=False)
    return render(request, 'accounts/attendance_detail.html', {
        'session': qr_session,
        'present_records': present_records,
        'absent_records': absent_records,
    })


from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect

@login_required
def academic_profile(request):
    # Sadece akademisyenler (superuser) için erişim kontrolü yapabilirsiniz:
    if not request.user.is_superuser:
        messages.error(request, "Bu sayfaya erişim yetkiniz yok.")
        return redirect('academic_panel')

    user = request.user
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        # E-posta değişikliği yapılıyorsa, e-posta uygunluğunu kontrol edelim
        if email and email != user.email:
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                messages.error(request, "Bu e-posta zaten kullanılıyor.")
                return render(request, 'accounts/academic_profile.html', {'user': user})
        
        # Kullanıcı bilgilerini güncelleyelim
        user.first_name = first_name
        user.last_name = last_name
        user.email = email

        # Eğer şifre güncelleme alanları doldurulduysa
        if current_password or new_password or confirm_password:
            if not user.check_password(current_password):
                messages.error(request, "Mevcut şifreniz yanlış.")
                return render(request, 'accounts/academic_profile.html', {'user': user})
            if new_password != confirm_password:
                messages.error(request, "Yeni şifreler eşleşmiyor.")
                return render(request, 'accounts/academic_profile.html', {'user': user})
            # Şifre kriterleri kontrol edilebilir (örneğin minimum uzunluk vs.)
            user.set_password(new_password)
        
        user.save()
        messages.success(request, "Profil bilgileriniz güncellendi.")
        # Eğer şifre güncellendiyse, tekrar giriş yapılması gerekebilir; burada isteğe bağlı yönlendirme yapabilirsiniz.
        return redirect('academic_profile')
    
    return render(request, 'accounts/academic_profile.html', {'user': user})

# accounts/views.py

from django.contrib.auth import logout
from django.shortcuts import redirect

def custom_logout(request):
    logout(request)
    return redirect('home')  # Çıkıştan sonra yönlendirilecek sayfa, örn: 'home'


from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import QrSession, AttendanceRecord

def qr_session_end(request, session_id):
    qr_session = get_object_or_404(QrSession, id=session_id)
    qr_session.is_active = False
    qr_session.ended_at = timezone.now()
    qr_session.save()
    
    # Akademisyene gönderilecek e-posta detayları
    total = qr_session.attendance_records.count()
    present_count = qr_session.attendance_records.filter(present=True).count()
    absent_count = total - present_count
    absent_students = qr_session.attendance_records.filter(present=False)
    absent_list = "\n".join([
        f"{record.student.first_name} {record.student.last_name} ({record.student.email})"
        for record in absent_students
    ])
    
    subject_academic = f"Yoklama Sonuçları: {qr_session.course.course_code.upper()} - Hafta {qr_session.week_number}"
    message_academic = (
        f"Ders: {qr_session.course.course_code.upper()} - {qr_session.course.course_name}\n"
        f"Hafta: {qr_session.week_number}\n"
        f"Toplam Öğrenci: {total}\n"
        f"Mevcut: {present_count}\n"
        f"Yok: {absent_count}\n\n"
        "Yok olmayan öğrenciler:\n"
        f"{absent_list if absent_list else 'Tüm öğrenciler yoklamaya girmiş.'}"
    )
    recipient_academic = [request.user.email]
    
    try:
        send_mail(
            subject_academic,
            message_academic,
            settings.DEFAULT_FROM_EMAIL,
            recipient_academic,
            fail_silently=False,
        )
    except Exception as e:
        messages.error(request, f"QR oturumu sonlandırıldı ancak akademisyene e-posta gönderilemedi: {e}")
    
    # Şimdi, o oturuma kayıtlı tüm öğrencilere e-posta gönderelim
    for record in qr_session.attendance_records.all():
        student_email = record.student.email
        subject_student = f"Yoklama Sonucu: {qr_session.course.course_code.upper()} - Hafta {qr_session.week_number}"
        message_student = (
            f"Sayın {record.student.first_name},\n\n"
            f"Ders: {qr_session.course.course_code.upper()} - {qr_session.course.course_name}\n"
            f"Hafta: {qr_session.week_number}\n"
            f"Yoklama Sonucunuz: {'Mevcut' if record.present else 'Mevcut Değil'}\n\n"
            "Bilginize."
        )
        try:
            send_mail(
                subject_student,
                message_student,
                settings.DEFAULT_FROM_EMAIL,
                [student_email],
                fail_silently=False,
            )
        except Exception as e:
            # Eğer bir öğrencinin e-postası gönderilemezse, loglama veya hata mesajı ekleyebilirsiniz
            print(f"E-posta gönderilemedi ({student_email}): {e}")
    
    messages.success(request, "QR Oturumu sonlandırıldı. Yoklama sonuçları akademisyen ve öğrencilere gönderildi.")
    return redirect('academic_panel')


def send_attendance_email(request, course_id):
    # Sadece ilgili akademisyenin oluşturduğu dersler için işlem yapalım
    course = get_object_or_404(Course, id=course_id, created_by=request.user)
    
    # İlgili derse kayıtlı öğrencileri alıyoruz (Enrollment üzerinden veya StudentProfile üzerinden)
    enrollments = course.enrollments.all()
    
    # Her öğrenci için yoklama kayıtlarını getirip e-posta gönderelim
    for enrollment in enrollments:
        student = enrollment.student
        # Bu öğrencinin ilgili ders için tüm yoklama kayıtlarını getiriyoruz
        records = AttendanceRecord.objects.filter(
            qr_session__course=course, student=student
        ).order_by('qr_session__week_number', 'qr_session__session_number')
        
        # HTML tablosu oluşturmak için basit bir yapı:
        html_table = "<table border='1' cellspacing='0' cellpadding='5'>"
        html_table += "<tr><th>Hafta</th><th>Oturum Numarası</th><th>Durum</th></tr>"
        for record in records:
            status = "Mevcut" if record.present else "Yok"
            html_table += f"<tr><td>{record.qr_session.week_number}</td><td>{record.qr_session.session_number}</td><td>{status}</td></tr>"
        html_table += "</table>"
        
        subject = f"{course.course_code.upper()} - Yoklama Kayıtları"
        # Basit bir HTML e-posta mesajı
        html_message = (
            f"<p>Sayın {student.first_name},</p>"
            f"<p>Dersiniz <strong>{course.course_code.upper()} - {course.course_name}</strong> için yoklama kayıtlarınız aşağıda yer almaktadır: (kayıtlar gerçeği yansıtmamaktadır eksik veri bulunmaktadı ve pilot çalışmalar devam etmektedir.)</p>"
            f"{html_table}"
            f"<p>İyi çalışmalar.</p>"
        )
        
        try:
            send_mail(
                subject,
                '',  # Plain text kısmını boş bırakıyoruz
                settings.DEFAULT_FROM_EMAIL,
                [student.email],
                fail_silently=False,
                html_message=html_message
            )
        except Exception as e:
            # Hata oluşursa loglama yapabilir veya hata mesajı gösterebilirsiniz.
            print(f"E-posta gönderilemedi ({student.email}): {e}")
    
    messages.success(request, "Yoklama kayıtları öğrencilerinize gönderildi.")
    return redirect('academic_panel')
# accounts/views.py
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import Course, AttendanceRecord
from django.template.loader import render_to_string

def send_academic_attendance_email(request):
    # Akademisyenin oluşturduğu tüm dersleri alıyoruz
    courses = Course.objects.filter(created_by=request.user).order_by('course_code')
    
    # HTML rapor başlangıcı
    html_message = (
        f"<p>Sayın {request.user.first_name},</p>"
        "<p>Aşağıda oluşturduğunuz derslerin yoklama kayıtlarına ilişkin detaylı rapor yer almaktadır:</p>"
    )
    
    for course in courses:
        html_message += f"<h3>{course.course_code.upper()} - {course.course_name}</h3>"
        
        # Dersin QR oturumlarını alalım
        qr_sessions = course.qr_sessions.all().order_by('week_number', 'session_number')
        if not qr_sessions.exists():
            html_message += "<p>Bu derse ait yoklama kaydı bulunmamaktadır.</p>"
        else:
            # Oturum özet tablosu
            html_message += (
                "<h4>Oturum Özeti</h4>"
                "<table border='1' cellspacing='0' cellpadding='5'>"
                "<tr>"
                "<th>Hafta</th>"
                "<th>Oturum Numarası</th>"
                "<th>Toplam Öğrenci</th>"
                "<th>Mevcut</th>"
                "<th>Yok</th>"
                "</tr>"
            )
            for session in qr_sessions:
                total = session.attendance_records.count()
                present = session.attendance_records.filter(present=True).count()
                absent = total - present
                html_message += (
                    f"<tr>"
                    f"<td>{session.week_number}</td>"
                    f"<td>{session.session_number}</td>"
                    f"<td>{total}</td>"
                    f"<td>{present}</td>"
                    f"<td>{absent}</td>"
                    f"</tr>"
                )
            html_message += "</table>"
            
            # Öğrenci detay tablosu
            enrollments = course.enrollments.all()
            if enrollments.exists():
                html_message += "<h4>Öğrenci Yoklama Detayları</h4>"
                # Tablo başlığı: İlk sütun öğrenci, ardından her bir oturum için ayrı sütun
                header_row = "<tr><th>Öğrenci</th>"
                # Oturumları listeleyip header'a ekliyoruz
                session_list = list(qr_sessions)
                for session in session_list:
                    header_row += f"<th>Hafta {session.week_number} - Oturum {session.session_number}</th>"
                header_row += "</tr>"
                
                html_message += "<table border='1' cellspacing='0' cellpadding='5'>"
                html_message += header_row
                
                # Her öğrenci için satır oluşturuyoruz
                for enrollment in enrollments:
                    student = enrollment.student
                    row = f"<tr><td>{student.first_name} {student.last_name}</td>"
                    for session in session_list:
                        try:
                            record = session.attendance_records.get(student=student)
                            status = "Mevcut" if record.present else "Mevcut Değil"
                        except AttendanceRecord.DoesNotExist:
                            status = "Kayıt Yok"
                        row += f"<td>{status}</td>"
                    row += "</tr>"
                    html_message += row
                html_message += "</table>"
            else:
                html_message += "<p>Bu derse kayıtlı öğrenci bulunmamaktadır.</p>"
        
        html_message += "<hr/>"
    
    subject = "Derslerinizin Yoklama Kayıtları - Detaylı Rapor"
    
    try:
        send_mail(
            subject,
            '',  # Plain text kısmı boş bırakıldı
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email],
            fail_silently=False,
            html_message=html_message
        )
        messages.success(request, "Yoklama kayıtları raporu e-posta ile gönderildi.")
    except Exception as e:
        messages.error(request, f"E-posta gönderilemedi: {e}")
    
    return redirect('academic_panel')

    
