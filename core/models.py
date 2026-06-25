from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    # Thêm các trường khác nếu cần sau này
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class OutageData(models.Model):
    district = models.CharField(max_length=255, verbose_name="Quận/Huyện")
    date = models.DateField(verbose_name="Ngày cúp điện")
    start_time = models.TimeField(verbose_name="Thời gian bắt đầu")
    end_time = models.TimeField(verbose_name="Thời gian kết thúc")
    area = models.TextField(verbose_name="Khu vực/Phường xã bị ảnh hưởng")
    reason = models.TextField(verbose_name="Lý do", blank=True, null=True)
    status = models.CharField(max_length=100, verbose_name="Trạng thái", blank=True, null=True)
    
    class Meta:
        unique_together = ('district', 'date', 'start_time', 'end_time', 'area')
        
    def __str__(self):
        return f"[{self.date}] {self.district} ({self.start_time} - {self.end_time})"

class UserSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    province_code = models.CharField(max_length=50)
    province_name = models.CharField(max_length=255)
    district_code = models.CharField(max_length=50)
    district_name = models.CharField(max_length=255)
    ward_code = models.CharField(max_length=50)
    ward_name = models.CharField(max_length=255)
    area_name = models.CharField(max_length=255, blank=True, null=True, help_text="Tên Ấp / Khu vực cụ thể")
    
    class Meta:
        unique_together = ('user', 'province_code', 'district_code', 'ward_code', 'area_name')
        
    def __str__(self):
        return f"{self.user.username} - {self.ward_name}, {self.district_name}"

