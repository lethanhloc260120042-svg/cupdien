import time
from datetime import datetime
from django.core.management.base import BaseCommand
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from core.models import OutageData

class Command(BaseCommand):
    help = 'Scrape power outage data from lichcupdien.org and save to database'

    def parse_outage_data(self, html_content):
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

    def handle(self, *args, **options):
        self.stdout.write('Starting scraper...')
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/114.0.0.0")
        
        try:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to initialize webdriver: {e}'))
            return

        base_url = "https://lichcupdien.org"
        main_url = f"{base_url}/lich-cup-dien-can-tho"
        
        try:
            driver.get(main_url)
            time.sleep(3)
            soup_main = BeautifulSoup(driver.page_source, 'html.parser')
            district_tags = soup_main.find_all('a', class_='related-area-main')
            districts = {tag.text.strip(): (base_url + tag.get('href') if tag.get('href').startswith('/') else tag.get('href')) 
                         for tag in district_tags if tag.get('href') and "can-tho" in tag.get('href')}
            
            for district_name, district_url in districts.items():
                self.stdout.write(f'Scraping district: {district_name}')
                driver.get(district_url)
                time.sleep(2)
                data = self.parse_outage_data(driver.page_source)
                
                # Save to database
                for item in data:
                    try:
                        # Convert date string DD-MM-YYYY to YYYY-MM-DD
                        date_str = item.get('Ngày', '')
                        if not date_str:
                            continue
                            
                        import re
                        match = re.search(r'(\d+)\s+tháng\s+(\d+)\s+năm\s+(\d+)', date_str)
                        if match:
                            day, month, year = match.groups()
                            date_str_formatted = f"{int(day):02d}-{int(month):02d}-{year}"
                            date_obj = datetime.strptime(date_str_formatted, '%d-%m-%Y').date()
                        else:
                            date_obj = datetime.strptime(date_str, '%d-%m-%Y').date()
                        
                        start_time_str = item.get('Thời gian bắt đầu', '00:00')
                        end_time_str = item.get('Thời gian kết thúc', '23:59')
                        
                        # Handle missing or invalid data gracefully
                        area = item.get('Khu vực', '')
                        if not area:
                            continue
                            
                        reason = item.get('Lý do', '')
                        status = item.get('Trạng thái', '')
                        
                        OutageData.objects.update_or_create(
                            district=district_name,
                            date=date_obj,
                            start_time=start_time_str,
                            end_time=end_time_str,
                            area=area,
                            defaults={
                                'reason': reason,
                                'status': status
                            }
                        )
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'Error processing item: {item} - {e}'))
                        
            self.stdout.write(self.style.SUCCESS('Successfully scraped and saved outage data. Running notification check...'))
            from core.utils import check_and_notify
            check_and_notify()
            self.stdout.write(self.style.SUCCESS('Notification check completed.'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Scraping failed: {e}'))
        finally:
            driver.quit()
