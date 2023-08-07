
package org.micromanager.pseudochannels;

import ij.process.ImageProcessor;


import org.micromanager.data.*;

import org.micromanager.PropertyMap;
import org.micromanager.PropertyMaps;
import org.micromanager.Studio;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;


public class PseudoChannelProcessor implements Processor {

   private final Studio studio_;
   int acqOrderMode_;
   int channels_;
   boolean useChannels_;
   String slices_;
   boolean useSlices_;
   double[] slicePositions_;


   public PseudoChannelProcessor(Studio studio, int acqOrderMode, int channels, boolean useChannels, String slices,
                                 boolean useSlices, double[] slicePositions) {
      studio_ = studio;
      acqOrderMode_ = acqOrderMode;
      channels_ = channels;
      useChannels_ = useChannels;
      slices_ = slices;
      useSlices_ = useSlices;
      slicePositions_ =  slicePositions;
   }

   /**
    * Process one image.
    */
   @Override
   public void processImage(Image image, ProcessorContext context) {
      // to allow processing old data, we do not check for the camera when no 
      // camera was selected
      context.outputImage(
              transformImage(studio_, image, acqOrderMode_, useSlices_, slices_, channels_, useChannels_, slicePositions_));
   }

   /**
    * Executes image transformation
    * First mirror the image if requested, than rotate as requested
    * 
    * @param studio main Studio instance
    * @param image Image to be transformed.
    * @param useSlices Whether or not to do a ZStack
    * @param slices Number of Slices for the ZStack
    * @param channels Number of channels
    * @return - Transformed Image, otherwise a copy of the input
    */
   public static Image transformImage(Studio studio, Image image,
         int acqOrderMode, boolean useSlices, String slices, int channels, boolean useChannels, double[] slicePositions) {

      int slices_int;
      if (useSlices) {
         slices_int = Integer.parseInt(slices);
      } else {
         slices_int = 1;
      }
//      ImageProcessor proc = studio.data().ij().createProcessor(image);

      // Insert some metadata to indicate what we did to the image.
      PropertyMap.Builder builder;
      PropertyMap userData = image.getMetadata().getUserData();
      if (userData != null) {
         builder = userData.copyBuilder();
      }
      else {
         builder = PropertyMaps.builder();
      }
      builder.putString("PseudoChannel-Channels", String.valueOf(channels));
      builder.putString("PseudoChannel-useChannels", useChannels ? "On" : "Off");
      builder.putString("PseudoChannel-useSlices", useSlices ? "On" : "Off");
      builder.putString("PseudoChannel-Slices", slices);
      Metadata newMetadata = image.getMetadata().copyBuilderPreservingUUID().userData(builder.build()).build();



      // Do the actual processing of the image
      Coords.Builder coordsBuilder = image.getCoords().copyBuilder();
      Coords old_coords = image.getCoords();

      int time = 0;
      int channel = 0;
      int zPos = 0;

      System.out.println("AcqOrder " + acqOrderMode);
      // Slices then channels
      if (acqOrderMode == 1) {
         int oldTime = old_coords.getT();

         channel = old_coords.getC();
         if (useChannels) {
            channel = (int) java.lang.Math.floor((old_coords.getT() % (channels * slices_int)) / slices_int);
            coordsBuilder.c(channel);
         } else {
            oldTime = old_coords.getT()*channels;
         }

         time = (int) java.lang.Math.floor(oldTime / channels / slices_int);
         coordsBuilder.t(time);

         zPos = oldTime % slices_int;
         // switch the direction of z for every second frame
         if (useSlices & channel % 2 == 1) {
            zPos = slices_int - 1 - zPos;
         }
         if (useSlices) {
            coordsBuilder.z(zPos);
            if (slicePositions != null) {
               newMetadata = newMetadata.copyBuilderPreservingUUID().zPositionUm(slicePositions[zPos]).build();
            }
         } else {
            zPos = 0;
         }
      // Channels then slices
      } else if (acqOrderMode == 0){
         int oldTime = old_coords.getT();

         channel = old_coords.getC();
         if (useChannels){
            channel = old_coords.getT() % channels;
            coordsBuilder.c(channel);
         } else {
            //useChannels false means that Emission filter is on and Channels are on even in the java acq
            oldTime = old_coords.getT()*channels;
         }

         time = (int) java.lang.Math.floor(oldTime/ channels / slices_int);
         coordsBuilder.t(time);

         System.out.printf("old_t %d, channels %d, slices_int %d%n", oldTime, channels, slices_int);
         zPos = (int) java.lang.Math.floor((oldTime % (channels * slices_int)) / channels);
         if (useSlices & time % 2 == 1) {
            zPos = slices_int - 1 - zPos;
         }

         if (useSlices) {
            coordsBuilder.z(zPos);
            if (slicePositions != null) {
               newMetadata = newMetadata.copyBuilderPreservingUUID().zPositionUm(slicePositions[zPos]).build();
            }
         } else {
            zPos = 0;
         }
      }

      System.out.printf("slices %d, channels %d%n", slices_int, channels);
      System.out.printf("time %d, zPos %d, channel %d%n",time, zPos, channel);
      System.out.println("Slices: " + Arrays.toString(slicePositions));
      System.out.println("useChannels: " + useChannels);
      return image.copyWith(coordsBuilder.build(), newMetadata);
   }

//   public static void setSlicePositions(float[] newSlicePositions){
//      slicePositions_ = newSlicePositions;
//   }
}
