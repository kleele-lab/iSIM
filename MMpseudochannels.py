
from pycromanager import Bridge
import re

bridge = Bridge(convert_camel_case=False)
core = bridge.get_core()

#get the micro-manager studio object:
studio = bridge.get_studio()

data = studio.getDataManager()
plugins = studio.getPluginManager()


pseudochannels = plugins.getProcessorPlugins().get('org.micromanager.pseudochannels.PseudoChannelPlugin')
pseudochannels.setSettings(studio, 1)
