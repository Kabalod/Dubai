import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { User, Shield, Key, Info, Check, Star, CreditCard } from 'lucide-react';
import apiService from '@/services/apiService';

// Тарифные планы (упрощенная версия для Profile)
const PRICING_PLANS = [
  {
    id: 'free',
    name: 'Free',
    price: 0,
    period: 'month',
    description: 'Basic access to property data',
    features: [
      'View up to 50 properties per day',
      'Basic search and filters', 
      'Public analytics dashboard',
      'Email support',
    ],
    color: 'gray',
    current: false,
  },
  {
    id: 'premium',
    name: 'Premium', 
    price: 299,
    period: 'month',
    description: 'Full access with advanced features',
    features: [
      'Unlimited property access',
      'Advanced search and analytics',
      'Export to CSV/Excel', 
      'Real-time market insights',
      'Premium dashboard with charts',
      'Priority email & chat support',
      'API access (limited)',
    ],
    color: 'blue',
    current: true,
    popular: true,
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: 999,
    period: 'month', 
    description: 'Enterprise solution with full API access',
    features: [
      'Everything in Premium',
      'Full API access with high limits',
      'Custom integrations',
      'Dedicated account manager',
      'SLA guarantee',
      '24/7 phone support',
      'Custom reporting',
    ],
    color: 'purple',
    current: false,
  },
];

