import React, { useMemo, useState, useCallback } from "react";
import { t } from "@lingui/core/macro";
import { apiService } from "../../services/apiService";
import { debounce } from "@/Utilities/utils";
import AutocompleteBase from "./AutocompleteBase";

export interface AutocompleteBuildingProps {
    onValueChange: (obj: AutocompleteState) => void;
}

const AutocompleteBuilding: React.FC<AutocompleteBuildingProps> = ({
    onValueChange,
}) => {
    const [value, setValue] = useState("");
    const [options, setOptions] = useState<AutocompleteOption[]>([]);
    const [loading, setLoading] = useState(false);

    const searchBuildings = useCallback(async (searchValue: string) => {
        if (!searchValue.trim()) {
            setOptions([]);
            return;
        }

        try {
            setLoading(true);
            console.log('🔍 Searching buildings for:', searchValue);
            
            // Комбинируем поиск по areas и buildings
            const [areasResponse, buildingsResponse] = await Promise.all([
                apiService.getAreas().catch(() => []),
                apiService.getBuildings({ limit: 50 }).catch(() => [])
            ]);
            
            // Фильтруем areas
            const filteredAreas = (areasResponse || []).filter((area: any) => 
                area.name?.toLowerCase().includes(searchValue.toLowerCase())
            );
            
            // Фильтруем buildings
            const buildingResults = buildingsResponse?.results || buildingsResponse || [];
            const filteredBuildings = buildingResults.filter((building: any) => 
                building.name?.toLowerCase().includes(searchValue.toLowerCase())
            );
            
            const areaOptions: AutocompleteOption[] = filteredAreas.map((area: any) => ({
                id: area.id?.toString(),
                value: area.name,
                type: "area" as SearchEntityType,
            }));
            
            const buildingOptions: AutocompleteOption[] = filteredBuildings.map((building: any) => ({
                id: building.id?.toString(),
                value: building.name,
                type: "building" as SearchEntityType,
            }));
            
            const combinedOptions = [...areaOptions, ...buildingOptions];
            setOptions(combinedOptions);
            console.log('✅ Found options:', combinedOptions.length);
            
        } catch (error) {
            console.warn('⚠️ Building search failed:', error);
            setOptions([]);
        } finally {
            setLoading(false);
        }
    }, []);

    const debouncedSearch = useMemo(
        () => debounce(searchBuildings, 400),
        [searchBuildings]
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

    const onBlur = () => {
        if (!value) {
            setValue(options[0]?.value ?? "");
        }
    };

    return (
        <AutocompleteBase
            placeholder={t({
                id: "autocomplete.building.placeholder",
                message: `Search by area, project or building`,
            })}
            options={options}
            onSearch={onSearch}
            onSelect={onSelect}
            onBlur={onBlur}
            value={value}
        />
    );
};

export default AutocompleteBuilding;
