import { ReactNode } from "react";
import { AutoComplete } from "antd";
import styles from "./Autocomplete.module.scss";

export interface AutocompleteProps {
    value: string;
    options: AutocompleteOption[];
    placeholder: ReactNode;
    onSelect: (value: string, option: AutocompleteOption) => void;
    onSearch: (value: string) => void;
    onBlur: () => void;
}

/* this is abstract element, implement overrides */
const AutocompleteBase: React.FC<AutocompleteProps> = ({
    options,
    placeholder,
    value,
    onSelect,
    onSearch,
    onBlur,
}) => {
    return (
        <AutoComplete
            options={options}
            placeholder={placeholder}
            onSelect={onSelect}
            onSearch={onSearch}
            onFocus={() => onSearch(value)}
            onBlur={onBlur}
            value={value}
            allowClear
            className={styles.container}
        />
    );
};

export default AutocompleteBase;
