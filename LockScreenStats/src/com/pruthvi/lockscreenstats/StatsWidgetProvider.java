package com.pruthvi.lockscreenstats;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.os.BatteryManager;
import android.os.Build;
import android.widget.RemoteViews;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public class StatsWidgetProvider extends AppWidgetProvider {

    @Override
    public void onReceive(Context context, Intent intent) {
        super.onReceive(context, intent);
        updateAllWidgets(context);
    }

    @Override
    public void onUpdate(Context context, AppWidgetManager appWidgetManager, int[] appWidgetIds) {
        for (int appWidgetId : appWidgetIds) {
            updateWidget(context, appWidgetManager, appWidgetId);
        }
    }

    public static void updateAllWidgets(Context context) {
        AppWidgetManager manager = AppWidgetManager.getInstance(context);
        ComponentName cn = new ComponentName(context, StatsWidgetProvider.class);
        int[] ids = manager.getAppWidgetIds(cn);
        if (ids != null && ids.length > 0) {
            for (int id : ids) {
                updateWidget(context, manager, id);
            }
        }
    }

    private static void updateWidget(Context context, AppWidgetManager appWidgetManager, int appWidgetId) {
        RemoteViews views = new RemoteViews(context.getPackageName(), R.layout.widget_stats);

        // 1. Read Battery Broadcast
        IntentFilter filter = new IntentFilter(Intent.ACTION_BATTERY_CHANGED);
        Intent batteryIntent = context.registerReceiver(null, filter);

        int level = 50;
        int scale = 100;
        int status = BatteryManager.BATTERY_STATUS_UNKNOWN;
        int plugged = 0;
        int voltageMv = 3850;
        int tempTenths = 300;

        if (batteryIntent != null) {
            level = batteryIntent.getIntExtra(BatteryManager.EXTRA_LEVEL, 50);
            scale = batteryIntent.getIntExtra(BatteryManager.EXTRA_SCALE, 100);
            status = batteryIntent.getIntExtra(BatteryManager.EXTRA_STATUS, -1);
            plugged = batteryIntent.getIntExtra(BatteryManager.EXTRA_PLUGGED, 0);
            voltageMv = batteryIntent.getIntExtra(BatteryManager.EXTRA_VOLTAGE, 3850);
            tempTenths = batteryIntent.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, 300);
        }

        int percent = (scale > 0) ? (level * 100 / scale) : level;
        float tempC = tempTenths / 10.0f;
        float volts = voltageMv / 1000.0f;

        boolean isCharging = (status == BatteryManager.BATTERY_STATUS_CHARGING ||
                              status == BatteryManager.BATTERY_STATUS_FULL);
        boolean isFull = (status == BatteryManager.BATTERY_STATUS_FULL || percent >= 100);

        // 2. Query BatteryManager hardware properties
        BatteryManager bm = (BatteryManager) context.getSystemService(Context.BATTERY_SERVICE);
        long currentNowUa = 0;
        long sysChargeTimeMs = -1;

        if (bm != null) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                currentNowUa = bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CURRENT_NOW);
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                try {
                    sysChargeTimeMs = bm.computeChargeTimeRemaining();
                } catch (Exception ignored) {}
            }
        }

        long currentMa = Math.abs(currentNowUa) / 1000;
        if (currentMa <= 0) {
            if (plugged == BatteryManager.BATTERY_PLUGGED_AC) {
                currentMa = 3500;
            } else if (plugged == BatteryManager.BATTERY_PLUGGED_USB) {
                currentMa = 480;
            } else {
                currentMa = 1200;
            }
        }

        float watts = (volts * currentMa) / 1000.0f;
        long now = System.currentTimeMillis();

        String percentText;
        String finishTimeText;
        String modeText;
        String durationText;

        if (isFull) {
            percentText = "⚡ 100%";
            finishTimeText = "Fully Charged";
            modeText = "READY TO UNPLUG";
            durationText = String.format(Locale.US, "%.1f°C", tempC);
        } else if (isCharging) {
            percentText = "⚡ " + percent + "%";

            // Classify Charger Mode
            if (plugged == BatteryManager.BATTERY_PLUGGED_AC) {
                if (currentMa >= 4000 || watts >= 30.0f) {
                    modeText = "SUPERVOOC 67W";
                } else if (currentMa >= 2000 || watts >= 15.0f) {
                    modeText = "FAST CHARGING (" + (int) watts + "W)";
                } else {
                    modeText = "AC CHARGING";
                }
            } else if (plugged == BatteryManager.BATTERY_PLUGGED_USB) {
                modeText = "USB CHARGE • " + currentMa + "mA";
            } else {
                modeText = "CHARGING";
            }

            // Estimate Remaining Time (Smart Model)
            long estimatedMins = -1;
            if (sysChargeTimeMs > 0 && sysChargeTimeMs < 86400000) {
                estimatedMins = sysChargeTimeMs / 60000;
            }

            if (estimatedMins <= 0) {
                int percentToCharge = 100 - percent;
                float remainingMah = percentToCharge * 50.0f; // 5000 mAh capacity

                float effectiveMa = (float) currentMa;
                if (percent >= 80) {
                    effectiveMa = effectiveMa * 0.65f;
                } else {
                    float ccWeight = (80 - percent);
                    float cvWeight = 20;
                    effectiveMa = effectiveMa * ((ccWeight * 1.0f + cvWeight * 0.65f) / (ccWeight + cvWeight));
                }
                if (effectiveMa < 150) effectiveMa = 150;

                float hours = remainingMah / effectiveMa;
                estimatedMins = (long) (hours * 60);
            }

            // Empirical rate calibration
            SharedPreferences sp = context.getSharedPreferences("smart_battery_tracker", Context.MODE_PRIVATE);
            long lastTime = sp.getLong("last_time", 0);
            int lastLevel = sp.getInt("last_level", -1);

            if (lastLevel > 0 && percent > lastLevel && (now - lastTime) > 20000 && (now - lastTime) < 1800000) {
                long msPerPercent = (now - lastTime) / (percent - lastLevel);
                long empiricalMins = (msPerPercent * (100 - percent)) / 60000;
                if (empiricalMins > 0 && empiricalMins < 600) {
                    estimatedMins = (long) (0.6f * estimatedMins + 0.4f * empiricalMins);
                }
            }
            if (percent != lastLevel) {
                sp.edit().putLong("last_time", now).putInt("last_level", percent).apply();
            }

            if (estimatedMins < 1) estimatedMins = 1;

            long h = estimatedMins / 60;
            long m = estimatedMins % 60;
            String dur = (h > 0) ? (h + "h " + m + "m") : (m + "m");
            durationText = "~" + dur + " to full";

            long finishEpoch = now + (estimatedMins * 60000);
            String finishClock = new SimpleDateFormat("hh:mm a", Locale.US).format(new Date(finishEpoch));
            finishTimeText = "Full at " + finishClock;

        } else {
            // Discharging mode
            percentText = "🔋 " + percent + "%";
            modeText = "ON BATTERY • " + String.format(Locale.US, "%.1f°C", tempC);

            // Endurance estimate (Dimensity 7050 typical mixed drain 5.5%/hr)
            float hoursLeft = percent / 5.5f;
            long totalMinsLeft = (long) (hoursLeft * 60);
            long h = totalMinsLeft / 60;
            long m = totalMinsLeft % 60;
            String dur = (h > 0) ? (h + "h " + m + "m") : (m + "m");
            durationText = "~" + dur + " left";

            long emptyEpoch = now + (totalMinsLeft * 60000);
            String emptyClock = new SimpleDateFormat("hh:mm a", Locale.US).format(new Date(emptyEpoch));
            finishTimeText = "Until " + emptyClock;
        }

        // 3. Update RemoteViews
        views.setTextViewText(R.id.tv_battery_percent, percentText);
        views.setTextViewText(R.id.tv_charge_finish_time, finishTimeText);
        views.setProgressBar(R.id.pb_battery, 100, percent, false);
        views.setTextViewText(R.id.tv_charge_mode, modeText);
        views.setTextViewText(R.id.tv_charge_duration, durationText);

        // 4. Click Intent (Instant live refresh on tap)
        Intent clickIntent = new Intent(context, StatsWidgetProvider.class);
        clickIntent.setAction(AppWidgetManager.ACTION_APPWIDGET_UPDATE);
        clickIntent.putExtra(AppWidgetManager.EXTRA_APPWIDGET_IDS, new int[]{appWidgetId});
        PendingIntent pi = PendingIntent.getBroadcast(
                context, appWidgetId, clickIntent,
                PendingIntent.FLAG_UPDATE_CURRENT | (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M ? PendingIntent.FLAG_IMMUTABLE : 0)
        );
        views.setOnClickPendingIntent(R.id.widget_root, pi);

        appWidgetManager.updateAppWidget(appWidgetId, views);
    }
}
