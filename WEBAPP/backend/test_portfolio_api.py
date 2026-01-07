#!/usr/bin/env python
"""
Test script for Portfolio API endpoints
Tests CRUD operations and bulk upload functionality
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api"
USERNAME = "testuser"
PASSWORD = "testpass123"
EMAIL = f"{USERNAME}@test.com"

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def print_header(text):
    print(f"\n{BLUE}{'='*60}")
    print(f"{text}")
    print(f"{'='*60}{RESET}\n")


def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text):
    print(f"{RED}✗ {text}{RESET}")


def print_info(text):
    print(f"{YELLOW}ℹ {text}{RESET}")


class PortfolioAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {}
    
    def register_user(self):
        """Register a new test user"""
        print_header("1. REGISTERING TEST USER")
        
        url = f"{self.base_url}/../users/register/"
        data = {
            "username": USERNAME,
            "email": EMAIL,
            "password": PASSWORD,
            "password_confirm": PASSWORD
        }
        
        try:
            response = requests.post(url, json=data)
            if response.status_code in [201, 400]:  # 400 if user exists
                if response.status_code == 201:
                    print_success(f"User registered: {USERNAME}")
                else:
                    print_info(f"User already exists: {USERNAME}")
                return True
            else:
                print_error(f"Registration failed: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print_error(f"Registration error: {str(e)}")
            return False
    
    def login(self):
        """Login and get JWT token"""
        print_header("2. LOGGING IN")
        
        url = f"{self.base_url}/../users/login/"
        data = {
            "username": USERNAME,
            "password": PASSWORD
        }
        
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access')
                self.headers = {
                    'Authorization': f'Bearer {self.token}',
                    'Content-Type': 'application/json'
                }
                print_success(f"Login successful")
                print_info(f"Token: {self.token[:50]}...")
                return True
            else:
                print_error(f"Login failed: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print_error(f"Login error: {str(e)}")
            return False
    
    def get_portfolio(self):
        """Get user's portfolio"""
        print_header("3. GET PORTFOLIO")
        
        url = f"{self.base_url}/portfolio/"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                print_success("Portfolio retrieved")
                print(json.dumps(data, indent=2))
                return True
            else:
                print_error(f"Failed to get portfolio: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print_error(f"Error: {str(e)}")
            return False
    
    def add_stock(self, symbol, quantity, cost_basis):
        """Add a single stock to portfolio"""
        print_header(f"4. ADD STOCK: {symbol}")
        
        url = f"{self.base_url}/portfolio/stocks/"
        data = {
            "symbol": symbol,
            "quantity": quantity,
            "cost_basis": cost_basis
        }
        
        try:
            response = requests.post(url, json=data, headers=self.headers)
            if response.status_code in [200, 201]:
                data = response.json()
                print_success(f"Stock added: {symbol}")
                print(json.dumps(data, indent=2))
                return True
            else:
                print_error(f"Failed to add stock: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print_error(f"Error: {str(e)}")
            return False
    
    def list_stocks(self):
        """List all stocks in portfolio"""
        print_header("5. LIST ALL STOCKS")
        
        url = f"{self.base_url}/portfolio/stocks/"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                print_success(f"Found {len(data)} stocks")
                print(json.dumps(data, indent=2))
                return True
            else:
                print_error(f"Failed to list stocks: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print_error(f"Error: {str(e)}")
            return False
    
    def get_stock(self, symbol):
        """Get specific stock details"""
        print_header(f"6. GET STOCK: {symbol}")
        
        url = f"{self.base_url}/portfolio/stocks/{symbol}/"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                print_success(f"Stock retrieved: {symbol}")
                print(json.dumps(data, indent=2))
                return True
            else:
                print_error(f"Failed to get stock: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print_error(f"Error: {str(e)}")
            return False
    
    def update_stock(self, symbol, quantity, cost_basis):
        """Update stock quantity and cost basis"""
        print_header(f"7. UPDATE STOCK: {symbol}")
        
        url = f"{self.base_url}/portfolio/stocks/{symbol}/"
        data = {
            "symbol": symbol,
            "quantity": quantity,
            "cost_basis": cost_basis
        }
        
        try:
            response = requests.put(url, json=data, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                print_success(f"Stock updated: {symbol}")
                print(json.dumps(data, indent=2))
                return True
            else:
                print_error(f"Failed to update stock: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print_error(f"Error: {str(e)}")
            return False
    
    def bulk_upload(self, stocks):
        """Bulk upload multiple stocks"""
        print_header("8. BULK UPLOAD STOCKS")
        
        url = f"{self.base_url}/portfolio/stocks/bulk_upload/"
        data = {"stocks": stocks}
        
        try:
            response = requests.post(url, json=data, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                print_success("Bulk upload successful")
                print(json.dumps(data, indent=2))
                return True
            else:
                print_error(f"Bulk upload failed: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print_error(f"Error: {str(e)}")
            return False
    
    def get_summary(self):
        """Get portfolio summary"""
        print_header("9. GET PORTFOLIO SUMMARY")
        
        url = f"{self.base_url}/portfolio/stocks/summary/"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                print_success("Summary retrieved")
                print(json.dumps(data, indent=2))
                return True
            else:
                print_error(f"Failed to get summary: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print_error(f"Error: {str(e)}")
            return False
    
    def delete_stock(self, symbol):
        """Delete a stock from portfolio"""
        print_header(f"10. DELETE STOCK: {symbol}")
        
        url = f"{self.base_url}/portfolio/stocks/{symbol}/"
        
        try:
            response = requests.delete(url, headers=self.headers)
            if response.status_code == 204:
                print_success(f"Stock deleted: {symbol}")
                return True
            else:
                print_error(f"Failed to delete stock: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print_error(f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run complete test suite"""
        print(f"\n{BLUE}{'='*60}")
        print("PORTFOLIO API TEST SUITE")
        print(f"{'='*60}{RESET}\n")
        
        # Step 1: Register user
        if not self.register_user():
            return
        
        # Step 2: Login
        if not self.login():
            print_error("Cannot proceed without authentication")
            return
        
        # Step 3: Get empty portfolio
        self.get_portfolio()
        
        # Step 4: Add single stock
        self.add_stock("AAPL", 100, 150.50)
        
        # Step 5: List stocks
        self.list_stocks()
        
        # Step 6: Get specific stock
        self.get_stock("AAPL")
        
        # Step 7: Update stock
        self.update_stock("AAPL", 120, 155.00)
        
        # Step 8: Bulk upload from CSV data
        csv_stocks = [
            {"symbol": "NVDA", "quantity": 50, "cost_basis": 85.00},
            {"symbol": "TSLA", "quantity": 60, "cost_basis": 195.50},
            {"symbol": "MSFT", "quantity": 45, "cost_basis": 315.00},
            {"symbol": "AMZN", "quantity": 100, "cost_basis": 130.80},
        ]
        self.bulk_upload(csv_stocks)
        
        # Step 9: Get summary
        self.get_summary()
        
        # Step 10: Delete a stock
        self.delete_stock("TSLA")
        
        # Final: List all stocks
        self.list_stocks()
        
        print_header("TEST SUITE COMPLETED!")
        print_success("All tests executed. Check results above.")


if __name__ == "__main__":
    tester = PortfolioAPITester()
    tester.run_all_tests()
