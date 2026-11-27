import { Link, Tabs } from "expo-router";
import React from "react";
import { Text } from "react-native";
import { brand } from "../../src/brand";
import { t } from "../../src/i18n";
import { useTheme } from "../../src/theme";

function icon(emoji: string) {
  return ({ focused }: { focused: boolean }) => <Text style={{ fontSize: 20, opacity: focused ? 1 : 0.55 }}>{emoji}</Text>;
}

export default function TabsLayout() {
  const { theme } = useTheme();
  return (
    <Tabs
      screenOptions={{
        headerStyle: { backgroundColor: theme.colors.surface },
        headerTintColor: theme.colors.text,
        headerTitleStyle: { fontWeight: "700" },
        tabBarStyle: { backgroundColor: theme.colors.surface, borderTopColor: theme.colors.border },
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.textMuted,
        sceneStyle: { backgroundColor: theme.colors.background },
        headerRight: () => (
          <Link href="/settings" accessibilityLabel={t("settings")} style={{ color: theme.colors.primary, fontSize: 22, paddingHorizontal: 12 }}>
            ⚙︎
          </Link>
        ),
      }}
    >
      <Tabs.Screen name="index" options={{ title: t("tabLessons"), headerTitle: brand.appName, tabBarIcon: icon("📘") }} />
      <Tabs.Screen name="gallery" options={{ title: t("tabGallery"), tabBarIcon: icon("🖼️") }} />
      <Tabs.Screen name="schedule" options={{ title: t("tabSchedule"), tabBarIcon: icon("🗓️") }} />
      <Tabs.Screen name="activities" options={{ title: t("tabActivities"), tabBarIcon: icon("⭐") }} />
    </Tabs>
  );
}
