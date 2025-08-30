@. // SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

// A simple smart contract for managing subscriptions to a service.
contract CryptoSentinelSubscription is Ownable {

    // --- State Variables ---

    // The subscription fee in Wei (the smallest denomination of Ether).
    // The owner can update this.
    uint256 public subscriptionFee;

    // The duration of a subscription in seconds.
    // A one-month duration is approximately 30 days.
    uint256 public constant SUBSCRIPTION_DURATION = 30 days;

    // Mapping to store the expiry timestamp for each subscriber.
    // The key is the user's address, and the value is the Unix timestamp when their subscription expires.
    mapping(address => uint256) public subscriptionExpiry;

    // --- Events ---

    // Emitted when a user successfully subscribes or renews their subscription.
    event SubscriptionRenewed(address indexed subscriber, uint256 expiryTimestamp);

    // Emitted when the owner updates the subscription fee.
    event SubscriptionFeeUpdated(uint256 newFee);

    // Emitted when the owner withdraws funds from the contract.
    event FundsWithdrawn(uint256 amount);

    // --- Constructor ---

    // The constructor is called once when the contract is deployed.
    // It sets the deployer as the owner and initializes the subscription fee.
    constructor(uint256 _initialSubscriptionFee) Ownable(msg.sender) {
        require(_initialSubscriptionFee > 0, "Fee must be greater than zero");
        subscriptionFee = _initialSubscriptionFee;
    }

    // --- Public Functions ---

    // Allows a user to subscribe or renew their subscription.
    // They must send the correct subscription fee with the transaction.
    function subscribe() public payable {
        // Checks: Ensure the correct amount of Ether is sent.
        require(msg.value == subscriptionFee, "Incorrect subscription fee sent");

        // Effects: Update the state of the contract.
        uint256 newExpiry = block.timestamp + SUBSCRIPTION_DURATION;
        // If the user already has an active subscription, extend it from the current expiry date.
        // Otherwise, start from now.
        if (subscriptionExpiry[msg.sender] > block.timestamp) {
            newExpiry = subscriptionExpiry[msg.sender] + SUBSCRIPTION_DURATION;
        }
        subscriptionExpiry[msg.sender] = newExpiry;

        // Interactions: No external calls here to prevent reentrancy attacks.
        
        // Emit an event to notify off-chain systems (like your web app).
        emit SubscriptionRenewed(msg.sender, newExpiry);
    }

    // A view function to check if a user has an active subscription.
    function isSubscriptionActive(address _subscriber) public view returns (bool) {
        return subscriptionExpiry[_subscriber] > block.timestamp;
    }

    // --- Owner-only Functions ---

    // Allows the owner to update the subscription fee.
    function updateSubscriptionFee(uint256 _newFee) public onlyOwner {
        require(_newFee > 0, "Fee must be greater than zero");
        subscriptionFee = _newFee;
        emit SubscriptionFeeUpdated(_newFee);
    }

    // Allows the owner to withdraw all accumulated funds.
    function withdrawFunds() public onlyOwner {
        // Checks: Ensure there is a balance to withdraw.
        uint256 balance = address(this).balance;
        require(balance > 0, "No funds to withdraw");
        
        // Effects: Reset the contract balance to zero implicitly.
        
        // Interactions: Transfer the funds to the owner.
        // Use a low-level call to prevent reentrancy attacks.
        (bool success, ) = payable(owner()).call{value: balance}("");
        require(success, "Failed to withdraw funds");
        
        // Emit an event to record the withdrawal.
        emit FundsWithdrawn(balance);
    }
}