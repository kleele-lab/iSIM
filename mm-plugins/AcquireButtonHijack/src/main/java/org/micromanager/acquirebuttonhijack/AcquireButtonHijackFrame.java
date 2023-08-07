/**
 * ExampleFrame.java
 *
 * This module shows an example of creating a GUI (Graphical User Interface).
 * There are many ways to do this in Java; this particular example uses the
 * MigLayout layout manager, which has extensive documentation online.
 *
 *
 * Nico Stuurman, copyright UCSF, 2012, 2015
 *
 * LICENSE: This file is distributed under the BSD license. License text is
 * included with the source distribution.
 *
 * This file is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
 * A PARTICULAR PURPOSE.
 *
 * IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
 * DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES.
 */
package org.micromanager.acquirebuttonhijack;

import org.micromanager.LogManager;
import org.micromanager.PluginManager;
import org.micromanager.Studio;
import org.micromanager.acquisition.SequenceSettings;
import org.micromanager.data.DataManager;
import org.micromanager.data.Datastore;
import org.micromanager.data.ProcessorConfigurator;
import org.micromanager.internal.MMStudio;
import org.micromanager.internal.dialogs.AcqControlDlg;
import org.micromanager.internal.utils.JavaUtils;
import org.micromanager.internal.utils.WindowPositioning;

import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionListener;
import java.beans.PropertyChangeEvent;
import java.util.ArrayList;
import java.util.Date;

/**
 * Defines the changes requested to the MDA window by AcquireButtonHIjack
 * <p>
 * This gets the 'Acquire!' button from the MDA window of Micro-
 * Manager and gives it a new name to show that is is active and
 * a new ActionCallback that adjusts things for iSIM imaging.
 * <p>
 *
 * @author Willi Stepp
 * @version 0.1
 */


public class AcquireButtonHijackFrame extends JFrame {

   private final JTextArea logTextArea;
   private JPanel panel = new JPanel();
   private BoxLayout boxLayout = new BoxLayout(panel, BoxLayout.Y_AXIS);
   private ProcessorConfigurator pseudoChannels;
   private final DataManager dataManager;
   private Studio studio_;
   private AcqControlDlg acw_;
   private PluginManager pluginManager_;
   private PipelineListener server_;

   public AcquireButtonHijackFrame(Studio studio) {
      super("AcquireButtonHijack");
      studio_ = studio;
      pluginManager_ = studio.getPluginManager();
      dataManager = studio.getDataManager();

      // Adjust the window
      JLabel title = new JLabel("AcquireButtonHijack");
      title.setFont(new Font("Arial", Font.BOLD, 14));
      title.setMaximumSize(new Dimension(200, 30));
      title.setAlignmentX(CENTER_ALIGNMENT);

      logTextArea = new JTextArea(30, 100);
      logTextArea.setAlignmentX(CENTER_ALIGNMENT);

      panel.setLayout(boxLayout);
      panel.add(title);
      panel.add(logTextArea);
      panel.setAlignmentX(CENTER_ALIGNMENT);

      super.add(panel);
      super.setIconImage(Toolkit.getDefaultToolkit().getImage(
              getClass().getResource("/org/micromanager/icons/microscope.gif")));
      super.setLocation(100, 100);
      super.setSize(new Dimension(100, 100));
      WindowPositioning.setUpLocationMemory(this, this.getClass(), null);
      super.pack();

      // Get the Acquire! Button and strip of the functionality, so we can put something of our own.
      acw_ = ((MMStudio) studio_).uiManager().getAcquisitionWindow();
      JPanel panel0 = (JPanel) acw_.getContentPane().getComponent(0);
      JPanel panel1 = (JPanel) panel0.getComponent(2);
      JPanel panel2 = (JPanel) panel1.getComponent(1);
      JButton button = (JButton) panel2.getComponent(0);
      button.setText("Acquire");
      ActionListener[] listeners = button.getActionListeners();
      for (ActionListener listener : listeners) {
         button.removeActionListener(listener);
         System.out.println(listener.toString());
      }

      // Increase the number of frames and turn channels off if channels is selected and then start acquisition
      button.addActionListener(e -> {
         Thread acq = new acqThread();
         acq.start();
      });

      // super.setDefaultCloseOperation(JFrame.DO_NOTHING_ON_CLOSE);
      server_ = new PipelineListener(studio_, this);
      server_.init();
      server_.start();

      addLog("Hijack Successful");


   }

