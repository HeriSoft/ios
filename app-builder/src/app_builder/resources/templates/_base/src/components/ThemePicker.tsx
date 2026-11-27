import React from "react";
import { Pressable, Text, View } from "react-native";
import { t } from "../i18n";
import { ThemeMode, useTheme } from "../theme";

export function ThemePicker() {
  const { theme, mode, setMode } = useTheme();
  const options: { value: ThemeMode; label: string }[] = [
    { value: "system", label: t("themeSystem") },
    { value: "light", label: t("themeLight") },
    { value: "dark", label: t("themeDark") },
  ];
  return (
    <View style={{ flexDirection: "row", gap: 8 }} accessibilityRole="radiogroup">
      {options.map((o) => {
        const active = o.value === mode;
        return (
          <Pressable
            key={o.value}
            accessibilityRole="radio"
            accessibilityState={{ selected: active }}
            onPress={() => setMode(o.value)}
            style={{
              flex: 1,
              paddingVertical: 10,
              alignItems: "center",
              borderRadius: theme.radius - 4,
              backgroundColor: active ? theme.colors.primary : theme.colors.surfaceAlt,
            }}
          >
            <Text style={{ color: active ? theme.colors.primaryText : theme.colors.text, fontWeight: "600" }}>{o.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}
