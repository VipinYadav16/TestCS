import React, { useState, useEffect } from "react";
import { ethers } from "ethers";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/lib/utils";

// To fix the TypeScript error for window.ethereum, you can add this declaration.
// In a real project, this would go in a global declaration file (e.g., vite-env.d.ts)
declare global {
  interface Window {
    ethereum?: any;
  }
}

// Make sure to replace this with your actual contract ABI and address.
// You would get these after deploying your CryptoSentinelSubscription contract.
const contractABI = [
  "function subscribe() public payable",
  "function isSubscriptionActive(address _subscriber) public view returns (bool)",
  "function subscriptionFee() public view returns (uint256)",
];
const contractAddress = "YOUR_CONTRACT_ADDRESS_HERE"; 

const SubscribeButton: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [subscriptionFee, setSubscriptionFee] = useState("0");
  const { user, isAuthenticated } = useAuth();
  const { toast } = useToast();

  const connectToWallet = async () => {
    if (typeof window.ethereum === "undefined") {
      toast({
        title: "MetaMask not detected",
        description: "Please install MetaMask to use this feature.",
        variant: "destructive",
      });
      return null;
    }
    return new ethers.BrowserProvider(window.ethereum);
  };

  const getContract = async () => {
    const provider = await connectToWallet();
    if (!provider) return null;
    const signer = await provider.getSigner();
    return new ethers.Contract(contractAddress, contractABI, signer);
  };

  const checkSubscriptionStatus = async () => {
    if (!isAuthenticated || !user) return;
    try {
      const provider = await connectToWallet();
      if (!provider) return;
      const contract = new ethers.Contract(contractAddress, contractABI, provider);
      const active = await contract.isSubscriptionActive(user.id);
      setIsSubscribed(active);
    } catch (error) {
      console.error("Error checking subscription status:", error);
    }
  };

  const fetchSubscriptionFee = async () => {
    try {
      const provider = await connectToWallet();
      if (!provider) return;
      const contract = new ethers.Contract(contractAddress, contractABI, provider);
      const fee = await contract.subscriptionFee();
      setSubscriptionFee(ethers.formatEther(fee));
    } catch (error) {
      console.error("Error fetching subscription fee:", error);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      checkSubscriptionStatus();
      fetchSubscriptionFee();
    }
  }, [isAuthenticated, user]);

  const handleSubscribe = async () => {
    if (!isAuthenticated) {
      toast({
        title: "Please log in",
        description: "You must be logged in to subscribe.",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      const contract = await getContract();
      if (!contract) return;
      
      const fee = await contract.subscriptionFee();
      const tx = await contract.subscribe({ value: fee });
      await tx.wait();
      
      toast({
        title: "Subscription Successful!",
        description: "Your subscription has been activated on-chain.",
      });
      setIsSubscribed(true);
    } catch (error) {
      console.error("Subscription failed:", error);
      toast({
        title: "Subscription Failed",
        description: "Please check your wallet and try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button
      onClick={handleSubscribe}
      disabled={loading || isSubscribed}
      className={cn(
        "w-full transition-all",
        isSubscribed ? "bg-green-500 hover:bg-green-600" : ""
      )}
    >
      {loading ? (
        <>
          <div className="h-4 w-4 mr-2 rounded-full border-2 border-current border-r-transparent animate-spin" />
          Processing...
        </>
      ) : isSubscribed ? (
        "Subscribed!"
      ) : (
        `Subscribe for ${subscriptionFee} ETH`
      )}
    </Button>
  );
};

export default SubscribeButton;