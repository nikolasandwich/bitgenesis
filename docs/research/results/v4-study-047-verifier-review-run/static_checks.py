"""核验新增代码边界、占位/秘密模式、导入依赖与空白。"""
import ast,json,re,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts import middle_withdrawal_inputs as inputs
paths=['scripts/verify_v4_middle_withdrawal.py','tests/test_v4_middle_withdrawal_verifier.py']
placeholders=[];secrets=[];whitespace=[]
for name in paths:
 text=Path(name).read_text()
 for number,line in enumerate(text.splitlines(),1):
  if re.search(r'\b(?:TBD|TODO|FIXME|HACK|XXX)\b',line):placeholders.append([name,number])
  if re.search(r'(?:sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,})',line):secrets.append([name,number])
  if line.rstrip()!=line:whitespace.append([name,number])
 if not text.endswith('\n'):whitespace.append([name,'EOF'])
imports=[]
for node in ast.walk(ast.parse(Path(paths[0]).read_text())):
 if isinstance(node,ast.Import):imports.extend(x.name for x in node.names)
 elif isinstance(node,ast.ImportFrom):imports.append(node.module)
assert not any('run_v4_middle_withdrawal' in x for x in imports)
result={'status':'PASS','placeholders':placeholders,'concrete_secret_patterns':secrets,'whitespace':whitespace,'verifier_imports':imports,'runtime_static_check':'标准库和既有字典核/union-find；无生产科学函数导入；未配置专门lint命令','tracked_diff':subprocess.check_output(['git','diff','--name-only'],text=True).splitlines(),'git_status':subprocess.check_output(['git','status','--short'],text=True).splitlines()}
assert not placeholders and not secrets and not whitespace and not result['tracked_diff']
(Path(__file__).parent/'static-checks.json').write_text(inputs.canonical(result)+'\n')
print(json.dumps(result,ensure_ascii=False))
