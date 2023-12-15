package org.kivy.speech;

import java.util.ArrayList;
import java.util.Base64;
import android.os.Bundle;
import android.speech.RecognitionListener;
import android.speech.SpeechRecognizer;
import org.kivy.speech.CallbackWrapper;


public class KivyRecognitionListener implements RecognitionListener {

    private CallbackWrapper callback_wrapper;

    public KivyRecognitionListener(CallbackWrapper callback_wrapper) {	
	this.callback_wrapper = callback_wrapper;
    }       
    
    @Override
    public void onReadyForSpeech(Bundle bundle) {
	this.callback_wrapper.callback_data("onReadyForSpeech",""); 
    }

    @Override
    public void onBeginningOfSpeech() {
	this.callback_wrapper.callback_data("onBeginningOfSpeech",""); 
    }

    @Override
    public void onRmsChanged(float v) {
	this.callback_wrapper.callback_data("onRmsChanged",String.valueOf(v)); 
    }

    @Override
    public void onBufferReceived(byte[] bytes) {
	String s = Base64.getEncoder().encodeToString(bytes);
	this.callback_wrapper.callback_data("onBufferReceived", s); 
    }

    @Override
    public void onEndOfSpeech() {
	this.callback_wrapper.callback_data("onEndOfSpeech",""); 
    }

    @Override
    public void onError(int i) {
	String s;
	if (i == 1) {
	    s = "Speech not recognized.";
	} else if (i == 2) {
	    s = "Client error.";
	} else if (i == 3) {
	    s = "Server error.";
	} else if (i == 4) {
	    s = "Network error.";
	} else if (i == 5) {
	    s = "Audio error.";
	} else {
	    s = "Unknown error.";
	}
	this.callback_wrapper.callback_data("onError", s); 
    }

    @Override
    public void onResults(Bundle bundle) {
	ArrayList<String> data = bundle.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
	this.callback_wrapper.callback_data("onResults",data.get(0)); 
    }

    @Override
    public void onPartialResults(Bundle bundle) {
	ArrayList<String> data = bundle.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
	this.callback_wrapper.callback_data("onPartialResults",data.get(0)); 
    }

    @Override
    public void onEvent(int i, Bundle bundle) {
	this.callback_wrapper.callback_data("onEvent",""); 
    }
}
