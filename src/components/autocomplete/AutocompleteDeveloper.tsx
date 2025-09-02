import React, { useMemo, useState, useCallback } from "react";
import { t } from "@lingui/core/macro";
import { apiService } from "../../services/apiService";
import { debounce } from "@/Utilities/utils";
import AutocompleteBase from "./AutocompleteBase";

export interface AutocompleteDeveloperProps {
    onValueChange: (obj: AutocompleteState) => void;
}

const AutocompleteDeveloper: React.FC<AutocompleteDeveloperProps> = ({
    onValueChange,
}) => {
    const [value, setValue] = useState("");
    const [options, setOptions] = useState<AutocompleteOption[]>([]);
    const [loading, setLoading] = useState(false);

    const searchAreas = useCallback(async (searchValue: string) => {
        if (!searchValue.trim()) {
            setOptions([]);
            return;
        }

        try {
            setLoading(true);
            console.log('🔍 Searching areas for:', searchValue);
            
            const response = await apiService.getAreas();
            const filteredAreas = response.filter((area: any) => 
                area.name.toLowerCase().includes(searchValue.toLowerCase())
            );
            
            const areaOptions: AutocompleteOption[] = filteredAreas.map((area: any) => ({
                id: area.id?.toString(),
                value: area.name,
                type: "area" as SearchEntityType,
            }));
            
            setOptions(areaOptions);
            console.log('✅ Found areas:', areaOptions.length);
            
        } catch (error) {
            console.warn('⚠️ Area search failed:', error);
            setOptions([]);
        } finally {
            setLoading(false);
        }
    }, []);

    const debouncedSearch = useMemo(
        () => debounce(searchAreas, 400),
        [searchAreas]
    );

    const onSearch = (value: string) => {
        setValue(value);
        debouncedSearch(value);
        onValueChange({
            id: undefined,
            type: undefined,
            value,
        });
    };

    const onSelect = (value: string, option: AutocompleteOption) => {
        setValue(value);
        onValueChange({
            id: option.id,
            type: option.type,
            value: option.value,
        });
    };

    const onBlur = () => {};

    return (
        <AutocompleteBase
            placeholder={t({
                id: "autocomplete.developer.placeholder",
                message: `Developer`,
            })}
            options={options}
            onSearch={onSearch}
            onSelect={onSelect}
            value={value}
            onBlur={onBlur}
        />
    );
};

export default AutocompleteDeveloper;
