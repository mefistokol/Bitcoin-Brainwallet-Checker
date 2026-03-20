import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk, simpledialog
import threading
from processor import FileProcessor

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Bitcoin Address Generator & Checker")
        self.root.geometry("600x450")
        
        self.processor = FileProcessor(
            update_callback=self.update_progress,
            log_callback=self.log_message
        )
        
        self.filepath = None
        self.thread = None
        self.start_line = 1
        
        self.setup_ui()
        
    def setup_ui(self):
        # Top frame for file selection
        top_frame = tk.Frame(self.root, pady=10, padx=10)
        top_frame.pack(fill=tk.X)
        
        self.btn_select = tk.Button(top_frame, text="Выбрать файл", command=self.select_file)
        self.btn_select.pack(side=tk.LEFT, padx=5)
        
        self.lbl_file = tk.Label(top_frame, text="Файл не выбран")
        self.lbl_file.pack(side=tk.LEFT, padx=5)
        
        # Options frame
        opt_frame = tk.Frame(self.root, pady=5, padx=10)
        opt_frame.pack(fill=tk.X)
        
        tk.Label(opt_frame, text="Режим:").pack(anchor=tk.W, padx=5)
        self.mode_var = tk.StringVar(value="all")
        tk.Radiobutton(opt_frame, text="Проверка и баланса и транзакций", variable=self.mode_var, value="all").pack(anchor=tk.W, padx=20)
        tk.Radiobutton(opt_frame, text="Только проверка были ли транзакции", variable=self.mode_var, value="txs").pack(anchor=tk.W, padx=20)
        tk.Radiobutton(opt_frame, text="Только проверка баланса", variable=self.mode_var, value="balance").pack(anchor=tk.W, padx=20)
        
        # Middle frame for progress
        mid_frame = tk.Frame(self.root, pady=10, padx=10)
        mid_frame.pack(fill=tk.X)
        
        self.progress = ttk.Progressbar(mid_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, padx=5)
        
        self.lbl_progress = tk.Label(mid_frame, text="0 / 0")
        self.lbl_progress.pack(pady=5)
        
        # Action buttons
        btn_frame = tk.Frame(self.root, pady=10)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.btn_start = tk.Button(btn_frame, text="Старт", command=self.start_processing, state=tk.DISABLED)
        self.btn_start.pack(side=tk.LEFT, padx=20)
        
        self.btn_stop = tk.Button(btn_frame, text="Стоп", command=self.stop_processing, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.RIGHT, padx=20)

        # Bottom frame for logs
        bot_frame = tk.Frame(self.root, pady=10, padx=10)
        bot_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
        self.log_area = scrolledtext.ScrolledText(bot_frame, state='disabled', height=15)
        self.log_area.pack(fill=tk.BOTH, expand=True)

    def log_message(self, message):
        self.root.after(0, self._append_log, message)
        
    def _append_log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def update_progress(self, current, total):
        self.root.after(0, self._set_progress, current, total)
        
    def _set_progress(self, current, total):
        if total > 0:
            self.progress['value'] = (current / total) * 100
        self.lbl_progress.config(text=f"{current} / {total}")
        
        if current >= total:
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)

    def select_file(self):
        filepath = filedialog.askopenfilename(
            title="Выберите текстовый файл",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        if filepath:
            start_line = simpledialog.askinteger(
                "Начальная строка",
                "С какой строки начинаем работать?",
                initialvalue=1,
                minvalue=1,
                parent=self.root
            )
            
            if start_line is None:
                return
                
            self.start_line = start_line
            self.filepath = filepath
            self.lbl_file.config(text=filepath)
            self.btn_start.config(state=tk.NORMAL)
            self.log_message(f"Выбран файл: {filepath}. Начнем со строки: {self.start_line}")

    def start_processing(self):
        if not self.filepath:
            return
            
        mode = self.mode_var.get()
            
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.progress['value'] = 0
        self.lbl_progress.config(text="0 / 0")
        
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')
        
        self.thread = threading.Thread(target=self.processor.process_file, args=(self.filepath, mode, self.start_line))
        self.thread.daemon = True
        self.thread.start()

    def stop_processing(self):
        self.processor.stop()
        self.btn_stop.config(state=tk.DISABLED)
        self.btn_start.config(state=tk.NORMAL)
        self.log_message("Остановка...")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
