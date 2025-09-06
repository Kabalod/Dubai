import { Col, Radio, Row } from "antd";
import styles from "./ModeSwitcher.module.scss";
import { useState } from "react";
import { Trans } from "@lingui/react/macro";
import iconDLD from "@/assets/icon_DLD.svg";
import iconMarket from "@/assets/icon_Marketplace.svg";
import ModeSwitcherCard from "./ModeSwitcherCard";

const ModeSwitcher: React.FC<{}> = () => {
    const [value, setValue] = useState("option1");

    return (
        <Radio.Group
            onChange={(e) => setValue(e.target.value)}
            value={value}
            className={styles.container}
            disabled
        >
            <Row gutter={{ xs: 8, sm: 16, md: 24, lg: 32 }}>
                <Col span={12}>
                    <ModeSwitcherCard
                        radValue="option1"
                        title={<Trans>DLD</Trans>}
                        isSelected={value === "option1"}
                        image={<img src={iconDLD} />}
                        subtext={
                            <Trans>
                                Analyze all real transaction data obtained from
                                Dubai Land Department.
                            </Trans>
                        }
                    />
                </Col>
                <Col span={12}>
                    <ModeSwitcherCard
                        radValue="option2"
                        title={<Trans>Marketplace</Trans>}
                        isSelected={value === "option2"}
                        image={<img src={iconMarket} />}
                        subtext={
                            <Trans>
                                Analyze data received from real estate sales
                                marketplaces.
                            </Trans>
                        }
                    />
                </Col>
            </Row>
        </Radio.Group>
    );
};

export default ModeSwitcher;
