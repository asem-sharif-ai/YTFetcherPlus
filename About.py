from PyQt6.QtWidgets import (
    QDialog, QWidget, QFrame, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QUrl
from PyQt6.QtGui import QColor, QCursor, QDesktopServices, QPixmap

DESCRIPTION = 'Lightweight, high-performance desktop tool for fetching, inspecting, and downloading video streams, audio tracks, and subtitles from YouTube and major platforms. Powered be PyQt6 and yt-dlp.'

LINKED = 'https://www.linkedin.com/in/asem-sharif'
GITHUB = 'https://github.com/asem-sharif-ai'
TELEGRAM = 'https://t.me/notasem'
SRC_CODE = 'https://github.com/asem-sharif-ai/YTFetcherPlus'

def _open(url: str):
    QDesktopServices.openUrl(QUrl(url))

class _TitleBar(QWidget):
    def __init__(self, parent: QDialog):
        super().__init__(parent)
        self._drag_pos = QPoint()
        self.setFixedHeight(40)
        self.setCursor(Qt.CursorShape.SizeAllCursor)

        box = QHBoxLayout(self)
        box.setContentsMargins(15, 0, 15, 0)
        box.setSpacing(10)

        for color, tip in [("#FF4343", 'Close'), ("#FFFF43", 'Minimize'), ("#43FF43", 'Maximize')]:
            dot = QLabel()
            dot.setFixedSize(12, 12)
            dot.setToolTip(tip)
            dot.setStyleSheet(f'''
                QLabel {{
                    background: {color};
                    border-radius: 6px;
                }}
                QLabel:hover {{
                    background: {color};
                    border: 1.5px solid rgba(0, 0, 0, 0.25);
                }}
            ''')
            box.addWidget(dot)

        box.addStretch()
        box.addSpacing(50)

        self.setStyleSheet('background: rgba(255, 255, 255, 0.1);')

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.window().frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.window().move(e.globalPosition().toPoint() - self._drag_pos)


class _LinkCard(QFrame):
    def __init__(self, svg: str, bg: str, title: str, subtitle: str, url: str):
        super().__init__()
        self.setObjectName('LinkCard')
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(60)
        self._url = url

        box = QHBoxLayout(self)
        box.setContentsMargins(15, 5, 15, 5)
        box.setSpacing(10)

        icon_wrap = QLabel()
        icon_wrap.setFixedSize(30, 30)
        icon_wrap.setText(svg)
        icon_wrap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_wrap.setStyleSheet(f'background: {bg}; border-radius: 8px; font-size: {15-len(svg)}px;')

        info = QVBoxLayout()
        info.setContentsMargins(0, 0, 0, 0)
        info.setSpacing(0)

        t = QLabel(title)
        t.setAlignment(Qt.AlignmentFlag.AlignBottom)
        t.setStyleSheet('color: rgba(255, 255, 255, 0.6); font-size: 11px; font-weight: 500; letter-spacing: 1px; background: transparent;')

        s = QLabel(subtitle)
        s.setStyleSheet('color: rgba(255, 255, 255, 0.3); font-size: 10px; font-family: monospace; letter-spacing: 1px; background: transparent;')

        info.addWidget(t)
        info.addWidget(s)

        arrow = QLabel('↗')
        arrow.setStyleSheet('color: rgba(255, 255, 255, 0.2); font-size: 20px; font-weight: 400; background: transparent;')

        box.addWidget(icon_wrap)
        box.addLayout(info)
        box.addStretch()
        box.addWidget(arrow)

        self.setStyleSheet('''
            QFrame#LinkCard {
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(255, 255, 255, 0.07);
                border-radius: 8px;
            }
            QFrame#LinkCard:hover {
                background: rgba(255, 255, 255, 0.07);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        ''')

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            _open(self._url)


class _UsageLine(QWidget):
    def __init__(self, prompt: str, cmd: str, comment: str):
        super().__init__()
        box = QHBoxLayout(self)
        box.setContentsMargins(0, 2, 0, 2)
        box.setSpacing(10)

        def lbl(text, style):
            l = QLabel(text)
            l.setStyleSheet(style)
            return l

        box.addWidget(lbl(prompt,  'color:rgba(255, 255, 255, 0.2); font-family:monospace; font-size:12px;'))
        box.addWidget(lbl(cmd,     'color:rgba(255, 255, 255, 0.75); font-family:monospace; font-size:12px; font-weight:500;'))
        box.addWidget(lbl(comment, 'color:rgba(255, 255, 255, 0.25); font-family:monospace; font-size:11px;'))
        box.addStretch()


class _AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Dialog              |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedWidth(540)
        self.setMinimumHeight(600)

        self._build()
        self.adjustSize()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        card = QFrame()
        card.setObjectName('AboutCard')
        card.setStyleSheet('''
            QFrame#AboutCard {
                background: rgba(10, 10, 10, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 14px;
            }
        ''')

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(60)
        shadow.setOffset(0, 12)
        shadow.setColor(QColor(0, 0, 0, 180))
        card.setGraphicsEffect(shadow)

        card_box = QVBoxLayout(card)
        card_box.setContentsMargins(0, 0, 0, 0)
        card_box.setSpacing(0)

        card_box.addWidget(_TitleBar(self))

        body = QWidget()
        body.setStyleSheet('background: transparent;')
        body_box = QVBoxLayout(body)
        body_box.setContentsMargins(30, 0, 30, 0)
        body_box.setSpacing(0)

        body_box.addLayout(self._header())
        body_box.addWidget(self._description())
        body_box.addSpacing(24)
        body_box.addWidget(self._divider())
        body_box.addSpacing(16)
        body_box.addLayout(self._usage())
        body_box.addSpacing(18)
        body_box.addWidget(self._divider())
        body_box.addSpacing(16)
        body_box.addLayout(self._links())
        body_box.addSpacing(24)
        card_box.addWidget(body)
        card_box.addWidget(self._footer())

        root.addWidget(card)

    def _header(self) -> QHBoxLayout:
        box = QHBoxLayout()
        box.setSpacing(20)

        icon = QLabel()
        icon.setFixedSize(80, 80)
        icon.setPixmap(QPixmap('BG.png').scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        text_col = QVBoxLayout()
        text_col.setSpacing(10)

        name = QLabel('𝖄𝕿 𝕱𝖊𝖙𝖈𝖍𝖊𝖗 𝕻𝖑𝖚𝖘')
        name.setTextFormat(Qt.TextFormat.RichText)
        name.setStyleSheet('''
            font-family: "Segoe UI Bold", "Roboto", "Helvetica Neue", sans-serif;
            font-size: 24px;
            font-weight: 800;
            color: #A00000;
            letter-spacing: 2px;
            background: transparent;
            padding: 0;
        ''')

        badges = QHBoxLayout()
        badges.setSpacing(10)
        badges.setContentsMargins(0,0,0,0)

        for text, style in [
            ('V 3.1.1', 'background:rgba(255, 255, 255, 0.2); color: rgba(255, 255, 255, 0.5); border:1px solid rgba(255, 255, 255, 0.1);'),
            ('STABLE', 'background:rgba(40, 200, 60, 0.1); color: #28C840; border: 1px solid rgba(40, 200, 60, 0.2);'),
        ]:
            b = QLabel(text)
            b.setFixedHeight(25)
            b.setStyleSheet(f'QLabel {{ {style} padding: 3px 9px; border-radius: 4px; font-size: 10px; font-family: monospace; letter-spacing: 1px; background: transparent; }}')
            badges.addWidget(b)

        badges.addStretch()

        text_col.addStretch()
        text_col.addWidget(name)
        text_col.addLayout(badges)
        text_col.addStretch()

        box.addWidget(icon)
        box.addLayout(text_col)
        box.addLayout(text_col)
        box.addStretch()

        return box

    def _description(self) -> QLabel:
        lbl = QLabel(DESCRIPTION)
        lbl.setWordWrap(True)
        lbl.setStyleSheet('color: rgba(255, 255, 255, 0.75); font-size: 12px; font-weight: 400; letter-spacing: 1px; background: transparent;')
        return lbl

    def _usage(self) -> QVBoxLayout:
        lay = QVBoxLayout()
        lay.setSpacing(8)

        lbl = QLabel('USAGE')
        lbl.setStyleSheet('color: rgba(255,255,255,0.2); font-size: 9px; font-family: monospace; letter-spacing: 2px; background: transparent;')
        lay.addWidget(lbl)

        box = QFrame()
        box.setObjectName('UsageBox')
        box.setStyleSheet('''
            QFrame#UsageBox {
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.07);
                border-radius: 8px;
            }
        ''')
        box_lay = QVBoxLayout(box)
        box_lay.setContentsMargins(14, 10, 14, 10)
        box_lay.setSpacing(2)

        for prompt, cmd, comment in [
            ('$', 'ytf              ', ' — Launch The App'),
            ('$', 'ytf "https://..."', ' — Launch With Quick Load')
        ]:
            box_lay.addWidget(_UsageLine(prompt, cmd, comment))

        lay.addWidget(box)
        return lay

    def _links(self) -> QVBoxLayout:
        box = QVBoxLayout()
        box.setSpacing(10)

        lbl = QLabel('DEVELOPER')
        lbl.setStyleSheet('color: rgba(255, 255, 255, 0.2); font-size: 9px; font-family: monospace; letter-spacing: 2px; background: transparent;')
        box.addWidget(lbl)

        grid_1 = QHBoxLayout()
        grid_1.setSpacing(10)
        grid_1.addWidget(_LinkCard('IN', 'rgba(10, 100, 195, 0.6)', 'LinkedIn', '@asem-sharif', LINKED))
        grid_1.addWidget(_LinkCard('T', 'rgba(0, 135, 205, 0.6)', 'Telegram',  '@notasem', TELEGRAM))

        grid_2 = QHBoxLayout()
        grid_2.setSpacing(10)
        grid_2.addWidget(_LinkCard('⌥', 'rgba(240, 80, 50, 0.6)', 'GitHub', '@asem-sharif-ai', GITHUB))
        grid_2.addWidget(_LinkCard(r'SRC', 'rgba(130, 80, 225, 0.6)', 'Source Code', '@YTFetcherPlus', SRC_CODE))

        box.addLayout(grid_1)
        box.addLayout(grid_2)

        return box

    def _footer(self) -> QFrame:
        foot = QFrame()
        foot.setObjectName('Footer')
        foot.setFixedHeight(50)
        foot.setStyleSheet('''
            QFrame#Footer {
                background: rgba(255, 255, 255, 0.02);
                border-top: 1px solid rgba(255, 255, 255, 0.05);
                border-bottom-left-radius:  14px;
                border-bottom-right-radius: 14px;
            }
        ''')

        box = QHBoxLayout(foot)
        box.setContentsMargins(15, 0, 15, 0)

        lbl = QLabel('Ⓒ 2026 Asem Sharif · MIT License')
        lbl.setStyleSheet('color: rgba(255, 255, 255, 0.4); font-size: 11px; font-family: monospace; background: transparent;')

        upd_btn = QPushButton('UPDATES')
        upd_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        upd_btn.clicked.connect(lambda: _open(SRC_CODE + '/releases'))
        upd_btn.setFixedWidth(120)

        ok_btn = QPushButton('OK')
        ok_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        ok_btn.clicked.connect(self._close_animated)
        ok_btn.setFixedWidth(80)

        for btn in (upd_btn, ok_btn):
            btn.setStyleSheet('''
                QPushButton {
                    color: rgba(255, 255, 255, 0.75);
                    background: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    border-radius: 5px;
                    padding: 5px 0;
                    font-size: 11px;
                    font-weight: 500;
                    letter-spacing: 0.5px;
                }
                QPushButton:hover {
                    color: white;
                    background: rgba(255, 255, 255, 0.15);
                    border-color: rgba(255, 255, 255, 0.25);
                }
                QPushButton:pressed {
                    background: rgba(255, 255, 255, 0.05);
                }
            ''')

        box.addWidget(lbl)
        box.addStretch()
        box.addWidget(upd_btn)
        box.addSpacing(10)
        box.addWidget(ok_btn)

        return foot

    def _divider(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet('background: rgba(255, 255, 255, 0.05); border: none;')
        return line

    def showEvent(self, e):
        super().showEvent(e)
        if self.parent():
            p = self.parent().geometry()
            self.move(
                p.center().x() - self.width()  // 2,
                p.center().y() - self.height() // 2
            )
        self._anim_in()

    def _anim_in(self):
        self.setWindowOpacity(0.0)
        anim = QPropertyAnimation(self, b'windowOpacity', self)
        anim.setDuration(180)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._anim = anim

    def _close_animated(self):
        anim = QPropertyAnimation(self, b'windowOpacity', self)
        anim.setDuration(140)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InCubic)
        anim.finished.connect(self.accept)
        anim.start()
        self._anim = anim

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._close_animated()


def show_about(parent=None) -> None:
    dlg = _AboutDialog(parent)
    dlg.exec()