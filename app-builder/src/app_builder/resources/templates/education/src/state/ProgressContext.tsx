import AsyncStorage from "@react-native-async-storage/async-storage";
import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { t } from "../i18n";

type Progress = { learned: string[]; activities: Record<string, string[]> };
const KEY = "edu.progress.v1";
const EMPTY: Progress = { learned: [], activities: {} };

export function todayKey(d = new Date()): string {
  const m = `${d.getMonth() + 1}`.padStart(2, "0");
  const day = `${d.getDate()}`.padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}

type Value = {
  progress: Progress;
  loading: boolean;
  error: string | null;
  reload: () => void;
  toggleLearned: (lessonId: string) => void;
  toggleActivity: (activityId: string, date?: string) => void;
  reset: () => void;
};

const Ctx = createContext<Value | null>(null);

export function ProgressProvider({ children }: { children: React.ReactNode }) {
  const [progress, setProgress] = useState<Progress>(EMPTY);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(() => {
    setLoading(true);
    setError(null);
    AsyncStorage.getItem(KEY)
      .then((raw) => {
        if (!raw) return setProgress(EMPTY);
        const p = JSON.parse(raw) as Partial<Progress>;
        setProgress({ learned: Array.isArray(p.learned) ? p.learned : [], activities: p.activities ?? {} });
      })
      .catch(() => setError(t("loadFailed")))
      .finally(() => setLoading(false));
  }, []);

  useEffect(reload, [reload]);

  const persist = (next: Progress) => {
    setProgress(next);
    AsyncStorage.setItem(KEY, JSON.stringify(next)).catch(() => setError(t("loadFailed")));
  };

  const value = useMemo<Value>(
    () => ({
      progress,
      loading,
      error,
      reload,
      toggleLearned: (id) => {
        const has = progress.learned.includes(id);
        persist({ ...progress, learned: has ? progress.learned.filter((x) => x !== id) : [...progress.learned, id] });
      },
      toggleActivity: (id, date = todayKey()) => {
        const list = progress.activities[date] ?? [];
        const next = list.includes(id) ? list.filter((x) => x !== id) : [...list, id];
        persist({ ...progress, activities: { ...progress.activities, [date]: next } });
      },
      reset: () => persist(EMPTY),
    }),
    [progress, loading, error, reload],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useProgress(): Value {
  const v = useContext(Ctx);
  if (!v) throw new Error("useProgress phải nằm trong ProgressProvider");
  return v;
}
