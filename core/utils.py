from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import OutageData, UserSubscription

def get_ward_mapping():
    import csv
    import os
    from django.conf import settings
    
    mapping = {}
    csv_paths = [
        os.path.join(settings.BASE_DIR, 'can_tho_day_du_9_quan_huyen_mapping.csv'),
        os.path.join(settings.BASE_DIR, 'can_tho_cac_phuong_xa_con_thieu_bo_sung.csv')
    ]
    
    for csv_path in csv_paths:
        if not os.path.exists(csv_path):
            continue
            
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                phuong_cu = row.get('phuong_xa_cu', '').lower().replace("phường ", "").replace("xã ", "").replace("thị trấn ", "").strip()
                phuong_moi = row.get('don_vi_moi_sau_sap_nhap', '').lower().replace("phường ", "").replace("xã ", "").replace("thị trấn ", "").strip()
                
                if phuong_cu and phuong_moi:
                    if phuong_cu not in mapping:
                        mapping[phuong_cu] = []
                    if phuong_moi not in mapping[phuong_cu]:
                        mapping[phuong_cu].append(phuong_moi)
    return mapping

def normalize_vn_text(text):
    import unicodedata
    if not text: return ""
    return unicodedata.normalize('NFC', str(text)).lower().strip()

def check_and_notify():
    """
    Tìm kiếm lịch cúp điện trong 7 ngày tới, đối chiếu với Subscriptions của User
    để gửi email thông báo.
    """
    today = timezone.localdate()
    # Lấy lịch trong 7 ngày tới
    upcoming_outages = OutageData.objects.filter(date__gte=today, date__lte=today + timezone.timedelta(days=7))
    
    if not upcoming_outages.exists():
        return

    # Gom nhóm thông báo theo User -> Subscription -> Outages
    user_notifications = {}
    ward_map = get_ward_mapping()
    
    for outage in upcoming_outages:
        out_area_norm = normalize_vn_text(outage.area)
        matching_subs = UserSubscription.objects.all()
        
        for sub in matching_subs:
            ward_clean = normalize_vn_text(sub.ward_name).replace("phường ", "").replace("xã ", "").replace("thị trấn ", "").strip()
            target_wards = ward_map.get(ward_clean, [ward_clean])
            
            match_ward = False
            for tw in target_wards:
                if tw in out_area_norm:
                    match_ward = True
                    break
            
            if match_ward:
                match_area = True
                if sub.area_name:
                    area_clean = normalize_vn_text(sub.area_name).replace("khu vực ", "").replace("kv ", "").replace("ấp ", "").strip()
                    if area_clean not in out_area_norm:
                        match_area = False
                
                if match_area:
                    user = sub.user
                    if user.email:
                        if user not in user_notifications:
                            user_notifications[user] = {}
                            
                        if sub not in user_notifications[user]:
                            user_notifications[user][sub] = []
                        
                        if outage not in user_notifications[user][sub]:
                            user_notifications[user][sub].append(outage)
                        
    # Tiến hành gửi Email cho từng User
    for user, sub_outages_map in user_notifications.items():
        total_outages = sum(len(outages) for outages in sub_outages_map.values())
        subject = f"⚡ Cảnh báo: Có lịch cúp điện tại khu vực của bạn ({total_outages} lịch)"
        
        message = f"Chào {user.username},\n\nKhu vực bạn đang theo dõi sắp có lịch cúp điện. Chi tiết như sau:\n\n"
        
        for sub, outages in sub_outages_map.items():
            if not outages: continue
            
            sub_title = f"{sub.ward_name}, {sub.district_name}"
            if sub.area_name:
                sub_title = f"{sub.area_name} - {sub.ward_name}, {sub.district_name}"
                
            message += f"📍 Lịch cúp điện tại: {sub_title}\n"
            message += "=" * 40 + "\n"
            
            for o in outages:
                message += f"- Ngày: {o.date.strftime('%d/%m/%Y')} | {o.start_time.strftime('%H:%M')} - {o.end_time.strftime('%H:%M')}\n"
                message += f"  Khu vực: {o.area}\n"
                if o.reason:
                    message += f"  Lý do: {o.reason}\n"
                message += "-" * 30 + "\n"
            message += "\n"
            
        message += "Cảm ơn bạn đã sử dụng hệ thống!\n"
        
        # Send Email
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send email to {user.email}: {e}")
            
        # Send Web Push
        try:
            from webpush import send_user_notification
            payload = {
                "head": "Cảnh báo Cúp điện!",
                "body": f"Khu vực bạn theo dõi sắp bị cúp điện ({total_outages} lịch). Kiểm tra email để xem chi tiết.",
                "icon": "https://lichcupdien.org/favicon.ico",
                "url": "/subscriptions/"
            }
            send_user_notification(user=user, payload=payload, ttl=1000)
        except Exception as e:
            print(f"Failed to send push notification to {user.username}: {e}")
