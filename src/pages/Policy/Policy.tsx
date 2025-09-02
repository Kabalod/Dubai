import React from "react";
import { Card, Typography, Divider, List, Alert } from "antd";
import styles from './Policy.module.scss';

const { Title, Paragraph, Text } = Typography;

const Policy: React.FC = () => {
    const privacyItems = [
        "Contact information (name, email, phone)",
        "Usage analytics data",
        "Real estate preferences",
        "Transaction history",
        "Communication preferences",
    ];

    const usageItems = [
        "Providing personalized services",
        "Improving platform quality",
        "Market trend analysis",
        "Customer communication",
        "Legal compliance",
    ];

    const rightsItems = [
        "Access your personal data",
        "Request data correction",
        "Request data deletion",
        "Withdraw consent",
        "Data portability",
    ];

    return (
        <div className={styles.root}>
            <Card>
                <Title level={1}>📋 Privacy Policy & Terms of Service</Title>
                <Paragraph>
                    This Privacy Policy describes how Dubai Real Estate Platform collects, uses, and protects your personal information.
                    By using our services, you agree to the collection and use of information in accordance with this policy.
                </Paragraph>

                <Divider />

                <Title level={2}>🔒 Data Collection & Privacy</Title>
                <Paragraph>
                    We respect your privacy and are committed to protecting your personal data in accordance with international standards
                    and the General Data Protection Regulation (GDPR).
                </Paragraph>

                <Card title="Information We Collect" className={styles.cardMb}>
                    <List
                        dataSource={privacyItems}
                        renderItem={(item) => (
                            <List.Item>
                                <Text>• {item}</Text>
                            </List.Item>
                        )}
                    />
                </Card>

                <Card title="How We Use Your Data" className={styles.cardMb}>
                    <List
                        dataSource={usageItems}
                        renderItem={(item) => (
                            <List.Item>
                                <Text>• {item}</Text>
                            </List.Item>
                        )}
                    />
                </Card>

                <Divider />

                <Title level={2}>🛡️ Data Security</Title>
                <Alert
                    message="Security Measures"
                    description="We implement industry-standard security measures including encryption, secure servers, and regular security audits to protect your data."
                    type="info"
                    showIcon
                    className={styles.alertMb}
                />

                <Paragraph>
                    Your data is stored on secure servers with encryption at rest and in transit. We regularly review and update
                    our security practices to ensure the highest level of protection.
                </Paragraph>

                <Divider />

                <Title level={2}>👤 Your Rights</Title>
                <Card title="Data Subject Rights" className={styles.cardMb}>
                    <List
                        dataSource={rightsItems}
                        renderItem={(item) => (
                            <List.Item>
                                <Text>• {item}</Text>
                            </List.Item>
                        )}
                    />
                </Card>

                <Paragraph>
                    You have the right to access, correct, or delete your personal data at any time. To exercise these rights,
                    please contact our Data Protection Officer at privacy@dubairealestate.com
                </Paragraph>

                <Divider />

                <Title level={2}>🌍 International Transfers</Title>
                <Paragraph>
                    Your data may be transferred to and processed in countries other than your own. We ensure that such transfers
                    comply with applicable data protection laws and implement appropriate safeguards.
                </Paragraph>

                <Divider />

                <Title level={2}>📞 Contact Information</Title>
                <Card>
                    <Paragraph>
                        <strong>Data Protection Officer:</strong><br />
                        Email: privacy@dubairealestate.com<br />
                        Phone: +971 4 XXX XXXX<br />
                        Address: Dubai Internet City, Dubai, UAE
                    </Paragraph>
                </Card>

                <Divider />

                <Title level={2}>📅 Policy Updates</Title>
                <Paragraph>
                    This Privacy Policy may be updated from time to time. We will notify you of any changes by posting the new
                    policy on this page and updating the "Last Updated" date.
                </Paragraph>

                <Text type="secondary">Last Updated: August 15, 2025</Text>
            </Card>
        </div>
    );
};

export default Policy;
