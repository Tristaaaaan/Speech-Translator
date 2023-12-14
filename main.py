import sqlite3
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from google_trans_new import google_translator
from kivy import platform

from docx import Document
import speech_recognition as sr
import os
from plyer import stt

if platform == "android":
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.INTERNET, Permission.RECORD_AUDIO])


class SignUpPopup(BoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(orientation='vertical', spacing=10, **kwargs)
        self.app = app

        self.add_widget(Label(text="Create an Account",
                        size_hint_y=None, height=30))

        self.username_input = TextInput(
            multiline=False, height=40, hint_text="Username")
        self.add_widget(self.username_input)

        self.password_input = TextInput(
            multiline=False, password=True, height=40, hint_text="Password")
        self.add_widget(self.password_input)

        button_layout = BoxLayout(orientation='horizontal', spacing=10)
        button_layout.add_widget(
            Button(text="Register", background_color=(0, 0, 1, 1), on_press=self.register))
        button_layout.add_widget(
            Button(text="Cancel", background_color=(1, 0, 0, 1), on_press=self.cancel))

        self.add_widget(button_layout)

    def cancel(self, instance):
        self.parent.dismiss()

    def register(self, instance):
        username = self.username_input.text
        password = self.password_input.text

        if self.app.register_user(username, password):
            print("Registration successful!")
        else:
            print("Registration failed")


class MenuBar(BoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.size_hint_y = None
        self.height = 50
        self.logged_in = False  # Add a variable to track login status

        self.add_widget(Button(text="Home", background_color=(
            0, 0, 1, 1), on_press=self.show_login_popup))
        self.add_widget(Button(text="Dashboard", background_color=(
            0, 0, 1, 1), on_press=self.show_login_popup))
        self.add_widget(Button(text="Profile", background_color=(
            0, 0, 1, 1), on_press=self.show_login_popup))

    def show_login_popup(self, instance):
        content = BoxLayout(orientation='vertical', spacing=10)
        content.add_widget(Label(text="Username", size_hint_y=None, height=30))
        self.username_input = TextInput(multiline=False, height=40)
        content.add_widget(self.username_input)
        content.add_widget(Label(text="Password", size_hint_y=None, height=30))
        self.password_input = TextInput(
            multiline=False, password=True, height=40)
        content.add_widget(self.password_input)

        button_layout = BoxLayout(orientation='horizontal', spacing=10)
        button_layout.add_widget(
            Button(text="Sign IN", background_color=(0, 0, 1, 1), on_press=self.sign_in))
        button_layout.add_widget(Button(text="Sign Up", background_color=(
            0, 0, 1, 1), on_press=self.sign_up_with_google))

        content.add_widget(button_layout)

        self.popup = Popup(title='Login', background_color=(
            0, 0, 1, 1), content=content, size_hint=(None, None), size=(300, 250))
        self.popup.open()

    def sign_up_with_google(self, instance):
        self.popup.dismiss()
        self.app.show_signup_popup()

    def sign_in(self, instance):
        username = self.username_input.text
        password = self.password_input.text

        # Check if the entered credentials are valid
        if self.authenticate_user(username, password):
            print("Login successful!")
            self.popup.dismiss()
            self.logged_in = True  # Update login status
            self.app.show_microphone_option()
        else:
            print("Invalid credentials")

    def authenticate_user(self, username, password):
        # Connect to SQLite database (you can replace this with your database connection logic)
        connection = sqlite3.connect("users.db")
        cursor = connection.cursor()

        # Check if the username and password match a record in the database
        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()

        connection.close()

        return user is not None

    def start_recording(self, instance):
        # Check if the user is logged in
        if self.logged_in:
            # Your existing start_recording logic
            self.app.start_recording(instance)
        else:
            # Display message on the output screen
            self.app.output_box.text = "User not logged in. Please log in to start recording."

    def stop_recording(self, instance):
        # Check if the user is logged in
        if self.logged_in:
            # Your existing stop_recording logic
            self.app.stop_recording(instance)
        else:
            print("User not logged in. Please log in to stop recording.")


class MyApp(App):
    def build(self):
        # Main layout
        self.main_layout = BoxLayout(orientation='vertical', spacing=10)

        # Menu bar
        self.menu_bar = MenuBar(self)
        self.main_layout.add_widget(self.menu_bar)

        button_start_recording = Button(
            text="Start Recording", size_hint_y=None, height=50, background_color=(0, 1, 0, 1))
        # Bind to MenuBar's method
        button_start_recording.bind(on_press=self.menu_bar.start_recording)

        button_stop_recording = Button(
            text="Stop Recording", size_hint_y=None, height=50, background_color=(1, 0, 0, 1))
        # Bind to MenuBar's method
        button_stop_recording.bind(on_press=self.menu_bar.stop_recording)

        # Home screen
        self.home_screen = BoxLayout(
            orientation='vertical', spacing=10, padding=10)

        # Output box
        self.output_box = TextInput(readonly=True, multiline=True)

        # Button
        button_download = Button(
            text="Download File", size_hint_y=None, height=50, background_color=(0, 0, 1, 1))
        button_download.bind(on_press=self.download_file)

        # Add widgets to home screen
        self.home_screen.add_widget(button_start_recording)
        self.home_screen.add_widget(button_stop_recording)
        self.home_screen.add_widget(self.output_box)
        self.home_screen.add_widget(button_download)

        # Add widgets to the main layout
        self.main_layout.add_widget(self.home_screen)

        return self.main_layout

    def download_file(self, instance):
        self.save_to_word_document()

    def start_recording(self, instance):

        if stt.listening:
            self.stop_recording()
            return

        stt.start()

    def update(self):

        recognized_text = '\n'.join(stt.results)

        translated_text = self.translate_and_display(recognized_text)
        self.output_box.text = f"Original Text: {recognized_text}\nTranslated Text: {translated_text}"

    def stop_recording(self, instance):
        self.output_box.text += "\nRecording stopped."
        stt.stop()
        self.update()

    def save_to_word_document(self):
        document = Document()
        document.add_paragraph(self.output_box.text)

        # Specify the directory where the file should be saved
        save_directory = "your_preferred_directory"

        # Check if the directory exists, if not, create it
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        # Save the document with a predefined name
        file_path = os.path.join(save_directory, "myconvertedfile.docx")
        document.save(file_path)

        self.output_box.text += f"\nFile '{file_path}' saved successfully!\n"

    def translate_and_display(self, original_text):
        translated_text = self.translate_text(original_text)
        return translated_text

    def translate_text(self, text):
        translator = google_translator()
        translation = translator.translate(text, dest='en')
        return translation.text

    def show_microphone_option(self):
        # Create and add a microphone option to the home screen
        microphone_icon = Label(
            text="[b]🎤[/b]", markup=True, size_hint=(None, None), height=100, width=40)
        microphone_button = Button(
            text="Microphone Option 🎤", size_hint_y=None, height=40, background_color=(0, 0, 1, 1))
        microphone_button.bind(on_release=self.start_recording)

    def show_login_popup(self):
        self.menu_bar.show_login_popup(None)

    def show_signup_popup(self):
        content = SignUpPopup(self)
        popup = Popup(title='Sign Up', background_color=(
            0, 0, 1, 1), content=content, size_hint=(None, None), size=(300, 250))
        popup.open()

    def register_user(self, username, password):
        # Connect to SQLite database (you can replace this with your database connection logic)
        connection = sqlite3.connect("users.db")
        cursor = connection.cursor()

        try:
            # Create users table if not exists
            cursor.execute('''CREATE TABLE IF NOT EXISTS users
                              (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT)''')

            # Insert user data into the table
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)", (username, password))

            # Commit the changes
            connection.commit()
            return True
        except sqlite3.Error as e:
            print("SQLite error:", e)
            return False
        finally:
            # Close the connection
            connection.close()


if __name__ == '__main__':
    MyApp().run()
