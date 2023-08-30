# 控制器
# 用于控制整个系统的运行
from memory import Memory, ConceptNode
from code import CodeWorkspace
from tools import Tools


class Controller:
    def __init__(self, workspace):
        # workspace: 工作空间
        self.workspace = workspace
        self.memory = Memory(f'{workspace}/memory.json')
        self.code_workspace = CodeWorkspace(f'{workspace}/code.bin')
        self.tools = Tools()

    def input(self, user_input):
        pass

    def _run_command(self, command):
        # 输入命令(string)，生成代码并执行
        retry_count = 3
        # 生成代码
        code = self._code_generate(command)
        # 检查&修复代码
        for index in range(retry_count):
            check_success = self._code_check(command, code)
            if check_success: break
            if index == retry_count - 1: return False
            code = self._code_fix(code, command=command)
        # 执行代码&修复代码
        for index in range(retry_count):
            run_success, sys_stdio = self.code_workspace.run_code(command, code)
            if run_success: break
            if index == retry_count - 1: return False
            code = self._code_fix(code, command=command, error=sys_stdio)
        return run_success

    def _code_generate(self, command):
        # 根据命令，生成执行的代码
        # TODO
        code = ''
        return code

    def _code_check(self, command, code):
        # TODO: 
        # 验证代码是否可以执行，有没有什么问题
        return True
    
    def _code_fix(self, code, command=None, error=None):
        # TODO: 
        # 根据command，修复代码
        return code