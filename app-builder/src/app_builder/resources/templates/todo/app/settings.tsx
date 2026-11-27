import Constants from "expo-constants";
import React from "react";
import { View } from "react-native";
import { ThemePicker } from "../src/components/ThemePicker";
import { Body, Button, Card, confirm, Screen, Title } from "../src/components/ui";
import { brand } from "../src/brand";
import { t } from "../src/i18n";
import { useTodos } from "../src/state/TodoContext";

export default function Settings() {
  const { todos, clearDone } = useTodos();
  const done = todos.filter((x) => x.done).length;

  const onClear = async () => {
    if (await confirm(t("confirmClearTitle"), t("confirmDeleteMessage"))) {
      await clearDone().catch(() => undefined);
    }
  };

  return (
    <Screen scroll>
      <View style={{ gap: 16 }}>
        <Card style={{ gap: 12 }}>
          <Title>{t("appearance")}</Title>
          <ThemePicker />
        </Card>
        <Card style={{ gap: 12 }}>
          <Title>{t("statsTitle")}</Title>
          <Body>{t("stats", { done, total: todos.length })}</Body>
          <Button label={t("clearDone", { count: done })} variant="secondary" onPress={onClear} disabled={done === 0} />
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
