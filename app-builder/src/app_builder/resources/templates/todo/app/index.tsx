import { Link, Stack, useRouter } from "expo-router";
import React, { useMemo, useState } from "react";
import { FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import { Button, EmptyState, ErrorState, LoadingState, Screen } from "../src/components/ui";
import { t } from "../src/i18n";
import { useTodos } from "../src/state/TodoContext";
import { Todo } from "../src/storage/todos";
import { useTheme } from "../src/theme";

type Filter = "all" | "active" | "done";

export default function TodoList() {
  const { theme } = useTheme();
  const router = useRouter();
  const { todos, loading, error, reload, toggle } = useTodos();
  const [filter, setFilter] = useState<Filter>("all");

  const visible = useMemo(
    () => todos.filter((x) => (filter === "all" ? true : filter === "done" ? x.done : !x.done)),
    [todos, filter],
  );
  const doneCount = todos.filter((x) => x.done).length;

  const headerRight = () => (
    <Link href="/settings" accessibilityLabel={t("settings")} style={{ color: theme.colors.primary, fontSize: 22, paddingHorizontal: 8 }}>
      ⚙︎
    </Link>
  );

  if (loading) return <Screen><Stack.Screen options={{ headerRight }} /><LoadingState /></Screen>;
  if (error && todos.length === 0) return <Screen><ErrorState message={error} onRetry={reload} /></Screen>;

  const renderItem = ({ item }: { item: Todo }) => (
    <Pressable
      onPress={() => router.push({ pathname: "/edit", params: { id: item.id } })}
      accessibilityRole="button"
      accessibilityLabel={item.title}
      style={({ pressed }) => [
        styles.row,
        {
          backgroundColor: theme.colors.surface,
          borderColor: theme.colors.border,
          borderRadius: theme.radius,
          opacity: pressed ? 0.85 : 1,
        },
      ]}
    >
      <Pressable
        onPress={() => toggle(item.id).catch(() => undefined)}
        accessibilityRole="checkbox"
        accessibilityState={{ checked: item.done }}
        hitSlop={10}
        style={[
          styles.check,
          { borderColor: item.done ? theme.colors.success : theme.colors.border, backgroundColor: item.done ? theme.colors.success : "transparent" },
        ]}
      >
        {item.done ? <Text style={{ color: "#fff", fontWeight: "800" }}>✓</Text> : null}
      </Pressable>
      <View style={{ flex: 1 }}>
        <Text
          style={{
            color: item.done ? theme.colors.textMuted : theme.colors.text,
            fontSize: 16,
            fontWeight: "600",
            textDecorationLine: item.done ? "line-through" : "none",
          }}
          numberOfLines={1}
        >
          {item.title}
        </Text>
        {item.note ? <Text style={{ color: theme.colors.textMuted, marginTop: 2 }} numberOfLines={1}>{item.note}</Text> : null}
      </View>
    </Pressable>
  );

  return (
    <Screen>
      <Stack.Screen options={{ headerRight }} />
      <View style={[styles.filters, { backgroundColor: theme.colors.surfaceAlt, borderRadius: theme.radius }]}>
        {(["all", "active", "done"] as Filter[]).map((f) => {
          const active = f === filter;
          const label = f === "all" ? t("filterAll") : f === "active" ? t("filterActive") : t("filterDone");
          return (
            <Pressable
              key={f}
              onPress={() => setFilter(f)}
              accessibilityRole="tab"
              accessibilityState={{ selected: active }}
              style={[styles.filter, { backgroundColor: active ? theme.colors.surface : "transparent", borderRadius: theme.radius - 4 }]}
            >
              <Text style={{ color: active ? theme.colors.primary : theme.colors.textMuted, fontWeight: "700" }}>{label}</Text>
            </Pressable>
          );
        })}
      </View>
      <Text style={{ color: theme.colors.textMuted, marginVertical: 10 }}>
        {t("stats", { done: doneCount, total: todos.length })}
      </Text>
      {visible.length === 0 ? (
        <EmptyState
          icon={todos.length === 0 ? "📝" : "🔍"}
          title={todos.length === 0 ? t("emptyTitle") : t("emptyFiltered")}
          message={todos.length === 0 ? t("emptyMessage") : undefined}
          action={todos.length === 0 ? <Button label={t("add")} onPress={() => router.push("/edit")} /> : undefined}
        />
      ) : (
        <FlatList
          data={visible}
          keyExtractor={(x) => x.id}
          renderItem={renderItem}
          ItemSeparatorComponent={() => <View style={{ height: 8 }} />}
          contentContainerStyle={{ paddingBottom: 96 }}
        />
      )}
      <Pressable
        onPress={() => router.push("/edit")}
        accessibilityRole="button"
        accessibilityLabel={t("add")}
        style={({ pressed }) => [styles.fab, { backgroundColor: theme.colors.primary, opacity: pressed ? 0.85 : 1 }]}
      >
        <Text style={{ color: theme.colors.primaryText, fontSize: 30, lineHeight: 32 }}>+</Text>
      </Pressable>
    </Screen>
  );
}

const styles = StyleSheet.create({
  filters: { flexDirection: "row", padding: 4, gap: 4 },
  filter: { flex: 1, paddingVertical: 8, alignItems: "center" },
  row: { flexDirection: "row", alignItems: "center", gap: 12, padding: 14, borderWidth: StyleSheet.hairlineWidth },
  check: { width: 26, height: 26, borderRadius: 13, borderWidth: 2, alignItems: "center", justifyContent: "center" },
  fab: {
    position: "absolute",
    right: 20,
    bottom: 24,
    width: 60,
    height: 60,
    borderRadius: 30,
    alignItems: "center",
    justifyContent: "center",
    elevation: 4,
    shadowColor: "#000",
    shadowOpacity: 0.2,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 4 },
  },
});
