import React, { useState, useEffect } from "react";
import {
  TrendingUp,
  Clock,
  AlertTriangle,
  Shield,
  ChevronDown,
  Filter,
  TrendingDown,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import Markdown from "react-markdown"; // Import the Markdown renderer
import { useTheme } from "@/hooks/use-theme";

// List of cryptocurrencies from main.ipynb
const CRYPTO_COINS = ["bitcoin", "ethereum", "ripple", "cardano", "solana"];

const Dashboard = () => {
  const [selectedStock, setSelectedStock] = useState("bitcoin");
  const [loading, setLoading] = useState(false);
  const [geminiAnalysis, setGeminiAnalysis] = useState("");
  const { toast } = useToast();
  const { theme } = useTheme();

  const fetchStockData = async (stockCode) => {
    if (!stockCode) return;
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:5000/api/analyze-crypto?stock_code=${stockCode}`
      );
      const data = await response.json();
      if (response.ok) {
        setGeminiAnalysis(data.gemini_analysis);
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      console.error("Error fetching data:", error);
      toast({
        title: "API Error",
        description: error.message,
        variant: "destructive",
      });
      setGeminiAnalysis("Failed to fetch analysis. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStockData(selectedStock);
  }, [selectedStock]);

  // Function to get the image path based on the selected stock
  const getImagePath = (stockName) => {
    // Capitalize the first letter for the image file name
    const capitalizedName = stockName.charAt(0).toUpperCase() + stockName.slice(1);
    // Construct the path to the image in the public folder
    return `/${capitalizedName}.jpg`;
  };

  return (
    <DashboardLayout>
      <div className="p-6">
        {/* Overview section */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold mb-1">
                CryptoSentinel Dashboard
              </h2>
              <p className="text-muted-foreground">
                Get on-chain insights on potential fraud activity
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Button size="sm" className="gap-2">
                <Filter className="h-4 w-4" />
                <span>Filters</span>
              </Button>
            </div>
          </div>

          {/* Main chart */}
          <div className="mb-8">
            <Tabs defaultValue="market" className="w-full">
              <div className="flex items-center justify-between mb-4">
                <TabsList className="bg-secondary">
                  <TabsTrigger value="market">Market Overview</TabsTrigger>
                </TabsList>

                <Select value={selectedStock} onValueChange={setSelectedStock}>
                  <SelectTrigger className="w-48 bg-secondary border-white/10">
                    <SelectValue placeholder="Select a token" />
                  </SelectTrigger>
                  <SelectContent>
                    {CRYPTO_COINS.map((coin) => (
                      <SelectItem key={coin} value={coin}>
                        {coin.charAt(0).toUpperCase() + coin.slice(1)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <TabsContent value="market" className="mt-0">
                <Card className="p-4">
                  <div className="relative">
                    {loading ? (
                      <div className="flex items-center justify-center h-[400px]">
                        <div className="h-8 w-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
                      </div>
                    ) : (
                      <img
                        src={getImagePath(selectedStock)}
                        alt={`${selectedStock} analysis`}
                        className="w-full h-auto"
                      />
                    )}
                  </div>
                </Card>
              </TabsContent>
              <TabsContent value="high-risk" className="mt-0">
                <Card className="p-4">
                  <div className="relative">
                    {loading ? (
                      <div className="flex items-center justify-center h-[400px]">
                        <div className="h-8 w-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
                      </div>
                    ) : (
                      <img
                        src={getImagePath(selectedStock)}
                        alt={`${selectedStock} analysis`}
                        className="w-full h-auto"
                      />
                    )}
                  </div>
                </Card>
              </TabsContent>
              <TabsContent value="watchlist" className="mt-0">
                <Card className="p-4">
                  <div className="relative">
                    {loading ? (
                      <div className="flex items-center justify-center h-[400px]">
                        <div className="h-8 w-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
                      </div>
                    ) : (
                      <img
                        src={getImagePath(selectedStock)}
                        alt={`${selectedStock} analysis`}
                        className="w-full h-auto"
                      />
                    )}
                  </div>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </div>
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>AI Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center p-8">
                <div className="h-8 w-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
              </div>
            ) : (
              <div
                style={{ wordWrap: "break-word", overflowWrap: "break-word" }}
              >
                <Markdown>{geminiAnalysis}</Markdown>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default Dashboard;