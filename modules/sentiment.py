import streamlit as st
import tensorflow as tf
from tensorflow.keras.models import load_model
import pickle
import numpy as np
from tensorflow.keras.preprocessing.sequence import pad_sequences

# Optimized model loader
@st.cache_resource
def load_sentiment_model():
    return tf.keras.models.load_model("Models/sentiment_model.keras")

# Optimized tokenizer loader
@st.cache_data
def load_tokenizer():
    with open('Models/tokenizer.pkl', 'rb') as handle:
        return pickle.load(handle)


def predict_sentiment(text, max_len=300):
    # Load resources inside function to benefit from Streamlit caching
    model = load_sentiment_model()
    tokenizer = load_tokenizer()
    
    # Preprocess the text
    text_seq = tokenizer.texts_to_sequences([text])
    padded_seq = pad_sequences(text_seq, maxlen=max_len)
    
    # Predict
    prediction = model.predict(padded_seq)
    sentiment = "Positive" if prediction[0][0] >= 0.5 else "Negative"
    
    return sentiment, prediction[0][0]  # probability

