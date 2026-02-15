import os
import shutil
from pathlib import Path
from pydub import AudioSegment
from rich.console import Console

from microfoon.main import process_usb_drive
from microfoon.database import init_db
from microfoon.config import STORAGE_DIRECTORY

console = Console()

def create_dummy_audio(path: Path):
    """Creates a 1-second silent MP3 file."""
    try:
        # Create 1 sec of silence
        silence = AudioSegment.silent(duration=1000) 
        silence.export(path, format="mp3")
        console.log(f"[green]Created dummy audio:[/green] {path}")
        return True
    except Exception as e:
        console.log(f"[red]Failed to create dummy audio (ffmpeg missing?):[/red] {e}")
        return False

def verify():
    # Setup
    test_usb_dir = Path("./test_usb_drive")
    if test_usb_dir.exists():
        shutil.rmtree(test_usb_dir)
    test_usb_dir.mkdir()
    
    test_file = test_usb_dir / "test_recording.mp3"
    
    # Initialize DB
    init_db()
    
    # Create Audio
    if not create_dummy_audio(test_file):
        console.log("[bold red]Skipping verification due to missing audio dependencies.[/bold red]")
        return

    # Run Pipeline (User interaction will be simulated or skipped if logic allows)
    # The main logic uses Confirm.ask which blocks. 
    # For verification, we might need to mock Confirm or just manually run parts of logic.
    
    console.log("[blue]Starting partial verification (skipping interactive parts)...[/blue]")
    
    # Verify file finding
    from microfoon.audio import find_audio_files
    files = find_audio_files(test_usb_dir)
    assert len(files) == 1
    console.log("[green]File detection passed.[/green]")
    
    # Verify processing (copy/rename)
    from microfoon.audio import copy_and_rename
    stored_path = copy_and_rename(files[0])
    assert stored_path.exists()
    assert stored_path.parent == STORAGE_DIRECTORY
    console.log("[green]Copy and Rename passed.[/green]")
    
    # Verify compression
    from microfoon.audio import compress_audio
    compressed = compress_audio(stored_path)
    if compressed and compressed.exists():
        console.log("[green]Compression passed.[/green]")
    else:
        console.log("[red]Compression failed.[/red]")

    # Cleanup
    if test_usb_dir.exists():
        shutil.rmtree(test_usb_dir)
    console.log("[bold green]Verification Complete![/bold green]")

if __name__ == "__main__":
    verify()
