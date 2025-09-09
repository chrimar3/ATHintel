#!/usr/bin/env python3
"""
🤖 CrewAI Real Estate Intelligence Workflow
Multi-agent system for comprehensive Athens real estate analysis

Agents:
1. Data Collector Agent - Scrapes and validates property data
2. Market Analyst Agent - Analyzes market trends and pricing
3. Investment Advisor Agent - Provides investment recommendations
4. Report Generator Agent - Creates comprehensive reports
"""

from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from typing import List, Dict, Any
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class RealEstateDataTool(BaseTool):
    """Tool for accessing real estate data"""
    name: str = "real_estate_data"
    description: str = "Access scraped Athens real estate data with prices, SQM, energy classes"
    
    def _run(self, query: str) -> str:
        """Load and return real estate data"""
        try:
            # Load our scraped data
            data_files = list(Path("data/processed").glob("athens_large_scale_real_data_*.json"))
            if not data_files:
                return "No real estate data found"
            
            latest_file = max(data_files, key=lambda x: x.stat().st_mtime)
            
            with open(latest_file, 'r') as f:
                data = json.load(f)
            
            # Filter based on query
            if "expensive" in query.lower():
                properties = sorted(data, key=lambda x: x['price'], reverse=True)[:10]
            elif "cheap" in query.lower():
                properties = sorted(data, key=lambda x: x['price'])[:10]
            elif "large" in query.lower():
                properties = sorted(data, key=lambda x: x['sqm'], reverse=True)[:10]
            elif "energy" in query.lower():
                properties = [p for p in data if p['energy_class'] in ['A+', 'A', 'B']][:10]
            else:
                properties = data[:10]
            
            return json.dumps(properties, indent=2)
            
        except Exception as e:
            return f"Error accessing data: {e}"

class MarketAnalysisTool(BaseTool):
    """Tool for market analysis calculations"""
    name: str = "market_analysis"
    description: str = "Perform market analysis on Athens real estate data"
    
    def _run(self, analysis_type: str) -> str:
        """Perform market analysis"""
        try:
            # Load data
            data_files = list(Path("data/processed").glob("athens_large_scale_real_data_*.json"))
            if not data_files:
                return "No data available for analysis"
            
            latest_file = max(data_files, key=lambda x: x.stat().st_mtime)
            with open(latest_file, 'r') as f:
                data = json.load(f)
            
            if analysis_type == "price_analysis":
                prices = [p['price'] for p in data if p['price']]
                return f"""Price Analysis:
- Average: €{sum(prices)/len(prices):,.0f}
- Min: €{min(prices):,.0f}
- Max: €{max(prices):,.0f}
- Median: €{sorted(prices)[len(prices)//2]:,.0f}
"""
            
            elif analysis_type == "neighborhood_analysis":
                neighborhoods = {}
                for prop in data:
                    neighborhood = prop['neighborhood']
                    if neighborhood not in neighborhoods:
                        neighborhoods[neighborhood] = []
                    neighborhoods[neighborhood].append(prop['price_per_sqm'])
                
                analysis = "Neighborhood Price/SQM Analysis:\n"
                for neighborhood, prices in neighborhoods.items():
                    if prices and len(prices) > 2:
                        avg_price = sum(prices) / len(prices)
                        analysis += f"- {neighborhood}: €{avg_price:.0f}/m² ({len(prices)} properties)\n"
                
                return analysis
            
            elif analysis_type == "energy_analysis":
                energy_classes = {}
                for prop in data:
                    energy = prop['energy_class']
                    if energy not in energy_classes:
                        energy_classes[energy] = []
                    energy_classes[energy].append(prop['price_per_sqm'])
                
                analysis = "Energy Class Price Analysis:\n"
                for energy, prices in energy_classes.items():
                    if prices:
                        avg_price = sum(prices) / len(prices)
                        analysis += f"- Class {energy}: €{avg_price:.0f}/m² ({len(prices)} properties)\n"
                
                return analysis
            
            return "Analysis type not recognized"
            
        except Exception as e:
            return f"Error in analysis: {e}"

