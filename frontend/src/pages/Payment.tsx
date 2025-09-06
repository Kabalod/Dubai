import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { CreditCard, Calendar, DollarSign, Download, Search, Check, Star, Zap, AlertCircle } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext'; // ✅ ДОБАВЛЕН ИМПОРТ
import { StripeCheckout } from '@/components/payment/StripeCheckout';

// Payment Plans Configuration
const PAYMENT_PLANS = [
    {
        id: 'free',
        name: 'Free',
        price: 0,
    period: 'forever',
    description: 'Perfect for getting started with basic analytics',
        features: [
      'Up to 100 property views per month',
      'Basic market analytics',
      'Standard support',
      'Export to PDF'
        ],
        limitations: [
      'Advanced analytics',
      'API access', 
      'Custom reports',
      'Priority support'
    ],
        popular: false,
    current: false,
    },
    {
        id: 'premium',
        name: 'Premium',
        price: 299,
        period: 'month',
    description: 'Advanced features for real estate professionals',
        features: [
      'Unlimited property views',
      'Advanced market analytics',
      'Real-time data updates',
      'API access',
      'Custom reports',
      'Priority support',
      'Export to multiple formats',
      'Team collaboration (up to 5 users)',
        ],
        limitations: [],
        popular: true,
    current: true,
    },
    {
        id: 'enterprise',
        name: 'Enterprise',
        price: 999,
        period: 'month',
    description: 'Complete solution for large organizations',
        features: [
            'Everything in Premium',
      'Unlimited team members',
            'Custom integrations',
            'Dedicated account manager',
      'SLA guarantee',
      'Custom branding',
      'Advanced security features',
      'On-premise deployment option',
        ],
        limitations: [],
        popular: false,
    current: false,
  },
];

const ADD_ONS = [
  {
    name: 'Additional API Calls',
    price: '0.01',
    unit: 'per call',
    description: 'Extra API calls beyond your plan limit',
  },
  {
    name: 'Data Export Credits',
    price: '49',
    unit: 'per 1000 exports',
    description: 'Additional data export capabilities',
  },
  {
    name: 'Custom Analytics',
    price: '199',
    unit: 'per month',
    description: 'Tailored analytics dashboard',
  },
];

const MOCK_TRANSACTIONS = [
  {
    id: 'TXN-001',
    date: '2024-01-15',
    description: 'Premium Plan Subscription',
    amount: '299.00',
    status: 'Completed',
    method: 'Visa ****4242',
  },
  {
    id: 'TXN-002',
    date: '2024-01-01',
    description: 'Analytics Add-on',
    amount: '99.00',
    status: 'Completed',
    method: 'Visa ****4242',
  },
  {
    id: 'TXN-003',
    date: '2023-12-15',
    description: 'Premium Plan Subscription',
    amount: '299.00',
    status: 'Completed',
    method: 'Visa ****4242',
  },
  {
    id: 'TXN-004',
    date: '2023-12-01',
    description: 'Data Export Credits',
    amount: '49.00',
    status: 'Failed',
    method: 'Visa ****4242',
  },
];

