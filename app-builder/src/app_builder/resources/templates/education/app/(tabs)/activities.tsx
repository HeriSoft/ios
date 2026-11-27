import React from "react";
import { Pressable, ScrollView, Text, View } from "react-native";
import { LoadingState, Screen } from "../../src/components/ui";
import { content } from "../../src/data/content";
import { t } from "../../src/i18n";
import { todayKey, useProgress } from "../../src/state/ProgressContext";
import { useTheme } from "../../src/theme";

export default function Activities() {
  const { theme } = useTheme();
  const { progress, loading, toggleActivity } = useProgress();
  if (loading) return <Screen><LoadingState /></Screen>;
  const done = progress.activities[todayKey()] ?? [];

  return (
    <Screen>
      <Text style={{ color: theme.colors.text, fontSize: 18, fontWeight: "700" }}>{t("todayActivities")}</Text>
      <Text style={{ color: theme.colors.textMuted, marginTop: 4, marginBottom: 12 }}>
        {t("activitiesDone", { done: done.length, total: content.activities.length })}
      </Text>
      <ScrollView contentContainerStyle={{ gap: 10 }}>
        {content.activities.map((a) => {
          const checked = done.includes(a.id);
          return (
            <Pressable
              key={a.id}
              onPress={() => toggleActivity(a.id)}
              accessibilityRole="checkbox"
              accessibilityState={{ checked }}
              style={{
                flexDirection: "row",
                alignItems: "center",
                gap: 14,
                padding: 14,
                borderRadius: theme.radius,
                backgroundColor: checked ? theme.colors.surfaceAlt : theme.colors.surface,
                borderWidth: 1,
                borderColor: checked ? theme.colors.success : theme.colors.border,
              }}
            >
              <Text style={{ fontSize: 26 }}>{a.emoji}</Text>
              <Text style={{ flex: 1, color: theme.colors.text, fontSize: 16, textDecorationLine: checked ? "line-through" : "none" }}>{a.title}</Text>
              <View style={{ width: 26, height: 26, borderRadius: 8, borderWidth: 2, borderColor: checked ? theme.colors.success : theme.colors.border, backgroundColor: checked ? theme.colors.success : "transparent", alignItems: "center", justifyContent: "center" }}>
                {checked ? <Text style={{ color: "#fff", fontWeight: "800" }}>✓</Text> : null}
              </View>
            </Pressable>
          );
        })}
      </ScrollView>
    </Screen>
  );
}
