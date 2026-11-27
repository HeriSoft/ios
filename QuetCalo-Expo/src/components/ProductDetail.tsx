import { Ionicons } from "@expo/vector-icons";
import { router, Stack } from "expo-router";
import React, { useState } from "react";
import { Alert, Image, Platform, ScrollView, View } from "react-native";
import { Calorie, effectiveKcalPerServing, kcalText, ProductInfo, shortText } from "../core/basics";
import { useStore } from "../state/store";
import { useTheme } from "../theme";
import { COLORS, NumberField, Row, Section, Segmented, SmallButton, Txt } from "./kit";
import { Button } from "./ui";

type Mode = "grams" | "servings";

export function ProductDetail({ product, preferServings = false }: { product: ProductInfo; preferServings?: boolean }) {
  const { theme } = useTheme();
  const store = useStore();
  const serving = effectiveKcalPerServing(product);
  const useServings = (preferServings || product.kcalPer100g == null) && serving != null;
  const [mode, setMode] = useState<Mode>(useServings ? "servings" : "grams");
  const [amount, setAmount] = useState<number | undefined>(useServings ? 1 : product.servingGrams ?? 100);
  const [manual100, setManual100] = useState<number>();

  const kcal100 = product.kcalPer100g ?? manual100;
  const kcalServing = serving ?? (kcal100 != null && product.servingGrams ? Calorie.per100g(kcal100, product.servingGrams) : undefined);
  const total = amount == null ? undefined
    : mode === "grams" ? (kcal100 != null ? Calorie.per100g(kcal100, amount) : undefined)
    : kcalServing != null ? Calorie.perServing(kcalServing, amount) : undefined;
  const step = mode === "grams" ? 10 : 0.5;

  function save() {
    if (total == null) return;
    store.addFood({ name: product.name, amount: amount ?? 0, unit: mode === "grams" ? "g" : "phần", kcal: total });
    const done = () => (router.canDismiss() ? router.dismissAll() : router.replace("/"));
    if (Platform.OS === "web") done();
    else Alert.alert("Đã thêm vào nhật ký", `${product.name}: ${kcalText(total)}`, [{ text: "OK", onPress: done }]);
  }

  return (
    <ScrollView contentContainerStyle={{ padding: 16, gap: 16, maxWidth: 760, width: "100%", alignSelf: "center" }}>
      <Stack.Screen options={{ title: product.name }} />
      <Section>
        <View style={{ flexDirection: "row", gap: 14, alignItems: "center" }}>
          <View style={{ width: 72, height: 72, borderRadius: 12, backgroundColor: theme.colors.surfaceAlt, alignItems: "center", justifyContent: "center", overflow: "hidden" }}>
            {product.imageUrl ? <Image source={{ uri: product.imageUrl }} style={{ width: 72, height: 72 }} resizeMode="contain" />
              : <Ionicons name={product.source === "estimate" ? "restaurant" : "cube"} size={30} color={theme.colors.textMuted} />}
          </View>
          <View style={{ flex: 1, gap: 2 }}>
            <Txt bold size={17}>{product.name}</Txt>
            {product.brand ? <Txt muted>{product.brand}</Txt> : null}
            <Txt muted size={12}>{[product.barcode, product.quantityText].filter(Boolean).join(" · ")}</Txt>
          </View>
        </View>
      </Section>
      <Section title="Giá trị dinh dưỡng">
        {product.kcalPer100g != null ? <Row label="Năng lượng / 100 g" value={kcalText(product.kcalPer100g)} />
          : <NumberField label="Năng lượng / 100 g (nhập từ bao bì)" value={manual100} onChange={setManual100} suffix="kcal" />}
        {kcalServing != null ? <Row label={"Mỗi khẩu phần" + (product.servingSizeText ? ` · ${product.servingSizeText}` : "")} value={kcalText(kcalServing)} /> : null}
        {product.protein100g != null ? <Row label="Chất đạm" value={`${shortText(product.protein100g)} g`} /> : null}
        {product.carbs100g != null ? <Row label="Carbohydrate" value={`${shortText(product.carbs100g)} g`} /> : null}
        {product.sugars100g != null ? <Row label="   trong đó đường" value={`${shortText(product.sugars100g)} g`} /> : null}
        {product.fat100g != null ? <Row label="Chất béo" value={`${shortText(product.fat100g)} g`} /> : null}
      </Section>
      <Section title="Bạn ăn bao nhiêu?">
        {kcalServing != null ? (
          <Segmented<Mode> options={[["grams", "Gram / ml"], ["servings", "Khẩu phần"]]} value={mode}
            onChange={(m) => { setMode(m); setAmount(m === "grams" ? product.servingGrams ?? 100 : 1); }} />
        ) : null}
        <View style={{ flexDirection: "row", alignItems: "flex-end", gap: 8 }}>
          <SmallButton label="−" onPress={() => setAmount(Math.max(0, (amount ?? 0) - step))} />
          <NumberField label="Số lượng" value={amount} onChange={setAmount} suffix={mode === "grams" ? "g / ml" : "phần"} />
          <SmallButton label="+" onPress={() => setAmount((amount ?? 0) + step)} />
        </View>
      </Section>
      <Section footer={product.source === "openFoodFacts" ? "Dữ liệu từ Open Food Facts (cộng đồng đóng góp). Giá trị có thể chưa chính xác tuyệt đối."
        : product.source === "estimate" ? "Giá trị ước tính trung bình. Lượng calo thực tế phụ thuộc cách chế biến và khẩu phần." : undefined}>
        <View style={{ flexDirection: "row", alignItems: "center" }}>
          <Txt bold size={17}>Tổng calo</Txt>
          <View style={{ flex: 1 }} />
          <Txt bold size={28} color={COLORS.orange}>{total != null ? kcalText(total) : "—"}</Txt>
        </View>
        <Button label="Thêm vào nhật ký" disabled={total == null} onPress={save} />
      </Section>
    </ScrollView>
  );
}
