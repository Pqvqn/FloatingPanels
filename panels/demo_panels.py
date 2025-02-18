from PySide6.QtCore import QSize
from PySide6.QtWidgets import QSizePolicy, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QSpinBox

from panel_widget import PanelWidget
from slot_containers import ListContainer

class PShelfHoriz(PanelWidget):
    """
    Panel that holds a list of subpanels, ordered left-to-right
    """

    def __init__(self, name: str, manager):
        super(PShelfHoriz, self).__init__(name, manager)

        # Container that holds all subpanels
        self.container = ListContainer(self, 'elem', True)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(self.name))
        layout.addWidget(self.container)
        self.setLayout(layout)

    @staticmethod
    def panel_type() -> str:
        return "hshelf"

    def fill_attributes(self, attrs: dict[str, object]):
        raise NotImplementedError("Shelves have no attributes")

    def fill_slots(self, slots: dict[tuple[str, int], str]):
        self.container.adjust_list(slots)

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

        layout = QVBoxLayout()
        layout.addWidget(QLabel(self.name))
        layout.addWidget(self.container)
        self.setLayout(layout)

    @staticmethod
    def panel_type() -> str:
        return "vshelf"

    def fill_attributes(self, attrs: dict[str, object]):
        raise NotImplementedError("Shelves have no attributes")

    def fill_slots(self, slots: dict[tuple[str, int], str]):
        self.container.adjust_list(slots)

    def get_slot_widget(self, slot: tuple[str, int]) -> 'PanelWidget':
        if slot[0] == 'elem':
            return self.container.panel_widget_at(slot[1])
        else:
            raise Exception("No such slot")


class PTask(PanelWidget):
    """
    Panel that can be checked off to mark completion of a task. The name is displayed as the task.
    """

    def __init__(self, name, manager):
        super(PTask, self).__init__(name, manager)

        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.checkbox = QPushButton()
        self.checkbox.setFixedSize(20, 20)
        self.text = QLabel(name)
        layout = QHBoxLayout()
        layout.addWidget(self.checkbox)
        layout.addWidget(self.text)
        self.setLayout(layout)

        self.checkbox.pressed.connect(lambda: self.pass_to_db(attributes={"checked": not self.checkbox.text()}))

    def sizeHint(self) -> QSize:
        return QSize(240, 40)

    @staticmethod
    def panel_type() -> str:
        return "task"

    @staticmethod
    def attributes() -> dict[str, str]:
        return {
            "checked": "INTEGER"
        }

    @staticmethod
    def default_attributes() -> dict[str, object]:
        return {
            "checked": False
        }

    def fill_attributes(self, attrs: dict[str, object]):
        if "checked" in attrs.keys():
            # Handle toggle of checkbox
            self.checkbox.setText("✅" if bool(attrs["checked"]) else "")

    def fill_slots(self, slots: dict[tuple[str, int], str]):
        raise NotImplementedError("Tasks have no slots; cannot fill")

    def get_slot_widget(self, slot: tuple[str, int]) -> 'PanelWidget':
        raise NotImplementedError("Tasks have no slots; cannot get")


class PNumber(PanelWidget):
    """
    Panel containing a number whose value can be adjusted,
    """

    def __init__(self, name, manager):
        super(PNumber, self).__init__(name, manager)

        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.num = QSpinBox()
        self.text = QLabel(name)
        layout = QHBoxLayout()
        layout.addWidget(self.text)
        layout.addWidget(self.num)
        self.setLayout(layout)

        self.num.editingFinished.connect(lambda: self.pass_to_db(attributes={"value": self.num.value()}))

    def sizeHint(self) -> QSize:
        return QSize(240, 40)

    @staticmethod
    def panel_type() -> str:
        return "number"

    @staticmethod
    def attributes() -> dict[str, str]:
        return {
            "value": "INTEGER"
        }

    @staticmethod
    def default_attributes() -> dict[str, object]:
        return {
            "value": 0
        }

    def fill_attributes(self, attrs: dict[str, object]):
        if "value" in attrs.keys():
            # Handle change in value
            self.num.setValue(attrs["value"])

    def fill_slots(self, slots: dict[tuple[str, int], str]):
        raise NotImplementedError("Numbers have no slots; cannot fill")

    def get_slot_widget(self, slot: tuple[str, int]) -> 'PanelWidget':
        raise NotImplementedError("Numbers  have no slots; cannot get")
