import React from "react";
import { Button } from "antd";
import { ButtonProps as AntButtonProps } from "antd/lib/button";
import classNames from "classnames";
import styles from "./CustomButton.module.scss";

interface CustomButtonProps extends AntButtonProps {
  variant?: "primary" | "secondary" | "outline" | "icon" | "link";
}

const CustomButton: React.FC<CustomButtonProps> = ({
  variant = "primary",
  className,
  ...props
}) => {
  const buttonClasses = classNames(
    styles.customBtn,
    variant && styles[`btn_${variant}`],
    className
  );

  return <Button className={buttonClasses} {...props} />;
};

export default CustomButton;
