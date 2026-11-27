import AsyncStorage from "@react-native-async-storage/async-storage";

export type Todo = {
  id: string;
  title: string;
  note: string;
  done: boolean;
  createdAt: number;
  updatedAt: number;
};

const KEY = "todos.v1";

function isTodo(x: unknown): x is Todo {
  const o = x as Todo;
  return !!o && typeof o.id === "string" && typeof o.title === "string" && typeof o.done === "boolean";
}

export async function loadTodos(): Promise<Todo[]> {
  const raw = await AsyncStorage.getItem(KEY);
  if (!raw) return [];
  const data: unknown = JSON.parse(raw);
  return Array.isArray(data) ? data.filter(isTodo) : [];
}

export async function saveTodos(todos: Todo[]): Promise<void> {
  await AsyncStorage.setItem(KEY, JSON.stringify(todos));
}

export function newId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}
