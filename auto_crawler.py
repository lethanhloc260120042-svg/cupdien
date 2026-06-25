from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import json

def parse_outage_data(html_content):
    """Hàm dùng BeautifulSoup để bóc tách dữ liệu từ HTML của 1 trang"""
    soup = BeautifulSoup(html_content, 'html.parser')
    blocks = soup.find_all('div', class_='lcd_detail_wrapper')
    
    outage_list = []
    for block in blocks:
        outage = {}
        rows = block.find_all('div', class_='new_lcd_wrapper')
        
        for row in rows:
            title_elem = row.find('span', class_='title_item_lcd_wrapper')
            if not title_elem: continue
            title = title_elem.text.strip().replace(':', '')
            
            content_elem = row.find('div', class_='item_content_lcd_wrapper')
            if not content_elem: continue
            
            if title == 'Thời gian':
                times = content_elem.find_all('span', class_='item_lcd_time')
                if len(times) == 2:
                    outage['Thời gian bắt đầu'] = times[0].text.strip()
                    outage['Thời gian kết thúc'] = times[1].text.strip()
            elif title == 'Trạng thái':
                status_elem = content_elem.find('span', class_='lcd_check_trang_thai')
                if status_elem:
                    outage['Trạng thái'] = status_elem.text.strip()
            else:
                span_content = content_elem.find('span', class_='content_item_content_lcd_wrapper')
                if span_content:
                    outage[title] = span_content.text.strip()
        
        if outage:
            outage_list.append(outage)
            
    return outage_list

def main():
    print("Khởi động trình duyệt (chế độ chạy ngầm)...")
    options = Options()
    options.add_argument("--headless") # Chạy ngầm, không mở popup
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/114.0.0.0")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    base_url = "https://lichcupdien.org"
    main_url = f"{base_url}/lich-cup-dien-can-tho"
    
    # Dictionary tổng để chứa dữ liệu của TẤT CẢ các quận
    all_districts_data = {}
    
    try:
        # BƯỚC 1: Vào trang tổng Cần Thơ để quét link các quận
        print(f"Đang truy cập trang chủ: {main_url}")
        driver.get(main_url)
        time.sleep(3) # Chờ load DOM
        
        soup_main = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Tìm tất cả các thẻ a chứa link quận (class 'related-area-main')
        district_tags = soup_main.find_all('a', class_='related-area-main')
        
        districts = {}
        for tag in district_tags:
            href = tag.get('href')
            name = tag.text.strip()
            
            # Đảm bảo chỉ lấy link của Cần Thơ và tránh bị trùng lặp
            if href and "can-tho" in href:
                full_url = base_url + href if href.startswith('/') else href
                districts[name] = full_url
                
        print(f"🎯 Tìm thấy {len(districts)} quận/huyện. Bắt đầu chạy auto quét từng trang...\n")
        
        # BƯỚC 2: Lặp qua từng link quận, truy cập và bóc dữ liệu
        for district_name, district_url in districts.items():
            print(f" -> Đang cào dữ liệu: {district_name} ({district_url})")
            driver.get(district_url)
            time.sleep(2) # Chờ 2s cho trang của quận load xong
            
            # Ném HTML của trang quận vào hàm bóc tách
            data = parse_outage_data(driver.page_source)
            all_districts_data[district_name] = data
            
        # BƯỚC 3: Lưu toàn bộ kết quả ra file JSON
        output_file = "toan_bo_cup_dien_can_tho.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_districts_data, f, ensure_ascii=False, indent=4)
            
        print(f"\n✅ HOÀN TẤT! Toàn bộ dữ liệu {len(districts)} quận/huyện đã được gom sạch vào file: {output_file}")

    except Exception as e:
        print(f"❌ Có lỗi xảy ra: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
