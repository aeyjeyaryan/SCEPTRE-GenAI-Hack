import os
import logging
import tempfile
import asyncio
from typing import Optional
import google.generativeai as genai
from fastapi import UploadFile, HTTPException
import cv2
import speech_recognition as sr
from pydub import AudioSegment
from moviepy import VideoFileClip
import requests
from bs4 import BeautifulSoup
from search_utils import fetch_document_content

# Configure logging
logger = logging.getLogger(__name__)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY environment variable")
genai.configure(api_key=GEMINI_API_KEY)

class ContentProcessor:
    """Handles processing of different content types: images, videos, and URLs."""
    
    def __init__(self):
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        self.recognizer = sr.Recognizer()
        
    async def process_image(self, image_file: UploadFile) -> str:
        """Process uploaded image and extract text description using Gemini Vision."""
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                content = await image_file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                # Use Gemini to analyze the image
                with open(temp_file_path, 'rb') as img_file:
                    image_data = img_file.read()
                
                prompt = """
                Analyze this image carefully and provide a detailed description of what you see. 
                Focus on:
                1. Any text content in the image
                2. Visual elements that might be relevant for fact-checking
                3. Context that could help determine if this might be misinformation
                4. Any claims, statistics, or statements visible in the image
                
                Provide a comprehensive description that would help verify the accuracy of the content.
                """
                
                # Create image part for Gemini
                image_part = {
                    "mime_type": image_file.content_type,
                    "data": image_data
                }
                
                response = await asyncio.to_thread(
                    self.gemini_model.generate_content,
                    [prompt, image_part]
                )
                
                return response.text if response.text else "Unable to analyze image content"
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")
    
    async def process_video(self, video_file: UploadFile) -> str:
        """Process uploaded video, extract audio, transcribe, and summarize."""
        try:
            # Save uploaded video file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
                content = await video_file.read()
                temp_video.write(content)
                temp_video_path = temp_video.name
            
            try:
                # Extract audio from video
                audio_path = await self._extract_audio_from_video(temp_video_path)
                
                # Transcribe audio to text
                transcription = await self._transcribe_audio(audio_path)
                
                if not transcription:
                    return "Unable to extract meaningful content from video"
                
                # Summarize the transcription using Gemini
                summary = await self._summarize_transcription(transcription)
                
                return summary
                
            finally:
                # Clean up temporary files
                os.unlink(temp_video_path)
                if 'audio_path' in locals():
                    try:
                        os.unlink(audio_path)
                    except:
                        pass
                        
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            raise HTTPException(status_code=500, detail=f"Video processing failed: {str(e)}")
    
    async def process_url(self, url: str) -> str:
        """Process URL and extract meaningful content."""
        try:
            # Fetch content from URL
            content = await fetch_document_content(url)
            
            if not content:
                # Fallback: try basic web scraping
                content = await self._basic_url_scraping(url)
            
            if not content:
                raise HTTPException(status_code=400, detail="Unable to fetch content from URL")
            
            # Summarize the content using Gemini
            summary = await self._summarize_web_content(content, url)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            raise HTTPException(status_code=500, detail=f"URL processing failed: {str(e)}")
    
    async def _extract_audio_from_video(self, video_path: str) -> str:
        """Extract audio from video file."""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
                audio_path = temp_audio.name
            
            # Use moviepy to extract audio
            video_clip = VideoFileClip(video_path)
            audio_clip = video_clip.audio
            audio_clip.write_audiofile(audio_path, logger=None)
            audio_clip.close()
            video_clip.close()
            
            return audio_path
            
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            raise Exception(f"Audio extraction failed: {str(e)}")
    
    async def _transcribe_audio(self, audio_path: str) -> Optional[str]:
        """Transcribe audio file to text using speech recognition."""
        try:
            # Convert to wav format if needed
            audio = AudioSegment.from_file(audio_path)
            wav_path = audio_path.replace('.wav', '_converted.wav')
            audio.export(wav_path, format="wav")
            
            # Transcribe using speech recognition
            with sr.AudioFile(wav_path) as source:
                audio_data = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio_data)
                
            # Clean up converted file
            try:
                os.unlink(wav_path)
            except:
                pass
                
            return text
            
        except sr.UnknownValueError:
            logger.warning("Speech recognition could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Could not request results from speech recognition service: {e}")
            return None
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None
    
    async def _summarize_transcription(self, transcription: str) -> str:
        """Summarize video transcription using Gemini."""
        try:
            prompt = f"""
            Analyze the following video transcription for potential misinformation or claims that need fact-checking:
            
            Transcription: {transcription}
            
            Please provide:
            1. Key claims or statements made in the video
            2. Any factual assertions that can be verified
            3. Context that might help determine credibility
            4. A summary of the main message
            
            Focus on extracting information that would be useful for fact-checking purposes.
            """
            
            response = await asyncio.to_thread(self.gemini_model.generate_content, prompt)
            return response.text if response.text else transcription
            
        except Exception as e:
            logger.error(f"Error summarizing transcription: {e}")
            return transcription
    
    async def _basic_url_scraping(self, url: str) -> str:
        """Basic web scraping as fallback method."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text[:5000]  # Limit content length
            
        except Exception as e:
            logger.error(f"Error in basic URL scraping: {e}")
            return ""
    
    async def _summarize_web_content(self, content: str, url: str) -> str:
        """Summarize web content using Gemini."""
        try:
            prompt = f"""
            Analyze the following web content from {url} for potential misinformation or claims that need fact-checking:
            
            Content: {content[:3000]}
            
            Please provide:
            1. Main claims or statements in the content
            2. Any factual assertions that can be verified
            3. Source credibility indicators
            4. A summary of key information
            
            Focus on extracting information relevant for fact-checking and misinformation detection.
            """
            
            response = await asyncio.to_thread(self.gemini_model.generate_content, prompt)
            return response.text if response.text else content[:1000]
            
        except Exception as e:
            logger.error(f"Error summarizing web content: {e}")
            return content[:1000]