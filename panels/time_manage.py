from PySide6.QtCore import QDate
from PySide6.QtWidgets import QGridLayout, QPushButton, QLineEdit, QSpinBox, QVBoxLayout, QHBoxLayout, QLabel, QFrame

from panel_widget import PanelWidget
from slot_containers import SingleContainer


class PCalendar(PanelWidget):
    """
    Panel that creates a calendar for a given month, with a new panel for each day
    """


    def __init__(self, name: str, manager):
        super(PCalendar, self).__init__(name, manager)

        self.daily_type = SingleContainer(self, "daily_type", allowed_types={"type"}, drags=False, drops=False)


        self.month_edit = QSpinBox()
        self.month_edit.setRange(1, 12)
        self.month_edit.editingFinished.connect(lambda: self.pass_to_db(attributes={"month": self.month_edit.value()}))
        self.year_edit = QSpinBox()
        self.year_edit.setRange(2000, 2100)
        self.year_edit.editingFinished.connect(lambda: self.pass_to_db(attributes={"year": self.year_edit.value()}))

        generate_button = QPushButton("⏬")
        generate_button.pressed.connect(self.generate_month)

        self.month_label = QLabel()

        self.grid = QGridLayout()
        for i in range(6):
            for j in range(7):
                day_frame = QFrame()
                day_frame.setLayout(QVBoxLayout())
                self.grid.addWidget(day_frame, i, j)

        setting_row = QHBoxLayout()
        setting_row.addWidget(QLabel("Month:"))
        setting_row.addWidget(self.month_edit)
        setting_row.addWidget(QLabel("Year:"))
        setting_row.addWidget(self.year_edit)

        gen_row = QHBoxLayout()
        gen_row.addWidget(self.daily_type)
        gen_row.addWidget(generate_button)

        layout = QVBoxLayout()
        layout.addLayout(setting_row)
        layout.addLayout(gen_row)
        layout.addWidget(self.month_label)
        layout.addLayout(self.grid)
        self.setLayout(layout)

    @staticmethod
    def panel_type() -> str:
        return "calendar"

    @staticmethod
    def attributes() -> dict[str, str]:
        return {
            "month": "INTEGER",
            "year": "INTEGER"
        }

    @staticmethod
    def default_attributes() -> dict[str, object]:
        right_now = QDate.currentDate()
        return {
            "month": right_now.month(),
            "year": right_now.year()
        }

    def fill_attributes(self, attrs: dict[str, object]):
        if "month" in attrs.keys():
            self.month_edit.setValue(attrs["month"])
        if "year" in attrs.keys():
            self.year_edit.setValue(attrs["year"])

    def fill_slots(self, slots: dict[tuple[str, int], str | None]):
        self.container.update_from(slots)

    def get_slot_widget(self, slot: tuple[str, int]) -> 'PanelWidget':
        if slot[0] == 'elem':
            return self.container.panel_widget_at(slot[1])
        else:
            raise Exception("No such slot")

    def day_to_cell(self, day: QDate) -> tuple[int, int]:
        pass

    def generate_month(self):
        date = QDate(self.year_edit.value(), self.month_edit.value(), 1)
        updates_dict = {}
        for i in date.daysInMonth():
