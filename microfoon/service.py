import os
import shutil
import time
from pathlib import Path
from typing import List, Dict, Optional
from rich.console import Console

from microfoon.config import STORAGE_DIRECTORY
from microfoon.database import get_db, Recording, ProcessingStatus
from microfoon.audio import find_audio_files, copy_and_rename, compress_audio
from microfoon.intelligence import GeminiProcessor
from microfoon.exporter import ObsidianExporter

console = Console()

class MicrofoonService:
    _instance = None

    def __init__(self):
        # Singleton pattern to ensure only one service instance
        self.processor = GeminiProcessor()
        self.exporter = ObsidianExporter()
        self.current_drive: Optional[Path] = None
        self.found_files: List[Path] = []
        
        # Ensure storage exists
        if not STORAGE_DIRECTORY.exists():
            STORAGE_DIRECTORY.mkdir(parents=True)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_drive(self, drive_path: Path):
        self.current_drive = drive_path
        self.scan_files()

    def scan_files(self) -> List[Dict]:
        if not self.current_drive or not self.current_drive.exists():
            return []
        
        self.found_files = find_audio_files(self.current_drive)
        result = []
        for f in self.found_files:
            size_mb = f.stat().st_size / (1024 * 1024)
            result.append({
                "filename": f.name,
                "path": str(f),
                "size_mb": round(size_mb, 2)
            })
        return result

    def process_file(self, filename: str) -> Dict:
        """
        Full processing pipeline for a single file:
        Copy -> DB Record -> Transcribe -> Export -> Return Status
        """
        # Find the file object from our cached list
        file_path = next((f for f in self.found_files if f.name == filename), None)
        if not file_path:
             return {"status": "error", "message": "File not found in current session"}

        db_session = next(get_db())
        
        try:
             # 1. Copy
            console.log(f"Processing {filename}...")
            stored_path = copy_and_rename(file_path)

            # 2. DB Record
            recording = Recording(
                original_filename=file_path.name,
                stored_filename=stored_path.name,
                source_path=str(file_path),
                status=ProcessingStatus.PROCESSING
            )
            db_session.add(recording)
            db_session.commit()

            # 3. Transcribe
            result = self.processor.process_audio(stored_path)
            
            if result:
                recording.transcript = result.get("transcript")
                recording.summary = result.get("summary")
                recording.title = result.get("title")
                recording.status = ProcessingStatus.COMPLETED
                
                # 4. Export
                obsidian_path = self.exporter.export(recording)
                if obsidian_path:
                    recording.obsidian_path = str(obsidian_path)
                    recording.status = ProcessingStatus.EXPORTED
            else:
                 recording.status = ProcessingStatus.FAILED
                 recording.error_message = "Gemini processing returned no result"

            db_session.commit()
            
            return {
                "status": "success", 
                "title": recording.title, 
                "summary": recording.summary,
                "obsidian_path": recording.obsidian_path
            }

        except Exception as e:
            console.print(f"[bold red]Error[/bold red]: {e}")
            if 'recording' in locals():
                recording.status = ProcessingStatus.FAILED
                recording.error_message = str(e)
                db_session.commit()
            return {"status": "error", "message": str(e)}
        finally:
            db_session.close()

    def delete_original(self, filename: str) -> bool:
        file_path = next((f for f in self.found_files if f.name == filename), None)
        if file_path and file_path.exists():
            try:
                os.remove(file_path)
                return True
            except Exception as e:
                console.print(f"Error deleting {filename}: {e}")
                return False
        return False

    def get_processed_files(self) -> List[Dict]:
        # Return list of processed recordings from DB
        db_session = next(get_db())
        recordings = db_session.query(Recording).order_by(Recording.created_at.desc()).all()
        result = [{
            "id": r.id,
            "title": r.title or r.original_filename,
            "status": r.status.value,
            "date": r.created_at.strftime("%Y-%m-%d %H:%M"),
            "obsidian_path": r.obsidian_path
        } for r in recordings]
        db_session.close()
        return result
