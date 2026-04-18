
import os, io, re, html, yt_dlp
import xml.etree.ElementTree as ET

from urllib.request import urlopen
from youtube_transcript_api import YouTubeTranscriptApi

from PIL import Image
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QThread, pyqtSignal

class Format:
    def size(b):
        if not b: return '?'
        for u in ('B', 'KB', 'MB', 'GB'):
            if b < 1024: return f'{b:.0f} {u}'
            b /= 1024
        return f'{b:.1f} GB'

    def bitrate(bps):
        return '?' if not bps else f'{bps:.0f} kbps'

    def classify(formats):
        vo, ao, co, uc = [], [], [], []
        for f in formats:
            hv = f.get('vcodec','none') not in (None, 'none')
            ha = f.get('acodec','none') not in (None, 'none')
            if hv and ha: co.append(f)
            elif hv:      vo.append(f)
            elif ha:      ao.append(f)
            else:         uc.append(f)

        vo.sort(key=lambda f: (f.get('height') or 0, f.get('tbr') or 0), reverse=True)
        ao.sort(key=lambda f:  f.get('abr')    or    f.get('tbr') or 0,  reverse=True)
        co.sort(key=lambda f: (f.get('height') or 0, f.get('tbr') or 0), reverse=True)

        return vo, ao, co, uc

    def caption(xml_data):
        def timestamp(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int(round((seconds % 1) * 1000))
            
            return f'{h:02}:{m:02}:{s:02},{ms:03}'
        try:
            content = re.search(r'(<transcript>.*?</transcript>)', xml_data, re.DOTALL)
            if not content:
                return None
            
            root = ET.fromstring(content.group(1))
            if root.tag != 'transcript':
                return None

            srt = []
            for i, child in enumerate(root.findall('text'), start=1):
                start = float(child.attrib.get('start', 0))
                end = start + float(child.attrib.get('dur', 0))
                srt.append(f'{i}\n{timestamp(start)} --> {timestamp(end)}\n{html.unescape(child.text or '')}\n')
                
            return '\n'.join(srt)

        except Exception:
            return None

class FetchWorker(QThread):
    done    = pyqtSignal(dict)
    error   = pyqtSignal(str)
    status  = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.setObjectName('FetchWorker')
        self.url = url

    def run(self):
        try:
            self.status.emit(f'Connecting :: {self.url}')
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'skip_download': True}) as ydl:
                info = ydl.extract_info(self.url, download=False)

            self.status.emit('Parsing Formats...')
            self.done.emit(info)
        except Exception as e:
            self.error.emit(str(e))

class ThumbnailWorker(QThread):
    done  = pyqtSignal(QPixmap)
    error = pyqtSignal()

    def __init__(self, url):
        super().__init__()
        self.setObjectName('ThumbnailWorker')
        self.url = url

    def run(self):
        try:
            data = urlopen(self.url, timeout=8).read()

            img  = Image.open(io.BytesIO(data)).convert('RGB')
            img.thumbnail((300, 200), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, 'PNG')
            pix = QPixmap()
            pix.loadFromData(buf.getvalue())
            self.done.emit(pix)
            
        except Exception:
            self.error.emit()

class DownloadWorker(QThread):
    done     = pyqtSignal(str)
    error    = pyqtSignal(str)
    status   = pyqtSignal(str)
    progress = pyqtSignal(int, str)

    def __init__(self, url, fmt, path):
        super().__init__()
        self.setObjectName('DownloadWorker')
        self.url, self.fmt, self.out_path = url, fmt, path

    def _hook(self, d):
        if d['status'] == 'downloading':
            raw_msg = d.get('_default_template', '')

            clean_msg = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])').sub('', raw_msg)
            clean_msg = ''.join(filter(lambda x: x.isprintable(), clean_msg))
            clean_msg = clean_msg.encode('ascii', 'ignore').decode('ascii')
            clean_msg = clean_msg.strip().replace('of', '').replace('at', '')
            clean_msg = ' | '.join(part.strip() for part in re.split(r'\s{2,}|(?=ETA)', clean_msg) if part.strip())

            pct = (d.get('downloaded_bytes', 0) / (d.get('total_bytes') or d.get('total_bytes_estimate') or 1)) * 100

            self.progress.emit(int(pct), clean_msg)

        elif d['status'] == 'finished':
            if self.is_merge:
                if self.is_frist:
                    self.status.emit('Processing Overlay...')
                    self.is_frist = False
                else:
                    self.status.emit('Post-Processing...')
            else:
                self.status.emit('Post-Processing...')

    def run(self):
        try:
            os.makedirs(self.out_path, exist_ok=True)
            self.is_merge = '+' in self.fmt
            self.is_frist = True

            opts = {
                'format'           : self.fmt,
                'outtmpl'          : os.path.join(self.out_path, '%(title).100s (%(autonumber)s).%(ext)s'),
                'progress_hooks'   : [self._hook],
                'quiet'            : True,
                'no_warnings'      : True,
                'restrictfilenames': True,
                'windowsfilenames' : True,
                'nooverwrites'     : True,
            }

            if self.is_merge:
                opts['merge_output_format'] = 'mkv'
                opts['postprocessors'] = [
                    {'key': 'FFmpegVideoConvertor', 'preferedformat' : 'mkv'},
                    {'key': 'FFmpegMetadata'}
                ]
            else:
                opts['postprocessors'] = [{'key': 'FFmpegMetadata'}]

            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([self.url])

            self.done.emit(self.out_path)
        except Exception as e:
            self.error.emit(str(e))

