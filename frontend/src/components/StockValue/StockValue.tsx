import styles from "./StockValue.module.scss";
import iconUp from "@/assets/stock_arrow_up.svg";
import iconDown from "@/assets/stock_arrow_down.svg";

interface StockValueProps {
    value: number;
    precision?: number;
}

const StockValue: React.FC<StockValueProps> = ({ value, precision = 2 }) => {
    const prec = 10 ** precision;
    const roundedNumber = Math.round(value * prec) / prec;
    const formattedNumber = roundedNumber.toFixed(2);
    const classname = roundedNumber >= 0 ? styles.pos : styles.neg;
    const icon = roundedNumber >= 0 ? iconUp : iconDown;

    return (
        <span className={classname}>
            &nbsp;
            {formattedNumber}%
            <img src={icon} />
        </span>
    );
};

export default StockValue;
