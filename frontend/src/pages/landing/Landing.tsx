import React from "react";
import styles from "./Landing.module.scss";

const Landing = () => {
    return (
        <div className={styles.root}>
            <h1 className={styles.title}>🏠 Real Estate Analytics Platform</h1>

            <div className={styles.card}>
                <h2 className={styles.statusTitle}>
                    ✅ Система успешно запущена!
                </h2>

                <p className={styles.lead}>
                    Ваша платформа для анализа недвижимости Дубая готова к работе
                </p>

                <div className={styles.grid}>
                    <div className={styles.boxGreen}>
                        <h3>📊 Аналитика</h3>
                        <p>Глубокий анализ рынка</p>
                    </div>
                    <div className={styles.boxBlue}>
                        <h3>🔍 Поиск</h3>
                        <p>Поиск недвижимости</p>
                    </div>
                    <div className={styles.boxGold}>
                        <h3>📈 Отчеты</h3>
                        <p>Детальные отчеты</p>
                    </div>
                </div>

                <div className={styles.status}>
                    <h3>🚀 Архитектура запущена:</h3>
                    <ul className={styles.list}>
                        <li>Backend Django: порты 8000, 8001</li>
                        <li>Frontend React: порт 5173</li>
                        <li>HTTP тест: порт 3000</li>
                    </ul>
                </div>
            </div>
        </div>
    );
};

export default Landing;
