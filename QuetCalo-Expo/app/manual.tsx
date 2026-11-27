import { router, useLocalSearchParams } from "expo-router";
import React, { useState } from "react";
import { ScrollView } from "react-native";
import { NumberField, Section, Segmented } from "../src/components/kit";
import { Button, Input } from "../src/components/ui";
import { LabelBasis } from "../src/core/labelParser";
import { useStore } from "../src/state/store";

export default function ManualScreen() {
  const { code } = useLocalSearchParams<{ code?: string }>();
  const store = useStore();
  const [name, setName] = useState("");
  const [basis, setBasis] = useState<LabelBasis>("perServing");
  const [kcal, setKcal] = useState<number>();
  const [grams, setGrams] = useState<number>();
  const ok = name.trim() !== "" && kcal != null;

  function next() {
    if (!ok) return;
    store.selectProduct({
      barcode: code, name: name.trim(), source: "manual",
      kcalPer100g: basis === "per100g" ? kcal : undefined,
      kcalPerServing: basis === "perServing" ? kcal : undefined,
      servingGrams: grams, servingSizeText: grams ? `${grams} g` : undefined,
    }, basis === "perServing");
    router.replace("/product");
  }

  return (
    <ScrollView contentContainerStyle={{ padding: 16, gap: 16, maxWidth: 760, width: "100%", alignSelf: "center" }} keyboardShouldPersistTaps="handled">
      <Section title="Món ăn / sản phẩm" footer="Dùng khi không có mã vạch hoặc món không có trong danh sách.">
        <Input label="Tên" placeholder="Ví dụ: Bánh bao nhân thịt" value={name} onChangeText={setName} />
        <Segmented<LabelBasis> options={[["perServing", "Calo cho 1 phần"], ["per100g", "Calo trên 100 g"]]} value={basis} onChange={setBasis} />
        <NumberField label="Năng lượng" value={kcal} onChange={setKcal} suffix="kcal" />
        <NumberField label="Khối lượng 1 phần (không bắt buộc)" value={grams} onChange={setGrams} suffix="g" />
        <Button label="Tiếp tục" disabled={!ok} onPress={next} />
      </Section>
    </ScrollView>
  );
}
