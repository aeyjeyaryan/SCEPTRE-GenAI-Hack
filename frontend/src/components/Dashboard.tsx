import React from 'react';
import { Button } from '@/components/ui/button';
import { Shield, LogOut } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import VerificationInterface from './VerificationInterface';

interface DashboardProps {
  user: any;
  token: string;
  onLogout: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({ user, token, onLogout }) => {
  const { toast } = useToast();

  const handleLogout = () => {
    localStorage.removeItem('sceptre_token');
    localStorage.removeItem('sceptre_user');
    onLogout();
    toast({
      title: "Logged out",
      description: "You have been successfully logged out.",
    });
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card shadow-sm">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Shield className="h-8 w-8 text-primary" />
            <div>
              <h1 className="text-2xl font-bold bg-gradient-cyber bg-clip-text text-transparent">
                SCEPTRE
              </h1>
              <p className="text-sm text-muted-foreground">
                Smart Cognitive Engine for Preventing Tricks, Rumors & Errors
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <span className="text-sm text-muted-foreground">
              Welcome, {user?.full_name || user?.email}
            </span>
            <Button variant="outline" size="sm" onClick={handleLogout}>
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="space-y-6">
          <div className="text-center space-y-4">
            <h2 className="text-3xl font-bold">Content Verification</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Upload text, files, or URLs to analyze content for misinformation, 
              get credibility assessments, and receive detailed verification reports.
            </p>
          </div>
          <VerificationInterface token={token} />
        </div>
      </main>
    </div>
  );
};

export default Dashboard;