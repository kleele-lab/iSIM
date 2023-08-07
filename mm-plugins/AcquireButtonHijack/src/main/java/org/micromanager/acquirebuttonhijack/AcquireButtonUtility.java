package org.micromanager.acquirebuttonhijack;

import java.io.File;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class AcquireButtonUtility {
    public static int getCurrentMaxIndex(File rootDir, String prefix) throws NumberFormatException {
        int maxNumber = 0;
        int number;
        String theName;
        File[] rootDirFiles = rootDir.listFiles();
        if (rootDirFiles != null) {
            for (File acqDir : rootDirFiles) {
                theName = acqDir.getName();
                if (theName.startsWith(prefix)) {
                    try {
                        //e.g.: "blah_32.ome.tiff"
                        Pattern p = Pattern.compile("\\Q" + prefix + "\\E" + "(\\d+).*+");
                        Matcher m = p.matcher(theName);
                        if (m.matches()) {
                            number = Integer.parseInt(m.group(1));
                            if (number >= maxNumber) {
                                maxNumber = number;
                            }
                        }
                    } catch (NumberFormatException e) {
                        e.printStackTrace();
                    }
                }
            }
        }
        return maxNumber;
    }

    public static int getCurrentMaxIndex(String rootDir, String prefix) throws NumberFormatException{
        Path path = Paths.get(rootDir);
        File directory = path.toFile();
        return getCurrentMaxIndex(directory, prefix);
    }
}

