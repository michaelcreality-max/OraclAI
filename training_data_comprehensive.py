"""
Comprehensive Training System for REAL Local LLM
Multi-domain training: Code, STEM, Finance, Website Building, General
"""

import numpy as np
import json
import pickle
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import random


@dataclass
class TrainingExample:
    """Single training example"""
    input_text: str
    output_text: str
    domain: str
    difficulty: str  # easy, medium, hard
    tags: List[str]


@dataclass
class DomainTrainingData:
    """Training data for a specific domain"""
    domain: str
    examples: List[TrainingExample]
    validation_split: float = 0.1
    
    def split(self) -> Tuple[List[TrainingExample], List[TrainingExample]]:
        """Split into train and validation sets"""
        random.shuffle(self.examples)
        split_idx = int(len(self.examples) * (1 - self.validation_split))
        return self.examples[:split_idx], self.examples[split_idx:]


class CodeTrainingData:
    """
    High-quality code generation training data
    Languages: Python, JavaScript, HTML, CSS, SQL
    """
    
    EXAMPLES = [
        # Python examples
        TrainingExample(
            input_text="create python function to calculate fibonacci",
            output_text="def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
            domain="code",
            difficulty="easy",
            tags=["python", "recursion", "math"]
        ),
        TrainingExample(
            input_text="python class for user authentication",
            output_text="class UserAuth:\n    def __init__(self):\n        self.users = {}\n    \n    def register(self, username, password):\n        if username not in self.users:\n            self.users[username] = password\n            return True\n        return False\n    \n    def login(self, username, password):\n        return self.users.get(username) == password",
            domain="code",
            difficulty="medium",
            tags=["python", "class", "authentication"]
        ),
        TrainingExample(
            input_text="create rest api with flask",
            output_text="from flask import Flask, jsonify, request\n\napp = Flask(__name__)\n\n@app.route('/api/data', methods=['GET'])\ndef get_data():\n    return jsonify({'success': True, 'data': []})\n\n@app.route('/api/data', methods=['POST'])\ndef post_data():\n    data = request.get_json()\n    return jsonify({'success': True, 'received': data})",
            domain="code",
            difficulty="medium",
            tags=["python", "flask", "api", "rest"]
        ),
        TrainingExample(
            input_text="python decorator for timing functions",
            output_text="import time\nfrom functools import wraps\n\ndef timer(func):\n    @wraps(func)\n    def wrapper(*args, **kwargs):\n        start = time.time()\n        result = func(*args, **kwargs)\n        elapsed = time.time() - start\n        print(f'{func.__name__} took {elapsed:.4f} seconds')\n        return result\n    return wrapper",
            domain="code",
            difficulty="medium",
            tags=["python", "decorator", "performance"]
        ),
        TrainingExample(
            input_text="async python function with aiohttp",
            output_text="import aiohttp\nimport asyncio\n\nasync def fetch_data(url):\n    async with aiohttp.ClientSession() as session:\n        async with session.get(url) as response:\n            return await response.json()\n\nasync def main():\n    urls = ['https://api.example.com/data']\n    results = await asyncio.gather(*[fetch_data(url) for url in urls])\n    return results",
            domain="code",
            difficulty="hard",
            tags=["python", "async", "aiohttp", "concurrency"]
        ),
        
        # JavaScript examples
        TrainingExample(
            input_text="javascript function to reverse string",
            output_text="function reverseString(str) {\n    return str.split('').reverse().join('');\n}\n\n// ES6 arrow function\nconst reverseString = str => str.split('').reverse().join('');",
            domain="code",
            difficulty="easy",
            tags=["javascript", "string", "es6"]
        ),
        TrainingExample(
            input_text="react component for user profile",
            output_text="import React, { useState, useEffect } from 'react';\n\nconst UserProfile = ({ userId }) => {\n    const [user, setUser] = useState(null);\n    const [loading, setLoading] = useState(true);\n\n    useEffect(() => {\n        fetchUser(userId).then(data => {\n            setUser(data);\n            setLoading(false);\n        });\n    }, [userId]);\n\n    if (loading) return <div>Loading...</div>;\n    \n    return (\n        <div className=\"user-profile\">\n            <h2>{user.name}</h2>\n            <p>{user.email}</p>\n        </div>\n    );\n};\n\nexport default UserProfile;",
            domain="code",
            difficulty="medium",
            tags=["javascript", "react", "hooks", "component"]
        ),
        TrainingExample(
            input_text="nodejs express server with middleware",
            output_text="const express = require('express');\nconst app = express();\n\n// Middleware\napp.use(express.json());\napp.use((req, res, next) => {\n    console.log(`${req.method} ${req.path}`);\n    next();\n});\n\n// Routes\napp.get('/', (req, res) => {\n    res.json({ message: 'Hello World' });\n});\n\napp.post('/users', (req, res) => {\n    const user = req.body;\n    res.status(201).json(user);\n});\n\n// Error handling\napp.use((err, req, res, next) => {\n    res.status(500).json({ error: err.message });\n});\n\napp.listen(3000);",
            domain="code",
            difficulty="medium",
            tags=["javascript", "nodejs", "express", "middleware"]
        ),
        TrainingExample(
            input_text="javascript promise.all with error handling",
            output_text="async function fetchMultiple(urls) {\n    try {\n        const promises = urls.map(url => fetch(url));\n        const responses = await Promise.all(promises);\n        const data = await Promise.all(\n            responses.map(res => res.json())\n        );\n        return data;\n    } catch (error) {\n        console.error('Fetch failed:', error);\n        throw error;\n    }\n}",
            domain="code",
            difficulty="medium",
            tags=["javascript", "promise", "async", "error-handling"]
        ),
        
        # HTML/CSS examples
        TrainingExample(
            input_text="responsive navigation bar html css",
            output_text="<nav class=\"navbar\">\n    <div class=\"nav-brand\">Logo</div>\n    <ul class=\"nav-links\">\n        <li><a href=\"#\">Home</a></li>\n        <li><a href=\"#\">About</a></li>\n        <li><a href=\"#\">Contact</a></li>\n    </ul>\n</nav>\n\n<style>\n.navbar {\n    display: flex;\n    justify-content: space-between;\n    padding: 1rem 2rem;\n    background: #333;\n}\n.nav-links {\n    display: flex;\n    gap: 2rem;\n    list-style: none;\n}\n.nav-links a {\n    color: white;\n    text-decoration: none;\n}\n@media (max-width: 768px) {\n    .nav-links {\n        flex-direction: column;\n    }\n}\n</style>",
            domain="code",
            difficulty="medium",
            tags=["html", "css", "responsive", "navigation"]
        ),
        TrainingExample(
            input_text="css grid layout for photo gallery",
            output_text=".gallery {\n    display: grid;\n    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));\n    gap: 1rem;\n    padding: 1rem;\n}\n\n.gallery img {\n    width: 100%;\n    height: 250px;\n    object-fit: cover;\n    border-radius: 8px;\n    transition: transform 0.3s;\n}\n\n.gallery img:hover {\n    transform: scale(1.05);\n}",
            domain="code",
            difficulty="easy",
            tags=["css", "grid", "layout", "gallery"]
        ),
        TrainingExample(
            input_text="flexbox centering vertical horizontal",
            output_text=".container {\n    display: flex;\n    justify-content: center;\n    align-items: center;\n    min-height: 100vh;\n}\n\n/* Alternative with CSS Grid */\n.container-grid {\n    display: grid;\n    place-items: center;\n    min-height: 100vh;\n}",
            domain="code",
            difficulty="easy",
            tags=["css", "flexbox", "centering"]
        ),
        
        # SQL examples
        TrainingExample(
            input_text="sql query to find top 5 customers by orders",
            output_text="SELECT c.customer_name, COUNT(o.order_id) as order_count, SUM(o.total_amount) as total_spent\nFROM customers c\nJOIN orders o ON c.customer_id = o.customer_id\nGROUP BY c.customer_id, c.customer_name\nORDER BY order_count DESC\nLIMIT 5;",
            domain="code",
            difficulty="medium",
            tags=["sql", "query", "aggregation", "join"]
        ),
        TrainingExample(
            input_text="create table with foreign key constraint",
            output_text="CREATE TABLE orders (\n    order_id INT PRIMARY KEY AUTO_INCREMENT,\n    customer_id INT NOT NULL,\n    order_date DATE DEFAULT CURRENT_DATE,\n    total_amount DECIMAL(10, 2),\n    status VARCHAR(50) DEFAULT 'pending',\n    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)\n        ON DELETE CASCADE\n        ON UPDATE CASCADE\n);",
            domain="code",
            difficulty="medium",
            tags=["sql", "ddl", "foreign-key", "constraints"]
        ),
        TrainingExample(
            input_text="sql window function for running total",
            output_text="SELECT\n    order_date,\n    daily_sales,\n    SUM(daily_sales) OVER (ORDER BY order_date) as running_total,\n    AVG(daily_sales) OVER (ORDER BY order_date ROWS 6 PRECEDING) as moving_average\nFROM daily_sales_summary\nORDER BY order_date;",
            domain="code",
            difficulty="hard",
            tags=["sql", "window-function", "analytics"]
        ),
        TrainingExample(
            input_text="sql index for performance optimization",
            output_text="-- Create index for frequently queried column\nCREATE INDEX idx_orders_customer_date\nON orders(customer_id, order_date);\n\n-- Composite index for query optimization\nCREATE INDEX idx_products_category_price\nON products(category, price DESC);\n\n-- Partial index for active records only\nCREATE INDEX idx_active_users\nON users(email) WHERE status = 'active';",
            domain="code",
            difficulty="medium",
            tags=["sql", "performance", "index", "optimization"]
        ),
    ]
    
    @classmethod
    def get_training_data(cls) -> DomainTrainingData:
        return DomainTrainingData(
            domain="code",
            examples=cls.EXAMPLES,
            validation_split=0.15
        )


