import Constants from "expo-constants";
import React from "react";
import { View } from "react-native";
import { ThemePicker } from "../src/components/ThemePicker";
import { Body, Button, Card, confirm, Screen, Title } from "../src/components/ui";
import { brand } from "../src/brand";
import { t } from "../src/i18n";
import { useProgress } from "../src/state/ProgressContext";

export default function Settings() {
  const { reset } = useProgress();
  return (
    <Screen scroll>
      <View style={{ gap: 16 }}>
        <Card style={{ gap: 12 }}>
          <Title>{t("appearance")}</Title>
          <ThemePicker />
        </Card>
        <Card style={{ gap: 12 }}>
          <Body muted>{t("privacyNote")}</Body>
          <Button
            label={t("resetProgress")}
            variant="danger"
            onPress={async () => {
              if (await confirm(t("confirmReset"), t("confirmResetMessage"))) reset();
            }}
          />
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
