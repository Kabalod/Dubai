import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Check, X, Star, Zap, CreditCard } from 'lucide-react';

const PricingPage: React.FC = () => {
  const plans = [
    {
      name: "Free",
      price: "0",
      period: "forever",
      description: "Perfect for getting started with basic analytics",
      features: [
        "Up to 100 property views per month",
        "Basic market analytics",
        "Standard support",
        "Export to PDF"
      ],
      limitations: [
        "Advanced analytics",
        "API access",
        "Custom reports", 
        "Priority support"
      ],
      popular: false,
      current: false,
    },
    {
      name: "Premium",
      price: "299",
      period: "month",
      description: "Advanced features for real estate professionals",
      features: [
        "Unlimited property views",
        "Advanced market analytics", 
        "Real-time data updates",
        "API access",
        "Custom reports",
        "Priority support",
        "Export to multiple formats",
        "Team collaboration (up to 5 users)",
      ],
      limitations: [],
      popular: true,
      current: true,
    },
    {
      name: "Enterprise", 
      price: "999",
      period: "month",
      description: "Complete solution for large organizations",
      features: [
        "Everything in Premium",
        "Unlimited team members", 
        "Custom integrations",
        "Dedicated account manager",
        "SLA guarantee",
        "Custom branding",
        "Advanced security features",
        "On-premise deployment option",
      ],
      limitations: [],
      popular: false,
      current: false,
    },
  ];

  const addOns = [
    {
      name: "Additional API Calls",
      price: "0.01", 
      unit: "per call",
      description: "Extra API calls beyond your plan limit",
    },
    {
      name: "Data Export Credits",
      price: "49",
      unit: "per 1000 exports", 
      description: "Additional data export capabilities",
    },
    {
      name: "Custom Analytics",
      price: "199",
      unit: "per month",
      description: "Tailored analytics dashboard",
    },
  ];

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8">
      {/* Page Header */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-gray-900">Choose Your Plan</h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Select the perfect plan for your real estate analytics needs
        </p>
      </div>

      {/* Pricing Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {plans.map((plan) => (
          <Card 
            key={plan.name} 
            className={`relative rounded-lg ${
              plan.popular ? "ring-2 ring-blue-500 shadow-lg" : ""
            }`}
          >
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
                    <X className="h-4 w-4 text-gray-400 flex-shrink-0" />
                    <span className="text-sm text-gray-500">{limitation}</span>
                  </div>
                ))}
              </div>

              <Button
                className={`w-full rounded-full ${
                  plan.popular ? "bg-blue-500 hover:bg-blue-600" : ""
                }`}
                variant={plan.current ? "outline" : plan.popular ? "default" : "outline"}
                disabled={plan.current}
              >
                {plan.current ? "Current Plan" : plan.name === "Free" ? "Get Started" : "Upgrade Now"}
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
          {addOns.map((addon) => (
            <Card key={addon.name} className="rounded-lg">
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
                <Button 
                  variant="outline" 
                  className="w-full bg-transparent rounded-full"
                >
                  Add to Plan
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* FAQ Section */}
      <Card className="rounded-lg">
        <CardHeader>
          <CardTitle className="text-center">Frequently Asked Questions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold mb-2">Can I change my plan anytime?</h3>
              <p className="text-sm text-gray-600">
                Yes, you can upgrade or downgrade your plan at any time. Changes will be reflected in your next billing cycle.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">What payment methods do you accept?</h3>
              <p className="text-sm text-gray-600">
                We accept all major credit cards, PayPal, and bank transfers for Enterprise plans.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Is there a free trial?</h3>
              <p className="text-sm text-gray-600">
                Yes, all paid plans come with a 14-day free trial. No credit card required.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Do you offer refunds?</h3>
              <p className="text-sm text-gray-600">
                We offer a 30-day money-back guarantee for all paid plans.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PricingPage;
