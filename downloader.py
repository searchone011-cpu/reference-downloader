#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
وحدة تحميل المراجع والبحث عنها
Reference Download Module
"""

import requests
from bs4 import BeautifulSoup
import os
import time
from urllib.parse import quote
import threading
import queue

class ReferenceDownloader:
    def __init__(self, references, download_path, retry_attempts=3, timeout=30, update_queue=None):
        """
        تهيئة وحدة التحميل
        
        Args:
            references: قائمة المراجع
            download_path: مسار حفظ الملفات
            retry_attempts: عدد محاولات التحميل
            timeout: المهلة الزمنية
            update_queue: طابور التحديثات
        """
        self.references = references
        self.download_path = download_path
        self.retry_attempts = retry_attempts
        self.timeout = timeout
        self.update_queue = update_queue
        self.is_running = False
        self.success_count = 0
        self.failed_count = 0
        self.failed_references = []
        
        # إنشاء مجلد المراجع
        self.references_folder = os.path.join(download_path, "PDFs")
        os.makedirs(self.references_folder, exist_ok=True)
        
    def log_message(self, message):
        """إرسال رسالة إلى واجهة المستخدم"""
        if self.update_queue:
            self.update_queue.put(("log", message))
            
    def update_progress(self, current, total):
        """تحديث شريط التقدم"""
        if self.update_queue:
            self.update_queue.put(("progress", (current, total)))
            
    def update_stats(self, success, failed, remaining):
        """تحديث الإحصائيات"""
        if self.update_queue:
            self.update_queue.put(("stats", (success, failed, remaining)))
            
    def search_google(self, reference):
        """
        البحث عن مرجع على جوجل
        
        Args:
            reference: المرجع للبحث عنه
            
        Returns:
            قائمة روابط البحث
        """
        try:
            search_url = f"https://www.google.com/search?q={quote(reference)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            links = []
            
            # البحث عن روابط نتائج البحث
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('/url?q=') and 'webcache' not in href:
                    clean_link = href.split('/url?q=')[1].split('&')[0]
                    if clean_link.startswith('http'):
                        links.append(clean_link)
                        if len(links) >= 5:  # الحد الأقصى 5 روابط لكل مرجع
                            break
                            
            return links
            
        except Exception as e:
            self.log_message(f"❌ خطأ في البحث عن '{reference}': {str(e)}")
            return []
            
    def download_pdf(self, url, filename):
        """
        تحميل ملف PDF
        
        Args:
            url: رابط الملف
            filename: اسم الملف
            
        Returns:
            True إذا نجح التحميل
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout, stream=True)
            response.raise_for_status()
            
            # التحقق من نوع الملف
            content_type = response.headers.get('content-type', '')
            if 'pdf' in content_type.lower():
                file_path = os.path.join(self.references_folder, f"{filename}.pdf")
                
                # تحميل الملف
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            
                return True
                
        except Exception as e:
            pass
            
        return False
        
    def process_reference(self, reference, index, total):
        """
        معالجة مرجع واحد
        
        Args:
            reference: المرجع
            index: رقم المرجع الحالي
            total: إجمالي المراجع
        """
        if not self.is_running:
            return
            
        remaining = total - index
        self.update_stats(self.success_count, self.failed_count, remaining)
        self.update_progress(index, total)
        
        # تنظيف اسم الملف
        safe_filename = "".join(c for c in reference if c.isalnum() or c in (' ', '-', '_'))[:50]
        
        self.log_message(f"🔍 جاري البحث عن: {reference}")
        
        # محاولة البحث والتحميل
        success = False
        for attempt in range(self.retry_attempts):
            if not self.is_running:
                return
                
            try:
                # البحث على جوجل
                links = self.search_google(reference)
                
                if not links:
                    self.log_message(f"⚠️  لم يتم العثور على روابط لـ: {reference}")
                    continue
                
                # محاولة تحميل أول ملف PDF
                for link in links:
                    if self.download_pdf(link, safe_filename):
                        self.log_message(f"✅ تم تحميل: {safe_filename}.pdf")
                        self.success_count += 1
                        success = True
                        break
                        
                if success:
                    break
                    
            except Exception as e:
                if attempt < self.retry_attempts - 1:
                    self.log_message(f"⚠️  محاولة {attempt + 1} فشلت: {str(e)}")
                    time.sleep(2)  # انتظار قبل المحاولة التالية
                    
        if not success:
            self.log_message(f"❌ فشل تحميل: {reference}")
            self.failed_count += 1
            self.failed_references.append(reference)
            
    def download_all(self):
        """تحميل جميع المراجع"""
        self.is_running = True
        self.success_count = 0
        self.failed_count = 0
        self.failed_references = []
        
        total = len(self.references)
        self.log_message(f"📊 بدء معالجة {total} مرجع")
        
        try:
            for index, reference in enumerate(self.references, 1):
                if not self.is_running:
                    break
                    
                self.process_reference(reference, index, total)
                time.sleep(1)  # تأخير بين الطلبات
                
            # حفظ التقرير النهائي
            self.save_final_report()
            
            self.log_message("\n" + "="*50)
            self.log_message("✅ انتهت عملية المعالجة!")
            self.log_message(f"✓ نجح: {self.success_count}")
            self.log_message(f"✗ فشل: {self.failed_count}")
            self.log_message("="*50)
            
            if self.update_queue:
                self.update_queue.put(("complete", None))
                
        except Exception as e:
            self.log_message(f"❌ خطأ عام: {str(e)}")
        finally:
            self.is_running = False
            
    def save_final_report(self):
        """حفظ التقرير النهائي"""
        try:
            report_path = os.path.join(self.download_path, "report.txt")
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("="*60 + "\n")
                f.write("تقرير تحميل المراجع من جوجل\n")
                f.write("="*60 + "\n\n")
                
                f.write(f"التاريخ والوقت: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"إجمالي المراجع: {len(self.references)}\n")
                f.write(f"نجح: {self.success_count}\n")
                f.write(f"فشل: {self.failed_count}\n")
                f.write(f"النسبة المئوية للنجاح: {(self.success_count/len(self.references)*100):.1f}%\n\n")
                
                if self.failed_references:
                    f.write("المراجع التي فشل تحميلها:\n")
                    f.write("-"*60 + "\n")
                    for ref in self.failed_references:
                        f.write(f"• {ref}\n")
                        
            self.log_message(f"💾 تم حفظ التقرير في: {report_path}")
            
        except Exception as e:
            self.log_message(f"❌ خطأ في حفظ التقرير: {str(e)}")
            
    def stop(self):
        """إيقاف عملية التحميل"""
        self.is_running = False
        self.log_message("⏹️ تم إيقاف العملية")
