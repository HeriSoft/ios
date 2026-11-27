import { Stack, useLocalSearchParams } from "expo-router";
import React from "react";
import { Text, View } from "react-native";
import { Button, Card, EmptyState, Screen } from "../../src/components/ui";
import { content } from "../../src/data/content";
import { t } from "../../src/i18n";
import { useProgress } from "../../src/state/ProgressContext";
import { useTheme } from "../../src/theme";

export default function LessonDetail() {
  const { theme } = useTheme();
  const { id } = useLocalSearchParams<{ id: string }>();
  const lesson = content.lessons.find((l) => l.id === id);
  const { progress, toggleLearned } = useProgress();

  if (!lesson) return <Screen><EmptyState icon="🔍" title={t("lessonNotFound")} /></Screen>;
  const learned = progress.learned.includes(lesson.id);

  return (
    <Screen scroll>
      <Stack.Screen options={{ title: lesson.title }} />
      <View style={{ gap: 16 }}>
        <View style={{ backgroundColor: lesson.color, borderRadius: theme.radius * 1.5, padding: 28, alignItems: "center" }}>
          <Text style={{ fontSize: 80 }}>{lesson.emoji}</Text>
          <Text style={{ color: "#fff", fontSize: 26, fontWeight: "800", marginTop: 8 }}>{lesson.title}</Text>
          <Text style={{ color: "#ffffffdd", marginTop: 4 }}>{lesson.summary}</Text>
        </View>
        <Card style={{ gap: 12 }}>
          <Text style={{ color: theme.colors.text, fontSize: 18, fontWeight: "700" }}>{t("steps")}</Text>
          {lesson.steps.map((s, i) => (
            <View key={s} style={{ flexDirection: "row", gap: 12, alignItems: "flex-start" }}>
              <View style={{ width: 28, height: 28, borderRadius: 14, backgroundColor: theme.colors.primary, alignItems: "center", justifyContent: "center" }}>
                <Text style={{ color: theme.colors.primaryText, fontWeight: "700" }}>{i + 1}</Text>
              </View>
              <Text style={{ flex: 1, color: theme.colors.text, fontSize: 16, lineHeight: 26 }}>{s}</Text>
            </View>
          ))}
        </Card>
        <Button
          label={learned ? t("unmarkLearned") : t("markLearned")}
          variant={learned ? "secondary" : "primary"}
          onPress={() => toggleLearned(lesson.id)}
        />
      </View>
    </Screen>
  );
}
