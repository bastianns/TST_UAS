import os
import logging
from datetime import datetime
from moviepy.editor import VideoFileClip
from speech_recognition import Recognizer, AudioFile, UnknownValueError, RequestError
from textblob import TextBlob
import nltk

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def check_nltk_data():
    """Ensure required NLTK data is available."""
    try:
        required_data = ['punkt', 'averaged_perceptron_tagger']
        for data in required_data:
            try:
                nltk.data.find(f'tokenizers/{data}' if data == 'punkt' else data)
            except LookupError:
                nltk.download(data, quiet=True)
        return True
    except Exception as e:
        logging.error(f"NLTK data check failed: {str(e)}")
        return False

def extract_audio(video_path: str) -> str:
    """Extract audio from video file and save as WAV."""
    logging.info(f"Starting audio extraction for file: {video_path}")

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    audio_path = os.path.splitext(video_path)[0] + ".wav"
    try:
        clip = VideoFileClip(video_path)
        logging.info(f"Video duration: {clip.duration}")
        clip.audio.write_audiofile(audio_path, codec='pcm_s16le', fps=44100)
        logging.info(f"Audio extracted to: {audio_path}")
        clip.close()
        return audio_path
    except Exception as e:
        logging.error(f"Audio extraction failed: {str(e)}")
        raise RuntimeError(f"Audio extraction error: {str(e)}")

def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio to text using speech recognition."""
    recognizer = Recognizer()
    try:
        with AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            logging.info(f"Transcribed text: {text}")
            return text
    except UnknownValueError:
        logging.error("Speech recognition failed to understand audio")
        raise RuntimeError("Speech recognition could not understand the audio")
    except RequestError as e:
        logging.error(f"Speech recognition service error: {str(e)}")
        raise RuntimeError(f"Speech recognition service error: {str(e)}")
    except Exception as e:
        logging.error(f"Transcription error: {str(e)}")
        raise RuntimeError(f"Transcription failed: {str(e)}")

def analyze_profanity(text: str) -> dict:
    """Analyze profanity in text with enhanced detection."""
    profanity_words = {
        'high': ['fuck', 'motherfucker', 'shit', 'anjing', 'bangsat', 'kontol', 'memek'],
        'medium': ['damn', 'hell', 'ass', 'goblok', 'bego', 'tolol'],
        'low': ['stupid', 'idiot', 'dumb', 'bodoh']
    }
    
    results = {
        'contains_profanity': False,
        'profanity_level': 'none',
        'found_profanity': [],
        'profanity_count': 0
    }

    text_lower = text.lower()
    words = text_lower.split()
    
    for level, word_list in profanity_words.items():
        for word in word_list:
            count = words.count(word)
            if count > 0:
                results['contains_profanity'] = True
                results['found_profanity'].append({
                    'word': word,
                    'count': count,
                    'level': level
                })
                results['profanity_count'] += count

    if results['contains_profanity']:
        if any(p['level'] == 'high' for p in results['found_profanity']):
            results['profanity_level'] = 'high'
        elif any(p['level'] == 'medium' for p in results['found_profanity']):
            results['profanity_level'] = 'medium'
        else:
            results['profanity_level'] = 'low'

    return results

def analyze_sentiment_details(text: str) -> dict:
    """Perform detailed sentiment analysis with profanity detection."""
    if not check_nltk_data():
        return {"error": "NLTK data initialization failed"}

    try:
        blob = TextBlob(text)
        profanity_results = analyze_profanity(text)
        
        # Analyze each sentence
        sentence_analysis = []
        total_polarity = 0
        
        for sentence in blob.sentences:
            polarity = sentence.sentiment.polarity
            
            # Adjust polarity for profanity
            sentence_text = str(sentence).lower()
            contains_profanity = any(
                word['word'] in sentence_text
                for word in profanity_results['found_profanity']
            )
            
            if contains_profanity:
                polarity -= 0.3
            
            sentiment = "neutral"
            if polarity < -0.1:
                sentiment = "negative"
            elif polarity > 0.1:
                sentiment = "positive"
            
            total_polarity += polarity
            
            sentence_analysis.append({
                "text": str(sentence),
                "polarity": round(polarity, 2),
                "sentiment": sentiment,
                "contains_profanity": contains_profanity
            })
        
        overall_polarity = total_polarity / max(len(sentence_analysis), 1)
        
        # Determine final sentiment
        if profanity_results['profanity_level'] == 'high':
            overall_sentiment = "negative"
            reasoning = "High level of profanity detected"
            overall_polarity -= 0.5
        elif overall_polarity < -0.1:
            overall_sentiment = "negative"
            reasoning = "Overall negative tone detected"
        elif overall_polarity > 0.1:
            overall_sentiment = "positive"
            reasoning = "Overall positive tone detected"
        else:
            overall_sentiment = "neutral"
            reasoning = "Balanced or neutral tone detected"

        return {
            "sentiment": overall_sentiment,
            "overall_polarity": round(overall_polarity, 2),
            "reasoning": reasoning,
            "profanity_analysis": profanity_results,
            "detailed_results": {
                "transcribed_text": text,
                "sentence_analysis": sentence_analysis,
                "sentiment_distribution": {
                    "positive": sum(1 for s in sentence_analysis if s["sentiment"] == "positive"),
                    "neutral": sum(1 for s in sentence_analysis if s["sentiment"] == "neutral"),
                    "negative": sum(1 for s in sentence_analysis if s["sentiment"] == "negative")
                }
            },
            "analysis_timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logging.error(f"Sentiment analysis error: {str(e)}")
        return {
            "error": f"Sentiment analysis failed: {str(e)}",
            "sentiment": "unknown",
            "overall_polarity": 0
        }

def process_video_sentiment(video_path: str) -> tuple:
    """Process video for sentiment analysis with comprehensive results."""
    audio_path = None
    try:
        audio_path = extract_audio(video_path)
        text = transcribe_audio(audio_path)
        sentiment_results = analyze_sentiment_details(text)
        
        if "error" in sentiment_results:
            return False, sentiment_results
        
        logging.info("Sentiment analysis completed successfully")
        return True, sentiment_results
    
    except Exception as e:
        error_msg = f"Video processing failed: {str(e)}"
        logging.error(error_msg)
        return False, {"error": error_msg}
    
    finally:
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                logging.info(f"Temporary audio file removed: {audio_path}")
            except Exception as e:
                logging.warning(f"Failed to remove temporary audio file: {str(e)}")