class CaptionsSearchWorker(QThread):
    done  = pyqtSignal(list, list)
    error = pyqtSignal(str)

    def __init__(self, url: str):
        super().__init__()
        self.setObjectName('CaptionsSearchWorker')
        self.url = url

    def _extract_id(self):
        for part in self.url.split('v=')[1:]:
            vid = part.split('&')[0].strip()
            if vid: return vid
        for part in self.url.split('youtu.be/')[1:]:
            vid = part.split('?')[0].split('&')[0].strip()
            if vid: return vid
        return None

    def run(self):
        try:
            vid = self._extract_id()
            if not vid:
                self.error.emit('Failed To Extract Video ID')
                return

            api = YouTubeTranscriptApi()
            transcripts = api.list(vid)

            seen, captions, options = set(), [], []
            for group in [transcripts._manually_created_transcripts.items(), transcripts._generated_transcripts.items()]:
                for code, t in group:
                    if code not in seen:
                        seen.add(code)
                        captions.append({'name' : t.language, 'code' : t.language_code, 'auto' : t.is_generated})

            for option in transcripts._translation_languages:
                options.append({'name': option.language, 'code': option.language_code})

            self.done.emit(captions, options)
        except Exception as e:
            self.error.emit(str(e))

class CaptionExtracterWorker(QThread):
    done     = pyqtSignal(str, bool)
    error    = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, url: str, code: str, name: str, translate_to: str | None, path: str):
        super().__init__()
        self.setObjectName('CaptionDownloadWorker')
        self.url, self.code = url, code
        self.name, self.translate_to = name, translate_to
        self.path = path

    def _extract_id(self):
        for part in self.url.split('v=')[1:]:
            vid = part.split('&')[0].strip()
            if vid:
                return vid
        for part in self.url.split('youtu.be/')[1:]:
            vid = part.split('?')[0].split('&')[0].strip()
            if vid:
                return vid
        return None

    def run(self):
        try:
            vid = self._extract_id()
            if not vid:
                self.error.emit('Cannot extract video ID')
                return

            api = YouTubeTranscriptApi()
            self.progress.emit(f'Fetching Caption :: [{self.code.upper()}]')

            transcript_raw = api.fetch(vid, languages=[self.code]).to_raw_data()
            if self.translate_to:   # does not fetch, neither by requests (429 Client Error)
                self.progress.emit(f'Translating :: [{self.code.upper()}]  TO  [{self.translate_to.upper()}]')
                url = api.list(vid).find_generated_transcript([self.code]).translate(self.translate_to)._url
                self.done.emit(url, True)
            else:
                self.done.emit(self._to_srt(transcript_raw), False)

        except Exception as e:
            self.error.emit(str(e))

    @staticmethod
    def _to_srt(raw: list) -> str:
        def _t(s: float) -> str:
            ms = int((s - int(s)) * 1000)
            s  = int(s)
            return f'{s//3600:02}:{(s%3600)//60:02}:{s%60:02},{ms:03}'

        lines = []
        for i, item in enumerate(raw, 1):
            start = item['start']
            end   = start + item['duration']
            text  = item['text'].replace('\n', ' ')
            lines.append(f'{i}\n{_t(start)} --> {_t(end)}\n{text}\n')
        return '\n'.join(lines)
