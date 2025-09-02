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
    const { checkAuth } = useAuth(); // Добавляем checkAuth для обновления состояния

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
            // Сохраняем email, имя и пароль, чтобы не потерять при обновлении страницы
            localStorage.setItem('signup-email', values.email as string);
            localStorage.setItem('signup-name', values.name as string);
            localStorage.setItem('signup-password', values.password as string);
            console.log('Email and name set to state:', values.email, values.name);
            
            console.log('About to send OTP request via apiService');
            setSendingOtp(true);
            
            try {
                // Используем register endpoint который автоматически отправляет OTP
                const data = await apiService.register({
                    email: values.email,
                    password: values.password,
                    username: values.email,
                    password_confirm: values.confirmPassword,
                    first_name: values.name?.split(' ')[0] || '',
                    last_name: values.name?.split(' ').slice(1).join(' ') || ''
                });
                console.log('Registration initiated, OTP sent:', data);
                
                if (data.email_sent) {
                    message.success('OTP code sent to your email!');
                    setCurrentStep(FormSteps.Confirm);
                    setResendCooldown(60);
                } else {
                    console.warn('Email not sent:', data.email_error);
                    message.warning('Registration initiated but email may not be delivered. Check the OTP code in console for testing.');
                    setCurrentStep(FormSteps.Confirm);
                    setResendCooldown(60);
                }
            } catch (error: any) {
                console.error('Failed to send OTP:', error);
                if (error.message.includes('already exists')) {
                    message.error('User with this email already exists. Try logging in instead.');
                } else {
                    message.error('Failed to send OTP. Please try again.');
                }
            }
        } catch (err) {
            console.error('Error in handleSignUp:', err);
            // ✅ ИСПРАВЛЕНО: убрали message.error
        } finally {
            setSendingOtp(false);
        }
    };

    const handleValidation = async (values: any) => {
        try {
            // OTP код приходит как строка из компонента
            const otpCode = values.otp || "";
            
            console.log('=== handleValidation CALLED ===');
            console.log('OTP Code:', otpCode);
            console.log('Email:', email);
            
            console.log('About to verify OTP via apiService');
            
            setVerifyingOtp(true);
            try {
                // Получаем имена из localStorage (сохранены после первого шага)
                const savedName = localStorage.getItem('signup-name') || '';
                const firstName = savedName.split(' ')[0] || '';
                const lastName = savedName.split(' ').slice(1).join(' ') || '';
                
                const data = await apiService.verifyOTP(email, otpCode, firstName, lastName);
                console.log('OTP verified successfully:', data);
                
                // Сохраняем токены
                if (data.access && data.refresh) {
                    localStorage.setItem('accessToken', data.access);
                    localStorage.setItem('refreshToken', data.refresh);
                    console.log('Tokens saved to localStorage');
                    
                    // Сохраняем пользователя (используем 'user' ключ, как ожидает AuthContext)
                    if (data.user) {
                        localStorage.setItem('user', JSON.stringify(data.user));
                    }
                    
                    // Регистрация завершена успешно!
                    message.success('Registration completed successfully!');
                    
                    // Очищаем временные данные
                    localStorage.removeItem('signup-email');
                    localStorage.removeItem('signup-name');
                    localStorage.removeItem('signup-password');
                    
                    // Обновляем AuthContext чтобы header показал пользователя
                    checkAuth();
                    
                    // Переходим на главную страницу
                    navigate("/");
                    return;
                }
                
                // Если токенов нет - что-то пошло не так, но пользователь успешно верифицирован
                message.warning('Registration completed but no tokens received. Please try logging in.');
            } catch (error) {
                console.error('OTP verification failed:', error);
                message.error('Invalid OTP code. Please try again.');
            }
        } catch (err) {
            console.error('Error in handleValidation:', err);
            // ✅ ИСПРАВЛЕНО: убрали message.error
        } finally {
            setVerifyingOtp(false);
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
                const savedName = localStorage.getItem('signup-name') || '';
                const savedPassword = localStorage.getItem('signup-password') || '';
                const data = await apiService.register({
                    email: email,
                    password: savedPassword,
                    username: email,
                    password_confirm: savedPassword,
                    first_name: savedName.split(' ')[0] || '',
                    last_name: savedName.split(' ').slice(1).join(' ') || ''
                });
                
                if (data.email_sent) {
                    message.success('OTP code resent successfully!');
                } else {
                    message.warning('OTP resent but email may not be delivered.');
                }
                setResendCooldown(60);
            } catch (error: any) {
                console.error('Failed to resend OTP:', error);
                if (error.message.includes('already exists')) {
                    // Пользователь уже существует, но это OK для resend
                    message.warning('User already exists. If you didn\'t receive the code, try logging in.');
                } else {
                    message.error('Failed to resend OTP. Please try again.');
                }
            }
        } catch (err) {
            console.error('Resend OTP error:', err);
            // ✅ ИСПРАВЛЕНО: убрали message.error
        }
    };

    const steps = [
        {
            title: 'Register',
            icon: <UserOutlined />,
            description: 'Enter your details',
        },
        {
            title: 'Verify',
            icon: <CheckCircleOutlined />,
            description: 'Verify your email',
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
                            name="name"
                            label="Full Name"
                            placeholder="Enter your full name"
                            rules={[
                                { required: true, message: 'Please enter your name!' }
                            ]}
                            fieldProps={{
                                size: 'large',
                                prefix: <UserOutlined />,
                            }}
                        />
                        
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


            </ProCard>
        </div>
    );
};

export default SignUpForm;