import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import React from "react";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { t } from "../src/i18n";
import { StoreProvider } from "../src/state/store";
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
          headerBackTitle: "Quay lại",
        }}
      >
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="product" options={{ title: "Sản phẩm" }} />
        <Stack.Screen name="lookup/[code]" options={{ title: "Tra cứu" }} />
        <Stack.Screen name="label" options={{ title: "Quét nhãn dinh dưỡng" }} />
        <Stack.Screen name="manual" options={{ title: "Nhập thủ công" }} />
        <Stack.Screen name="qr-text" options={{ title: "Mã QR" }} />
        <Stack.Screen name="plan" options={{ title: "Lịch tập gợi ý" }} />
        <Stack.Screen name="home-workout" options={{ title: "Bài tập tại nhà" }} />
        <Stack.Screen name="move/[id]" options={{ title: "Động tác" }} />
        <Stack.Screen name="symptoms" options={{ title: "Kiểm tra triệu chứng" }} />
        <Stack.Screen name="symptom-result" options={{ title: "Đánh giá" }} />
        <Stack.Screen name="condition/[id]" options={{ title: "Nguyên nhân" }} />
        <Stack.Screen name="settings" options={{ title: t("settings") }} />
      </Stack>
    </>
  );
}

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <ThemeProvider>
        <StoreProvider>
          <ThemedStack />
        </StoreProvider>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}
