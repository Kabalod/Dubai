import React from "react";
import { Input, InputProps } from "antd";
import classNames from "classnames";
import styles from "./CustomInput.module.scss";

export type CustomInputProps = InputProps & {
  variant?: "default" | "ghost";
};

const CustomInput: React.FC<CustomInputProps> = ({ variant = "default", className, ...props }) => {
  const rootClass = classNames(styles.customInput, styles[variant], className);
  return <Input className={rootClass} {...props} />;
};

// Attach common subcomponents to keep API parity with antd
// Wrap to preserve styling classes
const attachClass = (Cls: any) =>
  React.forwardRef<any, any>(({ className, variant = "default", ...rest }, ref) => {
    const rootClass = classNames(styles.customInput, styles[variant], className);
    return <Cls ref={ref} className={rootClass} {...rest} />;
  });

(CustomInput as any).Password = attachClass(Input.Password);
(CustomInput as any).OTP = attachClass((Input as any).OTP);

export type { InputProps };
export default CustomInput;


