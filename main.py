#!/usr/bin/env python
# coding=utf-8


import math
import os
import sys
import time
from datetime import datetime
from multiprocessing import Process

import cv2
import dlib
import numpy as np
import serial
import serial.tools.list_ports
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from mainwindow import Ui_MainWindow as ui_

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("face/shape_predictor_68_face_landmarks.dat")
facerec = dlib.face_recognition_model_v1(
    "face/dlib_face_recognition_resnet_model_v1.dat"
)


class Locker:
    def __init__(self, num=6):

        self._lockerList = []
        for _ in range(num):
            self._lockerList.append({"ID": 0})

    # 比较两个“128向量”的欧式距离
    def _return_euclidean_distance(self, face_vector_0, face_vector_1):

        face_vector_0 = np.array(face_vector_0)

        face_vector_1 = np.array(face_vector_1)

        tem = np.sqrt(np.sum(np.square(face_vector_0 - face_vector_1)))

        # print(tem)

        return tem

    def have_free_item(self):
        for i in range(len(self._lockerList)):
            if self._lockerList[i]["ID"] == 0:
                return True, i
        return False, 0

    def set_id(self, i, id):
        self._lockerList[i]["ID"] = id

    def get_id(self, input_id):

        for i in range(len(self._lockerList)):

            compare = self._return_euclidean_distance(
                input_id, self._lockerList[i]["ID"]
            )

            if compare < 0.4:
                self.set_id(i, 0)

                return True, i, compare

        return False, 0, 0


