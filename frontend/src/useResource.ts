import { useCallback, useEffect, useState } from "react";

/** Загрузка + перезагрузка. Всё, что нам нужно от «работы с данными». */
export function useResource<T>(load: () => Promise<T>, key: string) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);

  // key вместо массива зависимостей: у нас всё зависит от id цели и вкладки,
  // строка читается проще и не ломается при смене длины массива.
  const reload = useCallback(async () => {
    setLoading(true);
    try {
      setData(await load());
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { data, error, loading, reload, setData };
}
