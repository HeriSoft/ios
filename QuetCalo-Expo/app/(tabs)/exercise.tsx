import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import React, { useMemo, useState } from "react";
import { Pressable, ScrollView, View } from "react-native";
import { CATEGORY_ICON } from "../../src/components/exerciseIcon";
import { COLORS, NavRow, NumberField, Row, Section, SmallButton, Txt } from "../../src/components/kit";
import { Button, Input } from "../../src/components/ui";
import { kcalText } from "../../src/core/basics";
import { CATEGORY_TITLE, Exercise, exerciseKcal, searchExercises } from "../../src/core/exercise";
import { isToday, timeText, useStore } from "../../src/state/store";
import { useTheme } from "../../src/theme";

export default function ExerciseScreen() {
  const store = useStore();
  const { theme } = useTheme();
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Exercise>();
  const [minutes, setMinutes] = useState<number | undefined>(30);
  const list = useMemo(() => searchExercises(query), [query]);
  const today = store.workouts.filter((w) => isToday(w.time));
  const burned = today.reduce((s, w) => s + w.kcal, 0);
  const todayMinutes = today.reduce((s, w) => s + w.minutes, 0);
  const weight = store.profile.weightKg;
  const kcal = selected && minutes ? exerciseKcal(selected.met, weight, minutes) : undefined;

  function save() {
    if (!selected || !minutes || kcal == null) return;
    store.addWorkout({ name: selected.name, exerciseId: selected.id, minutes, kcal });
    setSelected(undefined);
  }

  return (
    <ScrollView contentContainerStyle={{ padding: 16, gap: 16, maxWidth: 760, width: "100%", alignSelf: "center" }} keyboardShouldPersistTaps="handled">
      <Section>
        <View style={{ flexDirection: "row" }}>
          {[["Đã đốt hôm nay", kcalText(burned), COLORS.orange], ["Thời gian", `${todayMinutes} phút`, COLORS.blue], ["Buổi tập", `${today.length}`, COLORS.green]].map(([l, v, c]) => (
            <View key={l} style={{ flex: 1, alignItems: "center", gap: 2 }}>
              <Txt bold size={20} color={c}>{v}</Txt>
              <Txt muted size={12}>{l}</Txt>
            </View>
          ))}
        </View>
      </Section>
      <Section>
        <NavRow icon="calendar-outline" title="Lịch tập gợi ý" subtitle="Theo mục tiêu và thể trạng của bạn" color={COLORS.green} onPress={() => router.push("/plan")} />
        <NavRow icon="home-outline" title="Bài tập tại nhà" subtitle="Không cần dụng cụ, có hướng dẫn từng bước" color={COLORS.cyan} onPress={() => router.push("/home-workout")} />
      </Section>
      {selected ? (
        <Section title={`Ghi buổi tập: ${selected.name}`} footer={`Ước tính theo MET ${selected.met} và cân nặng ${weight} kg (sửa ở tab Cơ thể).`}>
          <View style={{ flexDirection: "row", alignItems: "flex-end", gap: 8 }}>
            <SmallButton label="−" onPress={() => setMinutes(Math.max(5, (minutes ?? 0) - 5))} />
            <NumberField label="Thời gian" value={minutes} onChange={setMinutes} suffix="phút" />
            <SmallButton label="+" onPress={() => setMinutes((minutes ?? 0) + 5)} />
          </View>
          <Row label="Calo đốt" value={kcal != null ? kcalText(kcal) : "—"} color={COLORS.orange} bold />
          <View style={{ flexDirection: "row", gap: 10 }}>
            <View style={{ flex: 1 }}><Button label="Hủy" variant="secondary" onPress={() => setSelected(undefined)} /></View>
            <View style={{ flex: 1 }}><Button label="Lưu buổi tập" disabled={kcal == null} onPress={save} /></View>
          </View>
        </Section>
      ) : null}
      {today.length ? (
        <Section title="Hôm nay">
          {today.map((w) => (
            <View key={w.id} style={{ flexDirection: "row", alignItems: "center", gap: 10, paddingVertical: 4 }}>
              <View style={{ flex: 1 }}>
                <Txt>{w.name}</Txt>
                <Txt muted size={12}>{timeText(w.time)} · {w.minutes} phút</Txt>
              </View>
              <Txt bold color={COLORS.orange}>{kcalText(w.kcal)}</Txt>
              <Pressable onPress={() => store.removeWorkout(w.id)} accessibilityLabel={`Xóa ${w.name}`} hitSlop={8}>
                <Ionicons name="trash-outline" size={18} color={COLORS.red} />
              </Pressable>
            </View>
          ))}
        </Section>
      ) : null}
      <Section title="Chọn môn tập">
        <Input placeholder="Tìm: chạy bộ, bơi, cầu lông…" value={query} onChangeText={setQuery} />
        {list.map((e) => (
          <Pressable key={e.id} onPress={() => { setSelected(e); setMinutes(30); }} accessibilityRole="button"
            style={{ flexDirection: "row", alignItems: "center", gap: 12, paddingVertical: 8 }}>
            <Ionicons name={CATEGORY_ICON[e.category]} size={20} color={COLORS.green} />
            <View style={{ flex: 1 }}>
              <Txt>{e.name}</Txt>
              <Txt muted size={12}>{CATEGORY_TITLE[e.category]} · ~{kcalText(exerciseKcal(e.met, weight, 30))} / 30 phút</Txt>
            </View>
            <Ionicons name="add-circle-outline" size={22} color={theme.colors.primary} />
          </Pressable>
        ))}
      </Section>
    </ScrollView>
  );
}
