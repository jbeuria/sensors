from time import time,sleep
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowPresets
import mne

class muse:
    def __init__(self,address,path="",boardId=BoardIds.MUSE_S_BOARD):

        self.brainflow_id=boardId
        params = BrainFlowInputParams()
        params.mac_address = address
        
        self.board = BoardShim(boardId, params)
        self.brainflow_id = boardId
        self.board.prepare_session()
        self.raw_data=[]
        
        if(boardId==BoardIds.MUSE_S_BOARD):
            print("adding ppg channel as well")
            self.board.config_board("p61")
        elif (boardId==BoardIds.MUSE_2_BOARD):
            self.board.config_board("p50")

        self.set_file_streamer(path)

        self.board.start_stream()

        # wait for signal to settle
        sleep(5)

    def set_file_streamer(self,path=""):

        if(path !="" and path[-1]!="/"):
            path=path+"/"
        
        self.board.add_streamer("file://"+path+"default_from_streamer.csv:w",  BrainFlowPresets.DEFAULT_PRESET)
        self.board.add_streamer("file://"+path+"aux_from_streamer.csv:w",  BrainFlowPresets.AUXILIARY_PRESET)
        self.board.add_streamer("file://"+path+"anc_from_streamer.csv:w", BrainFlowPresets.ANCILLARY_PRESET)

    def getChannels(self,type='eeg',preset=BrainFlowPresets.DEFAULT_PRESET):
        if(type=='eeg'):
            return BoardShim.get_eeg_channels(self.brainflow_id,BrainFlowPresets.DEFAULT_PRESET)
        elif(type=='ppg'):
            return BoardShim.get_ppg_channels(self.brainflow_id,BrainFlowPresets.ANCILLARY_PRESET)
        elif(type=='timestamp'):
            return BoardShim.get_timestamp_channel(self.brainflow_id,preset)
        elif(type=='marker'):
            return BoardShim.get_marker_channel(self.brainflow_id,preset)
        else:
            return None

    def getChannelNames(self,type='eeg',preset=BrainFlowPresets.DEFAULT_PRESET):
        if(type=='eeg'):
            return BoardShim.get_eeg_names(self.brainflow_id,preset)
        elif(type=='ppg'):
            return BoardShim.get_ppg_names(self.brainflow_id,preset)
        elif(type=='ecg'):
            return BoardShim.get_ecg_names(self.brainflow_id,preset)
        else:
            return None


    def export_mne(self):

        eeg_channels = self.getChannels('eeg')

        eeg_data = self.raw_data[eeg_channels, :]
        eeg_data = eeg_data / 1000000  # BrainFlow returns uV, convert to V for MNE

        # Creating MNE objects from brainflow data arrays
        ch_types = ['eeg'] * len(eeg_channels)
        ch_names =  self.getChannelNames('eeg')
        sfreq = BoardShim.get_sampling_rate(self.brainflow_id,0) # 0 for default preset i.e. EEG 
        info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=ch_types)
        raw = mne.io.RawArray(eeg_data, info)

        return raw
    
        # its time to plot something!
        #raw.plot_psd(average=True)
        #plt.savefig('psd.png')

    def stop(self):
        data1 = self.board.get_board_data(preset=BrainFlowPresets.DEFAULT_PRESET)
        data2=self.board.get_board_data(preset=BrainFlowPresets.AUXILIARY_PRESET)
        data3=self.board.get_board_data(preset=BrainFlowPresets.ANCILLARY_PRESET)

        self.board.stop_stream()
        self.board.release_session()
        self.raw_data=[data1.T,data2.T,data3.T]
        return self.raw_data

    def insertMarker(self,value,preset=BrainFlowPresets.DEFAULT_PRESET):
        self.board.insert_marker(value,preset)

    def getData(self,lastN=1,type='all',preset=BrainFlowPresets.DEFAULT_PRESET):
        
        data=[]
        data=self.board.get_current_board_data(lastN,preset)

        if(type=='eeg'):
            return data.T [:, BoardShim.get_eeg_channels(self.brainflow_id,preset)]
        elif (type=='ppg'):
            return data.T [:, BoardShim.get_ppg_channels(self.brainflow_id,preset)]
        elif (type=='ecg'):
            return data.T [:, BoardShim.get_ecg_channels(self.brainflow_id,preset)]
        elif (type=='timestamp'):
            return data.T [:, BoardShim.get_timestamp_channel(self.brainflow_id,preset)]
        elif (type=='marker'):
            return data.T [:, BoardShim.get_marker_channel(self.brainflow_id,preset)]   
         
        elif (type=='all'):
            return data.T

        



