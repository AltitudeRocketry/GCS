import os
import sys
import requests
from PyQt6.QtCore import QThread, pyqtSignal

class NewVersionDownloader(QThread):
    progress_changed  = pyqtSignal(int)
    status_changed     = pyqtSignal(str)
    download_finished = pyqtSignal(bool, str, str) #success, msg, file_path

    def __init__(self, github_owner, repo_name, exe_name):
        super().__init__()
        self.github_owner = github_owner
        self.repo_name = repo_name
        self.exe_name = exe_name

        self.downloadURL = f"https://github.com/{github_owner}/{repo_name}/releases/latest/download/{exe_name}"


    def run(self):
        try:
            self.status_changed.emit("Connecting to GitHub")
            # Determine directory where the running executable lives
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            target_path = os.path.join(base_dir, f"new_{self.exe_name}")

            response = requests.get(self.downloadURL, stream=True, timeout=20, allow_redirects=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(target_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            self.progress_changed.emit(percent)

            self.download_finished.emit(True, "Download completed!", target_path)


        except Exception as e:
            self.download_finished.emit(False, f"Download failed: {str(e)}", "")