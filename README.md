## SCEPTRE – Smart Cognitive Engine for Preventing Tricks, Rumors & Errors

SCEPTRE is a platform designed to help users detect, analyze, and cross-verify potential misinformation across text, images, videos, and URLs.  
It leverages deep learning (TensorFlow), Google Cloud Platform, Programmable Search Engine, and Google Gemini to provide real-time fact-checking and credibility assessment.

## RUN SCEPTRE

1. git clone <repo-url>  

2. cd backend  

3. pip install -r requirements.txt  

4. Create a `.env` file inside `backend/` and add:  

GOOGLE_API_KEY=
GOOGLE_CSE_ID=
GEMINI_API_KEY=
JWT_SECRET_KEY=
MONGO_URI=



HOST=0.0.0.0
PORT=8000
DEBUG=false

MODEL_PATH=
TOKENIZER_PATH=


5. Run backend server:  

Backend runs at: http://127.0.0.1:8000  

6. cd frontend  

7. npm install  

8. npm run dev  

Frontend runs at: http://localhost:5173  

##

![alt text](image.png)

![alt text](image-1.png)

