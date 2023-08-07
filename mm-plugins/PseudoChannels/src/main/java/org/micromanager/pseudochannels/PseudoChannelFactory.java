package org.micromanager.pseudochannels;

import org.micromanager.data.Processor;
import org.micromanager.data.ProcessorFactory;

import org.micromanager.PropertyMap;
import org.micromanager.Studio;

public class PseudoChannelFactory implements ProcessorFactory {
   private final PropertyMap settings_;
   private final Studio studio_;
   private PseudoChannelProcessor processor_;

   public PseudoChannelFactory(PropertyMap settings, Studio studio) {
      settings_ = settings;
      studio_ = studio;
   }

   public void changeProcessor(int channels){
      processor_.channels_ = channels;
   }

   @Override
   public Processor createProcessor() {
      processor_ = new PseudoChannelProcessor(studio_,
              settings_.getInteger("acqOrderMode", 0),
              settings_.getInteger("channels", 1),
              settings_.getBoolean("useChannels", true),
              settings_.getString("slices", "10"),
              settings_.getBoolean("useSlices", false),
              settings_.getDoubleList("slicePositions", new double[1]));
      return processor_;
   }
}
