import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { FileText, Link, Upload, AlertTriangle, CheckCircle, XCircle, Clock } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface VerificationInterfaceProps {
  token: string;
}

interface VerificationResult {
  status: string;
  summary: string;
  classification_score: number;
  classification_label: string;
  credibility_assessment: string;
  sources: Array<{ title: string; url: string; relevance_score: string }>;
  timestamp: string;
}

const VerificationInterface: React.FC<VerificationInterfaceProps> = ({ token }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [sessionId] = useState(() => Math.random().toString(36).substr(2, 9));
  const { toast } = useToast();

  const getRiskColor = (assessment: string) => {
    switch (assessment) {
      case 'HIGH_RISK':
        return 'risk-high';
      case 'MODERATE_RISK':
        return 'risk-moderate';
      case 'LOW_RISK':
        return 'risk-low';
      case 'UNVERIFIABLE':
      case 'LIMITED_VERIFICATION':
        return 'risk-unverifiable';
      default:
        return 'muted';
    }
  };

  const getRiskIcon = (assessment: string) => {
    switch (assessment) {
      case 'HIGH_RISK':
        return <XCircle className="h-5 w-5" />;
      case 'MODERATE_RISK':
        return <AlertTriangle className="h-5 w-5" />;
      case 'LOW_RISK':
        return <CheckCircle className="h-5 w-5" />;
      default:
        return <Clock className="h-5 w-5" />;
    }
  };

  const handleTextVerification = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    
    const formData = new FormData(e.currentTarget);
    const content = formData.get('content') as string;

    try {
      const response = await fetch('/verify', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          content,
          session_id: sessionId,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setResult(data);
        toast({
          title: "Verification complete",
          description: "Content analysis has been completed.",
        });
      } else {
        throw new Error('Verification failed');
      }
    } catch (error) {
      toast({
        title: "Verification failed",
        description: "Please try again later.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileVerification = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    
    const formData = new FormData(e.currentTarget);
    formData.append('session_id', sessionId);

    try {
      const response = await fetch('/verify', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setResult(data);
        toast({
          title: "Verification complete",
          description: "File analysis has been completed.",
        });
      } else {
        throw new Error('Verification failed');
      }
    } catch (error) {
      toast({
        title: "Verification failed",
        description: "Please try again with a different file.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleUrlVerification = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    
    const formData = new FormData(e.currentTarget);
    const url = formData.get('url') as string;

    try {
      const response = await fetch('/verify', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          url,
          session_id: sessionId,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setResult(data);
        toast({
          title: "Verification complete",
          description: "URL analysis has been completed.",
        });
      } else {
        throw new Error('Verification failed');
      }
    } catch (error) {
      toast({
        title: "Verification failed",
        description: "Please try again with a valid URL.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Tabs defaultValue="text" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="text" className="flex items-center space-x-2">
            <FileText className="h-4 w-4" />
            <span>Text</span>
          </TabsTrigger>
          <TabsTrigger value="file" className="flex items-center space-x-2">
            <Upload className="h-4 w-4" />
            <span>File</span>
          </TabsTrigger>
          <TabsTrigger value="url" className="flex items-center space-x-2">
            <Link className="h-4 w-4" />
            <span>URL</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="text" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Text Verification</CardTitle>
              <CardDescription>
                Paste text content to analyze for misinformation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleTextVerification} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="content">Content to verify</Label>
                  <Textarea
                    id="content"
                    name="content"
                    placeholder="Paste the text you want to verify here..."
                    className="min-h-[120px]"
                    required
                  />
                </div>
                <Button type="submit" variant="hero" disabled={isLoading} className="w-full">
                  {isLoading ? 'Analyzing...' : 'Verify Content'}
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="file" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>File Verification</CardTitle>
              <CardDescription>
                Upload images or videos for content analysis
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleFileVerification} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="file">Upload file</Label>
                  <Input
                    id="file"
                    name="file"
                    type="file"
                    accept="image/*,video/*"
                    required
                  />
                </div>
                <Button type="submit" variant="hero" disabled={isLoading} className="w-full">
                  {isLoading ? 'Processing...' : 'Analyze File'}
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="url" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>URL Verification</CardTitle>
              <CardDescription>
                Enter a URL to analyze the content for misinformation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleUrlVerification} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="url">URL to verify</Label>
                  <Input
                    id="url"
                    name="url"
                    type="url"
                    placeholder="https://example.com/article"
                    required
                  />
                </div>
                <Button type="submit" variant="hero" disabled={isLoading} className="w-full">
                  {isLoading ? 'Analyzing...' : 'Verify URL'}
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {result && (
        <Card className="shadow-card">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center space-x-2">
                {getRiskIcon(result.credibility_assessment)}
                <span>Verification Result</span>
              </CardTitle>
              <Badge 
                className={`bg-${getRiskColor(result.credibility_assessment)} text-white`}
              >
                {result.credibility_assessment.replace('_', ' ')}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <h4 className="font-semibold mb-2">Analysis Summary</h4>
              <p className="text-muted-foreground">{result.summary}</p>
            </div>

            <div>
              <h4 className="font-semibold mb-2">Classification Score</h4>
              <div className="space-y-2">
                <Progress value={result.classification_score * 100} />
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>Reliable</span>
                  <span>{(result.classification_score * 100).toFixed(1)}% Risk</span>
                  <span>High Risk</span>
                </div>
              </div>
            </div>

            {result.sources && result.sources.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2">Supporting Sources</h4>
                <div className="space-y-2">
                  {result.sources.map((source, index) => (
                    <div key={index} className="border rounded-lg p-3">
                      <div className="flex items-center justify-between">
                        <h5 className="font-medium text-sm">{source.title}</h5>
                        <Badge variant="outline">
                          {(parseFloat(source.relevance_score) * 100).toFixed(0)}%
                        </Badge>
                      </div>
                      <a 
                        href={source.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-primary text-sm hover:underline"
                      >
                        {source.url}
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="text-xs text-muted-foreground">
              Analysis completed at {new Date(result.timestamp).toLocaleString()}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default VerificationInterface;