from PySide6.QtCore import QDate
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QGridLayout, QPushButton, QLineEdit, QSpinBox, QVBoxLayout, QHBoxLayout, QLabel, QFrame, \
    QSizePolicy

from panel_widget import PanelWidget
from slot_containers import SingleContainer


class PCalendar(PanelWidget):
    """
    Panel that creates a calendar for a given month, with a new panel for each day
    """


    def __init__(self, name: str, manager):
        super(PCalendar, self).__init__(name, manager)

        self.daily_type = SingleContainer(self, "daily_type", allowed_types={"type"})


        self.month_edit = QSpinBox()
        self.month_edit.setRange(1, 12)
        self.month_edit.editingFinished.connect(lambda: self.pass_to_db(attributes={"month": self.month_edit.value()}))
        self.year_edit = QSpinBox()
        self.year_edit.setRange(2000, 2100)
        self.year_edit.editingFinished.connect(lambda: self.pass_to_db(attributes={"year": self.year_edit.value()}))

        self.generate_button = QPushButton("⏬")
        self.generate_button.pressed.connect(self.generate_month)

        self.month_label = QLabel()
        self.month_label.setAlignment(Qt.AlignCenter)
        self.month_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        self.grid = QGridLayout()
        for i in range(6):
            for j in range(7):
                day_frame = SingleContainer(self, "day", slot_num=i*7+j, drags=False, drops=False)
                #day_frame.setFixedSize(200, 300)
                self.grid.addWidget(day_frame, i, j)

        setting_row = QHBoxLayout()
        setting_row.addWidget(QLabel("Month:"))
        setting_row.addWidget(self.month_edit)
        setting_row.addWidget(QLabel("Year:"))
        setting_row.addWidget(self.year_edit)

        gen_row = QHBoxLayout()
        gen_row.addWidget(self.daily_type)
        gen_row.addWidget(self.generate_button)

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
        self.daily_type.update_from(slots)
        for x in range(self.grid.rowCount()):
            for y in range(self.grid.columnCount()):
                self.grid.itemAtPosition(x, y).widget().update_from(slots)

    def get_slot_widget(self, slot: tuple[str, int]) -> 'PanelWidget':
        if slot[0] == 'daily_type':
            return self.daily_type.get_panel_widget()
        elif slot[0] == 'day':
            return self.grid.itemAtPosition(slot[1] // 7, slot[1] % 7).widget().get_panel_widget()
        else:
            raise Exception("No such slot")

    def day_to_cell(self, day: int) -> tuple[int, int]:
        first = QDate(self.year_edit.value(), self.month_edit.value(), 1)
        offset = first.dayOfWeek() % 7
        true_day = day - 1 + offset
        return true_day // 7, true_day % 7

    def generate_month(self):
        date = QDate(self.year_edit.value(), self.month_edit.value(), 1)
        self.month_label.setText(date.toString("MMMM yyyy"))
        updates_dict = {("day", x): None for x in range(42)}
        for i in range(date.daysInMonth()):
            id_str = self.name + "/" + date.addDays(i).toString("d-MMM-yyyy")
            cell = self.day_to_cell(i + 1)
            idx = cell[0] * 7 + cell[1]
            if self.manager.type_of_panel(id_str) is None:
                self.manager.invent_panel(id_str, self.daily_type.get_panel_widget().name)
            updates_dict[("day", idx)] = id_str
        self.pass_to_db(slots=updates_dict)