from PySide6.QtWidgets import QGridLayout

from panel_widget import PanelWidget
from slot_containers import SingleContainer


class PCalendar(PanelWidget):
    """
    Panel that creates a calendar for a given month, with a new panel for each day
    """
    pass
    #
    # def __init__(self, name: str, manager):
    #     super(PCalendar, self).__init__(name, manager)
    #
    #     self.daily_type = SingleContainer(self, "daily_type", allowed_types={"type"}, drags=False, drops=False)
    #
    #     self.grid = QGridLayout()
    #
    #     # Container that holds all subpanels
    #     self.container = ListContainer(self, 'elem')
    #     self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
    #
    #     layout = QVBoxLayout()
    #     layout.addWidget(QLabel(self.name))
    #     layout.addWidget(self.container)
    #     self.setLayout(layout)
    #
    # @staticmethod
    # def panel_type() -> str:
    #     return "calendar"
    #
    # def fill_attributes(self, attrs: dict[str, object]):
    #     raise NotImplementedError("Shelves have no attributes")
    #
    # def fill_slots(self, slots: dict[tuple[str, int], str | None]):
    #     self.container.update_from(slots)
    #
    # def get_slot_widget(self, slot: tuple[str, int]) -> 'PanelWidget':
    #     if slot[0] == 'elem':
    #         return self.container.panel_widget_at(slot[1])
    #     else:
    #         raise Exception("No such slot")