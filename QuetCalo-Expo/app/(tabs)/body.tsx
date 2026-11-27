import { router } from "expo-router";
import React from "react";
import { ScrollView, View } from "react-native";
import { Chip, COLORS, Disclaimer, IconText, NavRow, NumberField, Row, Section, Segmented, Txt } from "../../src/components/kit";
import { kcalText, shortText } from "../../src/core/basics";
import { kcalPerPortion } from "../../src/core/foods";
import { ACTIVITY, ActivityLevel, BMI_TITLE, bodyReport, GOAL_TITLE, isValidProfile, nutritionAdvice, Sex, WeightGoal } from "../../src/core/health";
import { useStore } from "../../src/state/store";
import { useTheme } from "../../src/theme";

const BMI_COLORS = { underweight: COLORS.blue, normal: COLORS.green, overweight: COLORS.yellow, obese1: COLORS.orange, obese2: COLORS.red };

function BMIScale({ bmi }: { bmi: number }) {
  const { theme } = useTheme();
  const min = 15, max = 35;
  const pos = Math.min(1, Math.max(0, (bmi - min) / (max - min)));
  const segs: [number, string][] = [[18.5, COLORS.blue], [23, COLORS.green], [25, COLORS.yellow], [30, COLORS.orange], [35, COLORS.red]];
  let prev = min;
  return (
    <View style={{ gap: 4 }}>
      <View style={{ height: 12, flexDirection: "row", borderRadius: 6, overflow: "hidden" }}>
        {segs.map(([end, c]) => { const w = (end - prev) / (max - min); prev = end; return <View key={end} style={{ flex: w, backgroundColor: c }} />; })}
      </View>
      <View style={{ height: 14 }}>
        <View style={{ position: "absolute", left: `${pos * 100}%`, marginLeft: -6, width: 0, height: 0, borderLeftWidth: 6, borderRightWidth: 6, borderBottomWidth: 10,
          borderLeftColor: "transparent", borderRightColor: "transparent", borderBottomColor: theme.colors.text }} />
      </View>
      <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
        {["15", "18,5", "23", "25", "30", "35"].map((x) => <Txt key={x} muted size={11}>{x}</Txt>)}
      </View>
    </View>
  );
}