class STEMTrainingData:
    """
    Science, Technology, Engineering, Math training data
    Physics, Calculus, Algebra, Statistics, Chemistry concepts
    """
    
    EXAMPLES = [
        # Mathematics
        TrainingExample(
            input_text="explain quadratic formula",
            output_text="The quadratic formula solves equations in the form ax² + bx + c = 0:\n\nx = (-b ± √(b² - 4ac)) / 2a\n\nThe discriminant (b² - 4ac) tells us:\n- Positive: Two real solutions\n- Zero: One real solution\n- Negative: Two complex solutions\n\nExample: x² - 5x + 6 = 0\nx = (5 ± √(25 - 24)) / 2\nx = (5 ± 1) / 2\nx = 3 or x = 2",
            domain="stem",
            difficulty="easy",
            tags=["math", "algebra", "quadratic"]
        ),
        TrainingExample(
            input_text="derivative of x squared plus 3x",
            output_text="f(x) = x² + 3x\n\nUsing the power rule: d/dx(xⁿ) = nxⁿ⁻¹\n\nf'(x) = d/dx(x²) + d/dx(3x)\nf'(x) = 2x + 3\n\nVerification:\n- d/dx(x²) = 2x¹ = 2x ✓\n- d/dx(3x) = 3x⁰ = 3 ✓",
            domain="stem",
            difficulty="easy",
            tags=["math", "calculus", "derivative"]
        ),
        TrainingExample(
            input_text="chain rule explanation with example",
            output_text="The chain rule: d/dx[f(g(x))] = f'(g(x)) · g'(x)\n\nExample: Find derivative of (3x² + 2)⁵\n\nLet u = 3x² + 2, so y = u⁵\n\ndy/du = 5u⁴ = 5(3x² + 2)⁴\ndu/dx = 6x\n\ndy/dx = dy/du · du/dx\ndy/dx = 5(3x² + 2)⁴ · 6x\ndy/dx = 30x(3x² + 2)⁴",
            domain="stem",
            difficulty="medium",
            tags=["math", "calculus", "chain-rule"]
        ),
        TrainingExample(
            input_text="calculate area under curve using integration",
            output_text="To find area under f(x) = x² from 0 to 3:\n\nArea = ∫₀³ x² dx\n\nUsing power rule for integration: ∫xⁿ dx = xⁿ⁺¹/(n+1) + C\n\nArea = [x³/3]₀³\nArea = (3³/3) - (0³/3)\nArea = 27/3 - 0\nArea = 9 square units",
            domain="stem",
            difficulty="medium",
            tags=["math", "calculus", "integration"]
        ),
        TrainingExample(
            input_text="probability of rolling two sixes",
            output_text="For two independent dice:\n\nP(first die = 6) = 1/6\nP(second die = 6) = 1/6\n\nP(both sixes) = P(6) × P(6)\nP(both sixes) = 1/6 × 1/6\nP(both sixes) = 1/36\nP(both sixes) ≈ 2.78%",
            domain="stem",
            difficulty="easy",
            tags=["math", "probability", "statistics"]
        ),
        TrainingExample(
            input_text="standard deviation calculation",
            output_text="For dataset: 2, 4, 4, 4, 5, 5, 7, 9\n\nStep 1: Mean\nμ = (2+4+4+4+5+5+7+9)/8 = 40/8 = 5\n\nStep 2: Squared differences\n(2-5)²=9, (4-5)²=1, (4-5)²=1, (4-5)²=1\n(5-5)²=0, (5-5)²=0, (7-5)²=4, (9-5)²=16\n\nStep 3: Variance\nσ² = (9+1+1+1+0+0+4+16)/8 = 32/8 = 4\n\nStep 4: Standard deviation\nσ = √4 = 2",
            domain="stem",
            difficulty="medium",
            tags=["math", "statistics", "standard-deviation"]
        ),
        TrainingExample(
            input_text="pythagorean theorem with 3 4 5 triangle",
            output_text="Pythagorean Theorem: a² + b² = c²\n\nFor 3-4-5 right triangle:\n- a = 3 (leg)\n- b = 4 (leg)\n- c = 5 (hypotenuse)\n\nVerification:\n3² + 4² = 5²\n9 + 16 = 25\n25 = 25 ✓\n\nApplication:\nIf a=6 and b=8, find c:\n6² + 8² = c²\n36 + 64 = c²\n100 = c²\nc = 10",
            domain="stem",
            difficulty="easy",
            tags=["math", "geometry", "pythagorean"]
        ),
        
        # Physics
        TrainingExample(
            input_text="newtons second law force equals mass times acceleration",
            output_text="Newton's Second Law: F = ma\n\nWhere:\n- F = force (Newtons, N)\n- m = mass (kilograms, kg)\n- a = acceleration (m/s²)\n\nExample: A 1000 kg car accelerates at 2 m/s²\nF = 1000 kg × 2 m/s²\nF = 2000 N\n\nRearranged formulas:\n- a = F/m (acceleration calculation)\n- m = F/a (mass calculation)",
            domain="stem",
            difficulty="easy",
            tags=["physics", "mechanics", "newton"]
        ),
        TrainingExample(
            input_text="kinetic energy formula and calculation",
            output_text="Kinetic Energy: KE = ½mv²\n\nWhere:\n- KE = kinetic energy (Joules, J)\n- m = mass (kg)\n- v = velocity (m/s)\n\nExample: 2 kg ball moving at 10 m/s\nKE = ½ × 2 kg × (10 m/s)²\nKE = 1 × 100\nKE = 100 J\n\nKey insight:\n- KE increases with velocity squared\n- Doubling speed quadruples energy\n- Tripling speed gives 9× energy",
            domain="stem",
            difficulty="easy",
            tags=["physics", "energy", "kinetic"]
        ),
        TrainingExample(
            input_text="ohms law voltage current resistance",
            output_text="Ohm's Law: V = IR\n\nWhere:\n- V = voltage (Volts, V)\n- I = current (Amperes, A)\n- R = resistance (Ohms, Ω)\n\nExample: Circuit with 12V battery and 4Ω resistor\nI = V/R = 12V/4Ω = 3A\n\nPower calculation:\nP = VI = I²R = V²/R\nP = 12V × 3A = 36W\n\nCircuit relationships:\n- Series: R_total = R₁ + R₂ + R₃\n- Parallel: 1/R_total = 1/R₁ + 1/R₂ + 1/R₃",
            domain="stem",
            difficulty="easy",
            tags=["physics", "electricity", "ohms-law"]
        ),
        TrainingExample(
            input_text="calculate wavelength from frequency",
            output_text="Wave equation: v = fλ\n\nWhere:\n- v = wave speed (m/s)\n- f = frequency (Hz)\n- λ = wavelength (m)\n\nFor light in vacuum:\nc = 3 × 10⁸ m/s\n\nExample: Red light with f = 4.3 × 10¹⁴ Hz\nλ = c/f\nλ = (3 × 10⁸) / (4.3 × 10¹⁴)\nλ = 698 nm (nanometers)\n\nVisible light range:\n- Violet: 380-450 nm\n- Blue: 450-495 nm\n- Green: 495-570 nm\n- Yellow: 570-590 nm\n- Orange: 590-620 nm\n- Red: 620-750 nm",
            domain="stem",
            difficulty="medium",
            tags=["physics", "waves", "optics"]
        ),
        
        # Chemistry
        TrainingExample(
            input_text="balance chemical equation h2 plus o2 equals h2o",
            output_text="Unbalanced: H₂ + O₂ → H₂O\n\nCount atoms:\n- Left: 2 H, 2 O\n- Right: 2 H, 1 O\n\nBalanced equation:\n2H₂ + O₂ → 2H₂O\n\nVerification:\n- Left: 4 H (2×2), 2 O\n- Right: 4 H (2×2), 2 O (2×1)\n- Balanced ✓\n\nCoefficients: 2, 1, 2\nMole ratio: H₂:O₂:H₂O = 2:1:2",
            domain="stem",
            difficulty="easy",
            tags=["chemistry", "stoichiometry", "balancing"]
        ),
        TrainingExample(
            input_text="calculate molar mass of water",
            output_text="Molar mass calculation for H₂O:\n\nAtomic masses:\n- H = 1.008 g/mol\n- O = 16.00 g/mol\n\nH₂O composition:\n- 2 hydrogen atoms: 2 × 1.008 = 2.016 g/mol\n- 1 oxygen atom: 1 × 16.00 = 16.00 g/mol\n\nTotal molar mass:\nM(H₂O) = 2.016 + 16.00 = 18.016 g/mol\n≈ 18.02 g/mol\n\nThis means 18.02 grams of water = 1 mole = 6.022×10²³ molecules",
            domain="stem",
            difficulty="easy",
            tags=["chemistry", "molar-mass", "stoichiometry"]
        ),
    ]
    
    @classmethod
    def get_training_data(cls) -> DomainTrainingData:
        return DomainTrainingData(
            domain="stem",
            examples=cls.EXAMPLES,
            validation_split=0.1
        )


