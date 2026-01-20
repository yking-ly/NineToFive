import re

# Read app.py
with open(r'e:\VSCODE\NineToFive\backend\app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the strip_markdown function and replace it
in_function = False
function_start = -1
function_end = -1

for i, line in enumerate(lines):
    if 'def strip_markdown(text):' in line:
        in_function = True
        function_start = i - 1  # Include the comment line before it
    elif in_function and line.strip() and not line.startswith(' ' * 12) and 'return' not in lines[i-1]:
        function_end = i
        break

if function_start >= 0:
    # New function
    new_lines = [
        '        # Helper function to strip markdown (for Kira plaintext responses)\n',
        '        def strip_markdown(text):\n',
        '            """Aggressively remove ALL markdown syntax for pure plaintext TTS output"""\n',
        '            import re\n',
        '            # Remove code blocks\n',
        "            text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)\n",
        '            # Remove bold (multiple passes for nested)\n',
        '            for _ in range(3):\n',
        "                text = re.sub(r'\\*\\*(.+?)\\*\\*', r'\\1', text)\n",
        "                text = re.sub(r'__(.+?)__', r'\\1', text)\n",
        '            # Remove italic\n',
        '            for _ in range(3):\n',
        "                text = re.sub(r'\\*(.+?)\\*', r'\\1', text)\n",
        "                text = re.sub(r'_(.+?)_', r'\\1', text)\n",
        '            # Remove headers\n',
        "            text = re.sub(r'^#{1,6}\\s+', '', text, flags=re.MULTILINE)\n",
        '            # Remove inline code\n',
        "            text = re.sub(r'`(.+?)`', r'\\1', text)\n",
        '            # Remove list markers\n',
        "            text = re.sub(r'^\\s*[-*+]\\s+', '', text, flags=re.MULTILINE)\n",
        "            text = re.sub(r'^\\s*\\d+\\.\\s+', '', text, flags=re.MULTILINE)\n",
        '            # Remove links [text](url)\n',
        "            text = re.sub(r'\\[([^]]+)\\]\\([^)]+\\)', r'\\1', text)\n",
        '            # Clean up spaces\n',
        "            text = re.sub(r'\\s+', ' ', text)\n",
        '            return text.strip()\n',
        '        \n',
    ]
    
    # Replace
    lines = lines[:function_start] + new_lines + lines[function_end:]
    
    # Write back
    with open(r'e:\VSCODE\NineToFive\backend\app.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("Successfully enhanced markdown stripper!")
else:
    print("Could not find strip_markdown function")
