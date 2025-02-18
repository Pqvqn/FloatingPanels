from PySide6.QtCore import Qt, QPoint, QSize
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QLabel


class VerticalText(QLabel):
    """
    QLabel that draws text vertically oriented, with the beginning of the line on the bottom
    """

    def __init__(self, text):
        super(VerticalText, self).__init__(text)

    def paintEvent(self, e):
        # Use painter to rotate text
        painter = QPainter(self)
        painter.rotate(270)
        # Must adjust start position to draw in correct place
        painter.drawText(QPoint(-self.height(), self.width()), self.text())

    def sizeHint(self):
        # Flip sizes to account for rotation
        s = super().sizeHint()
        return QSize(s.height(), s.width())

    def minimumSizeHint(self):
        # Flip sizes to account for rotation
        s = super().minimumSizeHint()
        return QSize(s.height(), s.width())
