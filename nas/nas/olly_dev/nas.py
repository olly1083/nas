import tkinter as tk
from tkinter import filedialog, simpledialog
from github import Github
import requests
import os
import io
from PIL import Image, ImageTk

class GitHubExplorer:
    def __init__(self, root, token, owner, repo_name):
        self.root = root
        self.root.title("NAS Interface")
        self.root.geometry("800x600")  # Initial size of the window
        self.root.resizable(True, True)  # Allow both horizontal and vertical resizing

        self.current_path = 'nas/nas'
        self.previous_paths = []

        self.g = Github(token)
        self.repo = self.g.get_user(owner).get_repo(repo_name)

        self.create_widgets()
        self.update_files_list(self.current_path)
    
    def edit_file(self, file_name):
        try:
            file_content = self.repo.get_contents(f"{self.current_path}/{file_name}")
            file_data = requests.get(file_content.download_url).content
            if self.is_image(file_name):
                self.show_image(file_name, file_data)
            else:
                self.open_edit_window(file_name, file_data.decode('utf-8'))
        except Exception as e:
            print("An error occurred while viewing the file:", e)

    def open_edit_window(self, file_name, file_text):
        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Editing: {file_name}")
        edit_window.geometry("600x400")

        self.text_area = tk.Text(edit_window, wrap=tk.WORD)
        self.text_area.insert(tk.END, file_text)
        self.text_area.pack(expand=1, fill='both')

        save_button = tk.Button(edit_window, text="Save", command=lambda: self.save_file(edit_window, file_name), font=("Arial", 14))
        save_button.pack(pady=10)

    def save_file(self, edit_window, file_name):
        new_text = self.text_area.get("1.0", tk.END)
        try:
            file_content = self.repo.get_contents(f"{self.current_path}/{file_name}")
            self.repo.update_file(file_content.path, f"Update {file_name}", new_text, file_content.sha)
            print("File saved successfully.")
            edit_window.destroy()  # Close the edit window after saving
            self.update_files_list(self.current_path)  # Update the file list
        except Exception as e:
            print("An error occurred while saving the file:", e)

    def create_widgets(self):
        # Create a frame to hold the buttons and the listbox
        frame = tk.Frame(self.root)
        frame.pack(padx=20, pady=20)

        open_and_edit_button = tk.Button(frame, text="Open and Edit", command=self.open_and_edit_file, font=("Arial", 14))
        open_and_edit_button.grid(row=9, column=0, padx=5, pady=5)


        # Create the "Upload" button
        upload_button = tk.Button(frame, text="Upload", command=self.upload, font=("Arial", 14))
        upload_button.grid(row=0, column=0, padx=5, pady=5)

        # Create the "Create Folder" button
        create_folder_button = tk.Button(frame, text="Create Folder", command=self.create_folder, font=("Arial", 14))
        create_folder_button.grid(row=1, column=0, padx=5, pady=5)

        #create/edit button
        create_file_button = tk.Button(frame, text="Create File", command=self.create_file_and_edit, font=("Arial", 14))
        create_file_button.grid(row=8, column=0, padx=5, pady=5)

        # Create the "Upload Folder" button
        upload_folder_button = tk.Button(frame, text="Upload Folder", command=self.upload_folder, font=("Arial", 14))
        upload_folder_button.grid(row=2, column=0, padx=5, pady=5)

        # Create the "Download" button
        download_button = tk.Button(frame, text="Download", command=self.download_selected, font=("Arial", 14))
        download_button.grid(row=3, column=0, padx=5, pady=5)

        open_and_edit_button = tk.Button(frame, text="Open and Edit", command=self.open_and_edit_file, font=("Arial", 14))
        open_and_edit_button.grid(row=9, column=0, padx=5, pady=5)

        # Create the "Delete" button
        delete_button = tk.Button(frame, text="Delete", command=self.delete_selected, font=("Arial", 14))
        delete_button.grid(row=4, column=0, padx=5, pady=5)

        # Create the "Dark Mode" button
        dark_mode_button = tk.Button(frame, text="Dark Mode", command=self.toggle_dark_mode, font=("Arial", 14))
        dark_mode_button.grid(row=5, column=0, padx=5, pady=5)

        # Create the "Light Mode" button
        light_mode_button = tk.Button(frame, text="Light Mode", command=self.toggle_light_mode, font=("Arial", 14))
        light_mode_button.grid(row=6, column=0, padx=5, pady=5)

        # Create the "Back" button
        self.back_button = tk.Button(frame, text="Back", command=self.go_back, font=("Arial", 14), state=tk.DISABLED)
        self.back_button.grid(row=7, column=0, padx=5, pady=5)

        # Create a listbox to display files in the repository
        self.listbox = tk.Listbox(frame, height=20, width=50, font=("Arial", 12))
        self.listbox.grid(row=0, column=1, rowspan=8, padx=5, pady=5)
        self.listbox.bind('<Double-1>', self.on_item_double_click)

    def upload(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            print("File uploaded:", file_path)
            self.upload_to_github(file_path)

    def upload_to_github(self, file_path):
        file_name = os.path.basename(file_path)
        try:
            self.repo.create_file(f"{self.current_path}/{file_name}", f"Upload {file_name}", open(file_path, 'rb').read())
            print("File uploaded successfully.")
            self.update_files_list(self.current_path)
        except Exception as e:
            print("An error occurred while uploading the file:", e)

    def create_folder(self):
        folder_name = simpledialog.askstring("Create Folder", "Enter folder name:")
        if folder_name:
            try:
                folder_path = f"{self.current_path}/{folder_name}"
                self.repo.create_file(f"{folder_path}/DO_NOT_DELETE.txt", f"Create folder {folder_name}", "", branch="main")
                print("Folder created successfully.")
                self.update_files_list(self.current_path)
            except Exception as e:
                print("An error occurred while creating the folder:", e)

    def update_files_list(self, path):
        try:
            contents = self.repo.get_contents(path)
            self.listbox.delete(0, tk.END)  # Clear the listbox
            for content in contents:
                if content.type == "dir":
                    self.listbox.insert(tk.END, f"[Folder] {content.name}")
                elif content.name != "DO_NOT_DELETE.txt":
                    self.listbox.insert(tk.END, content.name)
        except Exception as e:
            print("An error occurred while updating files list:", e)

    def download_selected(self):
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_item = self.listbox.get(selected_index[0])  # Retrieve the first selected item
            if selected_item.startswith("[Folder] "):
                folder_name = selected_item.split("[Folder] ")[1]
                self.open_folder(folder_name)
            else:
                self.download_file(selected_item)
    def create_file_and_edit(self):
        file_name = simpledialog.askstring("Create File", "Enter file name:")
        if file_name:
            try:
                file_content = simpledialog.askstring("File Content", "Enter file content:")
                if file_content is not None:
                    file_path = f"{self.current_path}/{file_name}"
                    self.repo.create_file(file_path, f"Create {file_name}", file_content, branch="main")
                    print("File created successfully.")
                    self.update_files_list(self.current_path)
                else:
                    print("File content cannot be empty.")
            except Exception as e:
                print("An error occurred while creating the file:", e)

    def download_file(self, file_name):
        download_path = filedialog.askdirectory()
        if download_path:
            try:
                file_content = self.repo.get_contents(f"{self.current_path}/{file_name}")
                with open(os.path.join(download_path, file_name), 'wb') as f:
                    f.write(requests.get(file_content.download_url).content)
                print("File downloaded successfully.")
            except Exception as e:
                print("An error occurred while downloading the file:", e)

    def open_folder(self, folder_name):
        self.previous_paths.append(self.current_path)
        self.current_path = f"{self.current_path}/{folder_name}"
        self.update_files_list(self.current_path)
        self.back_button.config(state=tk.NORMAL)

    def go_back(self):
        if self.previous_paths:
            self.current_path = self.previous_paths.pop()
            self.update_files_list(self.current_path)
        if not self.previous_paths:
            self.back_button.config(state=tk.DISABLED)

    def delete_selected(self):
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_item = self.listbox.get(selected_index)
            if selected_item.startswith("[Folder] "):
                folder_name = selected_item.split("[Folder] ")[1]
                self.delete_folder(folder_name)
            else:
                self.delete_file(selected_item)

    def delete_file(self, file_name):
        try:
            file_content = self.repo.get_contents(f"{self.current_path}/{file_name}")
            self.repo.delete_file(file_content.path, f"Delete {file_name}", file_content.sha)
            print("File deleted successfully")
            self.update_files_list(self.current_path)
        except Exception as e:
            print("An error occurred while deleting the file:", e)

    def delete_folder(self, folder_name):
        folder_path = f"{self.current_path}/{folder_name}"
        try:
            contents = self.repo.get_contents(folder_path)
            for content in contents:
                if content.type == "dir":
                    self.delete_folder(content.path)
                else:
                    self.repo.delete_file(content.path, f"Delete {content.name}", content.sha)
            self.repo.delete_file(f"{folder_path}/DO_NOT_DELETE.txt", f"Delete folder {folder_name}", contents[0].sha)
            print(f"Folder '{folder_name}' deleted successfully.")
            self.update_files_list(self.current_path)
        except Exception as e:
            print(f"An error occurred while deleting the folder '{folder_name}':", e)

    def upload_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    self.upload_to_github(file_path)

    def toggle_dark_mode(self):
        self.root.configure(bg='#2e2e2e')
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Button):
                widget.configure(bg='black', fg='white')  # Change button colors
            else:
                widget.configure(bg='#2e2e2e', fg='white')  # Update other widgets
        self.listbox.configure(bg='#3e3e3e', fg='white')  # Update listbox colors

    def toggle_light_mode(self):
        self.root.configure(bg='white')
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Button):
                widget.configure(bg='white', fg='black')  # Change button colors
            else:
                widget.configure(bg='white', fg='black')  # Update other widgets
        self.listbox.configure(bg='white', fg='black')  # Update listbox colors

    def on_item_double_click(self, event):
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_item = self.listbox.get(selected_index)
            if selected_item.startswith("[Folder] "):
                folder_name = selected_item.split("[Folder] ")[1]
                self.open_folder(folder_name)
            else:
                self.view_file(selected_item)

    def view_file(self, file_name):
        try:
            file_content = self.repo.get_contents(f"{self.current_path}/{file_name}")
            file_data = requests.get(file_content.download_url).content
            if self.is_image(file_name):
                self.show_image(file_name, file_data)
            else:
                self.show_file_content(file_name, file_data.decode('utf-8'))
        except Exception as e:
            print("An error occurred while viewing the file:", e)

    def is_image(self, file_name):
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.ico')
        return file_name.lower().endswith(image_extensions)

    def show_file_content(self, file_name):
        try:
            file_content = self.repo.get_contents(f"{self.current_path}/{file_name}")
            file_data = requests.get(file_content.download_url).content
            if self.is_image(file_name):
                self.show_image(file_name, file_data)
            else:
                self.show_file_content(file_name, file_data.decode('utf-8'))
        except Exception as e:
            print("An error occurred while viewing the file:", e)
    

    def open_and_edit_file(self):
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_item = self.listbox.get(selected_index)
            if not selected_item.startswith("[Folder] "):
                file_name = selected_item
                self.edit_file(file_name)
            else:
                print("Please select a file, not a folder.")
        else:
            print("Please select a file.")

    def is_image(self, file_name):
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.ico')
        return file_name.lower().endswith(image_extensions)

    def show_image(self, file_name, file_data):
        view_window = tk.Toplevel(self.root)
        view_window.title(f"Viewing: {file_name}")
        view_window.geometry("600x400")

        self.original_image_data = file_data  # Keep a reference to the original image data

        image = Image.open(io.BytesIO(file_data))
        self.photo = ImageTk.PhotoImage(image)

        self.image_label = tk.Label(view_window, image=self.photo)
        self.image_label.image = self.photo  # Keep a reference to avoid garbage collection
        self.image_label.pack(expand=1, fill='both')

        view_window.bind("<MouseWheel>", self.zoom_image)

    def zoom_image(self, event):
        scale = 1.0
        if event.delta > 0:
            scale *= 1.1
        else:
            scale /= 1.1
        width, height = self.photo.width(), self.photo.height()  # Get original image dimensions
        new_size = (int(width * scale), int(height * scale))
        image = Image.open(io.BytesIO(self.original_image_data))  # Use original image data
        resized_image = image.resize(new_size, Image.BICUBIC)
        self.photo = ImageTk.PhotoImage(resized_image)
        self.image_label.config(image=self.photo)
        self.image_label.image = self.photo  # Keep a reference to avoid garbage collection

    def show_file_content(self, file_name, file_text):
        view_window = tk.Toplevel(self.root)
        view_window.title(f"Viewing: {file_name}")
        view_window.geometry("600x400")

        self.text_area = tk.Text(view_window, wrap=tk.WORD)
        self.text_area.insert(tk.END, file_text)
        self.text_area.configure(state='disabled')  # Make the text area read-only
        self.text_area.pack(expand=1, fill='both')

        view_window.bind("<Control-MouseWheel>", self.zoom_text)

    def zoom_text(self, event):
        if event.state & 0x4:  # Check if the Ctrl key is pressed
            if event.delta > 0:
                self.font_size += 1  # Increase font size
            else:
                self.font_size -= 1  # Decrease font size
            self.font_size = max(self.font_size, 8)  # Limit font size minimum to 8
            self.font_size = min(self.font_size, 24)  # Limit font size maximum to 24
            self.text_area.configure(font=("Arial", self.font_size))  # Update text area font size

if __name__ == "__main__":
    # Check if settings.txt exists and load settings if it does
    token = ""
    owner = ""
    repo_name = ""
    if os.path.exists("settings.txt"):
        with open("settings.txt", "r") as file:
            lines = file.readlines()
            token = lines[0].strip()
            owner = lines[1].strip()
            repo_name = lines[2].strip()

    root = tk.Tk()
    if token and owner and repo_name:
        app = GitHubExplorer(root, token, owner, repo_name)
    else:
        token = simpledialog.askstring("GitHub Token", "Enter your GitHub token:")
        owner = simpledialog.askstring("Repository Owner", "Enter the repository owner:")
        repo_name = simpledialog.askstring("Repository Name", "Enter the repository name:")
        if token and owner and repo_name:
            app = GitHubExplorer(root, token, owner, repo_name)
            # Save settings to settings.txt
            with open("settings.txt", "w") as file:
                file.write(f"{token}\n{owner}\n{repo_name}")
        else:
            print("GitHub token, owner, and repository name are required.")
            root.destroy()
    root.mainloop()



