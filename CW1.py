import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import requests
import threading
from queue import Queue
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DirBuster:
    def __init__(self, root):
        self.root = root
        self.root.title("DIRBUSTER GUI V1")
        self.root.geometry("800x800")
        self.root.configure(bg="#0f0f0f")
        
        self.scanning = False
        self.queue = Queue(maxsize=10000)
        self.wordlist_path = ""
        self.wordlist = []
        self.scanned_urls = set()
        self.found_count = 0
        self.start_time = 0
        self.max_depth = 1
        self.lock = threading.Lock()
        
        self.setup_ui()
    
    def setup_ui(self):
        tk.Label(self.root, text="DIR BUSTER", font=("Impact", 24), 
                 fg="#00ff88", bg="#0f0f0f", pady=10).pack()
        
        container = tk.Frame(self.root, bg="#1a1a1a", padx=20, pady=15)
        container.pack(padx=30, pady=10, fill="both")
        
        tk.Label(container, text="TARGET:", bg="#1a1a1a", fg="white").grid(row=0, column=0, sticky='w', pady=(0, 5))
        
        url_frame = tk.Frame(container, bg="#1a1a1a")
        url_frame.grid(row=1, column=0, columnspan=3, sticky='ew', pady=(0, 10))
        
        self.protocol_var = tk.StringVar(value="https://")
        
        protocol_menu = tk.OptionMenu(url_frame, self.protocol_var, "https://", "http://")
        protocol_menu.config(bg="#333", fg="white", width=8)
        protocol_menu.pack(side='left', padx=(0, 5))
        
        self.url_entry = tk.Entry(url_frame, bg="#262626", fg="white", font=("Arial", 11))
        self.url_entry.pack(side='left', fill='x', expand=True, ipady=4)
        self.url_entry.insert(0, "example.com")
        
        tk.Label(container, text="WORDLIST:", bg="#1a1a1a", fg="white").grid(row=2, column=0, sticky='w', pady=(0, 5))
        
        wl_frame = tk.Frame(container, bg="#1a1a1a")
        wl_frame.grid(row=3, column=0, columnspan=3, sticky='ew', pady=(0, 10))
        
        self.path_display = tk.Entry(wl_frame, bg="#262626", fg="white", font=("Arial", 10))
        self.path_display.pack(side='left', fill='x', expand=True, ipady=4, padx=(0, 10))
        
        tk.Button(wl_frame, text="BROWSE", command=self.browse_file, bg="#333", fg="white").pack(side='left')
        
        tk.Label(container, text="SETTINGS:", bg="#1a1a1a", fg="white").grid(row=4, column=0, sticky='w', pady=(10, 5))
        
        settings_frame = tk.Frame(container, bg="#1a1a1a")
        settings_frame.grid(row=5, column=0, columnspan=3, pady=(0, 10))
        
        tk.Label(settings_frame, text="Threads:", bg="#1a1a1a", fg="white").pack(side='left', padx=(0, 5))
        self.thread_input = tk.Spinbox(settings_frame, from_=1, to=100, width=8, bg="#262626", fg="white")
        self.thread_input.delete(0, tk.END)
        self.thread_input.insert(0, "20")
        self.thread_input.pack(side='left', padx=(0, 20))
        
        tk.Label(settings_frame, text="Depth:", bg="#1a1a1a", fg="white").pack(side='left', padx=(0, 5))
        self.depth_input = tk.Spinbox(settings_frame, from_=1, to=5, width=8, bg="#262626", fg="white")
        self.depth_input.delete(0, tk.END)
        self.depth_input.insert(0, "2")
        self.depth_input.pack(side='left')
        
        btn_frame = tk.Frame(container, bg="#1a1a1a")
        btn_frame.grid(row=6, column=0, columnspan=3, pady=(10, 10))
        
        self.start_btn = tk.Button(btn_frame, text="START", command=self.start_scan, 
                                  bg="#00ff88", fg="black", font=("Arial", 10, "bold"), width=10)
        self.start_btn.pack(side='left', padx=2)
        
        self.stop_btn = tk.Button(btn_frame, text="STOP", command=self.stop_scan,
                                 bg="#ff4444", fg="white", font=("Arial", 10), width=8, state='disabled')
        self.stop_btn.pack(side='left', padx=2)
        
        clear_btn = tk.Button(btn_frame, text="CLEAR", command=self.clear_screen,
                             bg="#333333", fg="white", font=("Arial", 10), width=10)
        clear_btn.pack(side='left', padx=2)
        
        self.status_label = tk.Label(container, text="Ready", bg="#1a1a1a", fg="#888", font=("Arial", 9))
        self.status_label.grid(row=7, column=0, columnspan=3, pady=(5, 10))
        
        self.progress = ttk.Progressbar(container, length=300, mode='determinate')
        self.progress.grid(row=8, column=0, columnspan=3, pady=(0, 10))
        
        log_frame = tk.Frame(container, bg="#1a1a1a")
        log_frame.grid(row=9, column=0, columnspan=3, pady=(5, 0), sticky='nsew')
        
        container.grid_rowconfigure(9, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, width=85, height=18, 
                                                 bg="black", fg="#00ff88", font=("Consolas", 9))
        self.log_area.pack(fill='both', expand=True)
        
        self.log_area.tag_config('HIT', foreground='#00ff88')
        self.log_area.tag_config('DIR', foreground='#8888ff')
        self.log_area.tag_config('INFO', foreground='white')
        self.log_area.tag_config('ERROR', foreground='#ff4444')
        self.log_area.tag_config('REDIR', foreground='#ffaa00')
        self.log_area.tag_config('403', foreground='#ff8844')
        self.log_area.tag_config('WARN', foreground='#ffff00')
    
    def browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if path:
            self.wordlist_path = path
            self.path_display.delete(0, tk.END)
            self.path_display.insert(0, path)
    
    def log(self, msg, tag="INFO"):
        self.log_area.insert(tk.END, f"[{tag}] {msg}\n", tag)
        self.log_area.see(tk.END)
    
    def clear_screen(self):
        if self.scanning:
            response = messagebox.askyesno("Warning", 
                                          "A scan is running. Clear screen anyway?")
            if not response:
                return
        
        self.log_area.delete(1.0, tk.END)
        self.progress['value'] = 0
        
        if not self.scanning:
            self.status_label.config(text="Ready")
            self.found_count = 0
            self.scanned_urls.clear()
        
        self.log("Screen cleared", "INFO")
    
    def is_likely_directory(self, response, url):
        if url.endswith('/'):
            return True
        
        if response.status_code == 200 and response.text:
            text_lower = response.text.lower()
            directory_indicators = [
                'index of /', 'directory listing for', '<title>index of',
                'parent directory', 'name</a>', 'size</a>', 'last modified</a>',
                '<directory>', '[directory]'
            ]
            for indicator in directory_indicators:
                if indicator in text_lower:
                    return True
        
        if response.status_code in [301, 302, 303, 307, 308]:
            location = response.headers.get('Location', '')
            if location and location.endswith('/'):
                return True
        
        if response.status_code == 200 and len(response.text) < 5000:
            not_a_file = not any(url.lower().endswith(ext) for ext in 
                               ['.php', '.html', '.js', '.css', '.jpg', '.png', 
                                '.pdf', '.txt', '.xml', '.json', '.zip', '.gz'])
            if not_a_file:
                return True
        
        if response.status_code == 403 and '.' not in url.split('/')[-1]:
            return True
        
        return False
    
    def load_wordlist(self):
        if not self.wordlist_path:
            return False
        
        try:
            with open(self.wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                self.wordlist = [line.strip() for line in f if line.strip()]
            self.log(f"Loaded {len(self.wordlist)} words", "INFO")
            return len(self.wordlist) > 0
        except Exception as e:
            self.log(f"Error: {e}", "ERROR")
            return False
    
    def worker(self):
        while self.scanning:
            try:
                target_url, depth = self.queue.get(timeout=1)
                
                with self.lock:
                    if target_url in self.scanned_urls:
                        self.queue.task_done()
                        continue
                    self.scanned_urls.add(target_url)
                
                try:
                    response = requests.get(
                        target_url,
                        timeout=5,
                        allow_redirects=False,
                        verify=False,
                        headers={'User-Agent': 'DirBuster/1.0'}
                    )
                    
                    status = response.status_code
                    
                    if status == 200:
                        if self.is_likely_directory(response, target_url):
                            self.log(f"{target_url} (Directory - {status})", "DIR")
                            with self.lock:
                                self.found_count += 1
                            
                            if depth < self.max_depth:
                                self.add_recursive_tasks(target_url, depth + 1)
                        else:
                            self.log(f"{target_url} (File - {status})", "HIT")
                            with self.lock:
                                self.found_count += 1
                    
                    elif status in [301, 302, 303, 307, 308]:
                        self.log(f"{target_url} (Redirect - {status})", "REDIR")
                        
                        if self.is_likely_directory(response, target_url) and depth < self.max_depth:
                            self.add_recursive_tasks(target_url, depth + 1)
                    
                    elif status == 403:
                        self.log(f"{target_url} (Forbidden - {status})", "403")
                        
                        last_part = target_url.split('/')[-1]
                        if '.' not in last_part and depth < self.max_depth:
                            self.log(f"  -> Might be directory", "INFO")
                            self.add_recursive_tasks(target_url, depth + 1)
                    
                    elif status == 404:
                        pass
                    
                    elif status == 429:
                        self.log(f"Rate limited", "ERROR")
                        time.sleep(2)
                        self.queue.put((target_url, depth))
                    
                    else:
                        self.log(f"{target_url} (Status: {status})", "INFO")
                
                except requests.Timeout:
                    self.log(f"Timeout: {target_url}", "ERROR")
                except requests.ConnectionError:
                    self.log(f"Connection failed: {target_url}", "ERROR")
                except Exception as e:
                    self.log(f"Error: {str(e)[:50]}", "ERROR")
                
                self.update_ui_status()
                self.queue.task_done()
                
            except Exception:
                continue
    
    def add_recursive_tasks(self, base_url, new_depth):
        if not base_url.endswith('/'):
            base_url += '/'
        
        recursive_words = self.wordlist[:200]
        
        for word in recursive_words:
            if not self.scanning:
                break
            
            if self.queue.qsize() > 9000:
                time.sleep(0.1)
                continue
            
            new_url = base_url + word
            self.queue.put((new_url, new_depth))
    
    def update_ui_status(self):
        def _update():
            queue_size = self.queue.qsize()
            elapsed = time.time() - self.start_time if self.start_time > 0 else 0
            self.status_label.config(
                text=f"Found: {self.found_count} | Queue: {queue_size} | Time: {elapsed:.1f}s"
            )
            
            if hasattr(self, 'total_words') and self.total_words > 0:
                scanned = len(self.scanned_urls)
                progress = min(100, (scanned / self.total_words) * 100)
                self.progress['value'] = progress
        
        self.root.after(0, _update)
    
    def start_scan(self):
        if self.scanning:
            return
        
        target = self.url_entry.get().strip()
        if not target:
            messagebox.showwarning("Warning", "Enter target URL")
            return
        
        if not self.load_wordlist():
            messagebox.showwarning("Warning", "Select valid wordlist")
            return
        
        self.scanning = True
        self.found_count = 0
        self.scanned_urls.clear()
        self.max_depth = int(self.depth_input.get())
        
        protocol = self.protocol_var.get()
        base_url = f"{protocol}{target}".rstrip('/') + '/'
        
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except:
                pass
        
        self.log_area.delete(1.0, tk.END)
        self.log(f"Starting: {base_url}", "INFO")
        self.log(f"Depth: {self.max_depth}, Threads: {self.thread_input.get()}", "INFO")
        
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.progress['value'] = 0
        self.start_time = time.time()
        self.total_words = len(self.wordlist)
        
        for word in self.wordlist:
            if not self.scanning:
                break
            self.queue.put((base_url + word, 1))
        
        num_threads = min(int(self.thread_input.get()), 50)
        for _ in range(num_threads):
            threading.Thread(target=self.worker, daemon=True).start()
        
        threading.Thread(target=self.monitor_scan, daemon=True).start()
    
    def monitor_scan(self):
        while self.scanning:
            time.sleep(0.5)
            self.update_ui_status()
            
            if self.queue.empty() and self.queue.unfinished_tasks == 0:
                time.sleep(1)
                if self.queue.empty():
                    self.root.after(0, self.scan_complete)
                    break
    
    def scan_complete(self):
        self.scanning = False
        elapsed = time.time() - self.start_time
        self.log(f"Complete! Found {self.found_count} items in {elapsed:.1f}s", "INFO")
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_label.config(text=f"Complete - Found {self.found_count} items")
    
    def stop_scan(self):
        self.scanning = False
        self.log("Scan stopped", "INFO")
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')


if __name__ == "__main__":
    root = tk.Tk()
    app = DirBuster(root)
    root.mainloop()
