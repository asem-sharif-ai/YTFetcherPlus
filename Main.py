import sys, os, re, json

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel,
    QGridLayout, QVBoxLayout, QHBoxLayout, QFileDialog,
    QTabWidget, QLineEdit, QTextBrowser, QProgressBar,
    QAbstractItemView, QSizePolicy
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices

from Workers import (
    FetchWorker, ThumbnailWorker, DownloadWorker,
    CaptionsSearchWorker, CaptionExtracterWorker,
    Format
)
from Widgets import Label, Button, Dot, Card, Tree
from About import show_about

def QSS():
    with open('Style.qss', 'r') as file:
        return file.read()

class App(QMainWindow):
    def __init__(self, load: str = ''):
        super().__init__()
        self.setWindowTitle('YTFetcherPlus')
        self.setStyleSheet(QSS())

        self.setup()
        self.build()

        if load:
            self.url_input.setText(load)
            self._fetch()

        self.setMinimumSize(800, 200)
        self.show()

    def setup(self):
        self._info         = None
        self._f_worker     = None      # FetchWorker
        self._d_worker     = None      # DownloadWorker
        self._cf_worker    = None      # CaptionsWorker
        self._ce_worker    = None      # CaptionDownloadWorker
        self._selected     = []
        self._pixmap       = None
        self._captions     = []        # [{name, code, auto}]
        self._translate_to = None      # selected translate target code

        self.cfg_path, T = 'CFG.json', {'PATH': str(os.path.expanduser('~/Downloads/YTFetcherPlus')), 'HISTORY': []}

        if not os.path.exists(self.cfg_path):
            with open(self.cfg_path, 'w', encoding='utf-8') as file:
                json.dump(T, file, ensure_ascii=False, indent=4)
        else:
            with open(self.cfg_path, 'r+', encoding='utf-8') as file:
                try:
                    if os.path.getsize(self.cfg_path) == 0:
                        raise ValueError('Empty File')
                    
                    data = json.load(file)
                    if not (isinstance(data.get('PATH'), str) and isinstance(data.get('HISTORY'), list)):
                        raise ValueError('Invalid Structure')
                        
                except (json.JSONDecodeError, ValueError):
                    file.seek(0)
                    json.dump(T, file, ensure_ascii=False, indent=4)
                    file.truncate()

        with open(self.cfg_path, 'r') as file:
            self.cfg = json.load(file)

        self.download_path = self.cfg['PATH']

    def build(self):
        self.setCentralWidget(QWidget())
        self.grid = QGridLayout(self.centralWidget())
        self.grid.setContentsMargins(20, 20, 20, 20)
        self.grid.setSpacing(10)
        self.grid.setRowStretch(3, 2)

        self._build_header()
        self._build_panel()
        self._build_trees()
        self._build_footer()

    def _build_header(self):
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(10)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        grid.setColumnStretch(0, 14)
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(2, 1)
        grid.setColumnStretch(3, 1)
        grid.setColumnStretch(4, 2)

        logo = QLabel('  𝖄𝕿 𝕱𝖊𝖙𝖈𝖍𝖊𝖗 𝕻𝖑𝖚𝖘')
        logo.setObjectName('LogoLabel')

        about_btn = Button('ABOUT', 'AboutButton', lambda: show_about())
        about_btn.setMinimumWidth(100)

        self.url_input = QLineEdit()
        self.url_input.setObjectName('InputLine')
        self.url_input.setPlaceholderText('Paste Website Video URL (YouTube, Facebook, Instagram, X (Twitter), etc...)')
        self.url_input.returnPressed.connect(self._main_action)

        self.set_btn   = Button('SET DIRECTORY', 'DirButton', self._set_dir)
        self.open_btn  = Button('OPEN', 'DirButton', self._open_dir)
        self.sub_btn = Button('PASTE', 'SubButton', self._sub_action)
        self.main_btn = Button('FETCH', 'MainButton', self._main_action)

        grid.addWidget(logo, 0, 0)
        grid.addWidget(about_btn, 0, 0, alignment=Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self.url_input, 1, 0)

        grid.addWidget(self.set_btn, 0, 1, 1, 3)
        grid.addWidget(self.open_btn, 0, 4)
        grid.addWidget(self.sub_btn, 1, 1)
        grid.addWidget(self.main_btn, 1, 2, 1, 3)

        self.grid.addLayout(grid, 0, 0)

    def _build_panel(self):
        self.info_panel = QFrame()
        self.info_panel.setObjectName('Panel')
        self.info_panel.setVisible(False)

        grid = QGridLayout(self.info_panel)
        grid.setContentsMargins(15, 15, 15, 15)
        grid.setSpacing(15)
        grid.setRowStretch(0, 1)
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 4)
        grid.setColumnStretch(2, 2)

        self.thumbnail = Label(on_click=self._save_thumbnail, text='⟳')
        self.thumbnail.setObjectName('Thumbnail')
        self.thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.thumbnail.setMinimumSize(220, 130)
        self.thumbnail.setMaximumSize(300, 180)
        self.thumbnail.setToolTip('Save Thumbnail')

        title_vbox = QVBoxLayout()
        title_vbox.setContentsMargins(0, 0, 0, 0)
        title_vbox.setSpacing(20)

        self.title_lbl = Label('—', on_press=self._copy_title)
        self.title_lbl.setObjectName('TitleLabel')
        self.title_lbl.setWordWrap(True)
        self.title_lbl.setToolTip('Copy Title')

        self.desc_lbl = Label('—', on_press=self._copy_desc)
        self.desc_lbl.setObjectName('MetaLabel')
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setMaximumHeight(180)
        self.desc_lbl.setToolTip('Copy Description')

        title_vbox.addWidget(self.title_lbl)
        title_vbox.addWidget(self.desc_lbl)
        title_vbox.addStretch()

        cards_grid = QGridLayout()
        cards_grid.setSpacing(10)
        self.cards = {
          'Published By': Card('Published By'),
          'Published On': Card('Published On'),
          'Views':        Card('Views'),
          'Likes':        Card('Likes'),
          'Duration':     Card('Duration'),
          'Formats':      Card('Formats'),
        }
        for i, w in enumerate(self.cards.values()):
            cards_grid.addWidget(w, i // 2, i % 2)

        grid.addWidget(self.thumbnail, 0, 0)
        grid.addLayout(title_vbox, 0, 1)
        grid.addLayout(cards_grid, 0, 2)

        self.grid.addWidget(self.info_panel, 2, 0)

    def _build_trees(self):
        self.trees_panel = QWidget()
        self.trees_panel.setVisible(False)

        layout = QVBoxLayout(self.trees_panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tabs.currentChanged.connect(self._tab_change)

        self.guide_lbl = QLabel('')
        self.guide_lbl.setObjectName('MetaLabel')
        self.guide_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.guide_lbl.setContentsMargins(0, 0, 20, 8)
        self.tabs.setCornerWidget(self.guide_lbl, Qt.Corner.TopRightCorner)

        tab_1 = QWidget()
        box_1 = QHBoxLayout(tab_1)
        box_1.setContentsMargins(10, 10, 10, 10)
        box_1.setSpacing(10)

        self.video_tree = Tree('Video', ['EXTENSION', 'RESOLUTION', 'FPS', 'CODEC', 'BITRATE', 'SIZE'])
        self.video_tree.itemSelectionChanged.connect(self._select_separated)

        self.audio_tree = Tree('Audio', ['EXTENSION', 'SAMPLE RATE', 'CH', 'CODEC', 'BITRATE', 'SIZE'])
        self.audio_tree.itemSelectionChanged.connect(self._select_separated)

        box_1.addWidget(self.video_tree, 1)
        box_1.addWidget(self.audio_tree, 1)


        tab_2 = QWidget()
        box_2 = QVBoxLayout(tab_2)
        box_2.setContentsMargins(10, 10, 10, 10)
        self.combined_tree = Tree('Combined', ['EXTENSION', 'RESOLUTION', 'VCODEC', 'ACODEC', 'BITRATE', 'SIZE'])
        self.combined_tree.itemSelectionChanged.connect(lambda: self._select_combined())
        box_2.addWidget(self.combined_tree)


        tab_3 = QWidget()
        box_3 = QVBoxLayout(tab_3)
        box_3.setContentsMargins(10, 10, 10, 10)
        self.unclassified_tree = Tree('UnClassified', [])
        self.unclassified_tree.itemSelectionChanged.connect(lambda: self._select_unclassified())
        box_3.addWidget(self.unclassified_tree)


        tab_4 = QWidget()
        box_4 = QHBoxLayout(tab_4)
        box_4.setContentsMargins(10, 10, 10, 10)
        box_4.setSpacing(10)

        self.captions_tree = Tree('Captions', ['LANGUAGE'])
        self.captions_tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.captions_tree.itemSelectionChanged.connect(self._preview_caption)

        self.translate_tree = Tree('Captions', ['TRANSLATE TO'])
        self.translate_tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.translate_tree.itemSelectionChanged.connect(self._translate_caption)
        self.translate_tree.setEnabled(False)

        box_4_sub = QGridLayout()
        box_4_sub.setSpacing(10)

        box_4_sub.setRowStretch(0, 1)
        box_4_sub.setRowStretch(1, 0)
        box_4_sub.setColumnStretch(0, 1)
        box_4_sub.setColumnStretch(1, 1)

        self.preview_box = QTextBrowser()
        self.preview_box.setReadOnly(True)

        self.paste_caption_btn = Button('PASTE', 'MainButton', self._paste_caption)
        self.paste_caption_btn.setVisible(False)

        self.cancel_caption_btn = Button('CANCEL', 'SubButton', self._cancel_caption)
        self.cancel_caption_btn.setVisible(False)

        box_4_sub.addWidget(self.preview_box, 0, 0, 1, 2)
        box_4_sub.addWidget(self.paste_caption_btn, 1, 0)
        box_4_sub.addWidget(self.cancel_caption_btn, 1, 1)

        box_4.addWidget(self.captions_tree)
        box_4.addWidget(self.translate_tree)
        box_4.addLayout(box_4_sub)

        self.tabs.addTab(tab_1, '   Separated Streams   ')
        self.tabs.addTab(tab_2, '   Combined Streams   ')
        self.tabs.addTab(tab_3, '   UnClassified   ')
        self.tabs.addTab(tab_4, '   Captions   ')
        self.tabs.setTabEnabled(3, False)

        layout.addWidget(self.tabs)
        self.grid.addWidget(self.trees_panel, 3, 0)

    def _build_footer(self):
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.setValue(0)

        self.status_bar = QFrame()
        self.status_bar.setObjectName('StatusBar')
        self.status_bar.setFixedHeight(35)

        layout = QHBoxLayout(self.status_bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.dot = Dot()
        self.status_lbl = QLabel('Ready :: Paste A URL')
        self.status_lbl.setObjectName('StatusLabel')

        credit_lbl = QLabel('YTFetcherPlus | V 3.1.1')
        credit_lbl.setObjectName('StatusLabel')

        layout.addWidget(self.dot)
        layout.addWidget(self.status_lbl)
        layout.addStretch()
        layout.addWidget(credit_lbl)

        self.grid.addWidget(self.progress, 4, 0)
        self.grid.addWidget(self.status_bar, 5, 0)

    def _enable_all(self, enabled=False):
        for w in (self.url_input, self.set_btn, self.open_btn, self.sub_btn, self.main_btn):
            w.setEnabled(enabled)

    def _set_idle(self):
        self._enable_all(True)
        self.url_input.clear()
        self.sub_btn.setText('PASTE')
        self.main_btn.setText('FETCH')
        self.progress.setValue(0)

        self.setup()

        self.info_panel.deleteLater()
        self.trees_panel.deleteLater()

        self._build_panel()
        self._build_trees()

        self.main_btn.setEnabled(True)

    def _set_ready(self):
        self.url_input.setEnabled(False)
        self.sub_btn.setText('CANCEL')
        self.main_btn.setText('DOWNLOAD')

        for btn in [self.sub_btn, self.set_btn, self.open_btn]:
            btn.setEnabled(True)

    def _set_status(self, msg, busy=False, ok=None, saved_path=None):
        if saved_path:
            lbl = Label(msg[:150],
                on_press=lambda p=saved_path: QDesktopServices.openUrl(QUrl.fromLocalFile(p))
            )

            self.status_bar.layout().replaceWidget(self.status_lbl, lbl)
            self.status_lbl.deleteLater()
            self.status_lbl = lbl
        else:
            if isinstance(self.status_lbl, Label):
                lbl = QLabel(msg[:150])
                lbl.setObjectName('StatusLabel')

                self.status_bar.layout().replaceWidget(self.status_lbl, lbl)
                self.status_lbl.deleteLater()
                self.status_lbl = lbl
            else:
                self.status_lbl.setText(msg)

        if busy:
            self.dot.start()
        elif ok is not None:
            self.dot.stop(ok)

    def _set_dir(self):
        if (dp:= QFileDialog.getExistingDirectory(self, 'Select Download Folder', self.download_path)):
            self.cfg['PATH'] = dp
            self.download_path = dp

            with open(self.cfg_path, 'w', encoding='utf-8') as file:
                json.dump(self.cfg, file, ensure_ascii=False, indent=4)

    def _open_dir(self):
        os.makedirs(self.download_path, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.download_path))

    def _main_action(self):
        if self.main_btn.text() == 'DOWNLOAD':
            self._download()
        else:
            self._fetch()

    def _sub_action(self):
        if self.sub_btn.text() == 'PASTE':
            self.url_input.setText(QApplication.clipboard().text())
        else:
            for worker in (self._f_worker, self._d_worker, self._cf_worker, self._ce_worker):
                if worker and worker.isRunning():
                    worker.terminate()
                    worker.wait()

            self._set_idle()
            self._set_status('Cancelled :: Waiting For Next URL', ok=False)

    def _fetch(self):
        url = self.url_input.text().strip().split('&')[0]
        if url:
            self._enable_all(False)
            self.info_panel.setVisible(False)
            self.trees_panel.setVisible(False)
            self.progress.setValue(0)
            self._set_status(f'Fetching URL :: {url}', busy=True)

            self._f_worker = FetchWorker(url)
            self._f_worker.done.connect(self._fetch_result)
            self._f_worker.error.connect(self._fetch_error)
            self._f_worker.status.connect(lambda m: self._set_status(m, busy=True))
            self._f_worker.start()

    def _fetch_error(self, msg):
        self._set_idle()
        self._set_status(f'Fetch Error: {msg}', ok=False)

    def _fetch_result(self, info: dict):
        self.showMaximized()

        self._info = info
        self._set_ready()
        self._set_status('Loaded :: Select Stream To Download', ok=True)

        title = info.get('title', 'Unknown')
        self.title_lbl.setText(title[:90] + ('...' if len(title) > 90 else ''))

        desc = (info.get('description') or '').replace('\n', ' ')[:180]
        self.desc_lbl.setText(desc + ('...' if len(desc) > 180 else ''))

        self.cards['Published By'].set_value(info.get('uploader') or info.get('channel') or '—')

        date = f'{date[:4]}-{date[4:6]}-{date[6:]}' if len((date := info.get('upload_date') or '')) == 8 else date
        self.cards['Published On'].set_value(date or '—')

        views = info.get('view_count')
        self.cards['Views'].set_value(f'{views:,}' if views else '—')

        likes = info.get('like_count')
        self.cards['Likes'].set_value(f'{likes:,}' if likes else '—')

        self.cards['Duration'].set_value(info.get('duration_string') or '—')
        self.cards['Formats'].set_value(str(len(info.get('formats', []))))

        if (thumb_url := info.get('thumbnail') or ''):
            self.thumbnail.setText('⟳')
            self._pixmap = None
            self._th_worker = ThumbnailWorker(thumb_url)
            self._th_worker.done.connect(self._set_thumbnail)
            self._th_worker.error.connect(lambda: self.thumbnail.setText('—\n—\n—'))
            self._th_worker.start()

        self._populate_trees(info.get('formats', []))

        self.info_panel.setVisible(True)
        self.trees_panel.setVisible(True)

        url = info.get('webpage_url') or self.url_input.text().strip()
        self._cf_worker = CaptionsSearchWorker(url)
        self._cf_worker.done.connect(self._set_captions)
        self._cf_worker.error.connect(lambda _: None)
        self._cf_worker.start()

        self.cfg['HISTORY'].append({'URL': self.url_input.text(), 'TITLE': self.title_lbl.text()})
        self.cfg['HISTORY'] = self.cfg['HISTORY'][:100]

        with open(self.cfg_path, 'w', encoding='utf-8') as file:
            json.dump(self.cfg, file, ensure_ascii=False, indent=4)

    def _set_thumbnail(self, px):
        self._pixmap = px
        w, h = self.thumbnail.width(), self.thumbnail.height()
        self.thumbnail.setPixmap(
            px.scaled(
                w, h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )
        self.thumbnail.setStyleSheet('border: none; background: transparent;')

    def _copy_title(self):
        QApplication.clipboard().setText(self._info.get('title', 'Unknown'))

    def _copy_desc(self):
        QApplication.clipboard().setText(self._info.get('description', ''))

    def _save_thumbnail(self):
        if not self._pixmap:
            return

        title = ''.join(c for c in (self._info or {}).get('title', 'thumbnail') if c.isalnum() or c in ' _-')[:60].strip()
        default = os.path.join(self.download_path, f'{title}_thumbnail.png')
        path, _ = QFileDialog.getSaveFileName(self, 'Save Thumbnail', default, 'Images (*.png *.jpg)')

        if path:
            self._pixmap.save(path)
            self._set_status(f'Thumbnail saved  {path}', ok=True, saved_path=os.path.dirname(path))

    def _tab_change(self, index: int):
        if not hasattr(self, 'status_bar'):
            return

        def clear(tree):
            tree.blockSignals(True)
            tree.clearSelection()
            tree.blockSignals(False)

        if index == 0:     # Video / Audio
            clear(self.combined_tree)
            clear(self.unclassified_tree)
        elif index == 1:   # Combined
            clear(self.video_tree)
            clear(self.audio_tree)
            clear(self.unclassified_tree)
        elif index == 2:   # UnClassified
            clear(self.video_tree)
            clear(self.audio_tree)
            clear(self.combined_tree)
        elif index == 3:   # Captions
            clear(self.video_tree)
            clear(self.audio_tree)
            clear(self.combined_tree)
            clear(self.unclassified_tree)

        self._selected = []
        self.main_btn.setEnabled(False)

        self._update_guide()

    def _update_guide(self):
        idx = self.tabs.currentIndex()
        if idx == 0:
            self.guide_lbl.setText('Select Video  AND / OR  Audio Stream To Download')
        elif idx == 1:
            self.guide_lbl.setText('Select A Stream To Download')
        elif idx == 1:
            self.guide_lbl.setText('Select A Stream To Download')
        elif idx == 3:
            self.guide_lbl.setText('Select A Caption Track  AND / OPTIONAL  Translation To Download')
        else:
            self.guide_lbl.setText('')

    def _populate_trees(self, formats):
        self.video_tree.clear()
        self.audio_tree.clear()
        self.combined_tree.clear()
        self._selected = []

        vo, ao, co, uc = Format.classify(formats)

        for i, l in enumerate([vo, ao + co, uc]):
            if [] == l:
                self.tabs.setTabEnabled(i, False)

        for f in vo:
            fid = f.get('format_id', '?')
            ext = f.get('ext', '?')
            fps = str(f.get('fps', '?'))

            res  = (f"{f.get('width', '?')}x{f.get('height', '?')}" if f.get('height') else '?')
            res += f'({note})' if (note := f.get('format_note', '')) else ''

            codec = (f.get('vcodec') or '?').split('.')[0][:14]
            br    = Format.bitrate(f.get('vbr') or f.get('tbr'))
            size  = Format.size(f.get('filesize') or f.get('filesize_approx'))

            self.video_tree.add_item([ext, res, fps, codec, br, size], {'id': fid, 'type': 'VIDEO'})

        for f in ao:
            fid = f.get('format_id', '?')
            ext = f.get('ext', '?')
            asr = f"{f.get('asr','?')} Hz" if f.get('asr') else '?'

            ch  = str(f.get('audio_channels', '?'))
            ch += f'[{lang}]' if (lang := f.get('language', '')) else ''

            codec = (f.get('acodec') or '?').split('.')[0][:14]
            br    = Format.bitrate(f.get('abr') or f.get('tbr'))
            size  = Format.size(f.get('filesize') or f.get('filesize_approx'))
    
            self.audio_tree.add_item([ext, asr, ch, codec, br, size], {'id': fid, 'type': 'AUDIO'})

        for f in co:
            fid = f.get('format_id', '?')
            ext = f.get('ext', '?')

            res  = (f"{f.get('width', '?')}x{f.get('height', '?')}" if f.get('height') else '?')
            res += f'({note})' if (note := f.get('format_note', '')) else ''

            vcodec = (f.get('vcodec') or '?').split('.')[0][:10]
            acodec = (f.get('acodec') or '?').split('.')[0][:10]

            br     = Format.bitrate(f.get('tbr'))
            size   = Format.size(f.get('filesize') or f.get('filesize_approx'))
    
            self.combined_tree.add_item([ext, res, vcodec, acodec, br, size], {'id': fid, 'type': 'V+A'})

        uc_keys = sorted({key for f in uc for key in f.keys()})
        self.unclassified_tree.setup(uc_keys)

        for f in uc:
            if (fid := f.get('format_id')):
                self.unclassified_tree.add_item(
                    [str(f.get(key, '?')) for key in uc_keys],
                    {'id': fid, 'type': 'UNCLASSIFIED'}
                )

        self._update_guide()

    def _select_separated(self):
        selected = [d for tree in (self.video_tree, self.audio_tree) for item in tree.selectedItems() if (d := item.data(0, Qt.ItemDataRole.UserRole))]
        self._selected = [s['id'] for s in selected]

        n, types =  len(selected), [s['type'] for s in selected]
        if n == 0:
            self._update_guide()
            if self.main_btn.text() == 'DOWNLOAD':
                self.main_btn.setEnabled(False)
        elif n == 1:
            self.guide_lbl.setText(f'1 Stream Selected  ({types[0]})')
            self.main_btn.setEnabled(True)
        else:
            self.guide_lbl.setText('2 Streams Selected (Download AND Merge)')
            self.main_btn.setEnabled(True)

    def _select_combined(self):
        selected = [d for item in self.combined_tree.selectedItems() if (d := item.data(0, Qt.ItemDataRole.UserRole))]
        self._selected = [s['id'] for s in selected]

        if selected:
            self.guide_lbl.setText('Combined Stream Selected')
            self.main_btn.setEnabled(True)
        else:
            self._update_guide()
            if self.main_btn.text() == 'DOWNLOAD':
                self.main_btn.setEnabled(False)

    def _select_unclassified(self):
        selected = [d for item in self.unclassified_tree.selectedItems() if (d := item.data(0, Qt.ItemDataRole.UserRole))]
        self._selected = [s['id'] for s in selected]

        if selected:
            self.guide_lbl.setText('UnClassified Stream Selected')
            self.main_btn.setEnabled(True)
        else:
            self._update_guide()
            if self.main_btn.text() == 'DOWNLOAD':
                self.main_btn.setEnabled(False)

    def _set_captions(self, captions: list, options: list):
        self._captions = captions
        self._options  = options

        if captions:
            self.captions_tree.clear()
            for c in captions:
                self.captions_tree.add_item([f'{c['name']} ({c['code'].upper()})'], c)

        if options:
            self.translate_tree.clear()
            for o in options:
                self.translate_tree.add_item([f'{o['name']} ({o['code'].upper()})'], o['code'])

            self.tabs.setTabEnabled(3, True)

    def _preview_caption(self):
        items = self.captions_tree.selectedItems()
        if not items or not self._info:
            return

        selected = items[0].data(0, Qt.ItemDataRole.UserRole)

        self._enable_all(False)
        self._set_status(f'Fetching Caption :: [{selected["code"].upper()}]', busy=True)

        self.tabs.setEnabled(False)
        self.captions_tree.setEnabled(False)
        self.translate_tree.setEnabled(False)

        self._ce_worker = CaptionExtracterWorker(
            self._info.get('webpage_url') or self.url_input.text().strip(),
            selected['code'],
            selected['name'],
            self._translate_to,
            self.download_path
        )

        self._ce_worker.progress.connect(lambda m: self._set_status(m, busy=True))
        self._ce_worker.done.connect(self._caption_done)
        self._ce_worker.error.connect(self._caption_error)
        self._ce_worker.start()

    def _translate_caption(self):
        items = self.translate_tree.selectedItems()
        if items:
            self._translate_to = items[0].data(0, Qt.ItemDataRole.UserRole)
            self._preview_caption()
        else:
            self._translate_to = None

    def _caption_done(self, data: str, is_url: bool):
        self._set_ready()
        self.tabs.setEnabled(True)

        self.paste_caption_btn.setVisible(True)
        self.cancel_caption_btn.setVisible(True)
        if not is_url:
            self.paste_caption_btn.setText('SAVE')
            self.preview_box.setText(data)
            self.captions_tree.setEnabled(True)
            self.translate_tree.setEnabled(True)
            self._set_status(f'Caption Ready :: Preview OR Save', ok=True)
        else:
            self.paste_caption_btn.setText('PASTE')
            self.preview_box.setText('')
            self.preview_box.setPlaceholderText('Copy and Paste the captions XML content\nfrom your browser session')
            QDesktopServices.openUrl(QUrl(data))
            self._set_status(f'Caption Process :: Require User Interaction', ok=False)

    def _caption_error(self, msg):
        self._set_ready()
        self._set_status(f'Caption Error :: {msg}', ok=False)

        self.tabs.setEnabled(True)
        self.captions_tree.setEnabled(True)

    def _paste_caption(self):
        if self.paste_caption_btn.text() == 'SAVE':
            self._save_caption()
            return

        text = QApplication.clipboard().text()
        self.preview_box.setText(text)
        srt = Format.caption(text)

        if srt is None:
            self.preview_box.setText('Invalid Caption')
            self._set_status('Caption Formatting Error :: Invalid XML Input')
            self.paste_caption_btn.setText('SAVE')
        else:
            self.preview_box.setText(srt)
            self.paste_caption_btn.setText('SAVE')
            self._set_status(f'Caption Ready :: Preview OR Save', ok=True)

    def _cancel_caption(self, fake: bool = False):
        self.paste_caption_btn.setVisible(False)
        self.cancel_caption_btn.setVisible(False)

        self.paste_caption_btn.setText('PASTE')

        self.preview_box.setText('')
        self.preview_box.setPlaceholderText('')

        self.captions_tree.clearSelection()
        self.translate_tree.clearSelection()

        self.captions_tree.setEnabled(True)
        self.translate_tree.setEnabled(True)

        if not fake:
            self._set_status('Cancelled :: Waiting For Next Task', ok=False)

    def _save_caption(self):
        os.makedirs(self.download_path, exist_ok=True)

        try:
            name = re.sub(r'[^\w\s-]', '', self.title_lbl.text())[:40].strip()
            post = f'_{self._translate_to}' if self._translate_to else ''
            path = os.path.join(self.download_path, f'{name}{post}.srt')

            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.preview_box.toPlainText())
            self._set_status(f'Saved :: {os.path.dirname(path)}', ok=True, saved_path=os.path.dirname(path))

            self._cancel_caption(fake=True)

        except Exception as e:
            self._set_status(f'Caption Error :: {e}', ok=False)

    def _download(self):
        if not self._selected or not self._info:
            return

        fmt_str = '+'.join(self._selected)
        url     = (self._info.get('webpage_url') or self.url_input.text().strip().split('&')[0])

        self._enable_all(False)
        self.tabs.setEnabled(False)
        self.progress.setValue(0)
        self._set_status(f'Pre-Processing :: [{fmt_str}]', busy=True)

        self._d_worker = DownloadWorker(url, fmt_str, self.download_path)
        self._d_worker.progress.connect(self._download_progress)
        self._d_worker.done.connect(self._download_done)
        self._d_worker.error.connect(self._download_error)
        self._d_worker.status.connect(lambda m: self._set_status(m, busy=True))
        self._d_worker.start()

        self.sub_btn.setEnabled(True)

    def _download_progress(self, pct, speed):
        self.progress.setValue(pct)
        self._set_status(speed, busy=True)

    def _download_done(self, path):
        self._set_ready()
        self.tabs.setEnabled(True)
        self.progress.setValue(100)

        self.main_btn.setEnabled(bool(self._selected) or bool(self.captions_tree.selectedItems()))
        self._set_status(f'Downloaded :: Saved at `{path}`', ok=True, saved_path=path)

    def _download_error(self, msg):
        self.progress.setValue(0)
        self._set_ready()
        self.main_btn.setEnabled(bool(self._selected) or bool(self.captions_tree.selectedItems()))
        self._set_status(f'Download Error :: {msg}', ok=False)


    @staticmethod
    def Start(load: str = ''):
        app = QApplication(sys.argv)
        win = App(load)
        sys.exit(app.exec())