const Payment: React.FC = () => {
  const { user } = useAuth(); // ✅ ДОБАВЛЕНА ДЕСТРУКТУРИЗАЦИЯ user
  const [testPaymentLoading, setTestPaymentLoading] = useState<string>('');
  const [testPaymentSuccess, setTestPaymentSuccess] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedPlan, setSelectedPlan] = useState<any>(null);
  const [showStripeCheckout, setShowStripeCheckout] = useState(false);
  const [paymentError, setPaymentError] = useState<string>('');

  const handlePlanSelect = (plan: any) => {
    setSelectedPlan(plan);
    setShowStripeCheckout(true);
    setPaymentError('');
  };

  const handleStripeSuccess = (paymentIntent: any) => {
    console.log('Payment successful:', paymentIntent);
    setShowStripeCheckout(false);
    setTestPaymentSuccess(selectedPlan?.id || '');
    setSelectedPlan(null);

    // Сброс сообщения через 5 секунд
    setTimeout(() => {
      setTestPaymentSuccess('');
    }, 5000);
  };

  const handleStripeError = (error: string) => {
    console.error('Payment error:', error);
    setPaymentError(error);
    setShowStripeCheckout(false);
  };

  const handleTestPayment = async (planId: string) => {
    setTestPaymentLoading(planId);
    setTestPaymentSuccess('');

    // Для демонстрации оставляем старую симуляцию
    // В продакшене здесь будет реальный Stripe платеж
    setTimeout(() => {
      setTestPaymentLoading('');
      setTestPaymentSuccess(planId);

      // Сброс сообщения через 3 секунды
      setTimeout(() => {
        setTestPaymentSuccess('');
      }, 3000);
    }, 2000);
  };

  const filteredTransactions = MOCK_TRANSACTIONS.filter(transaction =>
    transaction.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    transaction.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Payments & Billing</h1>
          <p className="text-gray-600 mt-1">Manage your subscription, billing, and payment history</p>
        </div>
        <Button className="bg-blue-500 hover:bg-blue-600">
          <Download className="mr-2 h-4 w-4" />
          Export
        </Button>
      </div>

      {/* Success Message */}
      {testPaymentSuccess && (
        <Alert className="border-green-200 bg-green-50">
          <Check className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            ✅ Payment successful! Upgraded to {PAYMENT_PLANS.find(p => p.id === testPaymentSuccess)?.name} plan
          </AlertDescription>
        </Alert>
      )}

      {/* Payment Error Message */}
      {paymentError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Payment failed: {paymentError}
          </AlertDescription>
        </Alert>
      )}

      {/* Stripe Checkout Modal */}
      {showStripeCheckout && selectedPlan && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Complete Payment</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowStripeCheckout(false)}
              >
                ×
              </Button>
            </div>
            <StripeCheckout
              amount={selectedPlan.price}
              currency="usd"
              planName={selectedPlan.name}
              onSuccess={handleStripeSuccess}
              onError={handleStripeError}
            />
          </div>
        </div>
      )}

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="plans">Plans & Pricing</TabsTrigger>
          <TabsTrigger value="transactions">Transactions</TabsTrigger>
          <TabsTrigger value="methods">Payment Methods</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Payment Overview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Current Balance</CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">$1,234.56</div>
                <p className="text-xs text-muted-foreground">Available credits</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">This Month</CardTitle>
                <Calendar className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">$398.00</div>
                <p className="text-xs text-muted-foreground">Total spent</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Payment Method</CardTitle>
                <CreditCard className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">Visa ****4242</div>
                <p className="text-xs text-muted-foreground">Expires 12/25</p>
              </CardContent>
            </Card>
          </div>

          {/* Current Plan */}
          <Card>
            <CardHeader>
              <CardTitle>Current Plan</CardTitle>
              <CardDescription>You are currently on the Premium plan</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between p-6 border rounded-lg bg-blue-50">
                <div>
                  <h3 className="text-xl font-bold">Premium Plan</h3>
                  <p className="text-gray-600">$299/month • Next billing: January 15, 2024</p>
                  <div className="flex items-center gap-2 mt-2">
                    <Badge className="bg-green-100 text-green-700">Active</Badge>
                    <Badge className="bg-blue-100 text-blue-700">Most Popular</Badge>
                  </div>
                </div>
                <div className="text-right">
                  <Button variant="outline" className="mb-2">Manage Plan</Button>
                  <br />
                  <Button variant="ghost" className="text-red-500">Cancel Subscription</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Plans & Pricing Tab */}
        <TabsContent value="plans" className="space-y-6">
          {/* Payment Notice */}
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center gap-2 text-blue-800">
              <CreditCard className="h-4 w-4" />
              <strong>Secure Payment</strong>
            </div>
            <p className="text-sm text-blue-700 mt-1">
              All payments are processed securely through Stripe. Use test card: 4242 4242 4242 4242
            </p>
          </div>

          {/* Pricing Plans */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {PAYMENT_PLANS.map((plan) => (
              <Card key={plan.name} className={`relative ${plan.popular ? 'ring-2 ring-blue-500 shadow-lg' : ''}`}>
            {plan.popular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <Badge className="bg-blue-500 text-white px-4 py-1">
                      <Star className="w-3 h-3 mr-1" />
                      Most Popular
                    </Badge>
                </div>
            )}
                {plan.current && (
                  <div className="absolute top-4 right-4">
                    <Badge className="bg-green-100 text-green-700">Current Plan</Badge>
                  </div>
                )}

                <CardHeader className="text-center pb-8">
                  <CardTitle className="text-2xl font-bold">{plan.name}</CardTitle>
                  <div className="mt-4">
                    <span className="text-4xl font-bold">${plan.price}</span>
                    <span className="text-gray-500">/{plan.period}</span>
                </div>
                  <CardDescription className="mt-2">{plan.description}</CardDescription>
            </CardHeader>

            <CardContent className="space-y-6">
                  <div className="space-y-3">
                    {plan.features.map((feature) => (
                      <div key={feature} className="flex items-center space-x-3">
                        <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
                                <span className="text-sm">{feature}</span>
                      </div>
                    ))}
                    {plan.limitations.map((limitation) => (
                      <div key={limitation} className="flex items-center space-x-3">
                        <span className="h-4 w-4 text-gray-400 flex-shrink-0">✕</span>
                        <span className="text-sm text-gray-500">{limitation}</span>
                      </div>
                    ))}
                </div>

                  <Button
                    className={`w-full ${plan.popular ? 'bg-blue-500 hover:bg-blue-600' : ''}`}
                    variant={plan.current ? 'outline' : plan.popular ? 'default' : 'outline'}
                    disabled={plan.current || testPaymentLoading === plan.id}
                    onClick={() => plan.name === 'Free' ? handleTestPayment(plan.id) : handlePlanSelect(plan)}
                  >
                    {testPaymentLoading === plan.id ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Processing...
                      </>
                    ) : plan.current ? (
                      'Current Plan'
                    ) : plan.name === 'Free' ? (
                      'Get Started'
                    ) : (
                      'Upgrade Now'
                    )}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Add-ons Section */}
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900">Add-ons</h2>
              <p className="text-gray-600 mt-2">Enhance your plan with additional features</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {ADD_ONS.map((addon) => (
                <Card key={addon.name}>
                  <CardHeader>
                    <div className="flex items-center space-x-2">
                      <Zap className="h-5 w-5 text-blue-500" />
                      <CardTitle className="text-lg">{addon.name}</CardTitle>
                    </div>
                    <div className="mt-2">
                      <span className="text-2xl font-bold">${addon.price}</span>
                      <span className="text-gray-500 text-sm"> {addon.unit}</span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600 mb-4">{addon.description}</p>
                    <Button variant="outline" className="w-full bg-transparent">
                      Add to Plan
                </Button>
            </CardContent>
        </Card>
              ))}
                        </div>
                </div>
        </TabsContent>

        {/* Transactions Tab */}
        <TabsContent value="transactions" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Transaction History</CardTitle>
                  <CardDescription>Your recent payment transactions</CardDescription>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                    <Input 
                      placeholder="Search transactions..." 
                      className="pl-10 w-64"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                  </div>
                </div>
              </div>
                            </CardHeader>
                            <CardContent>
              <div className="space-y-4">
                {filteredTransactions.map((transaction) => (
                  <div key={transaction.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                        <DollarSign className="h-5 w-5 text-blue-600" />
                      </div>
                      <div>
                        <p className="font-medium">{transaction.description}</p>
                        <p className="text-sm text-gray-500">
                          {transaction.date} • {transaction.method}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <p className="font-medium">${transaction.amount}</p>
                        <Badge
                          variant={transaction.status === "Completed" ? "default" : "destructive"}
                          className={transaction.status === "Completed" ? "bg-green-100 text-green-700" : ""}
                        >
                          {transaction.status}
                        </Badge>
                      </div>
                      <Button variant="ghost" size="sm">
                        <Download className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
                            </CardContent>
                        </Card>
        </TabsContent>
                        
        {/* Payment Methods Tab */}
        <TabsContent value="methods" className="space-y-6">
                        <Card>
                            <CardHeader>
              <CardTitle>Payment Methods</CardTitle>
              <CardDescription>Manage your payment methods and billing information</CardDescription>
                            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  <CreditCard className="h-8 w-8 text-blue-500" />
                  <div>
                    <p className="font-medium">Visa ending in 4242</p>
                    <p className="text-sm text-gray-500">Expires 12/25</p>
                  </div>
                  <Badge className="bg-green-100 text-green-700">Primary</Badge>
                </div>
                <Button variant="outline" size="sm">
                  Edit
                </Button>
              </div>
              <Button variant="outline" className="w-full bg-transparent">
                <CreditCard className="mr-2 h-4 w-4" />
                Add Payment Method
              </Button>
                            </CardContent>
                        </Card>
                        
          {/* Billing Information */}
                        <Card>
                            <CardHeader>
              <CardTitle>Billing Information</CardTitle>
              <CardDescription>Update your billing address and contact information</CardDescription>
                            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Company Name</label>
                  <Input defaultValue="Real Estate Pro LLC" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Email</label>
                                      <Input defaultValue={user?.email || ""} />
                    </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Address</label>
                  <Input defaultValue="123 Business St" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">City</label>
                  <Input defaultValue="Dubai" />
                </div>
            </div>
              <Button className="bg-blue-500 hover:bg-blue-600">
                Update Billing Info
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
        </div>
    );
};

export default Payment;