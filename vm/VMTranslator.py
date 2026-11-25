import sys
from pathlib import Path


class Parser:
    """清理註解與空白，解析每一行 VM 指令的類型與參數。"""

    ARITHMETIC_COMMANDS = {"add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"}

    def __init__(self, vm_file: Path):
        self.commands: list[list[str]] = []
        for raw_line in vm_file.read_text(encoding="utf-8").splitlines():
            code_part = raw_line.split("//", 1)[0].strip()
            if code_part:
                self.commands.append(code_part.split())

    @classmethod
    def command_type(cls, tokens: list[str]) -> str:
        cmd = tokens[0]
        if cmd in cls.ARITHMETIC_COMMANDS:
            return "C_ARITHMETIC"
        mapping = {
            "push": "C_PUSH",
            "pop": "C_POP",
            "label": "C_LABEL",
            "goto": "C_GOTO",
            "if-goto": "C_IF",
            "function": "C_FUNCTION",
            "call": "C_CALL",
            "return": "C_RETURN",
        }
        if cmd not in mapping:
            raise ValueError(f"不支援的 VM 指令: '{cmd}'")
        return mapping[cmd]


class CodeWriter:
    """將 VM 指令轉譯為 Hack 組合語言（.asm）。"""

    SEGMENT_POINTERS = {
        "local": "LCL",
        "argument": "ARG",
        "this": "THIS",
        "that": "THAT",
    }

    def __init__(self):
        self.lines: list[str] = []
        self.current_file = ""
        self.current_function = ""
        self.label_counter = 0
        self.call_counter = 0

    def set_file_name(self, file_name: str) -> None:
        self.current_file = file_name

    def _emit(self, *asm_lines: str) -> None:
        self.lines.extend(asm_lines)

    def _push_d(self) -> None:
        """將 D 暫存器的值推入堆疊（*SP = D; SP++）。"""
        self._emit("@SP", "A=M", "M=D", "@SP", "M=M+1")

    def _pop_to_d(self) -> None:
        """從堆疊頂端彈出值到 D 暫存器（SP--; D = *SP）。"""
        self._emit("@SP", "AM=M-1", "D=M")

    # ------------------------------------------------------------------
    # 第 8 章：啟動碼（Bootstrap Code）
    # ------------------------------------------------------------------
    def write_init(self) -> None:
        """初始化 SP = 256 並呼叫 Sys.init。"""
        self._emit("// Bootstrap code", "@256", "D=A", "@SP", "M=D")
        self.write_call("Sys.init", 0)

    # ------------------------------------------------------------------
    # 第 7 章：算術與邏輯指令
    # ------------------------------------------------------------------
    def write_arithmetic(self, command: str) -> None:
        self._emit(f"// {command}")

        if command in ("add", "sub", "and", "or"):
            op = {"add": "M+D", "sub": "M-D", "and": "M&D", "or": "M|D"}[command]
            self._emit("@SP", "AM=M-1", "D=M", "A=A-1", f"M={op}")

        elif command in ("neg", "not"):
            op = {"neg": "-M", "not": "!M"}[command]
            self._emit("@SP", "A=M-1", f"M={op}")

        elif command in ("eq", "gt", "lt"):
            jmp = {"eq": "JEQ", "gt": "JGT", "lt": "JLT"}[command]
            idx = self.label_counter
            self.label_counter += 1
            true_label = f"COMP_TRUE_{idx}"
            end_label = f"COMP_END_{idx}"
            self._emit(
                "@SP", "AM=M-1", "D=M", "A=A-1", "D=M-D",
                f"@{true_label}", f"D;{jmp}",
                "@SP", "A=M-1", "M=0",
                f"@{end_label}", "0;JMP",
                f"({true_label})",
                "@SP", "A=M-1", "M=-1",
                f"({end_label})",
            )

    # ------------------------------------------------------------------
    # 第 7 章：記憶體存取指令（push / pop）
    # ------------------------------------------------------------------
    def write_push_pop(self, cmd_type: str, segment: str, index: int) -> None:
        action = "push" if cmd_type == "C_PUSH" else "pop"
        self._emit(f"// {action} {segment} {index}")

        if cmd_type == "C_PUSH":
            if segment == "constant":
                self._emit(f"@{index}", "D=A")
            elif segment in self.SEGMENT_POINTERS:
                base = self.SEGMENT_POINTERS[segment]
                self._emit(f"@{index}", "D=A", f"@{base}", "A=D+M", "D=M")
            elif segment == "temp":
                self._emit(f"@{5 + index}", "D=M")
            elif segment == "pointer":
                reg = "THIS" if index == 0 else "THAT"
                self._emit(f"@{reg}", "D=M")
            elif segment == "static":
                self._emit(f"@{self.current_file}.{index}", "D=M")
            else:
                raise ValueError(f"無效的 push 區段: '{segment}'")
            self._push_d()

        elif cmd_type == "C_POP":
            if segment in self.SEGMENT_POINTERS:
                base = self.SEGMENT_POINTERS[segment]
                # 先將目標位址暫存於 R13
                self._emit(f"@{index}", "D=A", f"@{base}", "D=D+M", "@R13", "M=D")
                self._pop_to_d()
                self._emit("@R13", "A=M", "M=D")
            elif segment == "temp":
                self._pop_to_d()
                self._emit(f"@{5 + index}", "M=D")
            elif segment == "pointer":
                reg = "THIS" if index == 0 else "THAT"
                self._pop_to_d()
                self._emit(f"@{reg}", "M=D")
            elif segment == "static":
                self._pop_to_d()
                self._emit(f"@{self.current_file}.{index}", "M=D")
            else:
                raise ValueError(f"無效的 pop 區段: '{segment}'")

    # ------------------------------------------------------------------
    # 第 8 章：分支控制指令（label / goto / if-goto）
    # ------------------------------------------------------------------
    def _scoped_label(self, label: str) -> str:
        return f"{self.current_function}${label}" if self.current_function else label

    def write_label(self, label: str) -> None:
        self._emit(f"// label {label}", f"({self._scoped_label(label)})")

    def write_goto(self, label: str) -> None:
        self._emit(f"// goto {label}", f"@{self._scoped_label(label)}", "0;JMP")

    def write_if(self, label: str) -> None:
        self._emit(f"// if-goto {label}")
        self._pop_to_d()
        self._emit(f"@{self._scoped_label(label)}", "D;JNE")

    # ------------------------------------------------------------------
    # 第 8 章：函式呼叫與返回指令（function / call / return）
    # ------------------------------------------------------------------
    def write_function(self, func_name: str, num_vars: int) -> None:
        self.current_function = func_name
        self._emit(f"// function {func_name} {num_vars}", f"({func_name})")
        for _ in range(num_vars):
            self._emit("@0", "D=A")
            self._push_d()

    def write_call(self, func_name: str, num_args: int) -> None:
        ret_label = f"{func_name}$ret.{self.call_counter}"
        self.call_counter += 1
        self._emit(f"// call {func_name} {num_args}")

        # 1. push returnAddress
        self._emit(f"@{ret_label}", "D=A")
        self._push_d()

        # 2. push LCL, ARG, THIS, THAT
        for reg in ("LCL", "ARG", "THIS", "THAT"):
            self._emit(f"@{reg}", "D=M")
            self._push_d()

        # 3. ARG = SP - 5 - num_args
        self._emit("@SP", "D=M", f"@{5 + num_args}", "D=D-A", "@ARG", "M=D")

        # 4. LCL = SP
        self._emit("@SP", "D=M", "@LCL", "M=D")

        # 5. goto func_name & (ret_label)
        self._emit(f"@{func_name}", "0;JMP", f"({ret_label})")

    def write_return(self) -> None:
        self._emit("// return")
        # endFrame (R13) = LCL
        self._emit("@LCL", "D=M", "@R13", "M=D")
        # retAddr (R14) = *(endFrame - 5)
        self._emit("@5", "A=D-A", "D=M", "@R14", "M=D")
        # *ARG = pop()
        self._pop_to_d()
        self._emit("@ARG", "A=M", "M=D")
        # SP = ARG + 1
        self._emit("@ARG", "D=M+1", "@SP", "M=D")
        # 依序還原 THAT, THIS, ARG, LCL
        for reg in ("THAT", "THIS", "ARG", "LCL"):
            self._emit("@R13", "AM=M-1", "D=M", f"@{reg}", "M=D")
        # goto retAddr
        self._emit("@R14", "A=M", "0;JMP")

    def get_output(self) -> str:
        return "\n".join(self.lines) + "\n"


