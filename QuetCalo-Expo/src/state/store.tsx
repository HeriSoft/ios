/** Trạng thái dùng chung + lưu trên máy bằng AsyncStorage (nhật ký, hồ sơ cơ thể, mục tiêu). */
import AsyncStorage from "@react-native-async-storage/async-storage";
import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { ProductInfo } from "../core/basics";
import { BodyProfile } from "../core/health";
import { emptySymptomInput, SymptomInput } from "../core/symptoms";

export interface FoodLogEntry { id: string; time: number; name: string; amount: number; unit: string; kcal: number }
export interface WorkoutLogEntry { id: string; time: number; name: string; exerciseId: string; minutes: number; kcal: number }

interface Persisted {
  foods: FoodLogEntry[];
  workouts: WorkoutLogEntry[];
  profile: BodyProfile;
  dailyGoal: number;
}

const KEY = "quetcalo.v1";
const DEFAULTS: Persisted = {
  foods: [],
  workouts: [],
  profile: { sex: "female", age: 28, heightCm: 158, weightKg: 62, activity: "light", goal: "lose" },
  dailyGoal: 2000,
};

interface Store extends Persisted {
  ready: boolean;
  addFood: (e: Omit<FoodLogEntry, "id" | "time">) => void;
  removeFood: (id: string) => void;
  addWorkout: (e: Omit<WorkoutLogEntry, "id" | "time">) => void;
  removeWorkout: (id: string) => void;
  setProfile: (p: BodyProfile) => void;
  setDailyGoal: (kcal: number) => void;
  // Dữ liệu tạm khi chuyển màn hình (không lưu)
  product?: ProductInfo;
  preferServings: boolean;
  selectProduct: (p: ProductInfo, servings?: boolean) => void;
  scannedText: string;
  setScannedText: (t: string) => void;
  symptomInput: SymptomInput;
  setSymptomInput: (i: SymptomInput) => void;
}

const Ctx = createContext<Store | null>(null);
const newId = () => `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;

export function StoreProvider({ children }: { children: React.ReactNode }) {
  const [data, setData] = useState<Persisted>(DEFAULTS);
  const [ready, setReady] = useState(false);
  const [product, setProduct] = useState<ProductInfo>();
  const [preferServings, setPreferServings] = useState(false);
  const [scannedText, setScannedText] = useState("");
  const [symptomInput, setSymptomInput] = useState<SymptomInput>(emptySymptomInput());

  useEffect(() => {
    AsyncStorage.getItem(KEY)
      .then((raw) => {
        if (raw) {
          const saved = JSON.parse(raw) as Partial<Persisted>;
          setData({ ...DEFAULTS, ...saved, profile: { ...DEFAULTS.profile, ...saved.profile } });
        }
      })
      .catch(() => undefined)
      .finally(() => setReady(true));
  }, []);

  const update = useCallback((fn: (d: Persisted) => Persisted) => {
    setData((prev) => {
      const next = fn(prev);
      AsyncStorage.setItem(KEY, JSON.stringify(next)).catch(() => undefined);
      return next;
    });
  }, []);

  const value = useMemo<Store>(
    () => ({
      ...data,
      ready,
      addFood: (e) => update((d) => ({ ...d, foods: [{ ...e, id: newId(), time: Date.now() }, ...d.foods] })),
      removeFood: (id) => update((d) => ({ ...d, foods: d.foods.filter((f) => f.id !== id) })),
      addWorkout: (e) => update((d) => ({ ...d, workouts: [{ ...e, id: newId(), time: Date.now() }, ...d.workouts] })),
      removeWorkout: (id) => update((d) => ({ ...d, workouts: d.workouts.filter((w) => w.id !== id) })),
      setProfile: (profile) => update((d) => ({ ...d, profile })),
      setDailyGoal: (kcal) => update((d) => ({ ...d, dailyGoal: Math.min(5000, Math.max(1000, Math.round(kcal))) })),
      product,
      preferServings,
      selectProduct: (p, servings = false) => {
        setProduct(p);
        setPreferServings(servings);
      },
      scannedText,
      setScannedText,
      symptomInput,
      setSymptomInput,
    }),
    [data, ready, update, product, preferServings, scannedText, symptomInput],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useStore(): Store {
  const s = useContext(Ctx);
  if (!s) throw new Error("useStore phải nằm trong StoreProvider");
  return s;
}

const dayKey = (t: number) => new Date(t).toDateString();
export const isToday = (t: number) => dayKey(t) === new Date().toDateString();
export const timeText = (t: number) => {
  const d = new Date(t);
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
};
export function dayTitle(t: number): string {
  const d = new Date(t);
  const today = new Date();
  const yesterday = new Date(today.getTime() - 86_400_000);
  if (d.toDateString() === today.toDateString()) return "Hôm nay";
  if (d.toDateString() === yesterday.toDateString()) return "Hôm qua";
  return `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}/${d.getFullYear()}`;
}
export { dayKey };
