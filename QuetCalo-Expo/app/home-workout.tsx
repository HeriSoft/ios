import { router } from "expo-router";
import React from "react";
import { ScrollView } from "react-native";
import { COLORS, NavRow, Section } from "../src/components/kit";
import { HOME_MOVES } from "../src/core/exercise";

export default function HomeWorkoutScreen() {
  return (
    <ScrollView contentContainerStyle={{ padding: 16, gap: 16, maxWidth: 760, width: "100%", alignSelf: "center" }}>
      <Section title="Không cần dụng cụ" footer="Gợi ý: làm lần lượt các động tác, nghỉ 30–60 giây giữa các hiệp, 2–3 buổi mỗi tuần.">
        {HOME_MOVES.map((m) => (
          <NavRow key={m.id} icon="fitness-outline" color={COLORS.cyan} title={m.name} subtitle={`${m.target} · ${m.reps}`} onPress={() => router.push(`/move/${m.id}`)} />
        ))}
      </Section>
    </ScrollView>
  );
}
