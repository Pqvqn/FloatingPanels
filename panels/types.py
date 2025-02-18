from PySide6.QtCore import QSize
from PySide6.QtWidgets import QSizePolicy, QLabel, QHBoxLayout

from panel_widget import PanelWidget


class PType(PanelWidget):

    def __init__(self, name: str, manager):
        super(PType, self).__init__(name, manager)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

        self.text = QLabel("<i>type:"+name+"</i>")
        layout = QHBoxLayout()
        layout.addWidget(self.text)
        self.setLayout(layout)

    def sizeHint(self) -> QSize:
        return QSize(40, 40)

    @staticmethod
    def panel_type() -> str:
        return "type"

    @staticmethod
    def allow_user_creation() -> bool:
        return False

    def fill_attributes(self, attrs: dict[str, object]):
        raise Exception("Type panel has no attributes; cannot fill")

    def fill_slots(self, slots: dict[tuple[str, int], str]):
        raise Exception("Type panel has no slots; cannot fill")

    def get_slot_widget(self, slot: tuple[str, int]) -> 'PanelWidget':
        raise Exception("Type panel has no slots; cannot get")
