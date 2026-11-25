# Nand2Tetris Project 7 & 8：VM Translator（虛擬機轉譯器）

本專案為 [Nand2Tetris](https://www.nand2tetris.org/) 課程 **Project 7 與 Project 8** 的完整實作，使用 Python 撰寫的 **Hack VM 轉譯器（VM Translator）**，可將虛擬機中間碼（`.vm`）轉譯為 Hack 組合語言（`.asm`）。

程式同時支援**單一 `.vm` 檔案**與**多檔案專案資料夾**，完整涵蓋堆疊算術邏輯運算、記憶體區段存取、程式流程控制、函式呼叫與返回，以及系統啟動碼（Bootstrap Code）。

---

## 專案目錄結構

```text
├── VMTranslator.py                  # 完整版 VM 轉譯器主程式（支援 Ch.7 與 Ch.8）
├── README.md                        # 專案說明文件
├── 07/                              # Project 7 測試範例
│   ├── StackArithmetic/
│   │   ├── SimpleAdd/               # 基礎加法測試
│   │   └── StackTest/               # 算術與比較指令測試
│   └── MemoryAccess/
│       ├── BasicTest/               # local, argument, this, that, temp 測試
│       ├── PointerTest/             # pointer 區段測試
│       └── StaticTest/              # static 靜態變數測試
└── 08/                              # Project 8 測試範例
    ├── ProgramFlow/
    │   ├── BasicLoop/               # label 與 if-goto 迴圈測試
    │   └── FibonacciSeries/         # goto 與條件分支測試
    └── FunctionCalls/
        ├── SimpleFunction/          # 單一函式宣告與返回測試
        ├── NestedCall/              # 多層巢狀函式呼叫（含 Sys.vm）
        ├── FibonacciElement/        # 遞迴函式與多檔合併（含 Sys.vm）
        └── StaticsTest/             # 跨檔案 static 變數隔離（含 Sys.vm）
```

---

## 系統架構與實作重點

程式分為 `Parser`（語法解析器）與 `CodeWriter`（組合語言產生器）兩大核心模組：

### 1. Project 7：堆疊運算與記憶體存取
* **算術與邏輯運算（9 種指令）**：
  * 二元運算：`add`、`sub`、`and`、`or`
  * 一元運算：`neg`、`not`
  * 比較運算：`eq`、`gt`、`lt`（自動產生遞增標籤 `COMP_TRUE_n` / `COMP_END_n`，以 `-1` 代表 `true`、`0` 代表 `false`）
* **記憶體區段存取（8 種區段）**：
  * `constant`：推入常數值至堆疊頂端
  * `local`、`argument`、`this`、`that`：透過基底指標（`LCL`、`ARG`、`THIS`、`THAT`）計算偏移位址
  * `temp`：直接對應固定暫存區 `RAM[5]` 至 `RAM[12]`
  * `pointer`：`0` 對應 `THIS`（`RAM[3]`），`1` 對應 `THAT`（`RAM[4]`）
  * `static`：以 `檔名.索引` 命名符號（如 `@StaticTest.3`），確保多檔案編譯時靜態變數互不衝突

### 2. Project 8：流程控制與函式呼叫
* **程式流程控制（Program Flow）**：
  * 支援 `label`、`goto` 與 `if-goto`，並自動加上目前所在函式的命名空間前綴（`函式名稱$標籤名稱`）。
* **函式呼叫與返回（Function Calling）**：
  * **`function f nVars`**：宣告函式進入點 `(f)`，並推入 `nVars` 個 `0` 初始化區域變數。
  * **`call f nArgs`**：推入唯一返回標籤（`f$ret.i`），依序備份呼叫端的 `LCL`、`ARG`、`THIS`、`THAT`，重新定位 `ARG = SP - 5 - nArgs` 與 `LCL = SP`，最後跳轉至目標函式。
  * **`return`**：使用 `R13` 暫存 `endFrame`、`R14` 暫存返回位址 `retAddr`（防止無參數函式覆寫返回位址），將回傳值寫入 `*ARG`、復原 `SP` 與呼叫端暫存器狀態後跳轉返回。
* **智慧啟動碼（Bootstrap Code）**：
  * 傳入**單一 `.vm` 檔案**時，不加入啟動碼，以配合單一模組測試腳本。
  * 傳入**資料夾路徑**且內部包含 `Sys.vm` 時，自動合併所有 `.vm` 檔並在開頭寫入啟動碼（設定 `SP = 256` 並執行 `call Sys.init 0`）。

---

## 使用方式

### 環境需求
* Python 3.8 以上版本（僅使用內建標準函式庫，無需額外安裝套件）

### 1. 轉譯單一 `.vm` 檔案（Project 7 & Project 8 單檔測試）
在終端機執行時傳入目標 `.vm` 檔案路徑，會在同目錄下產生對應的 `.asm` 檔案：

```bash
python3 VMTranslator.py 07/StackArithmetic/SimpleAdd/SimpleAdd.vm
python3 VMTranslator.py 07/MemoryAccess/BasicTest/BasicTest.vm
python3 VMTranslator.py 08/ProgramFlow/BasicLoop/BasicLoop.vm
python3 VMTranslator.py 08/FunctionCalls/SimpleFunction/SimpleFunction.vm
```

### 2. 轉譯整個專案資料夾（Project 8 多檔專案）
傳入包含 `Sys.vm` 的資料夾路徑，程式會自動合併所有 `.vm` 檔並加上啟動碼，於該資料夾內輸出同名 `.asm` 檔案：

```bash
python3 VMTranslator.py 08/FunctionCalls/NestedCall
python3 VMTranslator.py 08/FunctionCalls/FibonacciElement
python3 VMTranslator.py 08/FunctionCalls/StaticsTest
```

---

## 驗證方式

1. 開啟 Nand2Tetris 官方工具中的 **CPU Emulator**。
2. 載入各測試資料夾內的 `.tst` 測試腳本（例如 `SimpleAdd.tst` 或 `FibonacciElement.tst`）。
3. 執行腳本並確認底部狀態列顯示 `End of script - Comparison ended successfully`（與 `.cmp` 標準輸出完全一致）。