class FinanceTrainingData:
    """
    Financial concepts, stock analysis, investment strategies
    """
    
    EXAMPLES = [
        TrainingExample(
            input_text="explain price to earnings ratio",
            output_text="P/E Ratio = Stock Price / Earnings Per Share (EPS)\n\nExample:\n- Stock price: $100\n- EPS: $5\n- P/E = 100/5 = 20\n\nInterpretation:\n- P/E 15-25: Fairly valued (typical)\n- P/E < 15: Potentially undervalued\n- P/E > 25: Growth stock or overvalued\n\nLimitations:\n- Doesn't work for unprofitable companies\n- Industry varies (tech > banks)\n- Compare within same sector",
            domain="finance",
            difficulty="easy",
            tags=["finance", "valuation", "pe-ratio"]
        ),
        TrainingExample(
            input_text="calculate compound interest formula",
            output_text="Compound Interest Formula:\nA = P(1 + r/n)^(nt)\n\nWhere:\n- A = Final amount\n- P = Principal (initial investment)\n- r = Annual interest rate (decimal)\n- n = Compounding periods per year\n- t = Time in years\n\nExample: $10,000 at 7% for 20 years, compounded annually:\nA = 10000(1 + 0.07/1)^(1×20)\nA = 10000(1.07)^20\nA = 10000 × 3.8697\nA = $38,697\n\nRule of 72:\nYears to double ≈ 72 / interest rate\nAt 7%: 72/7 ≈ 10.3 years",
            domain="finance",
            difficulty="medium",
            tags=["finance", "compound-interest", "investment"]
        ),
        TrainingExample(
            input_text="portfolio diversification explained",
            output_text="Portfolio Diversification:\n\nPrinciple: Don't put all eggs in one basket\n\nDiversification types:\n1. Asset classes: Stocks, bonds, real estate, commodities\n2. Geography: US, international, emerging markets\n3. Sectors: Tech, healthcare, finance, energy\n4. Market cap: Large, mid, small cap\n\nBenefits:\n- Reduces unsystematic risk\n- Smoother returns over time\n- Protection against sector crashes\n\nExample allocation:\n- 60% stocks ( diversified across sectors)\n- 30% bonds\n- 10% alternatives (real estate, commodities)",
            domain="finance",
            difficulty="easy",
            tags=["finance", "portfolio", "diversification"]
        ),
        TrainingExample(
            input_text="moving average crossover strategy",
            output_text="Moving Average Crossover Strategy:\n\nSetup:\n- Short-term MA (e.g., 50-day)\n- Long-term MA (e.g., 200-day)\n\nSignals:\n- Golden Cross: Short MA crosses ABOVE long MA → BUY\n- Death Cross: Short MA crosses BELOW long MA → SELL\n\nExample with 50/200 MA:\nWhen 50-day > 200-day = Bullish trend\nWhen 50-day < 200-day = Bearish trend\n\nStrengths:\n- Captures trends\n- Reduces noise\n- Simple to implement\n\nWeaknesses:\n- Lagging indicator\n- Whipsaws in sideways markets\n- Late entry/exit",
            domain="finance",
            difficulty="medium",
            tags=["finance", "technical-analysis", "moving-average"]
        ),
        TrainingExample(
            input_text="rsi relative strength index interpretation",
            output_text="RSI (Relative Strength Index):\n\nScale: 0 to 100\nFormula: RSI = 100 - (100 / (1 + RS))\n\nInterpretation:\n- RSI > 70: Overbought (potential sell)\n- RSI < 30: Oversold (potential buy)\n- RSI 30-70: Neutral zone\n\nDivergences:\n- Bullish: Price makes lower low, RSI makes higher low\n- Bearish: Price makes higher high, RSI makes lower high\n\nExample:\nStock drops to $40, RSI at 25 (oversold)\n→ Potential buying opportunity\n\nCaution:\n- Oversold can stay oversold in downtrends\n- Use with other indicators (volume, trend)",
            domain="finance",
            difficulty="medium",
            tags=["finance", "technical-analysis", "rsi"]
        ),
        TrainingExample(
            input_text="calculate dividend yield",
            output_text="Dividend Yield = Annual Dividend / Stock Price\n\nExample:\n- Stock price: $50\n- Quarterly dividend: $0.50\n- Annual dividend: $0.50 × 4 = $2.00\n\nDividend Yield = $2.00 / $50 = 0.04 = 4%\n\nInterpretation:\n- 2-4%: Typical for stable companies\n- >6%: High yield (check sustainability)\n- 0%: Growth companies reinvest\n\nImportant metrics:\n- Payout ratio: Dividend/Earnings (<60% sustainable)\n- Dividend growth rate: 5-year history\n- Free cash flow covers dividend?",
            domain="finance",
            difficulty="easy",
            tags=["finance", "dividends", "yield"]
        ),
    ]
    
    @classmethod
    def get_training_data(cls) -> DomainTrainingData:
        return DomainTrainingData(
            domain="finance",
            examples=cls.EXAMPLES,
            validation_split=0.1
        )


