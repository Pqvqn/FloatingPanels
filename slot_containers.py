from PySide6.QtCore import QSize
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget, QScrollArea, QHBoxLayout

from panel_widget import PanelWidget


class SlotContainer(QFrame):
    """
    Base class for slot containers that hold subpanels.
    """

    def __init__(self, parent_panel: PanelWidget, slot_name: str, allowed_types: set = None, drags=True, drops=True):
        super(SlotContainer, self).__init__()
        self.parent_panel = parent_panel
        self.slot_name = slot_name  # Name used to reference these slots within the database
        self.allowed_types = allowed_types  # Types of panels allowed to fill this slot
        self.drops = drops  # Whether panels can be dropped into this slot
        self.drags = drags  # Whether panels can be dragged out of this slot
        self.setFrameStyle(QFrame.Panel | QFrame.Plain)

    def update_from(self, idx_to_id: dict[tuple[str, int], str | None]):
        """
        Apply updates listed under this container's name to the container

        :param idx_to_id: Dictionary of slot identifiers to the new value they must have. None indicates removal
        """
        raise Exception("Update not implemented in base class")

    def can_accept(self, panelid: str) -> bool:
        """
        Returns whether the given panelid can be added to this panel by the user

        :param panelid: ID to check for acceptance
        :return: Whether the ID can be added
        """
        return self.drops and (self.allowed_types is None
                               or self.parent_panel.manager.type_of_panel(panelid) in self.allowed_types)


class SingleContainer(SlotContainer):
    """
    Type of container that holds a single panel of a specified set of types.
    """

    def __init__(self, parent_panel: PanelWidget, slot_name: str, **kwargs):
        super(SingleContainer, self).__init__(parent_panel, slot_name, **kwargs)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        self.setAcceptDrops(True)

    def sizeHint(self) -> QSize():
        return QSize(40, 20)

    def get_panel_widget(self) -> PanelWidget | None:
        """
        Return the widget held in the container

        :return: Widget in the container, or None if it is empty
        """
        if self.layout.count() == 0:
            return None
        else:
            return self.layout.itemAt(0).widget()

    def dragEnterEvent(self, e):
        # Accept drags with text, as these hold panel id
        # Check that the id is allowed
        if e.mimeData().hasText() and self.can_accept(e.mimeData().text()):
            e.accept()

    def dropEvent(self, e):
        panelid = e.mimeData().text()

        # Check if this drop can be accepted
        if not self.can_accept(panelid):
            return

        # Request addition from parent
        self.parent_panel.pass_to_db(slots={(self.slot_name, 0): panelid})

        # Confirm the drop
        e.accept()

    def request_removal(self):
        """
        Requests that the parent remove the panel from this container
        """
        # Request removal from parent
        self.parent_panel.pass_to_db(slots={(self.slot_name, 0): None})

    def update_from(self, idx_to_id: dict[tuple[str, int], str | None]):
        key = (self.slot_name, 0)
        # Search in update dict for the key
        if key in idx_to_id:
            panelid = idx_to_id[key]
            if panelid is None:
                # Remove from layout if indicated
                wid = self.get_panel_widget()
                self.layout.removeWidget(wid)
                wid.setParent(None)

            else:
                # Check if there's already a panel in this slot before adding new one
                if self.get_panel_widget() is not None:
                    # Remove current from layout to make room
                    wid = self.get_panel_widget()
                    self.layout.removeWidget(wid)
                    wid.setParent(None)

                # Create widget and add to layout if indicated
                new_widget = self.parent_panel.make_from_db(panelid)
                new_widget.request_remove.connect(lambda x: self.request_removal())
                # If dragging out is disabled, lock the panel in
                if not self.drags:
                    new_widget.lock()
                self.layout.addWidget(new_widget)


