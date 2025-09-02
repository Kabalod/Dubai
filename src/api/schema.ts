import { MergedTransactionType } from "./dto";

export interface AreaType {
    __typename: string;
    id: number;
    areaIdx: number;
    nameAr: string;
    nameEn: string;
}

export interface BuildingType {
    __typename: string;
    id: number;
    buildingNumber: string;
    nameAr: string;
    nameEn: string;
}

export interface ProjectType {
    __typename: string;
    id: number;
    projectNumber: string;
    englishName: string;
    arabicName: string;
    worth: number;
    totalArea: number;
    totalUnits: number;
    descriptionEn: string;
    descriptionAr: string;
    statusEn: string;
    statusAr: string;
    completionRatio: number;
    completionDate: Date;
    startDate: Date;
    registrationDate: Date;
    escrowAgentEn: string;
    escrowAgentAr: string;
    escrowAccount: string;
    isFollowed: boolean;
    rooms: Record<string, string>;
    sizing: Record<string, string>;
    facilities: Record<string, string>;
    arFileUrl: string;
    projectIdx: number;
    nameAr: string;
    nameEn: string;
    projectNameEn: string;
    developer: DeveloperType;
    mainDeveloper: DeveloperType;
}

export interface DeveloperType {
    id: number;
    number: string;
    englishName: string;
    rating: string;
}
export interface AutocompleteResults {
    autocomplete: {
        areas: AreaType[];
        buildings: BuildingType[];
        projects: ProjectType[];
    };
}

export type AutocompleteQueryVariables = {
    search: string;
};

export type SearchTransactionsQuery = {
    searchTransactions: Array<MergedTransactionType>;
};

export type SearchTransactionsQueryVariables = {
    search: string;
    transactionType: TransactionTypeEnum;
};

export type TransactionTypeEnum = "SALE" | "RENT";

export enum Ordering {
    Asc = "ASC",
    AscNullsFirst = "ASC_NULLS_FIRST",
    AscNullsLast = "ASC_NULLS_LAST",
    Desc = "DESC",
    DescNullsFirst = "DESC_NULLS_FIRST",
    DescNullsLast = "DESC_NULLS_LAST",
}
