import { Divider } from "antd";

interface SeparatorProps {
    offset?: number;
}

const Separator: React.FC<SeparatorProps> = ({ offset = 12 }) => {
    return (
        <Divider
            style={{
                borderBlockStart: "2px solid #E3E6E8",
                margin: `${offset}px 0`,
            }}
        />
    );
};

export default Separator;
