import React from "react";
import styles from "./NotFound.module.scss";

function NotFound() {
    return (
        <div className={styles.root}>
            <h1>❌ 404 - Страница не найдена</h1>
            <h2>Запрашиваемая страница не существует</h2>

            <div className={styles.links}>
                <p className={styles.lead}>
                    Возможно, вы перешли по неверной ссылке или страница была удалена.
                </p>
            </div>

            <div className={styles.links}>
                <h3>🔗 Доступные страницы:</h3>
                <div className={styles.linkRow}>
                    <a href="/" className={`${styles.btn} ${styles.btnHome}`}>Главная</a>
                    <a href="/dashboard" className={`${styles.btn} ${styles.btnDash}`}>Dashboard</a>
                    <a href="/analytics" className={`${styles.btn} ${styles.btnAnalytics}`}>Аналитика</a>
                    <a href="/auth" className={`${styles.btn} ${styles.btnAuth}`}>Авторизация</a>
                </div>
            </div>

            <div className={styles.links}>
                <p>Или вернитесь на <a href="/" className={styles.backLink}>главную страницу</a></p>
            </div>
        </div>
    );
}

export default NotFound;
