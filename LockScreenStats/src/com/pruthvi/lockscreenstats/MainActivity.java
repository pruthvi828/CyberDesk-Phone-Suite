package com.pruthvi.lockscreenstats;

import android.app.Activity;
import android.app.NotificationManager;
import android.appwidget.AppWidgetManager;
import android.content.ComponentName;
import android.content.Context;
import android.os.Build;
import android.os.Bundle;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Delete channel and cancel any notifications
        NotificationManager nm = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        if (nm != null) {
            try {
                nm.cancel(1001);
                nm.cancelAll();
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    nm.deleteNotificationChannel("lockscreen_stats_channel");
                }
            } catch (Exception ignored) {}
        }

        // Update all active widgets
        StatsWidgetProvider.updateAllWidgets(this);

        finish();
    }
}
