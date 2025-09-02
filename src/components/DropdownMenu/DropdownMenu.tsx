import Dropdown from "antd/es/dropdown/dropdown";
import styles from "./DropdownMenu.module.scss";
import { Button, Col, Flex, Radio, Row } from "antd";
import { DownOutlined } from "@ant-design/icons";
import { ChangeEvent, ReactElement, useState } from "react";
import { Trans } from "@lingui/react/macro";
import Input from "antd/es/input/Input";
import AutocompleteDeveloper from "../autocomplete/AutocompleteDeveloper";
import Separator from "../Separator/Separator";

interface IDropdownMenuProps {
    content: ReactElement;
}

interface IDropdownMenuContentProps {
    onStateChange: (args: any) => void;
}

const initMoreState = {
    developer: "",
    soldBy: "",
    status: "",
    minPrice: "",
    maxPrice: "",
    minSize: "",
    maxSize: "",
};

const SoldByOptions = [
    {
        value: "ALL",
        label: "All",
    },
    {
        value: "SALE",
        label: "Sale",
    },
    {
        value: "RESALE",
        label: "Resale",
    },
];

const StatusOptions = [
    {
        value: "ALL",
        label: "All",
    },
    {
        value: "READY",
        label: "Ready",
    },
    {
        value: "OFFPLAN",
        label: "Off-plan",
    },
];

export const MoreDropdown: React.FC<IDropdownMenuContentProps> = ({
    onStateChange,
}) => {
    const [state, setState] = useState(initMoreState);

    const handleDeveloperChange = (obj: AutocompleteState) => {
        const newState = { ...state, developer: obj.value };
        setState(newState);
        onStateChange(newState); // ✅ ИСПРАВЛЕНО: вызываем callback
    };

    const handleMinPriceChange = (ev: ChangeEvent<HTMLInputElement>) => {
        const value = ev.target.value;
        console.log('🔄 Min price changed:', value);
        const newState = { ...state, minPrice: value };
        setState(newState);
        onStateChange(newState); // ✅ ИСПРАВЛЕНО: вызываем callback
    };

    const handleMinSizeChange = (ev: ChangeEvent<HTMLInputElement>) => {
        const value = ev.target.value;
        console.log('🔄 Min size changed:', value);
        const newState = { ...state, minSize: value };
        setState(newState);
        onStateChange(newState); // ✅ ИСПРАВЛЕНО: вызываем callback
    };
    
    const handleMaxSizeChange = (ev: ChangeEvent<HTMLInputElement>) => {
        const value = ev.target.value;
        console.log('🔄 Max size changed:', value);
        const newState = { ...state, maxSize: value };
        setState(newState);
        onStateChange(newState); // ✅ ИСПРАВЛЕНО: вызываем callback
    };

    const handleSoldByChange = (val: string) => {
        console.log('🔄 SoldBy changed:', { val });
        const newState = { ...state, soldBy: val };
        setState(newState);
        onStateChange(newState); // ✅ ИСПРАВЛЕНО: вызываем callback
    };
    
    const handleStatusChange = (val: string) => {
        console.log('🔄 Status changed:', { val });
        const newState = { ...state, status: val };
        setState(newState);
        onStateChange(newState); // ✅ ИСПРАВЛЕНО: вызываем callback
    };

    return (
        <Flex className={styles.wrapper} vertical>
            <Row className={styles.row}>
                <span className={styles.label}>
                    <Trans>Developer</Trans>
                </span>
                <AutocompleteDeveloper onValueChange={handleDeveloperChange} />
            </Row>
            <Row className={styles.row}>
                <span className={styles.title}>
                    <Trans>PRICE, AED</Trans>
                </span>
                <Row gutter={16}>
                    <Col span={12}>
                        <span className={styles.label}>MINIMUM</span>
                        <Input
                            onChange={handleMinPriceChange}
                            className={styles.input}
                        />
                    </Col>
                    <Col span={12}>
                        <span className={styles.label}>MAXIMUM</span>
                        <Input
                            onChange={handleMinPriceChange}
                            className={styles.input}
                        />
                    </Col>
                </Row>
            </Row>
            <Row className={styles.row}>
                <span className={styles.title}>
                    <Trans>SIZE M</Trans>
                    <sup>2</sup>
                </span>
                <Row gutter={16}>
                    <Col span={12}>
                        <span className={styles.label}>MINIMUM</span>
                        <Input
                            onChange={handleMinSizeChange}
                            className={styles.input}
                        />
                    </Col>
                    <Col span={12}>
                        <span className={styles.label}>MAXIMUM</span>
                        <Input
                            onChange={handleMaxSizeChange}
                            className={styles.input}
                        />
                    </Col>
                </Row>
            </Row>
            <Separator />
            <Row className={styles.row}>
                <span className={styles.title}>
                    <Trans>SOLD BY</Trans>
                </span>
                <Flex gap={"small"}>
                    {SoldByOptions.map((period, index) => (
                        <Button
                            shape="round"
                            className={styles.periodButton}
                            onClick={() => handleSoldByChange(period.value)}
                            color={"default"}
                            variant="outlined"
                            key={index}
                        >
                            {period.label}
                        </Button>
                    ))}
                </Flex>
            </Row>
            <Row className={styles.row}>
                <span className={styles.title}>
                    <Trans>STATUS</Trans>
                </span>
                <Flex gap={"small"}>
                    {StatusOptions.map((period, index) => (
                        <Button
                            shape="round"
                            className={styles.periodButton}
                            onClick={() => handleStatusChange(period.value)}
                            color={"default"}
                            variant="outlined"
                            key={index}
                        >
                            {period.label}
                        </Button>
                    ))}
                </Flex>
            </Row>
            <Separator />
            <Row className={styles.row}>
                <span className={styles.title}>
                    <Trans>OTHER</Trans>
                </span>
                <Radio.Group>
                    <Radio value={1}>Mortgage</Radio>
                </Radio.Group>
            </Row>
        </Flex>
    );
};

const DropdownMenu: React.FC<IDropdownMenuProps> = ({ content }) => {
    const [open, setOpen] = useState(false);
    return (
        <Dropdown
            // overlay={content}
            dropdownRender={() => content}
            trigger={["click"]}
            className={styles.buttonMore}
            onOpenChange={(open: boolean) => setOpen(open)}
            placement="bottom"
        >
            <Button>
                More <DownOutlined className={(open && styles.arrowUp) || ""} />
            </Button>
        </Dropdown>
    );
};

export default DropdownMenu;
