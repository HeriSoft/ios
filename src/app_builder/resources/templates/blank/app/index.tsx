import { useRouter } from "expo-router";
import React from "react";
import { View } from "react-native";
import { Body, Button, Card, Screen, Title } from "../src/components/ui";
import { brand } from "../src/brand";
import { t } from "../src/i18n";

export default function Home() {
  const router = useRouter();
  return (
    <Screen scroll>
      <View style={{ gap: 16 }}>
        <Card style={{ gap: 10 }}>
          <Title>{t("welcome")}</Title>
          <Body>{brand.appName}</Body>
          <Body muted>{brand.description || t("welcomeMessage")}</Body>
        </Card>
        <Button label={t("openSettings")} variant="secondary" onPress={() => router.push("/settings")} />
      </View>
    </Screen>
  );
}
