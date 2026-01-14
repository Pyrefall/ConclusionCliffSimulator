# Conclusion Cliff Simulator

Desktop toolkit for planning MouseHunt Postscript runs. Conclusion Cliff Simulator bundles several optimizers, simulators, and genre planners tailored for chapter routing.

## Feature Overview

1. **Postscript Optimizer**  
   - Iteratively nudges chapter page weights to maximize the probability that every genre reaches ≥ 80% notoriety.  
   - Dial in the adjustment range, iteration count, candidate pool, and simulations per candidate.
2. **Postscript Simulator**  
   - Configure cheese composition, chapter pages, and extension rules, then evaluate a single run plus a 30,000-run Monte Carlo average.  
   - Supports copy/paste for page weights and notoriety so setups move cleanly between modules.
3. **Contingency Start Fixer**  
   - Handles “second run starts with a genre that is already satisfied” by injecting extra pages while keeping the remaining genres proportional.  
   - Slider lets you pick the target genre share and copy the adjusted distribution for other tabs.
4. **Dual Postscript Simulator**  
   - Chains two setups with auto-extension logic, reporting single-run results, 50,000-run averages, and extension trigger rates.  
   - Ideal for A→B back-to-back plans.
5. **5/6 Genre Overview Tab**  
   - Runs 20,000 mallet simulations to compare transition probabilities and mallet use across different genre pools.
6. **Overview Tab**  
   - Documentation-style primer describing every module and the most common parameters.

All module inputs persist to `simulator_state.json` so your latest parameters reload automatically.

## Quick Start

1. `pip install -r requirements.txt` (if your environment is missing dependencies)  
2. `python main.py`  
3. Follow the prompts in the Overview tab and switch to the module you need.

## Publishing To Git

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-repo-url>
git push -u origin main
```

## License

© 2025 gujia. All rights reserved.  
**Personal, non-commercial use only.**  
Please contact the author before redistributing or creating derivative work.  
