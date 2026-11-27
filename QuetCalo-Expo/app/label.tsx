import * as ImagePicker from "expo-image-picker";
import { router, useLocalSearchParams } from "expo-router";
import React, { useState } from "react";
import { Image, Platform, ScrollView, View } from "react-native";
import { COLORS, IconText, NumberField, Section, Segmented, Txt } from "../src/components/kit";
import { Button, Input } from "../src/components/ui";
import { kcalText, ProductInfo } from "../src/core/basics";
import { LabelBasis, parseLabel } from "../src/core/labelParser";
import { mlAvailable, recognizeTextLines } from "../src/ml";
import { useStore } from "../src/state/store";
import { useTheme } from "../src/theme";

export default function LabelScreen() {
  const { code } = useLocalSearchParams<{ code?: string }>();
  const store = useStore();
  const { theme } = useTheme();
  const [photo, setPhoto] = useState<string>();
  const [status, setStatus] = useState<string>();
  const [found, setFound] = useState<number[]>([]);
  const [name, setName] = useState("");
  const [kcal, setKcal] = useState<number>();
  const [basis, setBasis] = useState<LabelBasis>("per100g");
  const [serving, setServing] = useState<number>();
  const canOCR = mlAvailable("text");

  async function scan(fromCamera: boolean) {
    const opts: ImagePicker.ImagePickerOptions = { mediaTypes: ["images"], quality: 0.9 };
    const res = fromCamera ? await ImagePicker.launchCameraAsync(opts) : await ImagePicker.launchImageLibraryAsync(opts);
    if (res.canceled || !res.assets[0]) return;
    setPhoto(res.assets[0].uri); setStatus("Đang đọc nhãn…");
    try {
      const r = parseLabel(await recognizeTextLines(res.assets[0].uri));
      setFound(r.allKcalValues);
      if (r.kcal != null) {
        setKcal(r.kcal); setBasis(r.basis); if (r.servingGrams) setServing(r.servingGrams);
        setStatus(`Đã đọc được ${kcalText(r.kcal)} ${r.basis === "per100g" ? "/ 100 g" : "/ khẩu phần"}. Kiểm tra lại trước khi dùng.`);
      } else setStatus("Không tìm thấy số kcal trên ảnh. Hãy chụp gần, rõ bảng dinh dưỡng hoặc nhập tay.");
    } catch (e) {
      setStatus("Không đọc được ảnh: " + (e as Error).message);
    }
  }

  function next() {
    if (kcal == null) return;
    const p: ProductInfo = {
      barcode: code, name: name.trim() || "Sản phẩm từ nhãn", source: "label",
      kcalPer100g: basis === "per100g" ? kcal : undefined,
      kcalPerServing: basis === "perServing" ? kcal : undefined,
      servingGrams: serving, servingSizeText: serving ? `${serving} g` : undefined,
    };
    store.selectProduct(p, basis === "perServing");
    router.replace("/product");
  }

  return (
    <ScrollView contentContainerStyle={{ padding: 16, gap: 16, maxWidth: 760, width: "100%", alignSelf: "center" }} keyboardShouldPersistTaps="handled">
      <Section title="Chụp bảng thành phần dinh dưỡng">
        {canOCR ? (
          <>
            {photo ? <Image source={{ uri: photo }} style={{ height: 200, borderRadius: 12, backgroundColor: theme.colors.surfaceAlt }} resizeMode="contain" /> : null}
            <View style={{ flexDirection: "row", gap: 10 }}>
              {Platform.OS !== "web" ? <View style={{ flex: 1 }}><Button label="Chụp nhãn" onPress={() => scan(true)} /></View> : null}
              <View style={{ flex: 1 }}><Button label="Chọn ảnh" variant="secondary" onPress={() => scan(false)} /></View>
            </View>
            {status ? <Txt muted>{status}</Txt> : null}
            {found.length > 1 ? <Txt muted size={12}>Các số kcal thấy trên nhãn: {found.join(", ")}</Txt> : null}
          </>
        ) : (
          <IconText icon="information-circle-outline" color={COLORS.blue}
            text="Đọc chữ trên nhãn (OCR) cần bản cài đặt native. Trên web và Expo Go, hãy nhập số kcal trên bao bì bên dưới." />
        )}
      </Section>
      <Section title="Thông tin trên nhãn">
        <Input label="Tên sản phẩm" placeholder="Ví dụ: Bánh quy bơ" value={name} onChangeText={setName} />
        <Segmented<LabelBasis> options={[["per100g", "Trên 100 g/ml"], ["perServing", "Trên khẩu phần"]]} value={basis} onChange={setBasis} />
        <NumberField label="Năng lượng" value={kcal} onChange={setKcal} suffix="kcal" />
        <NumberField label="Khối lượng 1 khẩu phần (nếu có)" value={serving} onChange={setServing} suffix="g" />
        <Txt muted size={12}>Nếu nhãn chỉ ghi kJ, chia cho 4,184 để ra kcal.</Txt>
        <Button label="Tiếp tục" disabled={kcal == null} onPress={next} />
      </Section>
    </ScrollView>
  );
}
