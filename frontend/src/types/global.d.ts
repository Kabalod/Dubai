import { MenuProps } from "antd";

declare module "*.svg" {
    const content: string;
    export default content;
}

interface LoginResponse {
    login: {
        token: string;
        user: {
            id: string;
            name: string;
        };
    };
}

interface LoginVariables {
    email: string;
    password: string;
}

type MenuItem = Required<MenuProps>["items"][number];
