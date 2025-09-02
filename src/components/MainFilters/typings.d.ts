import { TransactionTypeEnum } from "@/api/schema";
import { Ordering } from "@/api/schema";

interface IMainQuery {
    transactionType: TransactionTypeEnum;
    searchSubstring: string;
    propertyComponents: PropertyComponents[];
    periods: Periods;
    offset: number;
    limit?: number;
    sorting: Ordering;
    // Расширенные фильтры
    propertyType?: string;
    area?: string;
    priceRange?: string;
    minPrice?: number | null;
    maxPrice?: number | null;
}

type PropertyComponents =
    | "Studio"
    | "Office"
    | "Single Room"
    | "GYM"
    | "PENTHOUSE"
    | "1"
    | "NA"
    | "Shop"
    | "1 B/R"
    | "2 B/R"
    | "3 B/R"
    | "4 B/R"
    | "5 B/R"
    | "6 B/R"
    | "7 B/R"
    | "8 B/R";

type Periods =
    | "1 week"
    | "1 month"
    | "3 months"
    | "6 months"
    | "1 year"
    | "2 years"
    | "YTD";

interface PropertyComponentsOption {
    value: PropertyComponents;
    label: string;
}

interface TransactionTypeOption {
    value: TransactionTypeEnum;
    label: string;
}

interface PeriodOption {
    value: Periods;
    label: string;
}

interface MainFilterProps {
    onSearch: (obj: IMainQuery) => void;
}

interface MainFilterState {
    tras;
}
