import { useRouter } from "expo-router";
import React from "react";
import { FlatList, Pressable, Text, View } from "react-native";
import { ErrorState, LoadingState, Screen } from "../../src/components/ui";
import { content, Lesson } from "../../src/data/content";
import { t } from "../../src/i18n";
import { useProgress } from "../../src/state/ProgressContext";
import { useTheme } from "../../src/theme";

export default function Lessons() {
  const { theme } = useTheme();
  const router = useRouter();
  const { progress, loading, error, reload } = useProgress();

  if (loading) return <Screen><LoadingState /></Screen>;
  if (error) return <Screen><ErrorState message={error} onRetry={reload} /></Screen>;

  const done = content.lessons.filter((l) => progress.learned.includes(l.id)).length;
  const pct = content.lessons.length ? done / content.lessons.length : 0;

  const renderItem = ({ item }: { item: Lesson }) => {
    const learned = progress.learned.includes(item.id);
    return (
      <Pressable
        onPress={() => router.push({ pathname: "/lesson/[id]", params: { id: item.id } })}
        accessibilityRole="button"
        accessibilityLabel={item.title}
        style={({ pressed }) => ({
          flexDirection: "row",
          alignItems: "center",
          gap: 14,
          padding: 14,
          borderRadius: theme.radius,
          backgroundColor: theme.colors.surface,
          borderWidth: 1,
          borderColor: theme.colors.border,
          opacity: pressed ? 0.85 : 1,
        })}
      >
        <View style={{ width: 52, height: 52, borderRadius: 16, backgroundColor: item.color, alignItems: "center", justifyContent: "center" }}>
          <Text style={{ fontSize: 26 }}>{item.emoji}</Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text style={{ color: theme.colors.text, fontSize: 17, fontWeight: "700" }}>{item.title}</Text>
          <Text style={{ color: theme.colors.textMuted, marginTop: 2 }}>{item.summary}</Text>
        </View>
        {learned ? <Text style={{ color: theme.colors.success, fontWeight: "700" }}>✓ {t("learned")}</Text> : null}
      </Pressable>
    );
  };

  return (
    <Screen>
      <View style={{ marginBottom: 14, gap: 8 }}>
        <Text style={{ color: theme.colors.text, fontWeight: "600" }}>{t("progress", { done, total: content.lessons.length })}</Text>
        <View style={{ height: 10, borderRadius: 5, backgroundColor: theme.colors.surfaceAlt, overflow: "hidden" }}>
          <View style={{ width: `${Math.round(pct * 100)}%`, height: "100%", backgroundColor: theme.colors.primary }} />
        </View>
      </View>
      <FlatList
        data={content.lessons}
        keyExtractor={(x) => x.id}
        renderItem={renderItem}
        ItemSeparatorComponent={() => <View style={{ height: 10 }} />}
      />
    </Screen>
  );
}
