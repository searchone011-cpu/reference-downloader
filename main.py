#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
برنامج تحميل المراجع من جوجل
Reference Downloader from Google
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import os
from datetime import datetime
from downloader import ReferenceDownloader
import queue

class ReferenceDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("برنامج تحميل المراجع من جوجل - Reference Downloader")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f0f0f0")
        
        # Queue للتواصل بين threads
        self.update_queue = queue.Queue()
        self.downloader = None
        self.download_thread = None
        
        self.setup_ui()
        self.check_queue()
        
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        
        # الإطار الرئيسي
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # العنوان
        title_label = ttk.Label(main_frame, text="📥 برنامج تحميل المراجع من جوجل",
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # --- قسم إدخال المراجع ---
        input_frame = ttk.LabelFrame(main_frame, text="إدخال المراجع", padding="10")
        input_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # زر تحميل الملف
        load_btn = ttk.Button(input_frame, text="📂 تحميل ملف المراجع",
                             command=self.load_references_file)
        load_btn.grid(row=0, column=0, padx=5)
        
        # زر مسح
        clear_btn = ttk.Button(input_frame, text="🗑️ مسح الكل",
                              command=self.clear_references)
        clear_btn.grid(row=0, column=1, padx=5)
        
        # منطقة النص لإدخال المراجع
        ttk.Label(input_frame, text="المراجع (كل مرجع في سطر):").grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        
        self.references_text = scrolledtext.ScrolledText(input_frame, height=8, width=80, wrap=tk.WORD)
        self.references_text.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # --- قسم الإعدادات ---
        settings_frame = ttk.LabelFrame(main_frame, text="الإعدادات", padding="10")
        settings_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(settings_frame, text="مجلد الحفظ:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.download_path_var = tk.StringVar(value=os.path.expanduser("~/Downloads/References"))
        path_entry = ttk.Entry(settings_frame, textvariable=self.download_path_var, width=50)
        path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        browse_btn = ttk.Button(settings_frame, text="استعراض...",
                               command=self.browse_folder)
        browse_btn.grid(row=0, column=2, padx=5)
        
        # عدد المحاولات
        ttk.Label(settings_frame, text="عدد محاولات التحميل:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.retry_var = tk.IntVar(value=3)
        retry_spin = ttk.Spinbox(settings_frame, from_=1, to=10, textvariable=self.retry_var, width=10)
        retry_spin.grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # المهلة الزمنية
        ttk.Label(settings_frame, text="المهلة الزمنية (ثانية):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.timeout_var = tk.IntVar(value=30)
        timeout_spin = ttk.Spinbox(settings_frame, from_=10, to=120, textvariable=self.timeout_var, width=10)
        timeout_spin.grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # --- قسم التقدم ---
        progress_frame = ttk.LabelFrame(main_frame, text="التقدم", padding="10")
        progress_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.progress_label = ttk.Label(progress_frame, text="جاهز للبدء", font=("Arial", 10))
        self.progress_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, length=400, mode='determinate')
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # إحصائيات
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.stats_label = ttk.Label(stats_frame, text="✓ نجح: 0 | ✗ فشل: 0 | ⏳ المتبقي: 0",
                                    font=("Arial", 10, "bold"))
        self.stats_label.pack()
        
        # --- قسم السجل ---
        log_frame = ttk.LabelFrame(main_frame, text="سجل العمليات", padding="10")
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=80, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # --- الأزرار الرئيسية ---
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.start_btn = ttk.Button(button_frame, text="▶️ ابدأ التحميل",
                                   command=self.start_download)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="⏹️ إيقاف", state=tk.DISABLED,
                                  command=self.stop_download)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_log_btn = ttk.Button(button_frame, text="💾 حفظ التقرير",
                                      command=self.save_report)
        self.save_log_btn.pack(side=tk.LEFT, padx=5)
        
        self.open_folder_btn = ttk.Button(button_frame, text="📁 فتح مجلد الملفات",
                                         command=self.open_download_folder)
        self.open_folder_btn.pack(side=tk.LEFT, padx=5)
        
        exit_btn = ttk.Button(button_frame, text="❌ خروج", command=self.root.quit)
        exit_btn.pack(side=tk.RIGHT, padx=5)
        
        # تأكيد الإغلاق
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def load_references_file(self):
        """تحميل ملف المراجع"""
        file_path = filedialog.askopenfilename(
            title="اختر ملف المراجع",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.references_text.delete(1.0, tk.END)
                self.references_text.insert(1.0, content)
                self.log("✓ تم تحميل الملف بنجاح")
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل تحميل الملف: {str(e)}")
                
    def clear_references(self):
        """مسح المراجع"""
        self.references_text.delete(1.0, tk.END)
        self.log("تم مسح جميع المراجع")
        
    def browse_folder(self):
        """استعراض مجلد الحفظ"""
        folder = filedialog.askdirectory(title="اختر مجلد الحفظ")
        if folder:
            self.download_path_var.set(folder)
            
    def log(self, message):
        """إضافة رسالة إلى السجل"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def start_download(self):
        """بدء التحميل"""
        references = self.references_text.get(1.0, tk.END).strip().split('\n')
        references = [ref.strip() for ref in references if ref.strip()]
        
        if not references:
            messagebox.showwarning("تحذير", "يرجى إدخال مراجع على الأقل!")
            return
            
        # إنشاء المجلد
        download_path = self.download_path_var.get()
        os.makedirs(download_path, exist_ok=True)
        
        # تعطيل الأزرار
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        # بدء خيط التحميل
        self.downloader = ReferenceDownloader(
            references=references,
            download_path=download_path,
            retry_attempts=self.retry_var.get(),
            timeout=self.timeout_var.get(),
            update_queue=self.update_queue
        )
        
        self.download_thread = threading.Thread(target=self.downloader.download_all, daemon=True)
        self.download_thread.start()
        
        self.log("🔄 بدء عملية البحث والتحميل...")
        
    def stop_download(self):
        """إيقاف التحميل"""
        if self.downloader:
            self.downloader.stop()
            self.log("⏹️ تم إيقاف العملية من قبل المستخدم")
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            
    def check_queue(self):
        """فحص قائمة التحديثات من خيط التحميل"""
        try:
            while True:
                message_type, data = self.update_queue.get_nowait()
                
                if message_type == "log":
                    self.log(data)
                elif message_type == "progress":
                    current, total = data
                    self.progress_bar['value'] = (current / total) * 100 if total > 0 else 0
                    self.progress_label.config(text=f"جاري المعالجة: {current}/{total}")
                elif message_type == "stats":
                    success, failed, remaining = data
                    self.stats_label.config(
                        text=f"✓ نجح: {success} | ✗ فشل: {failed} | ⏳ المتبقي: {remaining}"
                    )
                elif message_type == "complete":
                    self.start_btn.config(state=tk.NORMAL)
                    self.stop_btn.config(state=tk.DISABLED)
                    messagebox.showinfo("اكتمل", "انتهت عملية التحميل!")
                    
        except queue.Empty:
            pass
        finally:
            self.root.after(500, self.check_queue)
            
    def save_report(self):
        """حفظ التقرير"""
        report_content = self.log_text.get(1.0, tk.END)
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            messagebox.showinfo("نجح", f"تم حفظ التقرير في:\n{file_path}")
            
    def open_download_folder(self):
        """فتح مجلد التحميل"""
        path = self.download_path_var.get()
        if os.path.exists(path):
            import platform
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                os.system(f"open '{path}'")
            else:
                os.system(f"xdg-open '{path}'")
        else:
            messagebox.showerror("خطأ", "مجلد التحميل غير موجود")
            
    def on_closing(self):
        """عند إغلاق النافذة"""
        if self.downloader and self.downloader.is_running:
            if messagebox.askyesno("تحذير", "جاري التحميل. هل تريد الخروج حقاً؟"):
                self.downloader.stop()
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    root = tk.Tk()
    app = ReferenceDownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
