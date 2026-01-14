# Conclusion Cliff Simulator

Desktop toolkit for planning MouseHunt Postscript runs. Conclusion Cliff Simulator bundles several optimizers, simulators, and genre planners tailored for chapter routing.

## Author's Note

This tool simulates Postscript chapters and searches for favorable page ratios so every genre can reach its target notoriety. You can either follow the packaging guide below to create your own `.exe`, or simply grab the ready-made executable from the Releases panel on the right side of the project page.

Postscript Optimizer can take a while—the runtime depends almost entirely on the Optimization Parameters you set. Because the map just launched, some mechanics might still be slightly off; ping me on Discord if you spot issues and I will patch them as soon as I can. Have fun!

## Build Your Own EXE

1. Activate your virtual environment (if any) and install PyInstaller: `pip install pyinstaller`.
2. From the project root, run `pyinstaller --onefile --windowed main.py`.  
   - Add `--icon path/to/icon.ico` or `--add-data "file;target_folder"` if you need custom assets.
3. When the command finishes, the packaged executable will be located at `dist/main.exe`. Copy that file to any machine where you want to run the simulator.
4. If you need console logs for debugging, drop the `--windowed` flag so the terminal window stays visible.

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
