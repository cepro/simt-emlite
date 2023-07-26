package com.cepro.util;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class WaitUtil {
    private static final Logger log = LoggerFactory.getLogger(WaitUtil.class);

    /**
     * Pause execution for a given number of milliseconds.
     */
    public static void delay(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            log.error("Interrupted", e);
        }
    }

}
