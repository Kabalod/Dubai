import React, { useEffect, useState } from 'react';
import { ProForm, ProFormText, ProFormCheckbox, ProCard } from '@ant-design/pro-components';
import { message, Steps, Form, Checkbox, Button, Input } from 'antd';
import CustomInput from '@/components/CustomInput/CustomInput';
import CustomButton from '@/components/CustomButton/CustomButton';
import styles from './SignUpForm.module.scss';
import { UserOutlined, MailOutlined, LockOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext'; // ✅ ДОБАВЛЕНО: используем AuthContext
import { API_BASE_URL } from '@/config';
import { apiService } from '../../services/api';

enum FormSteps {
    Join = 'join',
    Confirm = 'confirm',
    Details = 'details',
}

interface FieldType {
    email: string;
    name: string;
    password: string;
    confirmPassword: string;
}

const SignUpForm: React.FC = () => {
    const [currentStep, setCurrentStep] = useState<FormSteps>(FormSteps.Join);
    const [email, setEmail] = useState<string>('');
    const [submitting, setSubmitting] = useState<boolean>(false);
    const [sendingOtp, setSendingOtp] = useState<boolean>(false);
    const [verifyingOtp, setVerifyingOtp] = useState<boolean>(false);
    const [resendCooldown, setResendCooldown] = useState<number>(0);

    // Восстанавливаем email при монтировании (если страница обновлялась)
    useEffect(() => {
        const saved = localStorage.getItem('signup-email');
        if (saved && !email) {
            setEmail(saved);
        }
    }, []); // Намеренно игнорируем email в зависимостях для избежания цикла
    const [otpLength] = useState<number>(6);
    const navigate = useNavigate();

    const handleSignUp = async (values: FieldType) => {
        console.log('=== handleSignUp CALLED ===');
        console.log('Values:', values);
        console.log('Email from values:', values.email);
        
        try {
            setEmail(values.email as string);
            localStorage.setItem('signup-email', values.email as string);
            console.log('Email set to state:', values.email);
            
            setSendingOtp(true);
            
            try {
                // Инициируем регистрацию - это автоматически отправит OTP
                const data = await apiService.register({
                    email: values.email,
                    first_name: '', // Заполним на последнем шаге
                    last_name: ''   // Заполним на последнем шаге
                });
                console.log('Registration initiated, OTP sent:', data);
                
                if (data.otp_code) {
                    console.log('📧 DEBUG OTP Code:', data.otp_code);
                    message.info(`Debug: OTP Code is ${data.otp_code}`);
                }
                
                message.success('Verification code sent to your email!');
                setCurrentStep(FormSteps.Confirm);
                setResendCooldown(60);
            } catch (error: any) {
                console.error('Failed to send OTP:', error);
                
                // Обработка ошибки "пользователь уже существует"
                if (error.message && error.message.includes('already exists')) {
                    message.warning('Email already registered. Try verifying instead.');
                    // Все равно отправляем OTP для существующего пользователя
                    try {
                        const otpData = await apiService.sendOTP(values.email);
                        console.log('OTP sent for existing user:', otpData);
                        if (otpData.otp_code) {
                            console.log('📧 DEBUG OTP Code:', otpData.otp_code);
                            message.info(`Debug: OTP Code is ${otpData.otp_code}`);
                        }
                        setCurrentStep(FormSteps.Confirm);
                        setResendCooldown(60);
                    } catch (otpError) {
                        console.error('Failed to send OTP for existing user:', otpError);
                        message.error('Failed to send verification code. Please try again.');
                    }
                } else {
                    message.error('Registration failed. Please try again.');
                }
            }
        } catch (err) {
            console.error('Error in handleSignUp:', err);
            message.error('An unexpected error occurred. Please try again.');
        } finally {
            setSendingOtp(false);
        }
    };

    const handleValidation = async (values: any) => {
        try {
            const otpCode = values.otp || "";
            
            console.log('=== handleValidation CALLED ===');
            console.log('OTP Code:', otpCode);
            console.log('Email:', email);
            
            setVerifyingOtp(true);
            try {
                // Верифицируем OTP код
                const data = await apiService.verifyOTP(email, otpCode);
                console.log('OTP verified successfully:', data);
                
                // Сохраняем токены если они есть
                if (data.access) {
                    localStorage.setItem('accessToken', data.access);
                    localStorage.setItem('refreshToken', data.refresh);
                    console.log('Tokens saved to localStorage');
                    
                    // Сохраняем данные пользователя
                    if (data.user) {
                        localStorage.setItem('user', JSON.stringify(data.user));
                    }
                    
                    message.success('Email verified successfully!');
                    // Если уже есть токены - сразу переходим на главную
                    navigate('/');
                    return;
                }
                
                // Если токенов нет - переходим к заполнению деталей
                message.success('Email verified! Please complete your profile.');
                setCurrentStep(FormSteps.Details);
                
            } catch (error: any) {
                console.error('OTP verification failed:', error);
                
                if (error.message && error.message.includes('Invalid') || error.message.includes('expired')) {
                    message.error('Invalid or expired code. Please try again.');
                } else if (error.message && error.message.includes('attempts')) {
                    message.error('Too many attempts. Please request a new code.');
                } else {
                    message.error('Verification failed. Please try again.');
                }
            }
        } catch (err) {
            console.error('Error in handleValidation:', err);
            message.error('An unexpected error occurred. Please try again.');
        } finally {
            setVerifyingOtp(false);
        }
    };

    const handelFinishRegister = async (values: any) => {
        console.log('=== handelFinishRegister CALLED ===');
        console.log('Values parameter:', values);
        
        try {
            const effectiveEmail = email || localStorage.getItem('signup-email') || '';
            if (!effectiveEmail) {
                message.error('Email not found. Please start over.');
                setCurrentStep(FormSteps.Join);
                return;
            }
            
            setSubmitting(true);
            
            // Если уже есть токены - просто переходим на главную
            if (localStorage.getItem('accessToken')) {
                message.success('Welcome! Registration completed.');
                navigate("/");
                return;
            }
            
            // Обновляем профиль пользователя с именем
            const firstName = values.name.split(' ')[0] || '';
            const lastName = values.name.split(' ').slice(1).join(' ') || '';
            
            try {
                // Повторно верифицируем с именем и фамилией
                const data = await apiService.verifyOTP(effectiveEmail, '', firstName, lastName);
                console.log('Profile updated:', data);
                
                if (data.access) {
                    localStorage.setItem('accessToken', data.access);
                    localStorage.setItem('refreshToken', data.refresh);
                    
                    if (data.user) {
                        localStorage.setItem('user', JSON.stringify(data.user));
                    }
                }
                
                message.success('Registration completed successfully!');
                navigate("/");
                
            } catch (error: any) {
                console.error('Profile update failed:', error);
                // Если это не критично - все равно переходим
                message.warning('Registration completed, but profile update failed. You can update it later.');
                navigate("/");
            }
            
        } catch (error) {
            console.error('Registration error:', error);
            message.error('Registration failed. Please try again.');
        } finally {
            setSubmitting(false);
            // Очищаем временные данные
            localStorage.removeItem('signup-email');
        }
    };

    const getCookie = (name: string) => {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop()?.split(';').shift();
        return '';
    };

    // Тикер кулдауна
    useEffect(() => {
        if (resendCooldown <= 0) return;
        const id = setInterval(() => setResendCooldown((v) => v - 1), 1000);
        return () => clearInterval(id);
    }, [resendCooldown]);

    const resendCode = async () => {
        try {
            if (!email) {
                message.warning('Введите email на первом шаге');
                return;
            }
            if (resendCooldown > 0) {
                return;
            }

            console.log('Resend OTP to:', email);
            try {
                await apiService.sendOTP(email);
                message.success('OTP code resent successfully!');
                setResendCooldown(60);
            } catch (error) {
                console.error('Failed to resend OTP:', error);
                message.error('Failed to resend OTP. Please try again.');
            }
        } catch (err) {
            console.error('Resend OTP error:', err);
            // ✅ ИСПРАВЛЕНО: убрали message.error
        }
    };

    const steps = [
        {
            title: 'Email',
            icon: <MailOutlined />,
            description: 'Enter your email',
        },
        {
            title: 'Verify',
            icon: <CheckCircleOutlined />,
            description: 'Verify your email',
        },
        {
            title: 'Complete',
            icon: <UserOutlined />,
            description: 'Complete registration',
        },
    ];

    return (
        <div className={styles.pageRoot}>
            <ProCard
                className={styles.card}
                title={
                    <div className={styles.cardTitle}>
                        Welcome!
                    </div>
                }
            >
                <Steps
                    current={Object.values(FormSteps).indexOf(currentStep)}
                    items={steps}
                    className={styles.steps}
                />

                {currentStep === FormSteps.Join && (
                    <ProForm
                        onFinish={handleSignUp}
                        submitter={{
                            render: () => (
                                <CustomButton
                                    type="primary"
                                    size="large"
                                    htmlType="submit"
                                    block
                                    icon={<MailOutlined />}
                                    className={styles.primaryButton}
                                loading={sendingOtp}
                                disabled={sendingOtp}
                                >
                                    {sendingOtp ? 'Sending...' : 'SIGN UP'}
                                </CustomButton>
                            ),
                        }}
                    >
                        <ProFormText
                            name="email"
                            label="Email Address"
                            placeholder="Enter your email address"
                            rules={[
                                { required: true, message: 'Please enter your email!' },
                                { type: 'email', message: 'Please enter a valid email!' }
                            ]}
                            fieldProps={{
                                size: 'large',
                                prefix: <MailOutlined />,
                            }}
                        />
                    </ProForm>
                )}

                {currentStep === FormSteps.Confirm && (
                    <ProForm
                        onFinish={handleValidation}
                        submitter={{
                            render: () => (
                                <CustomButton
                                    type="primary"
                                    size="large"
                                    htmlType="submit"
                                    block
                                    icon={<CheckCircleOutlined />}
                                    className={styles.primaryButton}
                                loading={verifyingOtp}
                                disabled={verifyingOtp}
                                >
                                    {verifyingOtp ? 'Confirming...' : 'CONFIRM'}
                                </CustomButton>
                            ),
                        }}
                    >
                        <div className={styles.centerBlock}>
                            <CheckCircleOutlined className={styles.bigIcon} />
                            <h3>We have sent the code to {email}</h3>
                            <p className={styles.muted}>Enter the code to complete the registration</p>
                        </div>
                        
                        <ProFormText
                            name="otp"
                            label="Verification Code"
                            placeholder="Enter 6-digit code"
                            rules={[
                                { required: true, message: 'Please enter the verification code!' },
                                { len: 6, message: 'Code must be 6 digits!' },
                                { pattern: /^\d{6}$/, message: 'Code must contain only digits!' }
                            ]}
                            fieldProps={{
                                size: 'large',
                                maxLength: 6,
                                style: { textAlign: 'center', fontSize: '18px', letterSpacing: '4px' }
                            }}
                        />

                        <div className={styles.centerBlock}>
                            <CustomButton type="link" onClick={resendCode} disabled={resendCooldown > 0}>
                                {resendCooldown > 0 ? `Send the code again (${resendCooldown}s)` : 'Send the code again'}
                            </CustomButton>
                        </div>
                    </ProForm>
                )}

                {currentStep === FormSteps.Details && (
                    <ProForm
                        onFinish={handelFinishRegister}
                        submitter={{
                            render: () => (
                                <CustomButton
                                    type="primary"
                                    size="large"
                                    htmlType="submit"
                                    loading={submitting}
                                    block
                                    icon={<UserOutlined />}
                                    className={styles.primaryButton}
                                >
                                    CREATE ACCOUNT
                                </CustomButton>
                            ),
                        }}
                    >
                        <ProFormText
                            name="name"
                            label="Full Name"
                            placeholder="Enter your full name"
                            rules={[{ required: true, message: 'Please enter your name!' }]}
                            fieldProps={{
                                size: 'large',
                                prefix: <UserOutlined />,
                            }}
                        />

                        <ProFormText.Password
                            name="password"
                            label="Password"
                            placeholder="Enter your password"
                            rules={[
                                { required: true, message: 'Please enter your password!' },
                                { min: 8, message: 'Password must be at least 8 characters!' }
                            ]}
                            fieldProps={{
                                size: 'large',
                                prefix: <LockOutlined />,
                            }}
                        />

                        <ProFormText.Password
                            name="confirmPassword"
                            label="Confirm Password"
                            placeholder="Confirm your password"
                            rules={[
                                { required: true, message: 'Please confirm your password!' },
                                ({ getFieldValue }) => ({
                                    validator(_, value) {
                                        if (!value || getFieldValue('password') === value) {
                                            return Promise.resolve();
                                        }
                                        return Promise.reject(new Error('Passwords do not match!'));
                                    },
                                }),
                            ]}
                            fieldProps={{
                                size: 'large',
                                prefix: <LockOutlined />,
                            }}
                        />

                        <ProFormCheckbox
                            name="agreement"
                            rules={[{ required: true, message: 'Please accept the terms!' }]}
                        >
                            I have read the{' '}
                            <a href="/policy" target="_blank">
                                policy agreement
                            </a>
                            {' '}and I consent to the processing of{' '}
                            <a href="/privacy" target="_blank">
                                personal data
                            </a>
                        </ProFormCheckbox>
                    </ProForm>
                )}
            </ProCard>
        </div>
    );
};

export default SignUpForm;