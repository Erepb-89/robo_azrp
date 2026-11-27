"""Start the merged UI without hardware. Install PyQt5, then run this file."""
import os
import sys
from pathlib import Path

from PyQt5 import QtWidgets
from PyQt5.QtCore import QDir

from ui.main_window import MainOperWindow


def main():
    project_dir = Path(__file__).resolve().parent
    ui_dir = project_dir / "ui"
    # Some original stylesheet URLs are relative to the project root.
    os.chdir(project_dir)

    app = QtWidgets.QApplication(sys.argv)
    QDir.setSearchPaths("azrp", [str(ui_dir)])
    app.setStyleSheet((ui_dir / "style.qss").read_text(encoding="utf-8"))
    window = MainOperWindow()  # No RobotController, queues, robot threads, or network.
    window.setWindowTitle("АЗРП — автономный просмотр UI (без оборудования)")
    window.showFullScreen()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
