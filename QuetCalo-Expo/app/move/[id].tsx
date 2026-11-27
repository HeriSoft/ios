import { Stack, useLocalSearchParams } from "expo-router";
import React from "react";
import { ScrollView } from "react-native";
import { COLORS, IconText, Row, Section, Txt } from "../../src/components/kit";
import { EmptyState } from "../../src/components/ui";
import { HOME_MOVES } from "../../src/core/exercise";

export default function MoveScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const m = HOME_MOVES.find((x) => x.id === id);
  if (!m) return <EmptyState title="Không tìm thấy động tác" />;
  return (
    <ScrollView contentContainerStyle={{ padding: 16, gap: 16, maxWidth: 760, width: "100%", alignSelf: "center" }}>
      <Stack.Screen options={{ title: m.name }} />
      <Section>
        <Row label="Nhóm cơ" value={m.target} />
        <Row label="Số lần" value={m.reps} bold />
      </Section>
      <Section title="Cách làm">
        {m.steps.map((s, i) => <Txt key={s}>{i + 1}. {s}</Txt>)}
      </Section>
      <Section>
        <IconText icon="arrow-down-circle-outline" color={COLORS.green} text={`Dễ hơn: ${m.easier}`} />
        <IconText icon="warning-outline" color={COLORS.orange} text={`Chú ý: ${m.caution}`} />
      </Section>
    </ScrollView>
  );
}
