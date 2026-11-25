import sys
from pathlib import Path


class SymbolTable:
    """管理預定義符號、標籤（Label）與變數（Variable）的記憶體位址對應。"""

    def __init__(self):
        self.table = {
            "SP": 0,
            "LCL": 1,
            "ARG": 2,
            "THIS": 3,
            "THAT": 4,
            "SCREEN": 16384,
            "KBD": 24576,
            **{f"R{i}": i for i in range(16)},
        }
        self.next_ram_address = 16

    def add_entry(self, symbol: str, address: int) -> None:
        self.table[symbol] = address

    def contains(self, symbol: str) -> bool:
        return symbol in self.table

    def get_address(self, symbol: str) -> int:
        return self.table[symbol]

    def allocate_variable(self, symbol: str) -> int:
        address = self.next_ram_address
        self.table[symbol] = address
        self.next_ram_address += 1
        return address


class Code:
    """將 Hack 組合語言的 dest、comp、jump 助記碼轉換為二進位字串。"""

    DEST = {
        "": "000",
        "M": "001",
        "D": "010",
        "MD": "011",
        "DM": "011",
        "A": "100",
        "AM": "101",
        "MA": "101",
        "AD": "110",
        "DA": "110",
        "AMD": "111",
        "ADM": "111",
    }

    COMP = {
        # a = 0
        "0": "0101010",
        "1": "0111111",
        "-1": "0111010",
        "D": "0001100",
        "A": "0110000",
        "!D": "0001101",
        "!A": "0110001",
        "-D": "0001111",
        "-A": "0110011",
        "D+1": "0011111",
        "A+1": "0110111",
        "D-1": "0001110",
        "A-1": "0110010",
        "D+A": "0000010",
        "D-A": "0010011",
        "A-D": "0000111",
        "D&A": "0000000",
        "D|A": "0010101",
        # a = 1
        "M": "1110000",
        "!M": "1110001",
        "-M": "1110011",
        "M+1": "1110111",
        "M-1": "1110010",
        "D+M": "1000010",
        "D-M": "1010011",
        "M-D": "1000111",
        "D&M": "1000000",
        "D|M": "1010101",
    }

    JUMP = {
        "": "000",
        "JGT": "001",
        "JEQ": "010",
        "JGE": "011",
        "JLT": "100",
        "JNE": "101",
        "JLE": "110",
        "JMP": "111",
    }

    @classmethod
    def dest(cls, mnemonic: str) -> str:
        if mnemonic not in cls.DEST:
            raise ValueError(f"無效的 dest 欄位: '{mnemonic}'")
        return cls.DEST[mnemonic]

    @classmethod
    def comp(cls, mnemonic: str) -> str:
        if mnemonic not in cls.COMP:
            raise ValueError(f"無效的 comp 欄位: '{mnemonic}'")
        return cls.COMP[mnemonic]

    @classmethod
    def jump(cls, mnemonic: str) -> str:
        if mnemonic not in cls.JUMP:
            raise ValueError(f"無效的 jump 欄位: '{mnemonic}'")
        return cls.JUMP[mnemonic]


class Parser:
    """清理註解與空白，並解析每一行指令的類型與組成欄位。"""

    def __init__(self, lines: list[str]):
        self.instructions: list[tuple[int, str]] = []
        for line_no, raw_line in enumerate(lines, start=1):
            # 移除 // 註解與所有空白字元
            code_part = raw_line.split("//", 1)[0]
            cleaned = "".join(code_part.split())
            if cleaned:
                self.instructions.append((line_no, cleaned))

    @staticmethod
    def instruction_type(inst: str) -> str:
        if inst.startswith("@"):
            return "A_INSTRUCTION"
        if inst.startswith("(") and inst.endswith(")"):
            return "L_INSTRUCTION"
        return "C_INSTRUCTION"

    @staticmethod
    def symbol(inst: str) -> str:
        if inst.startswith("@"):
            return inst[1:]
        if inst.startswith("(") and inst.endswith(")"):
            return inst[1:-1]
        raise ValueError(f"無法從 C 指令擷取符號: '{inst}'")

    @staticmethod
    def parse_c_instruction(inst: str) -> tuple[str, str, str]:
        dest = ""
        jump = ""
        rest = inst

        if "=" in rest:
            dest, rest = rest.split("=", 1)
        if ";" in rest:
            comp, jump = rest.split(";", 1)
        else:
            comp = rest

        return dest, comp, jump


class HackAssembler:
    """執行兩階段組譯，將 Hack 組合語言轉換為 16-bit 二進位機器碼。"""

    def __init__(self):
        self.symbols = SymbolTable()

    def assemble(self, source_lines: list[str]) -> list[str]:
        parser = Parser(source_lines)

        # 第一階段（First Pass）：掃描所有 (LABEL) 並記錄對應的 ROM 位址
        rom_address = 0
        for line_no, inst in parser.instructions:
            inst_type = parser.instruction_type(inst)
            if inst_type == "L_INSTRUCTION":
                label = parser.symbol(inst)
                if not label:
                    raise ValueError(f"第 {line_no} 行：標籤名稱不可為空")
                self.symbols.add_entry(label, rom_address)
            else:
                rom_address += 1

        # 第二階段（Second Pass）：翻譯 A 指令與 C 指令為 16-bit 二進位碼
        machine_code: list[str] = []
        for line_no, inst in parser.instructions:
            inst_type = parser.instruction_type(inst)

            if inst_type == "L_INSTRUCTION":
                continue

            if inst_type == "A_INSTRUCTION":
                sym = parser.symbol(inst)
                if sym.isdigit():
                    address = int(sym)
                    if not (0 <= address <= 32767):
                        raise ValueError(f"第 {line_no} 行：常數超出 15-bit 範圍 ({address})")
                else:
                    if self.symbols.contains(sym):
                        address = self.symbols.get_address(sym)
                    else:
                        address = self.symbols.allocate_variable(sym)
                machine_code.append(f"0{address:015b}")

            elif inst_type == "C_INSTRUCTION":
                try:
                    dest, comp, jump = parser.parse_c_instruction(inst)
                    binary = "111" + Code.comp(comp) + Code.dest(dest) + Code.jump(jump)
                    machine_code.append(binary)
                except ValueError as e:
                    raise ValueError(f"第 {line_no} 行（{inst}）：{e}") from e

        return machine_code


def main() -> None:
    if len(sys.argv) != 2:
        print("用法: python HackAssembler.py <輸入檔案.asm>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.is_file():
        print(f"錯誤：找不到檔案 '{input_path}'")
        sys.exit(1)

    output_path = input_path.with_suffix(".hack")

    source_lines = input_path.read_text(encoding="utf-8").splitlines()
    assembler = HackAssembler()
    binary_lines = assembler.assemble(source_lines)

    output_path.write_text("\n".join(binary_lines) + "\n", encoding="utf-8")
    print(f"組譯完成：{output_path}（共 {len(binary_lines)} 行指令）")


if __name__ == "__main__":
    main()