const Profile: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [paymentLoading, setPaymentLoading] = useState<string>('');
  const [paymentSuccess, setPaymentSuccess] = useState<string>('');

  // Mock activity log
  const activityLog = [
    { action: 'Logged in', timestamp: '2024-01-15 09:30 AM', ip: '192.168.1.1' },
    { action: 'Exported data', timestamp: '2024-01-15 08:45 AM', ip: '192.168.1.1' },
    { action: 'Updated profile', timestamp: '2024-01-14 03:20 PM', ip: '192.168.1.1' },
    { action: 'Changed password', timestamp: '2024-01-10 11:15 AM', ip: '192.168.1.2' },
  ];

  useEffect(() => {
    const fetch = async () => {
      try {
        const resp = await apiService.getProfile();
        setData(resp || null);
      } catch (e) {
        setData(null);
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, []);

  const handleTestPayment = async (planId: string) => {
    setPaymentLoading(planId);
    setPaymentSuccess('');
    
    // Симуляция тестового платежа (без реального Stripe)
    setTimeout(() => {
      setPaymentLoading('');
      setPaymentSuccess(planId);
      
      // Сброс сообщения об успехе через 3 секунды
      setTimeout(() => {
        setPaymentSuccess('');
      }, 3000);
    }, 2000);
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin': return 'destructive';
      case 'premium': return 'default';
      case 'free': return 'secondary';
      default: return 'secondary';
    }
  };

  if (loading) {
    return (
      <div className="p-6 max-w-6xl mx-auto">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-6 max-w-6xl mx-auto">
        <Alert>
          <AlertDescription>
            Unable to load profile data. Please try refreshing the page.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      
      {/* Page Header */}
      <div className="flex items-center space-x-4">
        <Avatar className="h-16 w-16">
          <AvatarImage src="/placeholder.svg?height=64&width=64" />
          <AvatarFallback className="text-xl">
            {data.email?.substring(0, 2).toUpperCase() || 'JD'}
          </AvatarFallback>
        </Avatar>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{data.email || 'John Doe'}</h1>
          <p className="text-gray-600">{data.email || 'john.doe@example.com'}</p>
          <Badge variant={getRoleColor(data.role) as any} className="mt-1">
            {(data.role?.toUpperCase() || 'FREE') + ' Member'}
          </Badge>
        </div>
      </div>

      {/* Success Message */}
      {paymentSuccess && (
        <Alert className="border-green-200 bg-green-50">
          <Check className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            ✅ Test payment successful! Plan upgraded to {PRICING_PLANS.find(p => p.id === paymentSuccess)?.name}
          </AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="subscription">Subscription</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Personal Information</CardTitle>
              <CardDescription>Update your personal details and contact information</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">First Name</label>
                  <Input defaultValue="John" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Last Name</label>
                  <Input defaultValue="Doe" />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Email Address</label>
                <Input defaultValue={data.email || "john.doe@example.com"} type="email" />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Phone Number</label>
                <Input defaultValue="+1 (555) 123-4567" type="tel" />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Company</label>
                <Input defaultValue="Real Estate Pro LLC" />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Location</label>
                <Input defaultValue="Dubai, UAE" />
              </div>

              <Button className="bg-blue-500 hover:bg-blue-600">Save Changes</Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Profile Picture</CardTitle>
              <CardDescription>Update your profile picture</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-4">
                <Avatar className="h-20 w-20">
                  <AvatarImage src="/placeholder.svg?height=80&width=80" />
                  <AvatarFallback className="text-2xl">
                    {data.email?.substring(0, 2).toUpperCase() || 'JD'}
                  </AvatarFallback>
                </Avatar>
                <div className="space-y-2">
                  <Button variant="outline">Upload New Picture</Button>
                  <p className="text-xs text-gray-500">JPG, PNG or GIF. Max size 2MB.</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Subscription Tab */}
        <TabsContent value="subscription" className="space-y-6">
          {/* Current Plan */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-blue-500" />
                Current Plan
              </CardTitle>
              <CardDescription>Your subscription details</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="p-6 border rounded-lg bg-blue-50">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xl font-bold capitalize">{data.role || 'Premium'} Plan</h3>
                    <p className="text-gray-600">
                      {data.role === 'premium' ? '$299/month' : 'Free'} • Next billing: January 15, 2024
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge className="bg-green-100 text-green-700">Active</Badge>
                      {data.role === 'premium' && (
                        <Badge className="bg-blue-100 text-blue-700">Popular</Badge>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <Button variant="outline" className="mb-2">Manage Subscription</Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Available Plans */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="h-5 w-5 text-purple-500" />
                Available Plans & Test Payment
              </CardTitle>
              <CardDescription>
                Choose a plan that fits your needs. <strong>Test payment mode</strong> - no real charges.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {PRICING_PLANS.map((plan) => (
                  <div
                    key={plan.id}
                    className={`relative p-6 rounded-lg border-2 transition-all hover:shadow-md ${
                      plan.current 
                        ? 'border-blue-500 bg-blue-50' 
                        : 'border-gray-200'
                    }`}
                  >
                    {plan.popular && (
                      <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                        <Badge className="bg-orange-500 hover:bg-orange-600 text-white">
                          <Star className="h-3 w-3 mr-1" />
                          Popular
                        </Badge>
                      </div>
                    )}
                    
                    {plan.current && (
                      <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                        <Badge className="bg-green-500 hover:bg-green-600 text-white">
                          <Check className="h-3 w-3 mr-1" />
                          Current Plan
                        </Badge>
                      </div>
                    )}

                    <div className="text-center">
                      <h3 className="text-xl font-bold mb-2">{plan.name}</h3>
                      <div className="mb-4">
                        <span className="text-3xl font-bold">{plan.price === 0 ? 'Free' : `$${plan.price}`}</span>
                        {plan.price > 0 && <span className="text-gray-500">/{plan.period}</span>}
                      </div>
                      <p className="text-sm text-gray-600 mb-6">{plan.description}</p>
                    </div>

                    <ul className="space-y-2 mb-6">
                      {plan.features.slice(0, 4).map((feature, index) => (
                        <li key={index} className="flex items-start gap-2 text-sm">
                          <Check className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>

                    <div className="text-center">
                      {plan.current ? (
                        <Button variant="outline" className="w-full" disabled>
                          Current Plan
                        </Button>
                      ) : (
                        <Button
                          className="w-full"
                          variant={plan.color === 'blue' ? 'default' : 'outline'}
                          onClick={() => handleTestPayment(plan.id)}
                          disabled={paymentLoading === plan.id}
                        >
                          {paymentLoading === plan.id ? (
                            <>
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                              Processing...
                            </>
                          ) : (
                            `Test Upgrade - ${plan.price === 0 ? 'Free' : `$${plan.price}/${plan.period}`}`
                          )}
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Test Payment Notice */}
              <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex items-center gap-2 text-yellow-800">
                  <Shield className="h-4 w-4" />
                  <strong>Test Mode</strong>
                </div>
                <p className="text-sm text-yellow-700 mt-1">
                  All payments are simulated for testing purposes. No real charges will be made. 
                  Stripe integration is not connected in this demo version.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Password</CardTitle>
              <CardDescription>Change your account password</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Current Password</label>
                <Input type="password" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">New Password</label>
                <Input type="password" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Confirm New Password</label>
                <Input type="password" />
              </div>
              <Button className="bg-blue-500 hover:bg-blue-600">Update Password</Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Two-Factor Authentication</CardTitle>
              <CardDescription>Add an extra layer of security to your account</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-3">
                  <Shield className="h-5 w-5 text-green-500" />
                  <div>
                    <p className="font-medium">Authenticator App</p>
                    <p className="text-sm text-gray-500">Use an authenticator app to generate codes</p>
                  </div>
                </div>
                <Badge className="bg-green-100 text-green-700">Enabled</Badge>
              </div>
              <Button variant="outline">Disable 2FA</Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>API Keys</CardTitle>
              <CardDescription>Manage your API access keys</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-3">
                  <Key className="h-5 w-5 text-blue-500" />
                  <div>
                    <p className="font-medium">Production API Key</p>
                    <p className="text-sm text-gray-500">sk_live_****************************</p>
                  </div>
                </div>
                <Button variant="outline" size="sm">
                  Regenerate
                </Button>
              </div>
              <Button variant="outline">Create New API Key</Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Email Notifications</CardTitle>
              <CardDescription>Choose what email notifications you'd like to receive</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {[
                { title: 'Market Updates', description: 'Weekly market analysis and trends' },
                { title: 'Account Activity', description: 'Login alerts and security notifications' },
                { title: 'Billing', description: 'Payment confirmations and billing updates' },
                { title: 'Product Updates', description: 'New features and product announcements' },
              ].map((item) => (
                <div key={item.title} className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <p className="font-medium">{item.title}</p>
                    <p className="text-sm text-gray-500">{item.description}</p>
                  </div>
                  <Button variant="outline" size="sm">
                    Enabled
                  </Button>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Push Notifications</CardTitle>
              <CardDescription>Manage browser and mobile push notifications</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  Push notifications are currently disabled in your browser. Enable them to receive real-time updates.
                </AlertDescription>
              </Alert>
              <Button variant="outline">Enable Push Notifications</Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Activity Tab */}
        <TabsContent value="activity" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>Your recent account activity and login history</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {activityLog.map((activity, index) => (
                  <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <User className="h-4 w-4 text-blue-600" />
                      </div>
                      <div>
                        <p className="font-medium">{activity.action}</p>
                        <p className="text-sm text-gray-500">{activity.timestamp}</p>
                      </div>
                    </div>
                    <Badge variant="outline">{activity.ip}</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Account Statistics</CardTitle>
              <CardDescription>Your account usage and statistics</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">1,234</div>
                  <p className="text-sm text-gray-500">Properties Viewed</p>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-green-600">89</div>
                  <p className="text-sm text-gray-500">Reports Generated</p>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">156</div>
                  <p className="text-sm text-gray-500">API Calls This Month</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Profile;