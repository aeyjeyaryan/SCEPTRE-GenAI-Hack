import React, { useState, useEffect } from 'react';
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Landing from "./pages/Landing";
import Dashboard from "./components/Dashboard";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [token, setToken] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    try {
      // Check for existing authentication - using the same key as Landing component
      const savedAuth = localStorage.getItem('auth');
      
      console.log('Checking saved auth:', savedAuth); // Debug log
      
      if (savedAuth) {
        const { token: savedToken, user: savedUser } = JSON.parse(savedAuth);
        if (savedToken && savedUser) {
          setToken(savedToken);
          setUser(savedUser);
          setIsAuthenticated(true);
          console.log('Restored auth from localStorage:', { savedToken, savedUser });
        }
      }
    } catch (error) {
      console.error('Error loading saved auth:', error);
      localStorage.removeItem('auth');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleAuthSuccess = (authToken: string, userData: any) => {
    try {
      // Save using the same format as Landing component
      localStorage.setItem('auth', JSON.stringify({ token: authToken, user: userData }));
      setToken(authToken);
      setUser(userData);
      setIsAuthenticated(true);
      console.log('Auth success:', { authToken, userData }); // Debug log
    } catch (error) {
      console.error('Error saving auth data:', error);
    }
  };

  const handleLogout = () => {
    try {
      localStorage.removeItem('auth');
      setToken('');
      setUser(null);
      setIsAuthenticated(false);
      console.log('Logged out successfully'); // Debug log
    } catch (error) {
      console.error('Error during logout:', error);
    }
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-lg text-muted-foreground">Loading SCEPTRE...</p>
        </div>
      </div>
    );
  }

  console.log('App render state:', { isAuthenticated, user: !!user, token: !!token }); // Debug log

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <div className="min-h-screen">
          <BrowserRouter>
            <Routes>
              <Route 
                path="/" 
                element={
                  isAuthenticated ? (
                    <Dashboard user={user} token={token} onLogout={handleLogout} />
                  ) : (
                    <Landing onAuthSuccess={handleAuthSuccess} />
                  )
                } 
              />
              {/* Add other routes here if needed */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </div>
        <Toaster />
        <Sonner />
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;