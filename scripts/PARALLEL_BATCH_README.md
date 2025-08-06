# 🏛️ PARALLEL BATCH ATHENS PROPERTY COLLECTOR

A sophisticated parallel collection system that uses 10 concurrent workers to efficiently collect 500 authentic Athens properties from Spitogatos.gr.

## 🏗️ ARCHITECTURE

The system consists of 5 main components working together:

### 1. **BatchCoordinator** 
- Main orchestrator managing all workers
- Distributes distinct search strategies to avoid conflicts
- Coordinates staggered worker starts (30 seconds apart)
- Manages consolidated results

### 2. **BatchWorker**
- Individual worker collecting 50 properties each
- Uses proven extraction methodology from `scalable_athens_collector.py`
- Implements worker-specific rate limiting and delays
- Handles browser management and page navigation

### 3. **WorkerAgent** 
- Handles errors and implements retry logic for each worker
- Classifies errors (timeout, connection, extraction, browser)
- Implements recovery strategies with exponential backoff
- Tracks error history and patterns

### 4. **ProgressMonitor**
- Real-time monitoring across all workers
- Background thread reporting progress every 30 seconds
- Tracks worker status, completion rates, and performance
- Thread-safe progress updates

### 5. **ResultsConsolidator**
- Combines results from all completed workers
- Generates comprehensive statistics
- Saves data in multiple formats (JSON, CSV, statistics)

## 🚀 QUICK START

### Option 1: Simple Execution
```bash
cd scripts
python3 run_parallel_batch.py
```

### Option 2: Custom Configuration
```bash
cd scripts
python3 run_parallel_batch.py --workers 8 --per_worker 40
```

### Option 3: Direct Python Usage
```python
from parallel_batch_collector import run_parallel_collection_sync

# Collect 500 properties with 10 workers
properties = run_parallel_collection_sync(num_workers=10, properties_per_worker=50)
print(f"Collected {len(properties)} properties")
```

## 📊 TECHNICAL SPECIFICATIONS

### Concurrency Design
- **10 concurrent workers** running simultaneously
- **Staggered starts**: 30 seconds between worker launches
- **Worker-specific strategies**: Different search URLs and price ranges
- **Individual rate limiting**: Each worker has unique delay patterns

### Search Strategy Distribution
```
Worker 1: €50K-120K, Sale Apartments, Price Low→High
Worker 2: €120K-200K, Sale Homes, Price High→Low  
Worker 3: €200K-300K, Rent Apartments, Newest First
Worker 4: €300K-450K, Rent Homes, Largest First
Worker 5: €450K-650K, Sale Apartments, Price Low→High
Worker 6: €650K-900K, Sale Homes, Price High→Low
Worker 7: Kolonaki neighborhood, €50K-120K
Worker 8: Exarchia neighborhood, €120K-200K
Worker 9: Pagrati neighborhood, €200K-300K
Worker 10: All ranges mixed, €50K-3M
```

### Error Handling & Recovery
- **Timeout errors**: Progressive delays (30s, 60s, 120s)
- **Connection errors**: Exponential backoff (60s, 120s, 300s)
- **Extraction errors**: Skip problematic URL, continue
- **Browser errors**: Automatic browser restart
- **Maximum 3 retries** per worker before marking as failed

### Data Validation
Each property must pass validation to be marked as `PARALLEL_BATCH_AUTHENTIC`:
- **Required fields**: URL, Price, SQM, Energy Class
- **Price range**: €50,000 - €3,000,000
- **Size range**: 25m² - 600m²
- **Energy classes**: A+ to G
- **Price per sqm**: €500 - €15,000

## 📁 OUTPUT FILES

All files are saved in `data/processed/` with timestamp:

### 1. Consolidated JSON
`parallel_batch_consolidated_[session]_[timestamp].json`
- Complete property data for all workers
- Full extraction details and metadata
- Worker assignments and batch information

### 2. CSV Summary  
`parallel_batch_summary_[session]_[timestamp].csv`
```
Worker_ID,URL,Price,SQM,Energy_Class,Price_per_SQM,Neighborhood,Rooms,Strategy,Authentication
1,"https://...",150000,65,B,2307,Pagrati,2,worker_1_budget_price_low_to_high,AUTHENTIC
```

