# Chapter Simulation Playground

桌面版 Chapter Simulation Playground，包含多种 MouseHunt 章节模拟与计划工具。

## 功能概览

1. **Postscript Optimizer**  
   - 多轮拨动章节页数比例，自动寻找更高的 All Genre ≥ 80% 概率。  
   - 可自定义拨动范围、迭代次数、候选数量、单个候选的模拟次数。
2. **Postscript Simulator**  
   - 设定奶酪、章节页数、是否延长，再查看单次运行与 30,000 次模拟的平均值。  
   - 支持复制/粘贴页数与 Notoriety，便于跨模块交流。
3. **Contingency Start Fixer**  
   - 针对“开局就撞到已满足 Genre”情况，快速注入额外页数并保持剩余 Genre 的比例。  
   - 滑动条可调节目标 Genre 占比，结果可复制回其它模块使用。
4. **Dual Postscript Simulator**  
   - 两个 Setup 串联模拟，含自动延长逻辑，输出单次 + 50,000 次统计与延长触发率。  
   - 方便规划“先跑 A 再跑 B”的双段路线。
5. **5/6 Genres 概览标签**  
   - 20,000 次马槌模拟，对比不同 Genre 池的章节转场概率与马槌消耗。
6. **Overview**  
   - 说明文档，概述每个模块和常用参数。

程序会把各模块的输入与参数保存到 `simulator_state.json`，下次启动会自动恢复。

## 快速开始

1. `pip install -r requirements.txt`（如需）  
2. `python main.py`  
3. 根据 Overview 提示在对应标签页进行模拟/调整。

## Git 上传建议

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-repo-url>
git push -u origin main
```

## 版权声明

© 2025 gujia. 保留所有权利。  
**禁止用于盈利或任何商业用途。**  
如需引用或二次开发，请先与作者联系。  
