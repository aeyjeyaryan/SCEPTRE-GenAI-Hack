from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.sequence import pad_sequences
import pickle

# Load model
model = tf.keras.models.load_model('isot_lstm_model.h5')
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
print("Model loaded from isot_lstm_model.h5")

# Load tokenizer
with open('tokenizer.pkl', 'rb') as handle:
    tokenizer = pickle.load(handle)
print("Tokenizer loaded from tokenizer.pkl")

# FastAPI app
app = FastAPI(title="Fake News Detector API")

# Request body
class TextInput(BaseModel):
    text: str

@app.post("/predict")
def predict(input_data: TextInput):
    max_len = 500  # same as training
    sequences = tokenizer.texts_to_sequences([input_data.text])
    padded_sequences = pad_sequences(sequences, maxlen=max_len, padding='post', truncating='post')

    prediction = model.predict(padded_sequences)
    prob = float(prediction[0][0])
    label = "True News" if prob > 0.5 else "Fake News"

    return {
        "text": input_data.text,
        "probability_true_news": prob,
        "predicted_label": label
    }
