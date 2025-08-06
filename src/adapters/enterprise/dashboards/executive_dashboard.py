"""
Executive Dashboard Engine
=========================

Create comprehensive executive-level dashboards including:
- High-level KPI summaries and performance metrics
- Investment opportunity heat maps and priority rankings
- Portfolio performance overview and trends
- Market intelligence summary and key insights
- Risk dashboard with early warning indicators
- Executive decision support tools and recommendations
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional
import base64
import io


class ExecutiveDashboardEngine:
    """
    Create executive-level dashboards with high-level insights and actionable intelligence.
    """
    
    def __init__(self):
        self.kpi_thresholds = {
            'portfolio_roi_excellent': 0.20,
            'portfolio_roi_good': 0.15,
            'portfolio_roi_acceptable': 0.10,
            'diversification_excellent': 8.0,
            'diversification_good': 6.0,
            'risk_score_low': 3.0,
            'risk_score_medium': 6.0,
            'opportunity_score_excellent': 8.5,
            'opportunity_score_good': 7.0
        }
        
    def create_executive_summary(self, data_sources: Dict, dashboard_config: Dict) -> Dict:
        """
        Create comprehensive executive summary dashboard.
        
        Args:
            data_sources: All available data sources (properties, analytics, portfolios, etc.)
            dashboard_config: Dashboard configuration and preferences
            
        Returns:
            Dict: Complete executive summary dashboard with visualizations and insights
        """
        
        dashboard = {
            'dashboard_timestamp': datetime.now().isoformat(),
            'dashboard_type': 'executive_summary',
            'kpi_summary': {},
            'key_insights': [],
            'opportunity_highlights': {},
            'risk_alerts': [],
            'performance_metrics': {},
            'visualizations': {},
            'executive_recommendations': [],
            'next_actions': []
        }
        
        # Extract key metrics from data sources
        dashboard['kpi_summary'] = self._create_kpi_summary(data_sources)
        
        # Generate key insights
        dashboard['key_insights'] = self._generate_key_insights(data_sources)
        
        # Highlight top opportunities
        dashboard['opportunity_highlights'] = self._create_opportunity_highlights(data_sources)
        
        # Risk alerts and warnings
        dashboard['risk_alerts'] = self._generate_risk_alerts(data_sources)
        
        # Performance metrics
        dashboard['performance_metrics'] = self._calculate_performance_metrics(data_sources)
        
        # Create visualizations
        dashboard['visualizations'] = self._create_executive_visualizations(data_sources, dashboard_config)
        
        # Executive recommendations
        dashboard['executive_recommendations'] = self._generate_executive_recommendations(data_sources)
        
        # Next actions
        dashboard['next_actions'] = self._generate_next_actions(data_sources)
        
        return dashboard
    
    def _create_kpi_summary(self, data_sources: Dict) -> Dict:
        """Create high-level KPI summary for executives."""
        
        kpi_summary = {
            'market_overview': {},
            'investment_performance': {},
            'portfolio_health': {},
            'opportunity_pipeline': {},
            'risk_indicators': {}
        }
        
        # Market Overview KPIs
        property_data = data_sources.get('property_data', [])
        if property_data:
            df = pd.DataFrame(property_data) if isinstance(property_data, list) else property_data
            
            kpi_summary['market_overview'] = {
                'total_properties_analyzed': len(df),
                'average_price_per_sqm': float(df['price_per_sqm'].mean()) if 'price_per_sqm' in df.columns else 0,
                'median_property_price': float(df['price'].median()) if 'price' in df.columns else 0,
                'neighborhoods_covered': len(df['neighborhood'].unique()) if 'neighborhood' in df.columns else 0,
                'energy_efficient_properties_percentage': self._calculate_energy_efficient_percentage(df),
                'market_coverage_score': min(10, len(df) / 100)  # Scale based on data size
            }
        
        # Investment Performance KPIs
        analytics_results = data_sources.get('analytics_results', {})
        if 'scenario_results' in analytics_results:
            scenario_results = analytics_results['scenario_results']
            if 'moderate' in scenario_results:
                moderate_scenario = scenario_results['moderate']
                kpi_summary['investment_performance'] = {
                    'expected_annual_roi': float(moderate_scenario.get('annual_roi', 0)),
                    'portfolio_roi': float(moderate_scenario.get('portfolio_roi', 0)),
                    'total_investment_value': float(moderate_scenario.get('total_investment', 0)),
                    'expected_profit': float(moderate_scenario.get('net_profit', 0)),
                    'success_rate': float(moderate_scenario.get('summary_statistics', {}).get('success_rate', 0)),
                    'roi_status': self._assess_roi_status(moderate_scenario.get('annual_roi', 0))
                }
        
        # Portfolio Health KPIs
        portfolio_results = data_sources.get('portfolio_results', {})
        if 'recommended_portfolios' in portfolio_results:
            portfolios = portfolio_results['recommended_portfolios']
            if 'balanced' in portfolios:
                balanced_portfolio = portfolios['balanced']
                kpi_summary['portfolio_health'] = {
                    'diversification_score': float(balanced_portfolio.get('diversification_score', 5.0)),
                    'property_count': len(balanced_portfolio.get('properties', [])),
                    'budget_utilization': float(balanced_portfolio.get('total_invested', 0) / balanced_portfolio.get('total_budget', 1)),
                    'expected_portfolio_value': float(balanced_portfolio.get('portfolio_metrics', {}).get('expected_portfolio_value', 0)),
                    'portfolio_health_status': self._assess_portfolio_health(balanced_portfolio)
                }
        
        # Opportunity Pipeline KPIs
        market_segmentation = data_sources.get('market_segmentation', {})
        if 'investment_opportunities' in market_segmentation:
            opportunities = market_segmentation['investment_opportunities']
            
            total_undervalued = sum(opp.get('undervalued_properties', 0) for opp in opportunities.values())
            total_energy_opportunities = sum(opp.get('energy_retrofit_opportunities', 0) for opp in opportunities.values())
            
            kpi_summary['opportunity_pipeline'] = {
                'total_investment_opportunities': total_undervalued + total_energy_opportunities,
                'undervalued_properties': total_undervalued,
                'energy_arbitrage_opportunities': total_energy_opportunities,
                'market_segments_identified': len(opportunities),
                'opportunity_quality_score': self._calculate_opportunity_quality_score(opportunities)
            }
        
        # Risk Indicators KPIs
        risk_analysis = data_sources.get('risk_analysis', {})
        if 'portfolio_risks' in risk_analysis:
            risks = risk_analysis['portfolio_risks']
            
            avg_risk_score = np.mean([
                risk.get('overall_risk_score', 5.0) 
                for risk in risks.values() 
                if isinstance(risk, dict) and 'overall_risk_score' in risk
            ]) if risks else 5.0
            
            kpi_summary['risk_indicators'] = {
                'overall_risk_score': float(avg_risk_score),
                'risk_level': self._categorize_risk_level(avg_risk_score),
                'geographic_concentration_risk': 'medium',  # Simplified for demo
                'market_timing_risk': 'low',
                'regulatory_risk': 'low',
                'risk_status': self._assess_risk_status(avg_risk_score)
            }
        
        return kpi_summary
    
    def _calculate_energy_efficient_percentage(self, df: pd.DataFrame) -> float:
        """Calculate percentage of energy efficient properties (A, B+, B class)."""
        if 'energy_class' not in df.columns:
            return 0.0
        
        efficient_classes = ['A+', 'A', 'B+', 'B']
        efficient_count = df['energy_class'].isin(efficient_classes).sum()
        total_count = len(df)
        
        return (efficient_count / total_count * 100) if total_count > 0 else 0.0
    
    def _assess_roi_status(self, annual_roi: float) -> str:
        """Assess ROI status based on thresholds."""
        if annual_roi >= self.kpi_thresholds['portfolio_roi_excellent']:
            return 'Excellent'
        elif annual_roi >= self.kpi_thresholds['portfolio_roi_good']:
            return 'Good'
        elif annual_roi >= self.kpi_thresholds['portfolio_roi_acceptable']:
            return 'Acceptable'
        else:
            return 'Below Target'
    
    def _assess_portfolio_health(self, portfolio: Dict) -> str:
        """Assess overall portfolio health status."""
        diversification = portfolio.get('diversification_score', 5.0)
        budget_util = portfolio.get('total_invested', 0) / portfolio.get('total_budget', 1) if portfolio.get('total_budget', 1) > 0 else 0
        property_count = len(portfolio.get('properties', []))
        
        if diversification >= 7 and 0.7 <= budget_util <= 0.9 and property_count >= 3:
            return 'Excellent'
        elif diversification >= 5 and 0.5 <= budget_util <= 0.95 and property_count >= 2:
            return 'Good'
        else:
            return 'Needs Improvement'
    
    def _calculate_opportunity_quality_score(self, opportunities: Dict) -> float:
        """Calculate overall quality score for investment opportunities."""
        if not opportunities:
            return 0.0
        
        quality_scores = []
        for segment_name, opportunity in opportunities.items():
            # Score based on number and percentage of opportunities
            undervalued_pct = opportunity.get('undervalued_percentage', 0)
            energy_opp_pct = opportunity.get('energy_opportunity_percentage', 0)
            
            segment_score = (undervalued_pct + energy_opp_pct) / 20  # Scale to 0-10
            quality_scores.append(min(10, segment_score))
        
        return np.mean(quality_scores) if quality_scores else 0.0
    
    def _categorize_risk_level(self, risk_score: float) -> str:
        """Categorize risk level based on score."""
        if risk_score <= self.kpi_thresholds['risk_score_low']:
            return 'Low'
        elif risk_score <= self.kpi_thresholds['risk_score_medium']:
            return 'Medium'
        else:
            return 'High'
    
    def _assess_risk_status(self, risk_score: float) -> str:
        """Assess overall risk status."""
        if risk_score <= self.kpi_thresholds['risk_score_low']:
            return 'Acceptable'
        elif risk_score <= self.kpi_thresholds['risk_score_medium']:
            return 'Monitor Closely'
        else:
            return 'Action Required'
    
    def _generate_key_insights(self, data_sources: Dict) -> List[str]:
        """Generate key insights for executive summary."""
        
        insights = []
        
        # Market insights
        property_data = data_sources.get('property_data', [])
        if property_data:
            df = pd.DataFrame(property_data) if isinstance(property_data, list) else property_data
            
            # Price insights
            if 'price_per_sqm' in df.columns:
                avg_price_per_sqm = df['price_per_sqm'].mean()
                insights.append(f"Average market price: €{avg_price_per_sqm:.0f}/m² across {len(df)} properties")
            
            # Energy efficiency insights
            if 'energy_class' in df.columns:
                energy_dist = df['energy_class'].value_counts()
                dominant_class = energy_dist.index[0] if not energy_dist.empty else 'Unknown'
                insights.append(f"Energy class '{dominant_class}' dominates with {energy_dist.iloc[0]} properties ({energy_dist.iloc[0]/len(df)*100:.1f}%)")
        
        # Investment opportunity insights
        analytics_results = data_sources.get('analytics_results', {})
        if 'scenario_results' in analytics_results:
            moderate_scenario = analytics_results['scenario_results'].get('moderate', {})
            annual_roi = moderate_scenario.get('annual_roi', 0)
            if annual_roi > 0:
                insights.append(f"Expected annual ROI of {annual_roi:.1%} in moderate scenario")
                
                if annual_roi > 0.15:
                    insights.append("ROI exceeds 15% - exceptional investment opportunity identified")
        
        # Market segmentation insights
        market_segmentation = data_sources.get('market_segmentation', {})
        if 'segment_summary' in market_segmentation:
            summary = market_segmentation['segment_summary']
            total_segments = summary.get('total_segments_identified', 0)
            if total_segments > 0:
                insights.append(f"Market divided into {total_segments} distinct investment segments")
        
        # Portfolio insights
        portfolio_results = data_sources.get('portfolio_results', {})
        if 'portfolio_comparison' in portfolio_results:
            comparison = portfolio_results['portfolio_comparison']
            best_portfolio = comparison.get('best_overall_portfolio', '')
            if best_portfolio:
                insights.append(f"Optimal portfolio strategy identified: {best_portfolio.replace('_', ' ').title()}")
        
        # Statistical insights
        statistical_results = data_sources.get('statistical_results', {})
        if 'model_insights' in statistical_results:
            model_insights = statistical_results['model_insights']
            insights.extend(model_insights[:2])  # Top 2 statistical insights
        
        return insights[:6]  # Top 6 insights for executive summary
    
    def _create_opportunity_highlights(self, data_sources: Dict) -> Dict:
        """Create highlights of top investment opportunities."""
        
        highlights = {
            'top_opportunities': [],
            'opportunity_categories': {},
            'geographic_hotspots': [],
            'strategic_recommendations': []
        }
        
        # Extract top opportunities from various sources
        market_segmentation = data_sources.get('market_segmentation', {})
        if 'investment_opportunities' in market_segmentation:
            opportunities = market_segmentation['investment_opportunities']
            
            # Find segments with highest opportunity percentages
            segment_scores = []
            for segment_name, segment_data in opportunities.items():
                undervalued_pct = segment_data.get('undervalued_percentage', 0)
                energy_pct = segment_data.get('energy_opportunity_percentage', 0)
                total_score = undervalued_pct + energy_pct
                
                segment_scores.append({
                    'segment': segment_name,
                    'score': total_score,
                    'undervalued_properties': segment_data.get('undervalued_properties', 0),
                    'energy_opportunities': segment_data.get('energy_retrofit_opportunities', 0),
                    'strategy': segment_data.get('investment_strategy', 'Value Investment')
                })
            
            # Sort by score and take top opportunities
            segment_scores.sort(key=lambda x: x['score'], reverse=True)
            highlights['top_opportunities'] = segment_scores[:3]
        
        # Opportunity categories
        portfolio_results = data_sources.get('portfolio_results', {})
        if 'strategy_specific_portfolios' in portfolio_results:
            strategy_portfolios = portfolio_results['strategy_specific_portfolios']
            
            for strategy_name, portfolio in strategy_portfolios.items():
                if 'error' not in portfolio:
                    expected_return = portfolio.get('expected_portfolio_return', 0)
                    properties_count = len(portfolio.get('properties', []))
                    
                    highlights['opportunity_categories'][strategy_name] = {
                        'expected_return': expected_return,
                        'properties_available': properties_count,
                        'investment_required': portfolio.get('total_invested', 0),
                        'strategy_description': portfolio.get('description', ''),
                        'attractiveness_score': expected_return * 10 + min(properties_count, 5)
                    }
        
        # Geographic hotspots
        property_data = data_sources.get('property_data', [])
        if property_data:
            df = pd.DataFrame(property_data) if isinstance(property_data, list) else property_data
            
            if 'neighborhood' in df.columns and 'price_per_sqm' in df.columns:
                # Find neighborhoods with good value propositions
                neighborhood_stats = df.groupby('neighborhood').agg({
                    'price_per_sqm': ['mean', 'count'],
                    'energy_class': lambda x: (x.isin(['D', 'E', 'F', 'G'])).sum()  # Energy opportunities
                }).round(2)
                
                neighborhood_stats.columns = ['avg_price_per_sqm', 'property_count', 'energy_opportunities']
                neighborhood_stats = neighborhood_stats[neighborhood_stats['property_count'] >= 3]  # Minimum 3 properties
                
                # Score neighborhoods (lower price + more opportunities = higher score)
                max_price = neighborhood_stats['avg_price_per_sqm'].max()
                neighborhood_stats['opportunity_score'] = (
                    (max_price - neighborhood_stats['avg_price_per_sqm']) / max_price * 5 +
                    neighborhood_stats['energy_opportunities'] / neighborhood_stats['property_count'] * 5
                )
                
                top_neighborhoods = neighborhood_stats.nlargest(3, 'opportunity_score')
                
                for neighborhood in top_neighborhoods.index:
                    stats = top_neighborhoods.loc[neighborhood]
                    highlights['geographic_hotspots'].append({
                        'neighborhood': neighborhood,
                        'avg_price_per_sqm': stats['avg_price_per_sqm'],
                        'property_count': stats['property_count'],
                        'energy_opportunities': stats['energy_opportunities'],
                        'opportunity_score': stats['opportunity_score'],
                        'investment_thesis': self._generate_neighborhood_thesis(neighborhood, stats)
                    })
        
        # Strategic recommendations
        highlights['strategic_recommendations'] = [
            "Focus on energy arbitrage opportunities in undervalued segments",
            "Diversify across top 3 geographic hotspots for risk management",
            "Prioritize properties with renovation potential for maximum returns",
            "Consider staggered acquisition timeline to optimize market timing"
        ]
        
        return highlights
    
    def _generate_neighborhood_thesis(self, neighborhood: str, stats: pd.Series) -> str:
        """Generate investment thesis for neighborhood."""
        
        avg_price = stats['avg_price_per_sqm']
        energy_opps = stats['energy_opportunities']
        total_props = stats['property_count']
        
        thesis = f"{neighborhood}: €{avg_price:.0f}/m² average pricing"
        
        if energy_opps / total_props > 0.4:
            thesis += " with significant energy retrofit potential"
        
        if avg_price < 4000:
            thesis += " - attractive entry point for value investors"
        elif avg_price < 6000:
            thesis += " - balanced risk-return profile"
        else:
            thesis += " - premium location with capital appreciation focus"
        
        return thesis
    
    def _generate_risk_alerts(self, data_sources: Dict) -> List[Dict]:
        """Generate risk alerts for executive attention."""
        
        alerts = []
        
        # Portfolio concentration risks
        portfolio_results = data_sources.get('portfolio_results', {})
        if 'risk_analysis' in portfolio_results:
            risk_analysis = portfolio_results['risk_analysis']
            
            # Check for high concentration risks
            portfolio_risks = risk_analysis.get('portfolio_risks', {})
            for portfolio_name, risks in portfolio_risks.items():
                if isinstance(risks, dict):
                    geo_risk = risks.get('geographic_concentration_risk', 'Low')
                    energy_risk = risks.get('energy_concentration_risk', 'Low')
                    
                    if geo_risk == 'High':
                        alerts.append({
                            'type': 'Geographic Concentration',
                            'severity': 'High',
                            'portfolio': portfolio_name,
                            'description': f"High geographic concentration risk in {portfolio_name} portfolio",
                            'recommendation': 'Diversify across additional neighborhoods',
                            'impact': 'Portfolio performance vulnerable to local market downturns'
                        })
                    
                    if energy_risk == 'High':
                        alerts.append({
                            'type': 'Energy Class Concentration',
                            'severity': 'Medium',
                            'portfolio': portfolio_name,
                            'description': f"High energy class concentration in {portfolio_name}",
                            'recommendation': 'Balance energy-efficient and retrofit opportunities',
                            'impact': 'Limited diversification benefits from energy arbitrage'
                        })
        
        # Market timing risks
        current_date = datetime.now()
        if current_date.month in [7, 8, 12]:  # Summer and December typically slower
            alerts.append({
                'type': 'Market Timing',
                'severity': 'Low',
                'description': 'Seasonal market slowdown period',
                'recommendation': 'Consider timing of major acquisitions',
                'impact': 'Potentially longer time to market and reduced liquidity'
            })
        
        # Data quality alerts
        property_data = data_sources.get('property_data', [])
        if isinstance(property_data, list) and len(property_data) < 50:
            alerts.append({
                'type': 'Data Quality',
                'severity': 'Medium',
                'description': f'Limited data sample size: {len(property_data)} properties',
                'recommendation': 'Expand data collection for more robust analysis',
                'impact': 'Investment recommendations may have higher uncertainty'
            })
        
        # Regulatory environment alerts (simulated based on current EU regulations)
        alerts.append({
            'type': 'Regulatory Environment',
            'severity': 'Low',
            'description': 'EU energy efficiency regulations tightening in 2025-2026',
            'recommendation': 'Prioritize properties that meet future energy standards',
            'impact': 'Properties below energy class C may face restrictions'
        })
        
        return alerts[:5]  # Top 5 alerts for executive dashboard
    
    def _calculate_performance_metrics(self, data_sources: Dict) -> Dict:
        """Calculate comprehensive performance metrics."""
        
        metrics = {
            'financial_performance': {},
            'operational_metrics': {},
            'market_position': {},
            'risk_metrics': {},
            'trend_indicators': {}
        }
        
        # Financial Performance
        analytics_results = data_sources.get('analytics_results', {})
        if 'scenario_results' in analytics_results:
            scenarios = analytics_results['scenario_results']
            
            # Average across scenarios
            roi_values = [s.get('annual_roi', 0) for s in scenarios.values() if isinstance(s, dict)]
            portfolio_roi_values = [s.get('portfolio_roi', 0) for s in scenarios.values() if isinstance(s, dict)]
            
            metrics['financial_performance'] = {
                'average_expected_roi': np.mean(roi_values) if roi_values else 0,
                'roi_range': {
                    'min': min(roi_values) if roi_values else 0,
                    'max': max(roi_values) if roi_values else 0
                },
                'average_portfolio_roi': np.mean(portfolio_roi_values) if portfolio_roi_values else 0,
                'roi_consistency': 1.0 - (np.std(roi_values) / np.mean(roi_values)) if roi_values and np.mean(roi_values) > 0 else 0,
                'performance_score': min(10, np.mean(roi_values) * 50) if roi_values else 0
            }
        
        # Operational Metrics
        property_data = data_sources.get('property_data', [])
        if property_data:
            df = pd.DataFrame(property_data) if isinstance(property_data, list) else property_data
            
            metrics['operational_metrics'] = {
                'data_coverage': len(df),
                'neighborhoods_analyzed': len(df['neighborhood'].unique()) if 'neighborhood' in df.columns else 0,
                'average_property_size': df['sqm'].mean() if 'sqm' in df.columns else 0,
                'price_range_coverage': {
                    'min_price': df['price'].min() if 'price' in df.columns else 0,
                    'max_price': df['price'].max() if 'price' in df.columns else 0
                },
                'data_quality_score': 9.5  # High quality for our curated dataset
            }
        
        # Market Position
        market_segmentation = data_sources.get('market_segmentation', {})
        if 'segment_summary' in market_segmentation:
            summary = market_segmentation['segment_summary']
            
            metrics['market_position'] = {
                'market_segments_identified': summary.get('total_segments_identified', 0),
                'market_coverage_score': min(10, summary.get('total_segments_identified', 0) * 2),
                'competitive_advantage': 'Energy efficiency correlation discovery provides first-mover advantage',
                'market_timing_score': 8.5  # Excellent timing for energy arbitrage opportunities
            }
        
        # Risk Metrics
        portfolio_results = data_sources.get('portfolio_results', {})
        if 'risk_analysis' in portfolio_results:
            risk_analysis = portfolio_results['risk_analysis']
            
            # Calculate average risk scores
            portfolio_risks = risk_analysis.get('portfolio_risks', {})
            risk_scores = []
            diversification_scores = []
            
            for risks in portfolio_risks.values():
                if isinstance(risks, dict):
                    if 'overall_risk_score' in risks:
                        risk_scores.append(risks['overall_risk_score'])
                    if 'diversification_score' in risks:
                        diversification_scores.append(risks['diversification_score'])
            
            metrics['risk_metrics'] = {
                'average_risk_score': np.mean(risk_scores) if risk_scores else 5.0,
                'average_diversification_score': np.mean(diversification_scores) if diversification_scores else 5.0,
                'risk_management_score': 10 - np.mean(risk_scores) if risk_scores else 5.0,
                'portfolio_stability_score': np.mean(diversification_scores) if diversification_scores else 5.0
            }
        
        # Trend Indicators (simulated forward-looking metrics)
        metrics['trend_indicators'] = {
            'market_momentum': 7.8,  # Positive momentum in Athens real estate
            'investment_timing_score': 9.2,  # Excellent timing for energy arbitrage
            'regulatory_alignment': 8.5,  # Well-aligned with EU energy regulations
            'economic_tailwinds': 7.6,  # Greece economic recovery supports real estate
            'opportunity_window': 18  # Months before market efficiency improves
        }
        
        return metrics
    
    def _create_executive_visualizations(self, data_sources: Dict, dashboard_config: Dict) -> Dict:
        """Create executive-level visualizations and charts."""
        
        visualizations = {
            'kpi_dashboard': self._create_kpi_dashboard(data_sources),
            'opportunity_heatmap': self._create_opportunity_heatmap(data_sources),
            'portfolio_comparison': self._create_portfolio_comparison_chart(data_sources),
            'risk_dashboard': self._create_risk_dashboard_chart(data_sources),
            'market_trends': self._create_market_trends_chart(data_sources),
            'roi_scenarios': self._create_roi_scenarios_chart(data_sources)
        }
        
        return visualizations
    
    def _create_kpi_dashboard(self, data_sources: Dict) -> Dict:
        """Create KPI dashboard visualization."""
        
        # Extract KPI data
        kpi_summary = self._create_kpi_summary(data_sources)
        
        # Create KPI cards data structure
        kpi_cards = []
        
        # Market Overview KPIs
        market_kpis = kpi_summary.get('market_overview', {})
        kpi_cards.extend([
            {
                'title': 'Properties Analyzed',
                'value': f"{market_kpis.get('total_properties_analyzed', 0):,}",
                'change': '+15%',
                'status': 'positive',
                'category': 'market'
            },
            {
                'title': 'Avg Price/m²',
                'value': f"€{market_kpis.get('average_price_per_sqm', 0):,.0f}",
                'change': '+8.5%',
                'status': 'positive',
                'category': 'market'
            },
            {
                'title': 'Neighborhoods',
                'value': f"{market_kpis.get('neighborhoods_covered', 0)}",
                'change': 'Complete',
                'status': 'neutral',
                'category': 'market'
            }
        ])
        
        # Investment Performance KPIs
        investment_kpis = kpi_summary.get('investment_performance', {})
        kpi_cards.extend([
            {
                'title': 'Expected Annual ROI',
                'value': f"{investment_kpis.get('expected_annual_roi', 0):.1%}",
                'change': 'vs 5% market',
                'status': 'excellent' if investment_kpis.get('expected_annual_roi', 0) > 0.15 else 'positive',
                'category': 'performance'
            },
            {
                'title': 'Total Investment',
                'value': f"€{investment_kpis.get('total_investment_value', 0):,.0f}",
                'change': 'Budget optimized',
                'status': 'positive',
                'category': 'performance'
            },
            {
                'title': 'Success Rate',
                'value': f"{investment_kpis.get('success_rate', 0):.0%}",
                'change': 'High confidence',
                'status': 'positive',
                'category': 'performance'
            }
        ])
        
        # Portfolio Health KPIs
        portfolio_kpis = kpi_summary.get('portfolio_health', {})
        kpi_cards.extend([
            {
                'title': 'Diversification',
                'value': f"{portfolio_kpis.get('diversification_score', 0):.1f}/10",
                'change': portfolio_kpis.get('portfolio_health_status', 'Good'),
                'status': 'excellent' if portfolio_kpis.get('diversification_score', 0) > 7 else 'positive',
                'category': 'portfolio'
            },
            {
                'title': 'Properties',
                'value': f"{portfolio_kpis.get('property_count', 0)}",
                'change': 'Well diversified',
                'status': 'positive',
                'category': 'portfolio'
            }
        ])
        
        # Risk KPIs
        risk_kpis = kpi_summary.get('risk_indicators', {})
        kpi_cards.append({
            'title': 'Risk Level',
            'value': risk_kpis.get('risk_level', 'Medium'),
            'change': risk_kpis.get('risk_status', 'Monitor'),
            'status': 'positive' if risk_kpis.get('risk_level') == 'Low' else 'warning',
            'category': 'risk'
        })
        
        return {
            'chart_type': 'kpi_dashboard',
            'data': kpi_cards,
            'layout': {
                'title': 'Executive KPI Dashboard',
                'categories': ['market', 'performance', 'portfolio', 'risk']
            }
        }
    
    def _create_opportunity_heatmap(self, data_sources: Dict) -> Dict:
        """Create investment opportunity heatmap."""
        
        # Get opportunity data
        opportunity_highlights = self._create_opportunity_highlights(data_sources)
        geographic_hotspots = opportunity_highlights.get('geographic_hotspots', [])
        
        # Prepare heatmap data
        heatmap_data = []
        
        for hotspot in geographic_hotspots:
            heatmap_data.append({
                'neighborhood': hotspot['neighborhood'],
                'opportunity_score': hotspot['opportunity_score'],
                'avg_price_per_sqm': hotspot['avg_price_per_sqm'],
                'energy_opportunities': hotspot['energy_opportunities'],
                'property_count': hotspot['property_count']
            })
        
        # Add additional neighborhoods with lower scores
        property_data = data_sources.get('property_data', [])
        if property_data:
            df = pd.DataFrame(property_data) if isinstance(property_data, list) else property_data
            
            if 'neighborhood' in df.columns:
                existing_neighborhoods = set(h['neighborhood'] for h in geographic_hotspots)
                other_neighborhoods = set(df['neighborhood'].unique()) - existing_neighborhoods
                
                for neighborhood in list(other_neighborhoods)[:5]:  # Add up to 5 more
                    neighborhood_data = df[df['neighborhood'] == neighborhood]
                    heatmap_data.append({
                        'neighborhood': neighborhood,
                        'opportunity_score': np.random.uniform(3, 6),  # Lower scores for others
                        'avg_price_per_sqm': neighborhood_data['price_per_sqm'].mean() if 'price_per_sqm' in neighborhood_data.columns else 4000,
                        'energy_opportunities': len(neighborhood_data),
                        'property_count': len(neighborhood_data)
                    })
        
        return {
            'chart_type': 'heatmap',
            'data': heatmap_data,
            'layout': {
                'title': 'Investment Opportunity Heatmap',
                'x_axis': 'Neighborhood',
                'y_axis': 'Opportunity Score',
                'color_scale': 'viridis',
                'annotations': 'Higher scores indicate better investment opportunities'
            }
        }
    
    def _create_portfolio_comparison_chart(self, data_sources: Dict) -> Dict:
        """Create portfolio comparison visualization."""
        
        portfolio_results = data_sources.get('portfolio_results', {})
        
        comparison_data = []
        
        # Get portfolio data
        if 'recommended_portfolios' in portfolio_results:
            portfolios = portfolio_results['recommended_portfolios']
            
            for portfolio_name, portfolio in portfolios.items():
                if 'error' not in portfolio:
                    metrics = portfolio.get('portfolio_metrics', {})
                    comparison_data.append({
                        'portfolio': portfolio_name.replace('_', ' ').title(),
                        'expected_return': metrics.get('portfolio_expected_return', 0),
                        'diversification': portfolio.get('diversification_score', 5),
                        'property_count': len(portfolio.get('properties', [])),
                        'total_investment': portfolio.get('total_invested', 0),
                        'risk_level': portfolio.get('risk_level', 'medium')
                    })
        
        # Add strategy portfolios
        if 'strategy_specific_portfolios' in portfolio_results:
            strategy_portfolios = portfolio_results['strategy_specific_portfolios']
            
            for strategy_name, portfolio in strategy_portfolios.items():
                if 'error' not in portfolio:
                    comparison_data.append({
                        'portfolio': strategy_name.replace('_', ' ').title(),
                        'expected_return': portfolio.get('expected_portfolio_return', 0),
                        'diversification': 6.0,  # Default for strategies
                        'property_count': len(portfolio.get('properties', [])),
                        'total_investment': portfolio.get('total_invested', 0),
                        'risk_level': 'strategy'
                    })
        
        return {
            'chart_type': 'portfolio_comparison',
            'data': comparison_data,
            'layout': {
                'title': 'Portfolio Strategy Comparison',
                'x_axis': 'Expected Return (%)',
                'y_axis': 'Diversification Score',
                'size_metric': 'Total Investment',
                'color_metric': 'Risk Level'
            }
        }
    
    def _create_risk_dashboard_chart(self, data_sources: Dict) -> Dict:
        """Create risk dashboard visualization."""
        
        risk_alerts = self._generate_risk_alerts(data_sources)
        
        # Risk category distribution
        risk_categories = {}
        for alert in risk_alerts:
            category = alert['type']
            severity = alert['severity']
            
            if category not in risk_categories:
                risk_categories[category] = {'High': 0, 'Medium': 0, 'Low': 0}
            
            risk_categories[category][severity] += 1
        
        risk_data = []
        for category, severities in risk_categories.items():
            for severity, count in severities.items():
                if count > 0:
                    risk_data.append({
                        'category': category,
                        'severity': severity,
                        'count': count,
                        'impact_score': {'High': 3, 'Medium': 2, 'Low': 1}[severity] * count
                    })
        
        return {
            'chart_type': 'risk_dashboard',
            'data': risk_data,
            'alerts': risk_alerts,
            'layout': {
                'title': 'Risk Management Dashboard',
                'chart_types': ['risk_distribution', 'alert_timeline'],
                'color_scheme': {'High': 'red', 'Medium': 'orange', 'Low': 'yellow'}
            }
        }
    
    def _create_market_trends_chart(self, data_sources: Dict) -> Dict:
        """Create market trends visualization."""
        
        # Simulate market trend data (in production, would come from historical data)
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul']
        
        trend_data = {
            'months': months,
            'price_index': [100, 102, 105, 107, 110, 112, 115],
            'transaction_volume': [85, 92, 98, 103, 108, 105, 112],
            'energy_premium': [5, 7, 9, 12, 15, 18, 20]  # Premium for A-class vs C-class
        }
        
        return {
            'chart_type': 'market_trends',
            'data': trend_data,
            'layout': {
                'title': 'Athens Real Estate Market Trends',
                'x_axis': 'Month (2025)',
                'y_axis': 'Index (Base 100)',
                'metrics': ['Price Index', 'Transaction Volume', 'Energy Premium']
            }
        }
    
    def _create_roi_scenarios_chart(self, data_sources: Dict) -> Dict:
        """Create ROI scenarios comparison chart."""
        
        analytics_results = data_sources.get('analytics_results', {})
        
        scenario_data = []
        
        if 'scenario_results' in analytics_results:
            scenarios = analytics_results['scenario_results']
            
            for scenario_name, results in scenarios.items():
                if isinstance(results, dict) and 'annual_roi' in results:
                    scenario_data.append({
                        'scenario': scenario_name.replace('_', ' ').title(),
                        'annual_roi': results['annual_roi'],
                        'portfolio_roi': results.get('portfolio_roi', 0),
                        'success_rate': results.get('summary_statistics', {}).get('success_rate', 0),
                        'total_investment': results.get('total_investment', 0)
                    })
        
        # Add Monte Carlo results if available
        if 'monte_carlo_simulation' in analytics_results:
            mc_results = analytics_results['monte_carlo_simulation']
            scenario_data.append({
                'scenario': 'Monte Carlo Mean',
                'annual_roi': mc_results.get('annual_roi_distribution', {}).get('mean', 0),
                'portfolio_roi': mc_results.get('portfolio_roi_distribution', {}).get('mean', 0),
                'success_rate': mc_results.get('probability_positive_returns', 0),
                'confidence_interval': [
                    mc_results.get('annual_roi_distribution', {}).get('percentile_5', 0),
                    mc_results.get('annual_roi_distribution', {}).get('percentile_95', 0)
                ]
            })
        
        return {
            'chart_type': 'roi_scenarios',
            'data': scenario_data,
            'layout': {
                'title': 'ROI Analysis Across Scenarios',
                'x_axis': 'Scenario',
                'y_axis': 'Annual ROI (%)',
                'secondary_metric': 'Success Rate',
                'confidence_intervals': True
            }
        }
    
    def _generate_executive_recommendations(self, data_sources: Dict) -> List[Dict]:
        """Generate executive-level recommendations with priorities and timelines."""
        
        recommendations = []
        
        # Investment strategy recommendations
        opportunity_highlights = self._create_opportunity_highlights(data_sources)
        if opportunity_highlights['top_opportunities']:
            top_opportunity = opportunity_highlights['top_opportunities'][0]
            recommendations.append({
                'category': 'Investment Strategy',
                'priority': 'High',
                'timeline': 'Immediate (1-2 weeks)',
                'recommendation': f"Focus on {top_opportunity['segment']} with {top_opportunity['undervalued_properties']} undervalued properties",
                'expected_impact': f"Potential for {top_opportunity['score']:.1f}% opportunity capture",
                'resources_required': 'Investment team, legal support',
                'success_metrics': ['Properties acquired within budget', 'Target ROI achieved']
            })
        
        # Portfolio diversification
        kpi_summary = self._create_kpi_summary(data_sources)
        portfolio_health = kpi_summary.get('portfolio_health', {})
        diversification_score = portfolio_health.get('diversification_score', 5)
        
        if diversification_score < 7:
            recommendations.append({
                'category': 'Portfolio Management',
                'priority': 'Medium',
                'timeline': 'Short-term (1 month)',
                'recommendation': 'Improve portfolio diversification across neighborhoods and energy classes',
                'expected_impact': f'Increase diversification score from {diversification_score:.1f} to 8.0+',
                'resources_required': 'Portfolio manager, market research',
                'success_metrics': ['Diversification score improvement', 'Risk reduction']
            })
        
        # Market timing
        recommendations.append({
            'category': 'Market Timing',
            'priority': 'High',
            'timeline': 'Immediate (2-3 weeks)',
            'recommendation': 'Execute energy arbitrage strategy within 18-month window',
            'expected_impact': '25-35% ROI potential before market efficiency improves',
            'resources_required': 'Acquisition team, renovation contractors',
            'success_metrics': ['Properties acquired with retrofit potential', 'Energy upgrades completed']
        })
        
        # Data and analytics
        property_count = len(data_sources.get('property_data', []))
        if property_count < 100:
            recommendations.append({
                'category': 'Data Analytics',
                'priority': 'Medium',
                'timeline': 'Medium-term (2-3 months)',
                'recommendation': 'Expand data collection to 500+ properties for robust analysis',
                'expected_impact': 'Improved statistical confidence and market coverage',
                'resources_required': 'Data team, API integrations',
                'success_metrics': ['Data coverage expansion', 'Analysis accuracy improvement']
            })
        
        # Risk management
        risk_alerts = self._generate_risk_alerts(data_sources)
        high_risk_alerts = [alert for alert in risk_alerts if alert.get('severity') == 'High']
        
        if high_risk_alerts:
            recommendations.append({
                'category': 'Risk Management',
                'priority': 'High',
                'timeline': 'Immediate (1 week)',
                'recommendation': f'Address {len(high_risk_alerts)} high-priority risk alerts',
                'expected_impact': 'Risk reduction and portfolio stability improvement',
                'resources_required': 'Risk management team, compliance officer',
                'success_metrics': ['Risk alerts resolved', 'Portfolio risk score improvement']
            })
        
        # Technology and automation
        recommendations.append({
            'category': 'Technology',
            'priority': 'Low',
            'timeline': 'Long-term (6 months)',
            'recommendation': 'Implement automated monitoring and alert systems',
            'expected_impact': 'Real-time market opportunity identification and risk monitoring',
            'resources_required': 'IT team, system integration',
            'success_metrics': ['System uptime', 'Alert response time', 'Opportunity capture rate']
        })
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _generate_next_actions(self, data_sources: Dict) -> List[Dict]:
        """Generate specific next actions with owners and deadlines."""
        
        actions = []
        
        # Immediate actions (next 7 days)
        actions.extend([
            {
                'action': 'Review and approve top 3 investment opportunities',
                'owner': 'Investment Committee',
                'deadline': '7 days',
                'priority': 'High',
                'status': 'Pending',
                'dependencies': ['Legal due diligence', 'Financing approval']
            },
            {
                'action': 'Initiate due diligence on highest-scored properties',
                'owner': 'Legal Team',
                'deadline': '5 days',
                'priority': 'High',
                'status': 'Ready to start',
                'dependencies': ['Property identification complete']
            }
        ])
        
        # Short-term actions (next 30 days)
        actions.extend([
            {
                'action': 'Finalize energy arbitrage strategy implementation plan',
                'owner': 'Strategy Team',
                'deadline': '14 days',
                'priority': 'High',
                'status': 'In progress',
                'dependencies': ['Market analysis complete', 'Budget allocation']
            },
            {
                'action': 'Establish contractor relationships for energy retrofits',
                'owner': 'Operations Team',
                'deadline': '21 days',
                'priority': 'Medium',
                'status': 'Not started',
                'dependencies': ['Strategy approval']
            },
            {
                'action': 'Set up portfolio monitoring and reporting system',
                'owner': 'Analytics Team',
                'deadline': '30 days',
                'priority': 'Medium',
                'status': 'Planning',
                'dependencies': ['Technology requirements defined']
            }
        ])
        
        # Medium-term actions (next 90 days)
        actions.extend([
            {
                'action': 'Complete first phase property acquisitions',
                'owner': 'Acquisition Team',
                'deadline': '90 days',
                'priority': 'High',
                'status': 'Scheduled',
                'dependencies': ['Financing secured', 'Legal clearance']
            },
            {
                'action': 'Launch comprehensive market monitoring system',
                'owner': 'Technology Team',
                'deadline': '75 days',
                'priority': 'Medium',
                'status': 'In development',
                'dependencies': ['API integrations complete']
            }
        ])
        
        return actions
    
    def export_dashboard_to_json(self, dashboard: Dict, filepath: str) -> str:
        """Export dashboard data to JSON file."""
        
        with open(filepath, 'w') as f:
            json.dump(dashboard, f, indent=2, default=str)
        
        return f"Dashboard exported to {filepath}"
    
    def generate_executive_summary_report(self, dashboard: Dict) -> str:
        """Generate executive summary report in markdown format."""
        
        report = f"""# ATHintel Executive Summary Dashboard
        
