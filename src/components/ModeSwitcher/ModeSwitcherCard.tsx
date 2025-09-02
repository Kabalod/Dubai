import { Col, Menu, Radio, Row } from "antd";
import styles from "./ModeSwitcher.module.scss";
import { Trans } from "@lingui/react/macro";
import { ReactElement } from "react";
import Separator from "../Separator/Separator";
import { MenuItem } from "@/types/global";

interface ModeSwitcherCardProps {
    isSelected: boolean;
    radValue: string;
    title: ReactElement;
    image: ReactElement;
    subtext: ReactElement;
}

const subMenuItems: MenuItem[] = [
    {
        label: <Trans>All</Trans>,
        key: "All",
    },
    {
        label: <Trans>Apartments</Trans>,
        key: "Apartments",
    },
    {
        label: <Trans>Villas</Trans>,
        key: "Villas",
    },
    {
        label: <Trans>Land</Trans>,
        key: "Land",
    },
    {
        label: <Trans>Commercial</Trans>,
        key: "Commercial",
    },
];

const ModeSwitcherCard: React.FC<ModeSwitcherCardProps> = ({
    isSelected,
    radValue,
    title,
    image,
    subtext,
}) => {
    const wrapper = isSelected ? styles.wrapperSelected : styles.wrapper;

    return (
        <Col className={wrapper} span={24}>
            <Row className={styles.radioRow}>
                <Radio value={radValue} className={styles.blueRadio}>
                    <span className={styles.title}>{title}</span>
                </Radio>
                {image}
            </Row>
            <Row>
                <Menu
                    items={subMenuItems}
                    mode="horizontal"
                    selectedKeys={["Apartments"]}
                    className={styles.menu}
                    overflowedIndicator={<span>⋮</span>}
                />
                <Separator offset={16} />
            </Row>
            <Row>
                <span className={styles.subtext}>{subtext}</span>
            </Row>
        </Col>
    );
};

export default ModeSwitcherCard;
