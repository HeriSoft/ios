import { Stack, useLocalSearchParams } from "expo-router";
import React from "react";
import { ScrollView } from "react-native";
import { COLORS, Disclaimer, IconText, Pill, Section, Txt } from "../../src/components/kit";
import { EmptyState } from "../../src/components/ui";
import { foodById } from "../../src/core/foods";
import { assess, CARE, CONDITIONS } from "../../src/core/symptoms";
import { useStore } from "../../src/state/store";
import { LEVEL_COLOR } from "../../src/components/levels";

export default function ConditionScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { symptomInput } = useStore();
  const c = CONDITIONS.find((x) => x.id === id);
  if (!c) return <EmptyState title="Không tìm thấy" />;
  const meds = assess(symptomInput).showMedicationAdvice;
  const names = (ids: string[]) => ids.map((f) => foodById(f)?.name ?? f).join(", ");
  const list = (items: string[], icon: Parameters<typeof IconText>[0]["icon"], color: string) =>
    items.map((t) => <IconText key={t} icon={icon} color={color} text={t} />);
  return (
    <ScrollView contentContainerStyle={{ padding: 16, gap: 16, maxWidth: 760, width: "100%", alignSelf: "center" }}>
      <Stack.Screen options={{ title: c.name }} />
      <Section>
        <Txt>{c.summary}</Txt>
        <Pill text={CARE[c.minimumLevel].title} color={LEVEL_COLOR[c.minimumLevel]} />
        <Txt muted size={13}>Chuyên khoa: {c.specialty}</Txt>
      </Section>
      <Section title="Chăm sóc và nghỉ ngơi">{list(c.selfCare, "bed-outline", COLORS.blue)}</Section>
      <Section title="Ăn uống">
        {c.eatFoodIDs.length ? <IconText icon="checkmark-circle-outline" color={COLORS.green} text={`Nên ăn: ${names(c.eatFoodIDs)}`} /> : null}
        {c.avoidFoodIDs.length ? <IconText icon="close-circle-outline" color={COLORS.red} text={`Nên tránh: ${names(c.avoidFoodIDs)}`} /> : null}
      </Section>
      {meds ? (
        <>
          {c.otcMedicines.length ? (
            <Section title="Nhóm thuốc không kê đơn thường dùng" footer="Đọc kỹ hướng dẫn, hỏi dược sĩ về liều. Không dùng nếu dị ứng hoặc có bệnh nền chưa hỏi bác sĩ.">
              {list(c.otcMedicines, "medkit-outline", COLORS.cyan)}
            </Section>
          ) : null}
          {c.homeRemedies.length ? (
            <Section title="Mẹo dân gian (hỗ trợ, không thay thuốc)">{list(c.homeRemedies, "leaf-outline", COLORS.green)}</Section>
          ) : null}
        </>
      ) : (
        <IconText icon="alert-circle-outline" color={COLORS.orange} text="Không gợi ý thuốc/thảo dược cho trẻ dưới 5 tuổi và phụ nữ mang thai. Hãy hỏi bác sĩ." />
      )}
      <Section title="Đi khám ngay nếu">{list(c.seeDoctorIf, "warning-outline", COLORS.red)}</Section>
      <Disclaimer />
    </ScrollView>
  );
}
