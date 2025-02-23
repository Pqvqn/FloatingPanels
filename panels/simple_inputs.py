from PySide6.QtCore import QSize
from PySide6.QtWidgets import QSizePolicy, QLabel, QHBoxLayout, QPushButton, QSpinBox

from panel_widget import PanelWidget


class PTask(PanelWidget):
    """
    Panel that can be checked off to mark completion of a task. The name is displayed as the task.
    """

    def __init__(self, name, manager):
        super(PTask, self).__init__(name, manager)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

        self.checkbox = QPushButton()
        self.checkbox.setFixedSize(20, 20)
        self.text = QLabel(name)
        layout = QHBoxLayout()
        layout.addWidget(self.checkbox)
        layout.addWidget(self.text)
        self.setLayout(layout)

        self.checkbox.pressed.connect(lambda: self.pass_to_db(attributes={"checked": not self.checkbox.text()}))

    def sizeHint(self) -> QSize:
        return QSize(40, 40)

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

    def fill_slots(self, slots: dict[tuple[str, int], str | None]):
        raise NotImplementedError("Tasks have no slots; cannot fill")

    def get_slot_widget(self, slot: tuple[str, int]) -> 'PanelWidget':
        raise NotImplementedError("Tasks have no slots; cannot get")


class PNumber(PanelWidget):
    """
    Panel containing a number whose value can be adjusted,
    """

    def __init__(self, name, manager):
        super(PNumber, self).__init__(name, manager)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

        self.num = QSpinBox()
        self.num.setRange(-(10**8), 10**8)
        self.text = QLabel(name)
        layout = QHBoxLayout()
        layout.addWidget(self.text)
        layout.addWidget(self.num)
        self.setLayout(layout)

        self.num.editingFinished.connect(lambda: self.pass_to_db(attributes={"value": self.num.value()}))

    def sizeHint(self) -> QSize:
        return QSize(40, 40)

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

    def fill_slots(self, slots: dict[tuple[str, int], str | None]):
        raise NotImplementedError("Numbers have no slots; cannot fill")

    def get_slot_widget(self, slot: tuple[str, int]) -> 'PanelWidget':
        raise NotImplementedError("Numbers  have no slots; cannot get")
