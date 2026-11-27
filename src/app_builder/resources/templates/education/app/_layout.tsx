import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import React from "react";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { t } from "../src/i18n";
import { ProgressProvider } from "../src/state/ProgressContext";
import { ThemeProvider, useTheme } from "../src/theme";

function ThemedStack() {
  const { theme } = useTheme();
  return (
    <>
      <StatusBar style={theme.dark ? "light" : "dark"} />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: theme.colors.surface },
          headerTintColor: theme.colors.text,
          headerTitleStyle: { fontWeight: "700" },
          contentStyle: { backgroundColor: theme.colors.background },
        }}
      >
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="lesson/[id]" options={{ title: "" }} />
        <Stack.Screen name="settings" options={{ title: t("settings") }} />
      </Stack>
    </>
  );
}

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <ThemeProvider>
        <ProgressProvider>
          <ThemedStack />
        </ProgressProvider>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}
