import sqlite3
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from deep_translator import GoogleTranslator
from kivy import platform
from os.path import dirname, join
from docx import Document
from datetime import datetime
from kivy.clock import Clock
from kivy.clock import mainthread
from textwrap import fill
from kivy.uix.scrollview import ScrollView

if platform == "android":
    from speech_events import SpeechEvents
    from androidstorage4kivy import SharedStorage
    from jnius import autoclass
    from android.permissions import request_permissions, Permission

    # Define the required permissions
    request_permissions([
        Permission.RECORD_AUDIO,
        Permission.WRITE_EXTERNAL_STORAGE,
        Permission.READ_EXTERNAL_STORAGE,
        Permission.INTERNET
    ])

    # Environment
    Environment = autoclass('android.os.Environment')

# Connect to SQLite database (you can replace this with your database connection logic)
connection = sqlite3.connect("users.db")
cursor = connection.cursor()

# Create users table if not exists
cursor.execute('''CREATE TABLE IF NOT EXISTS users
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT)''')


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
        self.parent.parent.parent.dismiss()

    def register(self, instance):
        username = self.username_input.text
        password = self.password_input.text

        if self.app.register_user(username, password):
            print("Registration successful!")
            self.cancel
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
            0, 0, 1, 1), content=content, size_hint=(.8, .4))
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
            self.app.output_box.text = "\nUser not logged in. Please log in to start recording."

    def stop_recording(self, instance):

        # Check if the user is logged in
        if self.logged_in:
            # Your existing stop_recording logic
            self.app.stop_recording(instance)
        else:
            self.app.output_box.text = "\nUser not logged in. Please log in to start recording."


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

        button_clear_textbox = Button(
            text="Clear", size_hint_y=None, height=50, background_color=(128/255, 128/255, 128/255, 1))
        # Bind to MenuBar's method
        button_clear_textbox.bind(on_press=self.clear_textbox)
        
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
        self.home_screen.add_widget(button_clear_textbox)
        self.home_screen.add_widget(self.output_box)
        self.home_screen.add_widget(button_download)

        # Add widgets to the main layout
        self.main_layout.add_widget(self.home_screen)

        return self.main_layout

    def clear_textbox(self, instance):
        self.output_box.text = ''
        
    def download_file(self, instance):
        self.save_to_word_document()

    def start_recording(self, instance):

        self.output_box.text = ''

        self.unwrapped = ''

        self.output_box.text += "\nRecording started."

        self.speech_events = SpeechEvents()

        self.speech_events.create_recognizer(self.recognizer_event_handler)

        if self.speech_events:

            self.unwrapped = ''

            self.speech_events.start_listening()

    def stop_recording(self, instance):

        self.output_box.text += "\n\nRecording stopped."

        self.speech_events.stop_listening()

        self.update()

    @mainthread
    def recognizer_event_handler(self, key, value):
        if key == 'onReadyForSpeech':
            self.output_box.text += '\n\nStatus: Listening.'
        elif key == 'onBeginningOfSpeech':
            self.output_box.text += '\n\nStatus: Speaker Detected.'
        elif key == 'onEndOfSpeech':
            self.output_box.text += '\n\nStatus: Not Listening.'
        elif key == 'onError':
            self.output_box.text += '\n\nStatus: ' + value + ' Not Listening.'
        elif key in ['onPartialResults', 'onResults']:
            self.unwrapped = str(value)
            #self.output_box.text += fill(value, 40)
        elif key in ['onBufferReceived', 'onEvent', 'onRmsChanged']:
            pass

    def update(self):

        recognized_text = self.unwrapped

        translated_text = self.translate_and_display(recognized_text)

        self.output_box.text += f"\n\nTranslated Text: {translated_text}"

    def save_to_word_document(self):

        # Generate a unique filename with timestamp
        current_datetime = datetime.now()
        timestamp = current_datetime.strftime(
            "%Y%m%d%H%M%S")  # YearMonthDayHourMinuteSecond

        ss = SharedStorage()

        document = Document()
        document.add_paragraph(self.output_box.text)
        document_file = f"{timestamp}.docx"
        document.save(document_file)

        # Get the path to the DCIM camera directory
        save_path = Environment.getExternalStoragePublicDirectory(
            Environment.DIRECTORY_DOCUMENTS).getAbsolutePath()

        ss.copy_to_shared(document_file, save_path)

        self.output_box.text += f"\n\nFile '{document_file}' saved successfully!"

    def translate_and_display(self, original_text):

        translated_text = self.translate_text(original_text)

        return translated_text

    def translate_text(self, text):

        translate_text = GoogleTranslator(
            source='auto', target='en').translate(text)

        return translate_text

    def show_login_popup(self):
        self.menu_bar.show_login_popup(None)

    def show_signup_popup(self):
        content = SignUpPopup(self)
        popup = Popup(title='Sign Up', background_color=(
            0, 0, 1, 1), content=content, size_hint=(.8, .4))
        popup.open()

    def register_user(self, username, password):

        try:

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
