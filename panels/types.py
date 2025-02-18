from PySide6.QtCore import QSize
from PySide6.QtWidgets import QSizePolicy, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit

from panel_widget import PanelWidget
from slot_containers import SingleContainer


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

    def fill_slots(self, slots: dict[tuple[str, int], str | None]):
        raise Exception("Type panel has no slots; cannot fill")

    def get_slot_widget(self, slot: tuple[str, int]) -> 'PanelWidget':
        raise Exception("Type panel has no slots; cannot get")


class PCreator(PanelWidget):
    """
    Panel that can create a new instance of a type with a given name
    """

    def __init__(self, name: str, manager):
        super(PCreator, self).__init__(name, manager)

        # Containers for input and output
        self.type_to_make = SingleContainer(self, 'type_to_make', allowed_types={'type'})
        self.result = SingleContainer(self, 'result', drops=False)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        create_button = QPushButton("Create")
        create_button.pressed.connect(self.create_panel)
        self.id_edit = QLineEdit()

        layout = QVBoxLayout()
        layout.addWidget(self.type_to_make)
        layout.addWidget(self.id_edit)
        layout.addWidget(create_button)
        layout.addWidget(self.result)
        self.setLayout(layout)

    @staticmethod
    def panel_type() -> str:
        return "creator"

    def create_panel(self):
        new_id = self.id_edit.text()
        type_name = self.type_to_make.get_panel_widget().name
        self.manager.invent_panel(new_id, type_name)
        update_dict = {("result", 0): new_id}
        self.manager.update_panel(self, None, update_dict)

    def fill_attributes(self, attrs: dict[str, object]):
        raise NotImplementedError("Creators have no attributes")

    def fill_slots(self, slots: dict[tuple[str, int], str | None]):
        self.type_to_make.update_from(slots)
        self.result.update_from(slots)

    def get_slot_widget(self, slot: tuple[str, int]) -> 'PanelWidget':
        if slot[0] == 'type_to_make':
            return self.type_to_make.get_panel_widget()
        elif slot[0] == 'result':
            return self.result.get_panel_widget()
        else:
            raise Exception("No such slot")


