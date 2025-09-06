import React from "react";
import ReactDOM from "react-dom/client";
import { i18n } from "@lingui/core";
import { I18nProvider } from "@lingui/react";
import { messages as enMessages } from "./locales/en/messages";
import { messages as ruMessages } from "./locales/ru/messages";
import { messages as deMessages } from "./locales/de/messages";
import "./index.css"; // Подключаем базовые стили для UI компонентов (включает Tailwind + SCSS совместимость)
import App from "./App";

// Инициализация i18n
i18n.loadAndActivate({ locale: "en", messages: enMessages });

// Функция для смены языка
export function changeLanguage(locale: string) {
    let messages;
    switch (locale) {
        case "ru":
            messages = ruMessages;
            break;
        case "de":
            messages = deMessages;
            break;
        default:
            messages = enMessages;
            break;
    }
    i18n.loadAndActivate({ locale, messages });
}

const root = ReactDOM.createRoot(
    document.getElementById("root") as HTMLElement
);
root.render(
    <I18nProvider i18n={i18n}>
        <App />
    </I18nProvider>
);
