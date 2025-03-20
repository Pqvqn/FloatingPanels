import sqlite3
import types

from PySide6.QtCore import QMimeData, QPoint
from PySide6.QtGui import QDrag, QPixmap, Qt, QCursor

from panel_widget import PanelWidget
from panels import *
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

    # Types of panels currently able to be created.
    PANEL_TYPES = {shelves.PShelfVert, shelves.PShelfHoriz, simple_inputs.PTask, simple_inputs.PNumber,
                   types.PType, shelves.PFootnote, types.PCreator, types.PFinder, time_manage.PCalendar,
                   shelves.PMatrix}
    # TODO: Load panel types automatically from installed scripts

    def __init__(self, sid, db_path, *argv):
        super(WindowManager, self).__init__(sid, *argv)

        self.db_path = db_path
        self.db_con = None
        self.db_cur = None
        self.windows = None
        self.panel_classes = None
        self.drag_target = None
        self.drag_panelid = None

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

    def invent_panel(self, panelid: str, panel_type: str):
        """
        Adds the panelid to the database under the given type.

        :param panelid: ID to create panel under
        :param panel_type: Type of new panel
        """
        # Reject blank string as name
        if panelid == "":
            raise Exception("Cannot make panels with no name")

        # Get class for panel type if given
        panel_class = self.panel_classes[panel_type]
        if not panel_class.allow_user_creation():
            raise Exception("User cannot create new panels of this type")

        # Initiate database for this type if it isn't already initialized
        self.try_init_type_in_db(panel_type)

        # Add to metadata table
        self.db_cur.execute("INSERT INTO Panels VALUES (?, ?)", (panelid, panel_type))
        if len(panel_class.attributes()) > 0:
            # If the type has attributes, add this panel's attributes to the type's table
            self.db_cur.execute("INSERT INTO {}(panelid) VALUES (?)".format(panel_type), (panelid,))
        self.db_con.commit()

        for pair in panel_class.default_attributes().items():
            # Update this panel's row in its type's table to the default types
            self.db_cur.execute("UPDATE {} SET {}=? WHERE panelid=?".format(panel_type, pair[0]), (pair[1], panelid))
            self.db_con.commit()

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
            # If type given, must add panel to database
            self.invent_panel(panelid, panel_type)

        # Find panel's metadata in the database
        res = self.db_cur.execute("SELECT module FROM Panels WHERE id = ?", (panelid,))
        entry = res.fetchone()
        panel_class = self.panel_classes[entry[0]]

        # Form the new widget
        widget = panel_class(panelid, self)

        # Initialize all of the panel's values from the database
        widget.init_from_dicts(self.get_attributes_dict(widget), self.get_slots_dict(widget))

        return widget

    def create_window(self, params: tuple[str, str] | tuple[str], position: QPoint = None):
        """
        Forms a new panel widget and opens it as a floating window.

        :param params: Parameters describing how to open the window. First index represents panel id.
                       If a second index is given, it represents the panel type to create a new panel
                       for.
        :param position: Point on screen that window should be created at
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

        # Let window prepare anything that is unique to windows
        widget.prepare_window()

        # Open as window, as now parent is set
        widget.show()

        if position is not None:
            # Position window at proper location
            widget.setGeometry(position.x(), position.y(), widget.width(), widget.height())



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

    def try_init_type_in_db(self, panel_type: str):
        """
        If needed, create a database table and type panel for the panel's type.

        :param panel_widget: Widget whose type should have its initialization attempted.
        """

        res = self.db_cur.execute("SELECT * from Panels WHERE module='type' and id=?", (panel_type,))
        # Type already initialized in table, don't need to add it
        if res.fetchone() is not None:
            return

        # Add a panel of type 'type' to represent this type
        self.db_cur.execute("INSERT INTO Panels VALUES (?, ?)", (panel_type, 'type'))
        self.db_con.commit()

        # Only needs a table if the type has attributes
        attributes = self.panel_classes[panel_type].attributes()
        if len(attributes) > 0:
            table = panel_type
            # Only add table if it doesn't already exist. This line also validates the SQL
            res = self.db_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if res.fetchone() is None:
                # Create the table
                self.db_cur.execute("CREATE TABLE {} (panelid TEXT PRIMARY KEY)".format(table))
                # Add all attributes as columns
                for pair in attributes.items():
                    self.db_cur.execute("ALTER TABLE {} ADD {} {}".format(table, pair[0], pair[1]))
                self.db_con.commit()

    def type_of_panel(self, panelid: str) -> str | None:
        """
        Returns the type associated with a panel id.

        :param panelid: ID of the panel to query
        :return: Type of the panel as stored in the database. None if absent from db
        """
        res = self.db_cur.execute("SELECT module FROM Panels WHERE id=?", (panelid,))
        fetched = res.fetchone()
        return fetched['module'] if fetched is not None else None

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
            return None

    def get_slots_dict(self, panel_widget: PanelWidget) -> dict[tuple[str, int], str | None]:
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
            return None

    def update_panel(self, panel_widget: PanelWidget, attribute_dict: dict[str, object],
                     slots_dict: dict[tuple[str, int], str | None]):
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

    def query_panels(self, match_type: str) -> list[str]:
        """
        Returns a list of panelids that matched the given query.

        :param match_type: The type of panel to query the list for
        :return: List of IDs for panels that match the query
        """
        res = self.db_cur.execute("SELECT id FROM Panels WHERE module=?", (match_type,))
        rows = res.fetchall()
        return [x['id'] for x in rows]

    def drag_panel(self, panel: PanelWidget, action: Qt.DropActions):
        """
        Initiate a drag of the given panel.
        :param panel: Panel widget to be dragged
        :param action: Type of action for the drag
        """
        # Create the drag object
        drag = QDrag(self)
        # Track current drag. Needed for window creation

        # Create an image of the panel to follow the cursor
        pixmap = QPixmap(panel.size())
        panel.render(pixmap)
        drag.setPixmap(pixmap)

        # Pass the panel id as MIME data
        mime = QMimeData()
        drag.setMimeData(mime)
        mime.setText(panel.name)

        # Set receiver for when the drag ends
        drag.targetChanged.connect(self.set_drag_target)
        drag.destroyed.connect(lambda x: self.drag_ended())
        self.drag_target = None
        self.drag_panelid = panel.name

        if action == Qt.MoveAction:
            # Make original window invisible so it looks like it's being moved
            # Using hide() would mess up the drag image
            panel.setWindowOpacity(0)

        # Start drag
        drag.exec_(action)

    def set_drag_target(self, target):
        """
        Track the location of the drag target as it changes. Needed to respond
        to out-of-window drops

        :param target: The widget currently set to receive the drop. None if outside all slots
        """
        self.drag_target = target

    def drag_ended(self):
        """
        Responds to the current drag ending. Creates a new window if the drag wasn't accepted
        by a slot.
        """

        if not self.drag_target:
            # Create new window at mouse position if dropped outside slot
            self.create_window((self.drag_panelid,), position=QCursor.pos())

        self.drag_target = None
        self.drag_panelid = None