def create_real_estate_crew():
    """Create CrewAI crew for real estate analysis"""
    
    # Define Agents
    data_collector = Agent(
        role='Real Estate Data Specialist',
        goal='Collect, validate and organize Athens real estate data',
        backstory="""You are an expert in Athens real estate data collection. 
        You have deep knowledge of property markets, data validation, and ensuring 
        data quality for investment analysis.""",
        tools=[RealEstateDataTool()],
        verbose=True
    )
    
    market_analyst = Agent(
        role='Athens Market Analyst',
        goal='Analyze Athens real estate market trends and provide insights',
        backstory="""You are a seasoned Athens real estate market analyst with 15+ years 
        of experience analyzing property trends, pricing patterns, and neighborhood dynamics. 
        You specialize in identifying investment opportunities and market inefficiencies.""",
        tools=[MarketAnalysisTool()],
        verbose=True
    )
    
    investment_advisor = Agent(
        role='Real Estate Investment Advisor',
        goal='Provide investment recommendations based on data and market analysis',
        backstory="""You are a professional real estate investment advisor specializing 
        in Athens properties. You excel at identifying undervalued properties, calculating 
        ROI potential, and providing actionable investment strategies.""",
        tools=[RealEstateDataTool(), MarketAnalysisTool()],
        verbose=True
    )
    
    report_generator = Agent(
        role='Investment Report Specialist',
        goal='Create comprehensive investment reports and presentations',
        backstory="""You are an expert at creating detailed, professional investment 
        reports that synthesize complex data into actionable insights. Your reports 
        are used by investors to make multi-million euro decisions.""",
        tools=[RealEstateDataTool(), MarketAnalysisTool()],
        verbose=True
    )
    
    # Define Tasks
    data_collection_task = Task(
        description="""Analyze the available Athens real estate data and provide a comprehensive 
        overview of the dataset. Include statistics on:
        - Total number of properties
        - Price ranges and distributions
        - Size (SQM) distributions
        - Energy class distributions
        - Geographic coverage
        Ensure data quality and identify any potential issues.""",
        agent=data_collector,
        output_file="reports/crewai/data_overview.md"
    )
    
    market_analysis_task = Task(
        description="""Perform comprehensive market analysis of Athens real estate:
        1. Price analysis by neighborhood
        2. Energy class impact on pricing
        3. Size vs price correlations
        4. Market trends and patterns
        5. Identify market inefficiencies
        Provide specific insights that could inform investment decisions.""",
        agent=market_analyst,
        output_file="reports/crewai/market_analysis.md"
    )
    
    investment_strategy_task = Task(
        description="""Based on the data and market analysis, develop specific investment 
        strategies for Athens real estate:
        1. Identify top 10 investment opportunities
        2. Recommend portfolio allocation strategies
        3. Calculate expected ROI for different strategies
        4. Assess risk factors and mitigation strategies
        5. Provide actionable next steps for investors
        Focus on properties with best value, growth potential, and energy efficiency.""",
        agent=investment_advisor,
        output_file="reports/crewai/investment_strategy.md"
    )
    
    comprehensive_report_task = Task(
        description="""Create a comprehensive executive investment report that synthesizes 
        all previous analysis into a professional document for decision makers:
        1. Executive summary with key findings
        2. Market overview and trends
        3. Detailed investment recommendations
        4. Risk assessment and mitigation
        5. Implementation timeline and next steps
        Make it investor-ready with specific property recommendations and financial projections.""",
        agent=report_generator,
        output_file="reports/crewai/executive_investment_report.md"
    )
    
    # Create Crew
    crew = Crew(
        agents=[data_collector, market_analyst, investment_advisor, report_generator],
        tasks=[data_collection_task, market_analysis_task, investment_strategy_task, comprehensive_report_task],
        verbose=2
    )
    
    return crew

def run_crewai_analysis():
    """Run the CrewAI analysis workflow"""
    
    logger.info("🤖 Starting CrewAI Real Estate Analysis Workflow")
    
    # Create output directory
    Path("reports/crewai").mkdir(parents=True, exist_ok=True)
    
    # Create and run crew
    crew = create_real_estate_crew()
    
    logger.info("🚀 Executing multi-agent analysis...")
    result = crew.kickoff()
    
    logger.info("✅ CrewAI analysis completed!")
    logger.info(f"📋 Reports generated in: reports/crewai/")
    
    return result

if __name__ == "__main__":
    result = run_crewai_analysis()
    print("🎉 CrewAI Real Estate Analysis Complete!")
    print(f"Result: {result}")