class WebsiteBuildingTrainingData:
    """
    Website building domain-specific training data
    """
    
    EXAMPLES = [
        TrainingExample(
            input_text="create hero section for tech startup",
            output_text="Modern Hero Section:\n\nLayout:\n- Full viewport height (100vh)\n- Centered content\n- Large typography\n- CTA button\n\nHTML Structure:\n<section class=\"hero\">\n  <div class=\"hero-content\">\n    <h1>Transform Your Business</h1>\n    <p class=\"hero-subtitle\">AI-powered solutions for modern enterprises</p>\n    <div class=\"hero-cta\">\n      <button class=\"btn-primary\">Get Started</button>\n      <button class=\"btn-secondary\">Learn More</button>\n    </div>\n  </div>\n</section>\n\nCSS:\n.hero {\n  min-height: 100vh;\n  display: flex;\n  align-items: center;\n  justify-content: center;\n  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);\n  color: white;\n}\n\n.hero h1 {\n  font-size: 4rem;\n  margin-bottom: 1rem;\n}\n\n.hero-subtitle {\n  font-size: 1.5rem;\n  opacity: 0.9;\n}",
            domain="website",
            difficulty="easy",
            tags=["website", "hero", "layout", "css"]
        ),
        TrainingExample(
            input_text="responsive grid for product cards",
            output_text="Product Grid Layout:\n\nCSS Grid Solution:\n.products-grid {\n  display: grid;\n  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));\n  gap: 2rem;\n  padding: 2rem;\n}\n\n.product-card {\n  background: white;\n  border-radius: 12px;\n  box-shadow: 0 4px 6px rgba(0,0,0,0.1);\n  overflow: hidden;\n  transition: transform 0.3s;\n}\n\n.product-card:hover {\n  transform: translateY(-5px);\n  box-shadow: 0 8px 12px rgba(0,0,0,0.15);\n}\n\nBreakpoints:\n- Mobile: 1 column (auto-fit handles this)\n- Tablet: 2 columns\n- Desktop: 3-4 columns\n\nCard Structure:\n<div class=\"product-card\">\n  <img src=\"product.jpg\" alt=\"Product\">\n  <div class=\"card-content\">\n    <h3>Product Name</h3>\n    <p class=\"price\">$99.99</p>\n    <button>Add to Cart</button>\n  </div>\n</div>",
            domain="website",
            difficulty="medium",
            tags=["website", "grid", "responsive", "product"]
        ),
        TrainingExample(
            input_text="navigation with mobile hamburger menu",
            output_text="Responsive Navigation:\n\nHTML:\n<nav class=\"navbar\">\n  <div class=\"nav-brand\">Logo</div>\n  \n  <button class=\"nav-toggle\" aria-label=\"toggle navigation\">\n    <span class=\"hamburger\"></span>\n  </button>\n  \n  <ul class=\"nav-menu\">\n    <li><a href=\"#\">Home</a></li>\n    <li><a href=\"#\">About</a></li>\n    <li><a href=\"#\">Services</a></li>\n    <li><a href=\"#\">Contact</a></li>\n  </ul>\n</nav>\n\nCSS:\n.navbar {\n  display: flex;\n  justify-content: space-between;\n  align-items: center;\n  padding: 1rem 2rem;\n}\n\n.nav-menu {\n  display: flex;\n  gap: 2rem;\n  list-style: none;\n}\n\n.nav-toggle {\n  display: none;\n  background: none;\n  border: none;\n  cursor: pointer;\n}\n\n/* Mobile styles */\n@media (max-width: 768px) {\n  .nav-toggle {\n    display: block;\n  }\n  \n  .nav-menu {\n    position: fixed;\n    left: -100%;\n    top: 70px;\n    flex-direction: column;\n    width: 100%;\n    background: white;\n    transition: 0.3s;\n  }\n  \n  .nav-menu.active {\n    left: 0;\n  }\n}\n\nJavaScript:\nconst navToggle = document.querySelector('.nav-toggle');\nconst navMenu = document.querySelector('.nav-menu');\n\nnavToggle.addEventListener('click', () => {\n  navMenu.classList.toggle('active');\n});",
            domain="website",
            difficulty="medium",
            tags=["website", "navigation", "mobile", "responsive"]
        ),
        TrainingExample(
            input_text="contact form with validation",
            output_text="Contact Form with Validation:\n\nHTML:\n<form id=\"contact-form\" class=\"contact-form\">\n  <div class=\"form-group\">\n    <label for=\"name\">Name *</label>\n    <input type=\"text\" id=\"name\" name=\"name\" required>\n    <span class=\"error-message\"></span>\n  </div>\n  \n  <div class=\"form-group\">\n    <label for=\"email\">Email *</label>\n    <input type=\"email\" id=\"email\" name=\"email\" required>\n    <span class=\"error-message\"></span>\n  </div>\n  \n  <div class=\"form-group\">\n    <label for=\"message\">Message *</label>\n    <textarea id=\"message\" name=\"message\" rows=\"5\" required></textarea>\n  </div>\n  \n  <button type=\"submit\" class=\"btn-submit\">Send Message</button>\n</form>\n\nJavaScript Validation:\nconst form = document.getElementById('contact-form');\n\nform.addEventListener('submit', (e) => {\n  e.preventDefault();\n  \n  const name = document.getElementById('name').value.trim();\n  const email = document.getElementById('email').value.trim();\n  const message = document.getElementById('message').value.trim();\n  \n  // Validation\n  if (name.length < 2) {\n    showError('name', 'Name must be at least 2 characters');\n    return;\n  }\n  \n  if (!isValidEmail(email)) {\n    showError('email', 'Please enter a valid email');\n    return;\n  }\n  \n  // Submit form\n  submitForm({ name, email, message });\n});\n\nfunction isValidEmail(email) {\n  return /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email);\n}",
            domain="website",
            difficulty="medium",
            tags=["website", "form", "validation", "javascript"]
        ),
        TrainingExample(
            input_text="footer with social links and newsletter",
            output_text="Professional Footer:\n\nHTML:\n<footer class=\"site-footer\">\n  <div class=\"footer-container\">\n    <div class=\"footer-grid\">\n      \n      <div class=\"footer-brand\">\n        <h3>Company Name</h3>\n        <p>Building the future, one solution at a time.</p>\n        <div class=\"social-links\">\n          <a href=\"#\" aria-label=\"Facebook\"><i class=\"icon-facebook\"></i></a>\n          <a href=\"#\" aria-label=\"Twitter\"><i class=\"icon-twitter\"></i></a>\n          <a href=\"#\" aria-label=\"LinkedIn\"><i class=\"icon-linkedin\"></i></a>\n        </div>\n      </div>\n      \n      <div class=\"footer-links\">\n        <h4>Quick Links</h4>\n        <ul>\n          <li><a href=\"#\">About Us</a></li>\n          <li><a href=\"#\">Services</a></li>\n          <li><a href=\"#\">Portfolio</a></li>\n          <li><a href=\"#\">Contact</a></li>\n        </ul>\n      </div>\n      \n      <div class=\"footer-newsletter\">\n        <h4>Newsletter</h4>\n        <p>Subscribe for updates</p>\n        <form class=\"newsletter-form\">\n          <input type=\"email\" placeholder=\"Enter email\" required>\n          <button type=\"submit\">Subscribe</button>\n        </form>\n      </div>\n      \n    </div>\n    \n    <div class=\"footer-bottom\">\n      <p>&copy; 2024 Company Name. All rights reserved.</p>\n    </div>\n  </div>\n</footer>\n\nCSS:\n.site-footer {\n  background: #1a1a1a;\n  color: white;\n  padding: 4rem 0 2rem;\n}\n\n.footer-grid {\n  display: grid;\n  grid-template-columns: 2fr 1fr 1.5fr;\n  gap: 3rem;\n  margin-bottom: 3rem;\n}\n\n@media (max-width: 768px) {\n  .footer-grid {\n    grid-template-columns: 1fr;\n  }\n}",
            domain="website",
            difficulty="easy",
            tags=["website", "footer", "responsive", "newsletter"]
        ),
    ]
    
    @classmethod
    def get_training_data(cls) -> DomainTrainingData:
        return DomainTrainingData(
            domain="website",
            examples=cls.EXAMPLES,
            validation_split=0.1
        )


