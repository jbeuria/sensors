#adapted from https://brainflow.readthedocs.io/en/stable/Examples.html
import argparse
import logging

import pyqtgraph as pg
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter, FilterTypes, DetrendOperations
from pyqtgraph.Qt import QtGui, QtCore

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
class Graph:
    def __init__(self, board_shim,preset=0):
        self.board_id = board_shim.get_board_id()
        self.board_shim = board_shim
        self.preset=preset
        if(preset==0):
            self.channels = BoardShim.get_eeg_channels(self.board_id,preset)
        elif(preset==2):
            self.channels = BoardShim.get_ppg_channels(self.board_id,preset)

        self.sampling_rate = BoardShim.get_sampling_rate(self.board_id,preset)
        self.update_speed_ms = 200
        self.window_size = 4
        self.num_points = self.window_size * self.sampling_rate
        print(self.sampling_rate)

        self.app = QtGui.QApplication([])
        self.win = pg.GraphicsWindow(title='BrainFlow Plot', size=(800, 600))

        self._init_timeseries()

        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(self.update_speed_ms)
        QtGui.QApplication.instance().exec_()

    def _init_timeseries(self):
        self.plots = list()
        self.curves = list()
        for i in range(len(self.channels)):
            p = self.win.addPlot(row=i, col=0)
            #p.setColor(0,0,0)
            #p.setYRange(1000, 30000, padding=0)
            p.showAxis('left', True)
            p.setMenuEnabled('left', False)
            p.showAxis('bottom', True)
            p.setMenuEnabled('bottom', False)
            if i == 0:
                p.setTitle('TimeSeries Plot')
            self.plots.append(p)
            curve = p.plot(pen=pg.mkPen('b', width=2))
            self.curves.append(curve)

    def update(self):

        data = self.board_shim.get_current_board_data(self.num_points,self.preset)

        for count, channel in enumerate(self.channels):
            # plot timeseries
            if(self.preset==0):
                DataFilter.detrend(data[channel], DetrendOperations.CONSTANT.value)
                DataFilter.perform_bandpass(data[channel], self.sampling_rate, 3.0, 45.0, 2,
                                            FilterTypes.BUTTERWORTH.value, 0)
                DataFilter.perform_bandstop(data[channel], self.sampling_rate, 48.0, 52.0, 2,
                                            FilterTypes.BUTTERWORTH.value, 0)
                DataFilter.perform_bandstop(data[channel], self.sampling_rate, 58.0, 62.0, 2,
                                            FilterTypes.BUTTERWORTH.value, 0)
                
            self.curves[count].setData(data[channel].tolist())
            
        self.app.processEvents()

