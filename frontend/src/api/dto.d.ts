export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends { [key: string]: unknown }> = {
    [K in keyof T]: T[K];
};
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & {
    [SubKey in K]?: Maybe<T[SubKey]>;
};
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & {
    [SubKey in K]: Maybe<T[SubKey]>;
};
export type MakeEmpty<
    T extends { [key: string]: unknown },
    K extends keyof T
> = { [_ in K]?: never };
export type Incremental<T> =
    | T
    | {
          [P in keyof T]?: P extends " $fragmentName" | "__typename"
              ? T[P]
              : never;
      };

export type Scalars = {
    ID: { input: string; output: string };
    String: { input: string; output: string };
    Boolean: { input: boolean; output: boolean };
    Int: { input: number; output: number };
    Float: { input: number; output: number };
};

export type AggregationResultType = {
    __typename?: "AggregationResultType";
    averagePrice: AggregationType;
    averagePricePerSQM: AggregationType;
    deals: AggregationType;
    dealsVolume: AggregationType;
    growthDynamicPercent: Scalars["Float"]["output"];
    liquidity: AggregationType;
    medianPrice: AggregationType;
    priceRange: AggregationType;
    roi: AggregationType;
    totalBuildings: Scalars["Int"]["output"];
    totalDeals: Scalars["Int"]["output"];
    totalProperties: Scalars["Int"]["output"];
};

export type AggregationType = {
    __typename?: "AggregationType";
    comparison: Scalars["Float"]["output"];
    dynamic: Scalars["Float"]["output"];
    range: Scalars["String"]["output"];
    value: Scalars["Float"]["output"];
    versus: Scalars["Float"]["output"];
};

export type MarketVolumeType = {
    __typename?: "MarketVolumeType";
    commentNumber: Scalars["String"]["output"];
    deals: Scalars["Float"]["output"];
    dealsChangePercent: Scalars["Float"]["output"];
    direction: Scalars["String"]["output"];
    dynamicPercent: Scalars["Float"]["output"];
    liquidity: Scalars["Float"]["output"];
    liquidityChangePercent: Scalars["Float"]["output"];
    volumeDeals: Scalars["Float"]["output"];
};
export type PriceModelType = {
    __typename?: "PriceModelType";
    averagePrice: Scalars["Float"]["output"];
    averagePricePerSqm: Scalars["Float"]["output"];
    avgPriceSqmChangePercent: Scalars["Float"]["output"];
    commentNumber: Scalars["String"]["output"];
    direction: Scalars["String"]["output"];
    dynamicPercent: Scalars["Float"]["output"];
    medianPrice: Scalars["Float"]["output"];
    medianPriceChangePercent: Scalars["Float"]["output"];
    priceRange: Scalars["String"]["output"];
    priceRangeChangePercent: Scalars["Float"]["output"];
    roi: Scalars["Float"]["output"];
    roiChangePercent: Scalars["Float"]["output"];
};

// export type MergedTransactionConnection = {
//     __typename?: "MergedTransactionConnection";
//     edges: Array<MergedTransactionGQLType>;
//     pageInfo: PageInfo;
// };

export type PageInfo = {
    __typename?: "PageInfo";
    endCursor?: Maybe<Scalars["String"]["output"]>;
    hasNextPage: Scalars["Boolean"]["output"];
    hasPreviousPage: Scalars["Boolean"]["output"];
    startCursor?: Maybe<Scalars["String"]["output"]>;
    totalCount: Scalars["Int"]["output"];
};

export type QueryGetAggregationsArgs = {
    periods?: InputMaybe<Scalars["String"]["input"]>;
    propertyComponents?: InputMaybe<Array<Scalars["String"]["input"]>>;
    searchSubstring?: InputMaybe<Scalars["String"]["input"]>;
    somethingImportantV1?: InputMaybe<Array<Scalars["String"]["input"]>>;
    transactionType: Scalars["String"]["input"];
};

export type QueryGetFilterOptionsArgs = {
    transactionType: Scalars["String"]["input"];
};

export type QuerySearchTransactionsArgs = {
    periods?: InputMaybe<Scalars["String"]["input"]>;
    propertyComponents?: InputMaybe<Array<Scalars["String"]["input"]>>;
    searchSubstring?: InputMaybe<Scalars["String"]["input"]>;
    somethingImportantV1?: InputMaybe<Array<Scalars["String"]["input"]>>;
    transactionType: Scalars["String"]["input"];
};

export type FilterOptionsType = {
    __typename?: "FilterOptionsType";
    periods: Scalars["String"]["output"];
    propertyComponents: Array<Scalars["String"]["output"]>;
    somethingImportantV1: Array<Scalars["String"]["output"]>;
};

export type Query = {
    __typename?: "Query";
    getAggregations: AggregationResultType;
    searchTransactions: MergedTransactionTypeOffsetPaginated;
};

// export type MergedTransactionGQLType = {
//     __typename?: "MergedTransactionGQLType";
//     actualWorth?: Maybe<Scalars["Float"]["output"]>;
//     areaNameEn?: Maybe<Scalars["String"]["output"]>;
//     buildingName?: Maybe<Scalars["String"]["output"]>;
//     dateOfTransaction?: Maybe<Scalars["String"]["output"]>;
//     dealYear?: Maybe<Scalars["Int"]["output"]>;
//     developerNameEn?: Maybe<Scalars["String"]["output"]>;
//     id: Scalars["Int"]["output"];
//     locationName?: Maybe<Scalars["String"]["output"]>;
//     meterSalePrice?: Maybe<Scalars["Float"]["output"]>;
//     roi?: Maybe<Scalars["Float"]["output"]>;
//     roomsEn?: Maybe<Scalars["String"]["output"]>;
//     sqm?: Maybe<Scalars["Float"]["output"]>;
// };

export type MergedTransactionTypeOffsetPaginated = {
    __typename?: "MergedTransactionTypeOffsetPaginated";
    pageInfo: OffsetPaginationInfo;
    /** List of paginated results. */
    results: Array<MergedTransactionType>;
    /** Total count of existing results. */
    totalCount: Scalars["Int"]["output"];
};

export type MergedTransactionType = {
    __typename?: "MergedTransactionType";
    actualWorth?: Maybe<Scalars["Float"]["output"]>;
    areaNameEn?: Maybe<Scalars["String"]["output"]>;
    buildingName?: Maybe<Scalars["String"]["output"]>;
    dateOfTransaction?: Maybe<Scalars["String"]["output"]>;
    dealYear?: Maybe<Scalars["Int"]["output"]>;
    developerNameEn?: Maybe<Scalars["String"]["output"]>;
    id: Scalars["ID"]["output"];
    locationName?: Maybe<Scalars["String"]["output"]>;
    meterSalePrice?: Maybe<Scalars["Float"]["output"]>;
    roi?: Maybe<Scalars["Float"]["output"]>;
    roomsEn?: Maybe<Scalars["String"]["output"]>;
    sqm?: Maybe<Scalars["Float"]["output"]>;
};
