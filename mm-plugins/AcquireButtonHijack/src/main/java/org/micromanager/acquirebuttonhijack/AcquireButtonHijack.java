/**
 * A very simple Micro-Manager plugin, intended to be used as an example for
 * developers wishing to create their own, actually useful plugins. This one
 * demonstrates performing various common tasks, but does not do anything
 * really useful.
 *
 * Copy this code to a location of your choice, change the name of the project
 * (and the classes), build the jar file and copy it to the mmplugins folder
 * in your Micro-Manager directory.
 *
 * Once you have it loaded and running, you can attach the NetBean debugger
 * and use all of NetBean's functionality to debug your code.  If you make a
 * generally useful plugin, please do not hesitate to send a copy to
 * info@micro-managaer.org for inclusion in the Micro-Manager source code
 * repository.
 *
 * Nico Stuurman, 2012
 * copyright University of California
 *
 * LICENSE:      This file is distributed under the BSD license.
 *               License text is included with the source distribution.
 *
 *               This file is distributed in the hope that it will be useful,
 *               but WITHOUT ANY WARRANTY; without even the implied warranty
 *               of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 *
 *               IN NO EVENT SHALL THE COPYRIGHT OWNER OR
 *               CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 *               INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES.
 */


package org.micromanager.acquirebuttonhijack;

import org.micromanager.MenuPlugin;
import org.micromanager.Studio;

import org.scijava.plugin.Plugin;
import org.scijava.plugin.SciJavaPlugin;

/**
 * Changes the Acquire! button in Micro-Manager for iSIM acquisitions
 * <p>
 * This Plugin runs AcquireButtonHijackFrame, which does not actually
 * have a frame anymore. That the Plugin ran can be seen when the MDA
 * window in Micro-Manager shows the Acquire button without the '!'.
 *
 * @author Willi Stepp
 * @version 0.1
 */


@Plugin(type = MenuPlugin.class)
public class AcquireButtonHijack implements SciJavaPlugin, MenuPlugin {
   private Studio studio_;
   private AcquireButtonHijackFrame frame_;

   @Override
   public void setContext(Studio studio) {
      studio_ = studio;
   }

   @Override
   public void onPluginSelected() {
      if (frame_ == null) {
         // We have never before shown our GUI, so now we need to create it.
         frame_ = new AcquireButtonHijackFrame(studio_);
      }
      frame_.setVisible(!frame_.isVisible());
   }

   @Override
   public String getSubMenu() {
      return "Developer Tools";
   }

   /**
    * The name of the plugin in the Plugins menu.
    */
   @Override
   public String getName() {
      return "AcquireButtonHijack";
   }

   @Override
   public String getHelpText() {
      return "This plugin hijacks the Acquire button and puts it's own functionality on top";
   }

   @Override
   public String getVersion() {
      return "1.0";
   }

   @Override
   public String getCopyright() {
      return "Willi Stepp EPFL, 2021";
   }
}
