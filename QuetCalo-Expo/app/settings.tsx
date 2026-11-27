import Constants from "expo-constants";
import React from "react";
import { View } from "react-native";
import { ThemePicker } from "../src/components/ThemePicker";
import { Body, Card, Screen, Title } from "../src/components/ui";
import { brand } from "../src/brand";
import { t } from "../src/i18n";

export default function Settings() {
  return (
    <Screen scroll>
      <View style={{ gap: 16 }}>
        <Card style={{ gap: 12 }}>
          <Title>{t("appearance")}</Title>
          <ThemePicker />
        </Card>
        <Card style={{ gap: 6 }}>
          <Title>{t("about")}</Title>
          <Body>{brand.appName}</Body>
          <Body muted>{t("version", { version: Constants.expoConfig?.version ?? "1.0.0" })}</Body>
        </Card>
      </View>
    </Screen>
  );
}
