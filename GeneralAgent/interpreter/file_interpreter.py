import re, os
import logging
from .interpreter import Interpreter

file_prompt = """
# For file operations, ALWAYS enclose your commands in triple backticks (```). Here are the commands:

1. Write: 
```
file <file_path> write <start_line> <end_line> <<EOF
<content>
EOF
```
2. Read: 
```
file <file_path> read <start_line> <end_line>
```
3. Delete: 
```
file <file_path> delete <start_line> <end_line>
```

Line numbers start from 0, and -1 is the last line.
Read will print the content of the file with [line numbers] prefixed.
"""


class FileInterpreter(Interpreter):
    
    output_match_pattern = '```(\n)?file(\n| )?(.*?) (write|read|delete) (-?\d+) (-?\d+)(.*?)```'

    async def prompt(self, messages) -> str:
        return file_prompt
    
    def _parse_commands(self, string):
        match = re.search(self.output_match_pattern, string, re.DOTALL)
        assert match is not None
        file_path = match.group(3)
        operation = match.group(4)
        start_line = int(match.group(5))
        end_line = int(match.group(6))
        content = match.group(7).strip()
        if content.startswith('<<EOF'):
            content = content[5:].strip()
        if content.endswith('EOF'):
            content = content[:-3].strip()
        return file_path, operation, start_line, end_line, content

    async def output_parse(self, string) -> (str, bool):
        logging.debug('FileInterpreter:parse called')
        file_path, operation, start_line, end_line, content = self._parse_commands(string)
        is_stop = False
        if operation == 'write':
            self._write_file(file_path, content, start_line, end_line)
            return 'write successfully', is_stop
        elif operation == 'delete':
            self._delete_file(file_path, start_line, end_line)
            return 'delete successfully', is_stop
        elif operation == 'read':
            content = self._read_file(file_path, start_line, end_line)
            return content, is_stop
    
    def _write_file(self, file_path, content, start_index, end_index):
        # if .py file, remove ```python  and ``` pair
        if file_path.endswith('.py'):
            content = content.replace('```python', '')
            content = content.replace('```', '')
        # file_path = os.path.join(self.workspace, file_path)
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                f.write('')
        with open(file_path, 'r') as f:
            lines = f.readlines()
        if start_index == -1:
            start_index = len(lines)
        if end_index == -1:
            end_index = len(lines)
        lines = lines[:start_index] + [content] + lines[end_index+1:]
        with open(file_path, 'w') as f:
            f.writelines(lines)

    def _delete_file(self, file_path, start_index, end_index):
        # file_path = os.path.join(self.workspace, file_path)
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                f.write('')
        with open(file_path, 'r') as f:
            lines = f.readlines()
        if start_index == -1:
            start_index = len(lines)
        if end_index == -1:
            end_index = len(lines)
        lines = lines[:start_index] + lines[end_index+1:]
        with open(file_path, 'w') as f:
            f.writelines(lines)

    def _read_file(self, file_path, start_index, end_index):
        # file_path = os.path.join(self.workspace, file_path)
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                f.write('')
        with open(file_path, 'r') as f:
            lines = f.readlines()
        if start_index == -1:
            start_index = len(lines)
        if end_index == -1:
            end_index = len(lines)
        content = ''
        end_index = min(end_index + 1, len(lines))
        for index in range(start_index, end_index):
            new_add = f'[{index}]{lines[index]}\n'
            if len(content + new_add) > 2000:
                left_count = len(lines) - index
                content += f'...\n[there are {left_count} lines left]'
                break
            content += new_add
        return content.strip()