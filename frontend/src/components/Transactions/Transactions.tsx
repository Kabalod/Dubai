import React from "react";
import { Flex, TablePaginationConfig, TableProps } from "antd";
import { Table } from "antd";
import CustomButton from "@/components/CustomButton/CustomButton";
import {
    MergedTransactionType,
    MergedTransactionTypeOffsetPaginated,
} from "@/api/dto";
import styles from "./Transactions.module.scss";
import { formatPrice } from "@/Utilities/utils";
import { SorterResult } from "antd/es/table/interface";

export interface TransactionsProps {
    data: MergedTransactionTypeOffsetPaginated | null;
    dateRange: [string, string];
    pagination: TablePaginationConfig;
    isTransLoading: boolean;
    sortedInfo: SorterResult<MergedTransactionType>;
    handlePageChange: (
        pagination: TablePaginationConfig,
        sorter:
            | SorterResult<MergedTransactionType>
            | SorterResult<MergedTransactionType>[]
    ) => void;
}

export interface TransactionsState {
    data: Array<MergedTransactionType>;
}

const paginationSetup: TablePaginationConfig = {
    position: ["bottomCenter"],
    showSizeChanger: true,
    responsive: true,
    pageSizeOptions: [10, 20],
};

const Transactions: React.FC<TransactionsProps> = ({
    data,
    dateRange,
    pagination,
    sortedInfo,
    isTransLoading,
    handlePageChange,
}) => {
    const numberOfRecords = data?.totalCount ?? 0;
    const transactions =
        data?.results?.map((d, index) => ({ ...d, key: d.id || `transaction-${index}` })) ?? [];

    const handlePagination = (
        pagination: TablePaginationConfig,
        f: any,
        sorter:
            | SorterResult<MergedTransactionType>
            | SorterResult<MergedTransactionType>[]
    ) => {
        handlePageChange(pagination, sorter);
    };

    const columns: TableProps<MergedTransactionType>["columns"] = [
        {
            title: "Date",
            dataIndex: "dateOfTransaction",
            key: "dateOfTransaction",
            // sorter: (a, b) => randomShitSorter(a, b, "dateOfTransaction"),
            sorter: true,
            sortOrder:
                (sortedInfo.column?.title === "Date" && sortedInfo.order) ||
                undefined,
        },
        {
            title: "Location",
            dataIndex: "areaNameEn",
            key: "areaNameEn",
            render: (text) => <span className={styles.cellPre}>{text}</span>,
            // sorter: (a, b) => randomShitSorter(a, b, "areaNameEn"),
        },
        {
            title: "Building",
            dataIndex: "buildingName",
            key: "buildingName",
            render: (text) => <span className={styles.cellPre}>{text}</span>,
            // sorter: (a, b) => randomShitSorter(a, b, "buildingName"),
        },
        {
            title: "Rooms",
            dataIndex: "roomsEn",
            key: "roomsEn",
            // sorter: (a, b) => randomShitSorter(a, b, "roomsEn"),
        },
        {
            title: "Sq. Meters",
            dataIndex: "sqm",
            key: "sqm",
            // sorter: (a, b) => randomShitSorter(a, b, "sqm"),
            render: (value, record, index) => formatPrice(value, 2),
        },
        {
            title: "ROI",
            dataIndex: "roi",
            key: "roi",
            // sorter: (a, b) => randomShitSorter(a, b, "roi"),
        },
        {
            title: "Price, AED",
            dataIndex: "actualWorth",
            key: "actualWorth",
            // sorter: (a, b) => randomShitSorter(a, b, "actualWorth"),
        },
        {
            title: "",
            key: "action",
            render: () => (
                <CustomButton variant="link" className={styles.detailsLink}>
                    Details
                </CustomButton>
            ),
        },
    ];

    return (
        <section>
            <h2 className={styles.title}>Transactions</h2>
            <Flex justify="space-between">
                <div>
                    <span className={styles.subtitle}>
                        From&nbsp;
                        <span className={styles.subtitleVal}>
                            {dateRange[0]}
                        </span>
                        &nbsp;to&nbsp;
                        <span className={styles.subtitleVal}>
                            {dateRange[1]}
                        </span>
                    </span>
                </div>
                <span className={styles.subtitle}>
                    {numberOfRecords} results
                </span>
            </Flex>

            <div className={styles.tableContainer}>
                <Table<MergedTransactionType>
                    columns={columns}
                    dataSource={transactions}
                    loading={isTransLoading}
                    pagination={{
                        ...paginationSetup,
                        ...pagination,
                        total: data?.totalCount,
                    }}
                    className={styles.table}
                    onChange={handlePagination}
                />
            </div>
        </section>
    );
};

export default Transactions;
