import os
import time
from pathlib import Path
import requests


class OCRUtility:
    def __init__(self, host='http://localhost', port=5050, workers=6):
        self.host = host
        self.port = port
        self.workers = workers
        self.started = False

    @property
    def url(self):
        return f'{self.host}:{self.port}'

    @property
    def is_running(self):
        try:
            requests.get(self.url)
            return True
        except requests.exceptions.ConnectionError:
            return False

    def start(self, workers):
        if self.is_running:
            print('OCR server already running.')
        else:
            workers_arg = '' if workers <= 1 else f' -e DOCTOR_WORKERS={workers} '
            cmd = f'docker run -d -p {self.port}:5050 {workers_arg} freelawproject/doctor:latest'
            print(f'Starting OCR server with command: {cmd}')
            os.system(cmd)
            while not self.is_running:
                print('Waiting for service to start...')
                time.sleep(5)
            print(f'OCR server running at {self.url}')
        self.started = True

    def extract_text(self, pdf_path, ocr_available=True):
        if not self.started:
            self.start(self.workers)
        pdf_path = Path(pdf_path)
        url = self.url + '/extract/doc/text/'
        if ocr_available:
            url += '?ocr_available=True'
        return requests.post(
            url, files={'file': (pdf_path.name, pdf_path.read_bytes())},
        ).json()
