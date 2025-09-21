import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { RefreshCw, Database, Plus, Search } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface KnowledgeBaseProps {
  token: string;
}

interface RefreshResult {
  message: string;
  topic: string;
  document_count: number;
}

const KnowledgeBase: React.FC<KnowledgeBaseProps> = ({ token }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [refreshResults, setRefreshResults] = useState<RefreshResult[]>([]);
  const [sessionId] = useState(() => Math.random().toString(36).substr(2, 9));
  const { toast } = useToast();

  const handleRefreshKnowledgeBase = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    
    const formData = new FormData(e.currentTarget);
    const topic = formData.get('topic') as string;

    try {
      const response = await fetch('https://sceptre-genai-hack.onrender.com/refresh-knowledge-base', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          topic,
          session_id: sessionId,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setRefreshResults(prev => [data, ...prev]);
        toast({
          title: "Knowledge base updated",
          description: `Added ${data.document_count} documents for "${topic}".`,
        });
        // Clear the form
        (e.target as HTMLFormElement).reset();
      } else {
        throw new Error('Knowledge base refresh failed');
      }
    } catch (error) {
      toast({
        title: "Update failed",
        description: "Failed to update knowledge base. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Plus className="h-5 w-5 text-primary" />
              <span>Add New Topic</span>
            </CardTitle>
            <CardDescription>
              Refresh the knowledge base with information about a specific topic
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleRefreshKnowledgeBase} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="topic">Topic or Subject</Label>
                <Input
                  id="topic"
                  name="topic"
                  type="text"
                  placeholder="e.g., Climate change, COVID-19, Elections"
                  required
                />
              </div>
              <Button type="submit" variant="hero" disabled={isLoading} className="w-full">
                <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                {isLoading ? 'Updating...' : 'Update Knowledge Base'}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Database className="h-5 w-5 text-primary" />
              <span>Knowledge Base Status</span>
            </CardTitle>
            <CardDescription>
              Current status and information about the knowledge base
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-primary">
                  {refreshResults.length}
                </div>
                <div className="text-sm text-muted-foreground">
                  Topics Added
                </div>
              </div>
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-primary">
                  {refreshResults.reduce((sum, result) => sum + result.document_count, 0)}
                </div>
                <div className="text-sm text-muted-foreground">
                  Total Documents
                </div>
              </div>
            </div>
            
            <div className="text-sm text-muted-foreground">
              <p>The knowledge base helps SCEPTRE provide more accurate fact-checking by including up-to-date information on various topics.</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {refreshResults.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Search className="h-5 w-5 text-primary" />
              <span>Recent Updates</span>
            </CardTitle>
            <CardDescription>
              Recent knowledge base updates and their results
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {refreshResults.map((result, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div className="flex-1">
                    <h4 className="font-medium">{result.topic}</h4>
                    <p className="text-sm text-muted-foreground">{result.message}</p>
                  </div>
                  <Badge variant="outline" className="ml-4">
                    {result.document_count} docs
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="bg-muted/50">
        <CardHeader>
          <CardTitle className="text-lg">How Knowledge Base Works</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-muted-foreground">
          <p>
            <strong>Automatic Updates:</strong> When you add a topic, SCEPTRE searches for recent, credible information and adds it to the knowledge base.
          </p>
          <p>
            <strong>Fact-Checking Enhancement:</strong> Updated knowledge helps provide more accurate verification results and better source matching.
          </p>
          <p>
            <strong>Session-Based:</strong> Knowledge base updates are tied to your current session for personalized verification results.
          </p>
          <p>
            <strong>Quality Sources:</strong> Only information from reliable, fact-checked sources is added to maintain accuracy.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default KnowledgeBase;