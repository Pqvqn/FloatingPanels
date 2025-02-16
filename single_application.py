from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QByteArray, Signal
from PySide6.QtNetwork import QLocalSocket, QLocalServer


class SingleApplication(QApplication):
    """
    Defines a Qt Application that only runs one instance at a time.

    When a SingleApplication opens, it checks for other instances already running.
    If one exists, it connects to it and passes its arguments. If none do, it
    becomes the application.
    """

    # Signal emitted when this object becomes the application
    picked = Signal()
    # Signal emitted when this application receives arguments from an attempted instance
    args_received = Signal(tuple)
    # Separator used between arguments passed between instances
    SEPARATOR = ';;'

    def __init__(self, sid: str, *argv):
        super(SingleApplication, self).__init__(*argv)

        self.sid = sid  # Name to run the server on
        self.server = None
        self.in_socket = None
        self.pass_args = None

        self.running = 0  # 1 if running server, -1 if passing arguments, 0 if undecided

        # Create socket for connecting to server and register handlers
        self.out_socket = QLocalSocket()
        self.out_socket.errorOccurred.connect(self.not_found)
        self.out_socket.connected.connect(self.found)

    def try_connect(self, pass_args: tuple):
        """
        Try to connect to a server with the given arguments

        :param pass_args: Arguments to pass along to main application
        """
        self.pass_args = pass_args
        self.out_socket.connectToServer(self.sid)

    def found(self):
        """
        Handles case where an already-running server is found
        """
        # Encode arguments as data to pass
        full_str = self.SEPARATOR.join(self.pass_args)
        # Pass arguments to server
        self.out_socket.write(QByteArray(full_str.encode()))
        self.out_socket.waitForBytesWritten(1000)
        self.running = -1

    def not_found(self, err):
        """
        Handles case where no already-running server is found

        :param err: Error passed by socket
        """
        if err == QLocalSocket.ServerNotFoundError:
            # If no server, become the server
            self.server = QLocalServer()
            self.server.listen(self.sid)
            # Set up handlers and emit signals
            self.server.newConnection.connect(self.receive_connection)
            self.running = 1
            self.picked.emit()
            self.args_received.emit(self.pass_args)
        else:
            print(self.out_socket.errorString())

    def receive_connection(self):
        """
        Handles case where server receives data from a new instance
        """
        # Connect signals to respond when data is received
        self.in_socket = self.server.nextPendingConnection()
        self.in_socket.readyRead.connect(self.receive_message)

    def receive_message(self):
        """
        Handler for data received from new instance
        """
        # Receive and decode arguments passed
        msg = bytes(self.in_socket.readAll()).decode()
        msg_tuple = tuple(msg.split(self.SEPARATOR))
        # Disconnect from other instance
        self.in_socket.readyRead.disconnect(self.receive_message)
        # Announce the arguments
        self.args_received.emit(msg_tuple)
