from PySide6.QtGui import Qt
from PySide6.QtWidgets import QSizePolicy, QLabel, QVBoxLayout, QHBoxLayout

from custom_widgets import VerticalText
from panel_widget import PanelWidget
from slot_containers import ListContainer, SingleContainer


class PShelfHoriz(PanelWidget):
    """
    Panel that holds a list of subpanels, ordered left-to-right
    """

    def __init__(self, name: str, manager):
        super(PShelfHoriz, self).__init__(name, manager)

        # Container that holds all subpanels
        self.container = ListContainer(self, 'elem', True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        layout = QHBoxLayout()
        layout.addWidget(VerticalText(self.name))
        layout.addWidget(self.container)
        self.setLayout(layout)

    @staticmethod
    def panel_type() -> str:
        return "hshelf"

    def fill_attributes(self, attrs: dict[str, object]):
        raise NotImplementedError("Shelves have no attributes")

    def fill_slots(self, slots: dict[tuple[str, int], str | None]):
        self.container.update_from(slots)

    def get_slot_widget(self, slot: tuple[str, int]) -> 'PanelWidget':
        if slot[0] == 'elem':
            return self.container.panel_widget_at(slot[1])
        else:
            raise Exception("No such slot")


class PShelfVert(PanelWidget):
    """
    Panel that holds a list of subpanels, ordered top-to-bottom.
    """

    def __init__(self, name: str, manager):
        super(PShelfVert, self).__init__(name, manager)

        # Container that holds all subpanels
        self.container = ListContainer(self, 'elem')
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(self.name))
        layout.addWidget(self.container)
        self.setLayout(layout)

    @staticmethod
    def panel_type() -> str:
        return "vshelf"

    def fill_attributes(self, attrs: dict[str, object]):
        raise NotImplementedError("Shelves have no attributes")

    def fill_slots(self, slots: dict[tuple[str, int], str | None]):
        self.container.update_from(slots)

    def get_slot_widget(self, slot: tuple[str, int]) -> 'PanelWidget':
        if slot[0] == 'elem':
            return self.container.panel_widget_at(slot[1])
        else:
            raise Exception("No such slot")


class PFootnote(PanelWidget):
    """
    Panel that holds a different panel and adds a footnote beneath it
    """

    def __init__(self, name: str, manager):
        super(PFootnote, self).__init__(name, manager)

        # Container that holds the panel being commented on
        self.container = SingleContainer(self, 'body', {"task"})
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        layout = QVBoxLayout()
        layout.addWidget(self.container)
        note = QLabel(self.name)
        note.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        note.setFixedHeight(15)
        layout.addWidget(note)
        self.setLayout(layout)

    @staticmethod
    def panel_type() -> str:
        return "footnote"

    def fill_attributes(self, attrs: dict[str, object]):
        raise NotImplementedError("Footnotes have no attributes")

    def fill_slots(self, slots: dict[tuple[str, int], str | None]):
        self.container.update_from(slots)

    def get_slot_widget(self, slot: tuple[str, int]) -> 'PanelWidget':
        if slot[0] == 'body':
            return self.container.get_panel_widget()
        else:
            raise Exception("No such slot")
