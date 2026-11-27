import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import React from "react";
import { Linking, ScrollView, View } from "react-native";
import { COLORS, Disclaimer, IconText, NavRow, Section, Txt } from "../src/components/kit";
import { Button } from "../src/components/ui";
import { assess, CARE, CareLevel } from "../src/core/symptoms";
import { useStore } from "../src/state/store";
import { LEVEL_COLOR } from "../src/components/levels";

const LEVEL_ICON: Record<CareLevel, keyof typeof Ionicons.glyphMap> = { selfCare: "home", seeDoctor: "calendar", urgent: "time", emergency: "warning" };

export default function SymptomResultScreen() {
  const { symptomInput } = useStore();
  const a = assess(symptomInput);
  const color = LEVEL_COLOR[a.level];
  return (
    <ScrollView contentContainerStyle={{ padding: 16, gap: 16, maxWidth: 760, width: "100%", alignSelf: "center" }}>
      <View style={{ borderRadius: 16, padding: 16, gap: 8, backgroundColor: color + "22", borderWidth: 1, borderColor: color }}>
        <View style={{ flexDirection: "row", alignItems: "center", gap: 10 }}>
          <Ionicons name={LEVEL_ICON[a.level]} size={26} color={color} />
          <View style={{ flex: 1 }}><Txt bold size={18} color={color}>{CARE[a.level].title}</Txt></View>
        </View>
        <Txt>{CARE[a.level].detail}</Txt>
        {a.level === "emergency" ? <Button label="Gọi cấp cứu 115" variant="danger" onPress={() => Linking.openURL("tel:115")} /> : null}
      </View>
      <Section title="Vì sao">
        {a.reasons.map((r) => <IconText key={r} icon="chevron-forward-circle-outline" color={color} text={r} />)}
      </Section>
      {a.matches.length ? (
        <Section title="Nguyên nhân thường gặp có thể liên quan" footer="Chỉ là gợi ý dựa trên triệu chứng. Chỉ bác sĩ mới chẩn đoán được.">
          {a.matches.map((m) => (
            <NavRow key={m.condition.id} icon="document-text-outline" color={LEVEL_COLOR[m.condition.minimumLevel]} title={m.condition.name}
              subtitle={`Trùng ${m.matched} triệu chứng · Khám: ${m.condition.specialty}`} onPress={() => router.push(`/condition/${m.condition.id}`)} />
          ))}
        </Section>
      ) : (
        <Section><Txt muted>Không có nguyên nhân thường gặp phù hợp với các triệu chứng đã chọn. Nếu thấy không ổn, hãy đi khám.</Txt></Section>
      )}
      {!a.showMedicationAdvice ? (
        <IconText icon="alert-circle-outline" color={COLORS.orange} text="Trẻ dưới 5 tuổi và phụ nữ mang thai: không tự dùng thuốc hoặc thảo dược, hãy hỏi bác sĩ." />
      ) : null}
      <Disclaimer />
    </ScrollView>
  );
}
