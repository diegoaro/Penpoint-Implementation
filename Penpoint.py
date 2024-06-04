from pymongo import MongoClient
from couchbase.cluster import Cluster, ClusterOptions
from couchbase.auth import PasswordAuthenticator
from couchbase.options import QueryOptions
from datetime import timedelta
from datetime import datetime
from tkinter import filedialog
from tkinter import simpledialog
import tkinter as tk
from tkinter import ttk, messagebox
import base64
import uuid
import os
import requests
import traceback
import webbrowser
import math
from PIL import ImageTk
from PIL import Image
from io import BytesIO


MAX_FILE_SIZE = 1048576 * 18

ALLOWED_EXTENSIONS = ['csv', 'xlsx', 'txt', 'docx', 'jpg', 'jpeg', 'png']


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Penpoint Application")

        self.mongo_collection = self.connect_to_mongodb_atlas()
        self.couchbase_cluster = self.connect_to_couchbase()
        self.username_entry = ""
        self.create_main_window()

    def create_main_window(self):
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(padx=20, pady=20)

        ttk.Label(self.main_frame, text="Penpoint Application").grid(row=0, column=0, columnspan=2)

        ttk.Button(self.main_frame, text="Create Profile", command=self.create_profile).grid(row=1, column=0)
        ttk.Button(self.main_frame, text="Login", command=self.login).grid(row=1, column=1)
        ttk.Button(self.main_frame, text="Remove Profile", command=self.remove_profile).grid(row=2, column=0)
        ttk.Button(self.main_frame, text="Exit", command=self.destroy).grid(row=2, column=1)

    def create_profile(self):
        self.main_frame.destroy()

        create_profile_frame = ttk.Frame(self)
        create_profile_frame.pack(padx=20, pady=20)

        ttk.Label(create_profile_frame, text="Create Profile").grid(row=0, column=0, columnspan=2)

        ttk.Label(create_profile_frame, text="Enter username: ").grid(row=1, column=0)
        self.username_entry = ttk.Entry(create_profile_frame)
        self.username_entry.grid(row=1, column=1)

        ttk.Label(create_profile_frame, text="Enter email: ").grid(row=2, column=0)
        self.email_entry = ttk.Entry(create_profile_frame)
        self.email_entry.grid(row=2, column=1)

        ttk.Label(create_profile_frame, text="Enter password: ").grid(row=3, column=0)
        self.password_entry = ttk.Entry(create_profile_frame, show="*")
        self.password_entry.grid(row=3, column=1)

        ttk.Button(create_profile_frame, text="Submit", command=self.submit_profile).grid(row=4, column=0, columnspan=2)

    def submit_profile(self):
        username = self.username_entry.get()
        email = self.email_entry.get()
        password = self.password_entry.get()

        if not username or not email or not password:
            messagebox.showerror("Error", "Username, email, and password are required.")
            return

        existing_user = self.mongo_collection.find_one({'Username': username})
        if existing_user:
            messagebox.showerror("Error", "This username already exists for another account.")
            return

        existing_email = self.mongo_collection.find_one({'Email': email})
        if existing_email:
            messagebox.showerror("Error", "This email already exists for another account.")
            return

        user_profile = {
            'Username': username,
            'Email': email,
            'Password': password
        }

        self.mongo_collection.insert_one(user_profile)
        messagebox.showinfo("Success", "User profile created successfully")
        self.create_main_window()

    def login(self):
        self.main_frame.destroy()
        login_frame = ttk.Frame(self)
        login_frame.pack(padx=20, pady=20)
        ttk.Label(login_frame, text="Login").grid(row=0, column=0, columnspan=2)
        ttk.Label(login_frame, text="Enter username: ").grid(row=1, column=0)
        self.username_entry = ttk.Entry(login_frame)
        self.username_entry.grid(row=1, column=1)
        ttk.Label(login_frame, text="Enter password: ").grid(row=2, column=0)
        self.password_entry = ttk.Entry(login_frame, show="*")
        self.password_entry.grid(row=2, column=1)
        ttk.Button(login_frame, text="Login", command=self.authenticate_user).grid(row=3, column=0, columnspan=2)

    def authenticate_user(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Username and password are required.")
            return

        user = self.mongo_collection.find_one({'Username': username, 'Password': password})
        if user:
            messagebox.showinfo("Success", "Login successful!")
            self.current_user_id = str(user['_id'])
            self.file_options()
        else:
            messagebox.showerror("Error", "Invalid username or password.")

    def remove_profile(self):
        if self.couchbase_cluster is None:
            print("Failed to connect to Couchbase.")
            return

        try:
            username = simpledialog.askstring("Remove Profile", "Enter your username:")
            if not username:
                print("Error: Username cannot be empty.")
                return

            password = simpledialog.askstring("Remove Profile", "Enter your password:", show='*')
            if not password:
                print("Error: Password cannot be empty.")
                return

            query = f"DELETE FROM `UserProfiles` WHERE `Username` = $1 AND `Password` = $2"
            self.couchbase_cluster.query(query, QueryOptions(positional_parameters=[username, password]))
            self.mongo_collection.delete_one({'Username': username, 'Password': password})
            messagebox.showinfo("Remove Profile", "Profile removed successfully.")


        except Exception as e:
            print("Error removing profile:", e)
            messagebox.showerror("Remove Profile", "An error occurred while removing the profile.")

    def submit_location(self):
        location = self.location_entry.get().strip()
        if not location:
            print("Error: Location cannot be empty.")
            return

        latitude, longitude = self.get_coordinates_from_address(location)

        if latitude is None or longitude is None:
            print("Error: Unable to retrieve coordinates for the given location.")
            return

        filename = self.username_entry.get().strip()
        file_content = self.file_content

        file_data = {
            'Filename': filename,
            'Content': file_content,
            'Location': location,
            'Latitude': latitude,
            'Longitude': longitude,
            'UserID': self.current_user_id
        }

        document_id = str(uuid.uuid4())

        bucket = self.couchbase_cluster.bucket("Files")
        scope = bucket.scope("_default")
        collection = scope.collection("_default")
        collection.upsert(document_id, file_data)
        print(file_data)
        print("File uploaded successfully.")

        self.location_dialog.destroy()

    def get_location_input(self):
        location = simpledialog.askstring("Location", "Enter your location:")
        return location

    def create_note(self):
        try:
            print("Creating note...")
            print("User ID:", self.current_user_id)
            print("Couchbase cluster:", self.couchbase_cluster)

            note_content = simpledialog.askstring("Create Note", "Enter the note content:")
            if not note_content:
                print("Error: Note content cannot be empty.")
                return

            filename = simpledialog.askstring("Create Note", "Enter the filename:")
            if not filename:
                print("Error: Filename cannot be empty.")
                return
            filename = filename+'.txt'

            location = simpledialog.askstring("Create Note", "Enter the location:")
            if not location:
                print("Error: Location cannot be empty.")
                return

            latitude, longitude = self.get_coordinates_from_address(location)
            if latitude is None or longitude is None:
                print("Error: Unable to retrieve coordinates for the given location.")
                return

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            document_id = str(uuid.uuid4())

            if self.couchbase_cluster is None:
                print("Failed to connect to Couchbase.")
                return

            bucket = self.couchbase_cluster.bucket("Files")
            scope = bucket.scope("_default")
            collection = scope.collection("_default")
            collection.upsert(document_id, {
                'Filename': filename,
                'Content': note_content,
                'Location': location,
                'Latitude': latitude,
                'Longitude': longitude,
                'UserID': self.current_user_id,
                'Timestamp': timestamp
            })

            print("Note created successfully.")

        except Exception as e:
            print("Error creating note:", e)

    def get_coordinates_from_address(self, location):
        api_key = "AIzaSyD_pZg_kjk1hRgb953IS5vEbOg9JOtc6_w"
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={api_key}"
        try:
            response = requests.get(url)
            data = response.json()
            if data["status"] == "OK" and "results" in data and data["results"]:
                coordinates = data["results"][0]["geometry"]["location"]
                latitude = coordinates["lat"]
                longitude = coordinates["lng"]
                return latitude, longitude
            else:
                print("Unable to retrieve coordinates for the given location.")
                return None, None

        except Exception as e:
            print("Error retrieving coordinates:", e)
            return None, None

    def file_options(self):
        file_options_frame = ttk.Frame(self)
        file_options_frame.pack(padx=20, pady=20)

        ttk.Label(file_options_frame, text="File Options").grid(row=0, column=0, columnspan=2)

        ttk.Button(file_options_frame, text="Upload File", command=self.upload_file).grid(row=1, column=0)
        ttk.Button(file_options_frame, text="Retrieve File", command=self.retrieve_file).grid(row=1, column=1)
        ttk.Button(file_options_frame, text="Create Note", command=self.create_note).grid(row=2, column=0)
        ttk.Button(file_options_frame, text="Delete Note", command=self.delete_file).grid(row=2, column=1)
        ttk.Button(file_options_frame, text="Logout", command=self.logout).grid(row=3, column=0, columnspan=2)

    def logout(self):
        self.destroy()
        app = App()
        app.mainloop()

    def retrieve_file(self):
        def retrieve_nearest_files_gui():
            location = self.get_location_input()
            if location:
                files = self.retrieve_nearest_files(location)
                self.show_locations_on_map(files)

        def retrieve_most_recent_files_gui():
            files = self.retrieve_most_recent_files()
            self.show_locations_on_map(files)

        self.main_frame.destroy()

        retrieve_frame = ttk.Frame(self)
        retrieve_frame.pack(padx=20, pady=20)

        ttk.Label(retrieve_frame, text="Choose Retrieval Option").grid(row=0, column=0, columnspan=2)

        ttk.Button(retrieve_frame, text="Retrieve Nearest Files", command=retrieve_nearest_files_gui).grid(row=1, column=0)
        ttk.Button(retrieve_frame, text="Retrieve Most Recent Files", command=retrieve_most_recent_files_gui).grid(row=1, column=1)

    def haversine(self, lat1, lon1, lat2, lon2):
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        r = 6371
        return r * c

    def retrieve_nearest_files(self, location):
        if self.couchbase_cluster is None:
            print("Failed to connect to Couchbase.")
            return []

        latitude, longitude = self.get_coordinates_from_address(location)
        if latitude is None or longitude is None:
            print("Error: Unable to retrieve coordinates for the given location.")
            return []

        try:
            query = f"SELECT * FROM `Files` WHERE `Latitude` IS NOT MISSING AND `Longitude` IS NOT MISSING"
            result = self.couchbase_cluster.query(query)

            files_with_distance = []
            for row in result:
                file_data = row["Files"]
                if file_data["UserID"] == self.current_user_id:
                    distance = self.haversine(latitude, longitude, file_data["Latitude"], file_data["Longitude"])
                    files_with_distance.append((file_data, distance))

            files_with_distance.sort(key=lambda x: x[1])
            nearest_files = [file_data for file_data, _ in files_with_distance[:10]]
            return nearest_files

        except Exception as e:
            print("Error retrieving nearest files:", e)
            return []

    def retrieve_most_recent_files(self):
        if self.couchbase_cluster is None:
            print("Failed to connect to Couchbase.")
            return []

        try:
            query = f"SELECT * FROM `Files` WHERE `UserID` = $1 ORDER BY `Timestamp` DESC LIMIT 10"
            result = self.couchbase_cluster.query(query, QueryOptions(positional_parameters=[self.current_user_id]))
            recent_files = [row["Files"] for row in result]
            for file_data in recent_files:
                print("Retrieved file data:", file_data)
            return recent_files

        except Exception as e:
            print("Error retrieving most recent files:", e)
            return []

    def show_locations_on_map(self, files):
        print("Displaying locations on map.")
        if not files:
            print("No files to display.")
            return

        map_window = tk.Toplevel(self)
        map_window.title("Locations on Map")

        map_frame = ttk.Frame(map_window)
        map_frame.pack(padx=20, pady=20)

        ttk.Label(map_frame, text="Locations on Map").grid(row=0, column=0, columnspan=2)

        for idx, file_data in enumerate(files):
            location = (file_data["Latitude"], file_data["Longitude"])
            ttk.Button(map_frame, text=f"Show Location {idx + 1}: {file_data['Filename']}",
                       command=lambda loc=location, data=file_data: self.open_location_window(loc, data)).grid(
                row=idx + 1,
                column=0,
                columnspan=2)

    def open_location_window(self, location, file_data):
        print("Opening Google Maps for location:", location)
        url = f"https://www.google.com/maps/search/?api=1&query={location[0]},{location[1]}"
        webbrowser.open(url)
        print("Google Maps opened successfully.")

        document_window = tk.Toplevel(self)
        document_window.title("Document Content")

        document_frame = ttk.Frame(document_window)
        document_frame.pack(padx=20, pady=20)

        ttk.Label(document_frame, text="Document Content").grid(row=0, column=0, columnspan=2)

        ttk.Label(document_frame, text="Filename:").grid(row=1, column=0)
        ttk.Label(document_frame, text=file_data['Filename']).grid(row=1, column=1)

        if file_data['Filename'].lower().endswith(('.jpg', '.jpeg', '.png')):
            try:
                encoded_content = file_data['Content']
                image_bytes = base64.b64decode(encoded_content)
                image = Image.open(BytesIO(image_bytes))
                image.thumbnail((300, 300))
                photo = ImageTk.PhotoImage(image)
                image_label = ttk.Label(document_frame, image=photo)
                image_label.image = photo
                image_label.grid(row=2, column=0, columnspan=2)
            except Exception as e:
                print("Error displaying image:", e)
        elif file_data['Filename'].lower().endswith(('.csv', '.txt')):
            ttk.Label(document_frame, text="Content:").grid(row=2, column=0)
            content_text = tk.Text(document_frame, wrap="word", height=10, width=50)
            content_text.insert(tk.END, file_data['Content'])
            content_text.config(state="disabled")
            content_text.grid(row=2, column=1)
        else:
            ttk.Label(document_frame, text="File type not supported").grid(row=2, column=0, columnspan=2)

        ttk.Label(document_frame, text="Location:").grid(row=3, column=0)
        ttk.Label(document_frame, text=file_data['Location']).grid(row=3, column=1)

        ttk.Label(document_frame, text="Timestamp:").grid(row=4, column=0)
        ttk.Label(document_frame, text=file_data['Timestamp']).grid(row=4, column=1)

    def format_file_data(self, row):
        formatted_data = {
            "Filename": row.get("Filename", ""),
            "Latitude": row.get("Latitude", ""),
            "Longitude": row.get("Longitude", ""),
        }
        print("formatted_data : ", formatted_data)
        return formatted_data

    def upload_file(self):
        try:
            if not self.current_user_id:
                print("Error: User ID is not available.")
                return

            print("Starting file upload...")
            print("User ID:", self.current_user_id)
            print("Couchbase cluster:", self.couchbase_cluster)

            file_path = filedialog.askopenfilename()
            if not file_path:
                print("Error: No file selected.")
                return

            file_extension = os.path.splitext(file_path)[1].lower()[1:]
            if file_extension not in ALLOWED_EXTENSIONS:
                print("Error: File type not allowed.")
                return

            file_size = os.path.getsize(file_path)
            if file_size > MAX_FILE_SIZE:
                print("Error: File size exceeds the limit.")
                return

            with open(file_path, 'rb') as file:
                file_content = file.read()

            if not file_content:
                print("Error: File content cannot be empty.")
                return

            filename = os.path.basename(file_path)

            location = simpledialog.askstring("Upload File", "Enter the location:")
            if not location:
                print("Error: Location cannot be empty.")
                return

            latitude, longitude = self.get_coordinates_from_address(location)
            if latitude is None or longitude is None:
                print("Error: Unable to retrieve coordinates for the given location.")
                return

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            document_id = str(uuid.uuid4())

            if self.couchbase_cluster is None:
                print("Failed to connect to Couchbase.")
                return

            bucket = self.couchbase_cluster.bucket("Files")
            scope = bucket.scope("_default")
            collection = scope.collection("_default")

            encoded_content = base64.b64encode(file_content).decode('utf-8')

            collection.upsert(document_id, {
                'Filename': filename,
                'Content': encoded_content,
                'Location': location,
                'Latitude': latitude,
                'Longitude': longitude,
                'UserID': self.current_user_id,
                'Timestamp': timestamp
            })
            print("File uploaded successfully.")

        except Exception as e:
            print("Error uploading file:", e)

    def delete_file(self):
        if self.couchbase_cluster is None:
            messagebox.showerror("Delete File", "Failed to connect to Couchbase.")
            return

        filename = simpledialog.askstring("Delete File", "Enter the filename of the file to delete:")

        if filename:
            try:
                bucket = self.couchbase_cluster.bucket("Files")
                scope = bucket.scope("_default")
                collection = scope.collection("_default")

                query = f"SELECT META().id FROM `Files` WHERE `Filename` = $1"
                result = self.couchbase_cluster.query(query, QueryOptions(positional_parameters=[filename]))

                document_ids = [row['id'] for row in result.rows()]
                if document_ids:
                    for document_id in document_ids:
                        collection.remove(document_id)
                    messagebox.showinfo("Delete File", "File(s) deleted successfully.")
                else:
                    messagebox.showinfo("Delete File", "No file found with the specified filename.")

            except Exception as e:
                print("Error deleting file:", e)
                messagebox.showerror("Delete File", "An error occurred while deleting the file.")

    def connect_to_mongodb_atlas(self):
        try:
            connection_string = "mongodb+srv://dsci351:LA8fx4BTLA09uiYX@clustard.gdaup4r.mongodb.net"
            client = MongoClient(connection_string)
            db = client['Penpoint']
            user_profiles_collection = db['UserProfiles']
            print("Successfully connected to MongoDB Atlas and obtained UserProfiles collection.")
            return user_profiles_collection
        except Exception as e:
            print("Failed to connect to MongoDB Atlas or obtain UserProfiles collection:", e)
            return None

    def connect_to_couchbase(self):
        try:
            endpoint = "couchbases://cb.tnu5iu0up-eum00b.cloud.couchbase.com"
            username = "dsci351"
            password = "BananaPeely72###"

            auth = PasswordAuthenticator(username, password)
            options = ClusterOptions(auth)
            cluster = Cluster(endpoint, options)

            cluster.wait_until_ready(timedelta(seconds=5))
            print("Successfully connected to Couchbase.")
            return cluster
        except Exception as e:
            traceback.print_exc()
            print("Failed to connect to Couchbase:", e)
            return None

def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
