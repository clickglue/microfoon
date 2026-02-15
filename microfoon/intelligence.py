import json
import time
import google.generativeai as genai
from rich.console import Console

from microfoon.config import GEMINI_API_KEY, PROMPT_SUMMARY, PROMPT_TITLE

console = Console()

class GeminiProcessor:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in environment variables.")
        genai.configure(api_key=GEMINI_API_KEY)
        # using flash for speed and cost, supports audio input
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def process_audio(self, audio_path):
        """
        Uploads audio to Gemini and requests transcription, summary, and title in JSON format.
        """
        console.log(f"Uploading {audio_path} to Gemini...")
        try:
            audio_file = genai.upload_file(path=audio_path)
            
            # Wait for processing state to be ACTIVE
            while audio_file.state.name == "PROCESSING":
                time.sleep(2)
                audio_file = genai.get_file(audio_file.name)

            if audio_file.state.name == "FAILED":
                raise Exception("Audio file processing failed by Gemini.")

            console.log("Audio uploaded. Generating content...")
            
            prompt = f"""
            Please process the attached audio file.
            1. Transcribe the audio verbatim. Detect the language (English or Dutch) automatically.
            2. {PROMPT_SUMMARY}
            3. {PROMPT_TITLE}

            Output the result strictly in JSON format with the following keys:
            - "transcript": The full transcription text.
            - "summary": The summary text.
            - "title": The generated title.
            - "language": The detected language code (e.g., "en", "nl").
            """

            response = self.model.generate_content(
                [audio_file, prompt],
                generation_config={"response_mime_type": "application/json"}
            )
            
            # Cleanup remote file
            # genai.delete_file(audio_file.name) # clean up if needed, but maybe keep for a bit?
            # actually better to clean up to avoid cluttering the account storage
            try:
                genai.delete_file(audio_file.name)
            except:
                pass

            return json.loads(response.text)

        except Exception as e:
            console.log(f"[bold red]Gemini processing failed:[/bold red] {e}")
            return None
