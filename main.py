import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, font
import json
# import psutil
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.token import Text

class CodeEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("ProCode Editor")

        # Create a dark theme
        self.dark_theme()

        # Create a PanedWindow for resizable FileManager and CodeEditor
        self.paned_window = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.paned_window.pack(expand=True, fill="both")

        # Create a FileManager
        self.file_manager = FileManager(self.paned_window, self)
        self.paned_window.add(self.file_manager)

        # Create a scrolled text widget for code
        self.text = scrolledtext.ScrolledText(self.paned_window, wrap="word", undo=True, bg="#282c34", fg="white")
        self.paned_window.add(self.text)

        # Create a Text widget for line numbers
        self.line_numbers = tk.Text(self.paned_window, width=4, padx=4, wrap=tk.NONE, bg="#333", fg="white", state="disabled")
        self.paned_window.add(self.line_numbers)

        # Set initial sizes for the PanedWindow panes
        self.paned_window.sashpos(0, 200)

        # Create a menu bar
        self.menu_bar = tk.Menu(root)
        root.config(menu=self.menu_bar)


        # File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="New", command=self.new_file)
        self.file_menu.add_command(label="Open", command=self.open_file)
        self.file_menu.add_command(label="Save", command=self.save_file)
        self.file_menu.add_command(label="Save As", command=self.save_as_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.exit_application)

        # Edit menu
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)
        self.edit_menu.add_command(label="Undo", command=self.text.edit_undo)
        self.edit_menu.add_command(label="Redo", command=self.text.edit_redo)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Cut", command=self.cut)
        self.edit_menu.add_command(label="Copy", command=self.copy)
        self.edit_menu.add_command(label="Paste", command=self.paste)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Select All", command=self.select_all)

        # View menu
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)
        self.view_menu.add_command(label="Toggle Code Folding", command=self.toggle_code_folding)

        # Preferences menu
        self.preferences_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Preferences", menu=self.preferences_menu)
        self.preferences_menu.add_command(label="Settings", command=self.show_settings)
        self.preferences_menu.add_command(label="Font", command=self.choose_font)
        self.preferences_menu.add_command(label="Zoom In", command=lambda: self.zoom_cursor(1))
        self.preferences_menu.add_command(label="Zoom Out", command=lambda: self.zoom_cursor(-1))

        # Set color tags for syntax highlighting
        self.text.tag_configure("keyword", foreground="#569CD6")  # Blue color
        self.text.tag_configure("comment", foreground="#6A9955")  # Grey color
        self.text.tag_configure("string", foreground="#CE9178")  # Orange color

        # Bind events
        self.text.bind("<KeyRelease>", self.highlight)
        self.text.bind("<Tab>", self.auto_indent)
        self.text.bind("<Configure>", self.update_line_numbers)
        self.text.bind("<MouseWheel>", self.on_mousewheel)
        self.text.bind("<Button-4>", self.on_mousewheel)
        self.text.bind("<Button-5>", self.on_mousewheel)
        self.root.bind("<Control-plus>", lambda event: self.increase_font_size())  # Bind Ctrl + Plus to increase font size
        self.root.bind("<Control-s>", lambda event: self.save_file())  # Bind Ctrl + S to save file
        self.root.bind("<Control-o>", lambda event: self.open_file())  # Bind Ctrl + O to open file

        # Initialize file path
        self.file_path = None

        # Initialize font settings
        self.text_font = font.Font(family="Courier New", size=12)

        # Load settings
        self.load_settings()

    def increase_font_size(self):
        """Increase the font size in the text widget."""
        current_size = self.text_font.actual()["size"]
        new_size = int(current_size * 1.1)
        self.text_font.configure(size=new_size)
        self.text.config(font=self.text_font)
        self.update_line_numbers()

    def load_settings(self):
        """Load application settings from a JSON file."""
        try:
            with open("settings.json", "r") as settings_file:
                settings = json.load(settings_file)
                if "font" in settings:
                    font_settings = settings["font"]
                    self.text_font.configure(family=font_settings["family"], size=font_settings["size"])
                    self.text.config(font=self.text_font)
        except FileNotFoundError:
            pass  # Ignore if the file doesn't exist

    def save_settings(self):
        """Save application settings to a JSON file."""
        settings = {"font": {"family": self.text_font.actual()["family"], "size": self.text_font.actual()["size"]}}
        with open("settings.json", "w") as settings_file:
            json.dump(settings, settings_file)

    def exit_application(self):
        """Exit the application."""
        self.save_settings()  # Save settings before exiting
        self.root.destroy()
        
    def dark_theme(self):
        """Set a dark theme for the editor."""
        self.root.tk_setPalette(background="#282c34", foreground="white", activeBackground="#3E4451", activeForeground="white")

    def update_line_numbers(self, event=None):
        """Update line numbers."""
        line_numbers_text = "\n".join(str(i) for i in range(1, int(str(self.text.count("1.0", tk.END)).split('.')[0]) + 1))
        self.line_numbers.config(state="normal")
        self.line_numbers.delete("1.0", tk.END)
        self.line_numbers.insert("1.0", line_numbers_text)
        self.line_numbers.config(state="disabled")

    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.line_numbers.yview_scroll(-1 * (event.delta // 120), "units")
        self.text.yview_scroll(-1 * (event.delta // 120), "units")
        return "break"

    def choose_font(self):
        """Change the font of the text widget."""
        chosen_font = font.askfont(parent=self.root, font=self.text_font)
        if chosen_font:
            self.text_font = font.Font(family=chosen_font["family"], size=chosen_font["size"])
            self.text.config(font=self.text_font)

    def zoom_cursor(self, factor):
        """Zoom in/out the cursor."""
        current_size = self.text_font.actual()["size"]
        new_size = int(current_size * (1.1 ** factor))
        self.text_font.configure(size=new_size)
        self.text.config(font=self.text_font)

    def new_file(self):
        """Clear the text widget and reset the file path."""
        self.text.delete(1.0, tk.END)
        self.file_path = None
        self.update_line_numbers()
        

    def open_file(self):
        """Open a file and display its content in the text widget."""
        file_path = filedialog.askopenfilename(defaultextension=".py", filetypes=[("Python files", "*.py"), ("All files", "*.*")])
        if file_path:
            with open(file_path, "r") as file:
                content = file.read()
                self.text.delete(1.0, tk.END)
                self.text.insert(tk.END, content)
                self.highlight(None)
                self.file_path = file_path
                self.update_line_numbers()

    def save_file(self):
        """Save the content to the current file path."""
        if self.file_path:
            with open(self.file_path, "w") as file:
                content = self.text.get(1.0, tk.END)
                file.write(content)
        else:
            self.save_as_file()

    def save_as_file(self):
        """Save the content to a new file path."""
        file_path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python files", "*.py"), ("All files", "*.*")])
        if file_path:
            with open(file_path, "w") as file:
                content = self.text.get(1.0, tk.END)
                file.write(content)
                self.file_path = file_path
                self.update_line_numbers()

    def highlight(self, event):
        """Apply syntax highlighting to the code."""
        code = self.text.get(1.0, tk.END)
        self.text.tag_remove("keyword", 1.0, tk.END)
        self.text.tag_remove("comment", 1.0, tk.END)
        self.text.tag_remove("string", 1.0, tk.END)

        lexer = PythonLexer(stripnl=False)
        for token, value in lex(code, lexer):
            if token is Text:
                continue
            if len(value) < 2:
                continue  # Skip tokens without position information

            tag_name = str(token)
            start = f"1.{value[1] + 1}"  # Convert to Tkinter text index
            end = f"1.{value[1] + 1 + len(value[0])}"  # Convert to Tkinter text index
            self.text.tag_add(tag_name, start, end)

    def cut(self):
        """Cut selected text."""
        self.text.event_generate("<<Cut>>")

    def copy(self):
        """Copy selected text."""
        self.text.event_generate("<<Copy>>")

    def paste(self):
        """Paste clipboard content."""
        self.text.event_generate("<<Paste>>")

    def select_all(self):
        """Select all text in the editor."""
        self.text.tag_add(tk.SEL, "1.0", tk.END)

    def toggle_code_folding(self):
        """Toggle code folding."""
        # Implement code folding logic here
        messagebox.showinfo("Code Folding", "Toggle Code Folding")

    def auto_indent(self, event):
        """Implement auto-indentation logic."""
        current_line = self.text.get(tk.INSERT + " linestart", tk.INSERT)
        spaces = len(current_line) - len(current_line.lstrip())
        self.text.insert(tk.INSERT, " " * spaces)
        return 'break'

    def show_settings(self):
        """Show settings dialog."""
        # Create a new window for settings
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")

        # Add some basic settings
        label = tk.Label(settings_window, text="Choose your setting:")
        label.pack(pady=10)

        # Example checkbox setting
        checkbox_var = tk.BooleanVar()
        checkbox = tk.Checkbutton(settings_window, text="Enable Feature", variable=checkbox_var)
        checkbox.pack()

        # Example entry setting
        entry_label = tk.Label(settings_window, text="Enter something:")
        entry_label.pack()
        entry_var = tk.StringVar()
        entry = tk.Entry(settings_window, textvariable=entry_var)
        entry.pack()

        # Example button to save settings
        save_button = tk.Button(settings_window, text="Save Settings", command=lambda: self.save_settings(checkbox_var.get(), entry_var.get()))
        save_button.pack(pady=10)

    def save_settings(self, enable_feature, entered_text):
        """Save settings."""
        # You can save the settings to a file or perform actions based on the settings
        print("Enable Feature:", enable_feature)
        print("Entered Text:", entered_text)
        messagebox.showinfo("Settings Saved", "Settings have been saved.")
        
        # Create a button to open the settings
        settings_button = tk.Button(root, text="Open Settings", command=app.show_settings)
        settings_button.pack(pady=20)

        
        
    
    def update_system_performance(self):
        """Update system performance in the status bar."""
        cpu_usage = psutil.cpu_percent(interval=1)
        ram_usage = psutil.virtual_memory().percent
        performance_text = f"CPU: {cpu_usage:.2f}%   RAM: {ram_usage:.2f}%"
        self.status_bar.config(text=performance_text)
        
    def show_github_repo(self):
        """Open the GitHub repository in the default web browser."""
        import webbrowser
        webbrowser.open("https://github.com/your-username/your-repository")


class FileManager(tk.Frame):
    def __init__(self, parent, code_editor):
        super().__init__(parent, bg="#333")
        self.code_editor = code_editor

        self.file_listbox = tk.Listbox(self, bg="#333", fg="white", selectbackground="#555")
        self.file_listbox.pack(expand=True, fill="both")

        self.populate_file_list()
        self.file_listbox.bind("<Double-Button-1>", self.open_selected_file)
        

    def populate_file_list(self):
        """Populate the file listbox with files in the current directory."""
        self.file_listbox.delete(0, tk.END)
        files = os.listdir()
        for file in files:
            self.file_listbox.insert(tk.END, file)
    

    def open_selected_file(self, event):
        """Open the selected file in the code editor."""
        selected_index = self.file_listbox.curselection()
        if selected_index:
            selected_file = self.file_listbox.get(selected_index)
            file_path = os.path.abspath(selected_file)
            if os.path.isfile(file_path):
                with open(file_path, "r") as file:
                    content = file.read()
                    self.code_editor.text.delete(1.0, tk.END)
                    self.code_editor.text.insert(tk.END, content)
                    self.code_editor.highlight(None)
                    self.code_editor.file_path = file_path
                    self.code_editor.update_line_numbers()


if __name__ == "__main__":
    root = tk.Tk()
    app = CodeEditor(root)
    root.mainloop()