from django.db import models
from django.contrib.auth.models import User

# Ders bilgilerini saklayan model
class Course(models.Model):
    course_code = models.CharField("Ders Kodu", max_length=20, unique=True)
    course_name = models.CharField("Ders Adı", max_length=200)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="courses")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.course_code = self.course_code.lower()  # Her zaman küçük harfe çevir
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.course_code.upper()} - {self.course_name}"

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_number = models.CharField("Öğrenci Numarası", max_length=20)
    student_class = models.IntegerField("Sınıf", choices=[(i, str(i)) for i in range(1, 5)])
    department = models.CharField("Bölüm", max_length=100, default="Yönetim Bilişim Sistemleri")
    must_change_password = models.BooleanField(default=True)  # İlk girişte şifre değiştirmeyi zorunlu kılmak için
    paired_device = models.CharField("Eşleştirilmiş Cihaz Kimliği", max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.student_number}"


# Derslere kayıt olan öğrenciler (Enrollment)
class Enrollment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course', 'student')

    def __str__(self):
        return f"{self.student.get_full_name()} enrolled in {self.course.course_code.upper()}"

class QrSession(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name="qr_sessions")
    week_number = models.IntegerField("Hafta")
    session_number = models.PositiveIntegerField("Oturum Numarası", default=1)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="qr_sessions")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.course.course_code.upper()} - Hafta {self.week_number}, Oturum {self.session_number}"

# Her QR oturumu için öğrenci yoklama kaydı
class AttendanceRecord(models.Model):
    qr_session = models.ForeignKey(QrSession, on_delete=models.CASCADE, related_name="attendance_records")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="attendance_records")
    present = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('qr_session', 'student')

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.qr_session} - {'Mevcut' if self.present else 'Yok'}"
