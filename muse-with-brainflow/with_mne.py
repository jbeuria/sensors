import mne
from muse import muse

sensor=muse("5E7A9920-F60A-442A-C397-295F37233424")

raw_data=sensor.stop() 
raw_mne=sensor.export_mne()
