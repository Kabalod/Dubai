import React from "react";
import { Row, Col } from "antd";
import styles from "./Dashboard.module.scss";
import { DashboardProps } from "./typings";
import {
    extractTwoNumbers,
    formatPercent,
    formatPrice,
} from "@/Utilities/utils";
import { Trans } from "@lingui/react/macro";
import StockValue from "../StockValue/StockValue";
import DashboardBlock, { CardProps } from "../DashboardBlock/DashboardBlock";

const Dashboard: React.FC<DashboardProps> = ({ data, isLoading }) => {
    if (!data) return <></>;

    const [rangeFrom, rangeTo] = extractTwoNumbers(data.priceRange.range || "");

    const currency = "AED";

    const dashBlock1Items: CardProps[] = [
        {
            title: "Average Price",
            value: `${formatPrice(data.averagePrice.value)}`,
            suffix: <StockValue value={data.averagePrice.dynamic} />,
            currency: currency,
            against: `vs ${formatPrice(data.averagePrice.versus)} in Dubai`,
            ratio: `${
                data.averagePrice.comparison > 0 ? "better by" : "worse by"
            } ${formatPercent(data.averagePrice.comparison)}`,
        },
        {
            title: "Median Price",
            value: `${formatPrice(data.medianPrice.value)}`,
            suffix: <StockValue value={data.medianPrice.dynamic} />,
            currency: currency,
            against: `vs ${formatPrice(data.medianPrice.versus)} in Dubai`,
            ratio: `${
                data.medianPrice.comparison > 0 ? "better by" : "worse by"
            } ${formatPercent(data.medianPrice.comparison)}`,
        },
        {
            title: "Average price per sqm",
            value: `${formatPrice(data.averagePricePerSQM.value)}`,
            suffix: null,
            currency: currency,
            against: `vs ${formatPrice(
                data.averagePricePerSQM.versus
            )} in Dubai`,
            ratio: `${
                data.averagePricePerSQM.comparison > 0
                    ? "better by"
                    : "worse by"
            } ${formatPercent(data.averagePricePerSQM.comparison)}`,
        },
        {
            title: "Price range",
            value: `${rangeFrom} - ${rangeTo}`,
            suffix: <StockValue value={data.priceRange.dynamic} />,
            currency: currency,
            against: `vs ${formatPrice(data.priceRange.versus)} in Dubai`,
            ratio: `${
                data.priceRange.comparison > 0 ? "better by" : "worse by"
            } ${formatPercent(data.priceRange.comparison)}`,
        },
    ];

    const dashBlock2Items: CardProps[] = [
        {
            title: "Deals",
            value: `${formatPrice(data.deals.value)}`,
            suffix: <StockValue value={data.deals.dynamic} />,
            currency: "",
            against: `vs ${formatPrice(data.deals.versus)} in Dubai`,
            ratio: `${
                data.deals.comparison > 0 ? "better by" : "worse by"
            } ${formatPercent(data.deals.comparison)}`,
        },
        {
            title: "Deal Volume",
            value: `${formatPrice(data.dealsVolume.value)}`,
            suffix: <StockValue value={data.dealsVolume.dynamic} />,
            currency: currency,
            against: `vs ${formatPrice(data.dealsVolume.versus)} in Dubai`,
            ratio: `${
                data.dealsVolume.comparison > 0 ? "better by" : "worse by"
            } ${formatPercent(data.dealsVolume.comparison)}`,
        },
    ];

    const dashBlock3Items: CardProps[] = [
        {
            title: "Deals to the num of apartments",
            value: `${formatPrice(data.liquidity.value, 4)}`,
            suffix: <StockValue value={data.liquidity.dynamic} />,
            currency: "",
            against: `vs ${formatPrice(data.liquidity.versus)} in Dubai`,
            ratio: `${
                data.liquidity.comparison > 0 ? "better by" : "worse by"
            } ${formatPercent(data.liquidity.comparison)}`,
        },
    ];

    const dashBlock4Items: CardProps[] = [
        {
            title: "Average ROI",
            value: `${formatPrice(data.roi.value)}`,
            suffix: <StockValue value={data.roi.dynamic} />,
            currency: "%",
            against: `vs ${formatPrice(data.roi.versus)} in Dubai`,
            ratio: `${
                data.roi.comparison > 0 ? "better by" : "worse by"
            } ${formatPercent(data.roi.comparison)}`,
        },
    ];

    return (
        <section className={styles.container}>
            {/* Header Section */}
            <div className={styles.header}>
                <h2 className={styles.title}>
                    <Trans>Overview</Trans>
                </h2>
                <div className={styles.stats}>
                    <span className={styles.statLabel}>
                        <span className={styles.statValue}>
                            {data.totalBuildings}
                        </span>
                        &nbsp;
                        <Trans>BUILDINGS</Trans>
                    </span>
                    <span className={styles.statLabel}>
                        <span className={styles.statValue}>
                            {data.totalProperties}
                        </span>
                        &nbsp;
                        <Trans>APARTMENTS</Trans>
                    </span>
                    <span className={styles.statLabel}>
                        <span className={styles.statValue}>
                            {data.totalDeals}
                        </span>
                        &nbsp;
                        <Trans>DEALS</Trans>&nbsp;
                        <StockValue value={data.growthDynamicPercent} />
                    </span>
                </div>
            </div>

            {/* Price & Market Volume Sections (1st Row) */}
            <Row gutter={[24, 24]} className={styles.dashRow}>
                <Col span={12}>
                    <DashboardBlock title={"Price"} content={dashBlock1Items} />
                </Col>
                <Col span={12}>
                    <DashboardBlock
                        title={"Market Volume"}
                        content={dashBlock2Items}
                    />
                </Col>
            </Row>

            <Row gutter={[24, 24]}>
                <Col span={12}>
                    <DashboardBlock
                        title={"Liquidity"}
                        content={dashBlock3Items}
                    />
                </Col>
                <Col span={12}>
                    <DashboardBlock title={"ROI"} content={dashBlock4Items} />
                </Col>
            </Row>
        </section>
    );
};

export default Dashboard;
