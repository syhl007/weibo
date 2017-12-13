# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'test.ui'
#
# Created by: PyQt5 UI code generator 5.9.1
#
# WARNING! All changes made in this file will be lost!
import time
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal

from tools import collect_weibo_data, real_friend
from ui import Msg_UI


class UI(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(370, 162)
        self.get_pic = QtWidgets.QCheckBox(Dialog)
        self.get_pic.setGeometry(QtCore.QRect(30, 50, 221, 20))
        self.get_pic.setObjectName("get_pic")
        self.name = QtWidgets.QLineEdit(Dialog)
        self.name.setGeometry(QtCore.QRect(80, 20, 201, 20))
        self.name.setObjectName("name")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(23, 20, 61, 21))
        self.label.setObjectName("label")
        self.friendtest = QtWidgets.QCheckBox(Dialog)
        self.friendtest.setGeometry(QtCore.QRect(30, 80, 241, 16))
        self.friendtest.setObjectName("friendtest")
        self.startButton = QtWidgets.QPushButton(Dialog)
        self.startButton.setGeometry(QtCore.QRect(250, 120, 75, 23))
        self.startButton.setObjectName("pushButton")
        self.verticalLayoutWidget = QtWidgets.QWidget(Dialog)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(0, 100, 261, 61))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "微博数据下载器"))
        self.get_pic.setText(_translate("Dialog", "需要下载图片？（很慢啊。。。）"))
        self.label.setText(_translate("Dialog", "微博名："))
        self.friendtest.setText(_translate("Dialog", "密切好友分析（测试中。。。。。）"))
        self.startButton.setText(_translate("Dialog", "go"))


class MyUI(QtWidgets.QWidget, UI):
    def __init__(self):
        super(MyUI, self).__init__()
        self.setupUi(self)
        self.child = Msg_UI.MyUI()
        self.startButton.clicked.connect(self.click_event)

    def click_event(self):
        self.startButton.setEnabled(False)
        self.get_pic.setEnabled(False)
        self.friendtest.setEnabled(False)
        self.name.setEnabled(False)
        self.verticalLayout.addWidget(self.child)          #添加子窗口
        self.child.show()
        self.thread = WorkThread(name=self.name.text(), pic_flag=self.get_pic.isChecked(), fr=self.friendtest.isChecked())
        self.thread.msg_trigger.connect(self.refresh)
        self.thread.trigger.connect(self.done)
        self.thread.start()

    def refresh(self, text=None):
        self.child.label.setText(text)

    def done(self):
        self.child.label.setText("[完毕]")
        self.startButton.setEnabled(True)
        self.get_pic.setEnabled(True)
        self.friendtest.setEnabled(True)
        self.name.setEnabled(True)


class WorkThread(QThread):
    msg_trigger = pyqtSignal(str)
    trigger = pyqtSignal()
    def __init__(self, name, pic_flag, fr):
        super(WorkThread, self).__init__()
        self.name = name
        self.pic_flag = pic_flag
        self.fr = fr

    def run(self):
        try:
            collect_weibo_data(name=self.name, pic_flag=self.pic_flag, msg_trigger=self.msg_trigger.emit)
            if self.fr:
                real_friend(name=self.name)
        except Exception as e:
            self.msg_trigger.emit(e.args[0]+"\n[3s后返回上一级]")
            time.sleep(3)
        self.trigger.emit()


