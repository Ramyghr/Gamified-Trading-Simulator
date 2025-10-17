"""
Trading API Usage Examples
Complete examples for integrating with the trading engine API
"""

import requests
from typing import Dict, Optional
from decimal import Decimal
import json


class TradingAPIClient:
    """Client for interacting with the trading API"""
    
    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
    
    def place_market_order(
        self, 
        symbol: str, 
        side: str, 
        quantity: float,
        idempotency_key: Optional[str] = None
    ) -> Dict:
        """
        Place a market order (executes immediately)
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            side: 'BUY' or 'SELL'
            quantity: Number of shares
            idempotency_key: Optional unique key to prevent duplicates
        
        Returns:
            Order response dict
        """
        data = {
            'symbol': symbol.upper(),
            'order_type': 'MARKET',
            'side': side.upper(),
            'quantity': quantity
        }
        
        if idempotency_key:
            data['idempotency_key'] = idempotency_key
        
        response = requests.post(
            f'{self.base_url}/api/orders',
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        limit_price: float,
        time_in_force: str = 'GTC',
        idempotency_key: Optional[str] = None
    ) -> Dict:
        """
        Place a limit order (executes when price condition is met)
        
        Args:
            symbol: Stock symbol
            side: 'BUY' or 'SELL'
            quantity: Number of shares
            limit_price: Target price for execution
            time_in_force: 'GTC', 'IOC', 'FOK', or 'DAY'
            idempotency_key: Optional unique key
        
        Returns:
            Order response dict
        """
        data = {
            'symbol': symbol.upper(),
            'order_type': 'LIMIT',
            'side': side.upper(),
            'quantity': quantity,
            'price': limit_price,
            'time_in_force': time_in_force
        }
        
        if idempotency_key:
            data['idempotency_key'] = idempotency_key
        
        response = requests.post(
            f'{self.base_url}/api/orders',
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def place_stop_loss(
        self,
        symbol: str,
        quantity: float,
        stop_price: float,
        idempotency_key: Optional[str] = None
    ) -> Dict:
        """
        Place a stop loss order (sells when price drops to stop_price)
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares to sell
            stop_price: Price that triggers the sell
            idempotency_key: Optional unique key
        
        Returns:
            Order response dict
        """
        data = {
            'symbol': symbol.upper(),
            'order_type': 'STOP',
            'side': 'SELL',
            'quantity': quantity,
            'stop_price': stop_price
        }
        
        if idempotency_key:
            data['idempotency_key'] = idempotency_key
        
        response = requests.post(
            f'{self.base_url}/api/orders',
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def place_stop_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        stop_price: float,
        limit_price: float,
        idempotency_key: Optional[str] = None
    ) -> Dict:
        """
        Place a stop-limit order (triggers at stop, executes at limit)
        
        Args:
            symbol: Stock symbol
            side: 'BUY' or 'SELL'
            quantity: Number of shares
            stop_price: Price that triggers the order
            limit_price: Execution price after trigger
            idempotency_key: Optional unique key
        
        Returns:
            Order response dict
        """
        data = {
            'symbol': symbol.upper(),
            'order_type': 'STOP_LIMIT',
            'side': side.upper(),
            'quantity': quantity,
            'stop_price': stop_price,
            'price': limit_price
        }
        
        if idempotency_key:
            data['idempotency_key'] = idempotency_key
        
        response = requests.post(
            f'{self.base_url}/api/orders',
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def place_take_profit(
        self,
        symbol: str,
        quantity: float,
        target_price: float,
        idempotency_key: Optional[str] = None
    ) -> Dict:
        """
        Place a take profit order (sells when price reaches target)
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares to sell
            target_price: Price to sell at
            idempotency_key: Optional unique key
        
        Returns:
            Order response dict
        """
        data = {
            'symbol': symbol.upper(),
            'order_type': 'TAKE_PROFIT',
            'side': 'SELL',
            'quantity': quantity,
            'price': target_price
        }
        
        if idempotency_key:
            data['idempotency_key'] = idempotency_key
        
        response = requests.post(
            f'{self.base_url}/api/orders',
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def get_orders(
        self,
        status: Optional[str] = None,
        symbol: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> list:
        """
        Get user's orders with optional filters
        
        Args:
            status: Filter by status (PENDING, FILLED, CANCELED, etc.)
            symbol: Filter by symbol
            limit: Number of orders to return (max 500)
            offset: Number of orders to skip
        
        Returns:
            List of orders
        """
        params = {'limit': limit, 'offset': offset}
        
        if status:
            params['status'] = status
        if symbol:
            params['symbol'] = symbol.upper()
        
        response = requests.get(
            f'{self.base_url}/api/orders',
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def get_pending_orders(self, symbol: Optional[str] = None) -> list:
        """
        Get all pending and partially filled orders
        
        Args:
            symbol: Optional symbol filter
        
        Returns:
            List of pending orders
        """
        params = {}
        if symbol:
            params['symbol'] = symbol.upper()
        
        response = requests.get(
            f'{self.base_url}/api/orders/pending',
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def get_order(self, order_id: int) -> Dict:
        """
        Get specific order by ID
        
        Args:
            order_id: Order ID
        
        Returns:
            Order details
        """
        response = requests.get(
            f'{self.base_url}/api/orders/{order_id}',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def cancel_order(self, order_id: int) -> Dict:
        """
        Cancel a pending or partially filled order
        
        Args:
            order_id: Order ID to cancel
        
        Returns:
            Canceled order details
        """
        response = requests.delete(
            f'{self.base_url}/api/orders/{order_id}',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_order_transactions(self, order_id: int) -> list:
        """
        Get all fills/transactions for an order
        
        Args:
            order_id: Order ID
        
        Returns:
            List of transactions
        """
        response = requests.get(
            f'{self.base_url}/api/orders/{order_id}/transactions',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_transaction_history(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50
    ) -> list:
        """
        Get transaction history with optional filters
        
        Args:
            symbol: Filter by symbol
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            limit: Number of transactions to return
        
        Returns:
            List of transactions
        """
        params = {'limit': limit}
        
        if symbol:
            params['symbol'] = symbol.upper()
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        response = requests.get(
            f'{self.base_url}/api/orders/history/transactions',
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def validate_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = 'MARKET',
        price: Optional[float] = None
    ) -> Dict:
        """
        Validate order without placing it (dry run)
        
        Args:
            symbol: Stock symbol
            side: 'BUY' or 'SELL'
            quantity: Number of shares
            order_type: Order type
            price: Price (if applicable)
        
        Returns:
            Validation result with estimated costs
        """
        data = {
            'symbol': symbol.upper(),
            'order_type': order_type,
            'side': side.upper(),
            'quantity': quantity
        }
        
        if price:
            data['price'] = price
        
        response = requests.post(
            f'{self.base_url}/api/orders/validate',
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()


# ============================================
# Usage Examples
# ============================================

def example_basic_trading():
    """Example: Basic buy and sell"""
    
    # Initialize client
    client = TradingAPIClient(
        base_url='http://localhost:8000',
        auth_token='your_jwt_token_here'
    )
    
    # 1. Buy 10 shares of AAPL at market price
    print("Placing market BUY order...")
    order = client.place_market_order(
        symbol='AAPL',
        side='BUY',
        quantity=10,
        idempotency_key='unique_key_123'
    )
    print(f"Order placed: {order['id']}")
    print(f"Status: {order['status']}")
    print(f"Filled: {order['filled_quantity']}/{order['quantity']}")
    print(f"Price: ${order['average_fill_price']}")
    
    # 2. Sell 5 shares of AAPL at market price
    print("\nPlacing market SELL order...")
    sell_order = client.place_market_order(
        symbol='AAPL',
        side='SELL',
        quantity=5
    )
    print(f"Sold {sell_order['filled_quantity']} shares")


def example_limit_orders():
    """Example: Limit orders"""
    
    client = TradingAPIClient('http://localhost:8000', 'your_token')
    
    # Place limit buy order at $150
    print("Placing limit BUY order at $150...")
    order = client.place_limit_order(
        symbol='AAPL',
        side='BUY',
        quantity=10,
        limit_price=150.00
    )
    print(f"Limit order placed: {order['id']}")
    print(f"Will execute when price <= ${order['price']}")
    
    # Check pending orders
    print("\nChecking pending orders...")
    pending = client.get_pending_orders(symbol='AAPL')
    print(f"Found {len(pending)} pending orders")
    
    # Cancel order if needed
    if pending:
        order_id = pending[0]['id']
        print(f"\nCanceling order {order_id}...")
        canceled = client.cancel_order(order_id)
        print(f"Order canceled: {canceled['status']}")


def example_stop_loss():
    """Example: Stop loss to protect position"""
    
    client = TradingAPIClient('http://localhost:8000', 'your_token')
    
    # Buy shares first
    print("Buying 10 shares of AAPL...")
    buy_order = client.place_market_order('AAPL', 'BUY', 10)
    avg_price = float(buy_order['average_fill_price'])
    
    # Place stop loss 5% below purchase price
    stop_price = avg_price * 0.95
    print(f"\nPlacing stop loss at ${stop_price:.2f}...")
    stop_order = client.place_stop_loss(
        symbol='AAPL',
        quantity=10,
        stop_price=stop_price
    )
    print(f"Stop loss placed: {stop_order['id']}")
    print(f"Will sell if price drops to ${stop_price:.2f}")


def example_bracket_order():
    """Example: Bracket order (take profit + stop loss)"""
    
    client = TradingAPIClient('http://localhost:8000', 'your_token')
    
    # Buy shares
    print("Buying 10 shares of AAPL...")
    buy_order = client.place_market_order('AAPL', 'BUY', 10)
    avg_price = float(buy_order['average_fill_price'])
    
    # Take profit 10% above
    take_profit_price = avg_price * 1.10
    print(f"\nPlacing take profit at ${take_profit_price:.2f}...")
    tp_order = client.place_take_profit(
        symbol='AAPL',
        quantity=10,
        target_price=take_profit_price
    )
    
    # Stop loss 5% below
    stop_price = avg_price * 0.95
    print(f"Placing stop loss at ${stop_price:.2f}...")
    sl_order = client.place_stop_loss(
        symbol='AAPL',
        quantity=10,
        stop_price=stop_price
    )
    
    print(f"\nBracket orders placed:")
    print(f"  Entry: ${avg_price:.2f}")
    print(f"  Take Profit: ${take_profit_price:.2f} (Order ID: {tp_order['id']})")
    print(f"  Stop Loss: ${stop_price:.2f} (Order ID: {sl_order['id']})")


def example_validate_before_placing():
    """Example: Validate order before placing"""
    
    client = TradingAPIClient('http://localhost:8000', 'your_token')
    
    # Validate if we can afford to buy 100 shares
    print("Validating order...")
    validation = client.validate_order(
        symbol='AAPL',
        side='BUY',
        quantity=100,
        order_type='MARKET'
    )
    
    print(f"Validation result: {validation}")
    print(f"Estimated cost: ${validation['estimated_cost']}")
    print(f"Estimated fee: ${validation['estimated_fee']}")
    
    if validation.get('sufficient_funds'):
        print("✓ Sufficient funds - placing order...")
        order = client.place_market_order('AAPL', 'BUY', 100)
        print(f"Order placed: {order['id']}")
    else:
        available = validation.get('available_cash', 0)
        print(f"✗ Insufficient funds. Available: ${available}")


def example_view_history():
    """Example: View order and transaction history"""
    
    client = TradingAPIClient('http://localhost:8000', 'your_token')
    
    # Get all orders
    print("Fetching order history...")
    orders = client.get_orders(limit=10)
    print(f"\nLast {len(orders)} orders:")
    for order in orders:
        print(f"  {order['id']}: {order['side']} {order['quantity']} {order['symbol']} "
              f"@ ${order['average_fill_price'] or 'N/A'} - {order['status']}")
    
    # Get transaction history
    print("\nFetching transaction history...")
    transactions = client.get_transaction_history(limit=10)
    print(f"\nLast {len(transactions)} transactions:")
    for tx in transactions:
        print(f"  {tx['symbol']}: {tx['transaction_type']} {tx['quantity']} @ ${tx['price']} "
              f"(Fee: ${tx['fee']})")


def example_monitor_pending_orders():
    """Example: Monitor and manage pending orders"""
    
    client = TradingAPIClient('http://localhost:8000', 'your_token')
    
    # Get all pending orders
    print("Checking pending orders...")
    pending = client.get_pending_orders()
    
    print(f"\nFound {len(pending)} pending orders:")
    for order in pending:
        print(f"\nOrder ID: {order['id']}")
        print(f"  Symbol: {order['symbol']}")
        print(f"  Type: {order['order_type']}")
        print(f"  Side: {order['side']}")
        print(f"  Quantity: {order['filled_quantity']}/{order['quantity']}")
        print(f"  Status: {order['status']}")
        
        if order['price']:
            print(f"  Limit Price: ${order['price']}")
        if order['stop_price']:
            print(f"  Stop Price: ${order['stop_price']}")
        
        # Ask if user wants to cancel
        # (In real app, this would be a UI interaction)
        # cancel = input(f"Cancel order {order['id']}? (y/n): ")
        # if cancel.lower() == 'y':
        #     client.cancel_order(order['id'])
        #     print("Order canceled")


def example_error_handling():
    """Example: Proper error handling"""
    
    client = TradingAPIClient('http://localhost:8000', 'your_token')
    
    try:
        # Try to buy with insufficient funds
        order = client.place_market_order('AAPL', 'BUY', 10000)
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            error = e.response.json()
            print(f"Order rejected: {error['detail']}")
            
            # Handle specific errors
            if 'Insufficient funds' in error['detail']:
                print("Solution: Reduce order size or add more cash")
            elif 'Insufficient shares' in error['detail']:
                print("Solution: Reduce sell quantity")
            elif 'Market data not available' in error['detail']:
                print("Solution: Check symbol or try again later")
        
        elif e.response.status_code == 401:
            print("Authentication error: Token expired or invalid")
        
        elif e.response.status_code == 429:
            print("Rate limit exceeded: Too many requests")
        
        else:
            print(f"API error: {e.response.status_code}")
    
    except requests.exceptions.ConnectionError:
        print("Connection error: Cannot reach API server")
    
    except Exception as e:
        print(f"Unexpected error: {str(e)}")


def example_batch_operations():
    """Example: Batch operations (multiple orders)"""
    
    client = TradingAPIClient('http://localhost:8000', 'your_token')
    
    # Buy multiple stocks
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN']
    orders = []
    
    print("Placing orders for portfolio diversification...")
    for symbol in symbols:
        try:
            order = client.place_market_order(
                symbol=symbol,
                side='BUY',
                quantity=5,
                idempotency_key=f'batch_{symbol}'
            )
            orders.append(order)
            print(f"✓ {symbol}: Order {order['id']} placed")
        except Exception as e:
            print(f"✗ {symbol}: Failed - {str(e)}")
    
    print(f"\nSuccessfully placed {len(orders)} orders")


def example_partial_fills():
    """Example: Handling partial fills"""
    
    client = TradingAPIClient('http://localhost:8000', 'your_token')
    
    # Place a large order that might fill partially
    order = client.place_limit_order(
        symbol='AAPL',
        side='BUY',
        quantity=100,
        limit_price=150.00
    )
    
    print(f"Order placed: {order['id']}")
    print(f"Initial status: {order['status']}")
    
    # Check order status later
    import time
    time.sleep(5)
    
    updated_order = client.get_order(order['id'])
    fill_percentage = updated_order['fill_percentage']
    
    print(f"\nOrder update:")
    print(f"  Status: {updated_order['status']}")
    print(f"  Filled: {updated_order['filled_quantity']}/{updated_order['quantity']}")
    print(f"  Fill percentage: {fill_percentage:.1f}%")
    
    if updated_order['status'] == 'PARTIALLY_FILLED':
        print("\nOrder partially filled. Options:")
        print("1. Wait for full fill")
        print("2. Cancel remaining quantity")
        print("3. Modify order (if supported)")


def example_cost_analysis():
    """Example: Analyze costs before trading"""
    
    client = TradingAPIClient('http://localhost:8000', 'your_token')
    
    symbol = 'AAPL'
    quantity = 100
    
    # Validate to get cost estimate
    validation = client.validate_order(
        symbol=symbol,
        side='BUY',
        quantity=quantity
    )
    
    print(f"Cost Analysis for {quantity} shares of {symbol}:")
    print(f"  Estimated stock cost: ${validation['estimated_cost']:.2f}")
    print(f"  Trading fee: ${validation['estimated_fee']:.2f}")
    print(f"  Total cost: ${validation['estimated_cost']:.2f}")
    
    if validation.get('available_cash'):
        available = validation['available_cash']
        print(f"\n  Available cash: ${available:.2f}")
        remaining = available - validation['estimated_cost']
        print(f"  Remaining after trade: ${remaining:.2f}")
        
        if validation['sufficient_funds']:
            print("\n✓ Order is affordable")
        else:
            shortfall = validation['estimated_cost'] - available
            print(f"\n✗ Insufficient funds (short ${shortfall:.2f})")


# ============================================
# Frontend Integration Example (React/JS)
# ============================================

FRONTEND_EXAMPLE = """
// React component example for placing orders

import React, { useState } from 'react';
import axios from 'axios';

const TradingForm = ({ token }) => {
  const [orderData, setOrderData] = useState({
    symbol: '',
    orderType: 'MARKET',
    side: 'BUY',
    quantity: '',
    price: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const placeOrder = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post(
        'http://localhost:8000/api/orders',
        {
          symbol: orderData.symbol.toUpperCase(),
          order_type: orderData.orderType,
          side: orderData.side,
          quantity: parseFloat(orderData.quantity),
          price: orderData.price ? parseFloat(orderData.price) : null
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      alert(`Order placed successfully! ID: ${response.data.id}`);
      
    } catch (err) {
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Failed to place order');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="trading-form">
      <input
        type="text"
        placeholder="Symbol (e.g., AAPL)"
        value={orderData.symbol}
        onChange={(e) => setOrderData({...orderData, symbol: e.target.value})}
      />
      
      <select
        value={orderData.orderType}
        onChange={(e) => setOrderData({...orderData, orderType: e.target.value})}
      >
        <option value="MARKET">Market</option>
        <option value="LIMIT">Limit</option>
        <option value="STOP">Stop</option>
        <option value="STOP_LIMIT">Stop Limit</option>
      </select>
      
      <select
        value={orderData.side}
        onChange={(e) => setOrderData({...orderData, side: e.target.value})}
      >
        <option value="BUY">Buy</option>
        <option value="SELL">Sell</option>
      </select>
      
      <input
        type="number"
        placeholder="Quantity"
        value={orderData.quantity}
        onChange={(e) => setOrderData({...orderData, quantity: e.target.value})}
      />
      
      {(orderData.orderType === 'LIMIT' || orderData.orderType === 'STOP_LIMIT') && (
        <input
          type="number"
          placeholder="Limit Price"
          value={orderData.price}
          onChange={(e) => setOrderData({...orderData, price: e.target.value})}
        />
      )}
      
      <button onClick={placeOrder} disabled={loading}>
        {loading ? 'Placing Order...' : 'Place Order'}
      </button>
      
      {error && <div className="error">{error}</div>}
    </div>
  );
};

export default TradingForm;
"""


if __name__ == '__main__':
    print("Trading API Usage Examples")
    print("=" * 60)
    print("\nAvailable examples:")
    print("1. Basic trading (market orders)")
    print("2. Limit orders")
    print("3. Stop loss orders")
    print("4. Bracket orders (take profit + stop loss)")
    print("5. Order validation")
    print("6. View history")
    print("7. Monitor pending orders")
    print("8. Error handling")
    print("9. Batch operations")
    print("10. Partial fills")
    print("11. Cost analysis")
    print("\nFrontend integration example included in FRONTEND_EXAMPLE")
    print("\nTo use:")
    print("  from examples.trading_api_examples import TradingAPIClient")
    print("  client = TradingAPIClient('http://localhost:8000', 'your_token')")
    print("  order = client.place_market_order('AAPL', 'BUY', 10)")