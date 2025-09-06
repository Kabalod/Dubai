import React from "react";
import { Tabs, TabsProps } from "antd";
import classNames from "classnames";
import styles from "./CustomTabs.module.scss";

export type CustomTabsProps = TabsProps & {
  variant?: "default" | "segmented";
  className?: string;
};

const CustomTabs: React.FC<CustomTabsProps> = ({ variant = "default", className, ...props }) => {
  const rootClass = classNames(styles.customTabs, styles[variant], className);
  return <Tabs className={rootClass} {...props} />;
};

// Keep TabPane compatibility where needed
(CustomTabs as any).TabPane = (Tabs as any).TabPane;

export default CustomTabs;


