
package org.micromanager.pseudochannels;

import java.awt.*;
import java.util.ArrayList;
import javax.swing.*;

import org.micromanager.PropertyMap;
import org.micromanager.PropertyMaps;
import org.micromanager.Studio;
import org.micromanager.acquisition.SequenceSettings;
import org.micromanager.data.ProcessorConfigurator;
import org.micromanager.internal.utils.WindowPositioning;
import org.micromanager.propertymap.MutablePropertyMapView;


public class PseudoChannelConfigurator extends JFrame implements ProcessorConfigurator {

   private static final String DEFAULT_SLICES = "Whether or not to use slices";


   private final int frameXPos_ = 300;
   private final int frameYPos_ = 300;

   private final Studio studio_;
   private final MutablePropertyMapView defaults_;

   private int acqOrderMode_;
   private javax.swing.JComboBox channelComboBox_;
   private boolean useChannels_;
   private javax.swing.JLabel jLabel1;
   private javax.swing.JLabel jLabelchannel;
   private javax.swing.JCheckBox slicesCheckBox_;
   private javax.swing.JTextField slicesTextField_;
   private ArrayList<Double> slicePositions_;

   public PseudoChannelConfigurator(Studio studio, PropertyMap settings) {
      studio_ = studio;
      defaults_ = studio_.profile().getSettings(this.getClass());

      initComponents();

      boolean useChannels = settings.getBoolean("useChannels", true);

      boolean useSlices = settings.getBoolean("useSlices",
            defaults_.getBoolean(DEFAULT_SLICES, false));

      slicesCheckBox_.setSelected(useSlices);
      slicesTextField_.setText(settings.getString("slices", "1"));
      channelComboBox_.setSelectedIndex(settings.getInteger("channels", 1)-1);

      super.setIconImage(Toolkit.getDefaultToolkit().getImage(
              getClass().getResource("/org/micromanager/icons/microscope.gif")));
      super.setLocation(frameXPos_, frameYPos_);
      WindowPositioning.setUpLocationMemory(this, this.getClass(), null);

   }

   @Override
   public void showGUI() {
      // Put this here so we can call this function from the Acquirebutton hijack and we set the values correctly

      System.out.println("new setSettings has been called!!!!!!!!");
      SequenceSettings settings = studio_.acquisitions().getAcquisitionSettings();

      int acqOrderMode = settings.acqOrderMode();
      setAcqOrderMode(acqOrderMode);

      ArrayList<Double> slicePositions_ = settings.slices();
      setSlicePositions(slicePositions_);

      int numSlices = java.lang.Math.max(1,settings.slices().size());
      setUseSlices(settings.useSlices());
      setSlices(numSlices);

      int numChannels = 0;
      for (int i=0; i<settings.channels().size(); i++){
         numChannels += settings.channels().get(i).useChannel() ? 1 : 0;
      }

      boolean useChannels;
      if (!settings.channelGroup().equals("Emission filter")){
         setUseChannels(true);
         useChannels = true;
         if (settings.useChannels()) {
            setChannels(numChannels);
         } else {
            setChannels(1);
         }
      } else {
         setUseChannels(false);
         useChannels = false;
         if (settings.useChannels()){
            setChannels(numChannels);
         } else {
            setChannels(1);
         }
      }


      System.out.printf("PSEUDOCHANNELS:   slices %d, channels %d, useChannels %b, acqOrder %d%n", numSlices, numChannels, useChannels, acqOrderMode);
      setVisible(true);
   }

   private void setSlicePositions(ArrayList<Double> newSlicePositions_) {slicePositions_ = newSlicePositions_;}

   @Override
   public void cleanup() {
      dispose();
   }

