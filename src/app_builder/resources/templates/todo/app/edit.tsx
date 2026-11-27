import { Stack, useLocalSearchParams, useRouter } from "expo-router";
import React, { useEffect, useState } from "react";
import { Text, View } from "react-native";
import { Button, confirm, EmptyState, Input, LoadingState, Screen } from "../src/components/ui";
import { t } from "../src/i18n";
import { useTodos } from "../src/state/TodoContext";
import { useTheme } from "../src/theme";

export default function EditTodo() {
  const { theme } = useTheme();
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const id = typeof params.id === "string" ? params.id : undefined;
  const { todos, loading, add, update, remove } = useTodos();
  const existing = id ? todos.find((x) => x.id === id) : undefined;

  const [title, setTitle] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (existing) {
      setTitle(existing.title);
      setNote(existing.note);
    }
  }, [existing?.id]);

  if (loading) return <Screen><LoadingState /></Screen>;
  if (id && !existing) return <Screen><EmptyState icon="🔍" title={t("notFoundTodo")} action={<Button label={t("goHome")} onPress={() => router.back()} />} /></Screen>;

  const onSave = async () => {
    if (!title.trim()) {
      setError(t("titleRequired"));
      return;
    }
    setBusy(true);
    try {
      if (existing) await update(existing.id, { title: title.trim(), note: note.trim() });
      else await add(title, note);
      router.back();
    } catch (e) {
      setError(e instanceof Error ? e.message : t("saveFailed"));
    } finally {
      setBusy(false);
    }
  };

  const onDelete = async () => {
    if (!existing) return;
    if (!(await confirm(t("confirmDeleteTitle"), t("confirmDeleteMessage")))) return;
    setBusy(true);
    try {
      await remove(existing.id);
      router.back();
    } catch (e) {
      setError(e instanceof Error ? e.message : t("saveFailed"));
      setBusy(false);
    }
  };

  return (
    <Screen scroll>
      <Stack.Screen options={{ title: existing ? t("todoEdit") : t("todoNew") }} />
      <View style={{ gap: 16 }}>
        <Input
          label={t("fieldTitle")}
          placeholder={t("fieldTitlePlaceholder")}
          value={title}
          onChangeText={(v) => {
            setTitle(v);
            setError(null);
          }}
          autoFocus={!existing}
          maxLength={120}
          returnKeyType="done"
          onSubmitEditing={onSave}
        />
        <Input
          label={t("fieldNote")}
          placeholder={t("fieldNotePlaceholder")}
          value={note}
          onChangeText={setNote}
          multiline
          style={{ minHeight: 100, textAlignVertical: "top" }}
          maxLength={1000}
        />
        {error ? <Text style={{ color: theme.colors.danger }} accessibilityRole="alert">{error}</Text> : null}
        <Button label={t("save")} onPress={onSave} disabled={busy} />
        {existing ? <Button label={t("delete")} variant="danger" onPress={onDelete} disabled={busy} /> : null}
      </View>
    </Screen>
  );
}
