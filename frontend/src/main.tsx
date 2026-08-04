import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "@/App";
import "@/index.css";

const container = document.getElementById("root");
if (!container) throw new Error("Не найден #root — проверь index.html");

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