   /** This method is called from within the constructor to
    * initialize the form.
    */
   @SuppressWarnings("unchecked")
   private void initComponents() {

      slicesCheckBox_ = new javax.swing.JCheckBox();
      channelComboBox_ = new javax.swing.JComboBox();
      slicesTextField_ = new javax.swing.JTextField();
      jLabel1 = new javax.swing.JLabel();
      jLabelchannel = new javax.swing.JLabel();

      setDefaultCloseOperation(javax.swing.WindowConstants.DISPOSE_ON_CLOSE);
      setTitle("Pseudo Channels");
      setBounds(new java.awt.Rectangle(300, 300, 150, 150));
      setMinimumSize(new java.awt.Dimension(200, 200));
      setResizable(false);

      slicesCheckBox_.setText("Use Slices");
      slicesCheckBox_.addActionListener(new java.awt.event.ActionListener() {
         @Override
         public void actionPerformed(java.awt.event.ActionEvent evt) {
            slicesCheckBox_ActionPerformed(evt);
         }
      });

      channelComboBox_.setModel(new javax.swing.DefaultComboBoxModel(new String[] { "1", "2", "3", "4" }));
      channelComboBox_.addActionListener(new java.awt.event.ActionListener() {
         @Override
         public void actionPerformed(java.awt.event.ActionEvent evt) {
            channelComboBox_ActionPerformed(evt);
         }
      });

      slicesTextField_.setMinimumSize(new Dimension(100,20));
      slicesTextField_.addActionListener(new java.awt.event.ActionListener() {
         @Override
         public void actionPerformed(java.awt.event.ActionEvent evt) {
            slicesComboBox_ActionPerformed(evt);
         }
      });

      jLabel1.setText("Number of Slices");
      jLabelchannel.setText("Number of Channels");

      javax.swing.GroupLayout layout = new javax.swing.GroupLayout(getContentPane());
      getContentPane().setLayout(layout);
      layout.setHorizontalGroup(
         layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
         .addGroup(layout.createSequentialGroup()
            .addContainerGap()
            .addGroup(layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
               .addGroup(layout.createSequentialGroup()
                  .addGroup(layout.createParallelGroup(javax.swing.GroupLayout.Alignment.TRAILING)
                     .addGroup(layout.createSequentialGroup()
                        .addComponent(jLabelchannel)
                        .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.UNRELATED)
                        .addComponent(channelComboBox_, javax.swing.GroupLayout.PREFERRED_SIZE, 0, 153))
                     .addGroup(layout.createSequentialGroup()
                        .addComponent(jLabel1)
                        .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.UNRELATED)
                        .addComponent(slicesTextField_, javax.swing.GroupLayout.PREFERRED_SIZE, 100, javax.swing.GroupLayout.PREFERRED_SIZE)))
                  .addGap(38, 38, 38))
               .addGroup(layout.createSequentialGroup()
                  .addComponent(slicesCheckBox_)
                  .addContainerGap(121, Short.MAX_VALUE))))
      );
      layout.setVerticalGroup(
         layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
         .addGroup(javax.swing.GroupLayout.Alignment.TRAILING, layout.createSequentialGroup()
            .addGap(11, 11, 11)
            .addGroup(layout.createParallelGroup(javax.swing.GroupLayout.Alignment.BASELINE)
               .addComponent(channelComboBox_, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
               .addComponent(jLabelchannel))
            .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
            .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.UNRELATED)
            .addComponent(slicesCheckBox_)
            .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
            .addGroup(layout.createParallelGroup(javax.swing.GroupLayout.Alignment.BASELINE)
               .addComponent(slicesTextField_, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
               .addComponent(jLabel1))
            .addGap(25, 25, 25))
      );

      pack();
   }

    private void slicesCheckBox_ActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_mirrorCheckBox_ActionPerformed
       studio_.data().notifyPipelineChanged();
    }

   private void slicesComboBox_ActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_rotateComboBox_ActionPerformed
      studio_.data().notifyPipelineChanged();
   }

   private void channelComboBox_ActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_cameraComboBox_ActionPerformed
      studio_.data().notifyPipelineChanged();
   }

   public void setAcqOrderMode(int acqOrder){acqOrderMode_ = acqOrder;}

   public void setChannels(int channels) {
      channelComboBox_.setSelectedIndex(channels-1);
   }

   public void setUseChannels(boolean useChannels){useChannels_ = useChannels;}

   public void setSlices(int slices) {slicesTextField_.setText(String.valueOf(slices));}

   public void setUseSlices(boolean useSlices){slicesCheckBox_.setSelected(useSlices);}

   public String getSlices() {
       return slicesTextField_.getText();
   }

   public final boolean getUseSlices() {
      return slicesCheckBox_.isSelected();
   }

   public int getAcqOrderMode(){return acqOrderMode_;}

   public int getChannels(){return channelComboBox_.getSelectedIndex() + 1;}

   public boolean getUseChannels(){return useChannels_;}

   public ArrayList<Double> getSlicePositions(){return slicePositions_;}

   @Override
   public PropertyMap getSettings() {

      // Now return the values
      PropertyMap.Builder builder = PropertyMaps.builder();
      builder.putInteger("acqOrderMode", getAcqOrderMode());
      builder.putInteger("channels", getChannels());
      builder.putBoolean("useChannels", getUseChannels());
      builder.putDoubleList("slicePositions", getSlicePositions());
      builder.putString("slices", getSlices());
      builder.putBoolean("useSlices", getUseSlices());
      return builder.build();
   }
}