"""
Monte Carlo Investment Modeling - Advanced 2025 Financial Analytics

Implements sophisticated Monte Carlo simulations for real estate investment
analysis, including risk assessment, portfolio optimization, and scenario modeling.
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
import logging
from scipy import stats
from scipy.optimize import minimize
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from ..domain.entities import Property, Investment, Portfolio, PropertyType, InvestmentRisk
from ..ports.repositories import PropertyRepository, InvestmentRepository

logger = logging.getLogger(__name__)


class SimulationMethod(str, Enum):
    """Monte Carlo simulation methods"""
    BASIC = "basic"
    GEOMETRIC_BROWNIAN = "geometric_brownian"
    JUMP_DIFFUSION = "jump_diffusion"
    REGIME_SWITCHING = "regime_switching"
    COPULA_BASED = "copula_based"


class RiskMeasure(str, Enum):
    """Risk measurement methods"""
    VALUE_AT_RISK = "var"
    CONDITIONAL_VAR = "cvar"
    MAXIMUM_DRAWDOWN = "max_drawdown"
    SHARPE_RATIO = "sharpe_ratio"
    SORTINO_RATIO = "sortino_ratio"
    CALMAR_RATIO = "calmar_ratio"


@dataclass
class MarketParameters:
    """Market parameters for Monte Carlo simulation"""
    # Basic parameters
    annual_appreciation_mean: float = 0.05  # 5% annual appreciation
    annual_appreciation_std: float = 0.15   # 15% volatility
    
    # Rental parameters
    rental_yield_mean: float = 0.04         # 4% rental yield
    rental_yield_std: float = 0.01          # 1% rental yield volatility
    rental_growth_rate: float = 0.02        # 2% annual rental growth
    
    # Market cycle parameters
    cycle_length: float = 7.0               # 7-year market cycle
    boom_probability: float = 0.3           # 30% chance of boom
    bust_probability: float = 0.1           # 10% chance of bust
    
    # Economic parameters
    inflation_rate: float = 0.02            # 2% inflation
    risk_free_rate: float = 0.015           # 1.5% risk-free rate
    tax_rate: float = 0.24                  # 24% capital gains tax
    
    # Transaction costs
    buying_costs: float = 0.11              # 11% buying costs
    selling_costs: float = 0.06             # 6% selling costs
    maintenance_costs: float = 0.01         # 1% annual maintenance


@dataclass
class SimulationConfig:
    """Configuration for Monte Carlo simulations"""
    # Simulation parameters
    n_simulations: int = 10000
    n_years: int = 10
    time_step: float = 1/12  # Monthly steps
    random_seed: Optional[int] = 42
    
    # Methods and models
    simulation_method: SimulationMethod = SimulationMethod.GEOMETRIC_BROWNIAN
    correlation_modeling: bool = True
    regime_switching: bool = False
    
    # Market parameters
    market_params: MarketParameters = field(default_factory=MarketParameters)
    
    # Risk analysis
    confidence_levels: List[float] = field(default_factory=lambda: [0.95, 0.99])
    risk_measures: List[RiskMeasure] = field(default_factory=lambda: [
        RiskMeasure.VALUE_AT_RISK, 
        RiskMeasure.CONDITIONAL_VAR,
        RiskMeasure.SHARPE_RATIO
    ])
    
    # Portfolio optimization
    enable_portfolio_optimization: bool = True
    optimization_objective: str = "sharpe_ratio"  # "return", "risk", "sharpe_ratio"
    constraint_budget: Optional[float] = None
    constraint_max_weight: float = 0.3
    constraint_diversification: bool = True


@dataclass
class SimulationResults:
    """Results from Monte Carlo simulation"""
    # Basic results
    property_id: str
    simulation_paths: np.ndarray  # Shape: (n_simulations, n_time_steps)
    final_values: np.ndarray      # Final portfolio values
    
    # Statistical measures
    mean_return: float
    std_return: float
    median_return: float
    
    # Risk measures
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float
    max_drawdown: float
    
    # Performance metrics
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    
    # Probability metrics
    prob_positive_return: float
    prob_loss: float
    prob_extreme_loss: float  # > 20% loss
    
    # Time series results
    cash_flows: np.ndarray
    rental_income: np.ndarray
    capital_appreciation: np.ndarray
    total_returns: np.ndarray
    
    # Metadata
    simulation_config: SimulationConfig
    simulation_date: datetime = field(default_factory=datetime.now)


@dataclass
class PortfolioOptimizationResult:
    """Results from portfolio optimization"""
    optimal_weights: Dict[str, float]
    expected_return: float
    expected_risk: float
    sharpe_ratio: float
    
    # Efficient frontier
    efficient_frontier_returns: np.ndarray
    efficient_frontier_risks: np.ndarray
    
    # Individual asset metrics
    asset_returns: Dict[str, float]
    asset_risks: Dict[str, float]
    correlation_matrix: np.ndarray
    
    # Optimization metadata
    optimization_method: str
    constraints_satisfied: bool
    optimization_time: float


class MonteCarloSimulator:
    """
    Advanced Monte Carlo simulator for real estate investments
    """
    
    def __init__(self, config: Optional[SimulationConfig] = None):
        self.config = config or SimulationConfig()
        self.rng = np.random.RandomState(self.config.random_seed)
        
        logger.info("MonteCarloSimulator initialized", 
                   n_simulations=self.config.n_simulations,
                   method=self.config.simulation_method)
    
    async def simulate_investment(
        self, 
        property: Property, 
        investment_amount: Optional[float] = None
    ) -> SimulationResults:
        """
        Run Monte Carlo simulation for a single property investment
        """
        
        logger.info("Starting Monte Carlo simulation", property_id=property.property_id)
        
        if investment_amount is None:
            investment_amount = float(property.price)
        
        # Initialize simulation parameters
        n_steps = int(self.config.n_years / self.config.time_step)
        dt = self.config.time_step
        
        # Generate price paths
        price_paths = self._generate_price_paths(
            property, investment_amount, n_steps, dt
        )
        
        # Generate rental income paths
        rental_paths = self._generate_rental_paths(
            property, investment_amount, n_steps, dt
        )
        
        # Calculate total returns
        total_return_paths = self._calculate_total_returns(
            price_paths, rental_paths, investment_amount, dt
        )
        
        # Calculate final values
        final_values = total_return_paths[:, -1]
        
        # Calculate metrics
        results = self._calculate_simulation_metrics(
            property.property_id,
            price_paths,
            rental_paths,
            total_return_paths,
            final_values,
            investment_amount
        )
        
        logger.info("Monte Carlo simulation completed", 
                   property_id=property.property_id,
                   mean_return=results.mean_return,
                   sharpe_ratio=results.sharpe_ratio)
        
        return results
    
    async def simulate_portfolio(
        self, 
        properties: List[Property], 
        weights: Optional[Dict[str, float]] = None,
        total_budget: Optional[float] = None
    ) -> Dict[str, SimulationResults]:
        """
        Run Monte Carlo simulation for a portfolio of properties
        """
        
        logger.info("Starting portfolio Monte Carlo simulation", 
                   n_properties=len(properties))
        
        # Default to equal weights if not provided
        if weights is None:
            weight = 1.0 / len(properties)
            weights = {prop.property_id: weight for prop in properties}
        
        # Calculate individual investment amounts
        if total_budget:
            investment_amounts = {
                prop.property_id: total_budget * weights.get(prop.property_id, 0)
                for prop in properties
            }
        else:
            investment_amounts = {
                prop.property_id: float(prop.price) * weights.get(prop.property_id, 1.0)
                for prop in properties
            }
        
        # Run simulations for each property
        portfolio_results = {}
        correlation_data = []
        
        for prop in properties:
            investment_amount = investment_amounts[prop.property_id]
            
            if investment_amount > 0:
                results = await self.simulate_investment(prop, investment_amount)
                portfolio_results[prop.property_id] = results
                correlation_data.append(results.total_returns)
        
        # Add correlation analysis to results
        if len(correlation_data) > 1 and self.config.correlation_modeling:
            correlation_matrix = np.corrcoef(correlation_data)
            
            # Store correlation information in results
            for i, prop in enumerate(properties):
                if prop.property_id in portfolio_results:
                    # Add correlation info (simplified approach)
                    portfolio_results[prop.property_id].correlation_matrix = correlation_matrix
        
        return portfolio_results
    
    def _generate_price_paths(
        self, 
        property: Property, 
        initial_value: float, 
        n_steps: int, 
        dt: float
    ) -> np.ndarray:
        """Generate price paths using specified simulation method"""
        
        method = self.config.simulation_method
        
        if method == SimulationMethod.GEOMETRIC_BROWNIAN:
            return self._geometric_brownian_motion(initial_value, n_steps, dt)
        elif method == SimulationMethod.JUMP_DIFFUSION:
            return self._jump_diffusion_process(initial_value, n_steps, dt)
        elif method == SimulationMethod.REGIME_SWITCHING:
            return self._regime_switching_process(initial_value, n_steps, dt)
        else:
            # Default to geometric Brownian motion
            return self._geometric_brownian_motion(initial_value, n_steps, dt)
    
    def _geometric_brownian_motion(
        self, 
        initial_value: float, 
        n_steps: int, 
        dt: float
    ) -> np.ndarray:
        """Generate paths using geometric Brownian motion"""
        
        mu = self.config.market_params.annual_appreciation_mean
        sigma = self.config.market_params.annual_appreciation_std
        
        # Generate random shocks
        shocks = self.rng.normal(0, 1, (self.config.n_simulations, n_steps))
        
        # Calculate price paths
        paths = np.zeros((self.config.n_simulations, n_steps + 1))
        paths[:, 0] = initial_value
        
        for t in range(n_steps):
            drift = (mu - 0.5 * sigma**2) * dt
            diffusion = sigma * np.sqrt(dt) * shocks[:, t]
            
            paths[:, t + 1] = paths[:, t] * np.exp(drift + diffusion)
        
        return paths
    
    def _jump_diffusion_process(
        self, 
        initial_value: float, 
        n_steps: int, 
        dt: float
    ) -> np.ndarray:
        """Generate paths using Merton jump-diffusion model"""
        
        mu = self.config.market_params.annual_appreciation_mean
        sigma = self.config.market_params.annual_appreciation_std
        
        # Jump parameters
        jump_intensity = 0.1  # 0.1 jumps per year on average
        jump_mean = -0.05     # Average jump size -5%
        jump_std = 0.1        # Jump volatility 10%
        
        # Generate paths
        paths = np.zeros((self.config.n_simulations, n_steps + 1))
        paths[:, 0] = initial_value
        
        for t in range(n_steps):
            # Brownian motion component
            drift = (mu - 0.5 * sigma**2) * dt
            diffusion = sigma * np.sqrt(dt) * self.rng.normal(0, 1, self.config.n_simulations)
            
            # Jump component
            jump_occurs = self.rng.poisson(jump_intensity * dt, self.config.n_simulations)
            jump_sizes = np.where(
                jump_occurs > 0,
                self.rng.normal(jump_mean, jump_std, self.config.n_simulations),
                0
            )
            
            paths[:, t + 1] = paths[:, t] * np.exp(drift + diffusion + jump_sizes)
        
        return paths
    
    def _regime_switching_process(
        self, 
        initial_value: float, 
        n_steps: int, 
        dt: float
    ) -> np.ndarray:
        """Generate paths using regime-switching model"""
        
        # Define two regimes: bull and bear market
        regimes = {
            'bull': {'mu': 0.08, 'sigma': 0.12},
            'bear': {'mu': -0.02, 'sigma': 0.25}
        }
        
        # Transition probabilities
        transition_matrix = np.array([
            [0.95, 0.05],  # Bull to bull, bull to bear
            [0.2, 0.8]     # Bear to bull, bear to bear
        ])
        
        paths = np.zeros((self.config.n_simulations, n_steps + 1))
        paths[:, 0] = initial_value
        
        # Initialize regimes (start in bull market)
        current_regime = np.zeros(self.config.n_simulations, dtype=int)
        
        for t in range(n_steps):
            # Update regimes
            for i in range(self.config.n_simulations):
                current_regime[i] = self.rng.choice(
                    2, p=transition_matrix[current_regime[i]]
                )
            
            # Generate returns based on current regime
            for i, regime_idx in enumerate(current_regime):
                regime_name = 'bull' if regime_idx == 0 else 'bear'
                regime_params = regimes[regime_name]
                
                drift = (regime_params['mu'] - 0.5 * regime_params['sigma']**2) * dt
                diffusion = regime_params['sigma'] * np.sqrt(dt) * self.rng.normal()
                
                paths[i, t + 1] = paths[i, t] * np.exp(drift + diffusion)
        
        return paths
    
    def _generate_rental_paths(
        self, 
        property: Property, 
        initial_value: float, 
        n_steps: int, 
        dt: float
    ) -> np.ndarray:
        """Generate rental income paths"""
        
        # Base rental yield
        base_yield = self.config.market_params.rental_yield_mean
        yield_volatility = self.config.market_params.rental_yield_std
        rental_growth = self.config.market_params.rental_growth_rate
        
        # Adjust based on property characteristics
        yield_adjustment = self._calculate_yield_adjustment(property)
        adjusted_yield = base_yield + yield_adjustment
        
        # Generate rental paths
        rental_paths = np.zeros((self.config.n_simulations, n_steps + 1))
        
        for t in range(n_steps + 1):
            # Time-varying rental yield with growth
            time_factor = (1 + rental_growth) ** (t * dt)
            
            # Add volatility
            yield_shock = self.rng.normal(0, yield_volatility, self.config.n_simulations)
            current_yield = (adjusted_yield + yield_shock) * time_factor
            
            # Rental income = property value * yield
            rental_paths[:, t] = initial_value * current_yield * dt
        
        return rental_paths
    
    def _calculate_yield_adjustment(self, property: Property) -> float:
        """Calculate rental yield adjustment based on property characteristics"""
        
        adjustment = 0.0
        
        # Property type adjustment
        type_adjustments = {
            PropertyType.STUDIO: 0.005,      # +0.5%
            PropertyType.APARTMENT: 0.0,     # Base
            PropertyType.HOUSE: -0.003,      # -0.3%
            PropertyType.PENTHOUSE: -0.005,  # -0.5%
            PropertyType.MAISONETTE: -0.002  # -0.2%
        }
        adjustment += type_adjustments.get(property.property_type, 0.0)
        
        # Size adjustment
        if property.sqm:
            if property.sqm < 40:
                adjustment += 0.003  # Small properties have higher yields
            elif property.sqm > 120:
                adjustment -= 0.003  # Large properties have lower yields
        
        # Energy efficiency adjustment
        if property.energy_class:
            from ..domain.entities import EnergyClass
            energy_adjustments = {
                EnergyClass.A_PLUS: 0.002,
                EnergyClass.A: 0.001,
                EnergyClass.B_PLUS: 0.0005,
                EnergyClass.B: 0.0,
                EnergyClass.C: 0.0,
                EnergyClass.D: 0.0,
                EnergyClass.E: -0.002,
                EnergyClass.F: -0.005,
                EnergyClass.G: -0.008
            }
            adjustment += energy_adjustments.get(property.energy_class, 0.0)
        
        # Location adjustment (simplified)
        neighborhood = property.location.neighborhood.lower()
        location_adjustments = {
            'kolonaki': -0.005,  # Premium areas have lower yields
            'glyfada': -0.003,
            'kifisia': -0.004,
            'kipseli': 0.003,    # Emerging areas have higher yields
            'patisia': 0.004,
        }
        adjustment += location_adjustments.get(neighborhood, 0.0)
        
        return adjustment
    
    def _calculate_total_returns(
        self,
        price_paths: np.ndarray,
        rental_paths: np.ndarray,
        initial_investment: float,
        dt: float
    ) -> np.ndarray:
        """Calculate total returns including transaction costs"""
        
        n_simulations, n_steps_plus_one = price_paths.shape
        n_steps = n_steps_plus_one - 1
        
        # Initialize total return paths
        total_returns = np.zeros((n_simulations, n_steps + 1))
        
        # Account for initial transaction costs
        buying_costs = initial_investment * self.config.market_params.buying_costs
        net_initial_investment = initial_investment + buying_costs
        
        for t in range(n_steps + 1):
            # Capital value (property price minus selling costs if selling)
            if t == n_steps:  # Final period - assume selling
                selling_costs = price_paths[:, t] * self.config.market_params.selling_costs
                capital_value = price_paths[:, t] - selling_costs
            else:
                capital_value = price_paths[:, t]
            
            # Cumulative rental income
            if t > 0:
                cumulative_rental = np.sum(rental_paths[:, 1:t+1], axis=1)
                
                # Subtract maintenance costs
                maintenance_costs = (
                    price_paths[:, t] * 
                    self.config.market_params.maintenance_costs * 
                    t * dt
                )
                
                net_rental = cumulative_rental - maintenance_costs
            else:
                net_rental = 0
            
            # Total return
            total_returns[:, t] = (capital_value + net_rental - net_initial_investment)
        
        return total_returns
    
    def _calculate_simulation_metrics(
        self,
        property_id: str,
        price_paths: np.ndarray,
        rental_paths: np.ndarray,
        total_return_paths: np.ndarray,
        final_values: np.ndarray,
        initial_investment: float
    ) -> SimulationResults:
        """Calculate comprehensive simulation metrics"""
        
        # Basic statistics
        mean_return = np.mean(final_values) / initial_investment - 1
        std_return = np.std(final_values) / initial_investment
        median_return = np.median(final_values) / initial_investment - 1
        
        # Risk measures
        returns = final_values / initial_investment - 1
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)
        
        # Conditional VaR (Expected Shortfall)
        cvar_95 = np.mean(returns[returns <= var_95])
        cvar_99 = np.mean(returns[returns <= var_99])
        
        # Maximum drawdown
        max_drawdown = self._calculate_max_drawdown(total_return_paths, initial_investment)
        
        # Performance ratios
        risk_free_rate = self.config.market_params.risk_free_rate
        
        if std_return > 0:
            sharpe_ratio = (mean_return - risk_free_rate) / std_return
        else:
            sharpe_ratio = 0
        
        # Sortino ratio (using downside deviation)
        negative_returns = returns[returns < 0]
        if len(negative_returns) > 0:
            downside_deviation = np.sqrt(np.mean(negative_returns**2))
            sortino_ratio = (mean_return - risk_free_rate) / downside_deviation if downside_deviation > 0 else 0
        else:
            sortino_ratio = float('inf') if mean_return > risk_free_rate else 0
        
        # Calmar ratio
        calmar_ratio = (mean_return / max_drawdown) if max_drawdown > 0 else 0
        
        # Probability metrics
        prob_positive_return = np.mean(returns > 0)
        prob_loss = np.mean(returns < 0)
        prob_extreme_loss = np.mean(returns < -0.2)  # 20% loss
        
        # Time series aggregation
        cash_flows = np.mean(rental_paths, axis=0)
        rental_income = np.cumsum(cash_flows)
        capital_appreciation = np.mean(price_paths, axis=0) - initial_investment
        total_returns_ts = np.mean(total_return_paths, axis=0)
        
        return SimulationResults(
            property_id=property_id,
            simulation_paths=total_return_paths,
            final_values=final_values,
            mean_return=mean_return,
            std_return=std_return,
            median_return=median_return,
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            cvar_99=cvar_99,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            prob_positive_return=prob_positive_return,
            prob_loss=prob_loss,
            prob_extreme_loss=prob_extreme_loss,
            cash_flows=cash_flows,
            rental_income=rental_income,
            capital_appreciation=capital_appreciation,
            total_returns=total_returns_ts,
            simulation_config=self.config
        )
    
    def _calculate_max_drawdown(
        self, 
        return_paths: np.ndarray, 
        initial_investment: float
    ) -> float:
        """Calculate maximum drawdown across all paths"""
        
        max_drawdowns = []
        
        for path in return_paths:
            # Calculate cumulative returns
            cumulative_returns = path / initial_investment
            
            # Calculate running maximum
            running_max = np.maximum.accumulate(cumulative_returns)
            
            # Calculate drawdowns
            drawdowns = (cumulative_returns - running_max) / running_max
            
            # Find maximum drawdown for this path
            max_drawdown = np.min(drawdowns)
            max_drawdowns.append(abs(max_drawdown))
        
        return np.mean(max_drawdowns)


class PortfolioOptimizer:
    """
    Advanced portfolio optimization using Monte Carlo results
    """
    
    def __init__(self, config: Optional[SimulationConfig] = None):
        self.config = config or SimulationConfig()
        
    async def optimize_portfolio(
        self,
        simulation_results: Dict[str, SimulationResults],
        budget_constraint: Optional[float] = None,
        target_return: Optional[float] = None,
        target_risk: Optional[float] = None
    ) -> PortfolioOptimizationResult:
        """
        Optimize portfolio allocation using Monte Carlo simulation results
        """
        
        logger.info("Starting portfolio optimization", 
                   n_assets=len(simulation_results))
        
        start_time = datetime.now()
        
        # Prepare data
        asset_ids = list(simulation_results.keys())
        returns = np.array([results.mean_return for results in simulation_results.values()])
        risks = np.array([results.std_return for results in simulation_results.values()])
        
        # Build correlation matrix
        correlation_matrix = self._build_correlation_matrix(simulation_results)
        
        # Perform optimization
        if self.config.optimization_objective == "sharpe_ratio":
            optimal_weights, opt_return, opt_risk, sharpe = self._optimize_sharpe_ratio(
                returns, risks, correlation_matrix, budget_constraint
            )
        elif self.config.optimization_objective == "return":
            optimal_weights, opt_return, opt_risk, sharpe = self._optimize_return(
                returns, risks, correlation_matrix, target_risk, budget_constraint
            )
        elif self.config.optimization_objective == "risk":
            optimal_weights, opt_return, opt_risk, sharpe = self._optimize_risk(
                returns, risks, correlation_matrix, target_return, budget_constraint
            )
        else:
            raise ValueError(f"Unknown optimization objective: {self.config.optimization_objective}")
        
        # Build efficient frontier
        frontier_returns, frontier_risks = self._build_efficient_frontier(
            returns, risks, correlation_matrix
        )
        
        # Create weight mapping
        weight_mapping = {asset_ids[i]: optimal_weights[i] for i in range(len(asset_ids))}
        
        # Individual asset metrics
        asset_returns = {asset_ids[i]: returns[i] for i in range(len(asset_ids))}
        asset_risks = {asset_ids[i]: risks[i] for i in range(len(asset_ids))}
        
        # Check constraints
        constraints_satisfied = self._check_constraints(optimal_weights, budget_constraint)
        
        optimization_time = (datetime.now() - start_time).total_seconds()
        
        result = PortfolioOptimizationResult(
            optimal_weights=weight_mapping,
            expected_return=opt_return,
            expected_risk=opt_risk,
            sharpe_ratio=sharpe,
            efficient_frontier_returns=frontier_returns,
            efficient_frontier_risks=frontier_risks,
            asset_returns=asset_returns,
            asset_risks=asset_risks,
            correlation_matrix=correlation_matrix,
            optimization_method=self.config.optimization_objective,
            constraints_satisfied=constraints_satisfied,
            optimization_time=optimization_time
        )
        
        logger.info("Portfolio optimization completed",
                   optimization_time=optimization_time,
                   sharpe_ratio=sharpe)
        
        return result
    
    def _build_correlation_matrix(
        self, 
        simulation_results: Dict[str, SimulationResults]
    ) -> np.ndarray:
        """Build correlation matrix from simulation results"""
        
        asset_ids = list(simulation_results.keys())
        n_assets = len(asset_ids)
        
        # Use final values for correlation calculation
        returns_matrix = []
        
        for asset_id in asset_ids:
            results = simulation_results[asset_id]
            # Use returns from final values
            asset_returns = results.final_values / results.final_values[0] - 1
            returns_matrix.append(asset_returns)
        
        returns_matrix = np.array(returns_matrix)
        correlation_matrix = np.corrcoef(returns_matrix)
        
        # Handle NaN values
        correlation_matrix = np.nan_to_num(correlation_matrix, nan=0.0)
        
        # Ensure positive semi-definite
        eigenvals, eigenvecs = np.linalg.eigh(correlation_matrix)
        eigenvals = np.maximum(eigenvals, 0.01)  # Minimum eigenvalue
        correlation_matrix = eigenvecs @ np.diag(eigenvals) @ eigenvecs.T
        
        return correlation_matrix
    
    def _optimize_sharpe_ratio(
        self,
        returns: np.ndarray,
        risks: np.ndarray,
        correlation_matrix: np.ndarray,
        budget_constraint: Optional[float] = None
    ) -> Tuple[np.ndarray, float, float, float]:
        """Optimize portfolio for maximum Sharpe ratio"""
        
        n_assets = len(returns)
        risk_free_rate = self.config.market_params.risk_free_rate
        
        def negative_sharpe(weights):
            portfolio_return = np.dot(weights, returns)
            portfolio_variance = np.dot(weights, np.dot(np.diag(risks**2) * correlation_matrix, weights))
            portfolio_risk = np.sqrt(portfolio_variance)
            
            if portfolio_risk == 0:
                return -np.inf
            
            sharpe = (portfolio_return - risk_free_rate) / portfolio_risk
            return -sharpe
        
        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Weights sum to 1
        ]
        
        # Bounds
        bounds = [(0, self.config.constraint_max_weight) for _ in range(n_assets)]
        
        # Initial guess (equal weights)
        x0 = np.ones(n_assets) / n_assets
        
        # Optimize
        result = minimize(
            negative_sharpe,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000}
        )
        
        optimal_weights = result.x
        
        # Calculate portfolio metrics
        portfolio_return = np.dot(optimal_weights, returns)
        portfolio_variance = np.dot(
            optimal_weights, 
            np.dot(np.diag(risks**2) * correlation_matrix, optimal_weights)
        )
        portfolio_risk = np.sqrt(portfolio_variance)
        sharpe = (portfolio_return - risk_free_rate) / portfolio_risk
        
        return optimal_weights, portfolio_return, portfolio_risk, sharpe
    
    def _optimize_return(
        self,
        returns: np.ndarray,
        risks: np.ndarray,
        correlation_matrix: np.ndarray,
        target_risk: Optional[float],
        budget_constraint: Optional[float]
    ) -> Tuple[np.ndarray, float, float, float]:
        """Optimize portfolio for maximum return given risk constraint"""
        
        n_assets = len(returns)
        risk_free_rate = self.config.market_params.risk_free_rate
        
        def negative_return(weights):
            return -np.dot(weights, returns)
        
        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Weights sum to 1
        ]
        
        # Risk constraint
        if target_risk is not None:
            def risk_constraint(weights):
                portfolio_variance = np.dot(
                    weights, 
                    np.dot(np.diag(risks**2) * correlation_matrix, weights)
                )
                return target_risk**2 - portfolio_variance
            
            constraints.append({'type': 'ineq', 'fun': risk_constraint})
        
        # Bounds
        bounds = [(0, self.config.constraint_max_weight) for _ in range(n_assets)]
        
        # Initial guess
        x0 = np.ones(n_assets) / n_assets
        
        # Optimize
        result = minimize(
            negative_return,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        optimal_weights = result.x
        
        # Calculate metrics
        portfolio_return = np.dot(optimal_weights, returns)
        portfolio_variance = np.dot(
            optimal_weights, 
            np.dot(np.diag(risks**2) * correlation_matrix, optimal_weights)
        )
        portfolio_risk = np.sqrt(portfolio_variance)
        sharpe = (portfolio_return - risk_free_rate) / portfolio_risk if portfolio_risk > 0 else 0
        
        return optimal_weights, portfolio_return, portfolio_risk, sharpe
    
    def _optimize_risk(
        self,
        returns: np.ndarray,
        risks: np.ndarray,
        correlation_matrix: np.ndarray,
        target_return: Optional[float],
        budget_constraint: Optional[float]
    ) -> Tuple[np.ndarray, float, float, float]:
        """Optimize portfolio for minimum risk given return constraint"""
        
        n_assets = len(returns)
        risk_free_rate = self.config.market_params.risk_free_rate
        
        def portfolio_variance(weights):
            return np.dot(weights, np.dot(np.diag(risks**2) * correlation_matrix, weights))
        
        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Weights sum to 1
        ]
        
        # Return constraint
        if target_return is not None:
            def return_constraint(weights):
                return np.dot(weights, returns) - target_return
            
            constraints.append({'type': 'eq', 'fun': return_constraint})
        
        # Bounds
        bounds = [(0, self.config.constraint_max_weight) for _ in range(n_assets)]
        
        # Initial guess
        x0 = np.ones(n_assets) / n_assets
        
        # Optimize
        result = minimize(
            portfolio_variance,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        optimal_weights = result.x
        
        # Calculate metrics
        portfolio_return = np.dot(optimal_weights, returns)
        portfolio_risk = np.sqrt(portfolio_variance(optimal_weights))
        sharpe = (portfolio_return - risk_free_rate) / portfolio_risk if portfolio_risk > 0 else 0
        
        return optimal_weights, portfolio_return, portfolio_risk, sharpe
    
    def _build_efficient_frontier(
        self,
        returns: np.ndarray,
        risks: np.ndarray,
        correlation_matrix: np.ndarray,
        n_portfolios: int = 100
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Build efficient frontier"""
        
        min_return = np.min(returns)
        max_return = np.max(returns)
        
        target_returns = np.linspace(min_return, max_return, n_portfolios)
        frontier_risks = []
        frontier_returns = []
        
        for target_return in target_returns:
            try:
                _, opt_return, opt_risk, _ = self._optimize_risk(
                    returns, risks, correlation_matrix, target_return, None
                )
                frontier_returns.append(opt_return)
                frontier_risks.append(opt_risk)
            except:
                continue
        
        return np.array(frontier_returns), np.array(frontier_risks)
    
    def _check_constraints(
        self, 
        weights: np.ndarray, 
        budget_constraint: Optional[float]
    ) -> bool:
        """Check if constraints are satisfied"""
        
        # Weight sum constraint
        if not np.isclose(np.sum(weights), 1.0, rtol=1e-3):
            return False
        
        # Individual weight constraints
        if np.any(weights < 0) or np.any(weights > self.config.constraint_max_weight + 1e-6):
            return False
        
        # Budget constraint (if applicable)
        if budget_constraint is not None:
            # This would need property prices to check properly
            pass
        
        return True


