import React from "react";
import { Select, SelectProps } from "antd";
import classNames from "classnames";
import styles from "./CustomSelect.module.scss";

export type CustomSelectProps = SelectProps & {
  variant?: "default" | "ghost";
};

const CustomSelect: React.FC<CustomSelectProps> = ({ variant = "default", className, ...props }) => {
  const rootClass = classNames(styles.customSelect, styles[variant], className);
  return <Select className={rootClass} {...props} />;
};

export default CustomSelect;


