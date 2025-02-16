import sys
import argparse
from window_manager import WindowManager

parser = argparse.ArgumentParser(prog='PanelsOpener',
                                 description='Open panels in new windows using references to entries in database')
parser.add_argument('panelid', help="ID of the panel to open in a new window.")
parser.add_argument('--create_new', '-c', help="Type of module to create and open a new instance of.")

args = parser.parse_args()

if __name__ == '__main__':
    if args.create_new is not None:
        # If creating a new panel, pass along its type
        arg_tuple = (args.panelid, args.create_new)
    else:
        arg_tuple = (args.panelid,)

    # Attempt to start the application server on a certain name. Passes args to server if one already exists
    app = WindowManager("FLOATINGPANELSv0.1", "./panels.sqlite", sys.argv)
    app.try_connect(arg_tuple)

    # Only execute GUI app if it has been chosen to be the server
    if app.running > 0:
        sys.exit(app.exec())
    else:
        sys.exit(0)
