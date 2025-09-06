import { useState, useCallback } from "react";

interface IMainQuery {
    transactionType: "RENT" | "SALE";
    searchedText: string;
    searchedType: SearchEntityType,
    searchedId: string,
    numberOfBeds: number,
    period: {
        start: Date;
        end: Date;
    };
}

export const useTableQuery = () => {
    const [query, setQuery] = useState<IMainQuery | null>(null);

    const updateQuery = useCallback((newQuery: IMainQuery) => {
        // query logic
        setQuery(newQuery);
    }, []);

    return { query, updateQuery }
}