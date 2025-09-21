import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Shield, CheckCircle, Zap, Users, Eye, Brain } from 'lucide-react';
import AuthForm from '@/components/AuthForm';
import heroImage from '@/assets/hero-sceptre.jpg';

interface LandingProps {
  onAuthSuccess: (token: string, user: any) => void;
}

const Landing: React.FC<LandingProps> = ({ onAuthSuccess }) => {
  const features = [
    {
      icon: <Brain className="h-6 w-6" />,
      title: "AI-Powered Analysis",
      description: "Advanced machine learning algorithms detect misinformation patterns and assess content credibility."
    },
    {
      icon: <Eye className="h-6 w-6" />,
      title: "Multi-Format Support",
      description: "Analyze text, images, videos, and URLs across different platforms and media types."
    },
    {
      icon: <CheckCircle className="h-6 w-6" />,
      title: "Real-Time Verification",
      description: "Get instant credibility assessments with detailed explanations and source verification."
    },
    {
      icon: <Zap className="h-6 w-6" />,
      title: "Smart Classification",
      description: "Sophisticated risk scoring system identifies potential misinformation with high accuracy."
    },
    {
      icon: <Users className="h-6 w-6" />,
      title: "Knowledge Base",
      description: "Continuously updated database of verified facts and reliable sources."
    },
    {
      icon: <Shield className="h-6 w-6" />,
      title: "Trusted Sources",
      description: "Cross-reference with authoritative sources and fact-checking organizations."
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-dark opacity-90"></div>
        <img 
          src={heroImage} 
          alt="SCEPTRE AI Shield" 
          className="absolute inset-0 w-full h-full object-cover"
        />
        
        <div className="relative z-10 container mx-auto px-4 py-20">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left side - Information */}
            <div className="text-white space-y-8">
              <div className="space-y-6">
                <div className="flex items-center space-x-3">
                  <Shield className="h-12 w-12 text-primary-glow" />
                  <h1 className="text-5xl font-bold">
                    SCEPTRE
                  </h1>
                </div>
                <p className="text-xl text-gray-200">
                  Smart Cognitive Engine for Preventing Tricks, Rumors & Errors
                </p>
                <p className="text-lg text-gray-300 leading-relaxed">
                  Combat misinformation with advanced AI technology. Our platform analyzes content 
                  across multiple formats, provides real-time credibility assessments, and helps you 
                  make informed decisions about the information you encounter.
                </p>
              </div>

              {/* Key Features */}
              <div className="grid md:grid-cols-2 gap-4">
                <div className="flex items-center space-x-3">
                  <CheckCircle className="h-5 w-5 text-primary-glow" />
                  <span>Real-time verification</span>
                </div>
                <div className="flex items-center space-x-3">
                  <CheckCircle className="h-5 w-5 text-primary-glow" />
                  <span>Multi-format analysis</span>
                </div>
                <div className="flex items-center space-x-3">
                  <CheckCircle className="h-5 w-5 text-primary-glow" />
                  <span>AI-powered detection</span>
                </div>
                <div className="flex items-center space-x-3">
                  <CheckCircle className="h-5 w-5 text-primary-glow" />
                  <span>Trusted sources</span>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-8 pt-8 border-t border-white/20">
                <div className="text-center">
                  <div className="text-3xl font-bold text-primary-glow">99.2%</div>
                  <div className="text-sm text-gray-300">Accuracy Rate</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-primary-glow">1M+</div>
                  <div className="text-sm text-gray-300">Content Analyzed</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-primary-glow">24/7</div>
                  <div className="text-sm text-gray-300">Monitoring</div>
                </div>
              </div>
            </div>

            {/* Right side - Authentication */}
            <div className="flex justify-center">
              <AuthForm onAuthSuccess={onAuthSuccess} />
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <section className="py-20 bg-muted/30">
        <div className="container mx-auto px-4">
          <div className="text-center space-y-4 mb-16">
            <h2 className="text-4xl font-bold">Why Choose SCEPTRE?</h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Our advanced AI technology provides comprehensive misinformation detection 
              and verification services to help you navigate today's information landscape.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="shadow-card hover:shadow-glow transition-all duration-300">
                <CardContent className="p-6 text-center space-y-4">
                  <div className="flex justify-center">
                    <div className="p-3 rounded-lg bg-primary/10 text-primary">
                      {feature.icon}
                    </div>
                  </div>
                  <h3 className="text-xl font-semibold">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center space-y-4 mb-16">
            <h2 className="text-4xl font-bold">How SCEPTRE Works</h2>
            <p className="text-xl text-muted-foreground">
              Three simple steps to verify content and fight misinformation
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-gradient-primary text-white flex items-center justify-center text-2xl font-bold mx-auto">
                1
              </div>
              <h3 className="text-xl font-semibold">Submit Content</h3>
              <p className="text-muted-foreground">
                Upload text, images, videos, or paste URLs of content you want to verify
              </p>
            </div>
            <div className="text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-gradient-primary text-white flex items-center justify-center text-2xl font-bold mx-auto">
                2
              </div>
              <h3 className="text-xl font-semibold">AI Analysis</h3>
              <p className="text-muted-foreground">
                Our AI analyzes the content, checks multiple sources, and assesses credibility
              </p>
            </div>
            <div className="text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-gradient-primary text-white flex items-center justify-center text-2xl font-bold mx-auto">
                3
              </div>
              <h3 className="text-xl font-semibold">Get Results</h3>
              <p className="text-muted-foreground">
                Receive detailed verification reports with risk assessments and supporting sources
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-card border-t py-12">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-8">
            <div className="md:col-span-2">
              <div className="flex items-center space-x-3 mb-4">
                <Shield className="h-8 w-8 text-primary" />
                <h3 className="text-2xl font-bold">SCEPTRE</h3>
              </div>
              <p className="text-muted-foreground mb-4">
                Fighting misinformation with advanced AI technology. 
                Protecting truth and promoting information literacy.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Features</h4>
              <ul className="space-y-2 text-muted-foreground">
                <li>Content Verification</li>
                <li>AI Analysis</li>
                <li>Real-time Detection</li>
                <li>Source Checking</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-muted-foreground">
                <li>About Us</li>
                <li>Privacy Policy</li>
                <li>Terms of Service</li>
                <li>Contact</li>
              </ul>
            </div>
          </div>
          <div className="border-t mt-8 pt-8 text-center text-muted-foreground">
            <p>&copy; 2024 SCEPTRE. All rights reserved. Protecting truth in the digital age.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;