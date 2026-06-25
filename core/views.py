from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import OutageData, UserSubscription
from .utils import get_ward_mapping, normalize_vn_text

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    today = timezone.localdate()
    outages = OutageData.objects.filter(date__gte=today).order_by('district', 'date', 'start_time')
    return render(request, 'home.html', {'outages': outages})

@login_required
def dashboard(request):
    today = timezone.localdate()
    all_outages = OutageData.objects.filter(date__gte=today).order_by('district', 'date', 'start_time')
    
    subscriptions = UserSubscription.objects.filter(user=request.user)
    
    personalized_outages = []
    from .utils import get_ward_mapping, normalize_vn_text
    ward_map = get_ward_mapping()
    
    for sub in subscriptions:
        sub_outages = []
        ward_clean = normalize_vn_text(sub.ward_name).replace("phường ", "").replace("xã ", "").replace("thị trấn ", "").strip()
        target_wards = ward_map.get(ward_clean, [ward_clean])
        
        for out in all_outages:
            out_area_norm = normalize_vn_text(out.area)
            match_ward = False
            for tw in target_wards:
                if tw in out_area_norm:
                    match_ward = True
                    break
            
            if match_ward:
                if sub.area_name:
                    area_clean = normalize_vn_text(sub.area_name).replace("khu vực ", "").replace("kv ", "").replace("ấp ", "").strip()
                    if area_clean in out_area_norm:
                        if out not in sub_outages:
                            sub_outages.append(out)
                else:
                    if out not in sub_outages:
                        sub_outages.append(out)
        
        if sub_outages:
            personalized_outages.append({
                'subscription': sub,
                'outages': sub_outages
            })
            
    return render(request, 'dashboard.html', {
        'all_outages': all_outages,
        'personalized_outages': personalized_outages,
        'has_subscriptions': subscriptions.exists()
    })

@login_required
def manage_subscriptions(request):
    if request.method == 'POST':
        province_code = request.POST.get('province_code')
        province_name = request.POST.get('province_name')
        district_code = request.POST.get('district_code')
        district_name = request.POST.get('district_name')
        ward_code = request.POST.get('ward_code')
        ward_name = request.POST.get('ward_name')
        area_name = request.POST.get('area_name', '').strip()
        
        if province_code and district_code and ward_code:
            UserSubscription.objects.get_or_create(
                user=request.user,
                province_code=province_code,
                district_code=district_code,
                ward_code=ward_code,
                area_name=area_name,
                defaults={
                    'province_name': province_name,
                    'district_name': district_name,
                    'ward_name': ward_name,
                }
            )
            return redirect('manage_subscriptions')
            
    subscriptions = UserSubscription.objects.filter(user=request.user)
    
    today = timezone.localdate()
    all_outages = OutageData.objects.filter(date__gte=today)
    
    sub_data = []
    from .utils import get_ward_mapping
    ward_map = get_ward_mapping()
    
    for sub in subscriptions:
        sub_outages = []
        ward_clean = normalize_vn_text(sub.ward_name).replace("phường ", "").replace("xã ", "").replace("thị trấn ", "").strip()
        target_wards = ward_map.get(ward_clean, [ward_clean])
        
        for out in all_outages:
            out_area_norm = normalize_vn_text(out.area)
            match_ward = False
            for tw in target_wards:
                if tw in out_area_norm:
                    match_ward = True
                    break
            
            if match_ward:
                if sub.area_name:
                    area_clean = normalize_vn_text(sub.area_name).replace("khu vực ", "").replace("kv ", "").replace("ấp ", "").strip()
                    if area_clean in out_area_norm:
                        if out not in sub_outages:
                            sub_outages.append(out)
                else:
                    if out not in sub_outages:
                        sub_outages.append(out)
                    
        sub_outages.sort(key=lambda x: (x.date, x.start_time))
        sub_data.append({
            'sub': sub,
            'outages': sub_outages
        })
        
    return render(request, 'subscriptions.html', {'sub_data': sub_data})

@login_required
def delete_subscription(request, sub_id):
    if request.method == 'POST':
        sub = get_object_or_404(UserSubscription, id=sub_id, user=request.user)
        sub.delete()
    return redirect('manage_subscriptions')

@login_required
def test_notify(request):
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        from django.contrib import messages
        
        # 1. Gửi Email Test
        if request.user.email:
            send_mail(
                "⚡ Bíp bíp! Đây là tin nhắn Test từ hệ thống Lịch Cúp Điện",
                f"Chào {request.user.username},\n\nHệ thống thông báo của bạn đang hoạt động cực kỳ tốt nha!\n\nEmail này dùng để kiểm tra cấu hình Resend API.",
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                fail_silently=False,
            )
            
        # 2. Gửi Web Push Test
        try:
            from webpush import send_user_notification
            payload = {
                "head": "Ting ting! Test thành công",
                "body": "Thông báo Web Push của bạn hoạt động ngon lành rồi nhé!",
                "icon": "https://lichcupdien.org/favicon.ico",
                "url": "/subscriptions/"
            }
            send_user_notification(user=request.user, payload=payload, ttl=1000)
        except Exception as e:
            print("Web push test failed:", e)

        messages.success(request, "Đã gửi thông báo test thành công! Hãy kiểm tra Email và Web Push của bạn.")
        return redirect('manage_subscriptions')
    except Exception as e:
        import traceback
        from django.http import HttpResponse
        return HttpResponse(f"Error sending test notification:<br><br><b>{e}</b><br><br><pre>{traceback.format_exc()}</pre>", status=500)

def get_areas(request):
    import csv
    import os
    from django.http import JsonResponse
    from django.conf import settings
    
    district_name = request.GET.get('district', '').replace('Quận ', '').replace('Huyện ', '').strip()
    ward_name = request.GET.get('ward', '').replace('Phường ', '').replace('Xã ', '').replace('Thị trấn ', '').strip()
    
    areas = []
    ap_kv_dir = os.path.join(settings.BASE_DIR, 'ap_kv')
    
    if os.path.exists(ap_kv_dir):
        for filename in os.listdir(ap_kv_dir):
            if filename.endswith('.csv'):
                filepath = os.path.join(ap_kv_dir, filename)
                with open(filepath, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if district_name.lower() == row.get('quan_huyen', '').lower().strip() and ward_name.lower() == row.get('phuong_xa', '').lower().strip():
                            areas.append(row.get('ten_khu_vuc_ap', '').strip())
                            
    areas = sorted(list(set([a for a in areas if a])))
    return JsonResponse({'areas': areas})

@login_required
def outage_detail(request, outage_id):
    outage = get_object_or_404(OutageData, id=outage_id)
    return render(request, 'outage_detail.html', {'outage': outage})
