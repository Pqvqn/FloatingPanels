from PySide6.QtCore import Qt, QPoint, QSize
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QLabel


class VerticalText(QLabel):

    def __init__(self, text):
        super(VerticalText, self).__init__(text)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.rotate(270)
        painter.drawText(QPoint(-self.height(), self.width()), self.text())

    def sizeHint(self):
        s = super().sizeHint()
        return QSize(s.height(), s.width())

    def minimumSizeHint(self):
        s = super().minimumSizeHint()
        return QSize(s.height(), s.width())
