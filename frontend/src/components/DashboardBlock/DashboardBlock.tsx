import { Card, Col, Collapse, Row } from "antd";
import styles from "./DashboardBlock.module.scss";
import { ReactNode } from "react";
import iconChevronUp from "@/assets/chevron-up.svg";
import iconChevronDown from "@/assets/chevron-down.svg";
import iconInfo from "@/assets/info.svg";
import Separator from "../Separator/Separator";

export interface CardProps {
    title: string;
    value: string;
    currency: string;
    suffix: ReactNode;
    against: string;
    ratio: string;
}

interface DashboardBlockProps {
    title: string;
    content: CardProps[];
}

const DashboardBlock: React.FC<DashboardBlockProps> = ({ title, content }) => {
    return (
        <Collapse
            className={styles.container}
            bordered={false}
            defaultActiveKey={1}
            expandIconPosition="end"
            expandIcon={({ isActive }) => (
                <img
                    src={isActive ? iconChevronUp : iconChevronDown}
                    className={styles.chevron}
                />
            )}
            items={[
                {
                    key: 1,
                    label: <div className={styles.title}>{title}</div>,
                    children: (
                        <div className={styles.mosaic}>
                            {content.map((item, index) => {
                                return (
                                    <Card className={styles.card} key={item.title || `card-${index}`}>
                                        <Row>
                                            <Col span={16}>
                                                <span
                                                    className={styles.cardTitle}
                                                >
                                                    {item.title}
                                                </span>
                                            </Col>
                                            <Col
                                                span={8}
                                                className={styles.cardRightSide}
                                            >
                                                <img
                                                    src={iconInfo}
                                                    className={styles.iconInfo}
                                                />
                                            </Col>
                                        </Row>
                                        <Row>
                                            <Col span={16}>
                                                <span className={styles.value}>
                                                    {item.value}
                                                </span>
                                                <span
                                                    className={styles.currency}
                                                >
                                                    &nbsp;{item.currency}
                                                </span>
                                            </Col>
                                            <Col
                                                span={8}
                                                className={styles.cardRightSide}
                                            >
                                                {item.suffix}
                                            </Col>
                                        </Row>
                                        <Separator />
                                        <div className={styles.substring}>
                                            <span>{item.against}</span>
                                            {/* worth by / better можем пока убрать */}
                                            {/* <span>{item.ratio}</span> */}
                                        </div>
                                    </Card>
                                );
                            })}
                        </div>
                    ),
                },
            ]}
        ></Collapse>
    );
};

export default DashboardBlock;