export default function BodyScreen() {
  const store = useStore();
  const p = store.profile;
  const set = (patch: Partial<typeof p>) => store.setProfile({ ...p, ...patch });
  const report = isValidProfile(p) ? bodyReport(p) : undefined;
  const advice = report ? nutritionAdvice(p, report) : undefined;

  return (
    <ScrollView contentContainerStyle={{ padding: 16, gap: 16, maxWidth: 760, width: "100%", alignSelf: "center" }} keyboardShouldPersistTaps="handled">
      <Section>
        <NavRow icon="medkit-outline" title="Kiểm tra triệu chứng" subtitle="Đánh giá mức độ và gợi ý chăm sóc" color={COLORS.red} onPress={() => router.push("/symptoms")} />
      </Section>
      <Section title="Thông tin của bạn">
        <Segmented<Sex> options={[["male", "Nam"], ["female", "Nữ"]]} value={p.sex} onChange={(sex) => set({ sex })} />
        <View style={{ flexDirection: "row", gap: 10 }}>
          <NumberField label="Tuổi" value={p.age} onChange={(v) => set({ age: v ?? 0 })} />
          <NumberField label="Chiều cao" value={p.heightCm} onChange={(v) => set({ heightCm: v ?? 0 })} suffix="cm" />
          <NumberField label="Cân nặng" value={p.weightKg} onChange={(v) => set({ weightKg: v ?? 0 })} suffix="kg" />
        </View>
        <NumberField label="Vòng eo (không bắt buộc)" value={p.waistCm} onChange={(v) => set({ waistCm: v })} suffix="cm" />
        <Txt muted size={13}>Mức vận động</Txt>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8 }}>
          {(Object.keys(ACTIVITY) as ActivityLevel[]).map((a) => <Chip key={a} label={ACTIVITY[a].title} selected={p.activity === a} onPress={() => set({ activity: a })} />)}
        </View>
        <Segmented<WeightGoal> options={(Object.keys(GOAL_TITLE) as WeightGoal[]).map((g) => [g, GOAL_TITLE[g]])} value={p.goal} onChange={(goal) => set({ goal })} />
      </Section>
      {!report ? <Section><Txt muted>Nhập tuổi 10–100, chiều cao 100–250 cm và cân nặng 20–300 kg để xem kết quả.</Txt></Section> : (
        <>
          <Section title="Chỉ số cơ thể" footer="Ngưỡng BMI cho người châu Á trưởng thành.">
            <View style={{ flexDirection: "row", alignItems: "baseline", gap: 10 }}>
              <Txt bold size={34} color={BMI_COLORS[report.category]}>{shortText(report.bmi)}</Txt>
              <Txt bold color={BMI_COLORS[report.category]}>{BMI_TITLE[report.category]}</Txt>
            </View>
            <BMIScale bmi={report.bmi} />
            <Row label="Cân nặng hợp lý" value={`${shortText(report.healthyMin)}–${shortText(report.healthyMax)} kg`} />
            {report.weightChange !== 0 ? <Row label={report.weightChange > 0 ? "Cần tăng khoảng" : "Cần giảm khoảng"} value={`${shortText(Math.abs(report.weightChange))} kg`} /> : null}
            {report.bodyFatPercent != null ? <Row label="Mỡ cơ thể ước tính" value={`${shortText(report.bodyFatPercent)}%`} /> : null}
            {report.waistToHeight != null ? <Row label="Tỉ lệ eo/chiều cao" value={shortText(report.waistToHeight)} color={report.waistToHeight >= 0.5 ? COLORS.orange : undefined} /> : null}
          </Section>
          <Section title="Năng lượng mỗi ngày" footer="BMR theo công thức Mifflin-St Jeor.">
            <Row label="Trao đổi chất cơ bản (BMR)" value={kcalText(report.bmr)} />
            <Row label="Tiêu hao cả ngày (TDEE)" value={kcalText(report.tdee)} />
            <Row label={`Nên ăn để ${GOAL_TITLE[p.goal].toLowerCase()}`} value={kcalText(report.targetKcal)} color={COLORS.orange} bold />
            <Row label="Đạm / Béo / Tinh bột" value={`${Math.round(report.proteinGrams)} / ${Math.round(report.fatGrams)} / ${Math.round(report.carbGrams)} g`} />
            <Row label="Nước" value={`${shortText(report.waterLiters)} lít`} />
            {store.dailyGoal !== Math.round(report.targetKcal) ? (
              <Chip label={`Đặt ${kcalText(report.targetKcal)} làm mục tiêu nhật ký`} onPress={() => store.setDailyGoal(Math.round(report.targetKcal))} />
            ) : <IconText icon="checkmark-circle" color={COLORS.green} text="Đã dùng làm mục tiêu nhật ký" />}
          </Section>
          {advice ? (
            <>
              <Section title="Nên ăn thêm">
                {advice.eatMore.map((s) => <Row key={s.food.id} label={`${s.food.name} — ${s.reason}`} value={kcalText(kcalPerPortion(s.food))} color={COLORS.green} />)}
              </Section>
              <Section title="Nên hạn chế">
                {advice.limit.map((s) => <Row key={s.food.id} label={`${s.food.name} — ${s.reason}`} value={kcalText(kcalPerPortion(s.food))} color={COLORS.red} />)}
              </Section>
              <Section title="Lời khuyên">
                {advice.tips.map((t) => <IconText key={t} icon="leaf-outline" color={COLORS.green} text={t} />)}
              </Section>
            </>
          ) : null}
          <Disclaimer />
        </>
      )}
    </ScrollView>
  );
}