### 3. Statistics File
`parallel_batch_stats_[session]_[timestamp].json`
```json
{
  "total_properties": 487,
  "authentic_count": 487,
  "price_range": {"min": 52000, "max": 2800000, "avg": 425000},
  "sqm_range": {"min": 28, "max": 580, "avg": 95},
  "energy_classes": ["A+", "A", "B+", "B", "C", "D", "E", "F", "G"],
  "neighborhoods": 15,
  "worker_performance": {
    "1": 48, "2": 51, "3": 47, "4": 52, "5": 49,
    "6": 46, "7": 53, "8": 44, "9": 50, "10": 47
  }
}
```

## 📊 REAL-TIME MONITORING

The system provides live progress updates every 30 seconds:

```
📊 PARALLEL PROGRESS UPDATE:
   Total: 287/500 (57.4%)
   Runtime: 12.3 minutes
   Rate: 23.3 properties/minute
   Workers: 8/10 active
   Worker 1: 31/50 (COLLECTING)
   Worker 2: 28/50 (COLLECTING) 
   Worker 3: 29/50 (COLLECTING)
   Worker 4: 0/50 (FAILED)
   Worker 5: 32/50 (COLLECTING)
   ...
```

## 🔧 CUSTOMIZATION

### Adjust Worker Count
```python
# Run with fewer workers for lower load
properties = run_parallel_collection_sync(num_workers=5, properties_per_worker=40)
```

### Custom Search Strategies
Modify `_build_worker_strategies()` in `BatchCoordinator` to customize:
- Price ranges per worker
- Property types (apartments, homes, studios)
- Neighborhoods to focus on
- Sorting methods
- Pages per strategy

### Rate Limiting
Adjust delays in `BatchWorker.collect_batch()`:
```python
# Current: 1.5-2.5s + worker offset
base_delay = 1.5 + (self.worker_id * 0.2)
await asyncio.sleep(random.uniform(base_delay, base_delay + 1))
```

## 🛠️ TROUBLESHOOTING

### Common Issues

**Import Error**: Ensure you're in the scripts directory
```bash
cd /Users/chrism/spitogatos_premium_analysis/ATHintel/scripts
```

**Memory Issues**: Reduce worker count
```bash
python3 run_parallel_batch.py --workers 5 --per_worker 50
```

**Network Timeouts**: Workers have built-in retry logic, but check network stability

**Rate Limiting**: The system uses conservative delays, but if blocked, increase delays in worker code

### Monitoring Worker Health
Check individual worker progress and error rates:
- Workers reporting 0 properties after 10+ minutes likely have issues
- Check error logs for specific worker failure patterns
- Failed workers are automatically marked and excluded from final results

## 🎯 EXPECTED PERFORMANCE

### Typical Results
- **Collection time**: 45-90 minutes for 500 properties
- **Success rate**: 85-95% authentic properties
- **Rate**: 15-25 properties per minute across all workers
- **Worker efficiency**: 40-55 properties per worker (target: 50)

### Performance Factors
- Network speed and stability
- Spitogatos.gr server response times
- Complexity of property pages
- Rate limiting effectiveness

## ✅ VALIDATION & AUTHENTICITY

Every collected property is validated against proven criteria:

1. **Complete data**: URL, price, size, energy class all present
2. **Realistic ranges**: Price and size within Athens market norms  
3. **Valid classifications**: Energy classes A+ through G only
4. **Athens location**: Neighborhood matching target areas
5. **Market pricing**: Price per sqm within expected ranges

Properties passing all validations receive `PARALLEL_BATCH_AUTHENTIC` flag.

## 🔒 BUILT ON PROVEN SUCCESS

This system extends the successful methodology from `scalable_athens_collector.py`:
- ✅ Same extraction patterns and selectors
- ✅ Same browser configuration and headers
- ✅ Same validation logic and data structure
- ✅ Same rate limiting and error handling
- ✅ Proven to collect 100+ authenticated properties

The parallel architecture adds:
- 🚀 10x concurrency for faster collection
- 🚀 Intelligent work distribution
- 🚀 Real-time progress monitoring  
- 🚀 Advanced error recovery
- 🚀 Comprehensive result consolidation

## 📈 SCALING FURTHER

To scale beyond 500 properties:

1. **Increase workers**: `--workers 15 --per_worker 50` = 750 properties
2. **Multiple sessions**: Run system multiple times with breaks
3. **Extended strategies**: Add more neighborhoods and property types
4. **Time distribution**: Run different sessions at different times

The architecture supports scaling to 1000+ properties with proper resource management.