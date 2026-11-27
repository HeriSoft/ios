import { Ionicons } from "@expo/vector-icons";
import { Tabs } from "expo-router";
import React from "react";
import { useTheme } from "../../src/theme";

const icon = (name: keyof typeof Ionicons.glyphMap) =>
  ({ color, size }: { color: unknown; size: number }) => <Ionicons name={name} color={String(color)} size={size} />;

export default function TabsLayout() {
  const { theme } = useTheme();
  return (
    <Tabs
      screenOptions={{
        headerStyle: { backgroundColor: theme.colors.surface },
        headerTintColor: theme.colors.text,
        headerTitleStyle: { fontWeight: "700" },
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.textMuted,
        tabBarStyle: { backgroundColor: theme.colors.surface, borderTopColor: theme.colors.border },
        sceneStyle: { backgroundColor: theme.colors.background },
      }}
    >
      <Tabs.Screen name="index" options={{ title: "Quét", headerTitle: "Quét sản phẩm", tabBarIcon: icon("barcode-outline") }} />
      <Tabs.Screen name="food" options={{ title: "Món ăn", tabBarIcon: icon("restaurant-outline") }} />
      <Tabs.Screen name="exercise" options={{ title: "Tập luyện", tabBarIcon: icon("walk-outline") }} />
      <Tabs.Screen name="body" options={{ title: "Cơ thể", tabBarIcon: icon("body-outline") }} />
      <Tabs.Screen name="log" options={{ title: "Nhật ký", headerTitle: "Nhật ký calo", tabBarIcon: icon("book-outline") }} />
    </Tabs>
  );
}