class GeneralTrainingData:
    """
    General conversation, reasoning, helpful assistant behavior
    """
    
    EXAMPLES = [
        TrainingExample(
            input_text="hello how are you",
            output_text="Hello! I'm doing well, thank you for asking. How can I help you today? Whether you need help with coding, math, financial analysis, building a website, or just want to chat, I'm here to assist!",
            domain="general",
            difficulty="easy",
            tags=["greeting", "conversation"]
        ),
        TrainingExample(
            input_text="what can you help me with",
            output_text="I can help you with a wide range of topics:\n\n1. **Programming**: Python, JavaScript, HTML/CSS, SQL, and more\n2. **STEM**: Math, physics, chemistry, statistics\n3. **Finance**: Investment analysis, stock valuation, portfolio management\n4. **Website Building**: Design, responsive layouts, components\n5. **General Questions**: Explanations, advice, problem-solving\n\nJust tell me what you'd like to work on, and I'll do my best to help!",
            domain="general",
            difficulty="easy",
            tags=["capabilities", "help"]
        ),
        TrainingExample(
            input_text="explain machine learning in simple terms",
            output_text="Machine Learning Explained Simply:\n\nThink of machine learning like teaching a child to recognize animals:\n\n1. **Show Examples**: You show the child many pictures of cats and dogs, pointing out the differences\n\n2. **Find Patterns**: The child learns that cats have pointed ears and whiskers, while dogs have longer snouts\n\n3. **Practice**: When shown a new picture, the child uses what they learned to guess if it's a cat or dog\n\n4. **Get Better**: Each correct or wrong answer helps them improve\n\n**In Computers:**\n- Instead of a child, it's an algorithm\n- Instead of pictures, it's data (numbers, text, images)\n- The computer finds patterns and makes predictions\n- It gets better with more examples\n\n**Real Examples:**\n- Email spam filters learn from emails you mark as spam\n- Netflix recommendations learn from what you watch\n- Voice assistants learn from millions of voice samples",
            domain="general",
            difficulty="easy",
            tags=["explanation", "machine-learning", "analogy"]
        ),
        TrainingExample(
            input_text="how to stay productive while working from home",
            output_text="Work From Home Productivity Tips:\n\n**Environment Setup:**\n- Designate a dedicated workspace\n- Ensure good lighting and ergonomic setup\n- Minimize distractions (close unnecessary tabs/apps)\n\n**Routine & Structure:**\n- Start at consistent time\n- Dress for work (not pajamas)\n- Take regular breaks (Pomodoro: 25min work, 5min break)\n\n**Communication:**\n- Over-communicate with team\n- Use video calls when possible\n- Set clear availability hours\n\n**Boundaries:**\n- Create physical separation from family/roommates\n- Set 'do not disturb' hours\n- End work at consistent time\n\n**Health:**\n- Take walks/stretch breaks\n- Stay hydrated\n- Set up for good posture\n\nThe key is creating separation between 'work mode' and 'home mode' even in the same space.",
            domain="general",
            difficulty="easy",
            tags=["productivity", "remote-work", "advice"]
        ),
        TrainingExample(
            input_text="what is blockchain technology",
            output_text="Blockchain Technology Explained:\n\n**Core Concept:**\nA digital ledger (record book) distributed across many computers, making it nearly impossible to alter past records.\n\n**How It Works:**\n\n1. **Block**: Contains data (transactions), timestamp, and unique code\n2. **Chain**: Each block references the previous block's code\n3. **Network**: Thousands of computers validate and store copies\n4. **Consensus**: All computers must agree before adding new blocks\n\n**Key Features:**\n\n- **Decentralized**: No single company controls it\n- **Transparent**: Everyone can see the history\n- **Immutable**: Once recorded, nearly impossible to change\n- **Secure**: Cryptography protects the data\n\n**Real Uses:**\n\n- **Cryptocurrency**: Bitcoin, Ethereum\n- **Supply Chain**: Track products from factory to store\n- **Smart Contracts**: Self-executing agreements\n- **Voting**: Secure, verifiable elections\n- **Identity**: Digital IDs that can't be forged\n\n**Analogy**: Like a shared Google Doc where everyone can see all changes, but no one can secretly edit past entries.",
            domain="general",
            difficulty="medium",
            tags=["explanation", "blockchain", "technology"]
        ),
    ]
    
    @classmethod
    def get_training_data(cls) -> DomainTrainingData:
        return DomainTrainingData(
            domain="general",
            examples=cls.EXAMPLES,
            validation_split=0.1
        )