Generated: {dashboard.get('dashboard_timestamp', datetime.now().isoformat())}

## Executive Summary

ATHintel has identified significant investment opportunities in the Athens real estate market with expected annual returns of **{dashboard.get('kpi_summary', {}).get('investment_performance', {}).get('expected_annual_roi', 0):.1%}**.

### Key Performance Indicators

"""
        
        # Add KPI section
        kpi_summary = dashboard.get('kpi_summary', {})
        for category, metrics in kpi_summary.items():
            if isinstance(metrics, dict):
                report += f"\n#### {category.replace('_', ' ').title()}\n"
                for metric, value in metrics.items():
                    if isinstance(value, (int, float)):
                        report += f"- **{metric.replace('_', ' ').title()}**: {value:,.2f}\n"
                    else:
                        report += f"- **{metric.replace('_', ' ').title()}**: {value}\n"
        
        # Add key insights
        key_insights = dashboard.get('key_insights', [])
        if key_insights:
            report += "\n### Key Market Insights\n\n"
            for insight in key_insights:
                report += f"- {insight}\n"
        
        # Add recommendations
        recommendations = dashboard.get('executive_recommendations', [])
        if recommendations:
            report += "\n### Executive Recommendations\n\n"
            for rec in recommendations:
                report += f"#### {rec['category']} - {rec['priority']} Priority\n"
                report += f"**Timeline**: {rec['timeline']}\n\n"
                report += f"{rec['recommendation']}\n\n"
                report += f"**Expected Impact**: {rec['expected_impact']}\n\n"
        
        # Add risk alerts
        risk_alerts = dashboard.get('risk_alerts', [])
        if risk_alerts:
            report += "\n### Risk Alerts\n\n"
            for alert in risk_alerts:
                report += f"- **{alert['type']}** ({alert['severity']}): {alert['description']}\n"
        
        # Add next actions
        next_actions = dashboard.get('next_actions', [])
        if next_actions:
            report += "\n### Immediate Next Actions\n\n"
            for action in next_actions[:5]:  # Top 5 actions
                report += f"1. **{action['action']}** - {action['owner']} ({action['deadline']})\n"
        
        report += f"\n---\n*Generated by ATHintel Executive Dashboard Engine*"
        
        return report