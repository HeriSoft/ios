import { router } from "expo-router";
import React from "react";
import { ScrollView, View } from "react-native";
import { Chip, COLORS, Disclaimer, Section, Segmented, Txt } from "../src/components/kit";
import { Button } from "../src/components/ui";
import { DURATIONS, GROUPS, RED_FLAGS, Severity, SEVERITIES, SYMPTOMS } from "../src/core/symptoms";
import { useStore } from "../src/state/store";

function toggle<T>(list: T[], x: T): T[] {
  return list.includes(x) ? list.filter((y) => y !== x) : [...list, x];
}

export default function SymptomsScreen() {
  const { symptomInput: input, setSymptomInput: set } = useStore();
  const empty = input.symptoms.length === 0 && input.redFlags.length === 0;
  return (
    <ScrollView contentContainerStyle={{ padding: 16, gap: 16, maxWidth: 760, width: "100%", alignSelf: "center" }}>
      <Section title="Triệu chứng bạn đang có">
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8 }}>
          {SYMPTOMS.map(([s, title]) => <Chip key={s} label={title} selected={input.symptoms.includes(s)} onPress={() => set({ ...input, symptoms: toggle(input.symptoms, s) })} />)}
        </View>
      </Section>
      <Section title="Dấu hiệu nguy hiểm" footer="Chọn nếu có bất kỳ dấu hiệu nào. Khi đó cần đi cấp cứu ngay.">
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8 }}>
          {RED_FLAGS.map(([f, title]) => <Chip key={f} label={title} selected={input.redFlags.includes(f)} onPress={() => set({ ...input, redFlags: toggle(input.redFlags, f) })} />)}
        </View>
      </Section>
      <Section title="Thông tin thêm">
        <Txt muted size={13}>Người bệnh</Txt>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8 }}>
          {GROUPS.map(([g, title]) => <Chip key={g} label={title} selected={input.group === g} onPress={() => set({ ...input, group: g })} />)}
        </View>
        <Txt muted size={13}>Đã bị bao lâu</Txt>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8 }}>
          {DURATIONS.map(([d, title]) => <Chip key={d} label={title} selected={input.duration === d} onPress={() => set({ ...input, duration: d })} />)}
        </View>
        <Txt muted size={13}>Mức độ</Txt>
        <Segmented<Severity> options={SEVERITIES} value={input.severity} onChange={(severity) => set({ ...input, severity })} />
      </Section>
      <Button label="Xem đánh giá" disabled={empty} onPress={() => router.push("/symptom-result")} />
      {input.redFlags.length ? <Txt size={13} color={COLORS.red}>Bạn đã chọn dấu hiệu nguy hiểm: hãy gọi 115 hoặc đến cơ sở y tế gần nhất.</Txt>
        : empty ? <Txt muted size={12}>Chọn ít nhất một triệu chứng để xem đánh giá.</Txt> : null}
      <Disclaimer />
    </ScrollView>
  );
}
