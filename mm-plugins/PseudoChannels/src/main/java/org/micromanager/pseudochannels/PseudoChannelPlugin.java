
package org.micromanager.pseudochannels;

import org.micromanager.PluginManager;
import org.micromanager.PropertyMaps;
import org.micromanager.data.ProcessorConfigurator;
import org.micromanager.data.ProcessorPlugin;
import org.micromanager.data.ProcessorFactory;
import org.micromanager.data.DataManager;

import java.io.FileNotFoundException;
import java.io.PrintWriter;
import java.io.UnsupportedEncodingException;

import org.micromanager.PropertyMap;
import org.micromanager.Studio;

import org.scijava.plugin.Plugin;
import org.scijava.plugin.SciJavaPlugin;

@Plugin(type = ProcessorPlugin.class)
public class PseudoChannelPlugin implements ProcessorPlugin, SciJavaPlugin {
   private Studio studio_;
   private PseudoChannelFactory factory_;
   private DataManager data_;

   @Override
   public void setContext(Studio studio) {
      studio_ = studio;
   }

   @Override
   public ProcessorConfigurator createConfigurator(PropertyMap settings) {
//      PluginManager pluginManager_ = studio_.getPluginManager();
//      PrintWriter writer = null;
//      try {
//         writer = new PrintWriter("C:/Users/stepp/Desktop/MMlog.txt", "UTF-8");
//      } catch (FileNotFoundException ex) {
//         ex.printStackTrace();
//      } catch (UnsupportedEncodingException ex) {
//         ex.printStackTrace();
//      }
//      writer.println(pluginManager_.getProcessorPlugins());
//      writer.close();
      return new PseudoChannelConfigurator(studio_, settings);
   }

   @Override
   public ProcessorFactory createFactory(PropertyMap settings) {
      factory_ = new PseudoChannelFactory(settings, studio_);
      return factory_;
   }

   @Override
   public String getName() {
      return "Pseudo Channels";
   }

   @Override
   public String getHelpText() {
      return "Puts images into Pseudo Channels";
   }

   @Override
   public String getVersion() {
      return "Version 1.0";
   }

   @Override
   public String getCopyright() {
      return "Copyright Willi Stepp EPFL, 2021";
   }

   public ProcessorConfigurator getConfigurator(int acqOrderMode, int channels,boolean useChannels, int slices, boolean useSlices) {
      PropertyMap.Builder builder = PropertyMaps.builder();
      builder.putInteger("acqOrderMode", acqOrderMode);
      builder.putInteger("channels", channels);
      builder.putBoolean("useChannels", useChannels);
      builder.putString("slices", String.valueOf(slices));
      builder.putBoolean("useSlices", useSlices);
      System.out.println(builder.build());
      return createConfigurator(builder.build());
   }

}
