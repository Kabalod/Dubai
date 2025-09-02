import React from "react";
import { Breadcrumb } from "antd";
import { Link, useLocation } from "react-router-dom";
import styles from "./PageLayout.module.scss";

type PageLayoutProps = {
    children: React.ReactNode;
};

const PageLayout: React.FC<PageLayoutProps> = ({ children }) => {
    const location = useLocation();
    const pathSnippets = location.pathname.split("/").filter(Boolean);

    const breadcrumbItems = [
        <Breadcrumb.Item key="home">
            <Link to="/">Home</Link>
        </Breadcrumb.Item>,
        ...pathSnippets.map((_, index) => {
            const url = `/${pathSnippets.slice(0, index + 1).join("/")}`;
            const label = pathSnippets[index].charAt(0).toUpperCase() + pathSnippets[index].slice(1);
            return (
                <Breadcrumb.Item key={url}>
                    <Link to={url}>{label}</Link>
                </Breadcrumb.Item>
            );
        }),
    ];

    return (
        <div className={styles.page}>
            <div className={styles.container}>
                <div className={styles.breadcrumbs}>
                    <Breadcrumb>{breadcrumbItems}</Breadcrumb>
                </div>
                <div className={styles.content}>{children}</div>
            </div>
        </div>
    );
};

export default PageLayout;


