# Nand2Tetris Project 6：Hack Assembler（組譯器）

本專案為 [Nand2Tetris](https://www.nand2tetris.org/) 課程 **Project 6** 的實作，使用 Python 撰寫的 **Hack 組合語言組譯器（Assembler）**，可將 `.asm` 組合語言檔案轉換為 16-bit 二進位機器碼（`.hack`）。

---

## 專案目錄結構

```text
06/
├── HackAssembler.py    # Hack 組譯器主程式
├── README.md           # 專案說明文件
├── add/
│   └── Add.asm         # 測試檔（與產出的 Add.hack）
├── max/
│   └── Max.asm
├── pong/
│   └── Pong.asm
└── rect/
    └── Rect.asm
```

---

## 系統架構與運作流程

程式依據 Nand2Tetris 官方建議的模組化設計，分為四個核心類別，並採用 **兩階段掃描（Two-pass Assembly）** 機制：

### 1. 模組說明
* **`SymbolTable`（符號表）**：管理預定義符號（`R0`–`R15`、`SP`、`LCL`、`ARG`、`THIS`、`THAT`、`SCREEN`、`KBD`）、程式標籤（Label）與變數（Variable，從 RAM 位址 `16` 開始依序配置）。
* **`Code`（編碼器）**：將 C 指令中的 `dest`、`comp`、`jump` 助記碼查表轉換為對應的二進位字串。
* **`Parser`（語法解析器）**：清除 `//` 註解、空白字元與空行，並判斷指令類型（A 指令、C 指令、L 偽指令）及拆解欄位。
* **`HackAssembler`（主控制器）**：協調兩階段掃描流程並輸出 16-bit 機器碼。

### 2. 兩階段組譯流程
1. **前處理**：讀取 `.asm` 檔案，移除註解與空白。
2. **第一階段（First Pass）**：掃描所有 `(LABEL)` 偽指令，將標籤與對應的 ROM 指令位址寫入 `SymbolTable`（標籤本身不佔用 ROM 位址）。
3. **第二階段（Second Pass）**：
   * **A 指令（`@value`）**：若為數字直接轉為 `0` 開頭的 15-bit 二進位碼；若為符號則查詢 `SymbolTable`，未定義的變數自動配置新 RAM 位址。
   * **C 指令（`dest=comp;jump`）**：拆解欄位並組合為 `111 + a + cccccc + ddd + jjj` 的 16-bit 二進位碼。
4. **輸出檔案**：於原始 `.asm` 檔案的相同路徑下產生對應的 `.hack` 檔案。

---

## 使用方式

### 環境需求
* Python 3.8 以上版本（僅使用內建標準函式庫，無需額外安裝套件）

### 執行組譯
在終端機切換至 `06` 資料夾後，傳入目標 `.asm` 檔案路徑即可：

```bash
cd 06
python3 HackAssembler.py add/Add.asm
```

其他測試檔執行範例：

```bash
python3 HackAssembler.py max/Max.asm
python3 HackAssembler.py rect/Rect.asm
python3 HackAssembler.py pong/Pong.asm
```

執行成功後，終端機將顯示組譯完成的檔案路徑與總指令行數，並在對應子資料夾內產生 `.hack` 檔案。

---

## 驗證方式

1. 開啟 Nand2Tetris 官方工具中的 **Assembler** 或 **CPU Emulator**。
2. 載入相同的 `.asm` 檔案進行組譯，或將本程式產出的 `.hack` 檔案載入比較。
3. 確認所有指令行數與 16-bit 二進位內容完全一致。