# Risk analysis utilities
class RiskAnalyzer:
    """
    Advanced risk analysis for Monte Carlo results
    """
    
    @staticmethod
    def calculate_scenario_analysis(
        results: SimulationResults,
        scenarios: List[str] = ["best", "worst", "median"]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate scenario analysis"""
        
        final_returns = results.final_values / results.final_values[0] - 1
        
        scenario_results = {}
        
        for scenario in scenarios:
            if scenario == "best":
                percentile = 95
            elif scenario == "worst":
                percentile = 5
            elif scenario == "median":
                percentile = 50
            else:
                continue
            
            scenario_return = np.percentile(final_returns, percentile)
            
            scenario_results[scenario] = {
                "return": scenario_return,
                "final_value": results.final_values[0] * (1 + scenario_return),
                "probability": percentile / 100
            }
        
        return scenario_results
    
    @staticmethod
    def calculate_stress_tests(
        results: SimulationResults,
        stress_scenarios: Optional[Dict[str, Dict]] = None
    ) -> Dict[str, float]:
        """Calculate stress test results"""
        
        if stress_scenarios is None:
            stress_scenarios = {
                "market_crash": {"price_shock": -0.3},
                "interest_spike": {"rate_shock": 0.05},
                "recession": {"rental_shock": -0.2, "price_shock": -0.15}
            }
        
        stress_results = {}
        
        for scenario_name, scenario_params in stress_scenarios.items():
            # Apply shocks to the simulation results
            adjusted_returns = results.final_values / results.final_values[0] - 1
            
            if "price_shock" in scenario_params:
                adjusted_returns += scenario_params["price_shock"]
            
            # Calculate impact
            original_return = results.mean_return
            stressed_return = np.mean(adjusted_returns)
            impact = stressed_return - original_return
            
            stress_results[scenario_name] = impact
        
        return stress_results


# Export classes for use in other modules
__all__ = [
    'MonteCarloSimulator',
    'PortfolioOptimizer',
    'RiskAnalyzer',
    'SimulationConfig',
    'MarketParameters',
    'SimulationResults',
    'PortfolioOptimizationResult',
    'SimulationMethod',
    'RiskMeasure'
]