class ListContainer(SlotContainer):
    """
    Type of container that holds a rearrangeable list of panels.
    """

    def __init__(self, parent_panel: PanelWidget, slot_name: str, horizontal=False, **kwargs):
        super(ListContainer, self).__init__(parent_panel, slot_name, **kwargs)

        # List can either grow horizontally or vertically
        self.horizontal = horizontal
        if horizontal:
            self.container_layout = QHBoxLayout()
            self.container_layout.setAlignment(Qt.AlignLeft)
        else:
            self.container_layout = QVBoxLayout()
            self.container_layout.setAlignment(Qt.AlignTop)
        container = QWidget()
        container.setLayout(self.container_layout)
        scroll = QScrollArea()
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        layout = QVBoxLayout()
        layout.addWidget(scroll)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.setAcceptDrops(True)

    def num_entries(self) -> int:
        """
        Number of panel widgets in this list.

        :return: Count of panel widgets in this list layout
        """
        return self.container_layout.count()

    def panel_widget_at(self, idx) -> PanelWidget:
        """
        Returns panel widget found at a position in the list

        :param idx: Index to find panel at
        :return: Panel widget in list
        """
        return self.container_layout.itemAt(idx).widget()

    def update_from(self, idx_to_id: dict[tuple[str, int], str | None]):

        # First: skip first few widgets until one needs to be changed. Then remove all the remaining widgets
        # Removal is to simplify the update algorithm. The beginning widgets are excluded because, in the
        # common operations of addition and deletion, they will not change.
        existing_widgets = {}  # Widgets already in the layout that just need to be moved
        do_remove = False  # Switches to true when widgets must start being removed
        removed_order = []  # Original order of removed widgets, in case they aren't replaced
        insert_idx = -1  # Index that new widgets must start inserting relative to
        for idx in range(self.container_layout.count()):
            # Iterate through widgets in layout in order
            if not do_remove and (self.slot_name, idx) in idx_to_id.keys():
                # If this is the first slot receiving an update, start removing now
                do_remove = True
                insert_idx = idx
            if do_remove:
                # Mark widget removed, as an update has already occurred earlier in the list
                wid = self.panel_widget_at(idx)
                existing_widgets[wid.name] = wid
                removed_order.append(wid)

        # Remove the widgets from the layout
        for wid in removed_order:
            self.container_layout.removeWidget(wid)
            wid.setParent(None)

        # Default to inserting updates at the end, if no slots were overwritten
        if insert_idx < 0:
            insert_idx = self.container_layout.count()

        unaddressed = {x for x in idx_to_id.keys() if x[0] == self.slot_name}  # Set of slots that still need changes
        new_idx = insert_idx  # Tracks list as it is iterated for updates, starting at the removal point
        # Iterate list positions
        while len(unaddressed) > 0:
            slot = (self.slot_name, new_idx)
            if slot in idx_to_id.keys():
                # If this slot has an update, put the panel in its place
                new_panelid = idx_to_id[slot]
                if new_panelid is None:
                    # Panel was removed and no replacement is needed
                    pass
                elif new_panelid not in existing_widgets.keys():
                    # New panel widget must be created and inserted from database
                    new_widget = self.parent_panel.make_from_db(new_panelid)
                    new_widget.request_remove.connect(self.request_removal)
                    if not self.drags:
                        new_widget.lock()
                    self.container_layout.insertWidget(new_idx, new_widget)
                else:
                    # Panel was already in the container; add its widget back at new position
                    wid = existing_widgets.pop(new_panelid)
                    self.container_layout.insertWidget(new_idx, wid)

                unaddressed.remove(slot)
            elif new_idx - insert_idx < len(removed_order):
                # If slot has no update, put its original widget back in
                self.container_layout.insertWidget(new_idx, removed_order[new_idx - insert_idx])
            else:
                # Exception raised when insertions to end of list skip an index
                raise Exception("Index was skipped over in list slot")
            new_idx += 1

    def request_removal(self, w: PanelWidget):
        """
        Handles panel widgets getting closed by the user and requiring removal from this list

        :param w: Widget that wants to be removed
        """
        updates = {}  # Dictionary of slot updates to pass to manager
        # Iterate over all widgets after the removal point
        for i in range(self.container_layout.indexOf(w)+1, self.container_layout.count()):
            # Add update to shift each widget after removal point one spot earlier
            updates[(self.slot_name, i-1)] = self.panel_widget_at(i).name
        # Delete the last slot, as the length of the list has reduced by one
        updates[(self.slot_name, self.container_layout.count() - 1)] = None
        # Pass changes to manager
        self.parent_panel.pass_to_db(slots=updates)

    def request_addition(self, panelid: str, idx: int):
        """
        Asks the manager to add a new panel to the list.

        :param panelid: ID of panel to be inserted
        :param idx: Index to insert at
        """
        # List of updates to pass to the manager
        updates = {(self.slot_name, idx): panelid}
        # Iterate over all widgets after the removal point
        for i in range(idx, self.container_layout.count()):
            # Add update to shift each widget after insertion one spot later
            updates[(self.slot_name, i+1)] = self.panel_widget_at(i).name
        # Pass changes to manager
        self.parent_panel.pass_to_db(slots=updates)

    def dragEnterEvent(self, e):
        # Accept drags with text, as these hold panel id
        # Check that the id is allowed
        if e.mimeData().hasText() and self.can_accept(e.mimeData().text()):
            e.accept()

    def dropEvent(self, e):
        pos = e.pos()
        added = False  # Marks whether insertion index was found inside of the list
        panelid = e.mimeData().text()

        # Check if this drop can be accepted
        if not self.can_accept(panelid):
            return

        # Check each position to find index
        for n in range(self.container_layout.count()):
            w = self.panel_widget_at(n)
            # Check if drop point was on this widget
            # Calculation depends on whether list is horizontal or vertical
            if self.horizontal:
                at_index = pos.x() < w.x() + w.size().width()
            else:
                at_index = pos.y() < w.y() + w.size().height()

            if at_index:
                # If so, insert in place, shifting old widget later
                self.request_addition(panelid, n)
                added = True
                break
        # If no position is found, add to end of list
        if not added:
            self.request_addition(panelid, self.container_layout.count())
        # Confirm the drop
        e.accept()
