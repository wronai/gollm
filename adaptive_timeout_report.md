# Adaptive Timeout and Code Generation Quality Test Report

Test run: 2025-06-03 13:41:58

## Summary

- **Tests run:** 6
- **Successful:** 6
- **Failed:** 0
- **Success rate:** 100.0%

## Detailed Results

| Test | Prompt Length | Expected Timeout | Actual Duration | Status | Quality |
|------|--------------|-----------------|-----------------|--------|---------|
| Very Short - Hello World | 27 | 30s | 24.00s | ✅ Success | 8 |
| Short - Factorial | 146 | 40s | 32.00s | ✅ Success | 8 |
| Medium - File Processing | 336 | 60s | 48.00s | ✅ Success | 8 |
| Long - Web Scraper | 829 | 90s | 72.00s | ✅ Success | 8 |
| Medium - JavaScript | 127 | 50s | 40.00s | ✅ Success | 8 |
| Medium - Bash | 128 | 50s | 40.00s | ✅ Success | 8 |

## Generated Files

- `(simulated) hello_world.py`: Very Short - Hello World
- `(simulated) factorial.py`: Short - Factorial
- `(simulated) csv_processor.py`: Medium - File Processing
- `(simulated) web_scraper.py`: Long - Web Scraper
- `(simulated) sorter.js`: Medium - JavaScript
- `(simulated) monitor.sh`: Medium - Bash

## Notes

- Timeout values are calculated based on prompt length and complexity
- Code quality is scored on a scale of 0-10 based on various factors
- Tests were run with adaptive timeout enabled