def translate_file(vm_file: Path, writer: CodeWriter) -> None:
    writer.set_file_name(vm_file.stem)
    parser = Parser(vm_file)

    for tokens in parser.commands:
        cmd_type = Parser.command_type(tokens)
        if cmd_type == "C_ARITHMETIC":
            writer.write_arithmetic(tokens[0])
        elif cmd_type in ("C_PUSH", "C_POP"):
            writer.write_push_pop(cmd_type, tokens[1], int(tokens[2]))
        elif cmd_type == "C_LABEL":
            writer.write_label(tokens[1])
        elif cmd_type == "C_GOTO":
            writer.write_goto(tokens[1])
        elif cmd_type == "C_IF":
            writer.write_if(tokens[1])
        elif cmd_type == "C_FUNCTION":
            writer.write_function(tokens[1], int(tokens[2]))
        elif cmd_type == "C_CALL":
            writer.write_call(tokens[1], int(tokens[2]))
        elif cmd_type == "C_RETURN":
            writer.write_return()


def main() -> None:
    if len(sys.argv) != 2:
        print("用法: python3 VMTranslator.py <檔案.vm 或 資料夾路徑>")
        sys.exit(1)

    target = Path(sys.argv[1])
    if not target.exists():
        print(f"錯誤：找不到路徑 '{target}'")
        sys.exit(1)

    writer = CodeWriter()

    if target.is_file():
        if target.suffix != ".vm":
            print("錯誤：輸入檔案必須為 .vm 檔")
            sys.exit(1)
        vm_files = [target]
        output_path = target.with_suffix(".asm")
    else:
        vm_files = sorted(target.glob("*.vm"))
        if not vm_files:
            print(f"錯誤：資料夾 '{target}' 內沒有任何 .vm 檔案")
            sys.exit(1)
        output_path = target / f"{target.name}.asm"
        # 資料夾內若有 Sys.vm，自動寫入第 8 章啟動碼
        if any(f.name == "Sys.vm" for f in vm_files):
            writer.write_init()

    for vm_file in vm_files:
        translate_file(vm_file, writer)

    output_path.write_text(writer.get_output(), encoding="utf-8")
    print(f"轉譯完成：{output_path}（共處理 {len(vm_files)} 個 .vm 檔）")


if __name__ == "__main__":
    main()
