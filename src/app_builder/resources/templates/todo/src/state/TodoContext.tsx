import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { t } from "../i18n";
import { loadTodos, newId, saveTodos, Todo } from "../storage/todos";

type TodoContextValue = {
  todos: Todo[];
  loading: boolean;
  error: string | null;
  reload: () => void;
  add: (title: string, note: string) => Promise<void>;
  update: (id: string, patch: Partial<Pick<Todo, "title" | "note" | "done">>) => Promise<void>;
  remove: (id: string) => Promise<void>;
  toggle: (id: string) => Promise<void>;
  clearDone: () => Promise<void>;
};

const Ctx = createContext<TodoContextValue | null>(null);

export function TodoProvider({ children }: { children: React.ReactNode }) {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const ref = useRef<Todo[]>([]);

  const reload = useCallback(() => {
    setLoading(true);
    setError(null);
    loadTodos()
      .then((items) => {
        ref.current = items;
        setTodos(items);
      })
      .catch(() => setError(t("loadFailed")))
      .finally(() => setLoading(false));
  }, []);

  useEffect(reload, [reload]);

  const commit = useCallback(async (next: Todo[]) => {
    const prev = ref.current;
    ref.current = next;
    setTodos(next);
    try {
      await saveTodos(next);
    } catch {
      ref.current = prev;
      setTodos(prev);
      setError(t("saveFailed"));
      throw new Error(t("saveFailed"));
    }
  }, []);

  const value = useMemo<TodoContextValue>(
    () => ({
      todos,
      loading,
      error,
      reload,
      add: (title, note) => {
        const now = Date.now();
        return commit([{ id: newId(), title: title.trim(), note: note.trim(), done: false, createdAt: now, updatedAt: now }, ...ref.current]);
      },
      update: (id, patch) =>
        commit(ref.current.map((x) => (x.id === id ? { ...x, ...patch, updatedAt: Date.now() } : x))),
      remove: (id) => commit(ref.current.filter((x) => x.id !== id)),
      toggle: (id) =>
        commit(ref.current.map((x) => (x.id === id ? { ...x, done: !x.done, updatedAt: Date.now() } : x))),
      clearDone: () => commit(ref.current.filter((x) => !x.done)),
    }),
    [todos, loading, error, reload, commit],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useTodos(): TodoContextValue {
  const v = useContext(Ctx);
  if (!v) throw new Error("useTodos phải nằm trong TodoProvider");
  return v;
}
