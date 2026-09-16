package com.pruthvi.lockscreenstats;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.app.usage.UsageStats;
import android.app.usage.UsageStatsManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.os.BatteryManager;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.PowerManager;

import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public class StatsService extends Service {
    private static final String CHANNEL_ID = "lockscreen_stats_channel";
    private static final int NOTIFICATION_ID = 1001;

    private NotificationManager notificationManager;
    private Handler handler;
    private Runnable periodicUpdateRunnable;

    private int batteryLevel = -1;
    private int batteryStatus = BatteryManager.BATTERY_STATUS_UNKNOWN;
    private float batteryTemp = 0.0f;
    private long screenOnTimestamp = -1;
    private boolean isScreenOn = true;

    private SharedPreferences prefs;
    private String todayDateStr = "";

    private final BroadcastReceiver batteryReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            if (intent == null) return;
            if (Intent.ACTION_BATTERY_CHANGED.equals(intent.getAction())) {
                batteryLevel = intent.getIntExtra(BatteryManager.EXTRA_LEVEL, -1);
                batteryStatus = intent.getIntExtra(BatteryManager.EXTRA_STATUS, -1);
                int tempRaw = intent.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, 0);
                batteryTemp = tempRaw / 10.0f;
                updateNotification();
            }
        }
    };

    private final BroadcastReceiver screenReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            if (intent == null) return;
            String action = intent.getAction();
            checkAndResetMidnight();

            if (Intent.ACTION_SCREEN_ON.equals(action)) {
                isScreenOn = true;
                screenOnTimestamp = System.currentTimeMillis();
                updateNotification();
            } else if (Intent.ACTION_SCREEN_OFF.equals(action)) {
                isScreenOn = false;
                if (screenOnTimestamp > 0) {
                    long session = System.currentTimeMillis() - screenOnTimestamp;
                    addScreenTimeSession(session);
                    screenOnTimestamp = -1;
                }
                updateNotification();
            } else if (Intent.ACTION_USER_PRESENT.equals(action)) {
                incrementUnlockCount();
                updateNotification();
            }
        }
    };

    @Override
    public void onCreate() {
        super.onCreate();
        notificationManager = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        prefs = getSharedPreferences("stats_prefs", Context.MODE_PRIVATE);
        handler = new Handler(Looper.getMainLooper());

        todayDateStr = getTodayDateKey();
        checkAndResetMidnight();

        PowerManager pm = (PowerManager) getSystemService(Context.POWER_SERVICE);
        if (pm != null) {
            isScreenOn = pm.isInteractive();
            if (isScreenOn) {
                screenOnTimestamp = System.currentTimeMillis();
            }
        }

        createNotificationChannel();
        Notification initialNotif = buildNotification("LockScreen Stats", "Initializing live metrics...");
        startForeground(NOTIFICATION_ID, initialNotif);

        // Register Battery Receiver
        IntentFilter batteryFilter = new IntentFilter(Intent.ACTION_BATTERY_CHANGED);
        registerReceiver(batteryReceiver, batteryFilter);

        // Register Screen / Unlock Receivers
        IntentFilter screenFilter = new IntentFilter();
        screenFilter.addAction(Intent.ACTION_SCREEN_ON);
        screenFilter.addAction(Intent.ACTION_SCREEN_OFF);
        screenFilter.addAction(Intent.ACTION_USER_PRESENT);
        registerReceiver(screenReceiver, screenFilter);

        // Periodic refresher (every 30 seconds if screen on)
        periodicUpdateRunnable = new Runnable() {
            @Override
            public void run() {
                if (isScreenOn) {
                    updateNotification();
                }
                handler.postDelayed(this, 30000);
            }
        };
        handler.postDelayed(periodicUpdateRunnable, 30000);

        updateNotification();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        updateNotification();
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        try {
            unregisterReceiver(batteryReceiver);
            unregisterReceiver(screenReceiver);
        } catch (Exception ignored) {}
        if (handler != null && periodicUpdateRunnable != null) {
            handler.removeCallbacks(periodicUpdateRunnable);
        }
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID,
                    "Lock Screen Live Stats",
                    NotificationManager.IMPORTANCE_LOW
            );
            channel.setDescription("Real-time battery remaining hours and daily screen time usage on lock screen");
            channel.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC);
            channel.setShowBadge(false);
            channel.enableVibration(false);
            channel.setSound(null, null);
            if (notificationManager != null) {
                notificationManager.createNotificationChannel(channel);
            }
        }
    }

    private void updateNotification() {
        checkAndResetMidnight();
        Notification notif = computeAndBuildNotification();
        if (notificationManager != null) {
            notificationManager.notify(NOTIFICATION_ID, notif);
        }
    }

    private Notification computeAndBuildNotification() {
        boolean isCharging = (batteryStatus == BatteryManager.BATTERY_STATUS_CHARGING ||
                              batteryStatus == BatteryManager.BATTERY_STATUS_FULL);

        String batteryTitle;
        String batteryDetail;

        if (isCharging) {
            long chargeRemainMs = -1;
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                BatteryManager bm = (BatteryManager) getSystemService(Context.BATTERY_SERVICE);
                if (bm != null) {
                    chargeRemainMs = bm.computeChargeTimeRemaining();
                }
            }

            String timeStr;
            if (chargeRemainMs > 0) {
                long mins = chargeRemainMs / 60000;
                long h = mins / 60;
                long m = mins % 60;
                timeStr = (h > 0) ? (h + "h " + m + "m") : (m + "m");
            } else {
                int percentLeft = 100 - (batteryLevel > 0 ? batteryLevel : 0);
                int estMins = (int) (percentLeft * 0.85f);
                long h = estMins / 60;
                long m = estMins % 60;
                timeStr = (h > 0) ? (h + "h " + m + "m") : (m + "m");
            }

            batteryTitle = "⚡ " + batteryLevel + "% • Full in ~" + timeStr;
            batteryDetail = "Charging (" + batteryLevel + "%, ~" + timeStr + " to full)";
        } else {
            // Discharging: Dimensity 7050 + 5000mAh typical mixed discharge ~ 5.5% / hour
            float effectiveRate = 5.5f;
            float hoursRemaining = (batteryLevel > 0 ? batteryLevel : 50) / effectiveRate;
            int h = (int) hoursRemaining;
            int m = (int) ((hoursRemaining - h) * 60);
            batteryTitle = "🔋 " + batteryLevel + "% • ~" + h + "h " + m + "m left";
            batteryDetail = "Discharging (~" + h + "h " + m + "m battery life left)";
        }

        // Calculate Screen-On Time
        long totalScreenOnMs = getTodayScreenTime();
        if (isScreenOn && screenOnTimestamp > 0) {
            totalScreenOnMs += (System.currentTimeMillis() - screenOnTimestamp);
        }

        long sHours = totalScreenOnMs / 3600000;
        long sMins = (totalScreenOnMs % 3600000) / 60000;
        int unlocks = prefs.getInt("unlocks_" + todayDateStr, 0);

        String usageLine = "⏱️ " + sHours + "h " + String.format(Locale.US, "%02dm", sMins) + " screen  •  📱 " + unlocks + " unlocks";

        String bigText = "🔋 Battery: " + batteryLevel + "% (" + batteryTemp + "°C)\n" +
                         "⚡ " + batteryDetail + "\n" +
                         "⏱️ Screen-on Today: " + sHours + "h " + sMins + "m\n" +
                         "📱 Phone Unlocks: " + unlocks + " times";

        return buildNotification(batteryTitle, usageLine, bigText);
    }

    private Notification buildNotification(String title, String content) {
        return buildNotification(title, content, content);
    }

    private Notification buildNotification(String title, String content, String bigText) {
        Intent intent = new Intent(this, MainActivity.class);
        PendingIntent pi = PendingIntent.getActivity(
                this, 0, intent,
                PendingIntent.FLAG_UPDATE_CURRENT | (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M ? PendingIntent.FLAG_IMMUTABLE : 0)
        );

        Notification.Builder builder;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            builder = new Notification.Builder(this, CHANNEL_ID);
        } else {
            builder = new Notification.Builder(this);
        }

        builder.setSmallIcon(R.drawable.ic_stat)
                .setContentTitle(title)
                .setContentText(content)
                .setStyle(new Notification.BigTextStyle().bigText(bigText))
                .setOngoing(true)
                .setVisibility(Notification.VISIBILITY_PUBLIC)
                .setCategory(Notification.CATEGORY_STATUS)
                .setShowWhen(false)
                .setContentIntent(pi);

        return builder.build();
    }

    private String getTodayDateKey() {
        return new SimpleDateFormat("yyyyMMdd", Locale.US).format(new Date());
    }

    private void checkAndResetMidnight() {
        String current = getTodayDateKey();
        if (!current.equals(todayDateStr)) {
            todayDateStr = current;
            syncHistoricalUsageStats();
        }
    }

    private long getTodayScreenTime() {
        long stored = prefs.getLong("screen_time_" + todayDateStr, -1);
        if (stored < 0) {
            long historical = syncHistoricalUsageStats();
            return historical;
        }
        return stored;
    }

    private void addScreenTimeSession(long durationMs) {
        if (durationMs <= 0 || durationMs > 86400000) return;
        long current = prefs.getLong("screen_time_" + todayDateStr, 0);
        prefs.edit().putLong("screen_time_" + todayDateStr, current + durationMs).apply();
    }

    private void incrementUnlockCount() {
        int c = prefs.getInt("unlocks_" + todayDateStr, 0);
        prefs.edit().putInt("unlocks_" + todayDateStr, c + 1).apply();
    }

    private long syncHistoricalUsageStats() {
        long totalAppTime = 0;
        try {
            UsageStatsManager usm = (UsageStatsManager) getSystemService(Context.USAGE_STATS_SERVICE);
            if (usm != null) {
                Calendar cal = Calendar.getInstance();
                cal.set(Calendar.HOUR_OF_DAY, 0);
                cal.set(Calendar.MINUTE, 0);
                cal.set(Calendar.SECOND, 0);
                cal.set(Calendar.MILLISECOND, 0);
                long startOfDay = cal.getTimeInMillis();
                long now = System.currentTimeMillis();

                List<UsageStats> stats = usm.queryUsageStats(UsageStatsManager.INTERVAL_DAILY, startOfDay, now);
                if (stats != null) {
                    for (UsageStats u : stats) {
                        String pkg = u.getPackageName();
                        if (!"com.android.systemui".equals(pkg) &&
                            !"com.android.launcher".equals(pkg) &&
                            !"com.oplus.wallpapers".equals(pkg)) {
                            totalAppTime += u.getTotalTimeInForeground();
                        }
                    }
                }
            }
        } catch (Exception ignored) {}

        if (totalAppTime > 0) {
            prefs.edit().putLong("screen_time_" + todayDateStr, totalAppTime).apply();
        }
        return totalAppTime;
    }
}
