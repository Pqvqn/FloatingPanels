from PySide6.QtCore import QSize
from PySide6.QtWidgets import QSizePolicy, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit

from panel_widget import PanelWidget
from slot_containers import SingleContainer, ListContainer


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

        create_button = QPushButton("⬇")
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
        """
        Creates a new panel in the results slot using the type in the type
        slot and the name written in the line edit
        """
        new_id = self.id_edit.text()
        type_widget = self.type_to_make.get_panel_widget()
        if type_widget:
            self.manager.invent_panel(new_id, type_widget.name)
            update_dict = {("result", 0): new_id}
            self.manager.update_panel(self, None, update_dict)
        else:
            raise Exception("No type given for creator")

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

class PFinder(PanelWidget):
    """
    Panel that holds a manually-refreshed list of every panel of a certain type
    """

    def __init__(self, name: str, manager):
        super(PFinder, self).__init__(name, manager)

        # Containers for input and output
        self.type_to_find = SingleContainer(self, 'type_to_find', allowed_types={'type'})
        self.results = ListContainer(self, 'result', drops=False)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)

        refresh_button = QPushButton("🔄")
        refresh_button.pressed.connect(self.generate_list)

        layout = QVBoxLayout()
        layout.addWidget(self.type_to_find)
        layout.addWidget(refresh_button)
        layout.addWidget(self.results)
        self.setLayout(layout)

    @staticmethod
    def panel_type() -> str:
        return "finder"

    def generate_list(self):
        """
        Clears and regenerates the list of panels according to the type
        in the type slot
        """
        updates = {}
        # First, clear all current entries of the list by default
        for x in range(self.results.num_entries()):
            updates[("result", x)] = None

        # Get type from slot
        curr_type_wid = self.type_to_find.get_panel_widget()
        # Only add new results if a type exists. If none exists, clearing is enough
        if curr_type_wid:
            # Get panels matching type from the manager
            ids = self.manager.query_panels(match_type=curr_type_wid.name)
            # Interpret into update dict
            for i, x in enumerate(ids):
                updates[("result", i)] = x

        self.manager.update_panel(self, None, slots_dict=updates)

    def fill_attributes(self, attrs: dict[str, object]):
        raise NotImplementedError("Finders have no attributes")

    def fill_slots(self, slots: dict[tuple[str, int], str | None]):
        self.type_to_find.update_from(slots)
        self.results.update_from(slots)

    def get_slot_widget(self, slot: tuple[str, int]) -> 'PanelWidget':
        if slot[0] == 'type_to_find':
            return self.type_to_find.get_panel_widget()
        elif slot[0] == 'result':
            return self.results.panel_widget_at(slot[1])
        else:
            raise Exception("No such slot")
