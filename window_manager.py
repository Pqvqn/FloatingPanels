import sqlite3

from PySide6.QtCore import QMimeData
from PySide6.QtGui import QDrag, QPixmap, Qt

from panels.demo_panels import *
from single_application import SingleApplication


def open_db(filepath: str) -> sqlite3.Connection:
    """
    Opens connection to the database and initializes it if not already initialized.

    :param filepath: Path to file that database is already at or should be placed at.
    :return: SQLite connection to the database.
    """
    con = sqlite3.connect(filepath)
    # Create table for panel metadata
    con.execute("CREATE TABLE IF NOT EXISTS Panels (id TEXT PRIMARY KEY, module TEXT)")
    # Create table for slot hierarchy
    con.execute("CREATE TABLE IF NOT EXISTS Slots (parent TEXT REFERENCES Panels(id), slot_name TEXT NOT NULL, slot_num"
                " INTEGER, child TEXT REFERENCES Panels(id), PRIMARY KEY(parent, slot_name, slot_num))")
    con.row_factory = sqlite3.Row
    return con


class WindowManager(SingleApplication):
    """
    Central manager for every panels window.

    The window manager handles all databases accesses, creates all panels, and
    manages all currently open windows. As a SingleApplication, only one is
    able to exist on the OS at a time. Additional SingleApplications will pass
    their information to the original one and then close.
    """

    PANEL_TYPES = {PShelfVert, PShelfHoriz, PTask}  # Types of panels currently able to be created.
    # TODO: Load panel types automatically from installed scripts

    def __init__(self, sid, db_path, *argv):
        super(WindowManager, self).__init__(sid, *argv)

        self.db_path = db_path
        self.db_con = None
        self.db_cur = None
        self.windows = None
        self.panel_classes = None

        # Call init_manager when this object becomes the main application and server
        self.picked.connect(self.init_manager)
        # When a new instance of the program is launched, use its arguments to form a new window
        self.args_received.connect(self.create_window)

    def init_manager(self):
        """
        Initializes all values necessary for the manager.

        This method is called once this object is chosen as the main application.
        """
        self.db_con = open_db(self.db_path)
        self.db_cur = self.db_con.cursor()
        # Stores all open windows underneath their panel id. This is necessary so windows aren't garbage collected and
        # to allow panel updates to propagate to other windows.
        self.windows: dict[str, set[PanelWidget]] = {}
        # Stores all panel types by name
        self.panel_classes: dict[str, type] = {p.panel_type(): p for p in self.PANEL_TYPES}

    def make_panel_widget(self, panelid: str, panel_type: str = None) -> PanelWidget:
        """
        Creates a widget representing a panel.

        If no panel type is given, the panel id is used to load the panel from the database.
        If the type is given, a new panel is formed and added to the database.
        :param panelid: The id of the panel to form as a widget.
        :param panel_type: The type of panel to create and add to the database. If None, no new panel is created.
        :return: A new PanelWidget.
        """
        if panel_type is not None:
            # Get class for panel type if given
            panel_class = self.panel_classes[panel_type]
        else:
            # If type not given, find it as part of the panel's metadata in the database
            res = self.db_cur.execute("SELECT module FROM Panels WHERE id = ?", (panelid,))
            entry = res.fetchone()
            panel_class = self.panel_classes[entry[0]]

        # Form the new widget
        widget = panel_class(panelid, self)

        # If a new panel was created, add it to the database
        if panel_type is not None:
            # Add to metadata table
            self.db_cur.execute("INSERT INTO Panels VALUES (?, ?)", (panelid, panel_type))
            if len(panel_class.attributes()) > 0:
                # If the type has attributes, add this panel's attributes to the type's table
                self.db_cur.execute("INSERT INTO {}(panelid) VALUES (?)".format(panel_type), (panelid,))
            self.db_con.commit()

        # Initialize all of the panel's values from the database
        widget.init_from_dicts(self.get_attributes_dict(widget), self.get_slots_dict(widget))

        return widget

    def create_window(self, params: tuple[str, str] | tuple[str]):
        """
        Forms a new panel widget and opens it as a floating window.

        :param params: Parameters describing how to open the window. First index represents panel id.
                       If a second index is given, it represents the panel type to create a new panel
                       for.
        """
        # Form the widget
        widget = self.make_panel_widget(params[0], params[1] if len(params) > 1 else None)

        # Add the new window to the dictionary of windows
        if widget.name not in self.windows:
            self.windows[widget.name] = {widget}
        else:
            self.windows[widget.name].add(widget)

        # When window is manually closed, it must be removed from the dictionary
        widget.closed.connect(self.window_closed)
        # Delete widgets when a remove is requested. Happens when a drag is performed
        widget.request_remove.connect(lambda x: x.deleteLater())
        widget.show()

    def window_closed(self, window: PanelWidget, name: str):
        """
        Receives signal that a window has been closed.

        :param window: Window that was closed.
        :param name: Panelid of window that was closed.
        """
        # Remove the window from tracking dictionary
        self.windows[name].remove(window)
        # Remove set for this panel id if it is now empty
        if len(self.windows[name]) == 0:
            del self.windows[name]

    def try_create_panel_table(self, panel_widget: PanelWidget):
        """
        Creates database table for the panel widget's type if one is needed.

        :param panel_widget: Widget to create a new table for the type of.
        """

        # Only needs a table if the type has attributes
        attributes = panel_widget.attributes()
        if len(attributes) > 0:
            table = panel_widget.panel_type()
            # Only add table if it doesn't already exist. This line also validates the SQL
            res = self.db_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if res.fetchone() is None:
                # Create the table
                self.db_cur.execute("CREATE TABLE {} (panelid TEXT PRIMARY KEY)".format(table))
                # Add all attributes as columns
                for pair in attributes.items():
                    self.db_cur.execute("ALTER TABLE {} ADD {} {}".format(table, pair[0], pair[1]))
                self.db_con.commit()

    def get_attributes_dict(self, panel_widget: PanelWidget) -> dict[str, object]:
        """
        Retreive a dictionary of the panel's values for each of its type's attributes.

        :param panel_widget: Panel widget that needs attribute values.
        :return: Dictionary matching name of each attribute to its value for this panel. Empty if no attributes.
        """
        # Only fill dictionary if the type has attributes
        if len(panel_widget.attributes()) > 0:
            # Select row from the type's attribute table
            res = self.db_cur.execute("SELECT * FROM {} WHERE panelid = ?".format(panel_widget.panel_type()),
                                      (panel_widget.name,))
            row = res.fetchone()
            # Construct a dictionary from the row's column values
            return {k: row[k] for k in row.keys()}
        else:
            return {}

    def get_slots_dict(self, panel_widget: PanelWidget) -> dict[tuple[str, int], str]:
        """
        Retrieve a dictionary of all of the subpanels filling the slots for a panel.

        :param panel_widget: Panel widget that needs subpanels.
        :return: Dictionary of slot identifier to id of subpanel in that slot. Empty if none.
        """
        # Select slots from the slot table in the database
        res = self.db_cur.execute("SELECT * FROM Slots WHERE parent = ?", (panel_widget.name,))
        rows = res.fetchall()
        if len(rows) > 0:
            # Format rows into dictionary entries
            ret_dict = {(r['slot_name'], r['slot_num']): r['child'] for r in rows}
            return ret_dict
        else:
            return {}

    def update_panel(self, panel_widget: PanelWidget, attribute_dict: dict[str, object],
                     slots_dict: dict[tuple[str, int], str]):
        """
        Updates the panel based on attribute and slot changes.

        :param panel_widget: The widget that initiated these updates.
        :param attribute_dict: Dictionary of attribute names to their new values.
        :param slots_dict: Dictionary of slot identifiers (name and number) to the id of the subpanel now filling them,
                           or None if the subpanel must be deleted.
        """
        panelid = panel_widget.name
        # Update attributes
        if attribute_dict is not None:
            table = panel_widget.panel_type()
            for pair in attribute_dict.items():
                # Update this panel's row in its type's table
                self.db_cur.execute("UPDATE {} SET {}=? WHERE panelid=?".format(table, pair[0]), (pair[1], panelid))
                self.db_con.commit()
        # Update slots
        if slots_dict is not None:
            # Mark which slots must be deleted entirely
            deletes = [(panelid, x[0][0], x[0][1]) for x in slots_dict.items() if x[1] is None]
            # Mark which slots must have their value replaced
            updates = [(panelid, x[0][0], x[0][1], x[1]) for x in slots_dict.items() if x[1] is not None]
            # Run queries to delete and replace necessary slots
            self.db_cur.executemany("DELETE FROM Slots WHERE (parent, slot_name, slot_num) = (?,?,?)", deletes)
            self.db_cur.executemany("INSERT OR REPLACE INTO Slots VALUES(?,?,?,?)", updates)
            self.db_con.commit()
        # Pass updates to all windows containing this panel
        for window_id in self.windows.items():
            # Get list of paths within a specific window
            paths_to_panel = self.find_subpanel(window_id[0], panelid)
            for window in window_id[1]:
                for path in paths_to_panel:
                    # Pass changes to the window along with the path it must follow to find the panel
                    window.pass_down_changes(path[1:], attribute_dict, slots_dict)

    def find_subpanel(self, starting_point: str, target: str) -> list[list[tuple[str, int]]]:
        """
        Finds all paths from one panel down the slot hierarchy to another panel.

        :param starting_point: Panel to start navigating from
        :param target: Panel to search for
        :return: List of potential sequences of steps to take to find the target
        """
        # Run recursive query on the slot table to find all paths
        res = self.db_cur.execute("WITH RECURSIVE Paths AS ( \
                                    SELECT ? as name, ':0' as path \
                                    UNION ALL \
                                    SELECT Slots.child, Paths.path || '/' || Slots.slot_name || ':' || Slots.slot_num \
                                    FROM Slots JOIN Paths WHERE Slots.parent = Paths.name) \
                                    SELECT path FROM Paths WHERE name = ?", (starting_point, target))
        # Format query result as a list of lists of tuples
        return [[(step[:step.index(':')], int(step[step.index(':')+1:])) for step in path['path'].split("/")] for path
                in res.fetchall()]

    def drag_panel(self, panel: PanelWidget, action: Qt.DropActions):
        """
        Initiate a drag of the given panel.
        :param panel: Panel widget to be dragged
        :param action: Type of action for the drag
        """
        # Create the drag object
        drag = QDrag(self)

        # Create an image of the panel to follow the cursor
        pixmap = QPixmap(panel.size())
        panel.render(pixmap)
        drag.setPixmap(pixmap)

        # Pass the panel id as MIME data
        mime = QMimeData()
        drag.setMimeData(mime)
        mime.setText(panel.name)

        # Start drag
        drag.exec_(action)
