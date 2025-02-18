from PySide6.QtCore import QEvent, Signal
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QWidget, QFrame, QApplication


class PanelWidget(QFrame):
    """
    Base class for all widgets that represent panels.

    Panels are designed to run as either floating windows or as widgets
    embedded within a slot container in another panel widget. Panel
    widgets cannot update themselves and must instead pass user inputs
    to the window manager and process the updates it receives from the
    manager.
    """

    # Occurs when this widget is a window and is closed. Pass itself and its id
    closed = Signal(QWidget, str)
    # Occurs when the user requests that this widget be removed from its parent. Pass itself
    request_remove = Signal(QWidget)

    def __init__(self, name: str, manager, system_authority=False):
        super(PanelWidget, self).__init__()

        self.setFrameStyle(QFrame.Panel | QFrame.Plain)

        self.manager = manager  # Window manager for this widget
        self.name = name
        self.locked = False  # Whether this panel can be removed from its slot
        self.setWindowTitle(self.name)

        self.installEventFilter(self)
        # Initiate database for this type if it isn't already initialized
        self.manager.try_init_type_in_db(self)

        self.dragStartPosition = None

    @staticmethod
    def panel_type() -> str:
        """
        Gets string representing the type for database storage
        :return: String name of this panel type
        """
        raise NotImplementedError("Tried to get type of panels base class")

    @staticmethod
    def attributes() -> dict[str, str]:
        """
        Gets dictionary of attributes to be formed in the database table
        :return: Dictionary of attribute names and the SQLite definition
        """
        return {}

    @staticmethod
    def default_attributes() -> dict[str, object]:
        """
        Gets dictionary of initial attribute values for a new panel
        :return: Dictionary of attribute names and the default value
        """
        return {}

    @staticmethod
    def allow_user_creation() -> bool:
        """
        Boolean representing whether the user is allowed to create
        new instances of this type
        :return: True if user should be allowed to create this type
        """
        return True

    def eventFilter(self, source, event: QEvent) -> bool:
        # Announce when this panel is deleted by user
        if event.type() == QEvent.DeferredDelete or event.type() == QEvent.Close:
            self.closed.emit(self, self.name)
        # Pass event to parent class
        return super(QWidget, self).eventFilter(source, event)

    def init_from_dicts(self, attributes: dict[str, object], slots: dict[tuple[str, int], str | None]):
        """
        Convenience method for initializing widget values from dictionaries.

        :param attributes: Attributes to update widget with.
        :param slots: Slots to update widget with.
        """
        if attributes is not None:
            self.fill_attributes(attributes)
        if slots is not None:
            self.fill_slots(slots)

    def fill_attributes(self, attrs: dict[str, object]):
        """
        Fills attributes from update dictionary.
        :param attrs: Dictionary of updated values for attribute names
        """
        raise NotImplementedError("Tried filling attributes in base class")

    def fill_slots(self, slots: dict[tuple[str, int], str | None]):
        """
        Fills slots from update dictionary.
        :param slots: Dictionary of updated subpanels for slots. None indicates subpanel in slot must be removed.
        """
        raise NotImplementedError("Tried filling slots in base class")

    def pass_down_changes(self, path_to_panel: list[tuple[str, int]], attribute_dict: dict[str, object],
                          slots_dict: dict[tuple[str, int], str | None]):
        """
        Receive and pass on changes to this widget or its subpanels.

        :param path_to_panel: List of tuples representing the next slot to pass changes down to
        :param attribute_dict: Dictionary of changes to the final panel's attributes
        :param slots_dict: Dictionary of changes to the final panel's slots
        """
        if len(path_to_panel) == 0:
            # If this is the destination, apply all changes
            if attribute_dict is not None and len(attribute_dict) > 0:
                self.fill_attributes(attribute_dict)
            if slots_dict is not None and len(slots_dict) > 0:
                self.fill_slots(slots_dict)
        else:
            # If this isn't the destination, move forward a step and pass that widget the rest of the path
            next_step = path_to_panel[0]
            self.get_slot_widget(next_step).pass_down_changes(path_to_panel[1:], attribute_dict, slots_dict)

    def pass_to_db(self, attributes: dict[str, object] = None, slots: dict[tuple[str, int], str | None] = None):
        """
        Wrapper to pass updates to the manager to change the dictionary and all widgets.

        :param attributes: Dictionary of attribute updates
        :param slots: Dictionary of slot updates
        """
        # Pass changes to manager
        self.manager.update_panel(self, attributes, slots)

    def make_from_db(self, panelid: str):
        """
        Wrapper to get a new panel widget from the manager.

        :param panelid: ID of the panel to be created
        :return: The widget, as formed by the manager
        """
        return self.manager.make_panel_widget(panelid)

    def get_slot_widget(self, slot: tuple[str, int]) -> 'PanelWidget':
        """
        Returns the panel widget current occupying a slot.

        :param slot: Name and number of slot to check
        :return: PanelWidget occupying that slot
        """
        raise NotImplementedError("Get slot not implemented for this class")

    def lock(self, make_locked=True):
        """
        Sets lock value of the panel, determining whether it can be moved from its slot.

        :param make_locked: Whether the panel should be locked
        """
        self.locked = make_locked

    def mousePressEvent(self, e):
        b = e.buttons()
        # Check for drag only if valid action is performed
        if (not self.locked and b == Qt.LeftButton) or b == Qt.RightButton:
            # Track beginning of mouse hold and only start drag when it goes far enough
            self.dragStartPosition = e.pos()

    def mouseReleaseEvent(self, e):
        # Reset drag start once released
        self.dragStartPosition = None

    def mouseMoveEvent(self, e):
        b = e.buttons()

        # Only process dragging while button held
        if not((not self.locked and b == Qt.LeftButton) or b == Qt.RightButton):
            return

        # Don't do drag if start position not set
        if self.dragStartPosition is None:
            return

        # Only process dragging once the mouse has moved far enough
        if (e.pos() - self.dragStartPosition).manhattanLength() < QApplication.startDragDistance() * 6:
            return

        if b == Qt.LeftButton:
            # Left click for Move: remove from parent
            self.request_remove.emit(self)
            self.manager.drag_panel(self, Qt.MoveAction)

        elif b == Qt.RightButton:
            # Right click for Copy: keep within container
            self.manager.drag_panel(self, Qt.CopyAction)