   void addLog (String eventMsg){
      String currentText = logTextArea.getText();
      String newEvent = new Date() + " " + eventMsg;
      logTextArea.setText(newEvent + "\n" + currentText);
   }

   void setPseudoChannels (ProcessorConfigurator newPseudoChannels){
      pseudoChannels = newPseudoChannels;
      addLog("Received new PseudoChannels");
   }


   public class acqThread extends Thread{
      public void run(){
         System.out.println("ACQ running");

         // Call apply SettingsfromGUI with a small trick
         PropertyChangeEvent e = new PropertyChangeEvent(1, "test",0,1);
         acw_.propertyChange(e);

         // Save the original settings so we can reset them later
         SequenceSettings settings = studio_.acquisitions().getAcquisitionSettings();

         // Try to make the save path otherwise show error
         LogManager logs = studio_.getLogManager();
         if (settings.save()) {
            try {
               JavaUtils.createDirectory(settings.root());
            } catch (Exception exc) {
               logs.showError(exc);
               exc.printStackTrace();
               return;
            }
         }


         int index = AcquireButtonUtility.getCurrentMaxIndex(settings.root(), settings.prefix() + "_") + 1;
         server_.storeSettings(settings, index);
         // We modified the showGUI function to store the settings in pseudoChannels, because that function exists
         // for all ProcessorConfigurators and it didn't seem a good idea to have a direct dependency to PseudoChannels,
         // because there were problems with different ClassLoaders.
         pseudoChannels.showGUI();

         SequenceSettings.Builder new_settings_builder;
         // How many slices do we have to account for?
         int numSlices = java.lang.Math.max(1,settings.slices().size());
         // How many channels are actually active?
         int numChannels = 0;
         for (int i=0; i<settings.channels().size(); i++){
            numChannels += settings.channels().get(i).useChannel() ? 1 : 0;
         }
         System.out.printf("Channels: %d%n", numChannels);
         System.out.printf("Slices: %d%n", numSlices);

         // Special case if Emission filters are on, because we want to keep the channels from micro-manager.
         if (settings.channelGroup().equals("Emission filter")) {
            new_settings_builder = settings.copyBuilder().intervalMs(0)
                                                 .numFrames(settings.numFrames()*numSlices)
                                                 .useSlices(false).slices(new ArrayList<>())
                                                 .save(false);
         } else if (settings.useChannels()) {
            new_settings_builder = settings.copyBuilder().intervalMs(0)
                                                 .useChannels(false).channels(new ArrayList<>())
                                                 .numFrames(settings.numFrames()*numChannels*numSlices)
                                                 .useSlices(false).slices(new ArrayList<>())
                                                 .save(false);
         } else {
            new_settings_builder = settings.copyBuilder().intervalMs(0)
                                                 .useChannels(false).channels(new ArrayList<>())
                                                 .numFrames(settings.numFrames()*numSlices)
                                                 .useSlices(false).slices(new ArrayList<>())
                                                 .save(false);
         }
         SequenceSettings new_settings = new_settings_builder.cameraTimeout(999999).build();


         Datastore datastore = studio_.acquisitions().runAcquisitionWithSettings(new_settings,false);
         datastore.setName(settings.prefix() + "_" + index);

         addLog(String.valueOf(new_settings.useChannels()));
         addLog(new_settings.channels().toString());
         addLog(String.valueOf(new_settings.useSlices()));
         addLog(new_settings.slices().toString());
         studio_.acquisitions().setAcquisitionSettings(settings);
      }
   }

}



