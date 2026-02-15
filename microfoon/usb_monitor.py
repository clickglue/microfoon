import time
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rich.console import Console

from microfoon.config import WATCH_DIRECTORY, TARGET_VOLUME_NAME

console = Console()

class USBEventHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback

    def on_any_event(self, event):
        # verbose logging is good but maybe too noisy now? let's keep it for now as per previous debug step
        console.log(f"[dim]Event: {event.event_type} - {event.src_path}[/dim]")

    def on_created(self, event):
        if event.is_directory:
            path = Path(event.src_path)
            console.log(f"Directory created: {path}")
            
            # Check for target volume name
            if path.name != TARGET_VOLUME_NAME:
                console.log(f"[dim]Ignoring {path}: Name '{path.name}' does not match target '{TARGET_VOLUME_NAME}'[/dim]")
                return

            # macOS /Volumes often has hidden directories or system directories
            if path.parent == WATCH_DIRECTORY and not path.name.startswith("."):
                console.log(f"[bold green]New volume detected:[/bold green] {path}")
                # Give the OS a moment to mount and make files available
                time.sleep(2) 
                self.callback(path)
            else:
                console.log(f"[dim]Ignoring {path}: Parent={path.parent} (Expected {WATCH_DIRECTORY}), Name={path.name}[/dim]")

class USBMonitor:
    def __init__(self, callback):
        self.callback = callback
        self.observer = Observer()
        self.handler = USBEventHandler(self.callback)

    def start(self):
        console.log(f"Starting USB Monitor on {WATCH_DIRECTORY}...")
        try:
            self.observer.schedule(self.handler, str(WATCH_DIRECTORY), recursive=False)
            self.observer.start()
        except Exception as e:
            console.log(f"[bold red]Error starting observer:[/bold red] {e}")

    def stop(self):
        self.observer.stop()
        self.observer.join()

if __name__ == "__main__":
    # Test stub
    def mock_callback(path):
        console.log(f"Processing path: {path}")

    monitor = USBMonitor(mock_callback)
    monitor.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.stop()