# Export all training data
def get_all_training_data() -> Dict[str, DomainTrainingData]:
    """Get comprehensive training data for all domains"""
    return {
        "code": CodeTrainingData.get_training_data(),
        "stem": STEMTrainingData.get_training_data(),
        "finance": FinanceTrainingData.get_training_data(),
        "website": WebsiteBuildingTrainingData.get_training_data(),
        "general": GeneralTrainingData.get_training_data()
    }


if __name__ == "__main__":
    # Verify training data
    data = get_all_training_data()
    
    print("=" * 70)
    print("📚 COMPREHENSIVE TRAINING DATA SUMMARY")
    print("=" * 70)
    
    total_examples = 0
    for domain, training_data in data.items():
        train, val = training_data.split()
        count = len(training_data.examples)
        total_examples += count
        
        print(f"\n{domain.upper()}:")
        print(f"  Total examples: {count}")
        print(f"  Training: {len(train)}")
        print(f"  Validation: {len(val)}")
        
        # Show difficulty distribution
        easy = sum(1 for ex in training_data.examples if ex.difficulty == "easy")
        medium = sum(1 for ex in training_data.examples if ex.difficulty == "medium")
        hard = sum(1 for ex in training_data.examples if ex.difficulty == "hard")
        print(f"  Difficulty: Easy={easy}, Medium={medium}, Hard={hard}")
    
    print("\n" + "=" * 70)
    print(f"📊 TOTAL: {total_examples} high-quality training examples")
    print("=" * 70)
    print("✅ Ready for multi-domain LLM training!")