class NewUiMainWindow(ui_):
    def init(self):

        global capture

        capture = cv2.VideoCapture(0)
        global timer_camera
        self.timer_camera = QtCore.QTimer()
        self.timer_camera.timeout.connect(self.open_camera)
        self.timer_camera.start(10)
        self.serial_camera = QtCore.QTimer()

        self.locker = Locker(6)

        facerec.compute_face_descriptor(np.zeros((150, 150, 3), np.uint8))

        self.ser = serial.Serial()
        self.port_check()

    def setupFunction(self):

        self.pushButton_open.clicked.connect(self._clear)

        self.pushButton_open_2.clicked.connect(self._open_file)

        self.pushButton_re.clicked.connect(self._re_face)

        self.pushButton_get.clicked.connect(self._get_face)

        # 打开串口按钮
        self.open_button.clicked.connect(self.port_open)

        # 关闭串口按钮
        self.close_button.clicked.connect(self.port_close)

        self.pushButton_re.setEnabled(False)
        self.pushButton_get.setEnabled(False)

    # 清除记录

    def _clear(self):
        try:
            with open("data.txt", "w") as f:  # “a"代表追加内容
                f.write("name     time     " + "\n")

        except Exception as e:
            print(e)

    # 打开文件

    def _open_file(self):
        try:
            os.system("gedit  data.txt")

        except Exception as e:
            print(e)

    def _get_face(self):

        try:

            ret = self.locker.have_free_item()

            if not ret[0]:
                QMessageBox.about(None, "当前存储柜已满", "请联系工作人员")
            else:

                global all_mat
                id = self.get_vector(all_mat)
                self.locker.set_id(ret[1], id)

                c_box = (
                    self.checkBox
                    if ret[1] == 0
                    else eval("self.checkBox_" + str(ret[1] + 1))
                )

                c_box.setCheckable(True)
                c_box.setEnabled(False)
                c_box.setChecked(True)

                # cv2.imencode('.jpg', all_mat)[1].tofile( "faceLib/"+str(str_name)+'.jpg')
                # print(os.getcwd())

                QMessageBox.about(None, "结果", str(ret[1] + 1) + "：记录成功")

                if self.ser.isOpen():
                    # input_s = ('open' + str(i) + '\r\n').encode('utf-8')
                    #self.ser.write((0xA1))
                    #self.ser.write((0xA2))
                    #self.ser.write((ret[1]))
                    send_list = [0xA1, 0xA2, ret[1]]
                    self.ser.write(bytes(send_list))
                    print('serial send')
                with open("data.txt", "a") as f:  # “a"代表追加内容
                    f.write(
                        "储物柜存物:%d  " % (ret[1] + 1)
                        + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                        + "\n"
                    )

        except Exception as e:
            print(e)

    # 识别  打开该目录下的人脸文件逐个比较，如果在设定的阈值范围内则弹窗提示

    def _re_face(self):

        try:
            now_vector = self.get_vector(all_mat)  # 打开图片或摄像头图片

            ret = self.locker.get_id(now_vector)

            state, i, compare = ret

            if state:
                print("compare:" + str(compare))
                with open("data.txt", "a") as f:  # “a"代表追加内容
                    f.write(
                        "储物柜取物:%d  " % (i + 1)
                        + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                        + "\n"
                    )

                c_box = (
                    self.checkBox
                    if ret[1] == 0
                    else eval("self.checkBox_" + str(ret[1] + 1))
                )

                c_box.setCheckable(False)
                c_box.setEnabled(True)
                c_box.setChecked(False)

                if self.ser.isOpen():
                    # input_s = ('open' + str(i) + '\r\n').encode('utf-8')
                    send_list = [0xA1, 0xA2,i]
                    self.ser.write(bytes(send_list))

                QMessageBox.about(
                    None, "人脸识别结果:", "\n        识别到储物柜%d号        \n " % (i + 1)
                )

            else:
                QMessageBox.about(None, "人脸识别结果:", "\n        没有对应结果            \n ")

        except Exception as e:
            print(e)

    # 利用dlib_face_recognition_resnet_model_v1.dat得到人脸128向量特征，参考http://dlib.net/

    def get_vector(self, frame):

        tem = detector(frame, 1)

        face_vector = 0

        if len(tem) > 0:

            shape = predictor(frame, tem[0])

            face_vector = facerec.compute_face_descriptor(frame, shape)

        return face_vector

    # 比较两个“128向量”的欧式距离
    def return_euclidean_distance(self, face_vector_0, face_vector_1):

        face_vector_0 = np.array(face_vector_0)

        face_vector_1 = np.array(face_vector_1)

        tem = np.sqrt(np.sum(np.square(face_vector_0 - face_vector_1)))

        # print(tem)

        return tem

    def port_check(self):

        self.open_button.setEnabled(False)

        # 检测存在的串口
        self.Com_Dict = {}
        port_list = list(serial.tools.list_ports.comports())
        self.comboBox.clear()
        for port in port_list:
            self.Com_Dict["%s" % port[0]] = "%s" % port[1]
            self.comboBox.addItem(port[0])
        if len(self.Com_Dict) == 0:
            QMessageBox.critical(None, "请注意", "未检测到串口")
        else:
            self.open_button.setEnabled(True)

    # 打开串口

    def port_open(self):
        self.ser.port = self.comboBox.currentText()
        self.ser.baudrate = 115200
        self.ser.bytesize = 8
        self.ser.stopbits = 1
        #self.ser.parity = "N"

        try:
            self.ser.open()
        except:
            QMessageBox.critical(None, "请注意", "串口打开失败")
            return None

        if self.ser.isOpen():
            self.open_button.setEnabled(False)
            self.close_button.setEnabled(True)

    # 关闭串口

    def port_close(self):
        try:
            self.ser.close()
        except:
            pass
        self.open_button.setEnabled(True)
        self.close_button.setEnabled(False)

    def clamp(self, n, minn, maxn):
        return max(min(maxn, n), minn)

    def open_camera(self):

        try:
            ret, frame = capture.read()

            show_mat = frame.copy()
            if ret:
                frame = cv2.resize(frame, (640, 480))
                face_number = detector(frame, 0)

                if len(face_number) > 0:

                    global all_mat

                    # all为全局变量，为选择的媒体或摄像头的内容
                    all_mat = frame

                    self.pushButton_re.setEnabled(True)  # 有人脸时开启识别按钮使能
                    self.pushButton_get.setEnabled(True)

                    for k, d in enumerate(face_number):

                        # 绘制矩形框
                        show_mat = cv2.rectangle(
                            show_mat,
                            tuple([d.left(), d.top()]),
                            tuple([d.right(), d.bottom()]),
                            (0, 255, 255),
                            2,
                        )
                        self.clamp(d.left(), 1, show_mat.shape[1] - 1)
                        self.clamp(d.right(), 1, show_mat.shape[1] - 1)
                        self.clamp(d.top(), 1, show_mat.shape[0] - 1)
                        self.clamp(d.bottom(), 1, show_mat.shape[0 - 1])

                        # print(show_mat.shape)

                show_mat = cv2.cvtColor(show_mat, cv2.COLOR_BGR2RGB)
                self.label.setScaledContents(True)  # 设置适应窗口

                showImage = QtGui.QImage(
                    show_mat.data,
                    show_mat.shape[1],
                    show_mat.shape[0],
                    show_mat.shape[1] * 3,
                    QtGui.QImage.Format_RGB888,
                )

                self.label.setPixmap(QPixmap.fromImage(showImage))

        except Exception as e:

            print("---异常---：", e)


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)

    MainWindow = QtWidgets.QMainWindow()

    ui = NewUiMainWindow()

    ui.setupUi(MainWindow)

    ui.init()

    ui.setupFunction()  # 连接函数初始化

    MainWindow.show()  # 显示窗口

    sys.exit(app.exec_())
