
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

# restore = []
# data.getApplicationPipelineConfigurators(False).size()
# for i in range(data.getApplicationPipelineConfigurators(False).size()):
#     if not data.getApplicationPipelineConfigurators(False).get(i).toString()[0:45] == 'org.micromanager.pseudochannels.PseudoChannel':
#         restore.append(data.getApplicationPipelineConfigurators(False).get(i))


# regexp = re.compile('org.micromanager\.\w+.\w+')
# data.clearPipeline()
# for processor in restore:
#     module = regexp.match(processor.toString()).group()
#     parts = module.split('.')

#     if parts[-1]== 'FlipperConfigurator':
#         plugininstance = plugins.getProcessorPlugins().get(processor.toString().split('[')[0][0:-12] + 'Plugin')
#     elif parts[-1] == 'RatioImagingFrame':
#         plugininstance = plugins.getProcessorPlugins().get(module[0:-5])
#     elif parts[-1] == 'MultiChannelShadingMigForm':
#         plugininstance = plugins.getProcessorPlugins().get(module[0:-7])
#     elif parts[-1] == 'framecombiner':
#         plugininstance = plugins.getProcessorPlugins().get(module + '.FrameCombinerPlugin')
#     elif parts[-1] == 'SaverConfigurator':
#         plugininstance = plugins.getProcessorPlugins().get(module[0:-12] + 'Plugin')
#     elif parts[-1] == 'SplitViewFrame':
#         plugininstance = plugins.getProcessorPlugins().get(module[0:-5])

#     data.addConfiguredProcessor(processor, plugininstance)
#     processor.cleanup()

# data.addConfiguredProcessor(pseudochannelConfig, pseudochannels)
# pseudochannelConfig.cleanup()
