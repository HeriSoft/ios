import React from "react";
import { ScrollView, View } from "react-native";
import { COLORS, IconText, Pill, Section, Txt } from "../src/components/kit";
import { exerciseById, isRest, weeklyMinutes, workoutPlan } from "../src/core/exercise";
import { bmiCategory, bmiOf, GOAL_TITLE, isValidProfile } from "../src/core/health";
import { useStore } from "../src/state/store";

export default function PlanScreen() {
  const { profile } = useStore();
  const category = isValidProfile(profile) ? bmiCategory(bmiOf(profile.weightKg, profile.heightCm)) : undefined;
  const plan = workoutPlan(profile.goal, profile.age, category);
  return (
    <ScrollView contentContainerStyle={{ padding: 16, gap: 16, maxWidth: 760, width: "100%", alignSelf: "center" }}>
      <Section>
        <Txt bold size={17}>Mục tiêu: {GOAL_TITLE[profile.goal]}</Txt>
        <Txt muted>Tổng {weeklyMinutes(plan)} phút mỗi tuần{plan.lowImpact ? " · ít tác động lên khớp" : ""}</Txt>
      </Section>
      <Section title="Lịch trong tuần">
        {plan.days.map((d) => (
          <View key={d.day} style={{ gap: 4, paddingVertical: 6 }}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
              <Txt bold>{d.day}</Txt>
              <Txt>{d.title}</Txt>
              <View style={{ flex: 1 }} />
              {isRest(d) ? <Pill text="Nghỉ" color={COLORS.blue} /> : <Pill text={`${d.minutes} phút`} color={COLORS.green} />}
            </View>
            {!isRest(d) ? <Txt muted size={13}>{d.exerciseIDs.map((id) => exerciseById(id)?.name ?? id).join(" · ")}</Txt> : null}
          </View>
        ))}
      </Section>
      <Section title="Lưu ý">
        {plan.notes.map((n) => <IconText key={n} icon="information-circle-outline" color={COLORS.blue} text={n} />)}
      </Section>
    </ScrollView>
  );
}
