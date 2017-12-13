import csv
import os
import re
import time

import jieba
import requests
from PyQt5 import QtWidgets

from ui import Main_UI


if __name__ == "__main__":
    import sys
    try:
        app = QtWidgets.QApplication(sys.argv)
        myshow = Main_UI.MyUI()
        myshow.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(e)
pass
