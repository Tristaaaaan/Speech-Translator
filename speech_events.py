from android import mActivity, api_version
from android.runnable import run_on_ui_thread
from jnius import autoclass, cast, PythonJavaClass, java_method

String = autoclass('java.lang.String')
Toast = autoclass('android.widget.Toast')
Intent = autoclass('android.content.Intent')
Context = autoclass('android.content.Context')
ClipboardManager = autoclass('android.content.ClipboardManager')
ClipData = autoclass('android.content.ClipData')
SpeechRecognizer = autoclass('android.speech.SpeechRecognizer')
RecognizerIntent = autoclass('android.speech.RecognizerIntent')
# requires 'android.add_src = java' and the 'java/org/kivy.....' source code.
KivyRecognitionListener = autoclass('org.kivy.speech.KivyRecognitionListener')

class SpeechEvents:

    def __init__(self):
        self.speechRecognizer = None

    # create_recognizer() must be on Android main thread,
    # others are on the main thread to prevent any multi-threading issues
    @run_on_ui_thread
    def create_recognizer(self, recognizer_event_handler):
        self.speechRecognizer = \
            SpeechRecognizer.createSpeechRecognizer(mActivity)
        self.callback_wrapper = CallbackWrapper(recognizer_event_handler)
        self.speechRecognizer.setRecognitionListener(
            KivyRecognitionListener(self.callback_wrapper))  # Java

    @run_on_ui_thread
    def destroy_recognizer(self):
        if self.speechRecognizer:
            self.speechRecognizer.destroy()
            self.speechRecognizer = None

    @run_on_ui_thread
    def start_listening(self):
        if self.speechRecognizer:
            self.speechRecognizerIntent = Intent(
                RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
            self.speechRecognizerIntent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            self.speechRecognizerIntent.putExtra(
                RecognizerIntent.EXTRA_PARTIAL_RESULTS, True)
            self.speechRecognizer.startListening(self.speechRecognizerIntent)

    @run_on_ui_thread
    def stop_listening(self):
        if self.speechRecognizer:
            self.speechRecognizer.stopListening()

    # This is not related to speech.
    # It is here to keep all the Android api calls in one place.
    def share_text_with_clipboard(self, text):
        clipboard = cast(ClipboardManager,
                         mActivity.getSystemService(Context.CLIPBOARD_SERVICE))
        clip = ClipData.newPlainText('speech text', text)
        clipboard.setPrimaryClip(clip)
        if api_version < 33: 
            self.make_toast()

    # Toast requires that it is on the Android main thread.
    @run_on_ui_thread  
    def make_toast(self):
        Toast.makeText(mActivity, String('Copied to Clipboard.'),
                       Toast.LENGTH_LONG).show()     


class CallbackWrapper(PythonJavaClass):
    __javacontext__ = 'app'
    __javainterfaces__ = ['org/kivy/speech/CallbackWrapper']

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    @java_method('(Ljava/lang/String;Ljava/lang/String;)V')        
    def callback_data(self, key, value):
        if self.callback:
            self.callback(key, value)

