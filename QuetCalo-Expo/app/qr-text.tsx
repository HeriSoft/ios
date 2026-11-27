import React from "react";
import { Linking, ScrollView } from "react-native";
import { Section, Txt } from "../src/components/kit";
import { Button } from "../src/components/ui";
import { useStore } from "../src/state/store";

export default function QRTextScreen() {
  const { scannedText } = useStore();
  const isUrl = /^https?:\/\//i.test(scannedText.trim());
  return (
    <ScrollView contentContainerStyle={{ padding: 16, gap: 16, maxWidth: 760, width: "100%", alignSelf: "center" }}>
      <Section title="Nội dung mã" footer="Mã này không chứa mã vạch sản phẩm nên không tra được calo.">
        <Txt>{scannedText || "(trống)"}</Txt>
        {isUrl ? <Button label="Mở liên kết" variant="secondary" onPress={() => Linking.openURL(scannedText.trim())} /> : null}
      </Section>
    </ScrollView>
  );
}
