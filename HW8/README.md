# 實作報告：IC 設計的 EDA 是什麼？

**報告撰寫人：** \[謝秉潾\]

**日期：** 2026-10-30

## 摘要

在現代半導體產業中，積體電路（IC）的複雜度已達到數百億顆電晶體的規模，完全無法仰賴人工進行繪圖與設計。**EDA（Electronic Design Automation，電子設計自動化）** 軟體應運而生，成為晶片設計不可或缺的核心工具。本報告將探討 EDA 在 IC 設計中的定義、功能，並結合實際操作 EDA 軟體的經驗，以及開源與學術界的優質學習資源，分析其在整個晶片設計流程中的重要性。

## 一、 什麼是 EDA (電子設計自動化)？

EDA 是一套由電腦硬體、軟體程式及演算法組成的工具集合。它的主要目的是協助硬體工程師進行 IC 設計、模擬、驗證、佈局與測試。
簡單來說，如果把設計晶片比喻成建造一座擁有數十億個房間的超級城市，EDA 就是建築師手中的「數位繪圖板、結構模擬機與自動化施工藍圖」。沒有 EDA 工具（如 Synopsys、Cadence、Siemens EDA 等大廠提供的軟體），現代先進製程的晶片設計是完全不可能實現的。

## 二、 EDA 在 IC 設計流程中的關鍵角色

透過實際操作 EDA 軟體，可以深刻體會到它貫穿了 IC 設計的「前端（Front-end）」與「後端（Back-end）」流程：

### 1. 前端設計 (Front-end Design)

* **硬體描述語言 (HDL) 撰寫：** 使用 Verilog 或 VHDL 描述電路邏輯。
* **邏輯模擬 (Logic Simulation)：** 軟體會驗證我們寫的程式碼是否符合預期的功能，及早抓出邏輯錯誤。
* **邏輯合成 (Logic Synthesis)：** 這是非常驚豔的一步。EDA 工具能將抽象的程式碼，轉換成由實際邏輯閘（Gate-level netlist）組成的電路圖，並初步評估面積、功耗與速度。

### 2. 後端設計 (Back-end Design / Physical Design)

* **佈局與繞線 (APR - Auto Place and Route)：** 將合成後的邏輯閘擺放到實體晶片範圍內，並用金屬線連接起來。軟體必須在擁擠的空間中找出最佳路徑，避免訊號干擾。
* **物理驗證 (Physical Verification)：** 包含 **DRC** (設計規則檢查，確保電路符合晶圓廠的製造限制) 與 **LVS** (佈局對比電路圖，確保畫出來的版圖與最初設計的邏輯一致)。
* **靜態時序分析 (STA - Static Timing Analysis)：** 檢查所有訊號是否能在規定的時間內抵達目的地（Setup/Hold time check），這是決定晶片能跑多快（時脈頻率）的關鍵。

## 三、 實作心得與軟體體驗

在實際使用 EDA 軟體進行專案設計後，我有以下幾點深刻的體會：

1. **高度的自動化與運算龐大：** 執行一次合成（Synthesis）或繞線（Routing），往往需要伺服器跑上數小時甚至數天。軟體背後運行的圖論與最佳化演算法極度複雜，這也解釋了為何 EDA 軟體授權費如此昂貴。
2. **Debug（除錯）的挑戰：** 實作過程中，最大的挑戰往往不是寫出電路，而是學會看懂軟體給的 Timing Report 與 DRC Error，並從成千上萬行的警告中找到關鍵的 Bottleneck（瓶頸）來修改設計。
3. **PPA 的權衡：** 實作時，我們不斷透過 EDA 工具來優化 **PPA (Power 功耗, Performance 效能, Area 面積)**。想要晶片跑得快，可能面積就會變大、耗電增加。EDA 工具提供了多種約束指令讓我們在這三角關係中尋找最佳解。

## 四、 開源 EDA 工具與進階學習資源

除了昂貴的商業軟體，開源社群與學術界也提供了極具價值的 EDA 學習資源與輕量化工具，對於初學者與研究者來說是絕佳的入門管道：

1. **從邏輯閘到電腦的底層建構：Nand2tetris 網頁專案**
   * 專案原始碼：[https://github.com/ccc-js/hack-computer](https://github.com/ccc-js/hack-computer)
   * 線上實作：[https://ccc-js.github.io/hack-computer/dist/hdl.html](https://ccc-js.github.io/hack-computer/dist/hdl.html)
   * **簡評：** 這是學習硬體描述語言（HDL）與計算機架構的絕佳起點。透過網頁版工具，無需安裝龐大軟體，即可在瀏覽器上體驗從基本的 NAND Gate 一路設計出一台完整電腦的過程。

2. **AI 與自製 EDA 工具探索：veryl2chip**
   * 專案原始碼：[https://github.com/ccc-eda/veryl2chip/](https://github.com/ccc-eda/veryl2chip/)
   * 線上實作：[https://ccc-eda.github.io/veryl2chip/web/dist/index.html](https://ccc-eda.github.io/veryl2chip/web/dist/index.html)
   * **簡評：** 展示了利用 AI 輔助設計與自製 EDA 工具的潛力。這類輕量級的開源專案降低了 IC 設計的門檻，讓開發者能以更敏捷的方式驗證硬體邏輯。

3. **系統性理論教材：EDA 電子書**
   * 資源連結：[https://github.com/ccc-eda/eda-books/tree/main/book](https://github.com/ccc-eda/eda-books/tree/main/book)
   * **簡評：** 提供了豐富的開源電子書資源，涵蓋了 EDA 演算法、硬體設計理論等，適合用來補強實作背後的學術基礎。

4. **頂尖大學進階實務課程：康乃爾大學 IC 設計課程 (ECE 5745)**
   * 課程講義：[https://www.csl.cornell.edu/courses/ece5745/handouts.html](https://www.csl.cornell.edu/courses/ece5745/handouts.html)
   * **簡評：** 康乃爾大學的 ECE 5745 (Complex Digital ASIC Design) 是極具參考價值的學術課程。其公開的 Handouts 詳細說明了業界等級的 ASIC 設計流程（ASIC Toolflow），對於想要深入了解商業 EDA 軟體操作與進階架構設計的人來說是必讀材料。

## 五、 未來趨勢

隨著製程微縮至 3nm 甚至更小，EDA 軟體也正在進化：
* **AI 導入 EDA：** 目前許多 EDA 工具已開始結合機器學習，讓 AI 自動探索最佳的佈局與繞線策略，大幅縮短設計週期。
* **異質整合與先進封裝：** 針對 Chiplet（小晶片）技術，EDA 軟體正發展出能同時處理 2.5D/3D 封裝結構的設計與散熱模擬工具。

## 六、 結論

「工欲善其事，必先利其器」。經過實際的設計流程演練，我體認到 EDA 軟體早已超越了單純的「輔助工具」，它是現代 IC 設計工程師的大腦延伸。搭配豐富的開源工具（如 Nand2tetris 網頁版、veryl2chip）建立基礎，再進階研讀頂尖大學（如康乃爾大學）的實務講義，能讓我們不僅止於「把電路做出來」，更能深刻理解 EDA 系統運作的本質，以榨出晶片的最極致效能。
