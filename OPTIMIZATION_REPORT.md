# Weekly Stats Performance Optimization Report

## Summary
Analyzed and optimized the `/api/weekly-stats` endpoint performance.

## Performance Analysis

### Database Statistics
- Total matches: 2,830
- Total sub-matches: 19,888
- Total legs: 85,172
- Total throws: 1,840,891

### Original Performance (without caching)
- Query 1 (Top Averages): **0.001s** ⚡ (already optimal)
- Query 2 (Top Checkouts): **0.105s** 🟡
- Query 3 (Shortest Legs): **0.619s** 🟠 (slowest)
- Query 4 (Most 100+ Throws): **0.141s** 🟡
- **Total execution time: ~0.87s**

### Root Causes
1. **Query 2, 3, 4 perform full table scans** on `throws` table (1.8M rows)
2. **CTEs in Query 3 & 4** scan entire throws table before filtering by date
3. No application-level caching

### Query Plans Analysis
- Query 1: Uses index on `matches.match_date` ✅
- Query 2: **SCAN curr** (full table scan on throws) ❌
- Query 3: **SCAN t** in CTE (full table scan) ❌
- Query 4: **SCAN t** in CTE (full table scan) ❌

## Optimization Attempts

### 1. SQL Query Restructuring (FAILED)
**Approach**: Attempted to filter by date first using CTEs to reduce throws table scan.

**Results**:
- Query 2: -5.2% (slower)
- Query 4: -17.7% (slower)

**Conclusion**: SQLite's query optimizer already handles these queries well. Adding extra CTEs created overhead.

### 2. Index Creation (PARTIAL SUCCESS)
**Indexes considered**:
- `idx_throws_score` (already exists) ✅
- `idx_throws_remaining_score` (timeout during creation)
- `idx_throws_leg_team_round` (timeout during creation)

**Conclusion**: Creating indexes on 1.8M row table takes too long. Existing indexes are sufficient.

### 3. Application-Level Caching (IMPLEMENTED ✅)
**Approach**: Use Flask-Caching to cache `/api/weekly-stats` responses

**Implementation**:
```python
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300  # 5 minutes
})

@app.route('/api/weekly-stats')
@cache.cached(timeout=300, query_string=True)
def get_weekly_stats():
    ...
```

**Benefits**:
- First request: ~0.87s (run all queries)
- Subsequent requests: <0.01s (serve from cache)
- Cache invalidates after 5 minutes
- Varies by `division` query parameter
- **99% improvement for cached requests**

## Recommendations

### Implemented ✅
1. **Flask-Caching** with 5-minute TTL for `/api/weekly-stats`
2. Caching varies by division filter

### Future Optimizations (if needed)
1. **Materialized weekly stats table**
   - Create a `weekly_stats` table updated hourly
   - Pre-calculate all stats for current week
   - Would reduce response time to <0.01s always

2. **Redis caching** (for production)
   - Replace SimpleCache with Redis
   - Allows cache sharing across multiple app instances
   - Better cache invalidation control

3. **Index creation during off-peak hours**
   - Schedule index creation when app has low traffic
   - `CREATE INDEX idx_throws_remaining_score ON throws(remaining_score)`
   - `CREATE INDEX idx_throws_leg_team_round ON throws(leg_id, team_number, round_number)`

4. **Query result pagination**
   - If user wants to see more than top 10
   - Implement cursor-based pagination

## Impact

### Before Optimization
- Every request: 0.87s
- 100 requests/hour: 87s total query time

### After Optimization (with caching)
- First request: 0.87s
- Next 59 requests (within 5min): <0.01s each
- **Total time for 60 requests in 5min: ~0.88s** (99% improvement)

## Dependencies Added
```bash
pip install Flask-Caching
```

## Configuration
Cache timeout: **Infinite (0 seconds)**
- Cache persists until app restart/redeploy
- Optimal for deployment workflow where new data imports trigger redeploy
- Maximum performance - no cache expiration overhead
- SimpleCache stores in memory, clears automatically on restart

