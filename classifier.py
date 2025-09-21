import pickle
import numpy as np
from tensorflow.keras.models import load_model
from fastapi import HTTPException

def load_model_and_tokenizer(model_path: str, tokenizer_path: str):
    """
    Load the deep learning model and tokenizer from specified paths.
    
    Args:
        model_path (str): Path to the saved deep learning model file (.h5 or similar)
        tokenizer_path (str): Path to the saved tokenizer file (.pkl)
    
    Returns:
        tuple: Loaded model and tokenizer
    """
    try:
        # Load the deep learning model
        model = load_model(model_path)
        # Load the tokenizer
        with open(tokenizer_path, 'rb') as file:
            tokenizer = pickle.load(file)
        return model, tokenizer
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading model or tokenizer: {str(e)}")

def predict_text(text: str, model, tokenizer, max_length: int = 100):
    """
    Process input text and make predictions using the loaded model and tokenizer.
    
    Args:
        text (str): Input text to process
        model: Loaded deep learning model
        tokenizer: Loaded tokenizer
        max_length (int): Maximum sequence length for padding/truncation
    
    Returns:
        dict: Prediction results
    """
    try:
        # Tokenize and preprocess the input text
        sequences = tokenizer.texts_to_sequences([text])
        padded_sequences = np.array(tokenizer.sequences_to_matrix(sequences, mode='binary'))
        
        # Ensure input shape matches model expectations
        if padded_sequences.shape[1] > max_length:
            padded_sequences = padded_sequences[:, :max_length]
        elif padded_sequences.shape[1] < max_length:
            padding = np.zeros((1, max_length - padded_sequences.shape[1]))
            padded_sequences = np.hstack((padded_sequences, padding))
        
        # Make prediction
        prediction = model.predict(padded_sequences)
        
        # Convert prediction to readable format (example: assuming binary classification)
        result = {
            "input_text": text,
            "prediction": float(prediction[0][0]),  # Adjust based on model output
            "label": "positive" if prediction[0][0] > 0.5 else "negative"  # Adjust threshold as needed
        }
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during prediction: {str(e)}")
 