import { Ionicons } from "@expo/vector-icons";
import React from "react";
import { Pressable, ScrollView, View } from "react-native";
import { COLORS, Row, Section, SmallButton, Txt } from "../../src/components/kit";
import { EmptyState } from "../../src/components/ui";
import { kcalText, shortText } from "../../src/core/basics";
import { dayKey, dayTitle, isToday, timeText, useStore } from "../../src/state/store";
import { useTheme } from "../../src/theme";

export default function LogScreen() {
  const store = useStore();
  const { theme } = useTheme();
  const eaten = store.foods.filter((f) => isToday(f.time)).reduce((s, f) => s + f.kcal, 0);
  const burned = store.workouts.filter((w) => isToday(w.time)).reduce((s, w) => s + w.kcal, 0);
  const remaining = store.dailyGoal - eaten + burned;
  const progress = Math.min(1, eaten / Math.max(1, store.dailyGoal + burned));

  const groups = new Map<string, typeof store.foods>();
  for (const f of [...store.foods].sort((a, b) => b.time - a.time)) {
    const k = dayKey(f.time);
    groups.set(k, [...(groups.get(k) ?? []), f]);
  }

  return (
    <ScrollView contentContainerStyle={{ padding: 16, gap: 16, maxWidth: 760, width: "100%", alignSelf: "center" }}>
      <Section title="Hôm nay">
        <View style={{ alignItems: "center", gap: 2, paddingVertical: 6 }}>
          <Txt bold size={34} color={remaining >= 0 ? COLORS.green : COLORS.red}>{kcalText(Math.abs(remaining))}</Txt>
          <Txt muted>{remaining >= 0 ? "còn lại" : "vượt mục tiêu"}</Txt>
        </View>
        <View style={{ height: 10, borderRadius: 5, backgroundColor: theme.colors.surfaceAlt, overflow: "hidden" }}>
          <View style={{ width: `${progress * 100}%`, height: "100%", backgroundColor: remaining >= 0 ? COLORS.orange : COLORS.red }} />
        </View>
        <Row label="Đã ăn" value={kcalText(eaten)} color={COLORS.orange} />
        <Row label="Đã đốt khi tập" value={kcalText(burned)} color={COLORS.green} />
        <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
          <Txt>Mục tiêu</Txt>
          <View style={{ flex: 1 }} />
          <SmallButton label="−" onPress={() => store.setDailyGoal(store.dailyGoal - 50)} />
          <Txt bold>{kcalText(store.dailyGoal)}</Txt>
          <SmallButton label="+" onPress={() => store.setDailyGoal(store.dailyGoal + 50)} />
        </View>
      </Section>
      {groups.size === 0 ? (
        <EmptyState icon="🍽️" title="Chưa có món nào" message="Quét mã vạch hoặc tìm món ăn rồi bấm “Thêm vào nhật ký”." />
      ) : [...groups.entries()].map(([k, items]) => (
        <Section key={k} title={`${dayTitle(items[0].time)} · ${kcalText(items.reduce((s, f) => s + f.kcal, 0))}`}>
          {items.map((f) => (
            <View key={f.id} style={{ flexDirection: "row", alignItems: "center", gap: 10, paddingVertical: 4 }}>
              <View style={{ flex: 1 }}>
                <Txt>{f.name}</Txt>
                <Txt muted size={12}>{timeText(f.time)} · {shortText(f.amount)} {f.unit}</Txt>
              </View>
              <Txt bold color={COLORS.orange}>{kcalText(f.kcal)}</Txt>
              <Pressable onPress={() => store.removeFood(f.id)} accessibilityLabel={`Xóa ${f.name}`} hitSlop={8}>
                <Ionicons name="trash-outline" size={18} color={COLORS.red} />
              </Pressable>
            </View>
          ))}
        </Section>
      ))}
    </ScrollView>
  );
}