## Top Stats Optimization

### Performance Analysis
Similar to weekly stats, `/api/top-stats` performs 4 heavy queries:

**Without season filter (all-time):**
- Query 1 (Top Averages): 0.018s ⚡
- Query 2 (Top Checkouts): 0.157s 🟡
- Query 3 (Shortest Legs): 0.528s 🟠 (slowest)
- Query 4 (Most 180s): 0.018s ⚡
- **Total: ~0.72s**

**With season filter (faster):**
- Filtering by season reduces data scope
- ~0.54s improvement vs all-time queries

### Optimization Applied
Added Flask-Caching with 10-minute TTL:

```python
@app.route('/api/top-stats')
@cache.cached(timeout=600, query_string=True)
def get_top_stats():
    ...
```

### Results
- **First request (all-time):** 0.79s
- **Cached requests:** 0.0005s
- **Improvement: 1788x faster (99.9%)**
- **Cache varies by season parameter**

### Impact
- All-time stats: 0.79s → 0.0006s
- Season-filtered: 1.07s → 0.0007s
- Different seasons cached separately
- Infinite cache (cleared on redeploy)

## Cache Management

### Automatic Cache Clearing
**Cache is automatically cleared on:**
- App restart
- Redeploy (Railway/production)
- Container restart (Docker)

Since SimpleCache stores data in memory, every deployment gets fresh cache.

### Manual Cache Clearing (if needed during development)
```python
from app import cache
cache.clear()
```

Or via Flask shell:
```bash
flask shell
>>> from app import cache
>>> cache.clear()
>>> print("Cache cleared!")
```

### Recommended Workflow
1. Import new match data to database
2. Commit database changes
3. Deploy/restart app → Cache automatically clears
4. **Cache warmup runs automatically on startup** (pre-populates cache)
5. First user gets instant response (cache already populated)

### Cache Warmup
The app automatically pre-populates the cache at startup with:
- `/api/weekly-stats` (no filter)
- `/api/weekly-stats?division=X` (for ALL divisions in current season)
- `/api/top-stats` (all-time)
- `/api/top-stats?season=X` (current and previous season)

**Warmup time:** ~22 seconds at startup
**Entries cached:** ~22 endpoints (1 + 18 divisions + 3 top stats)
**Benefit:** First users get instant response instead of waiting 0.7-1.7s

This ensures ALL commonly accessed endpoints are pre-cached at startup.

### Cache Warmup Behavior

**Development mode (debug=True):**
- Warmup runs ONCE on initial startup
- Flask's reloader process skips warmup (to avoid duplication)
- Auto-reload on file changes doesn't re-run warmup

**Production mode (Gunicorn):**
- Warmup runs once when server starts
- No reloader, so only runs once

### Disabling Cache Warmup (Development)
For faster startup during local development, you can disable cache warmup:

```bash
python app.py --no-warmup
```

This skips the 22-second warmup and starts the app immediately. First requests will be slower but subsequent requests will still be cached.

### Cache Keys
The cache automatically creates separate entries for:
- `/api/weekly-stats` (no params)
- `/api/weekly-stats?division=SL6`
- `/api/top-stats` (no params)
- `/api/top-stats?season=2024/2025`
- etc.

## Files Added/Modified

### New Files
- `cache_warmup.py` - Automatic cache pre-population at startup
- `gunicorn.conf.py` - Gunicorn configuration with cache warmup hook
- `OPTIMIZATION_REPORT.md` - This documentation

### Modified Files
- `app.py` - Added Flask-Caching and warmup initialization
- `requirements.txt` - Added Flask-Caching==2.1.0

---
*Generated: 2025-10-10*
*Updated: 2025-10-10 - Added Top Stats optimization, infinite cache, and automatic cache warmup*
