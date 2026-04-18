
from PyQt6.QtWidgets import (
    QFrame, QLabel, QPushButton, QVBoxLayout, QSizePolicy,
    QTreeWidget, QTreeWidgetItem, QAbstractItemView, QHeaderView
)

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCursor


class Label(QLabel):
    def __init__(self, *args, on_press=None, on_click=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName('StatusLabel')

        self._on_press = on_press
        self._on_click = on_click

        if on_press or on_click:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self._on_press:
            self._on_press()
        super().mousePressEvent(e)

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self._on_click:
            self._on_click()
        super().mouseDoubleClickEvent(e)


class Button(QPushButton):
    def __init__(self, text, name='', action=lambda: None):
        super().__init__(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName(name)
        self.clicked.connect(action)


class Dot(QLabel):
    def __init__(self):
        super().__init__('●')
        self.setObjectName('StatusDot')

        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)

        self._colors = ['#003366', '#0052cc', '#0074ff', '#0052cc']
        self._i, self._l = 0, len(self._colors)

    def start(self):
        self._timer.start(500)

    def stop(self, ok=True):
        self._timer.stop()
        color = '#11ee11' if ok else '#ee1111'
        self.setStyleSheet(f'color: {color};')

    def _tick(self):
        self.setStyleSheet(f'color: {self._colors[self._i]};')
        self._i = (self._i + 1) % self._l


class Card(QFrame):
    def __init__(self, key, value='—'):
        super().__init__()
        self.setObjectName('Card')

        box = QVBoxLayout(self)
        box.setContentsMargins(10, 10, 10, 10)
        box.setSpacing(5)

        self.val_lbl = QLabel(value)
        self.val_lbl.setObjectName('CardValue')

        self.key_lbl = QLabel(key.upper())
        self.key_lbl.setObjectName('CardKey')

        box.addWidget(self.val_lbl)
        box.addWidget(self.key_lbl)

    def set_value(self, v):
        self.val_lbl.setText(v if len(v) <= 14 else f'{v[:13]}..')


class Tree(QTreeWidget):
    def __init__(self, name: str, columns: list[str]):
        super().__init__()
        self.setObjectName(f'{name}Tree')
        self.setColumnCount(len(columns))
        self.setHeaderLabels(columns)
        self.setRootIsDecorated(False)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        header = self.header()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionsMovable(False)

    def add_item(self, values: list[str], data: dict = None) -> QTreeWidgetItem:
        item = QTreeWidgetItem(self)
        for col, val in enumerate(values):
            item.setText(col, val)

        item.setData(0, Qt.ItemDataRole.UserRole, data)
        return item

    def setup(self, columns: list):
        self.setColumnCount(len(columns))
        self.setHeaderLabels(columns)