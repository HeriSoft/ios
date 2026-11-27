import { CameraView, useCameraPermissions } from "expo-camera";
import { router, useFocusEffect } from "expo-router";
import React, { useCallback, useRef, useState } from "react";
import { Platform, ScrollView, View } from "react-native";
import { Button, Input } from "../../src/components/ui";
import { Chip, COLORS, IconText, Section, Txt } from "../../src/components/kit";
import { classifyScan } from "../../src/core/basics";
import { useStore } from "../../src/state/store";
import { useTheme } from "../../src/theme";

const SAMPLES: [string, string][] = [["Nutella", "3017624010701"], ["Coca-Cola", "5449000000996"]];

export default function ScanScreen() {
  const { theme } = useTheme();
  const store = useStore();
  const [focused, setFocused] = useState(true);
  useFocusEffect(useCallback(() => { setFocused(true); return () => setFocused(false); }, []));
  const [permission, requestPermission] = useCameraPermissions();
  const [manual, setManual] = useState("");
  const busy = useRef(false);
  const canUseCamera = Platform.OS !== "web";

  function handle(raw: string) {
    if (busy.current) return;
    busy.current = true;
    setTimeout(() => (busy.current = false), 1500);
    const payload = classifyScan(raw);
    if (payload.kind === "barcode") router.push(`/lookup/${payload.code}`);
    else {
      store.setScannedText(payload.text);
      router.push("/qr-text");
    }
  }

  return (
    <ScrollView contentContainerStyle={{ padding: 16, gap: 16, maxWidth: 760, width: "100%", alignSelf: "center" }}>
      <View style={{ height: 300, borderRadius: 20, overflow: "hidden", backgroundColor: theme.colors.surfaceAlt, alignItems: "center", justifyContent: "center" }}>
        {canUseCamera && permission?.granted && focused ? (
          <CameraView
            style={{ width: "100%", height: "100%" }}
            facing="back"
            barcodeScannerSettings={{ barcodeTypes: ["ean13", "ean8", "upc_a", "upc_e", "code128", "itf14", "qr"] }}
            onBarcodeScanned={({ data }) => data && handle(data)}
          />
        ) : canUseCamera ? (
          <View style={{ alignItems: "center", gap: 10, padding: 16 }}>
            <Txt>App cần quyền camera để quét mã vạch</Txt>
            <Button label="Cho phép camera" onPress={requestPermission} />
          </View>
        ) : (
          <View style={{ alignItems: "center", gap: 8, padding: 16 }}>
            <Txt bold>Camera không khả dụng trên bản web</Txt>
            <Txt muted>Nhập mã vạch bên dưới hoặc thử mã mẫu.</Txt>
          </View>
        )}
      </View>
      <Txt muted>Đưa mã vạch hoặc mã QR trên bao bì vào khung hình để xem lượng calo.</Txt>
      <Button label="Quét nhãn dinh dưỡng" onPress={() => router.push("/label")} />
      <Section title="Nhập mã vạch thủ công">
        <Input placeholder="Dãy số dưới mã vạch, ví dụ 3017624010701" keyboardType="number-pad" value={manual}
          onChangeText={(v) => setManual(v.replace(/[^0-9]/g, ""))} onSubmitEditing={() => manual && handle(manual)} />
        <Button label="Tra cứu" variant="secondary" disabled={!manual} onPress={() => handle(manual)} />
      </Section>
      <View style={{ flexDirection: "row", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <Txt muted size={13}>Thử mã mẫu:</Txt>
        {SAMPLES.map(([name, code]) => <Chip key={code} label={name} onPress={() => handle(code)} />)}
      </View>
      <IconText icon="information-circle-outline" color={COLORS.blue}
        text="Dữ liệu sản phẩm lấy từ Open Food Facts (miễn phí, cộng đồng đóng góp) nên cần kết nối mạng." />
    </ScrollView>
  );
}
