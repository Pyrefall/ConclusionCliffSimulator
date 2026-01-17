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

1. **Overview Tab** – Read the built-in guide for each module, the suggested parameters, and how the tabs complement one another.  
2. **Postscript Optimizer** – Starting from your cheese and page setup, iteratively dial chapter weights via systematic/random candidates, Monte Carlo them, and surface the best distribution plus readiness odds.  
3. **Postscript Simulator** – Configure cheese stacks, chapter weights, and optional extensions, then inspect a detailed single run plus a 30,000-run summary (average notoriety + All-Genre-≥80 probability). Clipboard helpers simplify copy/paste.  
4. **Ratio Scaler** – Paste any five-genre distribution and scale the total pages uniformly with a slider while keeping genre ratios intact. Use it for quick what-if checks.  
5. **Contingency Start Fixer** – Paste an existing distribution, add a genre/length boost, then choose the final share for that genre while the remaining ones retain their ratios—great for emergency reroutes.  
6. **Dual Postscript Simulator** – Define two setups that run back-to-back with auto-extend logic, copy/paste utilities, and a 50,000-run aggregate report covering average notoriety, readiness rates, and extension usage.  
7. **Dual Postscript (Pruned)** – Same as above, but when Setup 2 begins it automatically zeroes page weights for genres that already exceeded the notoriety threshold, focusing entirely on unfinished genres.  
8. **Just Farming Mallets** – Model “short-only” farming loops: run six quick chapters, burn a fixed cheese bundle, and estimate runs, hunts, and mallets per cycle until every genre passes 80 notoriety.  
9. **5 Genres / 6 Genres** – Refresh to simulate 40,000 chains where you keep rerolling until the same genre (and separately the exact length/genre combo) appears through five additional areas; compares the Mallet burn when pulling from 5- vs 6-genre pools.

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
