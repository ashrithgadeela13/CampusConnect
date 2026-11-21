import {useEffect} from "react";

// Chrome may emit both events when switching windows. One read updates the current view.
export function useWindowReturn(onReturn: () => void, enabled = true) {
  useEffect(() => {
    if (!enabled) return;
    let timer: number | undefined;
    function schedule() {
      window.clearTimeout(timer);
      if (document.visibilityState === "hidden") return;
      timer = window.setTimeout(onReturn, 70);
    }
    window.addEventListener("focus", schedule);
    document.addEventListener("visibilitychange", schedule);
    return () => {
      window.clearTimeout(timer);
      window.removeEventListener("focus", schedule);
      document.removeEventListener("visibilitychange", schedule);
    };
  }, [onReturn, enabled]);
}
